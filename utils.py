"""
Utility functions for Royal Road data analysis
"""
import pandas as pd
import sqlite3
from pathlib import Path
from config import DATABASE_PATH, LATEST_STORIES_QUERY, ALL_SNAPSHOTS_QUERY

def load_latest_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load both latest and all historical data from the database
    
    Returns:
        tuple: (latest_data_df, all_snapshots_df)
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Load latest metrics for each story
        df_latest = pd.read_sql_query(LATEST_STORIES_QUERY, conn)
        
        # Load all historical snapshots for time-series analysis
        df_all = pd.read_sql_query(ALL_SNAPSHOTS_QUERY, conn)
        
        conn.close()
        
        # Convert scraped_date to datetime
        df_latest['last_updated'] = pd.to_datetime(df_latest['scraped_date'])
        df_all['last_updated'] = pd.to_datetime(df_all['scraped_date'])
        
        return df_latest, df_all
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_database_stats() -> dict:
    """Get basic statistics about the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get total stories
        cursor.execute("SELECT COUNT(*) FROM stories")
        total_stories = cursor.fetchone()[0]
        
        # Get total snapshots
        cursor.execute("SELECT COUNT(*) FROM story_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        # Get stories with multiple snapshots
        cursor.execute("""
            SELECT COUNT(DISTINCT story_id) 
            FROM story_snapshots 
            WHERE story_id IN (
                SELECT story_id 
                FROM story_snapshots 
                GROUP BY story_id 
                HAVING COUNT(*) > 1
            )
        """)
        stories_with_history = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_stories': total_stories,
            'total_snapshots': total_snapshots,
            'stories_with_history': stories_with_history
        }
        
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {}

def create_buckets(series: pd.Series, n_buckets: int = 10) -> pd.Series:
    """
    Creates equal-size buckets (quantiles) from a numerical series.
    Each bucket contains roughly the same number of stories.
    Bucket 1 has the lowest values, Bucket 10 has the highest values.
    """
    try:
        return pd.qcut(series, n_buckets, labels=[f'Bucket {i+1}' for i in range(n_buckets)])
    except ValueError:
        # Handle case where there are duplicate values
        return pd.qcut(series, n_buckets, labels=[f'Bucket {i+1}' for i in range(n_buckets)], duplicates='drop')