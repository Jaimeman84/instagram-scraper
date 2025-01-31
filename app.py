import streamlit as st
import json
from datetime import datetime
from scraper_service import InstagramScraperService
from models import ScraperConfig
import logging
import re
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
from io import BytesIO
import base64
import pyperclip
import time
import uuid
from typing import Dict

# Load environment variables at startup
load_dotenv()

# Initialize session state variables
if 'scraper' not in st.session_state:
    try:
        st.session_state.scraper = InstagramScraperService()
    except ValueError as e:
        st.error(f"Error: {str(e)}")
        st.stop()

if 'button_states' not in st.session_state:
    st.session_state.button_states = {}

def is_valid_instagram_url(url: str) -> bool:
    """Validate if the URL is a proper Instagram URL."""
    url = url.strip()
    if not url:
        return False
    
    # Basic Instagram URL pattern
    pattern = r'^https?:\/\/(www\.)?instagram\.com\/[a-zA-Z0-9_.]+\/?$'
    return bool(re.match(pattern, url))

def fetch_image(url: str, max_retries: int = 3) -> bytes:
    """
    Fetch image data from URL with appropriate headers and retry logic.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.instagram.com/'
    }
    
    session = requests.Session()
    
    retry_strategy = requests.adapters.Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        if "NameResolutionError" in str(e) or "getaddrinfo failed" in str(e):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            path = parsed.path
            params = parse_qs(parsed.query)
            
            cdn_domains = [
                "scontent-iad3-1.cdninstagram.com",
                "scontent-iad3-2.cdninstagram.com",
                "scontent-lga3-1.cdninstagram.com",
                "scontent-lga3-2.cdninstagram.com",
                "scontent-dfw5-1.cdninstagram.com",
                "scontent-dfw5-2.cdninstagram.com"
            ]
            
            for domain in cdn_domains:
                try:
                    alt_url = f"https://{domain}{path}?{parsed.query}"
                    response = session.get(alt_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    return response.content
                except requests.exceptions.RequestException:
                    continue
            
        raise

def encode_image(image_data: bytes) -> str:
    """Convert image data to base64 string."""
    return base64.b64encode(image_data).decode('utf-8')

def create_copy_button(text: str, button_key: str) -> None:
    """Create a copy button with feedback state."""
    if button_key not in st.session_state.button_states:
        st.session_state.button_states[button_key] = False
    
    # Create columns for button layout
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("📋 Copy", key=f"copy_{button_key}"):
            pyperclip.copy(text)
            st.session_state.button_states[button_key] = True
            time.sleep(0.1)  # Small delay to ensure state updates
    
    with col2:
        if st.session_state.button_states[button_key]:
            st.success("Copied! ✅")
            # Reset the state after 2 seconds
            time.sleep(2)
            st.session_state.button_states[button_key] = False

def display_post_card(post):
    """Display a single Instagram post in a card format."""
    st.markdown("""
    <style>
    .post-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin: 20px 0;
        border: 1px solid #333;
    }
    .image-container {
        position: relative;
        width: 100%;
        padding-bottom: 100%;
        overflow: hidden;
        background-color: #2C2C2C;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .image-container img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .post-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .engagement-stats {
        background-color: #2C2C2C;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .comment-box {
        padding: 8px;
        background-color: #2C2C2C;
        border-radius: 4px;
        margin: 4px 0;
        color: #E0E0E0;
    }
    hr {
        border: none;
        height: 1px;
        background-color: #333;
        margin: 10px 0;
    }
    .stTextArea textarea {
        background-color: #2C2C2C;
        color: #E0E0E0;
        border: 1px solid #333;
    }
    .stExpander {
        border: 1px solid #333;
        background-color: #1E1E1E;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        
        # Create columns for layout
        col1, col2 = st.columns([2, 3])
        
        with col1:
            try:
                # Try to get image URL from different possible sources
                image_url = None
                if post.get('displayUrl'):
                    image_url = str(post['displayUrl'])
                elif post.get('images') and len(post['images']) > 0:
                    image_url = str(post['images'][0])

                if image_url:
                    try:
                        image_data = fetch_image(image_url)
                        image_base64 = encode_image(image_data)
                        
                        st.markdown(f"""
                            <div style="
                                width: 100%;
                                padding-bottom: 100%;
                                position: relative;
                                overflow: hidden;
                                border-radius: 8px;
                                background-color: #2C2C2C;
                            ">
                                <img 
                                    src="data:image/jpeg;base64,{image_base64}"
                                    style="
                                        position: absolute;
                                        top: 0;
                                        left: 0;
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                    "
                                />
                            </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as img_error:
                        st.error(f"Could not load image: {str(img_error)}")
                        st.markdown(f"[View Image on Instagram]({post.get('url', image_url)})")
                else:
                    st.markdown("""
                        <div style="
                            width: 100%;
                            padding-bottom: 100%;
                            position: relative;
                            background-color: #2C2C2C;
                            border-radius: 8px;
                        ">
                            <div style="
                                position: absolute;
                                top: 50%;
                                left: 50%;
                                transform: translate(-50%, -50%);
                                color: #E0E0E0;
                                text-align: center;
                            ">
                                📷 No image available
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Show additional images if available
                if post.get('images') and len(post['images']) > 1:
                    with st.expander("📸 Additional Images"):
                        for idx, img_url in enumerate(post['images'][1:], 1):
                            try:
                                image_data = fetch_image(str(img_url))
                                image_base64 = encode_image(image_data)
                                st.markdown(f"""
                                    <div style="
                                        width: 100%;
                                        padding-bottom: 100%;
                                        position: relative;
                                        overflow: hidden;
                                        border-radius: 8px;
                                        background-color: #2C2C2C;
                                        margin: 10px 0;
                                    ">
                                        <img 
                                            src="data:image/jpeg;base64,{image_base64}"
                                            style="
                                                position: absolute;
                                                top: 0;
                                                left: 0;
                                                width: 100%;
                                                height: 100%;
                                                object-fit: cover;
                                            "
                                        />
                                    </div>
                                """, unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Could not load additional image {idx}: {str(e)}")
                                st.markdown(f"[View Additional Image {idx}]({img_url})")
                
            except Exception as e:
                st.error(f"Error processing images: {str(e)}")
                if post.get('url'):
                    st.markdown(f"[View Original Post on Instagram]({post['url']})")
        
        with col2:
            # Post header with username, timestamp, and link
            col2_1, col2_2 = st.columns([3, 1])
            with col2_1:
                st.markdown(f"**@{post.get('ownerUsername', 'unknown')}**")
                if post.get('timestamp'):
                    try:
                        timestamp = datetime.fromisoformat(str(post['timestamp']).replace('Z', '+00:00'))
                        st.caption(f"Posted: {timestamp.strftime('%B %d, %Y at %I:%M %p')}")
                    except:
                        st.caption(f"Posted: {post['timestamp']}")
            with col2_2:
                post_url = f"https://www.instagram.com/p/{post.get('shortCode')}/"
                st.markdown(f"[View on Instagram]({post_url})")
            
            # Engagement metrics
            st.markdown('<div class="engagement-stats">', unsafe_allow_html=True)
            cols = st.columns(3)
            with cols[0]:
                st.metric("👍 Likes", f"{post.get('likesCount', 0):,}")
            with cols[1]:
                st.metric("💬 Comments", f"{post.get('commentsCount', 0):,}")
            with cols[2]:
                if post.get('isSponsored'):
                    st.info("📢 Sponsored")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Caption with copy button
            if post.get('caption'):
                with st.expander("📝 Caption", expanded=True):
                    caption_text = str(post['caption'])
                    st.text_area(
                        label="Post Caption",
                        value=caption_text,
                        height=150,  # Increased height
                        key=f"caption_{post.get('shortCode')}",
                        label_visibility="collapsed"
                    )
            
            # Hashtags with copy button
            if post.get('hashtags'):
                with st.expander("🏷️ Hashtags", expanded=True):
                    hashtags = [str(tag) for tag in post['hashtags']]
                    hashtags_text = ' '.join([f'#{tag}' for tag in hashtags])
                    st.text_area(
                        label="Post Hashtags",
                        value=hashtags_text,
                        height=100,  # Increased height
                        key=f"hashtags_{post.get('shortCode')}",
                        label_visibility="collapsed"
                    )
            
            # Comments
            if post.get('latestComments'):
                with st.expander("💬 Latest Comments"):
                    for comment in post['latestComments'][:3]:
                        st.markdown(f"""
                        <div class="comment-box">
                            <strong style="color: #E0E0E0;">@{comment.get('ownerUsername', 'unknown')}</strong>
                            <br/>
                            <span style="color: #E0E0E0;">{str(comment.get('text', ''))}</span>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_analytics(posts):
    """Display analytics and insights about the scraped posts."""
    st.header("📊 Analytics Overview")
    
    # Create metrics for overall engagement
    total_likes = sum(post.get('likesCount', 0) for post in posts)
    total_comments = sum(post.get('commentsCount', 0) for post in posts)
    avg_likes = total_likes // len(posts) if posts else 0
    avg_comments = total_comments // len(posts) if posts else 0
    
    # Display metrics in columns with a modern look
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Total Posts", len(posts))
        with col2:
            st.metric("❤️ Total Likes", f"{total_likes:,}")
        with col3:
            st.metric("💬 Avg. Likes/Post", f"{avg_likes:,}")
        with col4:
            st.metric("💭 Avg. Comments/Post", f"{avg_comments:,}")

    # Create tabs for different analytics views
    tab1, tab2 = st.tabs(["📈 Engagement Analysis", "🏷️ Hashtag Analysis"])
    
    with tab1:
        st.subheader("Post Engagement Details")
        # Create a DataFrame for the engagement data
        engagement_data = []
        for post in posts:
            engagement_data.append({
                'Date': datetime.fromisoformat(str(post.get('timestamp')).replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M'),
                'Likes': post.get('likesCount', 0),
                'Comments': post.get('commentsCount', 0),
                'URL': f"https://www.instagram.com/p/{post.get('shortCode')}/",
                'Caption': str(post.get('caption', ''))[:100] + '...' if post.get('caption') else ''
            })
        
        # Display engagement data in an interactive table
        st.dataframe(
            engagement_data,
            column_config={
                "Date": st.column_config.DatetimeColumn("Posted Date", format="D MMM YYYY, h:mm a"),
                "URL": st.column_config.LinkColumn("Post Link"),
                "Caption": st.column_config.TextColumn("Caption Preview", width="medium"),
                "Likes": st.column_config.NumberColumn("👍 Likes", format="%d"),
                "Comments": st.column_config.NumberColumn("💬 Comments", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

    with tab2:
        st.subheader("Hashtag Analysis")
        # Create hashtag statistics
        hashtag_stats = {}
        for post in posts:
            for tag in post.get('hashtags', []):
                tag = str(tag)
                if tag in hashtag_stats:
                    hashtag_stats[tag]['count'] += 1
                    hashtag_stats[tag]['total_likes'] += post.get('likesCount', 0)
                    hashtag_stats[tag]['total_comments'] += post.get('commentsCount', 0)
                else:
                    hashtag_stats[tag] = {
                        'count': 1,
                        'total_likes': post.get('likesCount', 0),
                        'total_comments': post.get('commentsCount', 0)
                    }
        
        # Convert to list and sort by count
        hashtag_data = [
            {
                'Hashtag': f"#{tag}",
                'Usage Count': stats['count'],
                'Avg. Likes': stats['total_likes'] // stats['count'],
                'Avg. Comments': stats['total_comments'] // stats['count']
            }
            for tag, stats in hashtag_stats.items()
        ]
        hashtag_data.sort(key=lambda x: x['Usage Count'], reverse=True)
        
        # Display hashtag data in an interactive table
        st.dataframe(
            hashtag_data,
            column_config={
                "Hashtag": st.column_config.Column("Hashtag", width="medium"),
                "Usage Count": st.column_config.NumberColumn("🔄 Usage Count", format="%d"),
                "Avg. Likes": st.column_config.NumberColumn("❤️ Avg. Likes", format="%d"),
                "Avg. Comments": st.column_config.NumberColumn("💬 Avg. Comments", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Instagram Scraper",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Instagram Scraper")
    
    # Show setup instructions
    with st.expander("⚙️ Setup Instructions", expanded=True):
        st.markdown("""
        ### Required: Set up Apify API Token
        
        1. Sign up for an Apify account at [apify.com](https://apify.com)
        2. Get your API token from [apify.com/account#/integrations](https://console.apify.com/account#/integrations)
        3. Create a `.env` file in the project root with:
        ```
        APIFY_API_TOKEN=your_api_token_here
        ```
        """)
    
    st.markdown("""
    ### Enter Instagram URLs
    Enter one or more public Instagram profile URLs to scrape. 
    
    Examples:
    - Profile: `https://www.instagram.com/humansofny/`
    - Profile: `https://www.instagram.com/natgeo/`
    - Profile: `https://www.instagram.com/aivanai.supercars/`
    """)
    
    # Create the form
    with st.form("scraper_form"):
        # Form inputs
        urls = st.text_area(
            "Instagram URLs (one per line)",
            help="Enter Instagram profile URLs to scrape",
            placeholder="https://www.instagram.com/username/"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            results_limit = st.number_input(
                "Results Limit",
                min_value=1,
                max_value=1000,
                value=200,
                help="Maximum number of posts to scrape"
            )
            search_type = st.selectbox(
                "Search Type",
                options=["user", "hashtag", "place"],
                help="Type of Instagram content to search"
            )
            
        with col2:
            results_type = st.selectbox(
                "Results Type",
                options=["posts", "comments", "details", "mentions", "stories"],
                help="Type of data to retrieve: posts, comments, profile details, mentions, or stories"
            )
            search_limit = st.number_input(
                "Search Limit",
                min_value=1,
                max_value=100,
                value=1,
                help="Number of search results to process"
            )
        
        # Add advanced options
        advanced_options = st.expander("Advanced Options")
        with advanced_options:
            enhance_search = st.checkbox(
                "Enhance User Search with Facebook Page",
                value=False,
                help="Include Facebook page information if available"
            )
            is_reel_feed = st.checkbox(
                "Is User Reel Feed URL",
                value=False,
                help="Check if the URL is for Reels"
            )
            is_tagged_feed = st.checkbox(
                "Is User Tagged Feed URL",
                value=False,
                help="Check if the URL is for tagged posts"
            )
            add_parent_data = st.checkbox(
                "Add Parent Data",
                value=False,
                help="Include parent post data for comments"
            )
        
        submitted = st.form_submit_button("Start Scraping")

    # Process form submission and show results outside the form
    if submitted:
        if not urls.strip():
            st.error("Please enter at least one Instagram URL")
            return
        
        # Validate URLs
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        invalid_urls = [url for url in url_list if not is_valid_instagram_url(url)]
        
        if invalid_urls:
            st.error(f"Invalid Instagram URLs detected:\n" + "\n".join(invalid_urls))
            st.info("URLs should be in the format: https://www.instagram.com/username/")
            return
            
        # Create config from form data with all required fields
        config = ScraperConfig(
            directUrls=url_list,
            resultsLimit=results_limit,
            resultsType=results_type,
            searchLimit=search_limit,
            searchType=search_type,
            addParentData=add_parent_data,
            enhanceUserSearchWithFacebookPage=enhance_search,
            isUserReelFeedURL=is_reel_feed,
            isUserTaggedFeedURL=is_tagged_feed
        )
        
        with st.spinner('Scraping data... This may take a few minutes.'):
            try:
                results = st.session_state.scraper.scrape_posts(config)
                
                if not results:
                    st.warning("No data found for the provided URLs")
                    return
                
                # Convert results to JSON and store for download
                json_results = [result.model_dump() for result in results]
                st.session_state.scraped_data = json.dumps(json_results, default=str, indent=2)
                
                # Show success message
                st.success(f"Successfully scraped {len(results)} posts! 🎉")
                
                # Display analytics
                display_analytics(json_results)
                
                # Display posts in a visually appealing way
                st.subheader("📱 Instagram Posts")
                for post in json_results:
                    display_post_card(post)
                
                # Download button
                st.sidebar.markdown("### 💾 Export Data")
                st.sidebar.download_button(
                    label="📥 Download JSON",
                    data=st.session_state.scraped_data,
                    file_name=f"instagram_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"An error occurred while scraping: {str(e)}")

if __name__ == "__main__":
    main()