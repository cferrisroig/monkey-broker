# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 21:44:03 2019

@author: Christian
"""


##########################################
########     IMPORT LIBRARIES     ########
##########################################
import datetime
#import pandas as pd
import pandas_datareader.data as web
import numpy as np
import plotly
import plotly.graph_objects as go
import plotly.figure_factory as ff


##########################################
########        INPUT DATA        ########
##########################################
#Define start and end date for the data
start = datetime.datetime(2015, 12, 11)
end = datetime.datetime(2019, 12, 10)

#Declare the tickers in the analysis
ticker_list = ["HPQ"] #Other tickers: ^GSPC, HPQ, AMZN, WM, IBM, CL, PG, TSLA

#Define the initial amount of money available per investor
initial_cash = 10000



##########################################
########  FUNCTIONS  DECLARATION  ########
##########################################

#||||==-- CREATE A VECTOR WITH THE OPERATIONS OF THE MONKEYS --==||||
def monkey_broker (trade_days, freq_op): 
    #trade_days is the days of the experiment
    #freq_op is the average hold time for a position
    next_op = "B" #B for BUY // S for SELL
    hold_op = round(np.random.uniform(1, freq_op)) #days between operations
    operations = [] #Vector with operations executed
    op_day = 0
    
    #Build vector with operations
    for i in range(trade_days-1): 
        if op_day < hold_op:
            operations.append(0)
            op_day += 1
        else: 
            operations.append(next_op)
            hold_op = round(np.random.uniform(1, freq_op))
            op_day = 0
            if next_op == "B":
                next_op = "S"
            elif next_op == "S":
                next_op = "B"
    
    #Avoid last operation is a BUY by setting a SELL the last day (if needed)
    if next_op == "S":
        operations.append("S")
    else:
        operations.append(0)
    
    return operations



#||||==-- CREATE A DICTIONARY WITH THE OPERATIONS OF MULTIPLE MONKEYS --==||||
def monkey_population (n, freq_op):
    monkeys = {}
    
    for i in range(n):
        monkeys[i] = monkey_broker (trade_days, freq_op)
    
    return monkeys



#||||==-- CREATE A VECTOR WITH LONG TERM OPERATION --==||||
def lt_broker (trade_days): 
    operations = [0] * (trade_days)
    operations[0] = "B"
    operations[-1] = "S"

    return operations



#||||==-- GET THE PRICES AND ADD THE DAILY AVERAGE VALUE CALCULATED WITH THE HIGH AND LOW --==||||
def get_prices (ticker_list): 
    stocks_price = {}
    
    for ticker in ticker_list: 
        price = web.DataReader(ticker, 'yahoo', start, end)
        price["AVG"] = (price["High"] + price["Low"]) / 2
        price["Benchmark"] = price["AVG"] * initial_cash / price["AVG"][0]
        stocks_price[ticker] = price
    
    return stocks_price



#||||==-- EXECUTE THE ORDERS FOR ONE INVESTOR --==||||
def wallet_evolution (operations, ticker): 
    free_cash = []
    shares_owned = []
    wallet_value = []
    
    for op in operations: 
        if op == 0: 
            if len(free_cash) == 0:         #First day and no buy
                free_cash.append(initial_cash)
                shares_owned.append(0)
                wallet_value.append(0)
            elif shares_owned[-1] == 0:     #Days without stocks 
                free_cash.append(free_cash[-1])
                shares_owned.append(0)
                wallet_value.append(0)
            elif shares_owned[-1] > 0:      #Days when hold position
                free_cash.append(free_cash[-1])
                new_value = stocks_price[ticker]["AVG"][len(shares_owned)] * shares_owned[-1]
                shares_owned.append(shares_owned[-1])
                wallet_value.append(new_value)
        elif op == "B":                     #Days when buy shares
            share_price = stocks_price[ticker]["AVG"][len(free_cash)]
            if len(free_cash) == 0: 
                shares_ex = int(initial_cash / share_price)
                wallet_value.append(share_price * shares_ex)
                free_cash.append(initial_cash - wallet_value[-1])
            else:
                shares_ex = int(free_cash[-1] / share_price)
                wallet_value.append(share_price * shares_ex)
                free_cash.append(free_cash[-1] - wallet_value[-1])
            shares_owned.append(shares_ex)
        elif op == "S":                     #Days when sell shares
            share_price = stocks_price[ticker]["AVG"][len(free_cash)]
            shares_ex = shares_owned[-1]
            shares_owned.append(0)
            wallet_value.append(0)
            free_cash.append(free_cash[-1] + share_price * shares_ex)
    
    total_value = [x + y for x, y in zip(free_cash, wallet_value)]

    return {"Free cash": free_cash, "Wallet value": wallet_value, "Total": total_value}
    


#||||==-- Execution of the orders for an investors group --==||||
def wallets_evolution (investors_group, ticker):
    wallet = {}
    
    if ticker in ticker_list: 
        for investor in investors_group:
           wallet[investor] = wallet_evolution (investors_group[investor], ticker)
           #print ("Monkey number: " + str(investor))
           #print ("Ends period with: " + str(wallet[investor]["Total"][-1]) )
        return wallet
    else:
        print ("Ticker not in list, include it and run the program again")
        return False



#||||==-- Growth percentage of the investment for an invetsors group --==||||
def benchmark_growth (ticker):
    if ticker in ticker_list: 
        growth = ( stocks_price[ticker]["AVG"][-1] - stocks_price[ticker]["AVG"][0] ) / stocks_price[ticker]["AVG"][0]
        return growth
    else: 
        print ("Ticker not in list, include it and run the program again")
        return False



#||||==-- Growth percentage of the investment for an invetsors group --==||||
def wallet_growth (wallets): 
    total_growth = []
    
    for wallet in wallets: 
        growth = ( wallets[wallet]["Total"][-1] - wallets[wallet]["Total"][0] ) / wallets[wallet]["Total"][0]
        wallets[wallet]["Growth"] = growth
        total_growth.append(growth)
    
    return total_growth



#||||==-- Plot of wallets for an investors group --==||||
def wallets_plot (investors_wallets, ticker, file):
    file_name = file + ".html"
    data = []
    
    for wallet in investors_wallets:
        investor_data = go.Scatter(
                x = stocks_price[ticker].index,
                y = investors_wallets[wallet]["Total"],
                mode = 'lines',
                line = dict(color = 'rgb(130,130,130)', width = 1),
                name = "Investor_" + str(wallet))
        data = data + [investor_data]
    
    """
    lt_evolution = go.Scatter(
        x = stocks_price[ticker].index,
        y = wallet_evolution(lt_broker(trade_days),ticker)["Total"],
        mode = 'lines',
        line = dict(color = 'rgb(30,30,30)', width = 5 ),
        name = ticker)
    data = data + [lt_evolution]
    """
    
    benchmark = go.Scatter(
        x = stocks_price[ticker].index,
        y = stocks_price[ticker]["Benchmark"],
        mode = 'lines',
        line = dict(color = 'rgb(30,30,30)', width = 5 ),
        name = ticker)
    data = data + [benchmark]
    
    
    layout = go.Layout(
        title = file,
        xaxis = dict(title='Time'),
        yaxis = dict(title='Monetary Units'))
    
    fig = go.Figure(data=data, layout=layout)
    
    plotly.offline.plot(fig, show_link = False, output_type = 'file', 
                        filename = file_name, auto_open = True)
    
    return True



#||||==-- Plot histogram for growths from two groups --==||||
def growth_plot (growth_1, growth_2, file):
    file_name = file + ".html"
    
    # Group data together
    hist_data = [growth_1, growth_2]
    group_labels = ['Group 1', 'Group 2']
    
    # Create distplot with custom bin_size
    fig = ff.create_distplot(hist_data, group_labels, bin_size=.05, curve_type='normal')
    fig.show()
    
    plotly.offline.plot(fig, show_link = False, output_type = 'file', 
                        filename = file_name, auto_open = True)
    
    return True




##########################################
########   SIMULATION EXECUTION   ########
##########################################

import time
start_time = time.time()
print("--- %s seconds at start ---" % (time.time() - start_time))

#Get the prices and calculate the days of tradding data available
stocks_price = get_prices (ticker_list)
trade_days = stocks_price[ticker_list[0]]["AVG"].count()
print("--- %s seconds to get prices ---" % (time.time() - start_time))

#Generate the dictionaries with the operations for the monkeys
impatient_monkeys = monkey_population (200, 8)
patient_monkeys = monkey_population (200, 65)
print("--- %s seconds to populate all monkeys ---" % (time.time() - start_time))

#Generate the dictionaries with the evolutoin of the wallets
wallets_impatients = wallets_evolution (impatient_monkeys, "HPQ")
wallets_patients = wallets_evolution (patient_monkeys, "HPQ")
print("--- %s seconds to calculate all monkeys wallets ---" % (time.time() - start_time))

#Calculate the growth for the benchmark and the wallets
hpq_growth = benchmark_growth ("HPQ")
print("Benchmark growth is: " + str(hpq_growth) )

impatient_growth = wallet_growth (wallets_impatients)
patient_growth = wallet_growth (wallets_patients)
print("Impatient monkey got an average growth of: " + str(np.average(impatient_growth)) )
print("Patient monkey got an average growth of: " + str(np.average(patient_growth)) )

print("--- %s seconds to calculate all wallets growth ---" % (time.time() - start_time))




growth_plot (impatient_growth, patient_growth, "growth")







#Plot the evolution for every wallet
#wallets_plot (wallets_impatients, "HPQ", "Prueba1")
#print("--- %s seconds to plot impatient monkeys wallets---" % (time.time() - start_time))
#wallets_plot (wallets_patients, "HPQ", "Prueba2")
#print("--- %s seconds to plot patient monkeys wallets---" % (time.time() - start_time))