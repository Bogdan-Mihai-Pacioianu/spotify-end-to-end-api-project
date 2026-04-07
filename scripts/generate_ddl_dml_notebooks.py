"""Generate DDL and DML notebooks for all 16 tables."""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = "spotify_etl"
SCHEMAS = ["bronze", "silver", "gold"]

# ── Table metadata ──
BRONZE = [
    ("01_play_history", "bronze_play_history", [
        ("played_at", "STRING"), ("track_id", "STRING"), ("track_name", "STRING"),
        ("artist_id", "STRING"), ("artist_name", "STRING"), ("album_id", "STRING"),
        ("album_name", "STRING"), ("context_type", "STRING"), ("duration_ms", "BIGINT"),
    ]),
    ("02_playlists", "bronze_playlists", [
        ("playlist_id", "STRING"), ("playlist_name", "STRING"), ("owner_name", "STRING"),
        ("followers", "BIGINT"), ("total_tracks", "BIGINT"), ("description", "STRING"),
        ("snapshot_id", "STRING"),
    ]),
    ("03_playlist_tracks", "bronze_playlist_tracks", [
        ("playlist_id", "STRING"), ("track_id", "STRING"), ("track_name", "STRING"),
        ("artist_ids", "ARRAY<STRING>"), ("album_id", "STRING"), ("added_at", "STRING"),
        ("added_by", "STRING"), ("duration_ms", "BIGINT"), ("popularity", "INT"),
    ]),
    ("04_tracks", "bronze_tracks", [
        ("track_id", "STRING"), ("track_name", "STRING"), ("album_id", "STRING"),
        ("album_name", "STRING"), ("artist_id", "STRING"), ("artist_name", "STRING"),
        ("duration_ms", "BIGINT"), ("popularity", "INT"), ("explicit", "BOOLEAN"),
        ("release_date", "STRING"), ("preview_url", "STRING"),
    ]),
    ("05_artists", "bronze_artists", [
        ("artist_id", "STRING"), ("artist_name", "STRING"), ("genres", "ARRAY<STRING>"),
        ("followers", "BIGINT"), ("popularity", "INT"), ("uri", "STRING"),
    ]),
    ("06_audio_features", "bronze_audio_features", [
        ("track_id", "STRING"), ("danceability", "DOUBLE"), ("energy", "DOUBLE"),
        ("key", "INT"), ("loudness", "DOUBLE"), ("mode", "INT"),
        ("speechiness", "DOUBLE"), ("acousticness", "DOUBLE"), ("instrumentalness", "DOUBLE"),
        ("liveness", "DOUBLE"), ("valence", "DOUBLE"), ("tempo", "DOUBLE"),
        ("duration_ms", "BIGINT"), ("time_signature", "INT"),
    ]),
]

SILVER = [
    ("01_fct_plays", "fct_plays", [
        ("play_id", "STRING"), ("play_timestamp", "TIMESTAMP"), ("track_id", "STRING"),
        ("artist_id", "STRING"), ("duration_ms", "BIGINT"), ("context_type", "STRING"),
    ]),
    ("02_dim_tracks", "dim_tracks", [
        ("track_id", "STRING"), ("track_name", "STRING"), ("album_id", "STRING"),
        ("album_name", "STRING"), ("artist_id", "STRING"), ("artist_name", "STRING"),
        ("duration_ms", "BIGINT"), ("popularity", "INT"), ("explicit", "BOOLEAN"),
        ("release_date", "STRING"), ("preview_url", "STRING"),
    ]),
    ("03_dim_artists", "dim_artists", [
        ("artist_id", "STRING"), ("artist_name", "STRING"), ("genres", "ARRAY<STRING>"),
        ("followers", "BIGINT"), ("popularity", "INT"), ("uri", "STRING"),
    ]),
    ("04_dim_playlists", "dim_playlists", [
        ("playlist_id", "STRING"), ("playlist_name", "STRING"), ("owner_name", "STRING"),
        ("followers", "BIGINT"), ("total_tracks", "BIGINT"), ("description", "STRING"),
        ("snapshot_id", "STRING"),
    ]),
    ("05_dim_time", "dim_time", [
        ("play_timestamp", "TIMESTAMP"), ("hour_of_day", "INT"), ("day_of_week", "INT"),
        ("weekday_name", "STRING"), ("is_weekend", "BOOLEAN"), ("quarter", "STRING"),
        ("year", "INT"), ("month", "INT"), ("day", "INT"),
    ]),
]

