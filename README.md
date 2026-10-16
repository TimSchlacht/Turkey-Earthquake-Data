# Turkey Earthquake Analytics

A compact portfolio project that turns public earthquake records into a clean, auditable dataset for SQL and Power BI exploration. The live notebook uses the USGS Earthquake Catalog API for a one-day window on 6 February 2023 (magnitude 4+, geographic rectangle around Turkey). The rectangle can include neighboring countries and sea areas, so results are not Turkey-only.

The project demonstrates API ingestion, validation, deduplication, UTC handling, dimensional modeling, SQL analysis, great-circle distance calculations, and export to CSV and SQLite. It does not predict earthquakes or establish damage, safety, or operational availability. Any facility examples are synthetic and clearly marked.

## Run in Google Colab

1. Open `Turkey_Earthquake_Analytics.ipynb` from the GitHub repository in Colab.
2. Run all cells from top to bottom. The default `MODE = "live"` retrieves the documented USGS window; internet access is required.
3. Find the exported tables and audit files under `outputs/live_<run_id>/`.

For an offline pipeline demonstration, change `MODE` in the configuration cell to `"demo"`. The notebook embeds its functions and runs without needing `pipeline.py` or local dependencies in Colab. To run locally, install `requirements.txt` and start Jupyter Lab.

## Project files

- `Turkey_Earthquake_Analytics.ipynb` — runnable walkthrough and live USGS query.
- `pipeline.py` — reusable ingestion, validation, transformation, screening, and export functions.
- `test_pipeline.py` — deterministic tests using fabricated records.
- `analysis.sql` — location and magnitude-type summaries plus an optional proximity query.
- `POWER_BI.md` — model import and dashboard layout guidance.
- `data/facilities_template.csv` — empty template for sourced facility data; not needed for the core analysis.

## Suggested dashboard

Start with event count, maximum magnitude, and date range cards; a longitude/latitude map sized by magnitude; a daily event trend; and a magnitude-versus-depth scatter plot. Add source location and magnitude type slicers. Display the query scope and note that source location text is not a province assignment.

USGS API: https://earthquake.usgs.gov/fdsnws/event/1/
