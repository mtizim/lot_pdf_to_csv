# Mateusz Ziemła mtizim.xyz
# arg1 - pdf to be processed, full path
# arg2 - directory to save the csv to, full path
# python 2.7
# needs tabula-py, pdftotxt package,
# needs to have a tmp folder and a csv folder in the csv dir
# code mostly written in 2017

from tabula import read_pdf
import math
import re
import pandas as pd
import subprocess
from subprocess import call
import random
import sys


filename = sys.argv[1]
PATH_ = sys.argv[2]
PATH = PATH_
TMP = PATH + "tmp/"
TMP_ = PATH_ + "tmp/"
newfilename = PATH + "csvs/" + filename.split("/")[-1][0:-3] + "csv"
newfilename_ = PATH_ + "csvs/" + filename.split("/")[-1][0:-3] + "csv"
FILEPATH = filename


days_pattern = re.compile(r"^[0-9][0-9]\.\s")
period_pattern = re.compile(r"^Period:")
h_number_pattern = re.compile(r"^H([0-9]|\?)$")
period_to = ""
period_from = ""

month_num_dictionary = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}


def is_correct_date_order(start, end):
    start_hr = int(start[0:2])
    start_min = int(start[3:5])
    start_ampm = start[6:8]
    end_hr = int(end[0:2])
    end_min = int(end[3:5])
    end_ampm = end[6:8]
    if start_ampm == "PM" and end_ampm == "AM":
        return 0
    if start_ampm == "AM" and end_ampm == "PM":
        return 1
    if end_hr < start_hr:
        return 0
    if start_hr < end_hr:
        return 1
    if start_min == end_min:
        return 1
    if start_min > end_min:
        return 0
    if end_min > start_min:
        return 1


def extract_date_period(string):
    day = int(string[0] + string[1])
    # won't work after 2099
    year = int("20" + string[-2] + string[-1])
    monthstring = string[2] + string[3] + string[4]
    month = month_num_dictionary[monthstring]
    return day, month, year


def read_period():
    txtoutput = str(random.randrange(10000000)) + ".txt"
    call("pdftotext " + FILEPATH + " " + TMP + txtoutput, shell=True)
    with open(TMP_ + txtoutput) as file:
        f = file.read().split("\n")
        i = 0
        while not period_pattern.match(f[i]):
            i += 1
        periodline = f[i]
        file.close()
    call("rm " + TMP + txtoutput, shell=True)
    period = periodline.split()
    del period[0]
    del period[1]
    return extract_date_period(period[0]), extract_date_period(period[1])


def stringify(x):
    # nans go into nothings
    if (isinstance(x, float) and math.isnan(x)):
        return ""
    else:
        return str(x)


# DEV FUNCTION
# def print_2d_table(table):
#     for row in table:
#         print strip_row(row)


def strip_row(row):
    newrow = []
    for element in row:
        if not (h_number_pattern.match(element) or element == "" or
           "[" in element or
           "]" in element):
            newrow += element.split()
    return newrow


def four_digit_time_to_standard(time):
    hour = time[0] + time[1]
    if time == "2400":
        return "00:00 AM"
    ampm = "AM" if int(hour) < 12 else "PM"
    hour = str(int(hour) % 12)
    if len(hour) == 1:
        hour = "0" + hour
    minute = time[2] + time[3]
    return "%s:%s %s" % (hour, minute, ampm)


def file_to_table(filepath):
    readtable = read_pdf(filepath,
                         pandas_options={'header': None,
                                         'dtype': str},
                         pages="all",
                         java_options=['-Dwarbler.port=9999', '-Dsun.java2d.cmm=sun.java2d.cmm.kcms.KcmsServiceProvider'])
    readtable = readtable.values
    table = []
    for row in readtable:
        table += [[stringify(element) for element in row]]
    return table