GOLD = [
    ("01_user_listening_summary", "gold_user_listening_summary", [
        ("user_id", "STRING"), ("total_tracks", "BIGINT"), ("unique_artists", "BIGINT"),
        ("total_minutes", "DOUBLE"), ("favorite_artist", "STRING"), ("top_track", "STRING"),
    ]),
    ("02_top_tracks", "gold_top_tracks", [
        ("track_id", "STRING"), ("track_name", "STRING"), ("artist_name", "STRING"),
        ("play_count", "BIGINT"), ("total_minutes", "DOUBLE"), ("popularity", "INT"),
    ]),
    ("03_top_artists", "gold_top_artists", [
        ("artist_id", "STRING"), ("artist_name", "STRING"), ("total_plays", "BIGINT"),
        ("unique_tracks", "BIGINT"), ("total_minutes", "DOUBLE"), ("genres", "ARRAY<STRING>"),
    ]),
    ("04_genre_trends", "gold_genre_trends", [
        ("genre", "STRING"), ("month", "STRING"), ("total_plays", "BIGINT"),
        ("avg_popularity", "DOUBLE"), ("unique_users", "BIGINT"),
    ]),
    ("05_listening_patterns", "gold_listening_patterns", [
        ("user_id", "STRING"), ("hour_of_day", "INT"), ("weekday_name", "STRING"),
        ("total_minutes", "DOUBLE"),
    ]),
]

LAYER_TABLES = {"bronze": BRONZE, "silver": SILVER, "gold": GOLD}

