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

if __name__ == "__main__":

    # set up plot
    fig, ax = plt.subplots()
    sns.set_theme()

    # get data
    all_transactions = pd.read_csv('transactions/sess0001_transactions.csv', names=['type', 'time', 'price'])
    MM_transactions = pd.read_csv('transactions/sess0001_ZIPMM_transactions.csv')
    MM_ema = pd.read_csv('ema/sess0001_ZIPMM_ema.csv')
    MM_jobs = pd.read_csv('job_history/sess0001_ZIPMM_job_history.csv')

    # combine data
    concatenated = pd.concat([all_transactions.assign(dataset='all_transactions'),
                            MM_ema.assign(dataset='MM_ema')])
    print(concatenated)

    # plotting
    # sns.lineplot(data=concatenated, x="time", y="price", hue="dataset")
    sns.lineplot(data=all_transactions, x="time", y="price", ax=ax)
    # sns.lineplot(data=MM_ema, x="time", y="price", ax=ax)
    # sns.scatterplot(data=MM_transactions, x="time", y=[60] * len(MM_transactions), hue='transaction_type', ax=ax)
    sns.scatterplot(data=MM_jobs, x="time", y=[60]*len(MM_jobs), hue='new_job', ax=ax)

    plt.show()
