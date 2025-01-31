from typing import List, Optional, Dict
from models import InstagramPost, ScraperConfig
import logging
import time
import os
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from pathlib import Path

class InstagramScraperService:
    def __init__(self, api_token: str = None):
        """Initialize the Instagram scraper with API token."""
        self._setup_logging()
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            raise ValueError("Apify API token is required")
        self.client = ApifyClient(self.api_token)

    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def scrape_posts(self, config: ScraperConfig) -> List[InstagramPost]:
        """
        Scrape Instagram posts using Apify API.
        
        Args:
            config (ScraperConfig): Scraping configuration
            
        Returns:
            List[InstagramPost]: List of scraped posts
        """
        try:
            # Prepare the Actor input
            run_input = {
                "directUrls": [str(url) for url in config.directUrls],
                "resultsType": config.resultsType,
                "resultsLimit": config.resultsLimit,
                "searchType": config.searchType,
                "searchLimit": config.searchLimit,
                "addParentData": config.addParentData
            }

            self.logger.info(f"Starting Apify scraper with input: {run_input}")
            
            # Run the Actor and wait for it to finish
            run = self.client.actor("your_actor_id").call(run_input=run_input)
            
            if not run:
                raise Exception("Failed to start Apify actor run")
                
            run_id = run.get('id')
            dataset_id = run.get('defaultDatasetId')
            
            self.logger.info(f"Actor run started. Run ID: {run_id}, Dataset ID: {dataset_id}")
            
            # Wait for the dataset to be ready (with timeout)
            max_wait_time = 180  # Maximum wait time in seconds
            wait_start = time.time()
            
            while True:
                try:
                    # Get the dataset
                    dataset = self.client.dataset(dataset_id)
                    items = list(dataset.iterate_items())
                    
                    if items:
                        self.logger.info(f"Retrieved {len(items)} items from dataset")
                        break
                        
                    # Check run status
                    run_info = self.client.run(run_id).get()
                    status = run_info.get('status')
                    
                    if status == 'FAILED':
                        raise Exception(f"Actor run failed: {run_info.get('errorMessage', 'Unknown error')}")
                    elif status == 'SUCCEEDED' and not items:
                        self.logger.warning("Run succeeded but no items found")
                        break
                    
                    elapsed = time.time() - wait_start
                    if elapsed > max_wait_time:
                        raise TimeoutError(f"Dataset retrieval timed out after {elapsed} seconds")
                    
                    self.logger.info(f"Waiting for results... Status: {status} ({int(elapsed)}s elapsed)")
                    time.sleep(5)
                    
                except Exception as e:
                    elapsed = time.time() - wait_start
                    if elapsed > max_wait_time:
                        raise Exception(f"Failed to retrieve dataset after {elapsed}s: {str(e)}")
                    self.logger.warning(f"Temporary error retrieving dataset: {str(e)}")
                    time.sleep(5)
            
            # Process results
            posts = []
            for idx, item in enumerate(items):
                try:
                    self.logger.info(f"Processing item {idx + 1}/{len(items)}")
                    post = self._convert_apify_to_model(item)
                    if post:
                        posts.append(post)
                        self.logger.info(f"Successfully processed post: {post.shortCode}")
                    else:
                        self.logger.warning(f"Skipped item {idx + 1} - conversion returned None")
                except Exception as e:
                    self.logger.error(f"Error processing item {idx + 1}: {str(e)}")
                    continue

            self.logger.info(f"Successfully scraped {len(posts)} posts out of {len(items)} items")
            return posts

        except Exception as e:
            self.logger.error(f"Error running Apify scraper: {str(e)}", exc_info=True)
            raise

    def _convert_apify_to_model(self, item: Dict) -> Optional[InstagramPost]:
        """Convert Apify output to InstagramPost model."""
        try:
            # Log the raw item structure
            self.logger.info(f"Raw item keys: {item.keys()}")
            self.logger.info(f"Processing item with URL: {item.get('url', 'No URL')} and type: {item.get('type', 'No type')}")
            
            # Handle timestamp format
            timestamp_str = item.get('timestamp')
            if timestamp_str:
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str.replace('Z', '+00:00')
                timestamp = datetime.fromisoformat(timestamp_str)
                self.logger.info(f"Parsed timestamp: {timestamp}")
            else:
                timestamp = datetime.now()
                self.logger.warning("No timestamp found, using current time")

            # Extract comments from the response
            latest_comments = []
            if 'latestComments' in item:
                self.logger.info(f"Found {len(item['latestComments'])} comments")
                for position, comment in enumerate(item['latestComments']):
                    latest_comments.append({
                        'id': comment.get('id', ''),
                        'text': comment.get('text', ''),
                        'timestamp': comment.get('timestamp', ''),
                        'ownerId': comment.get('owner', {}).get('id', ''),
                        'ownerUsername': comment.get('owner', {}).get('username', ''),
                        'ownerIsVerified': comment.get('owner', {}).get('is_verified', False),
                        'ownerProfilePicUrl': comment.get('owner', {}).get('profile_pic_url', ''),
                        'postId': item.get('id', ''),  # Add the post ID
                        'position': position  # Add the position
                    })
            else:
                self.logger.info("No comments found in item")

            # Log key fields before creating InstagramPost
            self.logger.info(f"Short code: {item.get('shortCode', 'No shortCode')}")
            self.logger.info(f"Caption length: {len(item.get('caption', ''))}")
            self.logger.info(f"Number of images: {len(item.get('images', []))}")

            # Adjust URL handling - check if we have a shortCode
            shortCode = item.get('shortCode')
            if not shortCode:
                shortCode = item.get('url', '').split('/')[-2] if item.get('url') else ''
                self.logger.info(f"Extracted shortCode from URL: {shortCode}")

            # Create the InstagramPost object with more flexible field handling
            post = InstagramPost(
                inputUrl=item.get('url', item.get('inputUrl', '')),  # Try both url and inputUrl
                url=f"https://www.instagram.com/p/{shortCode}/" if shortCode else item.get('url', ''),
                type=item.get('type', item.get('mediaType', 'Image')),  # Try both type and mediaType
                shortCode=shortCode,
                caption=item.get('caption', item.get('text', '')),  # Try both caption and text
                hashtags=item.get('hashtags', []),
                mentions=item.get('mentions', []),
                commentsCount=item.get('commentsCount', 0),
                firstComment=item.get('firstComment', ''),
                latestComments=latest_comments,
                dimensionsHeight=item.get('dimensionsHeight', item.get('height', 0)),  # Try both formats
                dimensionsWidth=item.get('dimensionsWidth', item.get('width', 0)),
                displayUrl=item.get('displayUrl', item.get('imageUrl', '')),  # Try both formats
                images=item.get('images', [item.get('displayUrl')] if item.get('displayUrl') else []),
                alt=item.get('alt', item.get('accessibility_caption', '')),  # Try both formats
                likesCount=item.get('likesCount', 0),
                timestamp=timestamp,
                childPosts=item.get('childPosts', []),
                ownerFullName=item.get('ownerFullName', item.get('fullName', '')),  # Try both formats
                ownerUsername=item.get('ownerUsername', item.get('username', '')),
                ownerId=item.get('ownerId', item.get('userId', '')),
                isSponsored=item.get('isSponsored', False)
            )
            
            # Validate the created post
            if not post.url or not post.shortCode:
                self.logger.warning(f"Created post missing critical fields - URL: {post.url}, shortCode: {post.shortCode}")
                return None
                
            self.logger.info(f"Successfully converted post with shortCode: {post.shortCode}")
            return post
            
        except Exception as e:
            self.logger.error(f"Error converting item to model: {str(e)}", exc_info=True)
            self.logger.error(f"Problematic item: {item}")
            return None 