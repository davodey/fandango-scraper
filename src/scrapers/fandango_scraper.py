"""
Fandango movie scraper
Scrapes movie data from Fandango website
"""
import re
import hashlib
import time
from typing import List, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
try:
    # Optional: only used as a fallback if Selenium Manager fails
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ChromeDriverManager = None  # type: ignore
from bs4 import BeautifulSoup
import logging

from ..models.movie import Movie


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FandangoScraper:
    """Scraper for Fandango movie data"""

    BASE_URL = "https://www.fandango.com"
    NEW_MOVIES_URL = f"{BASE_URL}/movies-in-theaters"

    def __init__(self, headless: bool = True):
        """
        Initialize the scraper

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Set up Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            # Use modern headless mode when available
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        # Prefer Selenium Manager (built into selenium >= 4.6) to resolve the correct driver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Initialized Chrome via Selenium Manager")
        except Exception as e:
            logger.warning(
                "Selenium Manager failed to initialize Chrome (%s). Attempting webdriver-manager fallback...",
                e,
            )
            if ChromeDriverManager is None:
                # Re-raise original error if webdriver-manager isn't available
                raise
            # Fallback: use webdriver-manager to install a matching driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _generate_movie_id(self, title: str, release_date: Optional[str] = None) -> int:
        """
        Generate a unique movie ID from title and release date
        Uses hash to create consistent IDs across runs

        Args:
            title: Movie title
            release_date: Release date string

        Returns:
            Integer ID
        """
        # Create a string to hash
        hash_string = f"{title.lower().strip()}"
        if release_date:
            hash_string += f"_{release_date}"

        # Generate hash and convert to int
        hash_obj = hashlib.md5(hash_string.encode())
        # Take first 8 bytes and convert to int, then get absolute value
        return abs(int.from_bytes(hash_obj.digest()[:8], byteorder='big'))

    def _parse_release_date(self, date_string: str) -> Optional[str]:
        """
        Parse release date to yyyy-MM-dd format

        Args:
            date_string: Date string from Fandango

        Returns:
            Formatted date string or None
        """
        if not date_string:
            return None

        try:
            # Common formats: "Jan 1, 2024", "January 1, 2024", etc.
            # Try multiple date formats
            for fmt in ["%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                try:
                    date_obj = datetime.strptime(date_string.strip(), fmt)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            logger.warning(f"Could not parse date: {date_string}")
            return None
        except Exception as e:
            logger.error(f"Error parsing date {date_string}: {e}")
            return None

    def _extract_rating(self, rating_text: str) -> float:
        """
        Extract numeric rating from text
        Converts percentage or star ratings to 0-10 scale

        Args:
            rating_text: Rating text from page

        Returns:
            Float rating 0-10
        """
        try:
            # Look for percentage (e.g., "85%")
            percent_match = re.search(r'(\d+)%', rating_text)
            if percent_match:
                return float(percent_match.group(1)) / 10.0

            # Look for star rating (e.g., "4.5/5")
            star_match = re.search(r'([\d.]+)/5', rating_text)
            if star_match:
                return float(star_match.group(1)) * 2.0

            # Look for direct rating out of 10
            ten_match = re.search(r'([\d.]+)/10', rating_text)
            if ten_match:
                return float(ten_match.group(1))

            # Default if no rating found
            return 5.0
        except Exception as e:
            logger.error(f"Error extracting rating from {rating_text}: {e}")
            return 5.0

    def scrape_movies(self) -> List[Movie]:
        """
        Scrape all movies from Fandango

        Returns:
            List of Movie objects
        """
        logger.info("Starting Fandango scrape...")
        movies = []

        try:
            self._setup_driver()
            self.driver.get(self.NEW_MOVIES_URL)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Scroll to load dynamic content
            self._scroll_page()

            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # Find movie containers - Fandango uses various selectors
            # This will need adjustment based on current Fandango HTML structure
            movie_elements = self._find_movie_elements(soup)

            logger.info(f"Found {len(movie_elements)} movie elements")

            for idx, element in enumerate(movie_elements):
                try:
                    movie = self._parse_movie_element(element)
                    if movie:
                        movies.append(movie)
                        logger.info(f"Scraped: {movie.title}")
                except Exception as e:
                    logger.error(f"Error parsing movie element {idx}: {e}")
                    continue

            logger.info(f"Successfully scraped {len(movies)} movies")

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            self._close_driver()

        return movies

    def _scroll_page(self):
        """Scroll page to load all dynamic content"""
        try:
            # Scroll down in steps to trigger lazy loading
            scroll_pause = 1
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for _ in range(5):  # Limit scrolls to avoid infinite loop
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)

                # Calculate new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            logger.warning(f"Error during page scroll: {e}")

    def _find_movie_elements(self, soup: BeautifulSoup) -> list:
        """
        Find movie elements in the page
        Tries multiple selectors as Fandango may change structure

        Args:
            soup: BeautifulSoup object

        Returns:
            List of movie elements
        """
        # Try common Fandango selectors
        selectors = [
            'li[class*="movie"]',
            'div[class*="movie-card"]',
            'div[class*="MovieCard"]',
            'article[class*="movie"]',
            'div[data-testid*="movie"]',
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found elements with selector: {selector}")
                return elements

        # Fallback: try to find any reasonable container
        logger.warning("Using fallback element detection")
        return soup.find_all(['article', 'li', 'div'], limit=100)

    def _parse_movie_element(self, element) -> Optional[Movie]:
        """
        Parse a movie element into a Movie object

        Args:
            element: BeautifulSoup element

        Returns:
            Movie object or None
        """
        try:
            # Extract title
            title = self._extract_title(element)
            if not title:
                return None

            # Extract other fields
            overview = self._extract_overview(element)
            release_date = self._extract_release_date(element)
            poster_path = self._extract_poster_path(element)
            backdrop_path = self._extract_backdrop_path(element)
            vote_average = self._extract_vote_average(element)
            vote_count = self._extract_vote_count(element)
            popularity = self._calculate_popularity(vote_average, vote_count)

            # Generate consistent ID
            movie_id = self._generate_movie_id(title, release_date)

            return Movie(
                id=movie_id,
                title=title,
                overview=overview or "No description available.",
                releaseDate=release_date,
                posterPath=poster_path,
                backdropPath=backdrop_path,
                voteAverage=vote_average,
                voteCount=vote_count,
                popularity=popularity
            )

        except Exception as e:
            logger.error(f"Error parsing movie element: {e}")
            return None

    def _extract_title(self, element) -> Optional[str]:
        """Extract movie title"""
        # Try multiple selectors
        for selector in ['h3', 'h2', 'h4', '[class*="title"]', 'a']:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 2:
                    return title
        return None

    def _extract_overview(self, element) -> Optional[str]:
        """Extract movie overview/description"""
        for selector in ['p', '[class*="description"]', '[class*="synopsis"]']:
            desc_elem = element.select_one(selector)
            if desc_elem:
                desc = desc_elem.get_text(strip=True)
                if desc and len(desc) > 10:
                    return desc
        return None

    def _extract_release_date(self, element) -> Optional[str]:
        """Extract and parse release date"""
        for selector in ['[class*="date"]', 'time', 'span']:
            date_elem = element.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                parsed_date = self._parse_release_date(date_text)
                if parsed_date:
                    return parsed_date
        return None

    def _extract_poster_path(self, element) -> Optional[str]:
        """Extract poster image path"""
        img = element.find('img')
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                return src
        return None

    def _extract_backdrop_path(self, element) -> Optional[str]:
        """Extract backdrop image path (often same as poster for Fandango)"""
        # Fandango typically doesn't have separate backdrops
        # Could use poster or look for hero images
        return self._extract_poster_path(element)

    def _extract_vote_average(self, element) -> float:
        """Extract rating/vote average"""
        # Look for rating elements
        for selector in ['[class*="rating"]', '[class*="score"]', 'span', 'div']:
            rating_elem = element.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if any(char in rating_text for char in ['%', '/', '★']):
                    return self._extract_rating(rating_text)

        # Default rating
        return 5.0

    def _extract_vote_count(self, element) -> int:
        """Extract vote count"""
        # Look for review count
        for selector in ['[class*="review"]', '[class*="count"]']:
            count_elem = element.select_one(selector)
            if count_elem:
                count_text = count_elem.get_text(strip=True)
                # Extract numbers
                numbers = re.findall(r'\d+', count_text.replace(',', ''))
                if numbers:
                    return int(numbers[0])

        # Default count based on rating
        return 100

    def _calculate_popularity(self, vote_average: float, vote_count: int) -> float:
        """
        Calculate popularity score
        Simple formula: vote_average * log(vote_count + 1)

        Args:
            vote_average: Average rating
            vote_count: Number of votes

        Returns:
            Popularity score
        """
        import math
        return round(vote_average * math.log(vote_count + 1), 2)
