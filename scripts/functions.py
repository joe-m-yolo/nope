def animate(i, ys, ys2):
    global index, ax, callback
    h = int(day['Human Time'][index][-8:-6]) - 1
    if h == 0:
        h = 12
    txt = " Profit: {:.2f}"
    txt = txt.format(callback.unrealized_gain())
    ax.set_xlabel(str( h ) + day['Human Time'][index][-6:] + txt,fontsize=14)
    ax.relim()
    ax.autoscale_view()
    ax2.relim()
    #ax2.set_ylim([day['active_underlying_price'][0] - 4,day['active_underlying_price'][0] + 4])
    ax2.autoscale_view()

    # Add y to list
    ys.append(day['NOPE_busVolume'][index])
    ys2.append(day['active_underlying_price'][index])

    # Limit y list to set number of items
    ys = ys[-x_len:]
    ys2 = ys2[-x_len:]

    # Update line with new Y values
    line.set_ydata(ys)
    line2.set_ydata(ys2)
    index += 1

    if index >= len(day['NOPE_busVolume']):
        print ("End Of Data")
        quit()
    return line,line2

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
        print ( x )
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


