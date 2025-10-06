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
        
        # Modified query to focus on all stories and their genres
        query = """
        SELECT title, url, genres, 
               COALESCE(rating, 0) as rating,
               COALESCE(followers, 0) as followers,
               COALESCE(views, 0) as views,
               COALESCE(chapters, 0) as chapters
        FROM stories
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
    tab1, tab2, tab3 = st.tabs(["🎭 Genres", "🔗 Genre Combinations", "📊 Story List"])
    
    with tab1:
        st.plotly_chart(create_genre_chart(df), width='stretch')
    
    with tab2:
        st.plotly_chart(create_genre_combinations_chart(df), width='stretch')
    
    with tab3:
        # Show story list with genres
        story_df = df[['title', 'genres', 'chapters', 'views']].copy()
        story_df['views'] = story_df['views'].apply(lambda x: f"{x:,}")
        st.dataframe(story_df, width='stretch')

if __name__ == "__main__":
    main()