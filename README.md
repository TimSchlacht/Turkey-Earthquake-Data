Turkey Earthquake Analytics and Business Continuity
An independent Migros Türkiye case study
View the existing Power BI dashboard
Project status: The existing dashboard explores earthquake activity in Turkey. The business-continuity case study described below is the next development phase.
Business context
Migros Türkiye operates a geographically distributed retail and logistics network. Its public risk disclosures identify backup storage, alternative logistics plans, and geographically dispersed operations as measures for maintaining business continuity. Source: Migros risk disclosures
This project explores how earthquake data and publicly available facility locations could support an initial assessment of geographic exposure.
Business problem
Following an earthquake, an operations team needs to identify locations that may require status checks and understand where facilities are concentrated.
The central question is:
Which publicly identified Migros locations fall within a selected earthquake screening area, and how can that information support operational follow-up?

The proposed users are business-continuity analysts, regional operations managers, and supply-chain planners. These are case-study assumptions, not requirements provided by Migros.
Proposed analytical capabilities
- Explore historical earthquakes by date, location, magnitude, and depth.
- Map verified public store and distribution-center locations.
- Calculate distances between facilities and recorded earthquake epicenters.
- Identify facilities within a user-selected screening radius.
- Summarize the number and proportion of mapped facilities within that area.
- Show location coverage, coordinate accuracy, and data freshness.
- Add province-level population context where suitable data is available.
Distance-based screening identifies locations for further investigation. It does not establish damage, structural safety, or operational availability.
Expected business value
The intended benefit is a repeatable, transparent starting point for operational assessment:
- Reduce manual work combining earthquake records and facility locations.
- Make geographic concentration easier to understand.
- Provide consistent information for initial status-check briefings.
- Help users distinguish verified facts from missing or uncertain information.
Benefits will be evaluated through refresh performance, data-quality results, and timed analytical tasks. Financial savings and avoided losses will not be claimed without evidence.
Planned technology stack
Technology	Purpose
Python	Data ingestion, validation, geographic processing, and pipeline automation
AFAD earthquake data	Recorded event locations, timestamps, magnitudes, and depths
Public Migros information	Verified facility names, types, and addresses, subject to availability
TÜİK data	Population context with clearly identified reference years
Azure SQL Database	Storage of validated data and analytical tables
Power Query	Report preparation and transformations
Power BI and DAX	Interactive maps, measures, filtering, and operational summaries


Proposed data model
The model will separate earthquake events from facilities and preserve the grain of each dataset:
- Earthquake events: one record per source event.
- Facilities: one record per verified public location.
- Date and geography dimensions: consistent filtering and geographic classification.
- Event–facility distances: calculated relationships supporting proximity analysis.
- Population: geographic statistics stored with their reference year.
Actual supply relationships between stores and distribution centers will only be included if supported by reliable data.
Planned dashboard pages
1. Earthquake overview — event distribution, magnitude, depth, and time filters.
2. Facility exposure — selected earthquake, screening radius, and facilities requiring further investigation.
3. Network concentration — distribution of mapped facilities across regions.
4. Data quality — source coverage, missing values, duplicate checks, location confidence, and refresh status.
Data sources
- AFAD earthquake API
- TÜİK statistics portal
- Migros corporate information
Source availability, permitted access, geographic coverage, and update frequency will be verified during implementation.
Scope and limitations
This is an independent portfolio project using public information. It is not affiliated with or endorsed by Migros.
The project does not predict earthquakes, estimate building damage, or replace official emergency guidance. Facility revenue, inventory, capacity, and delivery dependencies are outside the initial scope unless reliable data becomes available. Any later synthetic scenarios will be explicitly labeled.

