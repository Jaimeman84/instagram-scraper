import pytest
from unittest.mock import Mock, patch
from models import ScraperConfig, InstagramPost
from scraper_service import InstagramScraperService
from datetime import datetime

@pytest.fixture
def scraper():
    return InstagramScraperService()

@pytest.fixture
def mock_config():
    return ScraperConfig(
        addParentData=False,
        directUrls=["https://www.instagram.com/test_user/"],
        enhanceUserSearchWithFacebookPage=False,
        isUserReelFeedURL=False,
        isUserTaggedFeedURL=False,
        resultsLimit=1,
        resultsType="posts",
        searchLimit=1,
        searchType="profile"
    )

@pytest.fixture
def mock_instaloader_post():
    post = Mock()
    post.shortcode = "ABC123"
    post.caption = "Test caption"
    post.caption_hashtags = ["test"]
    post.caption_mentions = ["user"]
    post.comments = 10
    post.dimensions = (1080, 720)
    post.url = "https://example.com/image.jpg"
    post.accessibility_caption = "Test alt text"
    post.likes = 100
    post.date = datetime.now()
    post.owner_profile.full_name = "Test User"
    post.owner_username = "test_user"
    post.owner_id = "12345"
    post.is_sponsored = False
    post.typename = "GraphImage"
    return post

def test_login_success(scraper):
    """Test successful login."""
    with patch.object(scraper.loader, 'login') as mock_login:
        mock_login.return_value = True
        assert scraper.login("test_user", "test_pass") is True

def test_login_failure(scraper):
    """Test failed login."""
    with patch.object(scraper.loader, 'login') as mock_login:
        mock_login.side_effect = Exception("Login failed")
        assert scraper.login("test_user", "test_pass") is False

def test_convert_post_to_model(scraper, mock_instaloader_post):
    """Test conversion from instaloader Post to InstagramPost model."""
    input_url = "https://www.instagram.com/test_user/"
    result = scraper._convert_post_to_model(mock_instaloader_post, input_url)
    
    assert isinstance(result, InstagramPost)
    assert result.shortCode == mock_instaloader_post.shortcode
    assert result.caption == mock_instaloader_post.caption
    assert result.commentsCount == mock_instaloader_post.comments
    assert result.ownerUsername == mock_instaloader_post.owner_username

def test_scrape_posts_success(scraper, mock_config, mock_instaloader_post):
    """Test successful post scraping."""
    with patch('instaloader.Profile.from_username') as mock_profile:
        mock_profile.return_value.get_posts.return_value = [mock_instaloader_post]
        
        results = scraper.scrape_posts(mock_config)
        
        assert len(results) == 1
        assert isinstance(results[0], InstagramPost)
        assert results[0].shortCode == mock_instaloader_post.shortcode

def test_scrape_posts_empty_urls(scraper):
    """Test scraping with empty URL list."""
    config = ScraperConfig(
        addParentData=False,
        directUrls=[],
        enhanceUserSearchWithFacebookPage=False,
        isUserReelFeedURL=False,
        isUserTaggedFeedURL=False,
        resultsLimit=1,
        resultsType="posts",
        searchLimit=1,
        searchType="profile"
    )
    
    results = scraper.scrape_posts(config)
    assert len(results) == 0

def test_scrape_posts_error_handling(scraper, mock_config):
    """Test error handling during scraping."""
    with patch('instaloader.Profile.from_username') as mock_profile:
        mock_profile.side_effect = Exception("Network error")
        
        results = scraper.scrape_posts(mock_config)
        assert len(results) == 0 