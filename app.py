import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Simulation Functions
# ---------------------------------------------------------------------
def simulate_buy_scenario(initial_savings, monthly_income, monthly_expenses,
                          annual_income_growth, annual_inflation_rate, annual_invest_return,
                          property_price, mortgage_term_years, mortgage_interest_rate, deposit_fraction,
                          owner_cost_initial, annual_owner_cost_inflation, annual_house_price_growth,
                          max_months=360):
    """
    Scenario 1: Buy a property now using a mortgage.
    
    Parameters:
    - initial_savings: Initial available savings (£)
    - monthly_income: Monthly household income (£)
    - monthly_expenses: Monthly non-housing expenses (£)
    - annual_income_growth: Annual income growth rate (in decimal, e.g., 0.03 for 3%)
    - annual_inflation_rate: Annual inflation rate for non-housing expenses (in decimal, e.g., 0.02 for 2%)
    - annual_invest_return: Annual investment return rate (in decimal, e.g., 0.05 for 5%)
    
    Mortgage-specific parameters:
    - property_price: The current property price (£)
    - mortgage_term_years: Mortgage term in years (reference)
    - mortgage_interest_rate: Annual interest rate on the mortgage (in decimal, e.g., 0.04 for 4%)
    - deposit_fraction: Fraction of the property price paid upfront (in decimal, e.g., 0.2 for 20%)
    
    Owner Occupier Housing Costs:
    - owner_cost_initial: Initial monthly cost for owner occupier housing (£)
    - annual_owner_cost_inflation: Annual inflation rate for these housing costs (in decimal, e.g., 0.02 for 2%)
    
    House Price Growth:
    - annual_house_price_growth: Annual house price growth rate (in decimal)
    
    Simulation Mechanics:
    1. At time zero, you pay the deposit and finance the remaining amount with a mortgage.
    2. Every month, the following occurs:
       - Monthly income and non-housing expenses grow according to their respective rates.
       - The current property price is updated using the house price growth rate.
       - You pay the monthly interest on the outstanding mortgage.
       - You also pay the owner occupier housing cost (which inflates monthly at its own rate).
       - Disposable income is computed as:
             monthly_income - monthly_expenses - interest_payment - current_owner_cost.
         If positive, it is added to your investment portfolio (which grows at the monthly investment rate).
    3. The simulation continuously records monthly history.
       The homeownership condition is considered achieved when the investment portfolio >= outstanding mortgage.
    
    Returns:
    - stop_month: The first month when the condition is met (or None if never met)
    - final_investment_portfolio: Investment portfolio at the final month.
    - history: A dictionary containing monthly history with keys:
         "months", "house_price", "investment_portfolio", "net_wealth"
       where net_wealth = (current_house_price - outstanding_mortgage) + investment_portfolio.
    """
    # Monthly multipliers
    mi_growth = (1 + annual_income_growth) ** (1 / 12)
    me_growth = (1 + annual_inflation_rate) ** (1 / 12)
    mi_return = (1 + annual_invest_return) ** (1 / 12)
    m_interest = mortgage_interest_rate / 12
    moc_growth = (1 + annual_owner_cost_inflation) ** (1 / 12)
    mhp_growth = (1 + annual_house_price_growth) ** (1 / 12)
    
    # Initial conditions
    deposit_amount = deposit_fraction * property_price
    if initial_savings < deposit_amount:
        st.error("For the buying scenario, initial savings are less than the required deposit.")
        return None, None, None

    investment_portfolio = initial_savings - deposit_amount
    outstanding_mortgage = property_price * (1 - deposit_fraction)
    
    current_income = monthly_income
    current_expenses = monthly_expenses
    current_owner_cost = owner_cost_initial
    current_house_price = property_price
    
    history = {"months": [], "house_price": [], "investment_portfolio": [], "net_wealth": []}
    stop_month = None
    
    for month in range(max_months):
        # Record state
        net_wealth = (current_house_price - outstanding_mortgage) + investment_portfolio
        history["months"].append(month)
        history["house_price"].append(current_house_price)
        history["investment_portfolio"].append(investment_portfolio)
        history["net_wealth"].append(net_wealth)
        
        # Set the stop month if condition met for the first time
        if stop_month is None and investment_portfolio >= outstanding_mortgage:
            stop_month = month
        
        # Compute monthly mortgage interest payment
        interest_payment = outstanding_mortgage * m_interest
        
        # Compute disposable income
        monthly_disposable = current_income - current_expenses - interest_payment - current_owner_cost
        if monthly_disposable < 0:
            monthly_disposable = 0
        
        # Update investment portfolio: grow then add disposable income
        investment_portfolio = investment_portfolio * mi_return + monthly_disposable
        
        # Update variables for next month
        current_income *= mi_growth
        current_expenses *= me_growth
        current_owner_cost *= moc_growth
        current_house_price *= mhp_growth
    
    return stop_month, investment_portfolio, history

