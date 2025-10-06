# Royal Road Fiction Analysis

A data analysis project for tracking and analyzing trending stories on Royal Road, a popular web fiction platform.

## Features

- **Web Scraping**: Collection of story data from Royal Road's trending page
- **Data Storage**: SQLite database for efficient storage and retrieval of story metrics
- **Exploratory Data Analysis**: Comprehensive analysis of story metrics, genres, and trends
- **Visualization**: Interactive charts and plots to explore the data
- **Time-series Analysis**: Track changes in story metrics over time with multiple manual data collections

## Project Structure

- `scraper.py` - The main scraper module that extracts data from Royal Road
- `database.py` - Database handling for storing and retrieving scraped data
- `royal_road_eda.ipynb` - Jupyter notebook for exploratory data analysis
- `requirements.txt` - Python package dependencies

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/SBoyapati13/Royal-Road-Scraper.git
   cd Royal-Road-Scraper
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```



## Usage

### Data Collection

Run the scraper manually whenever you want to collect new data:

```
python scraper.py
```

For time-series analysis, it's recommended to run the scraper multiple times daily at regular intervals.

### Data Analysis

Open the Jupyter notebook for analysis:

```
jupyter notebook royal_road_eda.ipynb
```

The notebook provides:
- Distribution analysis of key metrics (views, ratings, followers)
- Correlation analysis between different story attributes
- Genre popularity and performance analysis
- Story length impact assessment
- Time-series analysis (when multiple data points are available)

## Database Structure

The SQLite database (`data/royal_road.db`) contains two main tables:

1. `stories` - Stores story details and metrics
   - id, title, url, rating, followers, pages, chapters, views, favorites, ratings_count, genres, scraped_date

2. `scrape_history` - Logs each scraping session
   - id, scrape_date, pages_scraped, stories_added, stories_updated, status, notes

## Data Analysis Highlights

- **Distribution Analysis**: Examine right-skewed distributions with automatic log scaling
- **Correlation Heatmaps**: Visualize relationships between different story metrics
- **Genre Analysis**: Identify popular and high-performing genres
- **Story Length Impact**: Understand how story length affects popularity metrics
- **Time-Series Insights**: Track changes in story metrics over time (requires multiple manual scrapes)

## License

MIT

## Acknowledgments

- [Royal Road](https://www.royalroad.com/) for providing the platform and data source
- All the authors who contribute to the web fiction community