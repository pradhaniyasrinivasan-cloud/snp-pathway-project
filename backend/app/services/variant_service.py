"""
VariantService: the single place in the app that knows about the
provider chain (live -> demo). Everything else (API routes, simulation
engine) just calls `get_variant()` and gets back a normalized result
plus a flag saying which source actually answered.

Caching strategy for the MVP: check the DB first (by rsid); if not
present, walk the provider chain, persist whatever we get, and return it.
This means the first lookup of a given variant may hit the network, but
every lookup after that is instant and offline.
"""
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.services.variant_provider.base import VariantProvider, NormalizedVariant
from app.services.variant_provider.myvariant_provider import MyVariantProvider
from app.services.variant_provider.demo_provider import DemoVariantProvider
from app.services.functional_effect_service import functional_effect_service, known_direction_for
from app.models import models

logger = logging.getLogger(__name__)


class VariantService:
    def __init__(self, providers: Optional[list[VariantProvider]] = None):
        # Order matters: first provider that returns non-None data wins.
        # Live API first, demo dataset last -- this IS the fallback chain
        # described in the project spec (Section 14).
        self.providers = providers or [MyVariantProvider(), DemoVariantProvider()]
        # Keep a direct handle on the demo provider too, for the
        # /api/demo/variants listing endpoint.
        self.demo_provider = next(
            (p for p in self.providers if isinstance(p, DemoVariantProvider)),
            DemoVariantProvider(),
        )

    def get_variant(self, identifier: str, db: Session, force_refresh: bool = False) -> Optional[NormalizedVariant]:
        identifier = identifier.strip()

        if not force_refresh:
            cached = self._get_cached(identifier, db)
            if cached is not None:
                return cached

        for provider in self.providers:
            result = provider.fetch_variant(identifier)
            if result is not None:
                result = self._ensure_interpreted(result)
                self._persist(result, db)
                return result

        return None

    def _ensure_interpreted(self, result: NormalizedVariant) -> NormalizedVariant:
        """
        Providers may return functional_effect data that hasn't been through
        FunctionalEffectService yet (this is true of MyVariantProvider, which
        deliberately only returns raw fields -- see its module docstring).
        This is the one place that guarantees every variant, regardless of
        source, ends up with a real impact_level/perturbation_factor before
        it's cached or returned to the API layer.

        The demo provider's data is already fully curated/interpreted
        (including hand-set direction overrides like BRAF V600E's
        "activating" effect), so we leave it untouched here.
        """
        fe = result.get("functional_effect")
        if fe is None:
            return result

        already_interpreted = fe.get("impact_level") not in (None, "UNKNOWN")
        if already_interpreted:
            return result

        interpreted = functional_effect_service.interpret(
            clinvar_significance=fe.get("clinvar_significance"),
            sift_prediction=fe.get("sift_prediction"),
            polyphen_prediction=fe.get("polyphen_prediction"),
            consequence=result.get("consequence"),
            # e.g. BRAF V600E / RAS G12: databases call these "damaging" but the
            # protein becomes MORE active -- see KNOWN_ACTIVATING_HOTSPOTS.
            known_direction_override=known_direction_for(
                result.get("gene_symbol"), result.get("amino_acid_change")
            ),
        )

        result["functional_effect"] = {
            **fe,
            "impact_level": interpreted.impact_level,
            "perturbation_factor": interpreted.perturbation_factor,
            "perturbation_direction": interpreted.perturbation_direction,
            "is_modelled": interpreted.is_modelled,
            "note": interpreted.note,
        }
        return result

    def _get_cached(self, identifier: str, db: Session) -> Optional[NormalizedVariant]:
        # Demo keys ("demo-001") are never cached under their own rsid lookup key
        # in a meaningful way here -- resolve them to an rsid via the demo
        # provider first, then check the DB cache for that rsid.
        rsid = identifier
        if identifier.startswith("demo-"):
            demo_record = self.demo_provider.fetch_variant(identifier)
            if demo_record is None:
                return None
            rsid = demo_record["rsid"]

        variant_row = db.query(models.Variant).filter_by(rsid=rsid).first()
        if variant_row is None:
            return None

        return self._row_to_normalized(variant_row)

    def _row_to_normalized(self, variant_row: models.Variant) -> NormalizedVariant:
        fe_row = variant_row.functional_effect
        functional_effect = None
        if fe_row:
            functional_effect = {
                "sift_prediction": fe_row.sift_prediction,
                "sift_score": fe_row.sift_score,
                "polyphen_prediction": fe_row.polyphen_prediction,
                "polyphen_score": fe_row.polyphen_score,
                "clinvar_significance": fe_row.clinvar_significance,
                "impact_level": fe_row.impact_level,
                "perturbation_factor": fe_row.perturbation_factor,
                "perturbation_direction": fe_row.perturbation_direction,
                "affected_node": fe_row.affected_node,
                "is_modelled": fe_row.is_modelled,
                "note": fe_row.note,
            }

        raw = None
        if variant_row.raw_response_json:
            try:
                raw = json.loads(variant_row.raw_response_json)
            except (TypeError, ValueError):
                raw = None

        pathway_id = (raw or {}).get("pathway_id")
        protein = (raw or {}).get("protein")

        return NormalizedVariant(
            rsid=variant_row.rsid,
            chromosome=variant_row.chromosome,
            position=variant_row.position,
            ref_allele=variant_row.ref_allele,
            alt_allele=variant_row.alt_allele,
            gene_symbol=variant_row.gene_symbol,
            consequence=variant_row.consequence,
            amino_acid_change=variant_row.amino_acid_change,
            source=variant_row.source,
            protein=protein,
            functional_effect=functional_effect,
            pathway_id=pathway_id,
            raw_response=raw,
        )

    def _persist(self, result: NormalizedVariant, db: Session) -> None:
        existing = db.query(models.Variant).filter_by(rsid=result["rsid"]).first()
        if existing:
            return  # already cached from a previous lookup; don't overwrite

        variant_row = models.Variant(
            rsid=result["rsid"],
            chromosome=result.get("chromosome"),
            position=result.get("position"),
            ref_allele=result.get("ref_allele"),
            alt_allele=result.get("alt_allele"),
            gene_symbol=result.get("gene_symbol"),
            consequence=result.get("consequence"),
            amino_acid_change=result.get("amino_acid_change"),
            source=result.get("source", "unknown"),
            raw_response_json=json.dumps({
                **(result.get("raw_response") or {}),
                "pathway_id": result.get("pathway_id"),
            }, default=str),
        )
        db.add(variant_row)
        db.commit()
        db.refresh(variant_row)

        fe = result.get("functional_effect")
        if fe:
            db.add(models.FunctionalEffect(
                variant_id=variant_row.id,
                sift_prediction=fe.get("sift_prediction"),
                sift_score=fe.get("sift_score"),
                polyphen_prediction=fe.get("polyphen_prediction"),
                polyphen_score=fe.get("polyphen_score"),
                clinvar_significance=fe.get("clinvar_significance"),
                impact_level=fe.get("impact_level", "UNKNOWN"),
                perturbation_factor=fe.get("perturbation_factor", 1.0),
                perturbation_direction=fe.get("perturbation_direction"),
                affected_node=fe.get("affected_node"),
                is_modelled=fe.get("is_modelled", True),
                note=fe.get("note"),
                source=result.get("source"),
            ))
            db.commit()

        logger.info("Cached variant %s (source=%s)", result["rsid"], result.get("source"))


# Module-level singleton so we don't rebuild the demo dataset index
# (JSON file read + parse) on every single request.
variant_service = VariantService()
