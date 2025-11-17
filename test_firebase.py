#!/usr/bin/env python3
"""
Test Firebase/Firestore connection
"""
import sys
from src.utils.config import Config
from src.database.firestore_client import FirestoreClient
from src.models.movie import Movie

def test_connection():
    """Test Firebase connection"""
    print("=" * 60)
    print("Testing Firebase/Firestore Connection")
    print("=" * 60)

    # Load config
    config = Config()
    print(f"\n1. Configuration loaded:")
    print(f"   Credentials path: {config.firebase_credentials_path}")
    print(f"   Collection name: {config.collection_name}")

    # Validate config
    if not config.validate():
        print("\n❌ Configuration validation failed!")
        print(f"\nMake sure '{config.firebase_credentials_path}' exists in the project directory.")
        return False

    print("   ✓ Configuration valid")

    # Initialize Firestore client
    print("\n2. Initializing Firestore client...")
    try:
        db_client = FirestoreClient(
            credentials_path=config.firebase_credentials_path,
            collection_name=config.collection_name
        )
        print("   ✓ Firestore client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize Firestore: {e}")
        return False

    # Test read operation
    print("\n3. Testing read operation...")
    try:
        existing_movies = db_client.get_all_movies()
        print(f"   ✓ Successfully read from Firestore")
        print(f"   Found {len(existing_movies)} existing movies")
    except Exception as e:
        print(f"   ❌ Failed to read from Firestore: {e}")
        return False

    # Test write operation with a sample movie
    print("\n4. Testing write operation...")
    try:
        test_movie = Movie(
            id=999999999,
            title="Test Movie - DELETE ME",
            overview="This is a test movie created to verify Firestore connectivity.",
            releaseDate="2024-01-01",
            posterPath="/test.jpg",
            backdropPath="/test_backdrop.jpg",
            voteAverage=7.5,
            voteCount=100,
            popularity=50.0
        )

        success = db_client.save_movie(test_movie)
        if success:
            print("   ✓ Successfully wrote test movie to Firestore")

            # Verify read back
            read_movie = db_client.get_movie_by_id(999999999)
            if read_movie and read_movie.title == test_movie.title:
                print("   ✓ Successfully read back test movie")

                # Clean up test movie
                db_client.delete_movie(999999999)
                print("   ✓ Successfully deleted test movie")
            else:
                print("   ⚠ Could not read back test movie")
        else:
            print("   ❌ Failed to write test movie")
            return False

    except Exception as e:
        print(f"   ❌ Failed write test: {e}")
        # Try to clean up if movie was created
        try:
            db_client.delete_movie(999999999)
        except:
            pass
        return False

    print("\n" + "=" * 60)
    print("✓ All Firebase/Firestore tests passed!")
    print("=" * 60)
    print("\nYou're ready to run the scraper with:")
    print("  python main.py --dry-run        # Test scraping without saving")
    print("  python main.py                   # Full scrape and sync")
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
