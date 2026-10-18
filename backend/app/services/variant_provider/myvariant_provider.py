"""
Live provider: MyVariant.info.

Why MyVariant.info instead of calling Ensembl + ClinVar separately (as
listed as options in the original spec): it aggregates dbSNP (position,
alleles, gene), ClinVar (clinical significance) and dbNSFP (which itself
bundles SIFT/PolyPhen predictions) into a single JSON response for a
given rsID. That means ONE HTTP call covers what would otherwise be
2-3 separate API integrations -- fewer failure points for our fallback
logic to handle, which matters more than a purist "use the primary
source for each field" approach for an MVP.

IMPORTANT — division of responsibility:
This provider ONLY extracts raw fields as reported by the databases
(SIFT prediction string, PolyPhen score, ClinVar significance, etc.).
It does NOT decide what counts as LOW/MODERATE/HIGH impact, and it does
NOT compute a perturbation_factor for the simulation. That interpretation
step is a separate, explicitly-documented model (FunctionalEffectService,
added in Step 4) -- keeping "what the database reported" and "what we
computed from it" as clearly separate pieces of code, not just separate
UI labels.

This class makes a real network call and can fail for many reasons
(timeout, rate limit, variant not found, malformed response). All of
those are treated as "no data" (return None) rather than raised as
exceptions, so the caller can fall back to the demo provider cleanly.
"""
import logging
from typing import Optional

import httpx

from collections import Counter

from app.services.variant_provider.base import VariantProvider, NormalizedVariant
from app.services.functional_effect_service import normalize_sift, normalize_polyphen

logger = logging.getLogger(__name__)

# NOTE: /v1/variant/<id> only accepts HGVS IDs (e.g. chr11:g.5227002T>A),
# NOT rsIDs -- calling it with "rs334" always returns 404/notfound, which
# silently pushed every lookup onto the demo fallback. rsIDs must go
# through the query endpoint instead: /v1/query?q=dbsnp.rsid:rs334
MYVARIANT_QUERY_URL = "https://myvariant.info/v1/query"
MYVARIANT_FIELDS = "dbsnp,clinvar,dbnsfp,snpeff"
REQUEST_TIMEOUT_SECONDS = 10.0


