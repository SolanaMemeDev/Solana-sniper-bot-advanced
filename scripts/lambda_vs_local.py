'''
Calculator to compare Lambda Labs costs vs building a local machine for AI development
'''

# Cost Constants
LAMBDA_HOURLY_RATE = 1.50  # Lambda Labs cost per hour
LOCAL_MACHINE_COST = 6000  # Cost to build local machine
ELECTRICITY_COST_PER_HOUR = 0.50  # Estimated electricity cost per hour

# Usage Constants
HOURS_PER_DAY = 6
DAYS_PER_WEEK = 6
WEEKS_PER_MONTH = 4.33  # Average weeks in a month
WEEKS_PER_YEAR = 52

def calculate_costs():
    # Daily Lambda cost
    daily_lambda_cost = LAMBDA_HOURLY_RATE * HOURS_PER_DAY
    
    # Weekly Lambda cost
    weekly_lambda_cost = daily_lambda_cost * DAYS_PER_WEEK
    
    # Monthly Lambda cost
    monthly_lambda_cost = weekly_lambda_cost * WEEKS_PER_MONTH
    
    # Yearly Lambda cost
    yearly_lambda_cost = weekly_lambda_cost * WEEKS_PER_YEAR
    
    # Break-even calculations
    total_hours_per_year = HOURS_PER_DAY * DAYS_PER_WEEK * WEEKS_PER_YEAR
    yearly_electricity_cost = ELECTRICITY_COST_PER_HOUR * total_hours_per_year
    
    # Time to break even (including electricity costs)
    total_hourly_savings = LAMBDA_HOURLY_RATE - ELECTRICITY_COST_PER_HOUR
    hours_to_breakeven = LOCAL_MACHINE_COST / total_hourly_savings
    weeks_to_breakeven = hours_to_breakeven / (HOURS_PER_DAY * DAYS_PER_WEEK)
    months_to_breakeven = weeks_to_breakeven / WEEKS_PER_MONTH
    years_to_breakeven = months_to_breakeven / 12
    
    # Print results
    print(f"🌙 MoonDev's AI Cost Calculator")
    print(f"\n💰 Lambda Labs Costs:")
    print(f"Daily cost: ${daily_lambda_cost:.2f}")
    print(f"Weekly cost: ${weekly_lambda_cost:.2f}")
    print(f"Monthly cost: ${monthly_lambda_cost:.2f}")
    print(f"Yearly cost: ${yearly_lambda_cost:.2f}")
    
    print(f"\n🖥️ Local Machine Analysis:")
    print(f"Initial machine cost: ${LOCAL_MACHINE_COST:.2f}")
    print(f"Yearly electricity cost: ${yearly_electricity_cost:.2f}")
    
    print(f"\n⏰ Break-even Analysis:")
    print(f"Hours to break even: {hours_to_breakeven:.1f}")
    print(f"Weeks to break even: {weeks_to_breakeven:.1f}")
    print(f"Months to break even: {months_to_breakeven:.1f}")
    print(f"Years to break even: {years_to_breakeven:.1f}")
    
    print(f"\n💡 Recommendation:")
    if years_to_breakeven > 2:
        print("Stick with Lambda Labs - break-even time is too long!")
    elif years_to_breakeven > 1:
        print("Consider local machine if you plan long-term usage.")
    else:
        print("Local machine might be cost-effective!")

if __name__ == "__main__":
    calculate_costs()