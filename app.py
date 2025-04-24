import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------
# Simulation Functions
# ---------------------------------------------------------------------
def simulate_buy_scenario(initial_savings, monthly_income, monthly_expenses,
                          annual_income_growth, annual_inflation_rate, annual_invest_return,
                          property_price, mortgage_term_years, mortgage_interest_rate, deposit_fraction,
                          owner_cost_initial, annual_owner_cost_inflation, annual_house_price_growth,
                          max_months=480):
    """
    Scenario 1: Buy a property now using a mortgage.
    
    Simulation Mechanics:
    1. At time zero, you pay the deposit and finance the remaining amount with a mortgage.
    2. Every month:
       - Update income, expenses, and owner costs using growth/inflation rates.
       - The property price grows using the annual house price growth.
       - Pay monthly mortgage interest and owner costs.
       - Add any positive disposable income to your investment portfolio (which grows at the monthly investment rate).
    3. Homeownership is deemed achieved when the investment portfolio meets or exceeds the outstanding mortgage.
    
    Additionally, this function tracks the cumulative amount spent on housing:
      - For buying: deposit + interest payments + owner occupier housing costs.
    
    Returns:
    - stop_month: First month when homeownership is achieved (or None)
    - final_investment_portfolio: Final investment portfolio value.
    - history: Dictionary with monthly history: "months", "house_price", "investment_portfolio", 
               "net_wealth", and "cumulative_spent".
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

    # Investment portfolio starts after paying the deposit.
    investment_portfolio = initial_savings - deposit_amount
    outstanding_mortgage = property_price * (1 - deposit_fraction)
    
    current_income = monthly_income
    current_expenses = monthly_expenses
    current_owner_cost = owner_cost_initial
    current_house_price = property_price
    
    # Cumulative spent starts with the deposit.
    cumulative_spent = deposit_amount
    
    # History tracking
    history = {
        "months": [],
        "house_price": [],
        "investment_portfolio": [],
        "net_wealth": [],
        "cumulative_spent": []
    }
    stop_month = None
    
    for month in range(max_months):
        net_wealth = (current_house_price - outstanding_mortgage) + investment_portfolio
        history["months"].append(month)
        history["house_price"].append(current_house_price)
        history["investment_portfolio"].append(investment_portfolio)
        history["net_wealth"].append(net_wealth)
        history["cumulative_spent"].append(cumulative_spent)
        
        # Check homeownership condition
        if stop_month is None and investment_portfolio >= outstanding_mortgage:
            stop_month = month
        
        interest_payment = outstanding_mortgage * m_interest
        monthly_disposable = current_income - current_expenses - interest_payment - current_owner_cost
        if monthly_disposable < 0:
            monthly_disposable = 0
        
        # Add monthly cost (interest and owner cost) to cumulative spent
        cumulative_spent += interest_payment + current_owner_cost
        
        # Update investment portfolio and monthly variables
        investment_portfolio = investment_portfolio * mi_return + monthly_disposable
        current_income *= mi_growth
        current_expenses *= me_growth
        current_owner_cost *= moc_growth
        current_house_price *= mhp_growth
        
    return stop_month, investment_portfolio, history

def simulate_rent_scenario(initial_savings, monthly_income, monthly_expenses,
                           annual_income_growth, annual_inflation_rate, annual_invest_return,
                           property_price, monthly_rent, annual_rent_inflation_rate, annual_house_price_growth,
                           max_months=480):
    """
    Scenario 2: Rent now and purchase for cash later.
    
    Simulation Mechanics:
    1. All initial savings are invested.
    2. Every month:
         - Update income, expenses, and rent using their respective growth/inflation multipliers.
         - The property price grows according to the annual house price growth.
         - Add any positive disposable income to your investment portfolio.
    3. Homeownership is met when the investment portfolio reaches or exceeds the current property price.
    
    Additionally, this function tracks the cumulative amount spent on rent.
    
    Returns:
    - stop_month: The first month when homeownership is achieved (or None)
    - final_investment_portfolio: Final value of the investment portfolio.
    - history: Dictionary with monthly history: "months", "house_price", "investment_portfolio", 
               and "cumulative_spent".
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
    
    # Cumulative spent on rent.
    cumulative_spent = 0
    
    history = {
        "months": [],
        "house_price": [],
        "investment_portfolio": [],
        "cumulative_spent": []
    }
    stop_month = None
    
    for month in range(max_months):
        history["months"].append(month)
        history["house_price"].append(current_house_price)
        history["investment_portfolio"].append(investment_portfolio)
        history["cumulative_spent"].append(cumulative_spent)
        
        if stop_month is None and investment_portfolio >= current_house_price:
            stop_month = month
        
        monthly_disposable = current_income - current_expenses - current_rent
        if monthly_disposable < 0:
            monthly_disposable = 0
        
        cumulative_spent += current_rent
        
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
st.title("Buy vs Rent")

