"""
Seeds the SQLite database with:
  1. The demo variants (data/variants/demo_variants.json)
  2. The MAPK pathway definition (data/pathways/mapk_pathway.json)

Run this once after creating a fresh database:
    python -m app.database.seed_demo_data

It's safe to re-run: it clears existing demo data first, so you always
get a clean, consistent seed.
"""
import json
import os
import sys

# Allow running this file directly (python app/database/seed_demo_data.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.db import Base, engine, SessionLocal
from app.models.models import (
    Variant, FunctionalEffect, Protein, Pathway, PathwayNode, PathwayEdge
)

# Paths to the demo data JSON files (in the top-level data/ folder)
BACKEND_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..", "..")))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
VARIANTS_JSON = os.path.join(PROJECT_ROOT, "data", "variants", "demo_variants.json")
MAPK_JSON = os.path.join(PROJECT_ROOT, "data", "pathways", "mapk_pathway.json")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def seed_pathway(db, pathway_data: dict) -> Pathway:
    """Insert (or replace) a pathway and its nodes/edges."""
    existing = db.query(Pathway).filter_by(pathway_key=pathway_data["pathway_id"]).first()
    if existing:
        db.query(PathwayEdge).filter_by(pathway_id=existing.id).delete()
        db.query(PathwayNode).filter_by(pathway_id=existing.id).delete()
        db.delete(existing)
        db.commit()

    pathway = Pathway(
        pathway_key=pathway_data["pathway_id"],
        name=pathway_data["name"],
        description=pathway_data.get("description"),
        terminal_node_key=pathway_data.get("terminal_node"),
    )
    db.add(pathway)
    db.commit()
    db.refresh(pathway)

    for node in pathway_data["nodes"]:
        protein_id = None
        uniprot_id = node.get("protein_uniprot_id")
        if uniprot_id:
            protein = db.query(Protein).filter_by(uniprot_id=uniprot_id).first()
            if protein:
                protein_id = protein.id

        db.add(PathwayNode(
            pathway_id=pathway.id,
            node_key=node["node_key"],
            label=node["label"],
            protein_id=protein_id,
            baseline_activity=node.get("baseline_activity", 1.0),
            position_x=node.get("position", {}).get("x"),
            position_y=node.get("position", {}).get("y"),
        ))

    for edge in pathway_data["edges"]:
        db.add(PathwayEdge(
            pathway_id=pathway.id,
            source_node_key=edge["source"],
            target_node_key=edge["target"],
            weight=edge["weight"],
            interaction_type=edge.get("interaction_type", "activation"),
        ))

    db.commit()
    print(f"  Seeded pathway '{pathway.pathway_key}' "
          f"({len(pathway_data['nodes'])} nodes, {len(pathway_data['edges'])} edges)")
    return pathway


def seed_proteins(db, variants_data: dict):
    """Extract unique proteins referenced by demo variants and insert them."""
    seen = set()
    count = 0
    for key, v in variants_data.items():
        if key.startswith("_"):
            continue
        protein = v.get("protein")
        if not protein or protein["uniprot_id"] in seen:
            continue
        seen.add(protein["uniprot_id"])

        existing = db.query(Protein).filter_by(uniprot_id=protein["uniprot_id"]).first()
        if existing:
            continue

        db.add(Protein(
            uniprot_id=protein["uniprot_id"],
            name=protein["name"],
            gene_symbol=v.get("gene_symbol"),
            simple_description=protein.get("simple_description"),
        ))
        count += 1
    db.commit()
    print(f"  Seeded {count} proteins")


def seed_variants(db, variants_data: dict):
    count = 0
    for key, v in variants_data.items():
        if key.startswith("_"):
            continue

        existing = db.query(Variant).filter_by(rsid=v["rsid"]).first()
        if existing:
            db.query(FunctionalEffect).filter_by(variant_id=existing.id).delete()
            db.delete(existing)
            db.commit()

        variant = Variant(
            rsid=v["rsid"],
            chromosome=v.get("chromosome"),
            position=v.get("position"),
            ref_allele=v.get("ref_allele"),
            alt_allele=v.get("alt_allele"),
            gene_symbol=v.get("gene_symbol"),
            consequence=v.get("consequence"),
            amino_acid_change=v.get("amino_acid_change"),
            source=v.get("source", "demo"),
            raw_response_json=json.dumps(v),
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)

        fe = v.get("functional_effect", {})
        db.add(FunctionalEffect(
            variant_id=variant.id,
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
            source=v.get("source", "demo"),
        ))
        db.commit()
        count += 1
    print(f"  Seeded {count} variants (with functional effects)")


def run():
    print("Creating tables (if they don't already exist)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Loading demo JSON files...")
        variants_data = load_json(VARIANTS_JSON)
        mapk_data = load_json(MAPK_JSON)

        print("Seeding proteins...")
        seed_proteins(db, variants_data)

        print("Seeding pathway (MAPK)...")
        seed_pathway(db, mapk_data)

        print("Seeding variants + functional effects...")
        seed_variants(db, variants_data)

        print("\nDone. Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
