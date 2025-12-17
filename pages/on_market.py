import streamlit as st
import pandas as pd
from data.properties import get_on_market_df
from utils.csv_export import export_to_csv
from utils.investment_calculator import calculate_investment_analysis
from utils.data_cache import save_properties_cache, load_properties_cache, format_timestamp
from config import COLUMBUS_ZIP_CODES
from datetime import datetime

st.title("📍 On-Market Listings")
st.markdown("Recently listed properties from the last 7 days")

use_google_sheets = st.session_state.get('use_google_sheets', False)
cached_df, cached_timestamp = load_properties_cache("on_market", prefer_google_sheets=use_google_sheets)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("### Data Source")
    if cached_timestamp:
        st.caption(f"Data last updated: {format_timestamp(cached_timestamp)}")
    
with col2:
    if st.session_state.get('apify_api_key'):
        use_live = st.toggle("Use Live Data", value=st.session_state.get('use_live_data', False))
        st.session_state.use_live_data = use_live
    else:
        st.warning("Configure API key in sidebar")
        use_live = False
        
with col3:
    if st.session_state.get('apify_api_key') and st.session_state.get('use_live_data', False):
        if st.button("🔄 Fetch Live Data"):
            st.session_state.fetch_live_data = True
        st.success("🔴 Live")
    else:
        if cached_df is not None:
            st.info("📂 Cached")
        else:
            st.info("📋 Demo")

if st.session_state.get('fetch_live_data', False) and st.session_state.get('apify_api_key'):
    with st.spinner("Fetching live data from Zillow/Redfin..."):
        try:
            from utils.api_manager import RealEstateAPI
            api = RealEstateAPI(apify_key=st.session_state.apify_api_key)
            
            selected_zips = st.session_state.get('selected_zips', [43201, 43203, 43206])
            st.info(f"Searching {len(selected_zips)} zip codes: {', '.join(map(str, selected_zips))}")
            
            # Fetch properties using the correct API method
            properties_df = api.get_active_listings(selected_zips, days_back=7)
            
            if not properties_df.empty:
                # Convert API DataFrame to our format
                all_properties = []
                for _, row in properties_df.iterrows():
                    all_properties.append({
                        'id': f"{row.get('Zip', '')}_{row.get('Address', '')[:10]}",
                        'address': row.get('Address', 'N/A'),
                        'city': row.get('City', 'Columbus'),
                        'zip': str(row.get('Zip', '')),
                        'property_type': 'Single Family',  # Default, could be enhanced
                        'list_price': float(row.get('Price', 0)),
                        'bedrooms': int(row.get('Beds', 0)) if row.get('Beds') else 0,
                        'bathrooms': float(row.get('Baths', 0)) if row.get('Baths') else 0,
                        'sqft': 0,  # Not provided by API
                        'lot_size': 0,  # Not provided by API
                        'year_built': 0,  # Not provided by API
                        'list_date': datetime.now().strftime('%Y-%m-%d'),
                        'days_on_market': 1,
                        'property_tax': 0,  # Will need to be estimated
                        'hoa_fee': 0,
                        'estimated_rent': 0,  # Will need to be estimated
                        'description': f"Property from {row.get('Source', 'N/A')}",
                        'source': row.get('Source', 'N/A'),
                        'url': row.get('URL', '')
                    })
                
                df = pd.DataFrame(all_properties)
                
                timestamp = save_properties_cache(df, "on_market", use_google_sheets=use_google_sheets)
                
                cache_type = "Google Sheets" if use_google_sheets else "local cache"
                st.success(f"Fetched {len(all_properties)} live properties from {properties_df['Source'].unique().tolist()} and saved to {cache_type}!")
                st.session_state.live_properties_df = df
            else:
                st.warning("No properties found. Using cached or demo data.")
                df = cached_df if cached_df is not None else get_on_market_df()
                
            st.session_state.fetch_live_data = False
            
            # Show credit usage
            credits = api.check_credits()
            st.sidebar.markdown(f"**Apify Credits:** ${credits['apify']['used']:.2f} / ${credits['apify']['limit']:.2f}")
            
        except Exception as e:
            st.error(f"Error fetching live data: {str(e)}")
            df = cached_df if cached_df is not None else get_on_market_df()
            st.session_state.fetch_live_data = False
else:
    if st.session_state.get('use_live_data', False) and 'live_properties_df' in st.session_state:
        df = st.session_state.live_properties_df
    elif cached_df is not None:
        df = cached_df
    else:
        df = get_on_market_df()

