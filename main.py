#!/usr/bin/env python3
"""
Fandango Movie Scraper
Scrapes movie data from Fandango and syncs with Firestore
"""
import sys
import logging
import argparse
from datetime import datetime

from src.scrapers.fandango_scraper import FandangoScraper
from src.database.firestore_client import FirestoreClient
from src.utils.config import Config


def setup_logging(log_level: str):
    """Set up logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Scrape Fandango movies and sync with Firestore'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to .env configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run scraper but do not save to Firestore'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode'
    )

    args = parser.parse_args()

    # Load configuration
    config = Config(env_file=args.config)
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Fandango Movie Scraper Starting")
    logger.info("=" * 60)
    logger.info(f"Configuration: {config}")

    # Validate configuration
    if not args.dry_run and not config.validate():
        logger.error("Configuration validation failed")
        return 1

    try:
        # Initialize scraper
        headless = not args.no_headless if args.no_headless else config.scraper_headless
        scraper = FandangoScraper(headless=headless)

        # Scrape movies
        logger.info("Starting movie scrape...")
        movies = scraper.scrape_movies()

        if not movies:
            logger.warning("No movies found during scrape")
            return 1

        logger.info(f"Successfully scraped {len(movies)} movies")

        # Print sample movies
        logger.info("\nSample scraped movies:")
        for movie in movies[:3]:
            logger.info(f"  - {movie.title} (ID: {movie.id}, Rating: {movie.voteAverage})")

        # Sync with Firestore
        if args.dry_run:
            logger.info("\nDRY RUN: Skipping Firestore sync")
            logger.info(f"Would have synced {len(movies)} movies")
        else:
            logger.info("\nSyncing with Firestore...")
            db_client = FirestoreClient(
                credentials_path=config.firebase_credentials_path,
                collection_name=config.collection_name
            )

            stats = db_client.sync_movies(movies)

            logger.info("\n" + "=" * 60)
            logger.info("Sync Results:")
            logger.info("=" * 60)
            logger.info(f"  New movies:       {stats['new']}")
            logger.info(f"  Updated movies:   {stats['updated']}")
            logger.info(f"  Unchanged movies: {stats['unchanged']}")
            logger.info(f"  Failed:           {stats['failed']}")
            logger.info("=" * 60)

        logger.info("\nScraper completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.info("\nScraper interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\nError during execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
