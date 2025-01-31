# Instagram Scraper

A powerful Instagram scraping tool built with Python and Streamlit that allows you to scrape and download Instagram posts, profiles, places, hashtags, photos, and comments.

## Features

- Scrape Instagram posts, comments, and profiles
- Support for multiple Instagram URLs
- Modern, responsive UI with dark mode
- 1:1 aspect ratio image cards
- Interactive analytics dashboard
- Export data to JSON format
- User-friendly Streamlit interface
- Advanced search options
- Secure API token handling
- Rate limiting and error handling
- Robust image fetching with CDN fallbacks

## Prerequisites

- Python 3.8 or higher
- Apify account and API token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/instagram-scraper.git
cd instagram-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Apify API token:
```
APIFY_API_TOKEN=your_api_token_here
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Enter one or more Instagram URLs to scrape

4. Configure scraping options:
   - Results Limit: Maximum number of results to fetch (1-1000)
   - Search Type: Choose between user, hashtag, or place
   - Results Type: Choose between posts, comments, details, mentions, or stories
   - Search Limit: Number of search results to process (1-100)
   - Advanced Options: Additional configuration options

5. Click "Start Scraping" to begin

6. View the results:
   - Analytics Overview with engagement metrics
   - Interactive data tables for post engagement and hashtag analysis
   - Visual post cards with images, captions, and comments
   - Expandable sections for additional content

7. Download the results as JSON from the sidebar

## Project Structure

```
instagram-scraper/
├── app.py              # Streamlit application
├── models.py           # Pydantic data models
├── scraper_service.py  # Core scraping functionality
├── test_scraper.py    # Unit tests
├── requirements.txt    # Project dependencies
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## Features in Detail

### UI Components
- Dark mode interface
- Responsive layout with columns
- 1:1 aspect ratio image cards
- Expandable sections for captions and hashtags
- Interactive analytics dashboard
- Modern styling with consistent theme

### Data Display
- Post metadata (username, timestamp, engagement metrics)
- Full-size post images with proper aspect ratio
- Additional images in expandable sections
- Latest comments with user information
- Hashtag statistics and analysis

### Analytics
- Total posts, likes, and comments metrics
- Average engagement calculations
- Post engagement timeline
- Hashtag usage and performance analysis
- Interactive data tables with sorting and filtering

## Testing

Run the test suite:
```bash
pytest test_scraper.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Make sure to comply with Instagram's terms of service and API usage guidelines. The developers are not responsible for any misuse of this tool. 