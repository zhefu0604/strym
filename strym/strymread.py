#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Feb 17, 2020
# About: strymread class to read CAN data from CSV file recorded from `strym` class. Read associated README for full description
# License: MIT License

#   Permission is hereby granted, free of charge, to any person obtaining
#   a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject
#   to the following conditions:

#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
#   ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
#   TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
#   SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#   AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#   OR OTHER DEALINGS IN THE SOFTWARE.

__author__ = 'Rahul Bhadani'
__email__  = 'rahulbhadani@email.arizona.edu'

# For System and OS level task
import sys, getopt

## General Data processing and visualization Import

import struct
import signal
import binascii
import bitstring
import time
import datetime
import serial
import csv
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pandas as pd # Note that this is not commai Panda, but Database Pandas
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import uuid
import scipy.special as sp
import pickle
import os
from os.path import expanduser

import libusb1
import usb1

# cantools import
import cantools
import strym.DBC_Read_Tools as dbc

class strymread:
    '''
    `strymread` reads the logged CAN data from the given CSV file.
    This class provides several utilities functions

    Parameter
    ----------------
    csvfie: `str` The CSV file to be read
    dbcfile: `str` The DBC file which will provide codec for decoding CAN messages
    '''

    def __init__(self, csvfile, dbcfile, **kwargs):
        # CSV File
        self.csvfile = csvfile

        # All CAN messages will be saved as pandas dataframe
        self.dataframe = pd.read_csv(self.csvfile)

        # DBC file that has CAN message codec
        self.dbcfile = dbcfile
        # save the CAN database for later use
        self.candb = cantools.db.load_file(self.dbcfile)

    def _get_ts(self, msg_name, msg_id):
        return dbc.convertData(msg_name, msg_id,  self.dataframe, self.candb)

    def ts_speed(self):
        '''
        Returns
        --------
        Timeseries speed data from the CSV file

        '''
        return self._get_ts('SPEED', 1)

    def ts_long_dist(self, track_id):
        '''
        utility function to return timeseries longitudinal distance from radar traces of particular track id

        Parameters
        -------------
        track_id: `numpy array`

        Returns 
        -----------
        Timeseries longitduinal distance data from the CSV file
        '''
        df_obj = pd.DataFrame()

        for id in track_id:
            if id < 0 or id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj1 =self._get_ts('TRACK_A_'+str(id), 1)
            if df_obj1.empty:
                continue
            df_obj = [df_obj, df_obj1]
            df_obj = pd.concat(df_obj)

        return df_obj



    def ts_lat_dist(self, track_id):
        '''
        utility function to return timeseries lateral distance from radar traces of particular track id

        Parameters
        -------------
        track_id: `numpy array`
        Returns 
        -----------
        Timeseries lateral distance data from the CSV file
        '''
        df_obj = pd.DataFrame()

        for id in track_id:
            if id < 0 or id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj1 =self._get_ts('TRACK_A_'+str(id), 2)
            if df_obj1.empty:
                continue
            df_obj = [df_obj, df_obj1]
            df_obj = pd.concat(df_obj)

        return df_obj

    
    def plt_speed(self):
        '''
        Utility function to plot speed data
        '''
        dbc.plotDBC('SPEED',1,  self.dataframe, self.candb)

def ranalyze(df, title='Timeseries'):
    '''
    A utility  function to analyse rate of a timeseries data

    Parameter
    -------------
    title: `str` a descriptive string for this particular analysis
    '''
    if 'Time' not in df.columns:
        print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
        raise

    print('Analyzing Timestamp and Data Rate of ' + title)
    # Calculate instaneous rate
    diffs = df['Time'].diff()
    diffs = diffs.to_frame()
    diffs = diffs.rename(columns={'Time': 'Time Diff'})
    inst_rate = 1.0/(diffs)
    inst_rate = inst_rate.rename(columns={'Time Diff': 'Inst Rate'})
    df_toconcate = [df, diffs, inst_rate]
    df = pd.concat(df_toconcate, axis=1)
        
    inst_rate = inst_rate[1:] # drop the first row
    diffs = diffs[1:] # drop the first row
    # Calculate few parameters
    mean_rate = np.mean(inst_rate.to_numpy() )
    median_rate = np.median(inst_rate.to_numpy())
    max_rate = np.max(inst_rate.to_numpy())
    min_rate = np.min(inst_rate.to_numpy())
    std_rate = np.std(inst_rate.to_numpy())
    first_quartile = np.percentile(inst_rate.to_numpy(), 25)
    third_quartile = np.percentile(inst_rate.to_numpy(), 75)
    iqr = third_quartile- first_quartile #interquartile range


    print('Interquartile Range of Rate for {} is {} '.format(title, iqr))
    # plot the histogram of rate
    plt.style.use('ggplot')
    plt.rcParams["figure.figsize"] = (12,8)
    params = {'legend.fontsize': 15,
        'legend.handlelength': 2}
    plt.rcParams.update(params)
    plt.rcParams["font.family"] = "Times New Roman"
    fig, axes = plt.subplots(ncols=2, nrows=2)
    ax1, ax2, ax3, ax4 = axes.ravel()
    inst_rate.hist(ax=ax1)
    ax1.minorticks_on()
    ax1.set_title(title+'\n'+'Rate Histogram')

    inst_rate.boxplot(ax=ax2)
    ax2.set_title(title+'\n' + 'Rate Box Plot' + '\n' + 'Mean: ' + str(round(mean_rate,2)) + ', Median:' + str(round(median_rate,2)) + ', Max:' + str(round(max_rate, 2)) + ', Min:' + str(round(min_rate,2)) + ', STD:' + str(round(std_rate,2)) + ', IQR:'+ str(round(iqr,2)))
    
    # plot the time diffs as a function of time.
    ax3.plot(df.iloc[1:]['Time'], diffs['Time Diff'], '.')
    ax3.minorticks_on()
    ax3.set_title(title+'\n'+'Timeseries of Time diffs')

    plt.show()




def plt_ts(df):
    '''
    A utility function to plot a timeseries
    ''' 
    pass