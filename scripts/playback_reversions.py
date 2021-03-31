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

DATA_PATH = '../processed_data/'
DAILY=True
DAILY_DATA_PATH = '../daily_training/'
file_of_the_day = 0
all_files = os.listdir(DAILY_DATA_PATH)
random.shuffle(all_files)
all_data = pd.read_csv(DATA_PATH + 'allDataCombined.csv')
price_data = pd.read_csv(DATA_PATH + 'priceData.csv')
df = pd.merge(all_data, price_data, on="timestamp")
df['date'] = df['timestamp'].apply(lambda x: parser.parse(x).date())
df['time'] = df['timestamp'].apply(lambda x: parser.parse(x).strftime("%H:%M:%S"))
corr = []
corr_all = []
pnl = defaultdict(list)
index = 0
trades_total = 0
trade_win_pct = 0

def animate(i):
    global index, ax, callback, ys, ys2, ys3, xs
    global deltaNope, deltaPrice, deltaNope2, lastDNope
    threshold_high = 30
    threshold_low  = -60
    h = int(day['Human Time'][index][-8:-6]) - 1
    if h == 0:
        h = 12
    txt = " Profit: {:.2f} "
    prf = callback.unrealized_gain() * 500
    txt = txt.format(prf)
    #y_red = np.array(ys)
    #x_red = np.arange(len(y_red))
    #below_threshold = y_red < threshold_low
    #above_threshold = y_red > threshold_high
    #plt.scatter(x_red[below_threshold], y_red[below_threshold], color='red')
    #plt.scatter(x_red[above_threshold], y_red[above_threshold], color='red')

    ax.set_xlabel(str( h ) + day['Human Time'][index][-6:] + txt,fontsize=14)
    ax.relim()
    ax.autoscale_view()
    ax2.relim()
    #ax2.set_ylim([day['active_underlying_price'][0] - 4,day['active_underlying_price'][0] + 4])
    ax2.autoscale_view()

    lastDNope = deltaNope
    lastDPrice = deltaPrice
    if index > 0:
        deltaNope = day['NOPE_busVolume'][index - 1] - day['NOPE_busVolume'][index]
        deltaPrice = day['active_underlying_price'][index-1] - day['active_underlying_price'][index]
        deltaNope2 = lastDNope - deltaNope
        deltaPrice2 = lastDPrice - deltaPrice
        if deltaNope == 0:
            dPdNope = 0
        else:
            dPdNope = (deltaPrice/deltaNope)
    else:
        dPdNope = 0

    # Add y to list
    ys.append(day['NOPE_busVolume'][index])
    ys2.append(day['active_underlying_price'][index])
    ys3.append(dPdNope)
    xs.append(index)

    # Limit y list to set number of items
    #ys  = ys[-x_len_max:]
    #ys2 = ys2[-x_len_max:]
    #xs  = xs[-x_len_max:]

    # Add threshold markers

    # The x and y data to plot
    # Update line with new Y values
    line1.set_ydata(ys)
    line1.set_xdata(xs)
    line2.set_ydata(ys2)
    line2.set_xdata(xs)
    #line3.set_ydata(ys3)
    #line3.set_xdata(xs)
    index += 1

    if index >= len(day['NOPE_busVolume']):
        index -= 1

    return line1,line2

def backtest_short(day_group, short_entry, short_exit, stop, tolerance = 3):
    values = []
    trade_in_progress = False
    entry_price = None
    exit_price = None
    total_pnl = 0
    for index, row in day_group.iterrows():
        if row['NOPE_busVolume']*100 >= short_entry and not trade_in_progress and row['time'] > '09:45:00' and row['time'] < '15:30:00':
            entry_price = (row['NOPE_busVolume']*100, row['time'], row['active_underlying_price'])
            trade_in_progress = True
        if trade_in_progress and (row['NOPE_busVolume']*100 <= short_exit or row['NOPE_busVolume'] >= stop):
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (entry_price[2] - exit_price[2])
            trade_in_progress = False
            entry_price = None
            exit_price = None
        if row['time'] == '16:00:00':
            if trade_in_progress:
                exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
                values.append((entry_price, exit_price))
                total_pnl = total_pnl + (entry_price[2] - exit_price[2])
                trade_in_progress = False
                entry_price = None
                exit_price = None
            break
    return (values, total_pnl)

