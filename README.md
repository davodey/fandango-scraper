# Fandango Movie Scraper

A Python application that scrapes movie data from Fandango and syncs it with a Firestore database. The data structure matches TMDB format for seamless integration with iOS applications.

## Features

- Scrapes current movies from Fandango website
- Stores data in Firestore with TMDB-compatible structure
- Intelligent change detection - only updates movies when data changes
- Daily run support - identifies and saves only new releases
- Consistent movie ID generation for reliable tracking
- Comprehensive logging and error handling
- Dry-run mode for testing

## Project Structure

```
fandango-scraper/
├── src/
│   ├── models/
│   │   └── movie.py           # Movie data model (TMDB compatible)
│   ├── scrapers/
│   │   └── fandango_scraper.py # Fandango website scraper
│   ├── database/
│   │   └── firestore_client.py # Firestore database client
│   └── utils/
│       └── config.py           # Configuration management
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Movie Data Model

The scraper extracts and stores movies in the following TMDB-compatible format:

```python
{
    "id": int,                  # Unique identifier (required)
    "title": str,               # Movie name (required)
    "overview": str,            # Plot description (required)
    "releaseDate": str,         # Format: "yyyy-MM-dd" (optional)
    "posterPath": str,          # Relative path to poster image (optional)
    "backdropPath": str,        # Relative path to backdrop image (optional)
    "voteAverage": float,       # Rating 0-10 scale (required)
    "voteCount": int,           # Number of ratings (required)
    "popularity": float         # Popularity score (required)
}
```

## Prerequisites

- Python 3.8 or higher
- Chrome browser (for Selenium WebDriver)
- Firebase/Firestore account with credentials
- Internet connection

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd fandango-scraper
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Navigate to Project Settings > Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON file as `firebase-credentials.json` in the project root

### 5. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIRESTORE_COLLECTION=movies
SCRAPER_HEADLESS=true
LOG_LEVEL=INFO
```

## Usage

### Basic Usage

Run the scraper and sync with Firestore:

```bash
python main.py
```

### Command Line Options

```bash
# Dry run (scrape but don't save to Firestore)
python main.py --dry-run

# Run with visible browser (for debugging)
python main.py --no-headless

# Use custom config file
python main.py --config /path/to/.env
```

### Scheduled Daily Runs

#### Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * cd /path/to/fandango-scraper && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily
4. Set action to run:
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\fandango-scraper\main.py`
   - Start in: `C:\path\to\fandango-scraper`

#### Using Docker (Recommended for Production)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t fandango-scraper .
docker run -v $(pwd)/firebase-credentials.json:/app/firebase-credentials.json fandango-scraper
```

## How It Works

### 1. Scraping Process

The scraper uses Selenium WebDriver to:
- Load the Fandango movies page
- Scroll to trigger lazy-loaded content
- Extract movie information using BeautifulSoup
- Parse and normalize data to TMDB format

### 2. ID Generation

Movies are assigned consistent IDs using MD5 hash of:
- Movie title (normalized)
- Release date (if available)

This ensures the same movie gets the same ID across multiple runs.

### 3. Change Detection

Before updating Firestore, the system:
1. Retrieves all existing movies from Firestore
2. Compares each scraped movie with existing data
3. Only updates if data has changed
4. Saves new movies that don't exist

### 4. Data Sync

The sync process categorizes movies into:
- **New**: Movies not in database
- **Updated**: Movies with changed data
- **Unchanged**: Movies with identical data
- **Failed**: Movies that encountered errors

## Logging

Logs are written to:
- Console (stdout)
- Daily log file: `scraper_YYYYMMDD.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure via `LOG_LEVEL` environment variable.

## Troubleshooting

### Chrome Driver Issues

If you encounter Chrome/ChromeDriver errors:

```bash
# The webdriver-manager should auto-download, but if issues persist:
pip install --upgrade webdriver-manager
```

### Firestore Permission Errors

Ensure your service account has:
- Cloud Datastore User role
- Firebase Admin SDK Administrator role

### No Movies Found

- Check Fandango website structure hasn't changed
- Run with `--no-headless` to see browser behavior
- Check logs for specific errors
- Verify internet connection

### Memory Issues

For large scraping operations:
- Reduce batch size in `firestore_client.py`
- Run with more restrictive selectors
- Increase system memory allocation

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest tests/
```

### Code Style

```bash
# Install formatters
pip install black flake8

# Format code
black src/

# Lint code
flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Security Notes

- Never commit `firebase-credentials.json` to version control
- Keep `.env` file private
- Rotate service account keys regularly
- Use least-privilege IAM roles

## Support

For issues and questions:
- Check existing GitHub issues
- Create new issue with detailed description
- Include log files (redact sensitive info)

## Roadmap

- [ ] Add unit tests
- [ ] Support for additional movie sources
- [ ] Image download and storage
- [ ] Advanced filtering options
- [ ] GraphQL API endpoint
- [ ] Real-time sync with webhooks
- [ ] Performance monitoring

## Acknowledgments

- Built for integration with iOS TMDB-based apps
- Uses Selenium for dynamic content handling
- Firebase Admin SDK for Firestore access
