
SELECT 
    YEAR(date) AS quake_year,
    COUNT(*) AS quake_count,
    ROUND(AVG(magnitude), 2) AS avg_magnitude
FROM Earthquake_Data
GROUP BY YEAR(date)
ORDER BY quake_year;


quake_year quake_count	avg_magnitude
2020	  10987	        1.79
2021	  23758	        1.81
2022	  20997	        1.67
2023	  74509	        1.82
2024	  23431	        1.66