def backtest_long(day_group, long_entry, long_exit, stop, tolerance = 3):
    values = []
    trade_in_progress = False
    entry_price = None
    exit_price = None
    total_pnl = 0
    for index, row in day_group.iterrows():
        if row['NOPE_busVolume']*100 <= long_entry and not trade_in_progress and row['time'] > '09:45:00' and row['time'] < '12:30:00':
            entry_price = (row['NOPE_busVolume']*100, row['time'], row['active_underlying_price'])
            trade_in_progress = True
        if trade_in_progress and (row['NOPE_busVolume']*100 >= long_exit or row['NOPE_busVolume'] <= stop):
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (exit_price[2] - entry_price[2])
            trade_in_progress = False
            entry_price = None
            exit_price = None
        #if row['time'] == '16:00:00':
        if row['time'] == '15:20:00':
            if trade_in_progress:
                exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
                values.append((entry_price, exit_price))
                total_pnl = total_pnl + (exit_price[2] - entry_price[2])
                trade_in_progress = False
                entry_price = None
                exit_price = None
            break
    return (values, total_pnl)

plot_pnl = []
nope_pnl = []
if 0:
    for x in range(0,1):
        total_pnl = defaultdict(tuple)
        total_nope_pnl = defaultdict(tuple)
        real_total_pnl = 0
        nope_total_pnl = 0
        plot_spy = []
        for name, group in df.groupby('date'):
            total_pnl[str(name)] = backtest_short(group, 30, 15, -100)
            real_total_pnl = real_total_pnl + total_pnl[str(name)][1]
            plot_pnl.append(real_total_pnl )

            total_nope_pnl[str(name)] = backtest_long(group, -60, -30, -100)
            nope_total_pnl = nope_total_pnl + total_nope_pnl[str(name)][1]
            nope_pnl.append( nope_total_pnl )

            #total_pnl[str(name)] = backtest_short(group, 30, 15, -35)
            #real_total_pnl = real_total_pnl + total_pnl[str(name)][1]
            #print( group['active_underlying_price'] )

        #print(plot_pnl)
        for ii in range(1, 100):
            plot_pnl.append( real_total_pnl )
            nope_pnl.append( nope_total_pnl )
        plt.plot(plot_pnl, color= 'red')
        plt.plot(nope_pnl, color = 'green')
    #plt.plot(df.groupby('date')['active_underlying_price'])
    plt.show()
    quit()
#print(json.dumps(total_pnl, indent=1))
#print(real_total_pnl)




from matplotlib.widgets import Button
colors = itertools.cycle(['red','lightgrey'])

class Options:
    ind = 0
    profit = 0
    put_active = 0
    put_price = 0
    call_active = 0
    call_price = 0

    def buy_put(self, event):
        #print( day['active_underlying_price'][index])
        self.put_price = day['active_underlying_price'][index]
        self.put_active = 1
        bto_put.color = next(colors)

    def buy_call(self, event):
        self.call_price = day['active_underlying_price'][index]
        self.call_active = 1
        bto_call.color = next(colors)

    def option_sold(self, event):
        if self.put_active:
            self.profit += self.put_price - day['active_underlying_price'][index]
            self.put_active = 0
            bto_put.color = next(colors)
            #print("Total Profit: ", self.profit, "Net: ", self.put_price - day['active_underlying_price'][index])
        elif self.call_active:
            self.profit += day['active_underlying_price'][index] - self.call_price
            self.call_active = 0
            bto_call.color = next(colors)
            #print("Total Profit: ", self.profit, "Net: ", day['active_underlying_price'][index] - self.call_price)

    def unrealized_gain(self):
        if self.put_active:
            return self.profit + self.put_price - day['active_underlying_price'][index]
        elif self.call_active:
            return self.profit + day['active_underlying_price'][index] - self.call_price
        else:
            return self.profit

    def load_next_day(self,event):
        global day, DAILY_DATA_PATH, all_files, file_of_the_day, index
        global line1, line2, ax, ax2, xs, ys, ys2
        file_of_the_day += 1
        if file_of_the_day < len(all_files):
            data = pd.read_csv(DAILY_DATA_PATH + all_files[file_of_the_day])
            print (DAILY_DATA_PATH + all_files[file_of_the_day])
            day = data
            day['time'] = day['Human Time'].apply(lambda x: parser.parse(x).strftime("%H:%M"))
            day['NOPE_busVolume'] = day['NOPE']
            day['active_underlying_price'] = day['Stock Price']
            index = 0
            xs  = [0]
            ys  = [day['NOPE_busVolume'][0]]
            ys2 = [day['active_underlying_price'][0]]
            #ax.clear()
            #line1.pop()
            #line2.clear()
                # Create a blank line. We will update the line in animate
            #line1, = ax.plot(xs, ys,color='blue')
            #line2, = ax2.plot(xs, ys2, color='black')

            line1.set_ydata(ys)
            line1.set_xdata(xs)
            line2.set_ydata(ys2)
            line2.set_xdata(xs)
            #print( "new day: " , xs )
            # Create a blank line. We will update the line in animate
        return

