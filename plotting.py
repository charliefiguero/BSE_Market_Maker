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

data = pd.read_csv('networths_csv/sess0001_networth.csv')
print(type(data))
print(data)
# sns.set_theme()
# sns.relplot(data=data, x="Time", y="Networth")
# plt.show()