import sqlite3
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from config import DATABASE_PATH

class RoyalRoadDatabase:
    """Database manager for Royalroad story data"""

    db_path: str
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_path: str = DATABASE_PATH):
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

        # Base Stories table - stores current metadata about each story
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                royal_road_id INTEGER UNIQUE,
                title TEXT,
                url TEXT,
                genres TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Story Snapshots table - stores historical metrics for each story
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating REAL,
                followers INTEGER,
                pages INTEGER,
                chapters INTEGER,
                views INTEGER,
                favorites INTEGER,
                ratings_count INTEGER,
                FOREIGN KEY (story_id) REFERENCES stories(id)
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
            CREATE INDEX IF NOT EXISTS idx_stories_royal_road_id ON stories(royal_road_id)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_url ON stories(url)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_snapshots_story_id ON story_snapshots(story_id)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_snapshots_date ON story_snapshots(snapshot_date)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_snapshots_rating ON story_snapshots(rating)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_snapshots_followers ON story_snapshots(followers)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_story_snapshots_views ON story_snapshots(views)
        """)

        self.conn.commit()
        print("Database tables created or verified.")

    def _extract_royal_road_id(self, url: Optional[str]) -> Optional[int]:
        """
        Extract the RoyalRoad story ID from a URL
        
        Args:
            url: The URL of the story
            
        Returns:
            The RoyalRoad story ID as an integer or None if it couldn't be extracted
        """
        if not url:
            return None
            
        import re
        # URL format is typically https://www.royalroad.com/fiction/12345/story-title
        match = re.search(r'/fiction/(\d+)/', url)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                print(f"Could not convert story ID to integer: {match.group(1)}")
                return None
        return None
        
    def insert_story(self, story_data: Dict) -> Tuple[Optional[int], bool]:
        """
        Insert a single story into the database and create a snapshot of its current metrics
        
        Args:
            story_data: Dictionary containing story attributes
            
        Returns:
            Tuple of (story_id, is_new): ID of the inserted story and whether it was a new insert
        """
        try:
            # Extract Royal Road ID from URL
            royal_road_id = self._extract_royal_road_id(story_data.get('url'))
            
            # Skip if we can't get a Royal Road ID
            if royal_road_id is None:
                print(f"Skipping story with invalid URL: {story_data.get('url')}")
                return (None, False)
                
            # Check if story exists by Royal Road ID first
            self.cursor.execute("SELECT id FROM stories WHERE royal_road_id = ?", (royal_road_id,))
            existing = self.cursor.fetchone()
            
            is_new = existing is None
            
            if is_new:
                # Insert new story
                self.cursor.execute("""
                    INSERT INTO stories (royal_road_id, title, url, genres, first_seen, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    royal_road_id,
                    story_data.get('title'),
                    story_data.get('url'),
                    story_data.get('genres')
                ))
                
                # Get story ID
                story_id = self.cursor.execute(
                    "SELECT last_insert_rowid();"
                ).fetchone()[0]
            else:
                # Update existing story's metadata and last_updated timestamp
                story_id = existing[0]
                self.cursor.execute("""
                    UPDATE stories 
                    SET title = ?, url = ?, genres = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    story_data.get('title'),
                    story_data.get('url'),
                    story_data.get('genres'),
                    story_id
                ))
            
            # Always insert a new snapshot with the current metrics
            self.cursor.execute("""
                INSERT INTO story_snapshots 
                (story_id, snapshot_date, rating, followers, pages, chapters, views, favorites, ratings_count)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story_id,
                story_data.get('rating'),
                story_data.get('followers'),
                story_data.get('pages'),
                story_data.get('chapters'),
                story_data.get('views'),
                story_data.get('favorites'),
                story_data.get('ratings_count')
            ))

            self.conn.commit()
            return (story_id, is_new)
        
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

        # Get all existing Royal Road IDs first
        self.cursor.execute("SELECT id, royal_road_id FROM stories")
        existing_ids = {row[1]: row[0] for row in self.cursor.fetchall() if row[1] is not None}
        
        # Print current database state
        print(f"\nBefore update:")
        print(f"Total stories in database: {len(existing_ids)}")

        for story in stories:
            # Extract Royal Road ID from URL
            royal_road_id = self._extract_royal_road_id(story.get('url'))
            if not royal_road_id:
                print(f"Skipping story with invalid URL: {story.get('url')}")
                continue
                
            if royal_road_id in existing_ids:
                # Check if we need to create a new snapshot by comparing with the most recent one
                story_id = existing_ids[royal_road_id]
                self.cursor.execute("""
                    SELECT rating, followers, chapters, views, favorites 
                    FROM story_snapshots 
                    WHERE story_id = ? 
                    ORDER BY snapshot_date DESC 
                    LIMIT 1
                """, (story_id,))
                
                current = self.cursor.fetchone()
                if current:
                    old_vals = dict(zip(['rating', 'followers', 'chapters', 'views', 'favorites'], current))
                    new_vals = {k: story.get(k) for k in old_vals.keys()}
                    # Only insert a new snapshot if values actually changed
                    if any(old_vals[k] != new_vals[k] for k in old_vals.keys() if new_vals[k] is not None):
                        result = self.insert_story(story)
                        if result[0]:  # If update was successful
                            updated += 1
                else:
                    # No snapshots exist yet, create one
                    result = self.insert_story(story)
                    if result[0]:
                        updated += 1
            else:
                # This is a new story, add it
                result = self.insert_story(story)
                if result[0]:  # If insert was successful
                    added += 1
                    existing_ids[royal_road_id] = result[0]  # Store the new ID

        self.conn.commit()

        # Print detailed results
        print(f"\nScrape Results:")
        self.cursor.execute("SELECT COUNT(*) FROM stories")
        total_stories = self.cursor.fetchone()[0]
        print(f"Total stories in database now: {total_stories}")
        
        self.cursor.execute("SELECT COUNT(*) FROM story_snapshots")
        total_snapshots = self.cursor.fetchone()[0]
        print(f"Total snapshots in database: {total_snapshots}")
        
        print(f"Stories scraped this run: {len(stories)}")
        print(f"New stories added: {added}")
        print(f"Existing stories updated: {updated}")
        
        # Count stories with ratings in the latest snapshots
        self.cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT s.id
                FROM stories s
                JOIN story_snapshots ss ON s.id = ss.story_id
                WHERE ss.rating IS NOT NULL
                GROUP BY s.id
            )
        """)
        stories_with_ratings = self.cursor.fetchone()[0]
        print(f"Stories with ratings: {stories_with_ratings}")
        
        # Get some sample ratings from the most recent snapshots
        self.cursor.execute("""
            SELECT s.title, ss.rating, ss.snapshot_date 
            FROM stories s
            JOIN story_snapshots ss ON s.id = ss.story_id
            WHERE ss.rating IS NOT NULL 
            ORDER BY ss.snapshot_date DESC 
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

    def get_snapshot_count(self) -> int:
        """
        Get the total number of snapshots in the database
        
        Returns:
            Total number of story snapshots
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM story_snapshots")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting snapshot count: {e}")
            return 0
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()