if DAILY:
    daily_data = pd.read_csv(DAILY_DATA_PATH + all_files[file_of_the_day])
    print (DAILY_DATA_PATH + all_files[file_of_the_day])

    day = daily_data
    day['time'] = day['Human Time'].apply(lambda x: parser.parse(x).strftime("%H:%M"))
    #print ( day['time'] )
    #day['time'] = day['Human Time']
    day['NOPE_busVolume'] = day['NOPE']
    day['active_underlying_price'] = day['Stock Price']

    #print ( day['time'][0] )

#for name, day in df.groupby('date'):
    plt.style.use('ggplot')
    #print ( day )
    # create figure and axis objects with subplots()
    fig,ax_all = plt.subplots() #2,1, gridspec_kw={'height_ratios': [5, 1]})
    ax = ax_all
    plt.subplots_adjust(bottom=0.2)
    callback = Options()
    axbuyput = plt.axes([0.7 - .5, 0.05, 0.1, 0.075])
    axbuycall = plt.axes([0.8 - .5, 0.05, 0.1, 0.075])
    axsell = plt.axes([0.7 - 0.1, 0.05, 0.1, 0.075])
    axnextday = plt.axes([0.8 - 0.1, 0.05, 0.1, 0.075])
    bto_put = Button(axbuyput, 'PUT')
    bto_call = Button(axbuycall, 'CALL')
    sell_option = Button(axsell, 'SELL')
    next_day = Button(axnextday, 'NEXT DAY')

    bto_put.on_clicked(callback.buy_put)
    bto_call.on_clicked(callback.buy_call)
    sell_option.on_clicked(callback.option_sold)
    next_day.on_clicked(callback.load_next_day)

    index = 0

    # Parameters
    x_len_max = 387      # Max Number of points to display
    y_range = [-90, 90]  # Range of possible Y values to display

    plt.autoscale(True)
    plt.subplots_adjust(bottom=0.2)
    # make a plot
    ax2=ax.twinx()
    ax2.set_ylim(0, 100)
    #
    ax.set_ylabel("NOPE",color="blue",fontsize=14)
    #ax2.set_ylabel("PRICE",color="black",fontsize=14)
    plt.autoscale(True)
    if 0:
        xs  = list(range(0, x_len))
        ys  = [day['NOPE_busVolume'][0]] * x_len
        ys2 = [day['active_underlying_price'][0]] * x_len
    else:
        xs  = [0]
        ys  = [day['NOPE_busVolume'][0]]
        ys2 = [day['active_underlying_price'][0]]
        ys3 = [0]
        lastDNope = 0
        deltaNope = 0
        deltaPrice = 0
        deltaNope2 = lastDNope - deltaNope

    # Create a blank line. We will update the line in animate
    line1, = ax.plot(xs, ys,color='blue')
    line2, = ax2.plot(xs, ys2, color='black')
    #line3, = ax_all[1].plot(xs, ys3)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig,
        animate,
        fargs=(),
        interval=175,
        blit=False)

    plt.get_current_fig_manager().window.state('zoomed')
    plt.show()