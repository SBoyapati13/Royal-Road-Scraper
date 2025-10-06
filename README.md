# Royal Road Fiction Hourly Scraper

This project scrapes data from Royal Road fiction website on an hourly basis to collect time-series data for analysis.



## Project Structure

- `scraper.py` - The main scraper module that extracts data from Royal Road
- `database.py` - Database handling for storing and retrieving scraped data
- `scheduled_scraper.py` - Entry point for the scheduled scraper task
- `setup_scheduler.ps1` - PowerShell script to set up the Windows Task Scheduler
- `setup_scheduler.bat` - Batch file to set up the Windows Task Scheduler with admin privileges
- `royal_road_eda.ipynb` - Jupyter Notebook for Exploratory Data Analysis
- `requirements.txt` - Python package dependencies

## Setup Instructions

1. Make sure all required packages are installed:
   ```
   pip install -r requirements.txt
   ```

2. Set up the hourly scheduler:

   **Option 1: Using the batch file (Recommended)**
   
   Right-click on `setup_scheduler.bat` and select "Run as Administrator", then follow the prompts.
   
   **Option 2: Using PowerShell**
   ```
   powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
   ```

3. Either method will create a Windows Task Scheduler task named "RoyalRoadScraper" that runs hourly.

4. If you encounter permission issues, you can manually create the task in Task Scheduler:
   - Open Task Scheduler (taskschd.msc)
   - Create a Basic Task named "RoyalRoadScraper"
   - Set it to run hourly
   - Set the action to run program: `<python executable path>`
   - With arguments: `<path to scheduled_scraper.py>`
   - Set "Start in" to the project directory



## How It Works

- The scheduler will run the `scheduled_scraper.py` script every hour
- Data is scraped from Royal Road's trending page
- Stories are stored in a SQLite database in the `data` directory
- Each scraping session is logged in the database and in log files

## Log Files

Log files are stored in the `logs` directory with timestamps in the filename format:
```
logs/scraper_YYYYMMDD_HHMMSS.log
```

## Manual Execution

To manually trigger the scraper:

```
python scheduled_scraper.py
```

## Task Scheduler Management

To manually run the scheduled task:
```
schtasks /Run /TN "RoyalRoadScraper"
```

To check the status of the scheduled task:
```
schtasks /Query /TN "RoyalRoadScraper"
```

To remove the scheduled task:
```
schtasks /Delete /TN "RoyalRoadScraper" /F
```

## Time-series Analysis

The hourly data collection enables time-series analysis in the `royal_road_eda.ipynb` notebook, tracking how story metrics change over time:

- Changes in views, ratings, and followers
- Daily/weekly trends in story popularity
- Growth rates for different genres
- Impact of new chapter releases on metrics