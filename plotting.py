import sys
import math
import random
import csv
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import seaborn as sns

#############################

# Reading & Plotting Functions

#############################

# converts file -> (x_coord, y_coord) :: ([float], [float])
def read_transactions(file_name):
    with open(file_name, 'r') as f:
        data = csv.reader(f)
        l = np.array([ x for x in data ])
        f = np.vectorize(np.float)

        x = f(l[:,1])
        y = f(l[:,2])
        return x, y

def read_networths(file_name):
    with open(file_name, 'r') as f:
        data = csv.reader(f)
        l = np.array([ x for x in data ])
        f = np.vectorize(np.float)

        x = f(l[:,1])
        y = f(l[:,2])
        return x, y

def line_plot(x, y):
    _, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_ylim(ymin=0)
    return ax

def plot_networth(times, networth, title=None):
    ax = line_plot(times, networth)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Networth (£)')
    if title != None:
        ax.set_title(title)
    return ax

def plot_transactions(times, prices, title=None):
    ax = line_plot(times, prices)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Price (£)')
    if title != None:
        ax.set_title(title)
    return ax

def save_transactions_plot(file_name, save_to):
    times, prices = read_transactions(file_name)
    plot_transactions(times, prices, title=file_name)
    plt.savefig(save_to)

def save_networth_plot(file_name, save_to):
    times, networth = read_networths(file_name)
    plot_transactions(times, networth, title=file_name)
    plt.savefig(save_to)

def plot_transactions_with_ZIPMM():
    fig, ax = plt.subplots()
    all_transactions = pd.read_csv('transactions/sess0001_transactions.csv', names=['type', 'time', 'price'])
    MM_transactions = pd.read_csv('transactions/sess0001_ZIPMM_transactions.csv')
    sns.set_theme()
    sns.lineplot(data=all_transactions, x="time", y="price", ax=ax)
    sns.scatterplot(data=MM_transactions, x="time", y=[60] * len(MM_transactions), hue='transaction_type', ax=ax)
    plt.show()

# plot_transactions_with_ZIPMM()



def price_plot():
# set up plot
    fig, ax = plt.subplots()
    sns.set_theme()

    # get data
    all_transactions = pd.read_csv('transactions/sess0001_transactions.csv', names=['type', 'time', 'price'])
    MM_transactions = pd.read_csv('transactions/sess0001_ZIPMM_transactions.csv')
    MM_ema = pd.read_csv('ema/sess0001_ZIPMM_ema.csv')
    MM_jobs = pd.read_csv('job/sess0001_ZIPMM_job.csv')
    MM_ltt = pd.read_csv('ltt/sess0001_ZIPMM_ltt.csv')

    # combine data
    concatenated = pd.concat([all_transactions.assign(dataset='all_transactions'),
                              MM_ema.assign(dataset='MM_ema'),
                              MM_ltt.assign(dataset='MM_ltt')
                              ])
    print(concatenated)

    # plotting
    # sns.lineplot(data=concatenated, x="time", y="price", hue="dataset")
    sns.lineplot(data=concatenated, x="time", y="price", ax=ax, hue='dataset').set_title('Transaction and Indicator Prediction Prices')
    # sns.lineplot(data=all_transactions, x="time", y="price", ax=ax)
    # sns.lineplot(data=MM_ema, x="time", y="price", ax=ax)

    palette = sns.color_palette("hls", 2)
    sns.scatterplot(data=MM_transactions, x="time", y=[80] * len(MM_transactions), hue='transaction_type', palette=palette, ax=ax)
    # sns.scatterplot(data=MM_jobs, x="time", y=[80]*len(MM_jobs), hue='new_job', ax=ax)

    plt.show()


