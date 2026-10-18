"""
Abstract provider interface for variant data.

This is the key piece of the "fallback requirement" (project spec Section 14):
the rest of the application only ever talks to this interface, never to
Ensembl/MyVariant.info or the demo dataset directly. That means we can try
a real API first and silently fall back to demo data on failure, without
any other part of the codebase knowing or caring which one actually answered.

Every provider returns data in the SAME normalized shape (see
`NormalizedVariant` below) regardless of where the data actually came from.
"""
from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class NormalizedFunctionalEffect(TypedDict, total=False):
    sift_prediction: Optional[str]
    sift_score: Optional[float]
    polyphen_prediction: Optional[str]
    polyphen_score: Optional[float]
    clinvar_significance: Optional[str]
    impact_level: str                      # LOW | MODERATE | HIGH | UNKNOWN
    perturbation_factor: float
    perturbation_direction: Optional[str]   # "loss_of_function" | "activating"
    affected_node: Optional[str]
    is_modelled: bool
    note: Optional[str]


class NormalizedProtein(TypedDict, total=False):
    uniprot_id: str
    name: str
    simple_description: Optional[str]


class NormalizedVariant(TypedDict, total=False):
    rsid: str
    chromosome: Optional[str]
    position: Optional[int]
    ref_allele: Optional[str]
    alt_allele: Optional[str]
    gene_symbol: Optional[str]
    consequence: Optional[str]
    amino_acid_change: Optional[str]
    source: str                             # which provider actually answered
    protein: Optional[NormalizedProtein]
    functional_effect: Optional[NormalizedFunctionalEffect]
    pathway_id: Optional[str]               # which demo pathway this gene maps to
    raw_response: Optional[dict]            # original payload, cached for traceability


class VariantProvider(ABC):
    """
    Every provider (live API or demo/local) implements this same contract.
    `fetch_variant` should return None (not raise) if it simply doesn't have
    data for the given identifier -- that's how the caller knows to try the
    next provider in the chain, rather than treating "no data" as an error.
    """

    #: A short machine-readable name used in the `source` field, e.g. "myvariant", "demo"
    name: str = "base"

    @abstractmethod
    def fetch_variant(self, identifier: str) -> Optional[NormalizedVariant]:
        """
        `identifier` can be an rsID (e.g. "rs113488022") or, for the demo
        provider, a demo key (e.g. "demo-001").

        Returns a NormalizedVariant dict, or None if this provider has no
        data for the identifier (NOT an error -- just "try the next one").
        """
        raise NotImplementedError
