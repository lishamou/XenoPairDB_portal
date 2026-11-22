# XenoPairDB portal

An evidence-graded resource for pig–human molecular axes, candidate prioritization and donor-target coverage. This static portal uses the same frozen scientific results as the revised article.

Data and code archive: https://doi.org/10.5281/zenodo.24221712 (all versions). Scientific payload used here: https://doi.org/10.5281/zenodo.24221713 (specific archived version). This website update does not create a new Zenodo science version.

## Browse and reuse

Open index.html directly for offline browsing, or serve this complete repository with GitHub Pages. The page has no third-party scripts, fonts, analytics or network dependencies for browsing. Dataset selection, search, filters, sorting, pagination, details and filtered TSV export work offline. External source links need an internet connection.

api/ contains JSON endpoints; downloads/ contains actual TSV files. Paths inside metadata are relative to the portal root. Root-level JSON mirrors preserve existing links. API schemas describe the updated presentation; the retired priority and loso_units endpoints return status=retired and zero records. Their historical validation claims are not retained as current results.

## Rebuild the presentation

Python standard library only. From this repository run:

    python3 code/build_portal.py --source-dir source_data --template-dir code/templates --output-dir /absolute/path/to/new_portal

The output directory must not exist. Every source_data file is verified against SOURCE_MANIFEST.json before building. Rebuilding transforms and joins frozen tables for display; it does not run the underlying scientific analyses. To reproduce those analyses use the exact Zenodo science archive and its documented environment.

## Interpretation and licenses

Direct genetic targeting is not measured functional rescue. Parameter sensitivity, catalogue annotation association, reference-set enrichment, proteomic enrichment, complement deposition and cell injury are distinct endpoints. The resource supports evidence tracing and selection of follow-up assays; independent candidate experiments and clinical-outcome validation remain necessary.

User-facing field names follow the article. Original raw column names and source values are retained in source_data and in exact-source TSVs; DATA_DICTIONARY.md explains the aliases and derived display tables. Missing values are not converted to zero. No weighting, evidence or control labels were adjusted for this portal.

Code is MIT. Original project data are CC BY 4.0 subject to upstream terms; Liu-derived files retain the source CC BY-NC 4.0 restriction. DATA_LICENSE.md and THIRD_PARTY_NOTICES.md describe the source archive conditions. This repository redistributes selected tables and derived summaries, not the full upstream workbooks or literature. Cite the original studies when reusing their results.

The SHA256SUMS.txt manifest covers every delivered file except itself. Portal build date: 2026-11-18.
