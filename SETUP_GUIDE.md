# Local Setup Guide - Fandango Scraper

This guide will help you set up and run the Fandango scraper on your local machine.

## Prerequisites

Before you start, you need:

1. **Python 3.8+** installed
2. **Google Chrome** browser installed
3. **Git** (to clone the repository)
4. **Firebase credentials** (the JSON file you already have)

---

## Step-by-Step Setup

### 1. Check if Python is Installed

Open your terminal/command prompt and try these commands:

**macOS/Linux:**
```bash
python3 --version
```

**Windows:**
```bash
python --version
```

**If you see "command not found" or "not recognized":**

#### Install Python:

**macOS:**
```bash
brew install python3
# Or download from: https://www.python.org/downloads/
```

**Windows:**
1. Download from: https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation!
3. Restart your terminal/IDE after installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

---

### 2. Clone/Navigate to Project

If you haven't already, clone the repository:

```bash
git clone <your-repo-url>
cd fandango-scraper
```

Or if you already have it, just navigate to the folder:
```bash
cd /path/to/fandango-scraper
```

---

### 3. Run the Setup Script

We've created setup scripts to make this easier:

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

This will:
- Check if Python is installed
- Check if Chrome is installed
- Create a virtual environment for you

---

### 4. Activate Virtual Environment

A virtual environment keeps your project dependencies isolated.

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

You should see `(venv)` at the beginning of your terminal prompt.

---

### 5. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install all required packages (Selenium, BeautifulSoup, Firebase Admin, etc.)

---

### 6. Ensure Firebase Credentials are in Place

Make sure your `firebase-credentials.json` file is in the project root:

```bash
ls firebase-credentials.json    # macOS/Linux
dir firebase-credentials.json   # Windows
```

If it's not there, copy it from wherever you saved it:

```bash
cp /path/to/your/serviceAccountKey.json firebase-credentials.json
```

---

### 7. Test Firebase Connection

```bash
python test_firebase.py
```

**Expected Output:**
```
============================================================
Testing Firebase/Firestore Connection
============================================================

1. Configuration loaded:
   Credentials path: firebase-credentials.json
   Collection name: movies
   ✓ Configuration valid

2. Initializing Firestore client...
   ✓ Firestore client initialized

3. Testing read operation...
   ✓ Successfully read from Firestore
   Found X existing movies

4. Testing write operation...
   ✓ Successfully wrote test movie to Firestore
   ✓ Successfully read back test movie
   ✓ Successfully deleted test movie

============================================================
✓ All Firebase/Firestore tests passed!
============================================================
```

---

### 8. Test the Scraper (Dry Run)

Run a test without saving to Firestore:

```bash
python main.py --dry-run --no-headless
```

This will:
- Open Chrome browser (you can watch it work!)
- Navigate to Fandango
- Scrape movie data
- Show you the results
- **NOT** save to Firestore

**Expected Output:**
```
============================================================
Fandango Movie Scraper Starting
============================================================
Starting movie scrape...
Successfully scraped X movies

Sample scraped movies:
  - Movie Name 1 (ID: 123456, Rating: 7.5)
  - Movie Name 2 (ID: 789012, Rating: 8.2)
  ...

DRY RUN: Skipping Firestore sync
Would have synced X movies
```

---

### 9. Run the Full Scraper

If the dry run looks good, run for real:

```bash
python main.py
```

This will scrape Fandango and sync to Firestore.

**Expected Output:**
```
============================================================
Fandango Movie Scraper Starting
============================================================
...
Syncing with Firestore...

============================================================
Sync Results:
============================================================
  New movies:       15
  Updated movies:   3
  Unchanged movies: 42
  Failed:           0
============================================================

Scraper completed successfully!
```

---

## Common Issues & Fixes

### Issue: "python: command not found"

**Solution:** Use `python3` instead:
```bash
python3 test_firebase.py
python3 main.py
```

Or create an alias (macOS/Linux):
```bash
alias python=python3
```

---

### Issue: "No module named 'dotenv'" (or other module)

**Solution:** Make sure your virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### Issue: Chrome/ChromeDriver errors

**Solution:**
1. Make sure Chrome browser is installed
2. The scraper will auto-download ChromeDriver
3. If issues persist, try updating:
   ```bash
   pip install --upgrade selenium webdriver-manager
   ```

---

### Issue: Found 0 movies

**Possible causes:**
1. Fandango changed their HTML structure (CSS selectors need updating)
2. Network connectivity issues
3. Fandango is blocking the scraper

**Solution:**
- Run with `--no-headless` to see what's happening
- Check the scraper log file
- We may need to adjust the selectors in `src/scrapers/fandango_scraper.py`

---

### Issue: Firestore permission errors

**Solution:**
1. Check your Firebase credentials are correct
2. Verify your service account has proper permissions:
   - Cloud Datastore User
   - Firebase Admin SDK Administrator

---

## Running from Your IDE

### VS Code:

1. Open the project folder in VS Code
2. Select Python interpreter:
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
   - Type "Python: Select Interpreter"
   - Choose the one in `./venv/bin/python` or `.\venv\Scripts\python.exe`
3. Open terminal in VS Code (`Ctrl+~` or `Cmd+~`)
4. Virtual environment should activate automatically
5. Run: `python main.py`

### PyCharm:

1. Open project in PyCharm
2. PyCharm will detect `requirements.txt` and ask to install
3. Or manually: Settings → Project → Python Interpreter → Add → Existing Environment → Select `venv`
4. Right-click `main.py` → Run
5. Or use the built-in terminal (bottom panel)

### Other IDEs:

Most IDEs have similar steps:
1. Point the IDE to use the `venv` Python interpreter
2. Use the IDE's terminal (which should auto-activate venv)
3. Run the scripts

---

## Daily Automated Runs (Optional)

Once you've confirmed everything works, you can set up automatic daily runs.

### macOS/Linux (cron):

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/fandango-scraper && /path/to/fandango-scraper/venv/bin/python main.py >> logs/scraper.log 2>&1
```

### Windows (Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Fandango Scraper"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
   - Program: `C:\path\to\fandango-scraper\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\fandango-scraper`

---

## Using Docker (Alternative)

If you prefer Docker and have it installed:

```bash
# Build the image
docker-compose build

# Run once
docker-compose up

# Run in background (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Need Help?

If you're still having issues:

1. Check the log file: `scraper_YYYYMMDD.log`
2. Run with `--no-headless` to see what's happening
3. Make sure all prerequisites are installed
4. Try the setup script again

Let me know what error message you're seeing and I can help troubleshoot!
