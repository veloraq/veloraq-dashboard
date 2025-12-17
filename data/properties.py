from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from utils.api_manager import RealEstateAPI
from config import COLUMBUS_ZIP_CODES, DEFAULT_DAYS_BACK

# Off-market properties data
OFF_MARKET_PROPERTIES = [
    {
        "id": "OM001",
        "address": "1234 Main St",
        "city": "Columbus",
        "zip": "43215",
        "property_type": "Single Family",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1800,
        "lot_size": 0.25,
        "year_built": 1985,
        "estimated_value": 285000,
        "estimated_mortgage": 45000,
        "equity_percent": 84,
        "years_owned": 18,
        "tax_delinquent": False,
        "years_delinquent": 0,
        "probate": True,
        "foreclosure": False,
        "property_tax": 4200,
        "last_sale_date": "2006-03-15",
        "last_sale_price": 165000,
        "owner_occupied": False
    },
    {
        "id": "OM002",
        "address": "5678 Oak Avenue",
        "city": "Columbus",
        "zip": "43201",
        "property_type": "Single Family",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2400,
        "lot_size": 0.35,
        "year_built": 1978,
        "estimated_value": 320000,
        "estimated_mortgage": 180000,
        "equity_percent": 44,
        "years_owned": 22,
        "tax_delinquent": True,
        "years_delinquent": 3,
        "probate": False,
        "foreclosure": True,
        "property_tax": 5100,
        "last_sale_date": "2002-07-20",
        "last_sale_price": 142000,
        "owner_occupied": False
    },
    {
        "id": "OM003",
        "address": "910 Elm Street",
        "city": "Columbus",
        "zip": "43206",
        "property_type": "Multi-Family",
        "bedrooms": 6,
        "bathrooms": 4,
        "sqft": 3200,
        "lot_size": 0.28,
        "year_built": 1995,
        "estimated_value": 425000,
        "estimated_mortgage": 125000,
        "equity_percent": 71,
        "years_owned": 16,
        "tax_delinquent": False,
        "years_delinquent": 0,
        "probate": True,
        "foreclosure": False,
        "property_tax": 6800,
        "last_sale_date": "2008-11-10",
        "last_sale_price": 285000,
        "owner_occupied": False
    },
    {
        "id": "OM004",
        "address": "2468 Maple Drive",
        "city": "Columbus",
        "zip": "43220",
        "property_type": "Single Family",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1650,
        "lot_size": 0.22,
        "year_built": 2000,
        "estimated_value": 265000,
        "estimated_mortgage": 195000,
        "equity_percent": 26,
        "years_owned": 8,
        "tax_delinquent": True,
        "years_delinquent": 2,
        "probate": False,
        "foreclosure": False,
        "property_tax": 3900,
        "last_sale_date": "2016-05-22",
        "last_sale_price": 235000,
        "owner_occupied": True
    },
    {
        "id": "OM005",
        "address": "1357 Pine Boulevard",
        "city": "Columbus",
        "zip": "43214",
        "property_type": "Single Family",
        "bedrooms": 5,
        "bathrooms": 3,
        "sqft": 2800,
        "lot_size": 0.45,
        "year_built": 1992,
        "estimated_value": 385000,
        "estimated_mortgage": 55000,
        "equity_percent": 86,
        "years_owned": 20,
        "tax_delinquent": False,
        "years_delinquent": 0,
        "probate": True,
        "foreclosure": False,
        "property_tax": 5800,
        "last_sale_date": "2004-09-14",
        "last_sale_price": 198000,
        "owner_occupied": False
    }
]

