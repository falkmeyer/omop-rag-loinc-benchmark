# Retrieve-and-Rerank vs. OHDSI Usagi for LOINC Mapping

Code and analysis accompanying the paper

> Meyer-Eschenbach F\*, McCaughey T\*, Kohler S, Näher AF. *Beyond String Matching: Benchmarking a
> Retrieve-and-Rerank LLM Pipeline Against OHDSI Usagi for LOINC Mapping.* Submitted to MIE 2027.
> (\*shared first authorship)

The study maps the 753 laboratory items of the MIMIC-III `D_LABITEMS` dictionary to LOINC concepts of the OMOP
Standardized Vocabularies and compares a two-stage pipeline (Vertex AI `text-embedding-005` retrieval of five
candidates + Gemini 2.0 Flash reranking) against OHDSI Usagi, at three nested evaluation levels:

Three predictions ŷ are evaluated per item: Usagi (ŷ_Usagi), retrieval alone (ŷ_Ret) and the full pipeline
after reranking (ŷ_RAG).

| Level | Condition between prediction ŷ and reference code y |
|-------|------------------------------------------------------|
| L1    | ŷ = y                                                |
| L2    | L1, or ŷ is the direct parent of y                   |
| L3    | L2, or ŷ and y share a direct parent (siblings)      |

Parents come from the LOINC multiaxial hierarchy (LOINC 2.82).

## Repository structure

```
external/rag-pipeline/    submodule: retrieval and reranking pipeline (T. McCaughey, bachelor thesis, HPI 2026)
external/evaluation/      submodule: raw pipeline and Usagi outputs and the original thesis evaluation
analysis/final_metrics.py all results reported in the paper
analysis/fetch_parents.py retrieves direct LOINC parents from the HL7 FHIR terminology server tx.fhir.org
analysis/loinc_parents_2.82.json  cached result of fetch_parents.py (LOINC 2.82)
figures/make_figure1.py   Figure 1 of the paper
```

## Reproducing the paper results

```bash
git clone --recurse-submodules https://github.com/falkmeyer/omop-rag-loinc-benchmark.git
pip install -r requirements.txt
python analysis/final_metrics.py external/evaluation analysis/loinc_parents_2.82.json
python figures/make_figure1.py
```

`final_metrics.py` only reads the raw outputs in `external/evaluation` (Usagi export, retrieval top-5, reranking
choices). To refresh the hierarchy cache, delete it and run
`python analysis/fetch_parents.py external/evaluation analysis/loinc_parents_2.82.json`.

## Differences from the thesis evaluation

The paper re-analyses the raw outputs of the thesis. The scripts in `external/evaluation` assign reference codes
and pair Usagi with pipeline results by laboratory label; since many MIMIC-III labels occur for several fluids,
this mixes up items. `final_metrics.py` therefore

* assigns reference codes and pairs both systems by `ITEMID` (581 items evaluable for both systems),
* defines L1 as strict code identity, without the code normalisation table used in the thesis,
* takes hierarchy relations from the LOINC multiaxial hierarchy instead of the OMOPHub API.

The numbers in the paper therefore differ from those in the thesis.

## Data and licences

* MIMIC-III is available from [PhysioNet](https://physionet.org/content/mimiciii/1.4/) under a data use agreement.
  Users of this repository must hold their own credentialed access.
* The OMOP Standardized Vocabularies are available from [Athena](https://athena.ohdsi.org).
* This material contains content from LOINC® (http://loinc.org). LOINC is copyright © Regenstrief Institute, Inc.
  and the LOINC Committee and is available at no cost under the license at http://loinc.org/license.
* Code in this repository (outside `external/`) is released under the MIT License. The submodules keep their own
  terms.
