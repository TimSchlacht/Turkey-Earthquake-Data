
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





SELECT 
    province,
    COUNT(*) AS quake_count
FROM Earthquake_Data
where province is not null 
GROUP BY province
ORDER BY quake_count DESC;

province	  quake_count
Kahramanmaras	24400
Malatya	        21546
Mugla	        13719
Izmir	       13588
Adiyaman	    7250
Adana	        6193
Elazig	        4160
Hatay	        4039
Aydin	        3876
