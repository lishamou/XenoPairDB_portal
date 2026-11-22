# Data dictionary and interpretation

## Species and identifiers

Porcine records refer to *Sus scrofa* (NCBI Taxon 9823); human sequences refer to *Homo sapiens* (9606). Public functional source data separately identify human and cynomolgus-monkey serum. No genomic coordinates are remapped in these protein-level analyses. Current identifier sensitivity uses the cached UniProtKB release 2026_03 records; archived identifiers and sequence versions remain explicit.

An axis is defined by porcine molecule, human partner/response, direction and functional endpoint, together with its source. `pair_id` is a display identifier and must not be joined across historical releases without this molecular context. `stable_axis_id` is a hash-based identity key. A gene pair alone cannot establish direction or endpoint equivalence.

## Publication names and original schema

| Article term | Original input/result field | Meaning |
|---|---|---|
| ISI (stored-score scenario) | `ISI_v2` or `legacy_stored` | Stored catalogue score, including documented exceptions. |
| Earlier stored intermediate | `ISI` in raw catalogue | Historical intermediate; **not** the final stored score called ISI in the article. Do not substitute this raw column for `ISI_v2`. |
| General-formula scenario | `formula_sequence_available`, `formula_mixed3` or explicit scenario label | A calculated sensitivity, distinct from the stored-score scenario. |
| Antigen-priority score (fixed catalogue) | `antigenicity_v2` | Frozen predictor for public-proteomics comparisons. |
| Antigen-priority rank | `rank_v2` | Frozen catalogue rank; rank missing means ineligible. |
| Recalculated reference-set score | `combined` | Equal-weight percentile reconstruction within 4,122 eligible proteins; related but not identical to the fixed predictor. |

These aliases change publication wording only. Original column names and bytes are retained to preserve executable provenance.

## Axis scores and masks

`identity` and `iface_id` are percentages, not fractions. Divergence is 100 minus percent identity; mixed divergence averages available sequence/interface divergence. Evidence, functional severity and expression weights are annotation-based multipliers, not measured intervention effects. CFH stored score 0.3 and general multiplicative candidate 11.4 remain distinct. `NA`, blank or missing numerical cells are unavailable, not zero/compatible. Control severity is defined as zero, making severity-containing AUROC against these labels circular.

Each donor–axis `mask` is 0 or 1 for reported direct genetic targeting. `T`, `A`, `R` denote total, addressed and residual score on the stated common evaluable set, with T=A+R before rounding. Coverage is A/T when T is nonzero, otherwise unavailable. Count coverage and weighted coverage have separate denominators. A no-divergence product has different units from a divergence-weighted score. Hypothetical parameter intervals are sensitivity intervals, not clinical confidence intervals.

## Candidate, proteomic and functional data

Tier-2 rows are molecular interaction records; reciprocal rows are not independent gene discoveries. The 1,407 rows comprise 1,348 unique unordered pairs. N-X-S/T and N-X-C counts are sequence features, not glycan occupancy.

Liu peptide rows retain source accessions, group membership, supplied fold changes, intensity availability and mapping reasons. PK and E are supplied experimental and control intensity fields, not independent serum donors. Shared/ambiguous peptides are excluded under the stated rules; missing controls are never filled with zero. M0 is primary mapping; M1–M5 are explicitly post hoc identifier sensitivities. Primary association uses 6 proteins, the expanded same-gene observed-control comparison 7. Score direction and labels are unchanged.

Anand workbook coordinates, cell-source IDs, genotype, serum species, endpoint and duration identify each observation. Cell sources are the inference units; technical wells are not additional biological samples. C3b uses thousand MFI units; cytotoxicity uses percentages and differences use percentage points. CDC denotes complement-dependent cytotoxicity; RI denotes PERV inactivation. Welch intervals and exact tests use different assumptions; all 18 contrasts have Holm-adjusted p=1.00.

Nanno values are processed normalized log2 signals for 408 array components, 5 monkeys and 2 isotypes. The single supplied matrix has 4 missing values; its sampling timepoint remains unresolved, so no pre/post effect is inferred.

## Structure and uncertainty

PDB/AlphaFold files are template and predicted-monomer inputs. Raw/filtered Cα fits, retained residues, pLDDT and heavy-atom residue contacts are separate diagnostics. Main contacts use 5 Å; 8 Å is a sensitivity. These geometric comparisons do not measure affinity or signaling. Protein-bootstrap and dependency-proxy intervals condition on available selected data; publication/shared-family dependence is not fully eliminated. Multiple-testing families are kept separate and identified in result tables.

`TABLE_SCHEMAS.tsv` enumerates paths, row counts and exact fields for every archived TSV. `ANALYSIS_INDEX.tsv` links manuscript topics to the executable stages and outputs.
