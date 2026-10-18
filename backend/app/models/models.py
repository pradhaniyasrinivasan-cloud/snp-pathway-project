"""
SQLAlchemy ORM models.

These map directly onto the database schema from the architecture doc:
Variant, FunctionalEffect, Protein, Pathway, PathwayNode, PathwayEdge,
SimulationRun.

Plain-language note for each table is included as a docstring, since this
project has to stay understandable to a biology beginner (and to whoever
reads this code later).
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.db import Base


class Variant(Base):
    """A single genetic variant (SNP), e.g. rs113488022."""
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    rsid = Column(String, unique=True, index=True, nullable=False)
    chromosome = Column(String, nullable=True)
    position = Column(Integer, nullable=True)
    ref_allele = Column(String, nullable=True)
    alt_allele = Column(String, nullable=True)
    gene_symbol = Column(String, index=True, nullable=True)
    consequence = Column(String, nullable=True)
    amino_acid_change = Column(String, nullable=True)
    source = Column(String, nullable=False, default="demo")  # "ensembl" | "myvariant" | "demo"
    raw_response_json = Column(Text, nullable=True)  # cached raw API payload, for traceability
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    functional_effect = relationship(
        "FunctionalEffect", back_populates="variant", uselist=False
    )
    simulation_runs = relationship("SimulationRun", back_populates="variant")


class FunctionalEffect(Base):
    """
    The predicted functional impact of a variant: how damaging it is
    to the protein, and how much that should perturb pathway activity.
    """
    __tablename__ = "functional_effects"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)

    sift_prediction = Column(String, nullable=True)
    sift_score = Column(Float, nullable=True)
    polyphen_prediction = Column(String, nullable=True)
    polyphen_score = Column(Float, nullable=True)
    clinvar_significance = Column(String, nullable=True)

    impact_level = Column(String, nullable=False, default="UNKNOWN")  # LOW/MODERATE/HIGH/UNKNOWN
    perturbation_factor = Column(Float, nullable=False, default=1.0)
    perturbation_direction = Column(String, nullable=True)  # "loss_of_function" | "activating"
    affected_node = Column(String, nullable=True)  # which pathway node this maps to

    is_modelled = Column(Boolean, nullable=False, default=True)
    note = Column(Text, nullable=True)
    source = Column(String, nullable=True)

    variant = relationship("Variant", back_populates="functional_effect")


class Protein(Base):
    """A protein, and a plain-English explanation of what it does."""
    __tablename__ = "proteins"

    id = Column(Integer, primary_key=True, index=True)
    uniprot_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    gene_symbol = Column(String, index=True, nullable=True)
    simple_description = Column(Text, nullable=True)


class Pathway(Base):
    """A signalling pathway, e.g. the MAPK/ERK cascade."""
    __tablename__ = "pathways"

    id = Column(Integer, primary_key=True, index=True)
    pathway_key = Column(String, unique=True, index=True, nullable=False)  # "mapk"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    terminal_node_key = Column(String, nullable=True)

    nodes = relationship("PathwayNode", back_populates="pathway")
    edges = relationship("PathwayEdge", back_populates="pathway")


class PathwayNode(Base):
    """A single protein/step within a pathway (e.g. 'RAS')."""
    __tablename__ = "pathway_nodes"

    id = Column(Integer, primary_key=True, index=True)
    pathway_id = Column(Integer, ForeignKey("pathways.id"), nullable=False)
    node_key = Column(String, nullable=False)  # "RAS" - unique within a pathway
    label = Column(String, nullable=False)
    protein_id = Column(Integer, ForeignKey("proteins.id"), nullable=True)
    baseline_activity = Column(Float, nullable=False, default=1.0)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)

    pathway = relationship("Pathway", back_populates="nodes")
    protein = relationship("Protein")


class PathwayEdge(Base):
    """A directed connection between two pathway nodes."""
    __tablename__ = "pathway_edges"

    id = Column(Integer, primary_key=True, index=True)
    pathway_id = Column(Integer, ForeignKey("pathways.id"), nullable=False)
    source_node_key = Column(String, nullable=False)
    target_node_key = Column(String, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    interaction_type = Column(String, nullable=False, default="activation")  # "activation" | "inhibition"

    pathway = relationship("Pathway", back_populates="edges")


class SimulationRun(Base):
    """A stored record of one normal-vs-variant simulation, for caching/history."""
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    pathway_id = Column(Integer, ForeignKey("pathways.id"), nullable=False)

    normal_result_json = Column(Text, nullable=False)
    variant_result_json = Column(Text, nullable=False)
    pathway_output_normal = Column(Float, nullable=False)
    pathway_output_variant = Column(Float, nullable=False)
    percent_change = Column(Float, nullable=False)
    interpretation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    variant = relationship("Variant", back_populates="simulation_runs")
