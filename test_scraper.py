import pytest
from unittest.mock import Mock, patch, MagicMock
from models import ScraperConfig, InstagramPost
from scraper_service import InstagramScraperService
from datetime import datetime

@pytest.fixture
def mock_apify_client():
    """Mock Apify client with required functionality."""
    mock_client = MagicMock()
    
    # Mock the actor call
    mock_run = MagicMock()
    mock_run.get.return_value = {
        'id': 'test_run_id',
        'status': 'SUCCEEDED',
        'defaultDatasetId': 'test_dataset_id'
    }
    mock_client.actor.return_value.call.return_value = mock_run
    
    # Create test data
    test_data = [{
        'url': 'https://www.instagram.com/p/test123/',
        'shortCode': 'test123',
        'caption': 'Test caption',
        'hashtags': ['test'],
        'mentions': ['user'],
        'commentsCount': 10,
        'dimensionsHeight': 1080,
        'dimensionsWidth': 720,
        'displayUrl': 'https://example.com/image.jpg',
        'alt': 'Test alt text',
        'likesCount': 100,
        'timestamp': datetime.now().isoformat(),
        'ownerFullName': 'Test User',
        'ownerUsername': 'test_user',
        'ownerId': '12345',
        'isSponsored': False,
        'type': 'Image'
    }]
    
    # Mock the dataset
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter(test_data)  # Convert list to iterator
    mock_client.dataset.return_value = mock_dataset
    
    return mock_client

@pytest.fixture
def mock_error_apify_client():
    """Mock Apify client that simulates an error scenario."""
    mock_client = MagicMock()
    
    # Mock the actor call to fail
    mock_run = MagicMock()
    mock_run.get.return_value = {
        'id': 'test_run_id',
        'status': 'FAILED',
        'errorMessage': 'API error occurred'
    }
    mock_client.actor.return_value.call.return_value = mock_run
    
    return mock_client

@pytest.fixture
def scraper(mock_apify_client):
    """Create scraper instance with mocked Apify client."""
    with patch('scraper_service.ApifyClient', return_value=mock_apify_client):
        with patch.dict('os.environ', {'APIFY_API_TOKEN': 'test_token'}):
            return InstagramScraperService()

@pytest.fixture
def error_scraper(mock_error_apify_client):
    """Create scraper instance with error-producing mock client."""
    with patch('scraper_service.ApifyClient', return_value=mock_error_apify_client):
        with patch.dict('os.environ', {'APIFY_API_TOKEN': 'test_token'}):
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
        searchType="user"
    )

def test_scraper_initialization():
    """Test scraper initialization with API token."""
    with patch.dict('os.environ', {'APIFY_API_TOKEN': 'test_token'}):
        scraper = InstagramScraperService()
        assert scraper.api_token == 'test_token'

def test_scraper_initialization_no_token():
    """Test scraper initialization without API token."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="Apify API token is required"):
            InstagramScraperService()

def test_convert_apify_to_model(scraper, mock_apify_client):
    """Test conversion from Apify output to InstagramPost model."""
    # Get the first item from the iterator
    item = next(mock_apify_client.dataset().iterate_items())
    result = scraper._convert_apify_to_model(item)
    
    assert isinstance(result, InstagramPost)
    assert result.shortCode == item['shortCode']
    assert result.caption == item['caption']
    assert result.commentsCount == item['commentsCount']
    assert result.ownerUsername == item['ownerUsername']

def test_scrape_posts_success(scraper, mock_config, mock_apify_client):
    """Test successful post scraping."""
    results = scraper.scrape_posts(mock_config)
    
    assert len(results) == 1
    assert isinstance(results[0], InstagramPost)
    assert results[0].shortCode == 'test123'

def test_scrape_posts_empty_urls(scraper):
    """Test scraping with empty URL list."""
    config = ScraperConfig(
        addParentData=False,
        directUrls=[],  # Empty URLs list
        enhanceUserSearchWithFacebookPage=False,
        isUserReelFeedURL=False,
        isUserTaggedFeedURL=False,
        resultsLimit=1,
        resultsType="posts",
        searchLimit=1,
        searchType="user"
    )
    
    # Create a new mock client for this specific test
    mock_client = MagicMock()
    
    # Mock the actor call
    mock_run = MagicMock()
    mock_run.get.return_value = {
        'id': 'test_run_id',
        'status': 'SUCCEEDED',
        'defaultDatasetId': 'test_dataset_id'
    }
    mock_client.actor.return_value.call.return_value = mock_run
    
    # Mock the dataset with empty results
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter([])  # Return empty iterator
    mock_client.dataset.return_value = mock_dataset
    
    # Mock the run status check
    mock_run_info = MagicMock()
    mock_run_info.get.return_value = {'status': 'SUCCEEDED'}
    mock_client.run.return_value = mock_run_info
    
    # Replace the client for this test
    with patch('scraper_service.ApifyClient', return_value=mock_client):
        with patch.dict('os.environ', {'APIFY_API_TOKEN': 'test_token'}):
            scraper = InstagramScraperService()
            results = scraper.scrape_posts(config)
            assert len(results) == 0