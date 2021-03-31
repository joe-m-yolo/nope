import numpy as np
import pandas as pd
from scipy import stats
from dateutil import parser
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import statistics
import math
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
#all_data = pd.read_csv(DATA_PATH + 'allDataCombined.csv')
all_data = pd.read_csv(DATA_PATH + 'allDataCombinedMarchRemoved.csv')

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

def backtest_short(day_group, short_entry, short_exit, stop, reset_stop, points_to_entry, min_entry_time, \
                   max_entry_time, max_exit_time):
    values = []
    trade_in_progress = False
    entry_price = None
    exit_price = None
    total_pnl = 0
    wait_till_reset_stop = False
    points_seen = 0
    for index, row in day_group.iterrows():

        if not trade_in_progress:
            if row['NOPE_busVolume']*100 >= short_entry and row['time'] > min_entry_time and row['time'] < max_entry_time \
                    and not wait_till_reset_stop:

                points_seen += 1
                if points_to_entry >= points_seen:
                    entry_price = (row['NOPE_busVolume']*100, row['time'], row['active_underlying_price'])
                    trade_in_progress = True
                    points_seen = 0

        if not trade_in_progress:
            if row['NOPE_busVolume']*100 <= reset_stop:
                wait_till_reset_stop = False

        if trade_in_progress and row['NOPE_busVolume'] >= stop:
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (entry_price[2] - exit_price[2])
            trade_in_progress = False
            wait_till_reset_stop = True

        if trade_in_progress and (row['NOPE_busVolume']*100 <= short_exit):
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (entry_price[2] - exit_price[2])
            trade_in_progress = False

        if row['time'] >= max_entry_time:
            if trade_in_progress:
                exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
                values.append((entry_price, exit_price))
                total_pnl = total_pnl + (entry_price[2] - exit_price[2])

            break
    #print (values, total_pnl)
    return values, total_pnl

