"""
Demo/local provider.

Reads from data/variants/demo_variants.json. This is the provider that
guarantees the app still works end-to-end with zero network access
(project spec Section 14 - "the application MUST still work if an
external API is unavailable").

Supports lookup by:
  - demo key, e.g. "demo-001"
  - rsID, e.g. "rs113488022" (so a live-API miss can fall back seamlessly
    to a demo record for the *same* well-known variant, if we happen to
    have one)
"""
import json
import os
from typing import Optional

from app.services.variant_provider.base import VariantProvider, NormalizedVariant

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
DEMO_VARIANTS_PATH = os.path.join(PROJECT_ROOT, "data", "variants", "demo_variants.json")


class DemoVariantProvider(VariantProvider):
    name = "demo"

    def __init__(self):
        self._by_key = {}
        self._by_rsid = {}
        self._load()

    def _load(self):
        with open(DEMO_VARIANTS_PATH, "r") as f:
            raw = json.load(f)
        for key, record in raw.items():
            if key.startswith("_"):
                continue
            self._by_key[key] = record
            self._by_rsid[record["rsid"]] = record

    def list_demo_variants(self):
        """Used by GET /api/demo/variants — short list for a picker UI."""
        return [
            {
                "variant_id": key,
                "rsid": record["rsid"],
                "gene_symbol": record["gene_symbol"],
                "amino_acid_change": record.get("amino_acid_change"),
                "impact_level": record["functional_effect"]["impact_level"],
            }
            for key, record in self._by_key.items()
        ]

    def fetch_variant(self, identifier: str) -> Optional[NormalizedVariant]:
        record = self._by_key.get(identifier) or self._by_rsid.get(identifier)
        if record is None:
            return None

        return NormalizedVariant(
            rsid=record["rsid"],
            chromosome=record.get("chromosome"),
            position=record.get("position"),
            ref_allele=record.get("ref_allele"),
            alt_allele=record.get("alt_allele"),
            gene_symbol=record.get("gene_symbol"),
            consequence=record.get("consequence"),
            amino_acid_change=record.get("amino_acid_change"),
            source=self.name,
            protein=record.get("protein"),
            functional_effect=record.get("functional_effect"),
            pathway_id=record.get("pathway_id"),
            raw_response=record,
        )