if 'selected_zips' not in st.session_state:
    st.session_state.selected_zips = [43201, 43203, 43206]

# Filters
st.sidebar.markdown("### Filters")

st.sidebar.markdown("#### Search Area")
selected_zips = st.sidebar.multiselect(
    "Select Zip Codes to Search",
    options=COLUMBUS_ZIP_CODES,
    default=st.session_state.selected_zips,
    help="Choose which Columbus zip codes to fetch properties from"
)

if not selected_zips:
    st.sidebar.warning("Please select at least one zip code")

if len(df) == 0:
    st.warning("No properties found. Please fetch data or check your cache.")
    st.stop()

property_types = ["All"] + sorted(df["property_type"].unique().tolist())
selected_type = st.sidebar.selectbox("Property Type", property_types)

min_price = int(df["list_price"].min()) if len(df) > 0 and df["list_price"].notna().any() else 0
max_price = int(df["list_price"].max()) if len(df) > 0 and df["list_price"].notna().any() else 1000000

price_range = st.sidebar.slider(
    "Price Range",
    min_price,
    max_price,
    (min_price, max_price),
    step=10000
)

if selected_type != "Land" and selected_type != "Commercial":
    max_bedrooms = int(df["bedrooms"].max()) if len(df) > 0 and df["bedrooms"].notna().any() else 5
    min_beds = st.sidebar.slider("Minimum Bedrooms", 0, max_bedrooms, 0)
else:
    min_beds = 0

max_dom = st.sidebar.slider("Max Days on Market", 1, 7, 7)

# Apply filters
filtered_df = df.copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["property_type"] == selected_type]

filtered_df = filtered_df[
    (filtered_df["list_price"] >= price_range[0]) &
    (filtered_df["list_price"] <= price_range[1])
]

filtered_df = filtered_df[filtered_df["bedrooms"] >= min_beds]
filtered_df = filtered_df[filtered_df["days_on_market"] <= max_dom]

st.markdown(f"### Found {len(filtered_df)} Properties")

if len(filtered_df) > 0:
    csv_data = export_to_csv(filtered_df)
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="on_market_properties.csv",
        mime="text/csv"
    )

# Display properties
for idx, row in filtered_df.iterrows():
    with st.expander(f"{row['address']}, {row['city']}, OH {row['zip']} - ${row['list_price']:,.0f}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Property Type:** {row['property_type']}")
            if row['bedrooms'] > 0:
                st.markdown(f"**Bedrooms:** {row['bedrooms']} | **Bathrooms:** {row['bathrooms']}")
            if row['sqft'] > 0:
                st.markdown(f"**Square Feet:** {row['sqft']:,}")
            if row['lot_size'] > 0:
                st.markdown(f"**Lot Size:** {row['lot_size']} acres")
            if row['year_built'] > 0:
                st.markdown(f"**Year Built:** {row['year_built']}")
            st.markdown(f"**List Date:** {row['list_date']}")
            st.markdown(f"**Days on Market:** {row['days_on_market']}")
            st.markdown(f"**Property Tax:** ${row['property_tax']:,.0f}/year")
            if row['hoa_fee'] > 0:
                st.markdown(f"**HOA Fee:** ${row['hoa_fee']:,.0f}/month")
            if row['estimated_rent'] > 0:
                st.markdown(f"**Estimated Rent:** ${row['estimated_rent']:,.0f}/month")
            
            st.markdown(f"**Description:** {row['description']}")
            
            st.markdown("**Status:** Active")
        
        with col2:
            st.markdown("### Investment Analysis")
            if st.button(f"Run Full Analysis", key=f"analyze_{row['id']}"):
                st.session_state[f"analyze_{row['id']}"] = True
            
            if st.session_state.get(f"analyze_{row['id']}", False):
                analysis = calculate_investment_analysis(
                    purchase_price=row['list_price'],
                    down_payment_percent=20,
                    monthly_rent=row['estimated_rent'],
                    property_tax_annual=row['property_tax'],
                    hoa_monthly=row['hoa_fee']
                )
                
                st.metric("Monthly Rent", f"${analysis['monthly_rent']:,.0f}")
                st.metric("Monthly Cash Flow", f"${analysis['cash_flow_monthly']:,.0f}")
                st.metric("Annual Cash Flow", f"${analysis['cash_flow_annual']:,.0f}")
                st.metric("Cap Rate", f"{analysis['cap_rate']:.2f}%")
                st.metric("Cash-on-Cash Return", f"{analysis['cash_on_cash_return']:.2f}%")

# Save selected zip codes to session state
st.session_state.selected_zips = selected_zips
