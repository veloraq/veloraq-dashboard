import streamlit as st
from utils.investment_calculator import calculate_investment_analysis
import pandas as pd

def show():
    """Display investment analysis calculator page"""
    
    st.title("📊 Investment Analysis Calculator")
    st.markdown("Calculate detailed financial metrics for any investment property")
    
    # Input form
    st.markdown("### Property Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        purchase_price = st.number_input("Purchase Price ($)", min_value=0, value=300000, step=10000)
        down_payment_percent = st.slider("Down Payment (%)", 0, 100, 20, 5)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=7.0, step=0.25)
        loan_term = st.selectbox("Loan Term (years)", [15, 20, 30], index=2)
    
    with col2:
        monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, value=2000, step=100)
        property_tax_annual = st.number_input("Annual Property Tax ($)", min_value=0, value=4500, step=100)
        insurance_annual = st.number_input("Annual Insurance ($)", min_value=0, value=1200, step=100)
        hoa_monthly = st.number_input("Monthly HOA Fee ($)", min_value=0, value=0, step=50)
    
    st.markdown("### Operating Expense Assumptions")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        property_management = st.slider("Property Management (%)", 0, 20, 10, 1)
        maintenance = st.slider("Maintenance (%)", 0, 15, 8, 1)
    
    with col4:
        vacancy = st.slider("Vacancy Rate (%)", 0, 15, 5, 1)
        capex = st.slider("Capital Expenditures (%)", 0, 15, 5, 1)
    
    with col5:
        st.info("All percentages are calculated based on monthly rent")
    
    # Calculate button
    if st.button("Calculate Investment Metrics", type="primary"):
        st.session_state["run_analysis"] = True
    
    # Display results
    if st.session_state.get("run_analysis", False):
        analysis = calculate_investment_analysis(
            purchase_price=purchase_price,
            down_payment_percent=down_payment_percent,
            interest_rate=interest_rate,
            loan_term_years=loan_term,
            monthly_rent=monthly_rent,
            property_tax_annual=property_tax_annual,
            insurance_annual=insurance_annual,
            hoa_monthly=hoa_monthly,
            property_management_percent=property_management,
            maintenance_percent=maintenance,
            vacancy_percent=vacancy,
            capex_percent=capex
        )
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        # Key metrics
        st.markdown("### Key Investment Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cap Rate", f"{analysis['cap_rate']:.2f}%")
        
        with col2:
            st.metric("Cash-on-Cash Return", f"{analysis['cash_on_cash_return']:.2f}%")
        
        with col3:
            st.metric("Monthly Cash Flow", f"${analysis['cash_flow_monthly']:,.0f}")
        
        with col4:
            st.metric("Annual Cash Flow", f"${analysis['cash_flow_annual']:,.0f}")
        
        # Purchase breakdown
        st.markdown("### Purchase Breakdown")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Purchase Price", f"${analysis['purchase_price']:,.0f}")
        
        with col2:
            st.metric("Down Payment", f"${analysis['down_payment']:,.0f}")
        
        with col3:
            st.metric("Loan Amount", f"${analysis['loan_amount']:,.0f}")
        
        # Monthly breakdown
        st.markdown("### Monthly Income & Expenses")
        
        expense_data = {
            "Category": [
                "Rental Income",
                "Mortgage Payment",
                "Property Tax",
                "Insurance",
                "HOA Fee",
                "Property Management",
                "Maintenance",
                "Vacancy Reserve",
                "CapEx Reserve",
                "Total Operating Expenses",
                "NOI (Net Operating Income)",
                "Cash Flow"
            ],
            "Amount": [
                f"${analysis['monthly_rent']:,.2f}",
                f"-${analysis['monthly_mortgage']:,.2f}",
                f"-${analysis['property_tax_monthly']:,.2f}",
                f"-${analysis['insurance_monthly']:,.2f}",
                f"-${analysis['hoa_monthly']:,.2f}",
                f"-${analysis['property_management_monthly']:,.2f}",
                f"-${analysis['maintenance_monthly']:,.2f}",
                f"-${analysis['vacancy_monthly']:,.2f}",
                f"-${analysis['capex_monthly']:,.2f}",
                f"-${analysis['total_operating_expenses']:,.2f}",
                f"${analysis['noi_monthly']:,.2f}",
                f"${analysis['cash_flow_monthly']:,.2f}"
            ]
        }
        
        df_expenses = pd.DataFrame(expense_data)
        st.dataframe(df_expenses, use_container_width=True, hide_index=True)
        
        # Annual summary
        st.markdown("### Annual Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Annual Rent", f"${analysis['monthly_rent'] * 12:,.0f}")
        
        with col2:
            st.metric("Annual NOI", f"${analysis['noi_annual']:,.0f}")
        
        with col3:
            st.metric("Annual Cash Flow", f"${analysis['cash_flow_annual']:,.0f}")
        
        # Investment summary
        st.markdown("### Investment Summary")
        
        if analysis['cash_flow_monthly'] > 0:
            st.success(f"✅ This property generates positive cash flow of ${analysis['cash_flow_monthly']:,.0f} per month")
        else:
            st.warning(f"⚠️ This property has negative cash flow of ${abs(analysis['cash_flow_monthly']):,.0f} per month")
        
        if analysis['cap_rate'] >= 8:
            st.success(f"✅ Strong cap rate of {analysis['cap_rate']:.2f}% indicates good income potential")
        elif analysis['cap_rate'] >= 5:
            st.info(f"ℹ️ Moderate cap rate of {analysis['cap_rate']:.2f}%")
        else:
            st.warning(f"⚠️ Low cap rate of {analysis['cap_rate']:.2f}% - consider negotiating price or increasing rent")
        
        if analysis['cash_on_cash_return'] >= 10:
            st.success(f"✅ Excellent cash-on-cash return of {analysis['cash_on_cash_return']:.2f}%")
        elif analysis['cash_on_cash_return'] >= 6:
            st.info(f"ℹ️ Decent cash-on-cash return of {analysis['cash_on_cash_return']:.2f}%")
        else:
            st.warning(f"⚠️ Low cash-on-cash return of {analysis['cash_on_cash_return']:.2f}%")
