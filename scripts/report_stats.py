import numpy as np
import pandas as pd
from scipy import stats
from dateutil import parser
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import statistics
from time import sleep as sl
import itertools
from collections import defaultdict
import json
import random
import os
import locale
locale.setlocale(locale.LC_ALL,'')



DATA_PATH = '../trading_history/'
file_of_the_day = 0
all_files = os.listdir(DATA_PATH)
random.shuffle(all_files)
pnl = defaultdict(list)
index = 0
trades_total = 0
trade_win_pct = 0

data = pd.read_csv(DATA_PATH + all_files[file_of_the_day],sep='\t')
print (DATA_PATH + all_files[file_of_the_day])

print( data.shape )
print( data.columns )
print( data.dtypes )

buyorsell = data['Action']
price_list = data['Price']
qty_list = data['Qty']


data['Cost']=data.Commission.map(lambda x: locale.atof(x.strip('$'))) + \
    data.Fees.map(lambda x: locale.atof(x.strip('$')))

fees = sum(data['Cost'])

options = 0
price_paid = 0
price_sold = 0
net = 0
won = 0
lost = 0
complete_trades = 0
avg_win = 0
avg_loss = 0
win_list = []
lost_list = []
win_pct = 0
lose_pct = 0
avg_bet = 0

for i in range(len(buyorsell) - 1, -1, -1):
    #print(options)
    if buyorsell[i] == "Buy To Open":
        options = options + qty_list[i]
        price_paid = price_paid + (qty_list[i] * price_list[i])
        print ("Buy: ", qty_list[i], "at:",price_list[i],"holding:",options)
    else:
        options = options - qty_list[i]
        print ("sold:", qty_list[i], "at:", price_list[i], "holding:",options)
        price_sold = price_sold + (qty_list[i] * price_list[i])
        if options == 0:
            if (price_sold - price_paid) > 0:
                win_pct += (price_sold - price_paid)/price_paid
            else:
                lose_pct += (price_sold - price_paid)/price_paid

            print( "bought", round(price_paid*50,2), "sold:",round(price_sold*50,2), "Net $: ", round((price_sold - price_paid)*50,2), "\t",round((price_sold - price_paid)/price_paid, 2)*100, "%" )
            print()
            net += (price_sold - price_paid)*50
            complete_trades += 1
            avg_bet += price_paid
            if (price_sold - price_paid) > 0:
                won += 1
                avg_win += (price_sold - price_paid)*50
                win_list.append((price_sold - price_paid)*50)
            else:
                lost += 1
                avg_loss += (price_sold - price_paid)*50
                lost_list.append((price_sold - price_paid)*50)
            options = 0
            price_paid = 0
            price_sold = 0


avg_win = avg_win/won
avg_loss = avg_loss/lost
print ('Net Profit:', round(net - fees, 2), "Fees paid:", round(fees,2),"Winrate%:", (won/complete_trades*100), \
       "Avg Win:", avg_win, "Avg Loss:", avg_loss, "Trades:", won+lost)
print ("WinPct:", round(win_pct/won,2)*100, "LosePct:", round(lose_pct/lost, 2)*100, "Avg Bet Size:", avg_bet)
A = lose_pct/lost
B = win_pct/won
bankroll = avg_bet
A = avg_win/bankroll
B = avg_loss/bankroll
W = won/complete_trades
Kelly = W/A - (1 - W)/B
print ("Kelly Bet Percentage:", Kelly )
#If the downside-case loss is less than 100%, as in the scenario above,
# a different Kelly formula is required:
# Kelly % = W/A – (1 – W)/B,
# where:
# W is the win probability,
# B is the profit in the event of a win (20%),
# A is the potential loss (also 20%).

if 1:
    plt.style.use('ggplot')
    #print ( day )
    # create figure and axis objects with subplots()
    fig,ax_all = plt.subplots(2,1) #2,1, gridspec_kw={'height_ratios': [5, 1]})
    ax = ax_all

    plt.autoscale(True)

    ax[0].plot(win_list,'g')
    ax[1].plot(lost_list, 'r')
    plt.show()
    #plt.plot(lost_list,color='r')
    #line2, = ax.plot(lost_list,color='red')

