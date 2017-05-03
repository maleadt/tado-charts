#!/usr/bin/env python3

import os
import sys
import datetime
import pymysql
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
from scipy.signal import savgol_filter

import private

from enum import Enum
class Resolution(Enum):
    COARSE = 1
    FINE = 2

def smooth(y, factor=Resolution.FINE):
    if factor == Resolution.COARSE:
        return savgol_filter(y, 75, 1)
    if factor == Resolution.FINE:
        return savgol_filter(y, 31, 2)


def plot(zone, timestamps, values, time_lower, time_upper, name):
    outsideTemperature, setpoint, temperature, humidity, heatingpower = values

    # mask heatingpower==0 for clarity
    heatingpower = np.ma.masked_where(heatingpower == 0, heatingpower)


    # initialize

    fig, ax1 = plt.subplots(figsize=(12,5))


    # temperatures

    ax1.set_xlim([time_lower, time_upper])
    ax1.xaxis.set_major_locator(mdates.HourLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H'))

    ax1.set_ylabel('temperature (°celsius)')
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(1))
    ax1.yaxis.grid(alpha=0.25)

    ax1.plot(timestamps, smooth(outsideTemperature, Resolution.COARSE), label="Outside",
             linestyle="solid", color="gray")

    ax1.plot(timestamps, setpoint, label="Setpoint",
             linestyle="solid", color="lime", alpha=.5)

    ax1.plot(timestamps, smooth(temperature), label="Measured",
             linestyle="solid", color="orangered")

    ax1.legend(loc='lower left', bbox_to_anchor=(0, -0.175, 1, 0), ncol=3,
               fancybox=True, shadow=True)


    # percentages

    ax2 = ax1.twinx()

    ax2.set_xlim([time_lower, time_upper])

    ax2.set_ylabel('percentage')
    ax2.set_ylim([0,100])
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(10))

    p1 = ax2.plot(timestamps, smooth(humidity), label="Humidity",
                  linestyle="solid", color="darkcyan", alpha=.1,)
    ax2.fill_between(timestamps, 0, smooth(humidity), color='darkcyan', alpha=.1)

    p2 = ax2.plot(timestamps, heatingpower, label="Heating power",
                  linestyle="solid", color="orange", alpha=.15)
    ax2.fill_between(timestamps, 0, heatingpower, color='orange', alpha=.15)

    # the fill_between can't be represented directly in the legend,
    # so create proxy agents which don't live in the plot
    p1_proxy = mpatches.Patch(color=p1[0].get_color(), alpha=p1[0].get_alpha(), label=p1[0].get_label())
    p2_proxy = mpatches.Patch(color=p2[0].get_color(), alpha=p2[0].get_alpha(), label=p2[0].get_label())

    ax2.legend(handles=[p1_proxy, p2_proxy],
               loc='lower right', bbox_to_anchor=(0, -0.175, 1, 0), ncol=2,
               fancybox=True, shadow=True)


    # finalize

    now = datetime.datetime.now()
    ax1.annotate('Last update: {}'.format(now.strftime("%H:%M")),
                 fontsize=10, color="gray",
                 xy=(1, 1), xycoords='axes fraction',
                 horizontalalignment='right', verticalalignment='upper')

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15)

    dirname = os.path.dirname(sys.argv[0])
    plt.savefig("{}/{}.png".format(dirname, name))


## main

mysql = pymysql.connect(host=private.mysql_hostname,
                        user=private.mysql_user,
                        password=private.mysql_password,
                        db=private.mysql_db)

time_lower = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
time_upper = time_lower + datetime.timedelta(days=1)

for zone in private.zones:
    with mysql.cursor() as cursor:
        sql = """
            SELECT *
            FROM `{}`
            WHERE (timestamp >= %s and timestamp < %s)
        """.format(zone)
        cursor.execute(sql, (time_lower, time_upper))
        data = cursor.fetchall()

        timestamps = np.asarray(list(map(lambda vals: vals[0], data)))
        def convert(val):
            if val is None:
                # we can't create an array with None, or operations like 'isfinite' break
                return float('NaN')
            else:
                return float(val)
        values = np.asarray(list(map(lambda vals: tuple(map(convert, vals[1:])), data))).T

        # plot daily chart
        plot(zone, timestamps, values, time_lower, time_upper,
             "{:04d}{:02d}{:02d}_{}".format(time_lower.year, time_lower.month, time_lower.day, zone))

mysql.close()
