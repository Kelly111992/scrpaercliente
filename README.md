# Startup Instructions for G-Maps Lead Extractor

## Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

## Backend Setup (PowerShell)
1. Open a terminal in `backend/`
2. Create environment: `python -m venv venv`
3. Activate: `.\venv\Scripts\activate`
4. Install: `pip install -r requirements.txt`
5. Install browsers: `playwright install chromium`
6. Run: `python main.py`

## Frontend Setup
1. Open a terminal in `frontend/`
2. Install: `npm install`
3. Run: `npm run dev` (for development) or `npm run build && npm start` (for production)

## Usage
1. Open `http://localhost:3000`
2. Go to Google Maps and search for something (e.g., "Restaurants in Miami")
3. Copy the URL from the browser address bar
4. Paste it into the tool and click **Start Scraping**
5. Download results as CSV or JSON when finished
