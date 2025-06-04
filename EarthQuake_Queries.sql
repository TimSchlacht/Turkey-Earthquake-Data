
SELECT 
    YEAR(date) AS quake_year,
    COUNT(*) AS quake_count,
    ROUND(AVG(magnitude), 2) AS avg_magnitude
FROM Earthquake_Data
GROUP BY YEAR(date)
ORDER BY quake_year;
