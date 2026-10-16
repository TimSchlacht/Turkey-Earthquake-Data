# Power BI handoff

Import `fact_earthquake.csv` and `dim_date.csv` from one `outputs/live_<run_id>` folder. Use Power Query to assign types explicitly: `event_time_utc` as Date/Time/Timezone, latitude/longitude/magnitude/depth as Decimal Number, and IDs as Text or Whole Number according to their source type. Keep `location` as source-provided descriptive text; it is not a province dimension.

Create a one-to-many, single-direction relationship from `dim_date[date_key]` to `fact_earthquake[date_key]`. The core dashboard works with these two tables. Other exported tables support optional analyses.

## Suggested one-page report

- KPI cards: recorded events, maximum magnitude, average depth, and date range.
- Map: longitude and latitude, point size by magnitude, tooltip with UTC time, depth, magnitude type, and source location.
- Daily trend: event count by date, with magnitude type available as a slicer.
- Scatter plot: magnitude against depth, with source location in tooltip.
- Slicers: date, magnitude type, and source location.

Keep the map title and a small note explicit: “USGS catalogue results in a 25–45°E, 35–43°N query rectangle; this includes areas outside Turkey.” Counts describe the queried catalogue and period, not future earthquake likelihood. Do not label the results as province rankings because the live USGS feed is not spatially joined to province boundaries.

The exported facility tables and radius measure are optional. They are empty in live mode unless sourced facility coordinates are added. The notebook’s demo facilities are synthetic and should be labeled as such.
