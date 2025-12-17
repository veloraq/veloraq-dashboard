# Columbus Real Estate Investment Tool

A comprehensive Python-based real estate investment platform for Columbus, Ohio with **live API data integration from county auditor websites, Zillow, and Redfin**.

## Features

1. **Off-Market Listings**
   - **Live Data from Franklin & Delaware County Auditor Websites**
   - Properties likely to hit the market based on:
     - Probate/Inheritance
     - Tax delinquency (2+ years)
     - Foreclosure status
     - High equity (50%+ or 15+ years owned)
   - Direct integration with county GIS/parcel data APIs

2. **On-Market Listings**
   - **Live data from Zillow and Redfin via Apify**
   - Recently listed properties (last 7 days)
   - All property types: Single-family, Multi-family, Condos, Land, Commercial
   - CSV export functionality
   - Automatic property valuation estimates

3. **Investment Analysis Calculator**
   - Detailed ROI calculations with real property data
   - NOI (Net Operating Income)
   - Cash flow projections
   - Cap rate and Cash-on-Cash returns
   - Operating expense breakdowns:
     - Property management (8-10%)
     - Maintenance (1-2% of value)
     - Vacancy reserves (5-8%)
     - Capital expenditures (5-10%)
     - Property tax (from county data)
     - Insurance (estimated)
   - Assumes 20% down payment by default (configurable)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## API Configuration

### Apify API (For Live On-Market Data)

The platform integrates with Apify to fetch live property listings from Zillow and Redfin.

**Setup:**
1. Sign up for an account at [apify.com](https://apify.com)
2. Get your API key from the Apify dashboard
3. In the app sidebar, expand "⚙️ API Configuration"
4. Enter your Apify API key
5. On the On-Market Listings page, toggle "Live Data"

**How it works:**
- Searches Columbus zip codes for active listings
- Fetches data from Zillow first (maxcopell~zillow-zip-search actor)
- Falls back to Redfin if no Zillow results (benthepythondev~redfin-scraper actor)
- Filters properties listed or updated within the last 7 days
- Automatically estimates property tax and rent based on list price

**API Credits:**
- The app displays your current Apify credit usage
- Free tier: $5/month in credits
- Each zip code search uses approximately $0.10-0.30 in credits

### County Auditor APIs (For Off-Market Data)

The platform directly queries public county auditor websites for off-market leads.

**Data Sources:**
- **Franklin County**: GIS Parcel Features MapServer
  - URL: `https://gis.franklincountyohio.gov/hosting/rest/services/`
  - Data: Property addresses, owner names, sale dates, zip codes
- **Delaware County**: Auditor GIS Prior Year Parcels
  - URL: `https://maps.delco-gis.org/arcgiswebadaptor/rest/services/`
  - Data: Property addresses, owners, sale years

**How it works:**
- Queries county APIs by zip code
- Identifies properties with high equity (sold before 2015 or legacy properties)
- No API key required (public data)
- Results show potential off-market opportunities

### Optional: Parcl Labs API (Market Statistics)

**Setup:**
1. Sign up at [parcllabs.com](https://parcllabs.com)
2. Get your API key
3. Add to sidebar configuration
4. Access market statistics for Columbus zip codes

## Data Sources Summary

| Feature | Data Source | API Required | Real Data |
|---------|-------------|--------------|-----------|
| Off-Market Listings | Franklin & Delaware County Auditors | No | ✅ Yes |
| On-Market Listings | Zillow + Redfin (via Apify) | Yes | ✅ Yes |
| Market Statistics | Parcl Labs | Yes (Optional) | ✅ Yes |
| Property Analysis | Calculated from inputs | No | ✅ Yes |

## Project Structure

```
.
├── app.py                          # Main application entry point with API setup
├── config.py                       # Configuration and Columbus zip codes
├── data/
│   └── properties.py               # Property data (demo + API integration)
├── pages/
│   ├── home.py                     # Home page with API status
│   ├── off_market.py               # Off-market listings (county data)
│   ├── on_market.py                # On-market listings (Zillow/Redfin)
│   └── analysis.py                 # Investment calculator page
├── utils/
│   ├── api_manager.py              # Complete API integration
│   ├── investment_calculator.py    # ROI calculation logic
│   └── csv_export.py               # CSV export functionality
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Usage

### 1. Browse Off-Market Listings (Real Data)
- Toggle "Live Data" to fetch from county auditor websites
- Select Columbus zip codes to search
- Filter by county source and strategy
- Identifies high-equity properties likely to sell soon
- Export results to CSV

### 2. View On-Market Listings (Real Data)
- Configure Apify API key in sidebar
- Toggle "Live Data" to fetch from Zillow/Redfin
- Search recent listings with advanced filters
- Export filtered results to CSV
- Run instant investment analysis on any property

### 3. Analyze Investments
Input any property details to calculate comprehensive financial metrics including:
- Monthly/Annual cash flow
- Net Operating Income (NOI)
- Cap Rate
- Cash-on-Cash Return
- Detailed expense breakdown with industry-standard percentages

## Columbus Market Coverage

The platform covers all Columbus, OH zip codes including Franklin and Delaware counties:
- **Franklin County**: 43201-43240, 43004, 43016, 43017, 43026, 43054, 43081, 43082, 43085
- **Delaware County**: 43015, 43021, 43035, 43065, 43240
- Full list in `config.py`: 47 zip codes total

## Real Data Examples

### Off-Market Data Fields (County Auditor)
```python
{
    "Address": "123 Main St",
    "Owner": "John Smith",
    "Zip": "43201",
    "Source": "Franklin Co",
    "Strategy": "High Equity (2010)"  # Year last sold
}
```

### On-Market Data Fields (Zillow/Redfin)
```python
{
    "Address": "456 Oak Ave",
    "City": "Columbus",
    "Price": 250000,
    "Source": "Zillow",
    "Zip": "43214",
    "URL": "https://zillow.com/..."
}
```

## Customization

### Adjust Zip Codes
Edit `COLUMBUS_ZIP_CODES` in `config.py` to add/remove zip codes

### Change Investment Assumptions
Edit `utils/investment_calculator.py` to modify:
- Down payment percentage (default: 20%)
- Interest rate (default: 7.5%)
- Operating expense ratios
- Property management fees (default: 8%)
- Maintenance reserves (default: 1%)

### Add More Counties
Update `utils/api_manager.py` `get_off_market_leads()` method with new county auditor APIs

## Notes

- **Off-Market Data**: Real data from county auditor websites (no API key required)
- **On-Market Data**: Real data from Zillow/Redfin (Apify API key required)
- Free Apify tier has $5/month credit limit
- County auditor queries are free public data
- All financial calculations are estimates for educational purposes
- Operating expense percentages based on industry standards

## Troubleshooting

**No off-market properties showing:**
- Select more zip codes
- Try different counties (Franklin vs Delaware)
- County APIs may be temporarily unavailable

**No on-market properties in live mode:**
- Check Apify API key is valid
- Verify credit balance in sidebar
- Try fewer zip codes to reduce API costs
- Check Apify account status at apify.com

**API calls timing out:**
- Increase timeout values in `api_manager.py`
- Reduce number of zip codes searched simultaneously
- Check internet connection
- County APIs may have rate limits

## Credits & Attribution

- **County Data**: Franklin County GIS, Delaware County GIS
- **Listing Data**: Zillow, Redfin (via Apify)
- **Market Data**: Parcl Labs (optional)

## License

This is a demonstration project for educational purposes. Property data is sourced from public records and third-party APIs. Users are responsible for compliance with API terms of service and data usage policies.
