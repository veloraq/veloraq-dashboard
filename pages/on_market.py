import streamlit as st
import pandas as pd
from data.properties import get_on_market_df
from utils.csv_export import export_to_csv
from utils.investment_calculator import calculate_investment_analysis
from config import COLUMBUS_ZIP_CODES

def show():
    """Display on-market listings page"""
    
    st.title("📍 On-Market Listings")
    st.markdown("Recently listed properties from the last 7 days")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Data Source")
    with col2:
        if st.session_state.get('apify_api_key'):
            use_live = st.toggle("Use Live Data", value=st.session_state.get('use_live_data', False))
            st.session_state.use_live_data = use_live
            if use_live:
                st.info("🔴 Live Data")
            else:
                st.info("📋 Demo Data")
        else:
            st.info("📋 Demo Data")
    
    # Load data
    df = get_on_market_df()
    
    if st.session_state.get('apify_api_key') and st.session_state.get('use_live_data', False):
        try:
            from utils.api_manager import RealEstateAPI
            api = RealEstateAPI(apify_key=st.session_state.apify_api_key)
            credits = api.check_credits()
            st.sidebar.markdown(f"**Apify Credits:** ${credits['apify']['used']:.2f} / ${credits['apify']['limit']:.2f}")
        except Exception as e:
            st.sidebar.warning(f"Could not check credits: {str(e)}")
    
    # Filters
    st.sidebar.markdown("### Filters")
    
    # Property type filter
    property_types = ["All"] + sorted(df["property_type"].unique().tolist())
    selected_type = st.sidebar.selectbox("Property Type", property_types)
    
    # Price range
    price_range = st.sidebar.slider(
        "Price Range",
        int(df["list_price"].min()),
        int(df["list_price"].max()),
        (int(df["list_price"].min()), int(df["list_price"].max())),
        step=10000
    )
    
    # Bedrooms filter
    if selected_type != "Land" and selected_type != "Commercial":
        min_beds = st.sidebar.slider("Minimum Bedrooms", 0, int(df["bedrooms"].max()), 0)
    else:
        min_beds = 0
    
    # Days on market
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
    
    # Sort options
    sort_by = st.selectbox("Sort By", ["Price (Low to High)", "Price (High to Low)", "Days on Market", "Newest Listings"])
    
    if sort_by == "Price (Low to High)":
        filtered_df = filtered_df.sort_values("list_price", ascending=True)
    elif sort_by == "Price (High to Low)":
        filtered_df = filtered_df.sort_values("list_price", ascending=False)
    elif sort_by == "Days on Market":
        filtered_df = filtered_df.sort_values("days_on_market", ascending=True)
    elif sort_by == "Newest Listings":
        filtered_df = filtered_df.sort_values("list_date", ascending=False)
    
    # Display results
    st.markdown(f"### Found {len(filtered_df)} Properties")
    
    # Export button
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
                
                # Status badge
                st.markdown('<span class="badge badge-success">Active</span>', unsafe_allow_html=True)
            
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