def backtest_long(day_group, long_entry, long_exit, stop, reset_stop, \
                  points_to_entry, min_entry_time, max_entry_time, max_exit_time, \
                  target_exit_price, stop_exit_price):
    global exit_type
    global exit_win
    global low_nope, low_price
    global high_nope, high_price
    global exit_nope
    global mins
    values = []
    trade_in_progress = False
    entry_price = None
    exit_price = None
    total_pnl = 0
    wait_till_reset_stop = False
    points_seen = 0
    exited_via_price = 0
    exited_via_stop_price = 0
    exited_via_nope_thresh = 0
    exited_via_eod = 0
    max_nope = -9999
    last_active_underlying_price = 999999
    last_nope = 999999
    for index, row in day_group.iterrows():

        if row['NOPE_busVolume']*100 <= long_entry and not trade_in_progress and \
                        row['time'] > min_entry_time and row['time'] < max_entry_time \
                        and not wait_till_reset_stop and row['NOPE_busVolume']*100 < last_nope: #(row['active_underlying_price'] - last_active_underlying_price) >= 0: #(row['active_underlying_price'] - last_active_underlying_price) >= 0:

                points_seen += 1
                if points_to_entry >= points_seen:
                    entry_price = (row['NOPE_busVolume']*100, row['time'], row['active_underlying_price'])
                    entry_time = row['time']

                    if entry_time[3:5] < str(60 - mins):
                        temp_hr = int(entry_time[0:2])
                        temp_min = int(entry_time[3:5]) + mins

                        if temp_min < 10:
                            temp_min_str = '0' + str(temp_min)
                        else:
                            temp_min_str = str(temp_min)

                        if temp_hr == 9:
                            entry_hold = "09:" + temp_min_str + entry_time[5:]
                        else:
                            entry_hold = str(temp_hr) + ":" + temp_min_str + entry_time[5:]
                    else:
                        temp_hr = int(entry_time[0:2]) + 1
                        temp_min = int(entry_time[3:5]) + mins
                        temp_min = temp_min % 60
                        if temp_min < 10:
                            temp_min_str = '0' + str(temp_min)
                        else:
                            temp_min_str = str(temp_min)

                        entry_hold = str(temp_hr) + ":" + temp_min_str + entry_time[5:]
                        #print ( '\t', entry_time, entry_hold )

                    trade_in_progress = True
                    points_seen = 0
                    lowest_nope_seen   = row['NOPE_busVolume']*100
                    highest_nope_seen  = row['NOPE_busVolume']*100
                    lowest_price_seen  = 0
                    highest_price_seen = 0


        # if trade_in_progress:
        #     if (row['active_underlying_price'] - last_active_underlying_price) < 0 \
        #         and ((row['active_underlying_price'] - entry_price[2]) >= 2):
        #
        #             exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
        #             values.append((entry_price, exit_price))
        #             total_pnl = total_pnl + (exit_price[2] - entry_price[2])
        #             trade_in_progress = False
        #             exit_type['momo'] += 1
        #             exit_win['momo'] += exit_price[2] - entry_price[2]

        last_active_underlying_price = row['active_underlying_price']
        last_nope = row['NOPE_busVolume']*100

        if trade_in_progress:
            lowest_nope_seen   = min(row['NOPE_busVolume']*100,lowest_nope_seen)
            highest_nope_seen  = max(row['NOPE_busVolume']*100,highest_nope_seen)
            lowest_price_seen  = min(  row['active_underlying_price'] - entry_price[2],lowest_price_seen)
            highest_price_seen = max(  row['active_underlying_price'] - entry_price[2],highest_price_seen)

            if 0: #row['time'] >= entry_hold:
                if 1: #(row['active_underlying_price'] - entry_price[2]) < 0:
                    #if (row['NOPE_busVolume']*100) < -60:
                    #print (row['active_underlying_price'] - entry_price[2], row['NOPE_busVolume']*100 )
                    exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
                    values.append((entry_price, exit_price))
                    total_pnl = total_pnl + (exit_price[2] - entry_price[2])
                    trade_in_progress = False
                    exit_type['hold'] += 1
                    exit_win['hold'] += exit_price[2] - entry_price[2]

                    if (exit_price[2] - entry_price[2]) > 0:
                        exit_win['win_cnt'] += 1
                        exit_win['win_sum'] += (exit_price[2] - entry_price[2])
                    else:
                        exit_win['loss_sum'] += (exit_price[2] - entry_price[2])
                        exit_win['loss_cnt'] += 1
                    low_nope.append(lowest_nope_seen)
                    low_price.append(lowest_price_seen)
                    high_nope.append(highest_nope_seen)
                    high_price.append(highest_price_seen)
                    exit_nope.append(row['NOPE_busVolume']*100)

        if trade_in_progress:
            if max_nope < row['NOPE_busVolume']*100:
                max_nope = row['NOPE_busVolume']*100

        if not trade_in_progress:
            if row['NOPE_busVolume']*100 >= reset_stop:
                wait_till_reset_stop = False

        if trade_in_progress and ((row['active_underlying_price'] - entry_price[2]) >= target_exit_price):
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (exit_price[2] - entry_price[2])
            trade_in_progress = False
            exit_type['price'] += 1
            exit_win['price'] += exit_price[2] - entry_price[2]
            if (exit_price[2] - entry_price[2]) > 0:
                        exit_win['win_cnt'] += 1
                        exit_win['win_sum'] += (exit_price[2] - entry_price[2])
            else:
                        exit_win['loss_sum'] += (exit_price[2] - entry_price[2])
                        exit_win['loss_cnt'] += 1
            low_nope.append(lowest_nope_seen)
            low_price.append(lowest_price_seen)
            high_nope.append(highest_nope_seen)
            high_price.append(highest_price_seen)
            exit_nope.append(row['NOPE_busVolume']*100)

        if trade_in_progress and ((row['active_underlying_price'] - entry_price[2]) <= stop_exit_price):
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (exit_price[2] - entry_price[2])
            trade_in_progress = False
            #wait_till_reset_stop = True
            exit_type['stop'] += 1
            exit_win['stop'] += exit_price[2] - entry_price[2]
            low_nope.append(lowest_nope_seen)
            low_price.append(lowest_price_seen)
            high_nope.append(highest_nope_seen)
            high_price.append(highest_price_seen)
            exit_nope.append(row['NOPE_busVolume']*100)

        if trade_in_progress and row['NOPE_busVolume']*100 >= long_exit:
            wait_till_reset_stop = True
            exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
            values.append((entry_price, exit_price))
            total_pnl = total_pnl + (exit_price[2] - entry_price[2])
            trade_in_progress = False
            exit_type['nope'] += 1
            exit_win['nope'] += exit_price[2] - entry_price[2]
            low_nope.append(lowest_nope_seen)
            low_price.append(lowest_price_seen)
            high_nope.append(highest_nope_seen)
            high_price.append(highest_price_seen)
            exit_nope.append(row['NOPE_busVolume']*100)
            if (exit_price[2] - entry_price[2]) > 0:
                        exit_win['win_cnt'] += 1
                        exit_win['win_sum'] += (exit_price[2] - entry_price[2])
            else:
                        exit_win['loss_sum'] += (exit_price[2] - entry_price[2])
                        exit_win['loss_cnt'] += 1

        if row['time'] >= max_exit_time:
            if trade_in_progress:
                exit_price = (row['NOPE_busVolume']*100,row['time'],row['active_underlying_price'])
                values.append((entry_price, exit_price))
                total_pnl = total_pnl + (exit_price[2] - entry_price[2])
                exit_type['eod'] += 1
                exit_win['eod'] += exit_price[2] - entry_price[2]
                #if (row['active_underlying_price'] - entry_price[2]) < 0:
                #    print (row['active_underlying_price'] - entry_price[2], row['NOPE_busVolume']*100,max_nope )
                low_nope.append(lowest_nope_seen)
                low_price.append(lowest_price_seen)
                high_nope.append(highest_nope_seen)
                high_price.append(highest_price_seen)
                exit_nope.append(row['NOPE_busVolume']*100)
                print (entry_time,entry_hold,row['time'], max_exit_time)
                if (exit_price[2] - entry_price[2]) > 0:
                        exit_win['win_cnt'] += 1
                        exit_win['win_sum'] += (exit_price[2] - entry_price[2])
                else:
                        exit_win['loss_sum'] += (exit_price[2] - entry_price[2])
                        exit_win['loss_cnt'] += 1
            break

    return values, total_pnl

