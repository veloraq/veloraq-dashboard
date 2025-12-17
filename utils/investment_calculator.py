def calculate_investment_analysis(
    purchase_price,
    down_payment_percent=20,
    interest_rate=7.0,
    loan_term_years=30,
    monthly_rent=0,
    property_tax_annual=0,
    insurance_annual=1200,
    hoa_monthly=0,
    property_management_percent=10,
    maintenance_percent=8,
    vacancy_percent=5,
    capex_percent=5
):
    """
    Calculate comprehensive investment analysis for a property
    
    Returns dict with all calculated metrics
    """
    # Purchase calculations
    down_payment = purchase_price * (down_payment_percent / 100)
    loan_amount = purchase_price - down_payment
    
    # Monthly mortgage payment calculation
    monthly_rate = (interest_rate / 100) / 12
    num_payments = loan_term_years * 12
    
    if monthly_rate > 0:
        monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                          ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_mortgage = loan_amount / num_payments
    
    # Operating expenses
    property_tax_monthly = property_tax_annual / 12
    insurance_monthly = insurance_annual / 12
    property_management_monthly = monthly_rent * (property_management_percent / 100)
    maintenance_monthly = monthly_rent * (maintenance_percent / 100)
    vacancy_monthly = monthly_rent * (vacancy_percent / 100)
    capex_monthly = monthly_rent * (capex_percent / 100)
    
    total_operating_expenses = (
        property_tax_monthly +
        insurance_monthly +
        hoa_monthly +
        property_management_monthly +
        maintenance_monthly +
        vacancy_monthly +
        capex_monthly
    )
    
    # NOI and cash flow
    noi_monthly = monthly_rent - total_operating_expenses
    cash_flow_monthly = noi_monthly - monthly_mortgage
    cash_flow_annual = cash_flow_monthly * 12
    
    # Return metrics
    noi_annual = noi_monthly * 12
    cap_rate = (noi_annual / purchase_price) * 100 if purchase_price > 0 else 0
    cash_on_cash_return = (cash_flow_annual / down_payment) * 100 if down_payment > 0 else 0
    
    # ROI calculation
    total_annual_return = cash_flow_annual
    roi = (total_annual_return / down_payment) * 100 if down_payment > 0 else 0
    
    return {
        "purchase_price": purchase_price,
        "down_payment": down_payment,
        "loan_amount": loan_amount,
        "monthly_mortgage": monthly_mortgage,
        "monthly_rent": monthly_rent,
        "property_tax_monthly": property_tax_monthly,
        "insurance_monthly": insurance_monthly,
        "hoa_monthly": hoa_monthly,
        "property_management_monthly": property_management_monthly,
        "maintenance_monthly": maintenance_monthly,
        "vacancy_monthly": vacancy_monthly,
        "capex_monthly": capex_monthly,
        "total_operating_expenses": total_operating_expenses,
        "noi_monthly": noi_monthly,
        "noi_annual": noi_annual,
        "cash_flow_monthly": cash_flow_monthly,
        "cash_flow_annual": cash_flow_annual,
        "cap_rate": cap_rate,
        "cash_on_cash_return": cash_on_cash_return,
        "roi": roi
    }
