"""
Fandango movie scraper
Scrapes movie data from Fandango website by visiting individual movie detail pages
"""
import re
import hashlib
import time
from typing import List, Optional, Dict
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

        self.driver.implicitly_wait(5)

    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _generate_movie_id(self, title: str, fandango_id: Optional[str] = None) -> int:
        """
        Generate a unique movie ID from title and Fandango ID if available
        Uses hash to create consistent IDs across runs

        Args:
            title: Movie title
            fandango_id: Fandango's internal movie ID from URL

        Returns:
            Integer ID
        """
        # Prefer using Fandango's ID if available
        if fandango_id:
            try:
                return int(fandango_id)
            except ValueError:
                pass

        # Fallback to hash-based ID
        hash_string = f"{title.lower().strip()}"
        hash_obj = hashlib.md5(hash_string.encode())
        return abs(int.from_bytes(hash_obj.digest()[:8], byteorder='big'))

    def _parse_release_date(self, date_string: str) -> Optional[str]:
        """
        Parse release date to yyyy-MM-dd format
        Handles Fandango format: "Friday, Nov 14, 2025"

        Args:
            date_string: Date string from Fandango

        Returns:
            Formatted date string or None
        """
        if not date_string:
            return None

        try:
            # Remove day of week if present
            date_string = re.sub(r'^[A-Za-z]+,\s*', '', date_string.strip())

            # Try multiple date formats
            formats = [
                "%b %d, %Y",      # Nov 14, 2025
                "%B %d, %Y",      # November 14, 2025
                "%m/%d/%Y",       # 11/14/2025
                "%Y-%m-%d"        # 2025-11-14
            ]

            for fmt in formats:
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

    def scrape_movies(self) -> List[Movie]:
        """
        Scrape all movies from Fandango

        Process:
        1. Load movies-in-theaters page
        2. Extract all movie detail URLs
        3. Visit each movie page
        4. Extract detailed information
        5. Return list of Movie objects

        Returns:
            List of Movie objects
        """
        logger.info("Starting Fandango scrape...")
        movies = []

        try:
            self._setup_driver()

            # Step 1: Get all movie URLs from main page
            movie_urls = self._get_movie_urls()
            logger.info(f"Found {len(movie_urls)} movie URLs")

            # Step 2: Visit each movie and extract details
            for idx, url in enumerate(movie_urls, 1):
                try:
                    logger.info(f"Scraping movie {idx}/{len(movie_urls)}: {url}")
                    movie = self._scrape_movie_detail(url)
                    if movie:
                        movies.append(movie)
                        logger.info(f"  ✓ Scraped: {movie.title}")
                    else:
                        logger.warning(f"  ✗ Failed to scrape movie from {url}")

                    # Small delay to be polite
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue

            logger.info(f"Successfully scraped {len(movies)} movies")

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            self._close_driver()

        return movies

    def _get_movie_urls(self) -> List[str]:
        """
        Get all movie detail URLs from the main movies-in-theaters page

        Returns:
            List of movie detail URLs
        """
        logger.info(f"Loading {self.NEW_MOVIES_URL}")
        self.driver.get(self.NEW_MOVIES_URL)

        # Wait for page to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return []

        # Scroll to load all movies
        self._scroll_page()

        # Parse page
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        # Find all movie links
        movie_urls = set()

        # Common selectors for movie links
        selectors = [
            'a[href*="/movie-overview"]',
            'a[data-id]',
            'a[class*="movie"]',
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/movie-overview' in href:
                    # Make absolute URL
                    if href.startswith('/'):
                        href = self.BASE_URL + href
                    movie_urls.add(href)

        # Also try finding links by pattern
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            # Match Fandango movie overview URLs
            if re.search(r'/[\w-]+-\d+/movie-overview', href):
                if href.startswith('/'):
                    href = self.BASE_URL + href
                movie_urls.add(href)

        return list(movie_urls)

    def _scroll_page(self):
        """Scroll page to load all dynamic content"""
        try:
            scroll_pause = 1.5
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            logger.warning(f"Error during page scroll: {e}")

    def _scrape_movie_detail(self, url: str) -> Optional[Movie]:
        """
        Scrape detailed movie information from a movie detail page

        Args:
            url: URL to movie detail page

        Returns:
            Movie object or None
        """
        try:
            self.driver.get(url)

            # Wait for movie detail to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "movie-detail-header__title"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for movie details on {url}")
                return None

            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # Extract Fandango movie ID from URL
            fandango_id = self._extract_fandango_id(url)

            # Extract data from specific nodes
            title = self._extract_title_from_detail(soup)
            if not title:
                logger.warning("No title found, skipping movie")
                return None

            overview = self._extract_overview_from_detail(soup)
            release_date = self._extract_release_date_from_detail(soup)
            poster_path = self._extract_poster_from_detail(soup)
            backdrop_path = poster_path  # Use poster as backdrop
            vote_average = self._extract_rating_from_detail(soup)
            vote_count = self._extract_vote_count_from_detail(soup)
            popularity = self._calculate_popularity(vote_average, vote_count)
            trailer_url = self._extract_trailer_from_detail(soup)

            # Generate movie ID
            movie_id = self._generate_movie_id(title, fandango_id)

            # Store trailer URL in backdropPath for now (we can adjust Movie model later if needed)
            # Or we can add it to overview
            if trailer_url and overview:
                overview += f"\n\nTrailer: {trailer_url}"

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
            logger.error(f"Error scraping movie detail from {url}: {e}")
            return None

    def _extract_fandango_id(self, url: str) -> Optional[str]:
        """Extract Fandango's movie ID from URL"""
        # URL format: /movie-name-240495/movie-overview
        match = re.search(r'-(\d+)/movie-overview', url)
        if match:
            return match.group(1)
        return None

    def _extract_title_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from movie detail page"""
        title_elem = soup.select_one('h1.movie-detail-header__title')
        if title_elem:
            return title_elem.get_text(strip=True)
        return None

    def _extract_overview_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract synopsis/overview from 'More Info' section"""
        synopsis_elem = soup.select_one('p#movie-detail-synopsis')
        if synopsis_elem:
            return synopsis_elem.get_text(strip=True)

        # Fallback
        synopsis_elem = soup.select_one('.movie-detail__synopsis')
        if synopsis_elem:
            return synopsis_elem.get_text(strip=True)

        return None

    def _extract_release_date_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract release date from 'More Info' section"""
        # Look in the GRV list
        grv_items = soup.select('li.movie-detail__grv-item')
        for item in grv_items:
            text = item.get_text(strip=True)
            if 'RELEASE DATE:' in text:
                date_text = text.replace('RELEASE DATE:', '').strip()
                return self._parse_release_date(date_text)

        return None

    def _extract_poster_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract poster image URL"""
        # Look for poster in photo gallery
        img_elem = soup.select_one('.details-img-carousel__img')
        if img_elem:
            src = img_elem.get('src') or img_elem.get('data-src')
            if src and 'default_poster' not in src:
                return src

        # Try to find any movie image
        img_elem = soup.select_one('img[alt*="poster"], img[class*="poster"]')
        if img_elem:
            src = img_elem.get('src') or img_elem.get('data-src')
            if src:
                return src

        return None

    def _extract_rating_from_detail(self, soup: BeautifulSoup) -> float:
        """
        Extract Rotten Tomatoes rating from movie detail page
        Returns average of critic and audience scores
        """
        ratings = []

        # Look for Rotten Tomatoes scores
        rt_scores = soup.select('.rottentomatoes-rating')
        for score_elem in rt_scores:
            score_text = score_elem.get_text(strip=True)
            # Extract percentage
            match = re.search(r'(\d+)%', score_text)
            if match:
                rating = float(match.group(1)) / 10.0  # Convert to 0-10 scale
                ratings.append(rating)

        # Return average if we have ratings, otherwise default
        if ratings:
            return round(sum(ratings) / len(ratings), 1)

        return 5.0

    def _extract_vote_count_from_detail(self, soup: BeautifulSoup) -> int:
        """
        Extract vote count (estimated from ratings presence)
        Since Fandango doesn't show exact vote counts, we estimate
        """
        # If we have RT scores, assume decent vote count
        rt_scores = soup.select('.rottentomatoes-rating')
        if rt_scores:
            # Estimate based on having professional reviews
            return 500

        return 100

    def _extract_trailer_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract trailer URL from movie detail page"""
        # Look for trailer button/link
        trailer_link = soup.select_one('a.movie-detail-header__trailer-btn')
        if trailer_link:
            href = trailer_link.get('href')
            if href:
                if href.startswith('/'):
                    return self.BASE_URL + href
                return href

        # Also check in the More Info section for video links
        video_link = soup.select_one('watch-videos-link')
        if video_link:
            src = video_link.get('src')
            if src:
                return src

        return None

    def _calculate_popularity(self, vote_average: float, vote_count: int) -> float:
        """
        Calculate popularity score
        Formula: vote_average * log(vote_count + 1)

        Args:
            vote_average: Average rating
            vote_count: Number of votes

        Returns:
            Popularity score
        """
        import math
        return round(vote_average * math.log(vote_count + 1), 2)
