import streamlit as st
import pandas as pd
from data.properties import get_off_market_df
from utils.csv_export import export_to_csv
from utils.investment_calculator import calculate_investment_analysis
from config import COLUMBUS_ZIP_CODES

def show():
    """Display off-market listings page"""
    
    st.title("🏠 Off-Market Listings")
    st.markdown("Properties likely to hit the market soon based on various indicators")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Data Source")
    with col2:
        use_live_data = st.toggle("Live Data", value=False, help="Fetch from county auditor websites")
    
    # Load data
    if use_live_data:
        if 'api_manager' in st.session_state and st.session_state.api_manager:
            with st.spinner("Fetching off-market leads from county auditor websites..."):
                # Use a subset of zip codes to avoid long wait times
                selected_zips = st.multiselect(
                    "Select Zip Codes",
                    COLUMBUS_ZIP_CODES,
                    default=COLUMBUS_ZIP_CODES[:5],
                    help="Select zip codes to search (fewer = faster)"
                )
                
                if st.button("🔍 Fetch Off-Market Leads", type="primary"):
                    df_raw = st.session_state.api_manager.get_off_market_leads(selected_zips)
                    
                    if df_raw.empty:
                        st.warning("No off-market leads found. Try different zip codes or use Demo Data.")
                        df = get_off_market_df()
                    else:
                        st.success(f"Found {len(df_raw)} potential off-market leads!")
                        # Store in session state
                        st.session_state['off_market_live_data'] = df_raw
                        df = df_raw
                else:
                    # Use cached data if available
                    df = st.session_state.get('off_market_live_data', get_off_market_df())
        else:
            st.warning("⚠️ Please configure your API key in the sidebar to use live data.")
            df = get_off_market_df()
    else:
        df = get_off_market_df()
    
    st.sidebar.markdown("### Filters")
    
    # Check if we have demo data structure or live data structure
    has_property_type = 'property_type' in df.columns
    has_strategy = 'Strategy' in df.columns
    
    if has_property_type:
        # Demo data filters
        property_types = ["All"] + sorted(df["property_type"].unique().tolist())
        selected_type = st.sidebar.selectbox("Property Type", property_types)
        
        min_equity = st.sidebar.slider("Minimum Equity %", 0, 100, 0, 5)
        min_years_owned = st.sidebar.slider("Minimum Years Owned", 0, 30, 15, 1)
        
        show_probate = st.sidebar.checkbox("Probate/Inheritance", value=False)
        show_tax_delinquent = st.sidebar.checkbox("Tax Delinquent (2+ years)", value=False)
        show_foreclosure = st.sidebar.checkbox("Foreclosure", value=False)
        
        price_range = st.sidebar.slider(
            "Estimated Value Range",
            int(df["estimated_value"].min()),
            int(df["estimated_value"].max()),
            (int(df["estimated_value"].min()), int(df["estimated_value"].max())),
            step=10000
        )
        
        # Apply demo data filters
        filtered_df = df.copy()
        
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["property_type"] == selected_type]
        
        filtered_df = filtered_df[filtered_df["equity_percent"] >= min_equity]
        filtered_df = filtered_df[filtered_df["years_owned"] >= min_years_owned]
        filtered_df = filtered_df[
            (filtered_df["estimated_value"] >= price_range[0]) &
            (filtered_df["estimated_value"] <= price_range[1])
        ]
        
        if show_probate:
            filtered_df = filtered_df[filtered_df["probate"] == True]
        
        if show_tax_delinquent:
            filtered_df = filtered_df[filtered_df["tax_delinquent"] == True]
        
        if show_foreclosure:
            filtered_df = filtered_df[filtered_df["foreclosure"] == True]
    
    elif has_strategy:
        # Live data filters (simpler structure)
        if 'Source' in df.columns:
            sources = ["All"] + sorted(df["Source"].unique().tolist())
            selected_source = st.sidebar.selectbox("County Source", sources)
            
            if selected_source != "All":
                filtered_df = df[df["Source"] == selected_source]
            else:
                filtered_df = df.copy()
        else:
            filtered_df = df.copy()
    else:
        filtered_df = df.copy()
    
    # Display results
    st.markdown(f"### Found {len(filtered_df)} Properties")
    
    # Export button
    if len(filtered_df) > 0:
        csv_data = export_to_csv(filtered_df)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="off_market_properties.csv",
            mime="text/csv"
        )
    
    if has_property_type:
        # Demo data display (detailed)
        for idx, row in filtered_df.iterrows():
            with st.expander(f"{row['address']}, {row['city']}, OH {row['zip']} - ${row['estimated_value']:,.0f}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Property Type:** {row['property_type']}")
                    st.markdown(f"**Bedrooms:** {row['bedrooms']} | **Bathrooms:** {row['bathrooms']}")
                    st.markdown(f"**Square Feet:** {row['sqft']:,} | **Lot Size:** {row['lot_size']} acres")
                    st.markdown(f"**Year Built:** {row['year_built']}")
                    st.markdown(f"**Estimated Mortgage:** ${row['estimated_mortgage']:,.0f}")
                    st.markdown(f"**Equity:** {row['equity_percent']}% (${row['estimated_value'] - row['estimated_mortgage']:,.0f})")
                    st.markdown(f"**Years Owned:** {row['years_owned']}")
                    st.markdown(f"**Property Tax:** ${row['property_tax']:,.0f}/year")
                    
                    # Indicators
                    indicators = []
                    if row['probate']:
                        indicators.append('🔶 Probate/Inheritance')
                    if row['tax_delinquent']:
                        indicators.append(f'🔴 Tax Delinquent ({row["years_delinquent"]} years)')
                    if row['foreclosure']:
                        indicators.append('🔴 Foreclosure')
                    if row['equity_percent'] >= 50:
                        indicators.append('🟢 High Equity (50%+)')
                    
                    if indicators:
                        st.markdown(" | ".join(indicators))
                
                with col2:
                    st.markdown("### Quick Analysis")
                    if st.button(f"Analyze Investment", key=f"analyze_{row['id']}"):
                        st.session_state[f"analyze_{row['id']}"] = True
                    
                    if st.session_state.get(f"analyze_{row['id']}", False):
                        estimated_rent = row['estimated_value'] * 0.008
                        
                        analysis = calculate_investment_analysis(
                            purchase_price=row['estimated_value'],
                            down_payment_percent=20,
                            monthly_rent=estimated_rent,
                            property_tax_annual=row['property_tax']
                        )
                        
                        st.metric("Est. Monthly Rent", f"${analysis['monthly_rent']:,.0f}")
                        st.metric("Monthly Cash Flow", f"${analysis['cash_flow_monthly']:,.0f}")
                        st.metric("Cap Rate", f"{analysis['cap_rate']:.2f}%")
                        st.metric("Cash-on-Cash", f"{analysis['cash_on_cash_return']:.2f}%")
    
    elif has_strategy:
        # Live data display (simpler)
        for idx, row in filtered_df.iterrows():
            address = row.get('Address', 'N/A')
            owner = row.get('Owner', 'N/A')
            zip_code = row.get('Zip', 'N/A')
            source = row.get('Source', 'N/A')
            strategy = row.get('Strategy', 'N/A')
            
            with st.expander(f"{address} (Zip: {zip_code})"):
                st.markdown(f"**Owner:** {owner}")
                st.markdown(f"**Source:** {source}")
                st.markdown(f"**Strategy:** {strategy}")
                st.info("💡 This is a lead from county records. Research further to verify opportunity.")