def generate_event(row):
        row = strip_row(row)
        # this is where event names are generated
        start = ""
        end = ""
        name = ""
        if len(row) > 0:
            if len(row) > 6 and row[6] != "":
                name = "Flight %s %s from %s to %s; aboard %s" % (row[0],
                                                                  row[1],
                                                                  row[2],
                                                                  row[5],
                                                                  row[6])
                start = four_digit_time_to_standard(row[3])
                end = four_digit_time_to_standard(row[4])
                # print  start, end, name
                return start, end, name
            elif row[0] == "C/I":
                name = "Check in; city: %s" % row[1]
                start = four_digit_time_to_standard(row[2])
                end = start
                # print  start, end, name
                return start, end, name
            elif row[0] == "C/O":
                name = "Check out; city: %s" % row[2]
                start = four_digit_time_to_standard(row[1])
                end = start
                # print  start, end, name
                return start, end, name
            elif (row[0] == "X" or
                  row[0][0:3] == "OFF"):
                name = "Off"
                name += "; city: %s" % row[1] if len(row) > 1 else ""
                start = "full"
                end = "full"
                # print  start, end, name
                return start, end, name
            elif (row[0][0:7] == "E-LEARN" and len(row) > 1):
                name = "E-learning; city: %s" % row[1]
                start = four_digit_time_to_standard(row[2])
                end = four_digit_time_to_standard(row[3])
                # print  start, end, name
                return start, end, name
            elif (row[0][0:3] == "STB"):
                name = "Standby; type %s in %s" % (row[0], row[1])
                start = four_digit_time_to_standard(row[2])
                end = four_digit_time_to_standard(row[3])
                # print  start, end, name
                return start, end, name
            elif (row[0][0:9] == "SZKOLENIE"):
                name = "Szkolenie"
                start = four_digit_time_to_standard(row[2])
                end = four_digit_time_to_standard(row[3])
                # print  start, end, name
                return start, end, name
            # elif row
        return ["", "", ""]


def table_to_days(table):
    days_table = []
    current_table = []
    # a lot of things going on here
    for index, row in enumerate(table):
        if index + 1 == len(table):
            current_table += [row]
            days_table += [current_table]
            current_table = []
        else:
            current_table += [row]
            next_table = table[index + 1]
            if days_pattern.match(next_table[0]):
                days_table += [current_table]
                current_table = []
    # after this for we got a table of tables of tables
    # the thing is,the main table is split between the days now
    # the code further on generates Day objects with correct dates
    # also it prevents from reading past the specified period
    current_month = int(period_from[1])
    current_year = int(period_from[2])
    prev_day = 0
    for index, day_table in enumerate(days_table):
        current_day = int(day_table[0][0][0] + day_table[0][0][1])
        # it's the next month if we suddenly jump day numbers right
        if index > 0 and current_day - prev_day != 1:
            current_month = current_month + 1
        # same but for the year
        if current_month == 13:
            current_month = 1
            current_year += 1

        days_table[index] = Day(current_day, current_month,
                                current_year, day_table)
        # preventing from reading outside period
        if (current_day == period_to[0] and
            current_month == period_to[1] and
            current_year == period_to[2]):
            days_table[index].del_past_period_string()
            break
        prev_day = current_day
    while isinstance(days_table[-1], list):
        del days_table[-1]
    return days_table


class Day:
    def __init__(self, day, month, year, table):
        self.date = [day, month, year]
        table[0][0] = ""
        self.table = table
        self.events = []

    def gen_events_from_table(self):
        for row in self.table:
            time_start, time_end, name = generate_event(row)
            if name:
                self.add_event(time_start, time_end, name)

    def del_past_period_string(self):
        if self.table[-1][0][0:13] == "The following":
            self.table[-1] = []

    def add_event(self, time_start, time_end, name):
        self.events += [Event(self, time_start, time_end, name)]


class Event:
    # day is an instance of the Day class
    def __init__(self, day, time_start, time_end, name):
        self.day = day
        self.time_start = time_start
        self.time_end = time_end
        self.name = name

    def to_csv(self):
        if self.time_start == "full":
            self.time_start = "00:01 AM"
            self.time_end = "11:59 PM"
            fullday_bool = 1
        else:
            fullday_bool = 0
        if not is_correct_date_order(self.time_start, self.time_end):
            ends_on_next_day = 1
        else:
            ends_on_next_day = 0
        csv_line = self.name + ", "
        csv_line += str(self.day.date[1]) + "/" + str(self.day.date[0]) + "/" + str(self.day.date[2]) + ", "
        csv_line += self.time_start + ", "
        if not ends_on_next_day:
            csv_line += str(self.day.date[1]) + "/" + str(self.day.date[0]) + "/" + str(self.day.date[2]) + ", "
        else:
            csv_line += str(self.day.date[1]) + "/" + str(int(self.day.date[0]) + 1) + "/" + str(self.day.date[2]) + ", "
        csv_line += self.time_end + ", "
        if fullday_bool:
            csv_line += ", TRUE"
        return csv_line + "\n"


def create_csv(table_of_days):
    call("touch " + newfilename, shell=True)
    for day in table_of_days:
        day.gen_events_from_table()
    with open(newfilename_, "w") as file:
        file.write("Subject, Start Date, Start Time, End Date, End Time, Private, All Day Event, Location\n")
        for day in table_of_days:
            for event in day.events:
                file.write(event.to_csv())


period_from, period_to = read_period()
table_of_days = table_to_days(file_to_table(FILEPATH))
create_csv(table_of_days)
print newfilename
