# Royal Road Fiction Analysis

A data analysis project for tracking and analyzing trending stories on Royal Road, a popular web fiction platform.

## Features

- **Web Scraping**: Collection of story data from Royal Road's trending page with robust error handling and rate limiting
- **Data Storage**: SQLite database for efficient storage and retrieval of story metrics with time-series optimization
- **Exploratory Data Analysis**: Comprehensive analysis of story metrics, genres, and trends with enhanced visualizations
- **Interactive Dashboard**: Streamlit-based web interface for exploring data with real-time insights
- **Visualization**: Interactive charts and plots with improved formatting, hover details, and statistical analysis
- **Time-series Analysis**: Track changes in story metrics over time with complete historical data preservation, adaptive period detection and enhanced dynamic visualizations

## Project Status (October 15, 2025)

**✅ Fully Operational**: All components validated and working correctly
- **Latest Analysis**: Comprehensive EDA completed with execution counts 12-20
- **Active Variables**: 89 variables loaded including LENGTH_METRICS, PERFORMANCE_METRICS, correlation_matrix, growth_df
- **Environment**: Dual Python setup (global + virtual) with all dependencies confirmed working
- **Database**: SQLite database with complete time-series tracking operational
- **Visualizations**: All charts and plots rendering correctly with enhanced features
- **Analysis Pipeline**: Full analytical framework validated from data loading through advanced visualizations

## Project Structure

- `scraper.py` - The main scraper module that extracts data from Royal Road
- `database.py` - Database handling for storing and retrieving scraped data
- `dashboard.py` - Streamlit web interface for interactive data exploration
- `royal_road_eda.ipynb` - Jupyter notebook for exploratory data analysis
- `config.py` - Centralized configuration and constants
- `utils.py` - Common utility functions for data operations
- `check_db.py` - Database status checker and statistics tool
- `requirements.txt` - Python package dependencies

## Setup

### Environment Configuration (Validated October 15, 2025)

The project supports dual Python environment configuration for maximum compatibility:

1. Clone the repository:
   ```
   git clone https://github.com/SBoyapati13/Royal-Road-Scraper.git
   cd Royal-Road-Scraper
   ```

2. Install dependencies (choose one approach):

   **Option A: Global Installation (Recommended for VS Code)**
   ```
   pip install -r requirements.txt
   ```

   **Option B: Virtual Environment Setup**
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```
   python check_db.py  # Check database and environment status
   ```

### Jupyter Notebook Setup

For data analysis in VS Code:
1. Install Jupyter extension in VS Code
2. Open `royal_road_eda.ipynb`
3. Select Python kernel (global Python or .venv kernel will both work)
4. All 19 analysis cells are ready to run with validated execution

## Usage

### Data Collection

Run the scraper manually whenever you want to collect new data:

```
python scraper.py
```

For time-series analysis, it's recommended to run the scraper multiple times daily at regular intervals.

### Interactive Dashboard

Launch the Streamlit dashboard for web-based data exploration:

```
streamlit run dashboard.py
```

The dashboard provides:
- Real-time data overview with key metrics
- Genre analysis and distribution charts
- Interactive story listings
- Time-series visualization for tracked stories
- Growth rate analysis and comparisons

### Data Analysis

Open the Jupyter notebook for detailed analysis:

```
jupyter notebook royal_road_eda.ipynb
```

### Database Status

Check your database status anytime:

```
python check_db.py
```

The notebook provides:
- Distribution analysis of key metrics (views, ratings, followers)
- Correlation analysis between different story attributes
- Genre popularity and performance analysis
- Story length impact assessment
- Time-series analysis (when multiple data points are available)

## Database Structure

The SQLite database (`data/royal_road.db`) uses a time-series optimized structure with three main tables:

1. `stories` - Stores basic story information
   - id, royal_road_id, title, url, genres, first_seen, last_updated
   - Uses the Royal Road ID as a unique identifier (extracted from the URL)
   - Handles title changes gracefully by tracking the persistent royal_road_id

2. `story_snapshots` - Stores historical metrics for each story
   - id, story_id, snapshot_date, rating, followers, pages, chapters, views, favorites, ratings_count

3. `scrape_history` - Logs each scraping session
   - id, scrape_date, pages_scraped, stories_added, stories_updated, status, notes

This structure preserves the complete history of each story's metrics over time, enabling robust time-series analysis without overwriting historical data. The system can properly track stories even when their titles (and thus URLs) change over time.

## Data Analysis Highlights

- **Distribution Analysis**: Examine right-skewed distributions with automatic log scaling
- **Correlation Heatmaps**: Visualize relationships between different story metrics
- **Genre Analysis**: Identify popular and high-performing genres
- **Story Length Impact**: Understand how story length affects popularity metrics
- **Time-Series Insights**: Adaptive time-series analysis with:
  - Automatic period detection based on available data span
  - Growth rate visualization for views and followers
  - Genre performance over time
  - Story popularity trend visualization
  - Impact analysis of chapter updates on growth rates
  - Relative growth comparison between stories

## Time-Series Analysis Features

The time-series analysis component leverages the complete historical snapshot database to provide comprehensive insights:

- **Complete Historical Data**:
  - Every data point is preserved in the database
  - No overwriting of previous values
  - Full history available for each story

- **Adaptive Time Binning**: 
  - Daily analysis for short collection periods (less than a week)
  - Weekly analysis for medium collection periods (1-4 weeks)
  - Monthly analysis for longer collection periods (1+ months)

- **Growth Metrics**:
  - Daily growth rates calculation for views and followers
  - Snapshot-to-snapshot change analysis
  - Statistical analysis of growth patterns (mean, median, min, max)
  - Distribution visualization of growth rates

- **Story Performance Tracking**:
  - Time-series visualization of top stories' metrics
  - Normalized relative growth comparison
  - Impact analysis of chapter updates on growth rates

- **Genre Performance Over Time**:
  - Growth rate comparison across genres
  - Identification of trending genres
  - Visualization of genre performance differences

- **Advanced Visualizations**:
  - Interactive time-series plots
  - Growth rate distribution histograms
  - Growth vs. initial popularity scatter plots
  - Genre performance bar charts

To use these features, simply run the scraper multiple times on different days to collect time-series data.

## License

MIT

## Acknowledgments

- [Royal Road](https://www.royalroad.com/) for providing the platform and data source
- All the authors who contribute to the web fiction community