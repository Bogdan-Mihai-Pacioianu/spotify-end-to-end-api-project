# Spotify ETL Project Documentation

### Overview
This project implements a complete ETL (Extract, Transform, Load) pipeline in Databricks for extracting, processing, and analyzing personal listening data from the Spotify API. The goal is to transform raw API data into aggregated tables (KPIs), answering questions like:
- Who are my favorite artists?
- What is my dominant music genre?
- When do I listen to the most music during the day?

The project is built on the Medallion architecture (Bronze, Silver, Gold) and implemented entirely in Unity Catalog.

---

### Pipeline Architecture
The pipeline is divided into three logical stages, corresponding to Databricks notebooks and schemas in Unity Catalog.

1. **Bronze Layer (Raw Data)**
   - Extracts data from the Spotify API (listening history, playlists, tracks, artists).
   - Loads raw 1:1 data into Delta tables.

2. **Silver Layer (Transformed Data)**
   - Reads raw data from the Bronze layer.
   - Cleans, standardizes, de-duplicates, and models the data into a Star Schema.

3. **Gold Layer (Aggregated Data)**
   - Reads modeled data from the Silver layer.
   - Aggregates data into business-ready tables for analysis.

---

### Setup Instructions
1. **Spotify Developer Configuration**
   - Create an app in Spotify Developer Dashboard.
   - Obtain `Client ID` and `Client Secret`.
   - Add the following URI in "Redirect URIs": `http://localhost:8888/callback`.

2. **Obtain `refresh_token`**
   - Use a manual script or hybrid notebook to obtain a refresh token. This is required for authentication.

3. **Databricks Secrets Configuration**
   - Store your keys securely using Databricks Secrets.
     ```bash
     databricks secrets create-scope --scope spotify_secrets
     databricks secrets put --scope spotify_secrets --key "user" --string-value "YOUR_CLIENT_ID_HERE"
     databricks secrets put --scope spotify_secrets --key "client_secret" --string-value "YOUR_CLIENT_SECRET_HERE"
     databricks secrets put --scope spotify_secrets --key "refresh-token" --string-value "YOUR_REFRESH_TOKEN_HERE"
     ```

4. **Cluster Configuration**
   - Install the `requests` library on the cluster where the notebooks will run.

---

### Data Model
The pipeline creates the following structure in Unity Catalog:

**Catalog:** `spotify_etl`
- **Bronze Schema:**
  - `bronze_play_history`: Listens (raw JSON).
  - `bronze_playlists`: Playlist metadata.
  - `bronze_playlist_tracks`: Link table for playlists and tracks.
  - `bronze_tracks`: Track metadata (popularity, release date).
  - `bronze_artists`: Artist metadata (genres, followers).

- **Silver Schema:**
  - `fct_plays`: Fact table of cleaned listens.
  - `dim_tracks`: Track dimension (deduplicated).
  - `dim_artists`: Artist dimension.
  - `dim_playlists`: Playlist dimension.
  - `dim_time`: Time dimension (with enriched attributes).

- **Gold Schema:**
  - `gold_user_listening_summary`: Key KPIs (e.g., total minutes, favorite artist).
  - `gold_top_tracks`: Track rankings.
  - `gold_top_artists`: Artist rankings.
  - `gold_genre_trends`: Genre trends over time.
  - `gold_listening_patterns`: Listening patterns by time and day.

---

### Execution Instructions
1. **Manual Execution**
   - Run the notebooks in the following order:
     - `01_Bronze_Ingestion`: Extracts raw data from the API.
     - `02_Silver_Transformation`: Transforms and models data.
     - `03_Gold_Aggregation`: Aggregates data into KPIs.

2. **Automated Execution**
   - Configure a Databricks Job with three tasks:
     - Task 1: `01_Bronze_Ingestion`
     - Task 2: `02_Silver_Transformation` (depends on Task 1).
     - Task 3: `03_Gold_Aggregation` (depends on Task 2).

---

### Analysis and Usage
- The final data is available in the `spotify_etl.gold` schema.
- It can be used to:
  - Create dashboards in Databricks SQL.
  - Connect to external BI tools (e.g., Power BI, Tableau).
  - Run ad-hoc queries for insights.

Example Query:
```sql
SELECT
  genre,
  SUM(total_plays) AS total_plays
FROM
  spotify_etl.gold.gold_genre_trends
GROUP BY
  genre
ORDER BY
  total_plays DESC
LIMIT 10;
```