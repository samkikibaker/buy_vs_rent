import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

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
                           max_months=360):
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
st.title("Homeownership Comparison: Buy vs Rent")

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
tab_simulation, tab_methodology = st.tabs(["Simulation", "Methodology & Assumptions"])

with tab_simulation:
    st.header("Scenario 1: Buying with a Mortgage")
    property_price = st.number_input("Property Price (£)", value=430000.0, step=10000.0)
    mortgage_term_years = st.number_input("Mortgage Term (years)", value=35, step=1)
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
            max_months=360
        )
        stop_month_rent, final_portfolio_rent, history_rent = simulate_rent_scenario(
            initial_savings, monthly_income, monthly_expenses,
            annual_income_growth, annual_inflation_rate, annual_invest_return,
            property_price, monthly_rent, annual_rent_inflation_rate, annual_house_price_growth,
            max_months=360
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
        ax.plot(months, buy_cum_spent, label="Buy: Cumulative Spent", color="green")
        ax.plot(months, rent_cum_spent, label="Rent: Cumulative Spent", color="red")

        # Determine the crossover point (first month where buying cost becomes lower than renting)
        crossover_month = None
        for m, spent_buy, spent_rent in zip(history_buy["months"], buy_cum_spent, rent_cum_spent):
            if spent_buy < spent_rent:
                crossover_month = m
                break

        if crossover_month is not None:
            # Draw vertical line at the crossover point
            ax.axvline(crossover_month, color="purple", linestyle="--", linewidth=1.5)
            # Highlight the regions: left of crossover (renting is cheaper) and right (buying is cheaper)
            ax.axvspan(0, crossover_month, color="red", alpha=0.2, label="Renting Cheaper")
            ax.axvspan(crossover_month, months[-1], color="green", alpha=0.2, label="Buying Cheaper")
            ax.annotate(f"Crossover: {format_duration(crossover_month)}",
                        (crossover_month, np.max([buy_cum_spent.max(), rent_cum_spent.max()])),
                        textcoords="offset points", xytext=(0,20), ha="center", color="purple")

        # Also plot house price and additional curves for context.
        ax.plot(months, history_buy["house_price"], label="House Price", color="blue")
        outstanding_mortgage = property_price * (1 - deposit_fraction)
        net_wealth = [(hp - outstanding_mortgage) + inv for hp, inv in zip(history_buy["house_price"], history_buy["investment_portfolio"])]
        ax.plot(months, net_wealth, label="Scenario 1: Equity + Investments", color="darkgreen")
        ax.plot(months, history_rent["investment_portfolio"], label="Scenario 2: Investments", color="darkred")

        # Annotate homeownership points if available.
        if stop_month_buy is not None and stop_month_buy < len(months):
            ax.plot(stop_month_buy, net_wealth[stop_month_buy], "ko")
            ax.annotate(f"Buy: {format_duration(stop_month_buy)}",
                        (stop_month_buy, net_wealth[stop_month_buy]),
                        textcoords="offset points", xytext=(0,15), ha="center", color="green")
        if stop_month_rent is not None and stop_month_rent < len(months):
            ax.plot(stop_month_rent, history_rent["investment_portfolio"][stop_month_rent], "ko")
            ax.annotate(f"Rent: {format_duration(stop_month_rent)}",
                        (stop_month_rent, history_rent["investment_portfolio"][stop_month_rent]),
                        textcoords="offset points", xytext=(0,-15), ha="center", color="red")

        ax.set_xlabel("Months")
        ax.set_ylabel("£")
        ax.set_title("Homeownership Comparison Over Time\n(Regions Highlighted Based on Cheaper Option)")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

with tab_methodology:
    st.header("Methodology & Assumptions")
    st.markdown("""
    **Overview:**

    This simulation compares two scenarios – buying a property with a mortgage versus renting and saving to purchase the same property with cash. 
    The objective is to determine the time required to achieve homeownership as well as the cumulative amount spent on each approach.

    **Scenario 1: Buying with a Mortgage**
    - **Deposit & Mortgage:**  
      - You pay an upfront deposit and finance the remainder with a mortgage.
      - The cumulative spending starts with the deposit.
    - **Monthly Costs:**  
      - **Mortgage Interest:** Monthly interest is paid on the outstanding mortgage.
      - **Owner Costs:** A monthly owner occupier housing cost is paid, which adjusts for inflation.
      - **Investments:** Any disposable income (after deducting expenses, interest, and owner costs) is invested.
    - **Homeownership Condition:**  
      - When the investment portfolio equals or exceeds the outstanding mortgage.
      - Cumulative spending includes the deposit plus all monthly interest and owner cost payments.

    **Scenario 2: Renting**
    - **Rent & Investment:**  
      - Savings are fully invested.
      - Monthly rent is paid, and the cumulative spending tracks the sum of these rent payments.
    - **Monthly Updates:**  
      - Rent, income, and non-housing expenses grow at their specified rates.
      - Investments grow from the remaining disposable income.
    - **Homeownership Condition:**  
      - When the investment portfolio equals or exceeds the current property price.

    **Assumptions:**
    - All growth and inflation rates (including for the mortgage interest and housing costs) remain constant over the simulation period.
    - Monthly multipliers are derived from the given annual rates.
    - Disposable income is invested only after all required expenses are paid.
    - The simulation runs for up to 30 years (360 months), or until homeownership is achieved.

    **Purpose:**
    This model provides a side-by-side comparison of the time horizon and cumulative costs incurred in achieving homeownership when buying immediately versus renting and investing.
    """)