class MyVariantProvider(VariantProvider):
    name = "myvariant"

    def fetch_variant(self, identifier: str) -> Optional[NormalizedVariant]:
        if not identifier.lower().startswith("rs"):
            # MyVariant.info variant-by-ID lookup expects an rsID (or HGVS).
            # Demo keys like "demo-001" are never valid here -- skip the
            # network call entirely rather than waste a request.
            return None

        rsid = identifier.strip().lower()

        try:
            response = httpx.get(
                MYVARIANT_QUERY_URL,
                params={
                    "q": f"dbsnp.rsid:{rsid}",
                    "fields": MYVARIANT_FIELDS,
                    "size": 10,
                    # Demo data uses GRCh38 positions; ask for the same build so
                    # live and demo variants are directly comparable.
                    "assembly": "hg38",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("MyVariant.info request failed for %s: %s", identifier, exc)
            return None
        except ValueError as exc:
            logger.warning("MyVariant.info returned invalid JSON for %s: %s", identifier, exc)
            return None

        hits = (data or {}).get("hits") or []
        if not hits:
            logger.info("MyVariant.info has no record for %s", identifier)
            return None

        # One rsID can map to several hits (one per alternate allele, e.g.
        # rs334 -> T>A, T>C, T>G). Prefer the allele with the most clinical /
        # functional annotation, since that's the one the analysis needs.
        payload = max(hits, key=self._annotation_richness)

        try:
            return self._normalize(identifier.strip(), payload)
        except Exception as exc:
            # MyVariant's schema shape varies quite a bit between variant
            # types (SNV vs indel, single vs multiple ClinVar submissions,
            # etc.) -- if parsing breaks, treat it as "no usable data"
            # rather than letting a malformed response crash the request.
            logger.warning("Failed to parse MyVariant.info response for %s: %s", identifier, exc)
            return None

    @classmethod
    def _annotation_richness(cls, hit: dict) -> tuple:
        sig = (cls._clinvar_consensus(hit.get("clinvar")) or "").lower()
        clinical = 2 if "pathogenic" in sig and "conflicting" not in sig else (1 if sig else 0)
        coverage = bool(hit.get("dbnsfp")) + bool(hit.get("snpeff"))
        # Ties are broken by the hit's _id so the choice is deterministic
        # (the API does not guarantee hit order).
        return (clinical, coverage, hit.get("_id", ""))

    @staticmethod
    def _clinvar_consensus(clinvar) -> Optional[str]:
        """A variant usually has several ClinVar submissions (RCVs) that can
        disagree. Use the most common informative classification instead of
        whichever submission happens to be listed first."""
        clinvar = clinvar[0] if isinstance(clinvar, list) and clinvar else clinvar
        if not isinstance(clinvar, dict):
            return None
        rcvs = clinvar.get("rcv") or []
        rcvs = rcvs if isinstance(rcvs, list) else [rcvs]
        values = []
        for rcv in rcvs:
            sig = (rcv or {}).get("clinical_significance") if isinstance(rcv, dict) else None
            if sig and sig.strip().lower() not in ("not provided", "other", "not_provided"):
                values.append(sig.strip())
        if not values:
            return None
        return Counter(values).most_common(1)[0][0]

    @staticmethod
    def _first(value):
        """MyVariant.info sometimes returns a list instead of a single object
        when multiple sources/submissions exist. Normalize to "just the first one"."""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def _normalize(self, identifier: str, payload: dict) -> NormalizedVariant:
        dbsnp = self._first(payload.get("dbsnp")) or {}
        clinvar = self._first(payload.get("clinvar")) or {}
        dbnsfp = self._first(payload.get("dbnsfp")) or {}
        snpeff = self._first(payload.get("snpeff")) or {}
        ann = self._first(snpeff.get("ann")) or {}

        gene_symbol = (
            (self._first(dbsnp.get("gene")) or {}).get("symbol")
            or ann.get("gene_name")
        )

        clinvar_sig = self._clinvar_consensus(clinvar)

        sift = self._first(dbnsfp.get("sift")) or {}
        polyphen = self._first((self._first(dbnsfp.get("polyphen2")) or {}).get("hdiv")) or {}

        functional_effect = {
            "sift_prediction": normalize_sift(self._first(sift.get("pred"))),
            "sift_score": self._to_float(self._first(sift.get("score"))),
            "polyphen_prediction": normalize_polyphen(self._first(polyphen.get("pred"))),
            "polyphen_score": self._to_float(self._first(polyphen.get("score"))),
            "clinvar_significance": clinvar_sig,
            # Interpretation (impact_level / perturbation_factor) is
            # deliberately NOT computed here -- see module docstring.
            # FunctionalEffectService (Step 4) fills these in from the
            # raw values above.
            "impact_level": "UNKNOWN",
            "perturbation_factor": 1.0,
            "perturbation_direction": None,
            "affected_node": None,
            "is_modelled": True,
            "note": "Raw SIFT/PolyPhen/ClinVar fields retrieved live from MyVariant.info. "
                    "Impact level and perturbation factor not yet interpreted.",
        }

        return NormalizedVariant(
            rsid=identifier,
            chromosome=str(dbsnp.get("chrom")) if dbsnp.get("chrom") else None,
            position=(self._first(dbsnp.get("hg38")) or self._first(dbsnp.get("hg19")) or {}).get("start"),
            ref_allele=dbsnp.get("ref"),
            alt_allele=dbsnp.get("alt"),
            gene_symbol=gene_symbol,
            consequence=ann.get("effect"),
            amino_acid_change=ann.get("hgvs_p"),
            source=self.name,
            protein=None,  # UniProt lookup is a separate concern, not part of this provider
            functional_effect=functional_effect,
            pathway_id=None,  # gene-to-pathway mapping happens in the pathway service, not here
            raw_response=payload,
        )

    @staticmethod
    def _to_float(value) -> Optional[float]:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
