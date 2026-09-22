# XenoPairDB Release 3.4-FINAL API

This is a static, versioned JSON API generated from the R3.4-FINAL canonical freeze (A+ recalibration: 59 direct + 4 disputed + 12 compatibility controls; T = 1068.6; Protocol A only). The authoritative manifest is [`release.json`](release.json). Each endpoint includes its source path, row count, columns and SHA-256 checksum.

## Endpoints

See the portal README for the complete endpoint table. Dataset-specific JSON Schemas are in [`schemas/`](schemas/). TSV downloads are in [`../downloads/`](../downloads/).

Example:

```bash
curl -s ./api/atlas.json | jq '.records[0]'
curl -s ./api/release.json | jq '.files[] | {dataset,record_count,sha256}'
```

The `atlas` QC field is named `qc_flag`. Empty strings are the only missing-value representation. Empty strings are the only missing-value representation. The API is intended for bulk retrieval and reproducible local analysis; a deployment may add a domain-specific query layer without changing these frozen files.
