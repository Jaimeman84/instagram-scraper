# Instagram Scraper

A powerful Instagram scraping tool built with Python and Streamlit that allows you to scrape and download Instagram posts, profiles, places, hashtags, photos, and comments.

## Features

- Scrape Instagram posts, comments, and profiles
- Support for multiple Instagram URLs
- Export data to JSON format
- User-friendly Streamlit interface
- Advanced search options
- Secure login handling
- Rate limiting and error handling

## Prerequisites

- Python 3.8 or higher
- Instagram account for authentication

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

4. Create a `.env` file in the root directory with your Instagram credentials (optional):
```
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Log in with your Instagram credentials

4. Enter one or more Instagram URLs to scrape

5. Configure scraping options:
   - Results Limit: Maximum number of results to fetch
   - Search Type: Choose between hashtag, profile, or location
   - Results Type: Choose between posts, comments, or profile
   - Advanced Options: Additional configuration options

6. Click "Start Scraping" to begin

7. Download the results as JSON

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