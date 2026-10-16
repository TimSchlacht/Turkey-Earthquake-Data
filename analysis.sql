-- Run against outputs/<run>/analytics.sqlite.
-- Source place labels are not province assignments.
WITH location_activity AS (
    SELECT COALESCE(location, 'Location not supplied') AS source_location,
           COALESCE(magnitude_type, 'Unknown') AS magnitude_type,
           COUNT(*) AS recorded_events,
           MAX(magnitude) AS maximum_magnitude,
           ROUND(AVG(depth_km), 1) AS average_depth_km
    FROM fact_earthquake
    GROUP BY COALESCE(location, 'Location not supplied'),
             COALESCE(magnitude_type, 'Unknown')
)
SELECT source_location, magnitude_type, recorded_events, maximum_magnitude,
       average_depth_km,
       DENSE_RANK() OVER (
           PARTITION BY magnitude_type ORDER BY recorded_events DESC
       ) AS activity_rank
FROM location_activity
ORDER BY activity_rank, maximum_magnitude DESC;

-- Optional facility screening; this is a distance list, not a damage assessment.
-- The radius is illustrative. The live query only has results if facilities are supplied.
SELECT b.event_id, f.facility_name, f.coordinate_quality, f.is_synthetic, b.distance_km
FROM fact_event_facility b
JOIN dim_facility f ON f.facility_id = b.facility_id
WHERE b.distance_km <= 100
ORDER BY b.distance_km;
