import sqlite3
from typing import List, Dict, Tuple, Optional
from pathlib import Path

class RoyalRoadDatabase:
    """Database manager for Royalroad story data"""

    db_path: str
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_path: str = 'data/royal_road.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None  # type: ignore
        self.cursor = None  # type: ignore
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create database tables if they do not exist"""

        # Stories table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                rating REAL,
                followers INTEGER,
                pages INTEGER,
                chapters INTEGER,
                views INTEGER,
                favorites INTEGER,
                ratings_count INTEGER,
                genres TEXT,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create scrape_history table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pages_scraped INTEGER,
                stories_added INTEGER,
                stories_updated INTEGER,
                status TEXT,
                notes TEXT
            );
        """)

        # Create indexes for performance
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_rating ON stories(rating)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_followers ON stories(followers)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_url ON stories(url)
        """)

        self.conn.commit()
        print("Database tables created or verified.")

    def insert_story(self, story_data: Dict) -> Tuple[Optional[int], bool]:
        """
        Insert a single story into the database 
        
        Args:
            story_data: Dictionary containing story attributes
            
        Returns:
            Tuple of (story_id, is_new): ID of the inserted story and whether it was a new insert
        """
        try:
            # Check if story exists first
            self.cursor.execute("SELECT id FROM stories WHERE url = ?", (story_data.get('url'),))
            existing = self.cursor.fetchone()
            
            # Insert or update story
            self.cursor.execute("""
                INSERT OR REPLACE INTO stories (title, url, rating, followers, pages, chapters, views, favorites, ratings_count, genres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story_data.get('title'),
                story_data.get('url'),
                story_data.get('rating'),
                story_data.get('followers'),
                story_data.get('pages'),
                story_data.get('chapters'),
                story_data.get('views'),
                story_data.get('favorites'),
                story_data.get('ratings_count'),
                story_data.get('genres')
            ))

            # Get story ID
            story_id = self.cursor.execute(
                "SELECT last_insert_rowid();"
            ).fetchone()[0]

            self.conn.commit()
            return (story_id, existing is None)
        
        except sqlite3.Error as e:
            print(f"Error inserting story: {e}")
            return (None, False)
        
    def insert_stories_bulk(self, stories: List[Dict]) -> Tuple[int, int]:
        """
        Insert multiple stories at once
        
        Args:
            stories: List of story data dictionaries
            
        Returns:
            Tuple of (stories_added, stories_updated)
        """

        added = 0
        updated = 0

        # Get all existing URLs first
        self.cursor.execute("SELECT url FROM stories")
        existing_urls = {row[0] for row in self.cursor.fetchall()}
        
        # Print current database state
        print(f"\nBefore update:")
        print(f"Total stories in database: {len(existing_urls)}")

        for story in stories:
            url = story.get('url')
            if not url:
                continue
                
            if url in existing_urls:
                # For updates, compare current values with new values
                self.cursor.execute("""
                    SELECT rating, followers, chapters, views, favorites 
                    FROM stories WHERE url = ?
                """, (url,))
                current = self.cursor.fetchone()
                if current:
                    old_vals = dict(zip(['rating', 'followers', 'chapters', 'views', 'favorites'], current))
                    new_vals = {k: story.get(k) for k in old_vals.keys()}
                    # Only count as update if values actually changed
                    if any(old_vals[k] != new_vals[k] for k in old_vals.keys() if new_vals[k] is not None):
                        result = self.insert_story(story)
                        if result[0]:  # If update was successful
                            updated += 1
            else:
                result = self.insert_story(story)
                if result[0]:  # If insert was successful
                    added += 1
                    existing_urls.add(url)

        self.conn.commit()

        # Print detailed results
        print(f"\nScrape Results:")
        self.cursor.execute("SELECT COUNT(*) FROM stories")
        total_stories = self.cursor.fetchone()[0]
        print(f"Total stories in database now: {total_stories}")
        print(f"Stories scraped this run: {len(stories)}")
        print(f"Stories added: {added}")
        print(f"Stories updated: {updated}")
        
        # Count stories with ratings
        self.cursor.execute("SELECT COUNT(*) FROM stories WHERE rating IS NOT NULL")
        stories_with_ratings = self.cursor.fetchone()[0]
        print(f"Stories with ratings: {stories_with_ratings}")
        
        # Get some sample ratings
        self.cursor.execute("""
            SELECT title, rating, scraped_date 
            FROM stories 
            WHERE rating IS NOT NULL 
            ORDER BY scraped_date DESC 
            LIMIT 5
        """)
        samples = self.cursor.fetchall()
        if samples:
            print("\nMost Recent Story Ratings:")
            for title, rating, date in samples:
                print(f"{title}: {rating} (Scraped: {date})")
        
        return (added, updated)
    
    def log_scrape(self, pages_scraped: int, stories_added: int, stories_updated: int, 
                   status: str = "success", notes: Optional[str] = None):
        """
        Log a scraping session
        
        Args:
            pages_scraped: Number of pages scraped
            stories_added: Number of new stories added
            stories_updated: Number of existing stories updated
            status: Status of the scrape (e.g. 'success', 'partial', 'failed')
            notes: Optional notes about the scrape
        """

        try:
            self.cursor.execute("""
                INSERT INTO scrape_history (pages_scraped, stories_added, stories_updated, status, notes)
                VALUES (?, ?, ?, ?, ?);
            """, (pages_scraped, stories_added, stories_updated, status, notes))

            self.conn.commit()
            print("Scrape session logged.")
        
        except sqlite3.Error as e:
            print(f"Error logging scrape session: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()