def simulate_rent_scenario(initial_savings, monthly_income, monthly_expenses,
                           annual_income_growth, annual_inflation_rate, annual_invest_return,
                           property_price, monthly_rent, annual_rent_inflation_rate, annual_house_price_growth,
                           max_months=360):
    """
    Scenario 2: Rent now and purchase for cash later.
    
    Parameters:
    - initial_savings: Initial available savings (£)
    - monthly_income: Monthly household income (£)
    - monthly_expenses: Monthly non-housing expenses (£)
    - annual_income_growth: Annual income growth rate (in decimal, e.g., 0.03 for 3%)
    - annual_inflation_rate: Annual inflation rate for non-housing expenses (in decimal, e.g., 0.02 for 2%)
    - annual_invest_return: Annual investment return rate (in decimal, e.g., 0.05 for 5%)
    
    Rent and property parameters:
    - property_price: The current property price (£)
    - monthly_rent: Current monthly rent (£)
    - annual_rent_inflation_rate: Annual rent inflation rate (in decimal, e.g., 0.03 for 3%)
    - annual_house_price_growth: Annual house price growth rate (in decimal, e.g., 0.02 for 2%)
    
    Simulation Mechanics:
    1. Your savings are fully invested while you rent.
    2. Every month, record the state as:
         - Update monthly income, expenses, and rent.
         - Update the current property price using the house price growth rate.
         - Disposable income = monthly_income - monthly_expenses - current_rent.
         - Investment portfolio grows and disposable income is added.
    3. The homeownership condition is achieved when the investment portfolio >= current property price,
       and this is recorded as the stop month.
    
    Returns:
    - stop_month: The first month when the condition is met (or None if never met)
    - final_investment_portfolio: Investment portfolio at the final month.
    - history: A dictionary with keys: "months", "house_price", "investment_portfolio"
    """
    # Monthly multipliers
    mi_growth = (1 + annual_income_growth) ** (1 / 12)
    me_growth = (1 + annual_inflation_rate) ** (1 / 12)
    mi_return = (1 + annual_invest_return) ** (1 / 12)
    mr_growth = (1 + annual_rent_inflation_rate) ** (1 / 12)
    mhp_growth = (1 + annual_house_price_growth) ** (1 / 12)
    
    investment_portfolio = initial_savings
    current_income = monthly_income
    current_expenses = monthly_expenses
    current_rent = monthly_rent
    current_house_price = property_price
    
    history = {"months": [], "house_price": [], "investment_portfolio": []}
    stop_month = None
    
    for month in range(max_months):
        history["months"].append(month)
        history["house_price"].append(current_house_price)
        history["investment_portfolio"].append(investment_portfolio)
        
        if stop_month is None and investment_portfolio >= current_house_price:
            stop_month = month
        
        monthly_disposable = current_income - current_expenses - current_rent
        if monthly_disposable < 0:
            monthly_disposable = 0
        
        investment_portfolio = investment_portfolio * mi_return + monthly_disposable
        
        current_income *= mi_growth
        current_expenses *= me_growth
        current_rent *= mr_growth
        current_house_price *= mhp_growth
    
    return stop_month, investment_portfolio, history

def format_duration(months):
    years = months // 12
    remaining_months = months % 12
    return f"{years} years, {remaining_months} months"

# ---------------------------------------------------------------------
# Streamlit Interface
# ---------------------------------------------------------------------
st.title("Homeownership Comparison: Buy vs Rent")

# Sidebar for Global Variables (Shared Across Scenarios)
st.sidebar.header("Global Variables (Shared)")
initial_savings = st.sidebar.number_input("Initial Savings (£)", value=73000.0, step=1000.0)
monthly_income = st.sidebar.number_input("Monthly Household Income (£)", value=6500.0, step=100.0)
monthly_expenses = st.sidebar.number_input("Monthly Non-Housing Expenses (£)", value=3000.0, step=100.0)

# Global percentage inputs (as number inputs between given min and max)
annual_income_growth_input = st.sidebar.number_input("Annual Income Growth Rate (%)", 
                                                     min_value=0.0, max_value=20.0, value=3.0, step=0.5)
annual_inflation_rate_input = st.sidebar.number_input("Annual Inflation Rate (%)", 
                                                      min_value=0.0, max_value=20.0, value=2.0, step=0.5)
annual_invest_return_input = st.sidebar.number_input("Annual Investment Return Rate (%)", 
                                                     min_value=0.0, max_value=20.0, value=5.0, step=0.5)
annual_house_price_growth_input = st.sidebar.number_input("House Price Growth Rate (%)", 
                                                          min_value=0.0, max_value=20.0, value=2.0, step=0.5)

# Convert percentage inputs to decimals
annual_income_growth = annual_income_growth_input / 100
annual_inflation_rate = annual_inflation_rate_input / 100
annual_invest_return = annual_invest_return_input / 100
annual_house_price_growth = annual_house_price_growth_input / 100

