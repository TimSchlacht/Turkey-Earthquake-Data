-- Run against outputs/<run>/analytics.sqlite.
-- One row per province AND magnitude type; no cross-scale magnitude average.
WITH province_activity AS (
    SELECT province_id, COALESCE(magnitude_type, 'Unknown') AS magnitude_type,
           COUNT(*) AS recorded_events,
           SUM(CASE WHEN magnitude IS NULL THEN 1 ELSE 0 END) AS missing_magnitude,
           MAX(magnitude) AS maximum_recorded_magnitude
    FROM fact_earthquake
    GROUP BY province_id, COALESCE(magnitude_type, 'Unknown')
)
SELECT p.province_name, a.magnitude_type, a.recorded_events,
       a.missing_magnitude, a.maximum_recorded_magnitude,
       DENSE_RANK() OVER (PARTITION BY a.magnitude_type ORDER BY a.recorded_events DESC) AS activity_rank
FROM province_activity a
JOIN dim_province p ON p.province_id = a.province_id
ORDER BY a.magnitude_type, activity_rank;

-- This is a proximity list, not a damage assessment. 100 km is a demo parameter.
SELECT b.event_id, f.facility_name, f.coordinate_quality, f.is_synthetic, b.distance_km
FROM fact_event_facility b
JOIN dim_facility f ON f.facility_id = b.facility_id
WHERE b.distance_km <= 100
ORDER BY b.distance_km;