# ── Bronze DML python code per table ──
BRONZE_DML = {
    "bronze_play_history": """import os, json

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/recently_played"
    if not os.path.exists(entity_path): return rows
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("items", []):
                    if not item: continue
                    track = item.get("track", {})
                    artists = track.get("artists") or []
                    artist = artists[0] if artists else {}
                    rows.append({
                        "played_at": item.get("played_at"), "track_id": track.get("id"),
                        "track_name": track.get("name"), "artist_id": artist.get("id"),
                        "artist_name": artist.get("name"), "album_id": (track.get("album") or {}).get("id"),
                        "album_name": (track.get("album") or {}).get("name"),
                        "context_type": (item.get("context") or {}).get("type"),
                        "duration_ms": track.get("duration_ms"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows).dropDuplicates(["played_at", "track_id"])
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
    "bronze_playlists": """import os, json

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/me_playlists"
    if not os.path.exists(entity_path): return rows
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("items", []):
                    pid = p.get("id")
                    if not pid: continue
                    fo = p.get("followers")
                    rows.append({
                        "playlist_id": pid, "playlist_name": p.get("name"),
                        "owner_name": (p.get("owner") or {}).get("display_name"),
                        "followers": fo.get("total") if isinstance(fo, dict) else None,
                        "total_tracks": (p.get("tracks") or {}).get("total"),
                        "description": p.get("description"), "snapshot_id": p.get("snapshot_id"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows).dropDuplicates(["playlist_id"])
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
    "bronze_playlist_tracks": """import os, json, re

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/playlist_tracks"
    if not os.path.exists(entity_path): return rows
    meta_map = {}
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.endswith("_meta.json"):
                m = re.match(r"page_(\\d+)_meta\\.json", fn)
                if m:
                    with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    pid = meta.get("playlist_id")
                    if pid: meta_map[int(m.group(1))] = pid
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                m = re.match(r"page_(\\d+)\\.json", fn)
                page_idx = int(m.group(1)) if m else None
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                page_pid = meta_map.get(page_idx)
                if page_pid is None:
                    href = data.get("href", "")
                    m2 = re.search(r"playlists/([^/]+)/tracks", href)
                    page_pid = m2.group(1) if m2 else None
                if page_pid is None: continue
                for item in data.get("items", []):
                    track = item.get("track")
                    if not track or not track.get("id"): continue
                    artist_ids = [a.get("id") for a in (track.get("artists") or []) if a.get("id")]
                    rows.append({
                        "playlist_id": page_pid, "track_id": track.get("id"),
                        "track_name": track.get("name"), "artist_ids": artist_ids,
                        "album_id": (track.get("album") or {}).get("id"),
                        "added_at": item.get("added_at"),
                        "added_by": (item.get("added_by") or {}).get("id"),
                        "duration_ms": track.get("duration_ms"), "popularity": track.get("popularity"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows)
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
    "bronze_tracks": """import os, json

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/tracks_bulk"
    if not os.path.exists(entity_path): return rows
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for track in data.get("tracks", []):
                    if not track: continue
                    artists = track.get("artists") or []
                    first = artists[0] if artists else {}
                    album = track.get("album") or {}
                    rows.append({
                        "track_id": track.get("id"), "track_name": track.get("name"),
                        "album_id": album.get("id"), "album_name": album.get("name"),
                        "artist_id": first.get("id"), "artist_name": first.get("name"),
                        "duration_ms": track.get("duration_ms"), "popularity": track.get("popularity"),
                        "explicit": track.get("explicit"), "release_date": album.get("release_date"),
                        "preview_url": track.get("preview_url"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows).dropDuplicates(["track_id"])
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
    "bronze_artists": """import os, json

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/artists_bulk"
    if not os.path.exists(entity_path): return rows
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for artist in data.get("artists", []):
                    if not artist: continue
                    fo = artist.get("followers")
                    rows.append({
                        "artist_id": artist.get("id"), "artist_name": artist.get("name"),
                        "genres": artist.get("genres"),
                        "followers": fo.get("total") if isinstance(fo, dict) else None,
                        "popularity": artist.get("popularity"), "uri": artist.get("uri"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows).dropDuplicates(["artist_id"])
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
    "bronze_audio_features": """import os, json

def collect():
    rows = []
    entity_path = f"{RAW_BASE_PATH}/audio_features_bulk"
    if not os.path.exists(entity_path): return rows
    for root, dirs, files in os.walk(entity_path):
        for fn in files:
            if fn.startswith("page_") and fn.endswith(".json") and not fn.endswith("_meta.json"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for feat in data.get("audio_features", []):
                    if not feat: continue
                    rows.append({
                        "track_id": feat.get("id"), "danceability": feat.get("danceability"),
                        "energy": feat.get("energy"), "key": feat.get("key"),
                        "loudness": feat.get("loudness"), "mode": feat.get("mode"),
                        "speechiness": feat.get("speechiness"), "acousticness": feat.get("acousticness"),
                        "instrumentalness": feat.get("instrumentalness"), "liveness": feat.get("liveness"),
                        "valence": feat.get("valence"), "tempo": feat.get("tempo"),
                        "duration_ms": feat.get("duration_ms"), "time_signature": feat.get("time_signature"),
                    })
    return rows

rows = collect()
if rows:
    df = spark.createDataFrame(rows).dropDuplicates(["track_id"])
    df.write.format("delta").mode("append").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
    print(f"Wrote {df.count()} rows to {CATALOG}.{SCHEMA}.{TABLE}")
else:
    print(f"No data for {TABLE}")
""",
}

# ── Silver DML SQL ──
SILVER_SQL = {
    "fct_plays": f"""MERGE INTO {CATALOG}.silver.fct_plays t
USING (
  SELECT DISTINCT
    sha2(concat(played_at, track_id), 256) AS play_id,
    to_timestamp(played_at) AS play_timestamp,
    track_id, artist_id, duration_ms, context_type
  FROM {CATALOG}.bronze.bronze_play_history
  WHERE track_id IS NOT NULL AND artist_id IS NOT NULL
) s ON t.play_id = s.play_id
WHEN NOT MATCHED THEN INSERT *""",
    "dim_tracks": f"""MERGE INTO {CATALOG}.silver.dim_tracks t
USING (
  SELECT DISTINCT
    track_id, track_name, album_id, album_name, artist_id, artist_name,
    duration_ms, popularity, explicit, release_date, preview_url
  FROM {CATALOG}.bronze.bronze_tracks
  WHERE track_id IS NOT NULL
) s ON t.track_id = s.track_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *""",
    "dim_artists": f"""MERGE INTO {CATALOG}.silver.dim_artists t
USING (
  SELECT DISTINCT
    artist_id, artist_name, genres, followers, popularity, uri
  FROM {CATALOG}.bronze.bronze_artists
  WHERE artist_id IS NOT NULL
) s ON t.artist_id = s.artist_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *""",
    "dim_playlists": f"""MERGE INTO {CATALOG}.silver.dim_playlists t
USING (
  SELECT DISTINCT
    playlist_id, playlist_name, owner_name, followers, total_tracks, description, snapshot_id
  FROM {CATALOG}.bronze.bronze_playlists
  WHERE playlist_id IS NOT NULL
) s ON t.playlist_id = s.playlist_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *""",
    "dim_time": f"""MERGE INTO {CATALOG}.silver.dim_time t
USING (
  SELECT DISTINCT
    to_timestamp(played_at) AS play_timestamp,
    hour(to_timestamp(played_at)) AS hour_of_day,
    dayofweek(to_timestamp(played_at)) - 1 AS day_of_week,
    date_format(to_timestamp(played_at), 'EEEE') AS weekday_name,
    dayofweek(to_timestamp(played_at)) > 5 AS is_weekend,
    quarter(to_timestamp(played_at)) AS quarter,
    year(to_timestamp(played_at)) AS year,
    month(to_timestamp(played_at)) AS month,
    day(to_timestamp(played_at)) AS day
  FROM {CATALOG}.bronze.bronze_play_history
  WHERE played_at IS NOT NULL
) s ON t.play_timestamp = s.play_timestamp
WHEN NOT MATCHED THEN INSERT *""",
}

# ── Gold DML SQL (needs base_analytics temp view) ──
GOLD_SQL = {
    "gold_user_listening_summary": """WITH user_summary AS (
    SELECT 'default_user' AS user_id, COUNT(play_id) AS total_tracks,
           COUNT(DISTINCT artist_id) AS unique_artists, SUM(duration_ms / 60000.0) AS total_minutes
    FROM base_analytics
), top_artist AS (
    SELECT artist_name AS favorite_artist, COUNT(*) AS plays
    FROM base_analytics GROUP BY artist_name ORDER BY plays DESC LIMIT 1
), top_track AS (
    SELECT track_name AS top_track, COUNT(*) AS plays
    FROM base_analytics GROUP BY track_name ORDER BY plays DESC LIMIT 1
)
SELECT us.user_id, us.total_tracks, us.unique_artists, us.total_minutes,
       ta.favorite_artist, tt.top_track
FROM user_summary us CROSS JOIN top_artist ta CROSS JOIN top_track tt""",
    "gold_top_tracks": """SELECT track_id, track_name, artist_name,
       COUNT(play_id) AS play_count,
       SUM(duration_ms / 60000.0) AS total_minutes,
       MAX(popularity) AS popularity
FROM base_analytics WHERE track_id IS NOT NULL
GROUP BY track_id, track_name, artist_name ORDER BY play_count DESC""",
    "gold_top_artists": """SELECT artist_id, artist_name, COUNT(play_id) AS total_plays,
       COUNT(DISTINCT track_id) AS unique_tracks,
       SUM(duration_ms / 60000.0) AS total_minutes,
       FIRST(genres) IGNORE NULLS AS genres
FROM base_analytics WHERE artist_id IS NOT NULL
GROUP BY artist_id, artist_name ORDER BY total_plays DESC""",
    "gold_genre_trends": """SELECT genre, month, COUNT(play_id) AS total_plays,
       AVG(popularity) AS avg_popularity, 1 AS unique_users
FROM base_analytics
LATERAL VIEW explode(genres) exploded_genres AS genre
WHERE genre IS NOT NULL
GROUP BY genre, month ORDER BY month, total_plays DESC""",
    "gold_listening_patterns": """SELECT 'default_user' AS user_id, hour_of_day, weekday_name,
       SUM(duration_ms / 60000.0) AS total_minutes
FROM base_analytics
GROUP BY user_id, hour_of_day, weekday_name
ORDER BY hour_of_day, weekday_name""",
}


def make_notebook(cells):
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": src,
            }
            for src in cells
        ],
        "metadata": {
            "kernelspec": {"display_name": "Databricks", "language": "python", "name": "databricks"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(path, notebook):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)


# ── Generate ──

def col_ddl(table_name, columns):
    """Single %sql cell with CREATE TABLE."""
    lines = [f"CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.{table_name} ("]
    lines += [f"  {name} {dtype}" + ("," if i < len(columns) - 1 else "") for i, (name, dtype) in enumerate(columns)]
    lines.extend([
        ")",
        "USING DELTA"
        + (" PARTITIONED BY (processing_date)" if SCHEMA == "bronze" else ""),
        "TBLPROPERTIES (",
        "  delta.enableChangeDataFeed = true"
        + (",\n  delta.columnMapping.mode = 'name'" if SCHEMA != "bronze" else ""),
        ");",
    ])
    return "\n".join(lines)


def col_bronze_config():
    return f"""CATALOG = "{CATALOG}"
SCHEMA = "bronze"
TABLE = ""  # set per notebook

dbutils.widgets.text("raw_base_path", "/Workspace/Users/pacioianu4@gmail.com/Files/spotify-end-to-end-api-project/data/raw", "RAW base path")
RAW_BASE_PATH = dbutils.widgets.get("raw_base_path").rstrip("/")"""


def col_silver_sql(sql):
    return sql


def col_gold_setup():
    return f"""CATALOG = "{CATALOG}"
SCHEMA = "gold"
TABLE = ""  # set per notebook

# Create shared base_analytics temp view
fct = spark.table(f"{{CATALOG}}.silver.fct_plays")
dim_t = spark.table(f"{{CATALOG}}.silver.dim_tracks")
dim_a = spark.table(f"{{CATALOG}}.silver.dim_artists")
dim_time = spark.table(f"{{CATALOG}}.silver.dim_time")

from pyspark.sql import functions as F
base = fct.join(dim_t, "track_id", "left") \\
    .join(dim_a, fct.artist_id == dim_a.artist_id, "left") \\
    .join(dim_time, "play_timestamp", "left") \\
    .select(
        fct.play_id, fct.play_timestamp, fct.duration_ms, fct.context_type,
        dim_t.track_id, dim_t.track_name, dim_t.popularity,
        dim_a.artist_id, dim_a.artist_name, dim_a.genres,
        dim_time.hour_of_day, dim_time.weekday_name,
        F.date_format(fct.play_timestamp, "yyyy-MM").alias("month")
    )
base.createOrReplaceTempView("base_analytics")
print("Temp view 'base_analytics' created.")"""


def col_gold_sql(sql):
    return f"""result = spark.sql('''
{sql}
''')
full = f"{{CATALOG}}.{{SCHEMA}}.{{TABLE}}"
result.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(full)
print(f"Table {{full}} written with {{result.count()}} rows.")"""


# ── Bronze DDL ──
for slug, table, cols in BRONZE:
    SCHEMA = "bronze"
    nb = make_notebook([col_ddl(table, cols)])
    path = os.path.join(BASE_DIR, "notebooks", "ddl", "bronze", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DDL bronze: {path}")

# ── Silver DDL ──
for slug, table, cols in SILVER:
    SCHEMA = "silver"
    nb = make_notebook([col_ddl(table, cols)])
    path = os.path.join(BASE_DIR, "notebooks", "ddl", "silver", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DDL silver: {path}")

# ── Gold DDL ──
for slug, table, cols in GOLD:
    SCHEMA = "gold"
    nb = make_notebook([col_ddl(table, cols)])
    path = os.path.join(BASE_DIR, "notebooks", "ddl", "gold", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DDL gold: {path}")

# ── Bronze DML ──
for slug, table, cols in BRONZE:
    SCHEMA = "bronze"
    TABLE = table
    code = BRONZE_DML[table]
    header = f'RAW_BASE_PATH = dbutils.widgets.get("raw_base_path").rstrip("\\n")\nCATALOG = "{CATALOG}"\nSCHEMA = "bronze"\nTABLE = "{table}"'
    nb = make_notebook([col_bronze_config(), code])
    path = os.path.join(BASE_DIR, "notebooks", "dml", "bronze", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DML bronze: {path}")

# ── Silver DML ──
for slug, table, cols in SILVER:
    sql = SILVER_SQL[table]
    nb = make_notebook([
        f"""CATALOG = "{CATALOG}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {{CATALOG}}.silver")
print("Target: {CATALOG}.silver.{table}")""",
        col_silver_sql(sql),
        f"""result = spark.table(f"{{CATALOG}}.silver.{table}")
print(f"Table state: {{result.count()}} rows")""",
    ])
    path = os.path.join(BASE_DIR, "notebooks", "dml", "silver", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DML silver: {path}")

# ── Gold DML ──
for slug, table, cols in GOLD:
    sql = GOLD_SQL[table]
    nb = make_notebook([
        f"""CATALOG = "{CATALOG}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {{CATALOG}}.gold")
print("Target: {CATALOG}.gold.{table}")""",
        col_gold_setup(),
        col_gold_sql(sql),
        f"""result = spark.table(f"{{CATALOG}}.gold.{table}")
print(f"Table state: {{result.count()}} rows")""",
    ])
    path = os.path.join(BASE_DIR, "notebooks", "dml", "gold", f"{slug}.ipynb")
    write_notebook(path, nb)
    print(f"DML gold: {path}")

print("\n=== DONE: 32 notebooks generated ===")
