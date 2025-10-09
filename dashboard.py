import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="📚 Royal Road Trending Stories Analyzer",
    page_icon="📚",
    layout="wide"
)

@st.cache_data
def load_data():
    """Load data from SQLite database"""
    try:
        db_path = Path('data/royal_road.db')
        conn = sqlite3.connect(db_path)
        
        # Modified query to get the latest snapshot data for each story
        query = """
        SELECT s.royal_road_id, s.title, s.url, s.genres, 
               COALESCE(ss.rating, 0) as rating,
               COALESCE(ss.followers, 0) as followers,
               COALESCE(ss.views, 0) as views,
               COALESCE(ss.chapters, 0) as chapters,
               ss.snapshot_date
        FROM stories s
        JOIN (
            SELECT story_id, MAX(snapshot_date) as max_date
            FROM story_snapshots
            GROUP BY story_id
        ) latest ON s.id = latest.story_id
        JOIN story_snapshots ss ON latest.story_id = ss.story_id AND latest.max_date = ss.snapshot_date
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Expand genres into a list
        df['genre_list'] = df['genres'].str.split(',')
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def create_genre_chart(df):
    """Create genre distribution chart"""
    # Flatten genre lists into a single series
    all_genres = [genre.strip() for genres in df['genre_list'] for genre in genres if isinstance(genres, list)]
    genre_counts = pd.Series(all_genres).value_counts()
    
    # Create horizontal bar chart
    fig = px.bar(
        x=genre_counts.values[:15],
        y=genre_counts.index[:15],
        orientation='h',
        title='Top 15 Genres in Trending Stories',
        labels={'x': 'Number of Stories', 'y': 'Genre'}
    )
    fig.update_layout(showlegend=False)
    return fig

def create_genre_combinations_chart(df):
    """Analyze common genre combinations"""
    genre_pairs = []
    for genres in df['genre_list']:
        if isinstance(genres, list) and len(genres) > 1:
            # Get all possible pairs of genres
            pairs = [(g1.strip(), g2.strip()) 
                    for i, g1 in enumerate(genres) 
                    for g2 in genres[i+1:]]
            genre_pairs.extend(pairs)
    
    pair_counts = pd.Series(genre_pairs).value_counts()
    
    # Create horizontal bar chart for top genre combinations
    fig = px.bar(
        x=pair_counts.values[:10],
        y=[f"{pair[0]} + {pair[1]}" for pair in pair_counts.index[:10]],
        orientation='h',
        title='Top 10 Genre Combinations in Trending Stories',
        labels={'x': 'Number of Stories', 'y': 'Genre Combination'}
    )
    fig.update_layout(showlegend=False)
    return fig

def main():
    st.title("📚 Royal Road Trending Stories Analysis")
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Stories", len(df))
    with col2:
        st.metric("Total Genres", len(set([g.strip() for genres in df['genre_list'] for g in genres if isinstance(genres, list)])))
    with col3:
        avg_chapters = int(df['chapters'].mean())
        st.metric("Avg Chapters", avg_chapters)
    with col4:
        avg_views = int(df['views'].mean())
        st.metric("Avg Views", f"{avg_views:,}")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["🎭 Genres", "🔗 Genre Combinations", "📊 Story List", "📈 Time Series"])
    
    with tab1:
        st.plotly_chart(create_genre_chart(df), width='stretch')
    
    with tab2:
        st.plotly_chart(create_genre_combinations_chart(df), width='stretch')
    
    with tab3:
        # Show story list with genres
        story_df = df[['title', 'genres', 'chapters', 'views', 'snapshot_date']].copy()
        story_df['views'] = story_df['views'].apply(lambda x: f"{x:,}")
        story_df['snapshot_date'] = pd.to_datetime(story_df['snapshot_date']).dt.strftime('%Y-%m-%d')
        story_df.rename(columns={'snapshot_date': 'Last Updated'}, inplace=True)
        st.dataframe(story_df, width='stretch')
        
    with tab4:
        st.subheader("Time Series Analysis")
        # Create a function to load time series data
        @st.cache_data
        def load_time_series_data():
            db_path = Path('data/royal_road.db')
            conn = sqlite3.connect(db_path)
            query = """
            SELECT s.title, ss.snapshot_date, ss.views, ss.followers, ss.rating
            FROM stories s
            JOIN story_snapshots ss ON s.id = ss.story_id
            ORDER BY s.title, ss.snapshot_date
            """
            ts_df = pd.read_sql_query(query, conn)
            conn.close()
            ts_df['snapshot_date'] = pd.to_datetime(ts_df['snapshot_date'])
            return ts_df
            
        ts_df = load_time_series_data()
        
        # Find stories with multiple snapshots
        story_counts = ts_df.groupby('title')['snapshot_date'].nunique()
        multi_snapshot_stories = story_counts[story_counts > 1].index.tolist()
        
        if len(multi_snapshot_stories) > 0:
            # Create a dropdown to select a story
            selected_story = st.selectbox("Select a story to see its metrics over time:", multi_snapshot_stories)
            
            # Filter data for the selected story
            story_data = ts_df[ts_df['title'] == selected_story]
            
            # Create a time series plot
            fig = px.line(
                story_data, 
                x='snapshot_date', 
                y=['views', 'followers'], 
                title=f'Metrics Over Time for "{selected_story}"',
                labels={'snapshot_date': 'Date', 'value': 'Count', 'variable': 'Metric'}
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, width='stretch')
            
            # Create a second chart for rating
            if not story_data['rating'].isna().all():
                fig2 = px.line(
                    story_data,
                    x='snapshot_date',
                    y='rating',
                    title=f'Rating Over Time for "{selected_story}"',
                    labels={'snapshot_date': 'Date', 'rating': 'Rating'}
                )
                fig2.update_layout(hovermode="x unified")
                st.plotly_chart(fig2, width='stretch')
                
            # Calculate and show growth metrics if we have at least two data points
            if len(story_data) >= 2:
                st.subheader("Growth Metrics")
                
                # Calculate days between first and last snapshot
                story_data = story_data.sort_values('snapshot_date')
                first_snapshot = story_data.iloc[0]
                last_snapshot = story_data.iloc[-1]
                days_between = (last_snapshot['snapshot_date'] - first_snapshot['snapshot_date']).days
                
                if days_between > 0:
                    # Calculate growth metrics
                    views_growth = last_snapshot['views'] - first_snapshot['views']
                    views_per_day = views_growth / days_between
                    
                    followers_growth = last_snapshot['followers'] - first_snapshot['followers']
                    followers_per_day = followers_growth / days_between
                    
                    # Create columns for metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Days Tracked", days_between)
                    with col2:
                        st.metric("Views Growth", f"{views_growth:,}", f"{views_per_day:.1f}/day")
                    with col3:
                        st.metric("Followers Growth", f"{followers_growth:,}", f"{followers_per_day:.1f}/day")
                        
                    # Calculate percentage changes if possible
                    if first_snapshot['views'] > 0:
                        views_pct = (last_snapshot['views'] / first_snapshot['views'] - 1) * 100
                        st.metric("Views % Change", f"{views_pct:.1f}%")
                    
                    if first_snapshot['followers'] > 0:
                        followers_pct = (last_snapshot['followers'] / first_snapshot['followers'] - 1) * 100
                        st.metric("Followers % Change", f"{followers_pct:.1f}%")
                    
                    # Show rating change if available
                    if not pd.isna(first_snapshot['rating']) and not pd.isna(last_snapshot['rating']):
                        rating_change = last_snapshot['rating'] - first_snapshot['rating']
                        st.metric("Rating Change", f"{rating_change:.2f}")
            
            # Add a divider
            st.markdown("---")
            
            # Overall growth trends section
            st.subheader("Overall Growth Trends")
            
            # Calculate growth for all stories with multiple snapshots
            growth_data = []
            
            # For each story with multiple snapshots
            for story in multi_snapshot_stories:
                story_data = ts_df[ts_df['title'] == story].sort_values('snapshot_date')
                
                # Need at least 2 snapshots
                if len(story_data) < 2:
                    continue
                
                # Get first and last snapshot
                first = story_data.iloc[0]
                last = story_data.iloc[-1]
                days = (last['snapshot_date'] - first['snapshot_date']).days
                
                # Skip if less than 1 day
                if days < 1:
                    continue
                
                # Calculate metrics
                views_change = last['views'] - first['views']
                views_per_day = views_change / days
                
                followers_change = last['followers'] - first['followers']
                followers_per_day = followers_change / days
                
                # Add to growth data
                growth_data.append({
                    'title': story,
                    'days': days,
                    'views_change': views_change,
                    'views_per_day': views_per_day,
                    'followers_change': followers_change,
                    'followers_per_day': followers_per_day,
                    'initial_views': first['views'],
                    'initial_followers': first['followers']
                })
            
            if growth_data:
                growth_df = pd.DataFrame(growth_data)
                
                # Create scatter plot of growth vs initial popularity
                metric = st.selectbox("Select Growth Metric:", ["Views", "Followers"])
                
                if metric == "Views":
                    fig = px.scatter(
                        growth_df, 
                        x='initial_views', 
                        y='views_per_day',
                        hover_name='title',
                        labels={
                            'initial_views': 'Initial Views',
                            'views_per_day': 'Views Growth Per Day'
                        },
                        title='Views Growth Rate vs Initial Popularity'
                    )
                else:
                    fig = px.scatter(
                        growth_df, 
                        x='initial_followers', 
                        y='followers_per_day',
                        hover_name='title',
                        labels={
                            'initial_followers': 'Initial Followers',
                            'followers_per_day': 'Followers Growth Per Day'
                        },
                        title='Followers Growth Rate vs Initial Popularity'
                    )
                
                # Add a trend line
                fig.update_layout(hovermode="closest")
                st.plotly_chart(fig, width='stretch')
                
                # Show top growers
                st.subheader("Top Growing Stories")
                if metric == "Views":
                    top_growers = growth_df.sort_values('views_per_day', ascending=False).head(10)
                    top_growers = top_growers[['title', 'days', 'views_change', 'views_per_day']]
                    top_growers.columns = ['Story', 'Days Tracked', 'Total Views Growth', 'Views/Day']
                else:
                    top_growers = growth_df.sort_values('followers_per_day', ascending=False).head(10)
                    top_growers = top_growers[['title', 'days', 'followers_change', 'followers_per_day']]
                    top_growers.columns = ['Story', 'Days Tracked', 'Total Followers Growth', 'Followers/Day']
                
                st.dataframe(top_growers, width='stretch')
        else:
            st.info("No stories with multiple snapshots available yet. Run the scraper multiple times over different days to collect time-series data.")

if __name__ == "__main__":
    main()