#!/usr/bin/env python3
import os
import re
import sys
import time
import shutil
import numpy as np
import copy

# time liba
from astropy.time import Time, TimeDelta
from datetime import date, datetime


global DEBUG

DEBUG = True


class Log_class():
    def __init__(self, logname=None):
        time_now = Time.now()
        if logname is None:
            logname = 'Debug_DAPOI'
        self.logname = logname + '_' + time_now.isot.replace('-', '').replace(':', '').replace('T', '_').split('.')[0]
        self.dir = ''  # current dir if error at start
        self.length = 20

    def set_dir(self, directory):
        self.dir = str(directory)

    def __string_formating(self, msg, objet='LOG', timing=True):
        msg = msg.strip('\r').strip('\n').split('\n')
        string = []
        if timing is True:
            time_string = self.__timing_string()
        for imsg in range(len(msg)):
            if timing is True:
                msg[imsg] = time_string + ' ' + msg[imsg]
            string_tmp = "%s: %" + str(self.length - len(objet) + len(msg[imsg])) + "s"
            string.append(string_tmp % (objet, msg[imsg]))
        return string

    def log(self, msg, objet='LOG', timing=True):
        string = self.__string_formating(msg, objet=objet, timing=timing)
        with open(self.dir + self.logname + '.log', 'a') as log_file:
            for istring in string:
                print(istring, file=log_file)
                if(DEBUG):
                    print('LOG: ' + istring)

    def warning(self, msg, objet='WARNING', timing=True):
        string = self.__string_formating(msg, objet=objet, timing=timing)
        with open(self.dir + self.logname + '.warning', 'a') as warning_file:
            for istring in string:
                print(istring, file=warning_file)
                if(DEBUG):
                    print('WAR: ' + istring)

    def error(self, msg, objet='ERROR', timing=True):
        string = self.__string_formating(msg, objet=objet, timing=timing)
        with open(self.dir + self.logname + '.error', 'a') as error_file:
            for istring in string:
                print(istring, file=error_file)
                if(DEBUG):
                    print('ERR: ' + istring)

    def __timing_string(self):
        time_string = datetime.now()
        mili = time_string.strftime("%f")[:3]
        time_string = time_string.strftime("%Y-%m-%d %H:%M:%S.") + mili
        return time_string

    def filter(self, msg, objet='Filter', timing=True):
        msg = msg.strip('\r').strip('\n')
        if (re.search(' e:', msg.lower())) or (re.search('err', msg.lower())):
            self.error(msg, objet=objet, timing=timing)
        elif (re.search(' w:', msg.lower())) or (re.search('warn', msg.lower())):
            self.warning(msg, objet=objet, timing=timing)
        else:
            self.log(msg, objet=objet, timing=timing)

    def __sort_file(self, file):
        log_file = open(file, "r")
        time_list = []
        listed_file = []
        for line in log_file:
            line_tmp =  line.strip('\r').strip('\n')
            listed_file.append(line_tmp)
            if (line_tmp != ''):
                iso_str = line_tmp[22:22+23].replace('/', '-')
                iso_str = np.asarray(iso_str.split(' '))
                try:
                    iso_str = iso_str[(iso_str != '')]
                    if (len(iso_str) >= 2):
                        iso_str = iso_str[0] + ' ' + iso_str[1]
                        time_obj = Time(iso_str, format='iso', scale='utc')
                        time_list.append(time_obj.unix)
                    else:
                        time_list.append(0)
                except Exception as e:
                    self.warning('%s while converting \'%s\' as iso in line \'%s\'' % (e, line_tmp[22:22+23], line_tmp), objet='LOG')
                    time_list.append(0)
            else:
                time_list.append(0)

        sorted_file = []
        log_file.close()

        os.remove(file)
        with open(file, 'a') as log_file:
            for i in np.argsort(time_list):
                print(listed_file[i], file=log_file)

    def sort_log(self):
        self.__sort_file(self.dir + self.logname + '.log')