# On-market properties data
ON_MARKET_PROPERTIES = [
    {
        "id": "MLS001",
        "address": "789 Cherry Lane",
        "city": "Columbus",
        "zip": "43212",
        "property_type": "Single Family",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2200,
        "lot_size": 0.3,
        "year_built": 2010,
        "list_price": 425000,
        "list_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "days_on_market": 2,
        "status": "Active",
        "property_tax": 6200,
        "hoa_fee": 0,
        "estimated_rent": 2400,
        "description": "Beautiful modern home with updated kitchen and finished basement"
    },
    {
        "id": "MLS002",
        "address": "321 Birch Court",
        "city": "Columbus",
        "zip": "43235",
        "property_type": "Condo",
        "bedrooms": 2,
        "bathrooms": 2,
        "sqft": 1200,
        "lot_size": 0,
        "year_built": 2018,
        "list_price": 215000,
        "list_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "days_on_market": 5,
        "status": "Active",
        "property_tax": 2800,
        "hoa_fee": 250,
        "estimated_rent": 1500,
        "description": "Luxury condo in prime location with parking and amenities"
    },
    {
        "id": "MLS003",
        "address": "456 Walnut Street",
        "city": "Columbus",
        "zip": "43202",
        "property_type": "Multi-Family",
        "bedrooms": 8,
        "bathrooms": 6,
        "sqft": 4200,
        "lot_size": 0.4,
        "year_built": 2005,
        "list_price": 650000,
        "list_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "days_on_market": 1,
        "status": "Active",
        "property_tax": 9500,
        "hoa_fee": 0,
        "estimated_rent": 4800,
        "description": "Excellent investment property, 4 units fully rented"
    },
    {
        "id": "MLS004",
        "address": "2.5 Acres on Route 23",
        "city": "Columbus",
        "zip": "43230",
        "property_type": "Land",
        "bedrooms": 0,
        "bathrooms": 0,
        "sqft": 0,
        "lot_size": 2.5,
        "year_built": 0,
        "list_price": 180000,
        "list_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "days_on_market": 7,
        "status": "Active",
        "property_tax": 1200,
        "hoa_fee": 0,
        "estimated_rent": 0,
        "description": "Prime commercial land with highway frontage"
    },
    {
        "id": "MLS005",
        "address": "890 Business Park Drive",
        "city": "Columbus",
        "zip": "43240",
        "property_type": "Commercial",
        "bedrooms": 0,
        "bathrooms": 4,
        "sqft": 8500,
        "lot_size": 1.2,
        "year_built": 2015,
        "list_price": 1250000,
        "list_date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
        "days_on_market": 4,
        "status": "Active",
        "property_tax": 18500,
        "hoa_fee": 0,
        "estimated_rent": 12000,
        "description": "Modern office building with ample parking"
    },
    {
        "id": "MLS006",
        "address": "147 Garden Way",
        "city": "Columbus",
        "zip": "43219",
        "property_type": "Single Family",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1850,
        "lot_size": 0.27,
        "year_built": 2008,
        "list_price": 315000,
        "list_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "days_on_market": 3,
        "status": "Active",
        "property_tax": 4500,
        "hoa_fee": 0,
        "estimated_rent": 2000,
        "description": "Move-in ready with open floor plan and large backyard"
    }
]

def get_off_market_df():
    """Return off-market properties as pandas DataFrame"""
    return pd.DataFrame(OFF_MARKET_PROPERTIES)

def get_on_market_df():
    """Return on-market properties as pandas DataFrame"""
    
    # Check if API key is configured
    if st.session_state.get('apify_api_key') and st.session_state.get('use_live_data', False):
        try:
            api = RealEstateAPI(apify_key=st.session_state.apify_api_key)
            
            # Fetch live data from APIs
            with st.spinner("Fetching live listings from Zillow/Redfin..."):
                df = api.get_active_listings(
                    zips=COLUMBUS_ZIP_CODES[:10],  # Start with first 10 zip codes
                    days_back=DEFAULT_DAYS_BACK
                )
            
            if not df.empty:
                # Transform API data to match our schema
                df['id'] = 'API_' + df.index.astype(str)
                df['property_type'] = 'Single Family'  # Default, could be enhanced
                df['bedrooms'] = 0  # APIs may not provide this
                df['bathrooms'] = 0
                df['sqft'] = 0
                df['lot_size'] = 0
                df['year_built'] = 0
                df['list_price'] = df['Price']
                df['list_date'] = datetime.now().strftime("%Y-%m-%d")
                df['days_on_market'] = 1
                df['status'] = 'Active'
                df['property_tax'] = df['list_price'] * 0.015  # Estimate 1.5% of value
                df['hoa_fee'] = 0
                df['estimated_rent'] = df['list_price'] * 0.008  # 0.8% rule
                df['description'] = 'Live listing from ' + df['Source']
                df['address'] = df['Address']
                df['city'] = df['City']
                df['zip'] = df['Zip']
                
                st.success(f"✓ Loaded {len(df)} live listings from API")
                return df[['id', 'address', 'city', 'zip', 'property_type', 'bedrooms', 
                          'bathrooms', 'sqft', 'lot_size', 'year_built', 'list_price', 
                          'list_date', 'days_on_market', 'status', 'property_tax', 
                          'hoa_fee', 'estimated_rent', 'description']]
        except Exception as e:
            st.warning(f"API fetch failed: {str(e)}. Using demo data.")
    
    # Return demo data if no API key or fetch failed
    return pd.DataFrame(ON_MARKET_PROPERTIES)
