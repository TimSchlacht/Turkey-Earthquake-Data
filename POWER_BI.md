# Power BI integration

Import the CSV files from one completed run directory. Demo exports contain synthetic data.
The notebook does not modify the existing PBIX or deploy an Azure database.

## Model grain and relationships

Use single-direction, one-to-many relationships:

- dim_date[date_key] → fact_earthquake[date_key]
- dim_province[province_id] → fact_earthquake[province_id]
- fact_earthquake[event_id] → fact_event_facility[event_id]
- dim_facility[facility_id] → fact_event_facility[facility_id]

Keep the facility province as an attribute initially. Adding a second active province
filter path through facilities and events would make the intended filtering ambiguous.
dim_district is an optional reference table; event district text has not been joined
to district IDs. Do not join it using names alone.

This is an event fact with date/geography dimensions plus an event–facility bridge.
The bridge currently covers ONE selected event, documented in manifest.json. Do not
interpret missing event–facility rows as zero exposure for all other earthquakes.

## Power Query example

Create a Text parameter named ExportFolder pointing to one run directory. This query
demonstrates explicit typing and renaming, rather than relying on Excel type inference.

```powerquery
let
    Source = Csv.Document(File.Contents(ExportFolder & "/fact_earthquake.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {
        {"event_id", type text}, {"event_time_utc", type datetimezone},
        {"date_key", Int64.Type}, {"province_id", Int64.Type},
        {"latitude", type number}, {"longitude", type number},
        {"magnitude", type number}, {"depth_km", type number}
    }, "en-US"),
    Named = Table.RenameColumns(Typed, {{"location", "Source location description"}})
in
    Named
```

Import dim_date[date] as Date and mark dim_date as a date table. Import IDs using matching
types at both sides of each relationship. In dim_facility, latitude/longitude are decimal
numbers, verified_on is Date, and is_synthetic is True/False. Display coordinate_quality.

## DAX measures

Create a disconnected numeric parameter table ScreeningRadius with a [km] column.
100 km is a demonstration choice, not an official hazard or damage threshold.

```dax
Recorded events = COUNTROWS(fact_earthquake)

Mapped facilities = DISTINCTCOUNT(dim_facility[facility_id])

Facilities in screening radius =
VAR RadiusKm = SELECTEDVALUE(ScreeningRadius[km], 100)
VAR PairCount = COUNTROWS(fact_event_facility)
RETURN
IF(
    NOT HASONEVALUE(fact_earthquake[event_id]) || PairCount = 0,
    BLANK(),
    COALESCE(
        CALCULATE(
            DISTINCTCOUNT(fact_event_facility[facility_id]),
            KEEPFILTERS(fact_event_facility[distance_km] <= RadiusKm)
        ), 0
    )
)

Share of mapped facilities in radius =
DIVIDE([Facilities in screening radius], [Mapped facilities])
```

Use a single-select event slicer. These M/DAX snippets are handoff code, not verified in
Power BI Desktop in this environment. Confirm filter behavior there before publication.
Treat magnitude types separately; do not describe catalogue counts as earthquake risk.