# Layout: Center inputs for each scenario
st.header("Scenario 1: Buying with a Mortgage")
property_price = st.number_input("Property Price (£)", value=430000.0, step=10000.0)
mortgage_term_years = st.number_input("Mortgage Term (years)", value=35, step=1)
mortgage_interest_rate_input = st.number_input("Mortgage Interest Rate (%)", 
                                               min_value=0.0, max_value=20.0, value=4.5, step=0.1)
deposit_percentage_input = st.number_input("Deposit (%)", 
                                           min_value=0.0, max_value=60.0, value=10.0, step=1.0)

# Convert these to decimals
mortgage_interest_rate = mortgage_interest_rate_input / 100
deposit_fraction = deposit_percentage_input / 100

# New inputs for owner occupier housing costs in Scenario 1.
owner_cost_initial = st.number_input("Initial Owner Occupier Housing Cost (£ per month)", 
                                      value=200.0, step=50.0)
annual_owner_cost_inflation_input = st.number_input("Owner Occupier Housing Cost Inflation Rate (%)", 
                                                    min_value=0.0, max_value=20.0, value=5.0, step=0.5)
annual_owner_cost_inflation = annual_owner_cost_inflation_input / 100

st.markdown("---")
st.header("Scenario 2: Renting")
monthly_rent = st.number_input("Monthly Rent (£)", value=1995.0, step=50.0)
annual_rent_inflation_rate_input = st.number_input("Annual Rent Inflation Rate (%)", 
                                                   min_value=0.0, max_value=20.0, value=3.0, step=0.5)
annual_rent_inflation_rate = annual_rent_inflation_rate_input / 100

# Run simulations when the button is pressed
if st.button("Simulate"):
    # Simulate Scenario 1 (Buying)
    stop_month_buy, final_portfolio_buy, history_buy = simulate_buy_scenario(
        initial_savings, monthly_income, monthly_expenses,
        annual_income_growth, annual_inflation_rate, annual_invest_return,
        property_price, mortgage_term_years, mortgage_interest_rate, deposit_fraction,
        owner_cost_initial, annual_owner_cost_inflation, annual_house_price_growth,
        max_months=360
    )
    # Simulate Scenario 2 (Renting)
    stop_month_rent, final_portfolio_rent, history_rent = simulate_rent_scenario(
        initial_savings, monthly_income, monthly_expenses,
        annual_income_growth, annual_inflation_rate, annual_invest_return,
        property_price, monthly_rent, annual_rent_inflation_rate, annual_house_price_growth,
        max_months=360
    )
    
    st.markdown("### Results")
    if stop_month_buy is not None:
        st.subheader("Scenario 1: Buying with a Mortgage")
        st.write("Homeownership achieved after:", format_duration(stop_month_buy))
    else:
        st.subheader("Scenario 1: Buying with a Mortgage")
        st.write("Homeownership was not achieved within the simulation horizon.")
    
    if stop_month_rent is not None:
        st.subheader("Scenario 2: Renting")
        st.write("Homeownership achieved after:", format_duration(stop_month_rent))
    else:
        st.subheader("Scenario 2: Renting")
        st.write("Homeownership was not achieved within the simulation horizon.")
    
    # -------------------------------
    # Plotting the History
    # -------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot House Price (from Scenario 1 history; both scenarios use same global house price growth)
    ax.plot(history_buy["months"], history_buy["house_price"], label="House Price", color="blue")
    
    # Plot Scenario 1: Equity + Investments
    outstanding_mortgage = property_price * (1 - deposit_fraction)
    net_wealth = [(hp - outstanding_mortgage) + inv for hp, inv in zip(history_buy["house_price"], history_buy["investment_portfolio"])]
    ax.plot(history_buy["months"], net_wealth, label="Scenario 1: Equity + Investments", color="green")
    
    # Plot Scenario 2: Investments
    ax.plot(history_rent["months"], history_rent["investment_portfolio"], label="Scenario 2: Investments", color="red")
    
    # Annotate the points where homeownership is achieved in each scenario.
    if stop_month_buy is not None and stop_month_buy < len(history_buy["months"]):
        ax.plot(stop_month_buy, net_wealth[stop_month_buy], "ko")
        # Offset annotation upward by 15 units
        ax.annotate(f"Buy: {format_duration(stop_month_buy)}", 
                    (stop_month_buy, net_wealth[stop_month_buy]),
                    textcoords="offset points", xytext=(0,15), ha="center", color="green")
    if stop_month_rent is not None and stop_month_rent < len(history_rent["months"]):
        ax.plot(stop_month_rent, history_rent["investment_portfolio"][stop_month_rent], "ko")
        # Offset annotation downward by 15 units
        ax.annotate(f"Rent: {format_duration(stop_month_rent)}", 
                    (stop_month_rent, history_rent["investment_portfolio"][stop_month_rent]),
                    textcoords="offset points", xytext=(0,-15), ha="center", color="red")
    
    ax.set_xlabel("Months")
    ax.set_ylabel("£")
    ax.set_title("Homeownership Comparison Over Time")
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)
