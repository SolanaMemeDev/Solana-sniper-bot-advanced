#!/usr/bin/env python3
"""
Funding Rate Arbitrage Calculator

This script helps you calculate:
1) How many hours you need to hold a position to break even,
   given an annual funding rate and one-time costs (slippage + fees).
2) The annualized funding rate required to break even if you plan 
   to hold for X hours.
3) Your potential net profit or loss given a target hold time, 
   desired profit, etc.

All major variables are configurable.
"""

def funding_arbitrage_calculator(
    slippage=0.005,           # e.g. 0.5% slippage in decimal form
    fees=0.001,               # e.g. 0.1% total round-trip fees in decimal
    annual_funding_rate=1.5,  # e.g. 1.0 = 100% annual
    hold_hours=48,            # e.g. 48 hours hold time
    desired_profit=0.002      # e.g. 0.2% in decimal form
):
    """
    Calculates various metrics for a funding rate 'carry trade' or 'arbitrage':
    - total_cost: sum of slippage + fees
    - hourly_funding_rate: annual_funding_rate / 8760
    - total_funding_earned: hold_hours * hourly_funding_rate
    - net_result: total_funding_earned - total_cost
    - hours_to_break_even: how many hours needed so that total_funding == total_cost
    - annual_rate_for_break_even_in_hold: what annual rate is required to break even in 'hold_hours'
    - hours_for_desired_profit: how many hours needed to get 'desired_profit' above total_cost
    """
    
    # 1. One-time cost (slippage + fees)
    total_cost = slippage + fees
    
    # 2. Hourly funding rate (decimal per hour)
    #    annual_funding_rate is expressed as a decimal (e.g. 1.0 = 100%)
    #    1 year ≈ 365 days × 24 hours = 8760 hours
    hourly_funding_rate = annual_funding_rate / 8760.0
    
    # 3. Total funding you'd earn over 'hold_hours'
    total_funding_earned = hold_hours * hourly_funding_rate
    
    # 4. Net result after subtracting the cost
    net_result = total_funding_earned - total_cost
    
    # 5. Hours required to break even:  cost = (hourly_rate × hours)
    #    => hours = cost / hourly_rate
    #    If hourly_funding_rate is 0, we handle that edge case.
    if hourly_funding_rate > 0:
        hours_to_break_even = total_cost / hourly_funding_rate
    else:
        hours_to_break_even = float('inf')  # can't break even if funding=0
    
    # 6. If we want to break even exactly in 'hold_hours',
    #    how big must the annual_funding_rate be?
    #    cost = hold_hours × (annual_rate / 8760)
    #    => annual_rate = cost × 8760 / hold_hours
    if hold_hours > 0:
        annual_rate_for_break_even_in_hold = total_cost * 8760.0 / hold_hours
    else:
        annual_rate_for_break_even_in_hold = float('inf')
    
    # 7. Hours to achieve 'desired_profit' above cost:
    #    desired_profit + total_cost = hold_hours × hourly_funding_rate
    #    => hold_hours = (cost + desired_profit) / hourly_funding_rate
    total_required = total_cost + desired_profit
    if hourly_funding_rate > 0:
        hours_for_desired_profit = total_required / hourly_funding_rate
    else:
        hours_for_desired_profit = float('inf')
    
    return {
        'slippage_decimal': slippage,
        'fees_decimal': fees,
        'annual_funding_rate_decimal': annual_funding_rate,
        'hold_hours': hold_hours,
        'desired_profit_decimal': desired_profit,
        'total_cost_decimal': total_cost,
        'hourly_funding_rate_decimal': hourly_funding_rate,
        'total_funding_earned_decimal': total_funding_earned,
        'net_result_decimal': net_result,
        'hours_to_break_even': hours_to_break_even,
        'annual_rate_for_break_even_in_hold_decimal': annual_rate_for_break_even_in_hold,
        'hours_for_desired_profit': hours_for_desired_profit
    }

def print_calculator_results(results):
    """
    Nicely format and print the results from funding_arbitrage_calculator().
    """
    print("\n--- FUNDING ARBITRAGE CALCULATOR RESULTS ---")
    print(f"Slippage (decimal)           : {results['slippage_decimal']:.4f} "
          f"({results['slippage_decimal']*100:.2f}%)")
    print(f"Fees (decimal)               : {results['fees_decimal']:.4f} "
          f"({results['fees_decimal']*100:.2f}%)")
    print(f"Total one-time cost (decimal): {results['total_cost_decimal']:.4f} "
          f"({results['total_cost_decimal']*100:.2f}%)")
    print(f"Annual funding rate (decimal): {results['annual_funding_rate_decimal']:.4f} "
          f"({results['annual_funding_rate_decimal']*100:.2f}%)")
    print(f"Hourly funding rate (decimal): {results['hourly_funding_rate_decimal']:.8f} "
          f"({results['hourly_funding_rate_decimal']*100:.6f}% per hour)")
    print(f"Hold duration (hours)        : {results['hold_hours']} h")
    print(f"Desired profit (decimal)     : {results['desired_profit_decimal']:.4f} "
          f"({results['desired_profit_decimal']*100:.2f}%)")
    
    print("\n--- KEY CALCULATIONS ---")
    print(f"Total Funding Earned (decimal): {results['total_funding_earned_decimal']:.6f} "
          f"({results['total_funding_earned_decimal']*100:.4f}%)")
    print(f"Net Result (decimal)         : {results['net_result_decimal']:.6f} "
          f"({results['net_result_decimal']*100:.4f}%) after cost")
    print(f"Hours to Break Even          : {results['hours_to_break_even']:.2f} hours")
    print(f"Days to Break Even           : {results['hours_to_break_even']/24:.2f} days")
    print(f"Annual Rate for Break Even in {results['hold_hours']}h : "
          f"{results['annual_rate_for_break_even_in_hold_decimal']:.4f} "
          f"({results['annual_rate_for_break_even_in_hold_decimal']*100:.2f}%)")
    print(f"Hours to achieve desired profit: {results['hours_for_desired_profit']:.2f} hours")
    print(f"Days to achieve desired profit : {results['hours_for_desired_profit']/24:.2f} days")
    print("--- END ---\n")

def main():
    """
    Example usage of the calculator. Modify these parameters
    to test different scenarios.
    """
    # Customize these parameters as you wish
    slippage = 0.005           # 0.5% slippage
    fees = 0.001               # 0.1% total round-trip fees
    annual_funding_rate = 20 # 1.0 = 100% annual
    hold_hours = 48            # hold for 48 hours
    desired_profit = 0.01     # 0.2% additional profit target above cost
    
    # Calculate
    results = funding_arbitrage_calculator(
        slippage=slippage,
        fees=fees,
        annual_funding_rate=annual_funding_rate,
        hold_hours=hold_hours,
        desired_profit=desired_profit
    )
    
    # Print
    print_calculator_results(results)

if __name__ == "__main__":
    main()
