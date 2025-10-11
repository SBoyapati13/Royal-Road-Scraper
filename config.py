# Configuration file for Royal Road project

# Database configuration
DATABASE_PATH = 'data/royal_road.db'

# Scraping configuration
BASE_URL = "https://www.royalroad.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Analysis configuration
DEFAULT_METRICS = ['views', 'rating', 'followers', 'favorites', 'chapters', 'pages']
PERFORMANCE_METRICS = ['views', 'rating', 'followers']
LENGTH_METRICS = ['chapters', 'pages']

# Visualization configuration
PLOTLY_CONFIG = {
    'height': 600,
    'width': 1000,
    'margin': dict(r=200)
}

# Standard SQL queries for data loading
LATEST_STORIES_QUERY = """
SELECT 
    s.id, s.royal_road_id, s.title, s.url, s.genres AS genre, s.first_seen, s.last_updated,
    ss.rating, ss.followers, ss.pages, ss.chapters, ss.views, 
    ss.favorites, ss.ratings_count, ss.snapshot_date AS scraped_date
FROM stories s
JOIN (
    SELECT story_id, MAX(snapshot_date) AS max_date
    FROM story_snapshots
    GROUP BY story_id
) latest ON s.id = latest.story_id
JOIN story_snapshots ss ON latest.story_id = ss.story_id AND latest.max_date = ss.snapshot_date
"""

ALL_SNAPSHOTS_QUERY = """
SELECT 
    s.id, s.royal_road_id, s.title, s.url, s.genres AS genre, 
    ss.rating, ss.followers, ss.pages, ss.chapters, ss.views, 
    ss.favorites, ss.ratings_count, ss.snapshot_date AS scraped_date
FROM stories s
JOIN story_snapshots ss ON s.id = ss.story_id
ORDER BY s.royal_road_id, ss.snapshot_date
"""

DASHBOARD_LATEST_QUERY = """
SELECT s.royal_road_id, s.title, s.url, s.genres, 
       COALESCE(ss.rating, 0) as rating,
       COALESCE(ss.followers, 0) as followers,
       COALESCE(ss.views, 0) as views,
       COALESCE(ss.chapters, 0) as chapters,
       ss.snapshot_date
FROM stories s
JOIN (
    SELECT story_id, MAX(snapshot_date) as max_date
    FROM story_snapshots
    GROUP BY story_id
) latest ON s.id = latest.story_id
JOIN story_snapshots ss ON latest.story_id = ss.story_id AND latest.max_date = ss.snapshot_date
"""

DASHBOARD_TIMESERIES_QUERY = """
SELECT s.title, ss.snapshot_date, ss.views, ss.followers, ss.rating
FROM stories s
JOIN story_snapshots ss ON s.id = ss.story_id
ORDER BY s.title, ss.snapshot_date
"""