# Sidebar for Global Variables
st.sidebar.header("Global Variables (Shared)")
initial_savings = st.sidebar.number_input("Initial Savings (£)", value=73000.0, step=1000.0)
monthly_income = st.sidebar.number_input("Monthly Household Income (£)", value=6500.0, step=100.0)
monthly_expenses = st.sidebar.number_input("Monthly Non-Housing Expenses (£)", value=3000.0, step=100.0)

# Global percentage inputs
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

# Create tabs
tab_methodology, tab_simulation,  = st.tabs(["Methodology & Assumptions", "Simulation"])

with tab_methodology:
    st.markdown("""
    # Methodology & Assumptions
    
    ### Disclaimer
    This does not constitute financial advice. 
    
    ### Overview
    This simulation compares two scenarios: buying a property with a mortgage versus renting and saving to purchase the same property with cash. 
    The objective is to determine the time required to achieve homeownership as well as the cumulative amount spent on each approach.

    ### Scenario 1: Buying with a Mortgage
    - You immediately buy a property with a mortgage and invest any spare income
    - Once your investments grow to exceed the remaining mortgage balance, you pay off the mortgage in one go
    
    ### Scenario 2: Renting until cash Purchase
    - You rent a property, investing any spare income
    - Once your investments grow to exceed the value of the property (including any growth), you buy with 100% cash
    
    ### Assumptions
    - All spare income is invested
    - The interest rate of the mortgage stays fixed for the entire term
    - There are no penalties for early repayment
    - Moving & completion costs are not considered    
    
    ### Inputs & Definitions
    - Initial Savings: The amounts of savings you start with. This will be used for the deposit in scenario 1 with 
                     any spare being invested. In scenario 2 this is what you start investing with. 
    - Monthly Household Income: Take home pay (i.e. after tax, pension contributions etc) for your household per month.
    - Monthly Non-Housing Expenses: Amount spent on any expenses not relating to rent/mortgage/ground rent/service charge/
                                  owner-occupier housing costs. These should be standard expenses (food, bills, holidays
                                  etc). The difference between your income and expenses will be invested. 
    - Annual Income Growth Rate: How much your income rises in percentage terms each year (ignoring inflation)
    - Annual Inflation Rate: Headline inflation rate. Note this will be used to inflate the Monthly Non-Housing Expenses
    - Annual Investment Return Rate: How much your investments rise per year in percentage terms. 
    - House Price Growth Rate: How much the property increases in value each year in percentage terms.
    - Property Price: Price of the property you want to purchase. In scenario 1 this is the price you buy at immediately. 
                    In scenario 2 this price will grow and this is what you need to reach. 
    - Mortgage Term: Years over which the mortgage runs
    - Mortgage Interest Rate: Annual interest rate over the entire lifetime of the mortgage (assumed fixed)
    - Deposit: The amount you put down on the property in scenario 1 as a percentage of the property's price. Note this 
             must not be set in a way that makes it exceed your initial savings. 
    - Initial Owner Occupier Housing Cost: Monthly cost of owning the home. This could include repairs, renovations etc.
    - Owner Occupier Housing Cost Inflation Rate: How much the Initial Owner Occupier Housing Cost increases per year in 
                                                percentage terms.
    - Monthly Rent: How much you initially pay each month in rent in scenario 2
    - Annual Rent Inflation Rate: How much the Monthly Rent increases per year in percentage terms
    
    ### Instructions
    1. Fill in all the global inputs (refer to the Inputs & Definitions above for guidance)
    2. Under the Simulation tab, fill in the inputs for scenarios 1 & 2 (refer to the Inputs & Definitions above for guidance)
    3. Click Simulate
    4. Inspect the results for each scenario to see:
        - How long it takes to achieve home ownership
        - The cumulative cost of homeownership (mortgage/rent, bills, etc)
        - The crossover point at which the cumulative cost of buying is lower than renting
    """)

