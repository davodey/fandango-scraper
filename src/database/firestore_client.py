"""
Firestore database client for movie data
"""
import logging
from typing import List, Optional, Dict, Tuple
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin

from ..models.movie import Movie


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for Firestore database operations"""

    def __init__(self, credentials_path: str, collection_name: str = "movies"):
        """
        Initialize Firestore client

        Args:
            credentials_path: Path to Firebase service account credentials JSON
            collection_name: Name of Firestore collection (default: "movies")
        """
        self.collection_name = collection_name
        self._initialize_firebase(credentials_path)
        self.db = firestore.client()
        self.collection = self.db.collection(collection_name)

    def _initialize_firebase(self, credentials_path: str):
        """
        Initialize Firebase Admin SDK

        Args:
            credentials_path: Path to credentials file
        """
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(credentials_path)
                initialize_app(cred)
                logger.info("Firebase initialized successfully")
            else:
                logger.info("Firebase already initialized")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            raise

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """
        Get a movie from Firestore by ID

        Args:
            movie_id: Movie ID

        Returns:
            Movie object or None if not found
        """
        try:
            doc = self.collection.document(str(movie_id)).get()
            if doc.exists:
                return Movie.from_dict(doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Error getting movie {movie_id}: {e}")
            return None

    def get_all_movies(self) -> Dict[int, Movie]:
        """
        Get all movies from Firestore

        Returns:
            Dictionary mapping movie ID to Movie object
        """
        movies = {}
        try:
            docs = self.collection.stream()
            for doc in docs:
                try:
                    movie = Movie.from_dict(doc.to_dict())
                    movies[movie.id] = movie
                except Exception as e:
                    logger.error(f"Error parsing movie {doc.id}: {e}")
                    continue

            logger.info(f"Retrieved {len(movies)} movies from Firestore")
        except Exception as e:
            logger.error(f"Error getting all movies: {e}")

        return movies

    def save_movie(self, movie: Movie) -> bool:
        """
        Save a movie to Firestore

        Args:
            movie: Movie object to save

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.collection.document(str(movie.id))
            doc_ref.set(movie.to_dict())
            logger.debug(f"Saved movie: {movie.title} (ID: {movie.id})")
            return True
        except Exception as e:
            logger.error(f"Error saving movie {movie.id}: {e}")
            return False

    def batch_save_movies(self, movies: List[Movie]) -> Tuple[int, int]:
        """
        Save multiple movies in a batch operation

        Args:
            movies: List of Movie objects

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        try:
            # Firestore batch has limit of 500 operations
            batch_size = 500
            for i in range(0, len(movies), batch_size):
                batch = self.db.batch()
                batch_movies = movies[i:i + batch_size]

                for movie in batch_movies:
                    try:
                        doc_ref = self.collection.document(str(movie.id))
                        batch.set(doc_ref, movie.to_dict())
                    except Exception as e:
                        logger.error(f"Error preparing movie {movie.id} for batch: {e}")
                        failed += 1
                        continue

                # Commit batch
                try:
                    batch.commit()
                    successful += len(batch_movies) - (failed - (i // batch_size) * failed)
                    logger.info(f"Batch saved {len(batch_movies)} movies")
                except Exception as e:
                    logger.error(f"Error committing batch: {e}")
                    failed += len(batch_movies)

        except Exception as e:
            logger.error(f"Error in batch save: {e}")
            failed += len(movies) - successful

        return successful, failed

    def update_movie(self, movie: Movie) -> bool:
        """
        Update an existing movie in Firestore

        Args:
            movie: Movie object with updated data

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.collection.document(str(movie.id))
            doc_ref.update(movie.to_dict())
            logger.debug(f"Updated movie: {movie.title} (ID: {movie.id})")
            return True
        except Exception as e:
            logger.error(f"Error updating movie {movie.id}: {e}")
            return False

    def delete_movie(self, movie_id: int) -> bool:
        """
        Delete a movie from Firestore

        Args:
            movie_id: ID of movie to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.document(str(movie_id)).delete()
            logger.info(f"Deleted movie ID: {movie_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting movie {movie_id}: {e}")
            return False

    def movie_exists(self, movie_id: int) -> bool:
        """
        Check if a movie exists in Firestore

        Args:
            movie_id: Movie ID to check

        Returns:
            True if exists, False otherwise
        """
        try:
            doc = self.collection.document(str(movie_id)).get()
            return doc.exists
        except Exception as e:
            logger.error(f"Error checking movie existence {movie_id}: {e}")
            return False

    def sync_movies(self, new_movies: List[Movie]) -> Dict[str, int]:
        """
        Sync movies with Firestore - add new and update changed movies

        Args:
            new_movies: List of movies from scraper

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'new': 0,
            'updated': 0,
            'unchanged': 0,
            'failed': 0
        }

        try:
            # Get existing movies from Firestore
            existing_movies = self.get_all_movies()
            logger.info(f"Syncing {len(new_movies)} scraped movies with {len(existing_movies)} existing movies")

            for movie in new_movies:
                try:
                    if movie.id in existing_movies:
                        # Check if movie has changed
                        existing_movie = existing_movies[movie.id]
                        if movie.has_changed(existing_movie):
                            if self.save_movie(movie):
                                stats['updated'] += 1
                                logger.info(f"Updated: {movie.title}")
                            else:
                                stats['failed'] += 1
                        else:
                            stats['unchanged'] += 1
                    else:
                        # New movie
                        if self.save_movie(movie):
                            stats['new'] += 1
                            logger.info(f"New movie: {movie.title}")
                        else:
                            stats['failed'] += 1
                except Exception as e:
                    logger.error(f"Error syncing movie {movie.title}: {e}")
                    stats['failed'] += 1
                    continue

            logger.info(f"Sync complete: {stats}")

        except Exception as e:
            logger.error(f"Error during sync: {e}")

        return stats
