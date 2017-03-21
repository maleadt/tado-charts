#!/usr/bin/env python3

import csv
import pytz
import datetime
import dateutil.parser
import numpy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches

local_timezone = 'Europe/Brussels'
matplotlib.rcParams['timezone'] = local_timezone

def parse(zone):
    timestamps = []
    values = []

    csv_reader = csv.reader(open(zone + ".csv"))
    for line in csv_reader:
        timestamp = pytz.utc.localize(dateutil.parser.parse(line.pop(0)))
        timestamps.append(timestamp)
        for i in range(len(line)):
            if i >= len(values):
                values.append([])
            values[i].append(float(line[i]))

    return timestamps, values

def plot(zone, timestamps, values, time_lower, time_upper, name):
    # mask NaNs and decode values
    for i in range(len(values)):
        values[i] = numpy.ma.masked_where(numpy.isnan(values[i]), values[i])
    outsideTemperature, setpoint, temperature, humidity, heatingpower = values

    fig, ax1 = plt.subplots(figsize=(15,7))


    # temperatures

    ax1.set_ylabel('temperature (celsius)')
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(1))
    ax1.yaxis.grid(alpha=0.25)

    ax1.set_xlim([time_lower, time_upper])
    ax1.xaxis.set_major_locator(mdates.HourLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    ax1.plot(timestamps, outsideTemperature, 'y-', label="Outside")

    ax1.plot(timestamps, setpoint, 'g-', alpha=.5, label="Requested")

    ax1.plot(timestamps, temperature, 'r-', label="Measured")

    ax1.legend(loc='lower left', bbox_to_anchor=(0, -0.11, 1, 0), ncol=3,
               fancybox=True, shadow=True)


    # percentages

    ax2 = ax1.twinx()

    ax2.set_ylabel('percentage')
    ax2.set_ylim([0,100])
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(10))

    ax2.set_xlim([time_lower, time_upper])
    ax2.xaxis.set_major_locator(mdates.HourLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    p1 = ax2.plot(timestamps, humidity, 'b-', alpha=.1, label="Humidity")
    ax2.fill_between(timestamps, 0, humidity, color='b', alpha=.1)

    p2 = ax2.plot(timestamps, heatingpower, 'r-', alpha=.15, label="Heating power")
    ax2.fill_between(timestamps, 0, heatingpower, color='r', alpha=.15)

    # the fill_between can't be represented directly in the legend,
    # so create proxy agents which don't live in the plot
    p1_proxy = mpatches.Patch(color=p1[0].get_color(), alpha=p1[0].get_alpha(), label=p1[0].get_label())
    p2_proxy = mpatches.Patch(color=p2[0].get_color(), alpha=p2[0].get_alpha(), label=p2[0].get_label())

    ax2.legend(handles=[p1_proxy, p2_proxy],
               loc='lower right', bbox_to_anchor=(0, -0.11, 1, 0), ncol=2,
               fancybox=True, shadow=True)


    # finalize
    plt.title(zone, fontsize=26)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.1)
    plt.savefig(name + '.png')


for zone in ["Living", "Bureau", "Badkamer"]:
    timestamps, values = parse(zone)

    tz = pytz.timezone(local_timezone)
    start = timestamps[0]
    end = timestamps[-1]

    # plot daily chart
    time_lower = tz.normalize(end).replace(hour=0, minute=0, second=0, microsecond=0)
    time_upper = time_lower + datetime.timedelta(days=1)
    plot(zone, timestamps, values, time_lower, time_upper,
         "{:04d}{:02d}{:02d}_{}".format(time_lower.year, time_lower.month, time_lower.day, zone))