plot_pnl = []
short_plot = []
long_plot = []
day_name = []
mins = 50

if 1:
    for profile in range(1, 2):
        total_pnl = defaultdict(tuple)
        total_nope_pnl = defaultdict(tuple)
        short_pnl = defaultdict(tuple)
        long_pnl = defaultdict(tuple)
        exit_type = defaultdict(tuple)
        exit_win  = defaultdict(tuple)
        exit_type['price'] = 0
        exit_type['stop'] = 0
        exit_type['nope'] = 0
        exit_type['eod'] = 0
        exit_type['hold'] = 0
        exit_type['momo'] = 0

        exit_win['win_cnt'] = 0
        exit_win['win_sum'] = 0
        exit_win['loss_cnt'] = 0
        exit_win['loss_sum'] = 0

        exit_win['momo'] = 0
        exit_win['eod'] = 0
        exit_win['hold'] = 0
        exit_win['nope'] = 0
        exit_win['stop'] = 0
        exit_win['price'] = 0

        low_nope = []
        high_nope = []
        low_price = []
        high_price = []
        exit_nope = []
        short_total_pnl = 0
        long_total_pnl = 0
        max_profit = -9999999
        plot_spy = []

        for ii in range(1,100):
            plot_pnl.append(0)
            short_plot.append(0)
            long_plot.append(0)

        if profile == 0:
            entry_pt_num = 1
            entry_at_long = -60
            exit_at_long  = -30
            long_exit_price = 999999
            stop_exit_price = -2000
            stop_at_long  = -100
            start_time_long  = '09:45:00'
            stop_time_long_entry = '15:30:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 1:
            entry_pt_num = 1
            threshold = 0
            entry_at_long = -60 + threshold
            exit_at_long  = -30 + threshold
            stop_at_long  = -1000
            long_exit_price = 500000
            stop_exit_price = -1000000
            start_time_long  = '09:35:00'
            stop_time_long_entry = '12:00:00'
            stop_time_long_exit = '16:00:00'
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:35:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        # if profile == 1:
        #     entry_pt_num = 1
        #     entry_at_long = -60
        #     exit_at_long  = 400
        #     stop_at_long  = -100
        #     long_exit_price = 5
        #     stop_exit_price = -100
        #     start_time_long  = '09:45:00'
        #     stop_time_long_entry = '13:00:00'
        #     stop_time_long_exit = '16:00:00'
        #     stop_reset_at = 0
        #     exit_at_short = 15
        #     stop_at_short = -100
        #     start_time_short = '09:45:00'
        #     stop_time_short_entry  = '15:30:00'
        #     stop_time_short_exit = '16:00:00'

        if profile == 2: # best strategy so far, do not tweak
            entry_pt_num = 1
            entry_at_long = -50
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '15:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 3:
            entry_pt_num = 1
            entry_at_long = -40
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:45:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 4:
            entry_pt_num = 1
            entry_at_long = -30
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:45:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 5:
            entry_pt_num = 1
            entry_at_long = -20
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 6:
            entry_pt_num = 1
            entry_at_long = -10
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 7:
            entry_pt_num = 1
            entry_at_long = 0
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '14:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 8:
            entry_pt_num = 1
            entry_at_long = 10
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 9:
            entry_pt_num = 1
            entry_at_long = 20
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 50
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '15:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 10:
            entry_pt_num = 1
            entry_at_long = 30
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '13:00:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        if profile == 11:
            entry_pt_num = 1
            entry_at_long = 40
            exit_at_long  = 400
            stop_at_long  = -100
            long_exit_price = 5
            stop_exit_price = -100
            start_time_long  = '09:35:00'
            stop_time_long_entry = '15:30:00'
            stop_time_long_exit = '16:00:00'
            stop_reset_at = 0
            exit_at_short = 15
            stop_at_short = -100
            start_time_short = '09:45:00'
            stop_time_short_entry  = '15:30:00'
            stop_time_short_exit = '16:00:00'

        for name, group in df.groupby('date'):

            #short_pnl[str(name)] = backtest_short(group, 30, exit_at_short, 100, 0, entry_pt_num, start_time_short, stop_time_short_entry, stop_time_short_exit)
            #short_total_pnl = short_total_pnl + short_pnl[str(name)][1]

            long_pnl[str(name)]  = backtest_long(group, entry_at_long, exit_at_long, -1000, 0, entry_pt_num, \
                                                 start_time_long, stop_time_long_entry, stop_time_long_exit, \
                                                 long_exit_price, -100)
            long_total_pnl = long_total_pnl + long_pnl[str(name)][1]

            plot_pnl.append((short_total_pnl + long_total_pnl))
            short_plot.append(short_total_pnl)
            long_plot.append(long_total_pnl)

        print ( exit_type )
        print ( exit_win )

        total_trials = exit_type['hold'] + exit_type['price'] + exit_type['nope'] + exit_type['eod'] + exit_type['momo']

        win_per = exit_win['win_cnt']/total_trials
        avg_win = exit_win['win_sum']/exit_win['win_cnt']
        avg_lss = exit_win['loss_sum']/exit_win['loss_cnt']
        print ( "Win Percentage:", win_per, "Avg Win:", \
                avg_win, "Avg Loss:", avg_lss)

        max_profit = max(plot_pnl[-1], max_profit)

        print ( "EV of bet:", (win_per)*avg_win - (1 - win_per)*avg_lss )

    plt.plot(plot_pnl, color= 'black')
    plt.plot(short_plot, color = 'red')
    plt.plot(long_plot, color = 'green')
    plt.title("Unit SPY $: " + str(max_profit) )

    plt.legend(["Total PNL", "Short Only PNL", "Long Only PNL"])
    #plt.show()

    plt.figure()
    nope_bins = 100
    nope_hist1 = list(range(int(min(low_nope)) - 10, int(max(high_nope)) + 10, 10))
    price_hist1 = list(range( int(min(low_price)) - 1, int(max(high_price)) + 1, 1))
    nope_hist = nope_hist1 + nope_hist1
    price_hist = price_hist1 + price_hist1
    price_hist.sort()
    nope_hist.sort()

    all_nopes = low_nope + high_nope

    n, bins, patches = plt.hist(x=all_nopes, bins=nope_hist, color='#0504aa',
                            alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xticks(nope_hist1)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('NOPEs after entry -60, Min and Max seen in ' + str(mins) + ' mins after entry')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

    plt.figure()
    n, bins, patches = plt.hist(x=exit_nope, bins=nope_hist, color='#0504aa',
                            alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xticks(nope_hist1)
    plt.xlabel('Exit NOPE Value')
    plt.ylabel('Frequency')
    plt.title('Exit ' + str(mins) + ' mins after entry at -60, NOPE distribution')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

    plt.figure()
    n, bins, patches = plt.hist(x=high_nope, bins=nope_hist, color='#0504aa',
                            alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xticks(nope_hist1)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Max NOPEs after entry -60, ' + str(mins) + ' mins after entry')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

    plt.figure()
    n, bins, patches = plt.hist(x=low_nope, bins=nope_hist, color='#0504aa',
                            alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xticks(nope_hist1)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Min NOPEs after entry -60, ' + str(mins) + ' mins after entry')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)


    plt.figure()
    n, bins, patches = plt.hist(x=(low_price + high_price), bins=price_hist, color='#0504aa',
                            alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xticks(price_hist1)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Prices after entry -60, ' + str(mins) + ' mins after entry')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)


    #
    # n, bins, patches = plt.hist(x=high_nope, bins=nope_hist, color='#0504aa',
    #                         alpha=0.7, rwidth=0.85)
    # plt.grid(axis='y', alpha=0.75)
    # plt.xlabel('Value')
    # plt.ylabel('Frequency')
    # plt.title('Highest NOPE after entry')
    # plt.text(23, 45, r'$\mu=15, b=3$')
    # maxfreq = n.max()
    # #
    # # Set a clean upper y-axis limit.
    # plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.show()

    quit()