with tab_simulation:
    st.header("Scenario 1: Buying with a Mortgage")
    property_price = st.number_input("Property Price (£)", value=430000.0, step=10000.0)
    mortgage_term_years = st.number_input("Mortgage Term (years)", value=35, step=1, min_value=1, max_value=40)
    mortgage_interest_rate_input = st.number_input("Mortgage Interest Rate (%)", 
                                                   min_value=0.0, max_value=20.0, value=4.5, step=0.1)
    deposit_percentage_input = st.number_input("Deposit (%)", 
                                               min_value=0.0, max_value=60.0, value=10.0, step=1.0)
    mortgage_interest_rate = mortgage_interest_rate_input / 100
    deposit_fraction = deposit_percentage_input / 100
    
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

    if st.button("Simulate"):
        stop_month_buy, final_portfolio_buy, history_buy = simulate_buy_scenario(
            initial_savings, monthly_income, monthly_expenses,
            annual_income_growth, annual_inflation_rate, annual_invest_return,
            property_price, mortgage_term_years, mortgage_interest_rate, deposit_fraction,
            owner_cost_initial, annual_owner_cost_inflation, annual_house_price_growth,
            max_months=480
        )
        stop_month_rent, final_portfolio_rent, history_rent = simulate_rent_scenario(
            initial_savings, monthly_income, monthly_expenses,
            annual_income_growth, annual_inflation_rate, annual_invest_return,
            property_price, monthly_rent, annual_rent_inflation_rate, annual_house_price_growth,
            max_months=480
        )
        
        st.header("Results")
        if stop_month_buy is not None:
            st.subheader("Scenario 1: Buying with a Mortgage")
            st.write("Homeownership achieved after:", format_duration(stop_month_buy))
            st.write("Cumulative amount spent:",
                     "£{:,.2f}".format(history_buy["cumulative_spent"][stop_month_buy]))
        else:
            st.subheader("Scenario 1: Buying with a Mortgage")
            st.write("Homeownership was not achieved within the simulation horizon.")

        if stop_month_rent is not None:
            st.subheader("Scenario 2: Renting")
            st.write("Homeownership achieved after:", format_duration(stop_month_rent))
            st.write("Cumulative amount spent:",
                     "£{:,.2f}".format(history_rent["cumulative_spent"][stop_month_rent]))
        else:
            st.subheader("Scenario 2: Renting")
            st.write("Homeownership was not achieved within the simulation horizon.")

        # -------------------------------
        # Plotting the History with Highlighted Regions
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 6))

        months = np.array(history_buy["months"])
        buy_cum_spent = np.array(history_buy["cumulative_spent"])
        rent_cum_spent = np.array(history_rent["cumulative_spent"])

        # Plot cumulative spent curves
        ax.plot(months, buy_cum_spent, label="Buy: Cumulative Spent", color="green", linestyle="--")
        ax.plot(months, rent_cum_spent, label="Rent: Cumulative Spent", color="red", linestyle="--")

        # Determine the crossover point (first month where buying cost becomes lower than renting)
        crossover_month = None
        for m, spent_buy, spent_rent in zip(history_buy["months"], buy_cum_spent, rent_cum_spent):
            if spent_buy < spent_rent:
                crossover_month = m
                break

        if crossover_month is not None:
            # Draw vertical line at the crossover point
            ax.axvline(crossover_month, color="black", linestyle="--", linewidth=1.5)
            # Highlight the regions: left of crossover (renting is cheaper) and right (buying is cheaper)
            ax.axvspan(0, crossover_month, color="red", alpha=0.2, label="Renting Cheaper")
            ax.axvspan(crossover_month, months[-1], color="green", alpha=0.2, label="Buying Cheaper")
            ax.annotate(f"Crossover: {format_duration(crossover_month)}",
                        (crossover_month, np.max([buy_cum_spent.max(), rent_cum_spent.max()])),
                        textcoords="offset points", xytext=(0,20), ha="center", color="black", arrowprops=dict(arrowstyle="-", color="black", linewidth=1))

        # Also plot house price and additional curves for context.
        ax.plot(months, history_buy["house_price"], label="House Price", color="blue")
        outstanding_mortgage = property_price * (1 - deposit_fraction)
        net_wealth = [(hp - outstanding_mortgage) + inv for hp, inv in zip(history_buy["house_price"], history_buy["investment_portfolio"])]
        ax.plot(months, net_wealth, label="Scenario 1: Equity + Investments", color="green")
        ax.plot(months, history_rent["investment_portfolio"], label="Scenario 2: Investments", color="red")

        # Annotate homeownership points if available.
        if stop_month_buy is not None and stop_month_buy < len(months):
            ax.plot(stop_month_buy, net_wealth[stop_month_buy], "ko")
            ax.annotate(f"Buy: {format_duration(stop_month_buy)}",
                        (stop_month_buy, net_wealth[stop_month_buy]),
                        textcoords="offset points", xytext=(0,25), ha="center", color="green", arrowprops=dict(arrowstyle="-", color="black", linewidth=1))
        if stop_month_rent is not None and stop_month_rent < len(months):
            ax.plot(stop_month_rent, history_rent["investment_portfolio"][stop_month_rent], "ko")
            ax.annotate(f"Rent: {format_duration(stop_month_rent)}",
                        (stop_month_rent, history_rent["investment_portfolio"][stop_month_rent]),
                        textcoords="offset points", xytext=(0,-25), ha="center", color="red", arrowprops=dict(arrowstyle="-", color="black", linewidth=1))

        ax.set_xlabel("Months")
        ax.set_ylabel("£")
        ax.set_title("Homeownership Comparison Over Time")
        ax.legend()
        ax.grid(True)
        formatter = mticker.FuncFormatter(lambda x, pos: f'£{x:,.0f}')
        ax.yaxis.set_major_formatter(formatter)

        fig.tight_layout()
        st.pyplot(fig)
