import streamlit as st
from data.properties import get_off_market_df, get_on_market_df

def show():
    """Display home page"""
    
    # Hero section
    st.markdown('<div class="main-header">Find Your Next Investment Property in Columbus</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Access off-market opportunities, analyze on-market listings, and calculate ROI with institutional-grade tools</div>', 
                unsafe_allow_html=True)
    
    # API Status indicator
    if st.session_state.get('apify_key'):
        st.success("✅ Live API Integration Active - Fetch real-time data from Zillow & Redfin")
    else:
        st.info("📋 Demo Mode - Configure API keys in sidebar to access live data")
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🏠 Off-Market Listings</h3>
            <p>Properties likely to hit the market soon based on probate, tax delinquency, foreclosure status, and high equity positions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📍 On-Market Listings</h3>
            <p>Recently listed and updated properties from the last 7 days. Single-family, multi-family, condos, land, and commercial</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Investment Analysis</h3>
            <p>Calculate NOI, cash flow, cap rate, and cash-on-cash returns with detailed operating expense breakdowns</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Stats section
    st.markdown("### Platform Statistics")
    
    off_market_count = len(get_off_market_df())
    on_market_count = len(get_on_market_df())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Off-Market Opportunities", off_market_count)
    
    with col2:
        st.metric("Active Listings", on_market_count)
    
    with col3:
        st.metric("Primary Market", "Columbus")
    
    with col4:
        st.metric("Default Down Payment", "20%")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Quick start
    st.markdown("### Quick Start")
    
    if st.session_state.get('apify_key'):
        st.success("""
        ✅ **API Connected**
        - Go to On-Market Listings and toggle "Use Live Data" to fetch real properties
        - Browse Off-Market opportunities for distressed properties
        - Use Investment Analysis to calculate ROI on any property
        """)
    else:
        st.info("""
        👈 **Getting Started:**
        1. Explore demo data using the sidebar navigation
        2. Configure API keys in the sidebar to access live listings
        3. Run investment analysis on any property to see detailed financial projections
        """)
    
    with st.expander("📖 How to Get Live Data"):
        st.markdown("""
        ### Setting Up Apify API
        
        1. **Create Account**: Sign up at [apify.com](https://apify.com)
        2. **Get API Key**: Find your API key in the Apify dashboard
        3. **Add to App**: Enter the key in the sidebar "⚙️ API Configuration" section
        4. **Use Live Data**: Go to On-Market Listings and toggle "Use Live Data"
        
        ### What You'll Get
        - Real properties from Zillow and Redfin
        - Updated listings from Columbus zip codes
        - Properties listed or updated within the last 7 days
        - Automatic property valuation and rent estimates
        
        ### Credit Usage
        - Free tier: $5/month
        - Each zip code search: ~$0.10-$0.30
        - Platform starts with first 10 Columbus zip codes
        """)
