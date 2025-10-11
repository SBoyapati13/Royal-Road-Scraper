import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import time
from typing import List, Dict, Optional, Tuple, Union, cast
import re
import logging
from pathlib import Path
from database import RoyalRoadDatabase
from config import BASE_URL, HEADERS, DATABASE_PATH

class RoyalRoadScraper:
    """Scraper for RoyalRoad stories and chapters"""

    def __init__(self, delay: float = 1.5, log_level: int = logging.DEBUG):
        """Initialize the scraper with delay and logging configuration.

        Args:
            delay: Delay between requests in seconds
            log_level: Logging level (default: logging.DEBUG)
        """
        self.BASE_URL = BASE_URL
        self.HEADERS = HEADERS
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        # Configure logging
        self.logger = logging.getLogger('RoyalRoadScraper')
        self.logger.setLevel(log_level)
        
        # Create console handler with formatting if it doesn't exist
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Also add a file handler for better debugging
            try:
                Path('logs').mkdir(exist_ok=True)
                file_handler = logging.FileHandler('logs/royal_road_scraper.log')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception:
                self.logger.warning("Could not create log file, continuing with console logging only")
    
    def _extract_story_stats(self, soup: BeautifulSoup) -> Dict[str, Union[int, float]]:
        """Extract statistics from a story page.
        
        Args:
            soup: BeautifulSoup object of the story page
            
        Returns:
            Dictionary containing story statistics with keys: followers, pages, views, chapters
        """
        stats: Dict[str, Union[int, float]] = {}
        
        # Find the stats container - div with class 'portlet-body fiction-stats'
        stats_container = soup.find('div', {'class': 'portlet-body fiction-stats'})
        if not stats_container or not isinstance(stats_container, Tag):
            return stats

        def find_stat_value(container: Tag, label: str) -> Optional[Union[int, float]]:
            # Find all li elements with class 'bold uppercase'
            for li in container.find_all('li', {'class': ['bold', 'uppercase']}):
                if not isinstance(li, Tag):
                    continue
                    
                if label in li.get_text(strip=True):
                    value_li = li.find_next_sibling('li')
                    if isinstance(value_li, Tag):
                        value = value_li.get_text(strip=True)
                        return self._parse_number(value)
            return None

        # Extract all stats
        stat_mappings = [
            ('Total Views', 'views'),
            ('Followers', 'followers'),
            ('Favorites', 'favorites'),
            ('Ratings', 'ratings_count'),
            ('Chapters', 'chapters'),
            ('Pages', 'pages')
        ]

        for label, key in stat_mappings:
            try:
                value = find_stat_value(stats_container, label)
                if value is not None:
                    stats[key] = value
            except Exception as e:
                self.logger.error(f"Error extracting {label}: {e}")
        
        return stats

    def _get_story_ratings(self, url: Optional[str]) -> Tuple[Optional[float], Dict[str, Union[int, float]]]:
        """Fetch and parse additional stats from a story's detail page.
        
        Args:
            url: Full URL to the story page
            
        Returns:
            Tuple of (rating, stats dictionary)
            Note: Rating is included for backwards compatibility but prefer using the list page rating
        """
        if not url:
            return None, {}
        
        try:
            self.logger.debug(f"Fetching story page {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching page: {e}", exc_info=True)
            return None, {}

        rating = None
        stats = self._extract_story_stats(soup)  # Extract stats first
        
        # Get rating directly from the font-red-sunglo span's aria-label or data-content
        try:
            rating_span = soup.find('span', {'class': 'font-red-sunglo'})
            if rating_span and isinstance(rating_span, Tag):
                # Try aria-label first
                rating_text = rating_span.get('aria-label', '')
                if not rating_text:
                    # Fall back to data-content
                    rating_text = rating_span.get('data-content', '')
                if rating_text and isinstance(rating_text, str):
                    # Extract number from format like "4.83 stars" or similar
                    rating_match = re.search(r'([0-9.]+)', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                        except ValueError:
                            self.logger.error(f"Failed to convert rating value: {rating_match.group(1)}")
        except Exception as e:
            self.logger.error(f"Error extracting rating: {e}")

        time.sleep(self.delay)  # Respect rate limiting
        if rating is not None:
            stats['rating'] = rating
        return rating, stats

    def _parse_number(self, text: str) -> Optional[Union[int, float]]:
        """
        Parse a number from text, handling K/M suffixes.
        
        Args:
            text: Text containing a number (e.g., "1.2K", "3M", "500", "1,234 Followers")
            
        Returns:
            Parsed number or None if parsing fails
        """
        try:
            if not text:
                return None
                
            # Extract number part using regex
            number_match = re.search(r'[\d,\.]+', text)
            if not number_match:
                return None
                
            # Get the matched number string
            number_str = number_match.group(0).strip().upper()
            
            # Handle K/M suffixes
            multiplier = 1
            if 'K' in text.upper():
                multiplier = 1000
            elif 'M' in text.upper():
                multiplier = 1000000
            
            # Remove commas and convert to float
            clean_number = float(number_str.replace(',', ''))
            result = int(clean_number * multiplier)
            
            self.logger.debug(f"Parsed number {text} -> {result}")
            return result
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.debug(f"Failed to parse number from '{text}': {e}")
            return None

    def scrape_top_stories(self) -> List[Dict]:
        """
        Scrapes the top stories from Royal Road's trending page.
        
        Returns:
            List of story dictionaries
        """

        stories = []
        url = f"{self.BASE_URL}/fictions/trending"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all story entries
            story_items = soup.find_all('div', class_='fiction-list-item')

            if not story_items:
                # Try alternative selectors
                story_items = soup.find_all('div', class_=re.compile(r'fiction-list-item'))

            self.logger.info(f"Found {len(story_items)} stories")

            for item in story_items:
                story_data = self._parse_story_item(item)
                if story_data and story_data.get('title'):
                    stories.append(story_data)

            time.sleep(self.delay)

        except Exception as e:
            self.logger.error(f"Error scraping trending page: {e}", exc_info=True)

        print(f"Scraped {len(stories)} stories in total.")
        return stories
    
    def _parse_story_item(self, item) -> Optional[Dict]:
        """Parse a single story item from the best-rated list page."""

        try:
            # Title and URL
            title_elem = item.find('h2', class_='fiction-title')
            if not title_elem:
                return None
            title_link = title_elem.find('a')
            title = title_link.get_text(strip=True) if title_link else "Unknown"
            story_url = title_link['href'] if title_link and title_link.get('href') else None
            
            # Extract stats from the list page
            stats_div = item.find('div', class_='stats')
            list_page_stats = {}
            
            if stats_div and isinstance(stats_div, Tag):
                # Views and chapters are directly on the list page
                for stat in stats_div.find_all('span'):
                    if not isinstance(stat, Tag):
                        continue
                    text = stat.get_text(strip=True)
                    if 'View' in text:
                        list_page_stats['views'] = self._parse_number(text)
                    elif 'Chapter' in text:
                        list_page_stats['chapters'] = self._parse_number(text)
                        
                # Rating is also on the list page
                rating_div = stats_div.find('span', class_='font-red-sunglo')
                if rating_div and isinstance(rating_div, Tag):
                    rating_text = rating_div.get_text(strip=True)
                    rating_match = re.search(r'([0-9.]+)\s*/\s*5', rating_text)
                    if rating_match:
                        try:
                            list_page_stats['rating'] = float(rating_match.group(1))
                        except ValueError:
                            pass
            
            # Tags/Genres - in <span class="tags">
            genres = []
            tags_span = item.find('span', class_='tags')
            if tags_span:
                tag_elements = tags_span.find_all('a', class_='label')
                genres = [tag.get_text(strip=True) for tag in tag_elements if tag.get_text(strip=True)]
            
            # Get additional stats from story page
            story_url_full = f"{self.BASE_URL}{story_url}" if story_url else None
            _, detail_stats = self._get_story_ratings(story_url_full)
            
            # Log stats from both sources
            self.logger.debug(f"Stats from list page: {list_page_stats}")
            self.logger.debug(f"Stats from detail page: {detail_stats}")

            # Combine stats from both pages
            combined_stats = {**list_page_stats, **detail_stats}  # Detail stats take precedence


            return {
                'title': title,
                'url': f"{self.BASE_URL}{story_url}" if story_url else None,
                'genres': ', '.join(genres) if genres else None,
                'rating': combined_stats.get('rating'),
                'followers': combined_stats.get('followers'),
                'pages': combined_stats.get('pages'),
                'chapters': combined_stats.get('chapters'),
                'views': combined_stats.get('views'),
                'favorites': combined_stats.get('favorites'),
                'ratings_count': combined_stats.get('ratings_count')
            }
        
        except Exception as e:
            print(f"Error parsing story item: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_to_database(self, stories: List[Dict], db_path: str = DATABASE_PATH):
        """
        Saves the list of stories to a SQLite database.
        
        Args:
            stories: List of story metadata dictionaries.
            db_path: Path to the SQLite database file.

        Returns:
            Tuple of (stories_added, stories_updated)
        """
        print(f"Attempting to save to database at: {db_path}")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with RoyalRoadDatabase(db_path) as db:
            added, updated = db.insert_stories_bulk(stories)

            db.log_scrape(
                pages_scraped = 1,  # Trending page is always 1 page
                stories_added = added,
                stories_updated = updated,
                status = "success",
                notes = f"Scraped {len(stories)} stories total, created {added + updated} snapshots"
            )
            
            # Calculate stats for user feedback
            total_snapshots = db.get_snapshot_count()
            print(f"\nDatabase now contains:")
            print(f"- {added + updated} new snapshots created in this run")
            print(f"- {total_snapshots} total snapshots")
            print(f"- {added} new stories added")
            print(f"- {updated} existing stories updated\n")
            print("Time-series data is being preserved. Run the analysis notebook to see trends over time.")

        return added, updated

if __name__ == "__main__":
    scraper = RoyalRoadScraper(log_level=logging.DEBUG)
    print("Starting to scrape RoyalRoad...")
    stories = scraper.scrape_top_stories()
    added, updated = scraper.save_to_database(stories)
    print(f"Scraping complete! Added {added} new stories and updated {updated} existing stories.")