def networth_plot():
    # set up plot
    fig, ax = plt.subplots()
    sns.set_theme()

    # get data
    # all_transactions = pd.read_csv('transactions/sess0001_transactions.csv', names=['type', 'time', 'price']) # equilibrium price
    MM_transactions = pd.read_csv('transactions/sess0001_ZIPMM_transactions.csv')
    MM_networth = pd.read_csv('networths/sess0001_ZIPMM_networth.csv')

    print(MM_networth.iloc[-1])

    DIMM_transactions = pd.read_csv('transactions/sess0001_DIMM01_transactions.csv')
    DIMM_networth = pd.read_csv('networths/sess0001_DIMM_networth.csv')

    print(DIMM_networth.iloc[-1])

    # MM_inventory = pd.read_csv('inventory/sess0001_ZIPMM_inventory.csv')
    # MM_ema = pd.read_csv('ema/sess0001_ZIPMM_ema.csv')
    # MM_jobs = pd.read_csv('job_history/sess0001_ZIPMM_job_history.csv')
    # MM_ltt = pd.read_csv('ltt_history/sess0001_ZIPMM_ltt_history.csv')

    # combine data

    concatenated = pd.concat([MM_networth.assign(dataset='MM_networth'),
                              DIMM_networth.assign(dataset='DIMM_networth')
                              ])
    # print(concatenated)

    # plotting
    # sns.lineplot(data=concatenated, x="time", y="price", hue="dataset")
    # sns.lineplot(data=concatenated, x="time", y="price", ax=ax, hue='dataset').set_title('networth')
    sns.lineplot(data=concatenated, x="time", y="networth", ax=ax, hue='dataset').set_title('Net Worth Plot - Shock')

    # sns.lineplot(data=MM_inventory, x="time", y="inventory", ax=ax)

    # sns.lineplot(data=all_transactions, x="time", y="price", ax=ax)
    # sns.lineplot(data=MM_ema, x="time", y="price", ax=ax)

    # sns.scatterplot(data=concatenated, x="time", y=[400] * len(concatenated), hue='transaction_type', ax=ax)
    # sns.scatterplot(data=concatenated, x="time", y=[400] * len(concatenated), hue='transaction_type', palette=palette, ax=ax)

    palette = sns.color_palette("hls", 2)
    sns.scatterplot(data=MM_transactions, x="time", y=[400] * len(MM_transactions), hue='transaction_type', palette=palette, ax=ax)
    # sns.scatterplot(data=DIMM_transactions, x="time", y=[400] * len(DIMM_transactions), hue='transaction_type', palette=palette, ax=ax)

    # sns.scatterplot(data=MM_jobs, x="time", y=[80]*len(MM_jobs), hue='new_job', ax=ax)

    plt.show()




if __name__ == "__main__":

    # price_plot()
    networth_plot()

    # # set up plot
    # fig, ax = plt.subplots()
    # sns.set_theme()



    # # get data
    # # all_transactions = pd.read_csv('transactions/sess0001_transactions.csv', names=['type', 'time', 'price']) # equilibrium price
    # MM_transactions = pd.read_csv('transactions/sess0001_ZIPMM_transactions.csv')
    # MM_networth = pd.read_csv('networths/sess0001_ZIPMM_networth.csv')


    # DIMM_transactions = pd.read_csv('transactions/sess0001_DIMM01_transactions.csv')
    # DIMM_networth = pd.read_csv('networths/sess0001_DIMM_networth.csv')


    # # MM_inventory = pd.read_csv('inventory/sess0001_ZIPMM_inventory.csv')
    # # MM_ema = pd.read_csv('ema/sess0001_ZIPMM_ema.csv')
    # # MM_jobs = pd.read_csv('job_history/sess0001_ZIPMM_job_history.csv')
    # # MM_ltt = pd.read_csv('ltt_history/sess0001_ZIPMM_ltt_history.csv')



    # # combine data

    # concatenated = pd.concat([MM_networth.assign(dataset='MM_networth'),
    #                           DIMM_networth.assign(dataset='DIMM_networth')
    #                           ])
    # print(concatenated)





    # # plotting
    # # sns.lineplot(data=concatenated, x="time", y="price", hue="dataset")
    # # sns.lineplot(data=concatenated, x="time", y="price", ax=ax, hue='dataset').set_title('networth')
    # sns.lineplot(data=concatenated, x="time", y="networth", ax=ax, hue='dataset').set_title('networth')

    # # sns.lineplot(data=MM_inventory, x="time", y="inventory", ax=ax)

    # # sns.lineplot(data=all_transactions, x="time", y="price", ax=ax)
    # # sns.lineplot(data=MM_ema, x="time", y="price", ax=ax)

    # # sns.scatterplot(data=concatenated, x="time", y=[400] * len(concatenated), hue='transaction_type', ax=ax)
    # # sns.scatterplot(data=concatenated, x="time", y=[400] * len(concatenated), hue='transaction_type', palette=palette, ax=ax)



    # sns.scatterplot(data=MM_transactions, x="time", y=[400] * len(MM_transactions), hue='transaction_type', ax=ax)
    # # palette = sns.color_palette("hls", 2)
    # # sns.scatterplot(data=DIMM_transactions, x="time", y=[400] * len(DIMM_transactions), hue='transaction_type', palette=palette, ax=ax)


    # # sns.scatterplot(data=MM_jobs, x="time", y=[80]*len(MM_jobs), hue='new_job', ax=ax)

    # plt.show()
