# Turkey Earthquake Analytics

A rebuilt version of the original API-to-Excel notebook, demonstrating a validated data
pipeline and a proposed business-continuity use case. **Demo outputs are synthetic.**
No verified Migros facility data is included and no affiliation is implied.

## Run

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
jupyter lab Turkey_Earthquake_Analytics.ipynb
```

Run all cells in order. The default demo requires no network. The notebook embeds the
pipeline functions, so it can also be uploaded alone to a pandas/NumPy-enabled notebook
environment. Live facility input still requires the supplied CSV template.

## Files

- `Turkey_Earthquake_Analytics.ipynb`: explained, executable walkthrough.
- `pipeline.py`: reusable ingestion, validation, transformation, screening, and export functions.
- `test_pipeline.py`: deterministic tests with explicitly fabricated records.
- `analysis.sql`: CTE, dimensional join, window function, and proximity query.
- `POWER_BI.md`: relationship design and draft Power Query/DAX examples.
- `data/facilities_template.csv`: empty provenance-aware template for real facilities.

## What was fixed

The original notebook overwrote its province DataFrame with earthquake records, produced
duplicate district/province column names, made unbounded API requests without timeouts,
and exported without validating data. The rebuild preserves table grain, keys, source
provenance, invalid-record audits, latest-revision deduplication, query boundaries, and
explicit missing values. It exports separate date/geography dimensions and an event fact.

## Validation

```bash
python -m unittest -v test_pipeline.py
```

The supplied notebook was executed cell-by-cell in demo mode and the SQL result was
checked. Live AFAD access failed TLS certificate verification in the authoring environment;
it has not been bypassed. API limits and timestamp semantics still require live validation.
The v1 province API is legacy; a change in its contract should fail visibly, not silently
substitute incomplete data. Power BI snippets have not been executed in Power BI Desktop.

## Before publishing real findings

1. Verify the AFAD source timezone and request-limit behavior; set the notebook configuration.
2. Run live ingestion for a small period and reconcile it with the official catalogue.
3. Add sourced, date-stamped facility coordinates; inspect approximate matches manually.
4. Test Power BI relationships, types, slicers, and DAX measures.
5. Keep synthetic outputs separate from real outputs. Do not infer safety, damage, or
   future earthquake probability from distance or historical event counts.

SQLite is the tested local SQL backend. Azure SQL deployment, verified population data,
spatial province boundaries, and production scheduling are future work, not implemented claims.
