# From SNPs to Pathways

**Integration of functional effects of sequence variations on models of cell signalling pathways.**

A full-stack web application that takes a genetic variant (SNP), predicts its functional
impact on its protein, and runs that effect through a computational model of a real
signalling pathway — producing a quantitative, reproducible comparison of normal vs.
variant pathway activity.

---

## Table of contents

1. [Problem statement](#problem-statement)
2. [Motivation](#motivation)
3. [Objectives](#objectives)
4. [Biology background](#biology-background-plain-language)
5. [Relationship to prior work](#relationship-to-prior-work)
6. [System architecture](#system-architecture)
7. [Data sources](#data-sources)
8. [Functional workflow](#functional-workflow)
9. [Mathematical model](#mathematical-model)
10. [Technology stack](#technology-stack)
11. [Installation](#installation)
12. [Running the backend](#running-the-backend)
13. [Running the frontend](#running-the-frontend)
14. [Running the tests](#running-the-tests)
15. [API documentation](#api-documentation)
16. [Limitations](#limitations)
17. [Future work](#future-work)
18. [References](#references)

---

## Problem statement

Single nucleotide polymorphisms (SNPs) are the most common form of genetic variation
between individuals. Databases like ClinVar and tools like SIFT/PolyPhen can tell you
*whether* a variant is likely damaging to its protein — but that information sits in
isolation. It doesn't say what happens next: how a change to one protein ripples through
the signalling network that protein belongs to, and what that means for the cell's
behaviour downstream.

## Motivation

Most student bioinformatics projects either (a) build a variant lookup/database viewer,
or (b) build a static pathway diagram viewer. Neither integrates the two. The genuinely
interesting — and harder — problem is connecting them: taking a variant's predicted
functional effect and actually propagating it through a pathway model to produce a
quantitative, before/after comparison.

## Objectives

- Accept a variant identifier (rsID) and retrieve real variant information where possible
- Predict or retrieve the variant's functional impact (SIFT/PolyPhen/ClinVar, or a
  documented fallback estimate when real data isn't available)
- Map the affected protein onto a node in a real signalling pathway
- Computationally propagate the variant's effect through that pathway
- Visualize the pathway interactively, with the affected node highlighted
- Quantify and visualize the difference between normal and variant pathway output
- Generate a plain-language interpretation of the result, clearly labeled as a
  computational prediction rather than a claim of biological fact

## Biology background (plain language)

```
DNA  →  Gene  →  Protein  →  Signalling pathway  →  Cellular response
```

- **DNA variant**: a single letter of your DNA differs from the reference sequence.
- **Gene**: the variant sits inside a gene — the instructions for building one protein.
- **Protein**: the gene's protein may fold or function slightly differently as a result.
- **Signalling pathway**: that protein is one link in a chain of proteins that relay
  a signal from outside the cell to inside it — like a relay race, or a row of
  dominoes, each one activating (or sometimes inhibiting) the next.
- **Cellular response**: a change partway down that chain can change what the cell
  does at the end — grow, divide, or something else entirely.

This project models the middle three steps computationally: given a variant's effect on
one protein, how much does that change the pathway's final output?

## Relationship to prior work

This project's title and framing are a direct nod to:

> Bauer-Mehren A, Furlong LI, Rautschka M, Sanz F. **"From SNPs to pathways: integration
> of functional effect of sequence variations on models of cell signalling pathways."**
> *BMC Bioinformatics.* 2009;10(Suppl 8):S6. PMID: [19758470](https://pubmed.ncbi.nlm.nih.gov/19758470/)

That paper's contribution is a **data-integration and annotation strategy**: it gathers
mutation/variant annotations from UniProt, maps them to OMIM disease associations and GO
terms, and generates Cytoscape node-attribute files so the annotated network can be
browsed in desktop Cytoscape. It does not implement a dynamic simulation of activity
propagating through the network.

This project shares the same core framing (variant → gene → protein → pathway) but
diverges methodologically:

| | Bauer-Mehren et al. (2009) | This project |
|---|---|---|
| Pathway topology source | Reactome / BioModels (BioPAX / SBML) | Manually curated from standard pathway diagrams |
| Annotation depth | UniProt variants, OMIM, GO terms via NER | SIFT / PolyPhen / ClinVar via MyVariant.info |
| Output | Cytoscape node-attribute files (desktop browsing) | Interactive web dashboard |
| Computation | Annotation + visualization only | Annotation **plus** a quantitative normal-vs-variant propagation simulation |

In short: their paper is deeper on data integration and stops at annotation; this
project is shallower on annotation but adds an actual computational propagation model
on top, delivered as a live web app rather than a desktop Cytoscape session.

## System architecture

```
┌─────────────────────────────┐
│         FRONTEND             │
│   React + Vite + Tailwind    │
│   React Flow · Recharts      │
└──────────────┬────────────────┘
               │ HTTPS/JSON
┌──────────────▼────────────────┐
│          BACKEND               │
│        FastAPI (Python)        │
│                                 │
│  API Layer (routers)           │
│  Variant Service                │──┐
│   (provider chain + caching)    │  │  MyVariant.info
│  Functional Effect Service      │◄─┘  (dbSNP/ClinVar/dbNSFP)
│  Pathway Graph Builder          │
│  Propagation Engine             │
│  SQLite (SQLAlchemy)             │
└─────────────────────────────────┘
```

Every biology-fetching service follows a **provider interface**: a live provider and a
demo/local provider implement the same contract, so the rest of the app never knows or
cares which one actually answered a request. This is what makes the app work with zero
network access.

## Data sources

| Data | Source | Real or modelled |
|---|---|---|
| Variant position, alleles, consequence | MyVariant.info (aggregates dbSNP) | Real, when reachable |
| SIFT / PolyPhen scores | MyVariant.info (aggregates dbNSFP) | Real, when available for the variant |
| ClinVar clinical significance | MyVariant.info (aggregates ClinVar) | Real, when available |
| Protein names/descriptions | Curated demo dataset (UniProt-style) | Modelled for the MVP — not a live UniProt call yet |
| Pathway topology (MAPK/ERK) | Hand-digitized from standard textbook pathway diagrams | Real topology, manually curated (not pulled from Reactome/BioModels) |
| Edge weights | — | **Modelled** — documented simplification, not a measured biological constant |
| Perturbation factor when no real prediction exists | Consequence-type heuristic (see [Mathematical Model](#mathematical-model)) | **Modelled**, explicitly flagged `is_modelled: true` |

Every API response includes a `source` field (`"demo"` or `"myvariant"`) and, for
functional-effect data, an `is_modelled` flag plus a plain-language `note` explaining
exactly what evidence produced the result.

## Functional workflow

```
Enter SNP
   ↓
Look up variant (live API → demo fallback)
   ↓
Interpret functional effect (ClinVar → SIFT/PolyPhen → consequence heuristic)
   ↓
Resolve affected pathway node (gene symbol → protein → node)
   ↓
Build pathway graph (networkx)
   ↓
Run normal pass (no perturbation)
   ↓
Run variant pass (perturbation applied at the affected node, propagated downstream)
   ↓
Compute percent change + generate interpretation
   ↓
Render: variant info, protein, functional effect, pathway graph, simulation toggle,
        comparison chart, interpretation
```

## Mathematical model

The pathway is a directed acyclic graph. For each node, in topological order:

- **No predecessors** (e.g. Growth Factor): `activity = baseline_activity` (default 1.0)
- **One or more predecessors**: for each predecessor `p` with edge weight `w`:
  - activation: `contribution = activity[p] * w`
  - inhibition: `contribution = activity[p] * (1 - w)`
  - `activity = average(all contributions)` — a documented simplification for nodes
    with multiple parents (see [Limitations](#limitations))
- **Perturbation**: applied by multiplying the affected node's *computed* activity by
  a `perturbation_factor`, after its normal contribution from predecessors is computed.
  This means the perturbation still respects upstream pathway state and then propagates
  forward through every downstream node exactly as normal.

The **normal** run is this same computation with every perturbation factor at 1.0.

```
percent_change = (variant_output − normal_output) / normal_output × 100
```

`perturbation_factor` itself comes from `FunctionalEffectService`, in priority order:
1. **ClinVar** significance, if present (e.g. "Pathogenic" → 0.4)
2. **SIFT + PolyPhen** predictions, if ClinVar has nothing
3. **Consequence-type heuristic** (e.g. `stop_gained` → 0.15), always flagged as modelled

Worked example (BRAF V600E, an activating mutation, applied at the RAF node):

```
Normal pathway output:  0.561
Variant pathway output: 1.010
Change:                 +80.0%
```

## Technology stack

**Frontend**: React 18, Vite, Tailwind CSS, React Flow (pathway graph), Recharts (comparison chart), React Router
**Backend**: Python, FastAPI, SQLAlchemy, networkx, httpx, pandas/numpy (available for future analysis features)
**Database**: SQLite
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)

## Installation

```bash
git clone <this-repo>
cd snp-pathway-project
```

## Running the backend

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a virtualenv
python -m app.database.seed_demo_data
uvicorn app.main:app --reload
```

The API is now live at `http://localhost:8000`. Interactive docs (Swagger UI) are at
`http://localhost:8000/docs`.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. Try `http://localhost:5173/analyze/demo-001` directly
to jump straight to the BRAF V600E demo.

## Running the tests

```bash
# Backend — 48 tests
cd backend
pytest

# Frontend — 14 tests
cd frontend
npm run test
```

## API documentation

Full interactive documentation is auto-generated by FastAPI at `/docs` once the backend
is running. Summary:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/variant/{variant_id}` | Core variant info (rsID or demo key) |
| GET | `/api/variant/{variant_id}/functional-effect` | SIFT/PolyPhen/ClinVar + computed impact |
| GET | `/api/pathway/{pathway_id}` | Pathway graph (nodes + edges) |
| POST | `/api/simulate` | Runs normal-vs-variant propagation |
| GET | `/api/demo/variants` | List of demo variants |
| GET | `/api/demo/pathways` | List of demo pathways |

## Limitations

- **Single pathway**: only MAPK/ERK is modelled. Multi-pathway support is architected
  for (the DB schema supports many pathways) but only one is seeded.
- **Multi-parent averaging**: nodes with more than one predecessor combine incoming
  contributions by simple average — a real simplification, not biological fact. This
  doesn't affect MAPK (a linear chain) but would matter for a branching pathway.
- **Pathway topology is hand-curated**, not parsed from Reactome/BioModels — see
  [Relationship to prior work](#relationship-to-prior-work).
- **Protein descriptions are not pulled from a live UniProt API** — they're part of
  the curated demo dataset for the MVP.
- **Edge weights and perturbation-factor mappings are our own modelled simplifications**,
  clearly labeled as such throughout the UI (`is_modelled` flag), never presented as
  measured biological constants.
- **Direction overrides** (e.g. BRAF V600E being activating rather than loss-of-function)
  are a manual, documented judgment call per known variant — not something ClinVar/SIFT/
  PolyPhen encode structurally.
- Live lookups depend on MyVariant.info being reachable; this was not verifiable from the
  development sandbox used to build this project (see note in the codebase), so confirm
  connectivity in your actual deployment environment.

## Future work

- Multiple pathways (PI3K-AKT, JAK-STAT) and multi-pathway comparison
- Live UniProt integration for protein descriptions
- Reactome/BioModels-sourced pathway topology instead of manual curation
- More sophisticated propagation models (ODE-based, or a proper multi-parent
  integration rule instead of simple averaging)
- Multiple-SNP batch analysis and downloadable PDF reports
- Confidence scoring and network centrality-based variant prioritization

## References

1. Bauer-Mehren A, Furlong LI, Rautschka M, Sanz F. From SNPs to pathways: integration
   of functional effect of sequence variations on models of cell signalling pathways.
   *BMC Bioinformatics.* 2009;10(Suppl 8):S6. PMID: 19758470.
2. MyVariant.info — variant annotation aggregation API.
3. NCBI dbSNP, ClinVar.
4. SIFT, PolyPhen-2 — variant effect prediction tools (accessed via dbNSFP/MyVariant.info).
5. Standard MAPK/ERK signalling pathway topology (textbook reference).
