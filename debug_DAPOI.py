#!/usr/bin/env python3
import os
import re
import sys
import time
import numpy as np
import copy

# multi threading and multiprocessing
import threading
from multiprocessing import Pool, TimeoutError

# time liba
from astropy.time import Time, TimeDelta
from datetime import date, datetime

import socket

from debug_DAPOI.obs_class import Observation 
from debug_DAPOI.log_class import Log_class 


global INI_FILE, RUN_THREAD, DEBUG

INI_FILE = 'C:\\tools_dev\\NDA_PARAMETERS.INI'
DEBUG = False
RUN_THREAD = True

global START_CMD, ABORT_CMD
global ACQ_MSG, ACQ_MSG
global LISTE_MR_OFF
global MR_OFF, MR_ON, CC_ON

START_CMD = b"START\r\n"
ABORT_CMD = b"STOP\r\n"
ACQ_MSG = b'OK\r\n'
BAD_ACQ_MSG = b"NOK\r\n"
KILL_MSG = 'KILL'.encode('utf-8')

LISTE_MR_ON = b"LISTE_MR_ON\r\n"
LISTE_MR_OFF = b"LISTE_MR_OFF\r\n"
APPLY_ALL = b"APPLY_ALL"
SET_MR = b"SET_MR"
LOAD_MR = b"LOAD_MR"
STATUS_ALL = b"STATUS_ALL"
STATUS_MR = b"STATUS_MR"
#MR_OFF = [ ]
# MR_OFF = [1, 2, 6, 11]  # list of MR OFF
# MR_ON = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]  # list of MR ON
# CC_ON = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]  # concentrator to the corespondding MR

global TCP_BUFFER_SIZE
TCP_BUFFER_SIZE = 1024




class Debug_DAPOI(Observation):
    def __init__(self, *args, **kwargs):
        try:
            self.log = Log_class(logname=kwargs['logname'])
        except KeyError:
            self.log = Log_class()

        # read INI and recevers.conf files
        self.ini_file_path = INI_FILE
        self.ini_file = Read_INI(self.ini_file_path, log_obj=self.log)

        self.methode = Methode(log_obj=self.log)

        # read receivers.conf file (ip and port per receiver)
        self.log.set_dir(self.ini_file.get_log_directory())

    # def __del__(self):
    #    del self.methode
    #    del self.log

    # -----------------------tcp send functions--------------------------

    def start_Pointage_auto_service(self, delay=None, name='TCP_Send'):
        if delay is not None:
            time.sleep(delay)
        address_receiver = self.ini_file.get_pointage_auto_address()
        self.methode.send_tcp(address_receiver, START_CMD, name=name)

    def stop_Pointage_service(self, delay=None, name='TCP_Send'):
        if delay is not None:
            time.sleep(delay)
        address_receiver = self.ini_file.get_pointage_auto_address()
        self.methode.send_tcp(address_receiver, ABORT_CMD, name=name)

    # def send_liste_mr_on(self, delay=None, name='TCP_send'):
    #     if delay is not None:
    #         time.sleep(delay)
    #     listen_service_address = self.ini_file.get_pointage_listen_address()
    #     self.log.log('Sending %s to %s' % (LISTE_MR_ON, "Listen service"), objet=name)
    #     self.methode.send_tcp(listen_service_address, LISTE_MR_ON, verbose=False, name=name)
    #     
    # def send_load_mr(self, delay=None, name='TCP_send'):
    #     if delay is not None:
    #         time.sleep(delay)
    #     listen_service_address = self.ini_file.get_pointage_listen_address()
    #     for iMR in MR_ON:
    #         string = ('LOAD_MR 00Z %.3d 078 056 3 52 2 31 1' % iMR).encode('utf-8') + b'\r\n'
    #         self.log.log('Sending %s to %s' % (string, "Listen service"), objet=name)
    #         self.methode.send_tcp(listen_service_address, string, verbose=False, name=name)
    # def send_set_mr(self, delay=None, name='TCP_send'):
    #     if delay is not None:
    #         time.sleep(delay)
    #     listen_service_address = self.ini_file.get_pointage_listen_address()
    #     for iMR in MR_ON:
    #         string = ('SET_MR 00Z %.3d 078 056 3 52 2 31 1' % iMR).encode('utf-8') + b'\r\n'
    #         self.log.log('Sending %s to %s' % (string, "Listen service"), objet=name)
    #         self.methode.send_tcp(listen_service_address, string, verbose=False, name=name)

    # -----------------------simult dedicated functions--------------------------

    def simult_Fire_service(self):
        # generate_OBS_with_disabled    generate_nOBS_with_disabled
        # TODO verife observation with disabled in current

        # send 'START' to all receivers
        self.start_Pointage_service(name='Simu_Fire')
        self.stop_Pointage_service(name='Simu_Fire')

    def simult_Pointage_auto_service(self):
        # getting address ((ip, port))
        pointage_auto_address = self.ini_file.get_pointage_auto_address()

        # launching listeners
        self.methode.listen_tcp(pointage_auto_address, message_expected=[START_CMD, ABORT_CMD], name='Simu_Pointage_auto')

        # self.send_liste_mr_on(name='Simu_Pointage_auto', delay=1)
        # self.send_apply_all(name='Simu_Pointage_auto', delay=1)
        # self.send_load_mr(name='Simu_Pointage_auto', delay=1)

    def simult_Listen_service(self):
        # getting address ((ip, port))
        listen_service_address = self.ini_file.get_pointage_listen_address()

        # launching listeners
        self.methode.listen_tcp(listen_service_address, message_expected=[LISTE_MR_ON, LISTE_MR_OFF, LOAD_MR, APPLY_ALL, STATUS_MR], name='Simu_Listen')
        time.sleep(0.25)

    # def simult_receiver(self, receiver='undysputed', name='Simu_receiver'):
    #     name = 'Simu_' + str(receiver)
    #     address_receiver = self.receivers_file.get_receiver_address(receiver)
    #     # check IP == '127.0.0.1'
    #     if(address_receiver[0] != '127.0.0.1'):
    #         self.log.warning('Receiver %s is not set with the local ip (%s != 127.0.0.1)' % (receiver, address_receiver[0]), objet=name)
    #     else:
    #         self.methode.listen_tcp(address_receiver, message_expected=[START_CMD, ABORT_CMD], name=name)
    #     time.sleep(0.01)


    # -----------------------observation dedicated functions--------------------------

    def __generate_nPOU_arg_checker(self, *args, **kwargs):
        try:
            pou_directory = str(kwargs['pou_directory'])
        except KeyError:
            self.log.error("missing observation_directory argument", objet='Gen_pou_rou')
        try:
            rou_directory = str(kwargs['rou_directory'])
        except KeyError:
            self.log.error("missing observation_directory argument", objet='Gen_pou_rou')
        try:
            self.nOBS = int(kwargs['nOBS'])
        except KeyError:
            self.log.error('input argument \'nOBS\' is missing in generate_nOBS calling (default: 2)', objet='Gen_pou_rou')
        try:
            self.dt = int(kwargs['dt'])
        except KeyError:
            self.log.warning('input argument \'dt\' is missing in generate_nOBS calling (default: 600 sec)', objet='Gen_pou_rou')

        # check start time
        try:
            self.start_time = kwargs['start_time']
        except KeyError:
            self.log.warning('input argument \'start_time\' is missing in generate_nOBS calling (default: now + 15 sec)', objet='Gen_pou_rou')
            self.start_time = Time.now() + TimeDelta(15, format='sec')

        # check duration vs dt
        try:
            duration = float(kwargs['duration'])
            if(duration > self.dt):
                self.log.error('POU duration > TimeDelta btw observations ', objet='Gen_pou_rou')
        except KeyError:
            duration = 60
            if(duration > self.dt):
                self.log.warning('POU default duration > TimeDelta %s sec btw pointing series' % self.dt , objet='Gen_pou_rou')
                self.log.warning('POU duration set to %d sec' % (self.dt), objet='Gen_pou_rou')
                kwargs['duration'] = self.dt
        return (args, kwargs)

    def generate_POU(self, *args, **kwargs):
        kwargs['log_obj']=self.log
        # self.log.log('1 / 1', objet='Gen_pou_rou')
        obs_obj = Observation(*args, **kwargs)
        obs_obj.generate_pou_file()
        obs_obj.generate_rou_file()
        return obs_obj

    def generate_nPOU(self, *args, **kwargs):
        kwargs['log_obj']=self.log
        obs_obj = []
        args, kwargs = self.__generate_nPOU_arg_checker(*args, **kwargs)
        for iOBS in range(self.nOBS):
            self.log.log('%d / %d' % (iOBS+1, self.nOBS), objet='Gen_pou_rou')
            kwargs['start_time'] = self.start_time + TimeDelta(iOBS * self.dt, format='sec')
            objet = self.generate_POU(*args, **kwargs)
            obs_obj.append(objet)
        return obs_obj

    def __bool_return_YN(self):
        ret = input()
        if (ret == 'Y') or (ret == 'y') or (ret == 'O') or (ret == 'o') or (ret == ''):
            return True
        elif (ret == 'N') or (ret == 'n'):
            return False
        elif (ret == 'Q') or (ret == 'q'):
            print("Exiting")
            exit(0)
            return False
        else:
            print("\'%s\' is not a valid answare pls selecte [y]/[n] or [q]" % (ret))

    def __question(self, string):
        string = str(string) + ' [y]/[n] or [q]'
        print(string)
        ret = self.__bool_return_YN()
        while not (ret):
            print(string)
            ret = self.__bool_return_YN()

class Methode():
    def __init__(self, log_obj=None):
        if (log_obj is None):
            self.log = Log_class()
        else:
            self.log = log_obj

        self.all_thread = []
        self.all_TCP_socket = []
        return

    def wait(self, delay=None):
        for thread_i in self.all_thread:
            #self.log.log("stop "+thread_i.name)
            if (len(thread_i.name.split('_')) > 1):
                if (thread_i.name.split('_')[0] == 'Simu'):
                    thread_i.join()

    def close(self, delay=None):
        if delay is not None:
            h = 10
            while (delay > 0):
                if (h > delay):
                    h = delay
                self.log.log("STOP all thread & TCP socket in %d sec" % int(delay), objet='Debug_DAPOI')
                time.sleep(h)
                delay -= h
            self.log.log("STOP all thread & TCP socket", objet='Debug_DAPOI')
        else:
            self.log.log("STOP all thread & TCP socket", objet='Debug_DAPOI')
        # stop thread but not socket.accept() call
        global RUN_THREAD
        RUN_THREAD = False
        # by design stop for socket
        for thread_i in self.all_thread:
            #self.log.log("stop "+thread_i.name)
            if (len(thread_i.name.split('_')) > 1):
                if (thread_i.name.split('_')[0] == 'Simu'):  # 'tail' 'TCP_listen'
                    self.send_tcp(thread_i.args[0], KILL_MSG)
                    thread_i.join()
        self.log.sort_log()

    def search_new_log(self, search_dir, refresh=1, name=None, timing=True):
        self.check_directory_validity(search_dir)
        self.search_dir = search_dir
        new_thread = Thread(self.search_new_log_core, args=(search_dir,), kwargs={
                            'refresh': refresh, 'name': name, 'timing': timing}, name='sniff_dir')
        new_thread.start()
        self.all_thread.append(new_thread)
        time.sleep(0.25)  # TODO wait on event in Thread

    def search_new_log_core(self, search_dir, refresh=1, name=None, timing=True):
        list_old = os.listdir(search_dir)
        list_new = list_old

        while RUN_THREAD:
            time.sleep(float(refresh))
            if (list_new != list_old):
                list_diff = list(set(list_new) - set(list_old))
                for new_file in list_diff:
                    self.check_file_validity(search_dir + new_file)
                    for line in open(search_dir + new_file, 'r'):
                        self.log.log(line, objet=name, timing=timing)
                list_old = list_new
            else:
                list_new = os.listdir(search_dir)

    ''' Represents a tail command. '''

    def tail(self, tailed_file, refresh=1, name=None, timing=True):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed.
        Arguments:
            s - Number of seconds to wait between each iteration; Defaults to 1. '''

        # self.check_file_validity(tailed_file)
        new_thread = Thread(self.tail_core, args=(refresh, tailed_file), kwargs={'name': name, 'timing': timing}, name='tail')
        new_thread.start()
        self.all_thread.append(new_thread)
        time.sleep(0.25)  # TODO wait on event in Thread

    def tail_core(self, refresh, tailed_file, name=None, timing=True):
        global RUN_THREAD
        try:
            file_exist = False
            first = True
            while RUN_THREAD and not (file_exist):
                try:
                    file_exist = self.check_file_validity(tailed_file)
                except NameError as e:
                    if (first):
                        self.log.log("Waiting for %s" % (tailed_file))
                        first = False
                    time.sleep(0.25)
                    pass
            if file_exist:
                with open(tailed_file) as file_:
                    # Go to the end of file
                    file_.seek(0, 2)
                    while RUN_THREAD:
                        curr_position = file_.tell()
                        line = file_.readline()
                        if not line:
                            file_.seek(curr_position)
                            time.sleep(float(refresh))
                        elif (line.strip( ).strip('\r').strip('\n') == ''):
                            file_.seek(curr_position)
                            time.sleep(float(refresh))
                        else:
                            if name is None:
                                name = 'log_file'
                            self.log.filter(line, objet=name, timing=timing)
            else:
                self.log.error("File %s do not exist" % tailed_file)

        except KeyboardInterrupt:
            self.log.error('KeyboardInterrupt for %s from %s' % (name, tailed_file), objet=name)
            RUN_THREAD = False

    def check_file_validity(self, file_):
        ''' Check whether the a given file exists, readable and is a file '''
        if not os.access(file_, os.F_OK):
            raise NameError("File '%s' does not exist" % (file_))
            return False
        if not os.access(file_, os.R_OK):
            raise NameError("File '%s' not readable" % (file_))
            return False
        if os.path.isdir(file_):
            raise NameError("File '%s' is a directory" % (file_))
            return False
        return True

    def check_directory_validity(self, dir_):
        ''' Check whether the a given file exists, readable and is a file '''
        if not os.access(dir_, os.F_OK):
            raise NameError("Directory '%s' does not exist" % (dir_))
            return False
        if not os.access(dir_, os.R_OK):
            raise NameError("Directory '%s' not readable" % (dir_))
            return False
        if not os.path.isdir(dir_):
            raise NameError("'%s' is not a directory" % (dir_))
            return False
        return True

    #def copyfile(self, file_, target, name='copy_file'):
    #    ''' Check whether the a given file exists, readable and is a file '''
    #    try:
    #        self.check_file_validity(file_)
    #        self.check_directory_validity(os.path.dirname(target))
    #        shutil.copyfile(file_, target)
    #        self.check_file_validity(target)
    #    except NameError as e:
    #        self.log.error('Copy error for %s in %s : %s' % (file_, target, e), name=name)

    def send_tcp(self, server_address, cmd, verbose=True, name='TCP_Send'):
        # Create a TCP/IP socket
        string_address = ('ip:%s port:%d' % (server_address[0], server_address[1]))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.02)

            sock.connect(server_address)

            # Send command
            if (verbose):
                self.log.log('Sending %s to %s' % (str(cmd), string_address), objet=name)

            # Look for the response
            sock.sendall(cmd)
            # sock.sendto(cmd, server_address)
            # print(cmd, server_address)
            # sock.sendto(cmd, server_address)
            confimation_message = sock.recv(1024)
            # self.log.log('Received %s'%confimation_message)
        except socket.timeout as err:
            self.log.error('TimeoutError %s for %s from %s' % (err, cmd, string_address), objet=name)
            confimation_message = ''
        except socket.error as err:
            self.log.error('Socket error %s for %s from %s' % (err, cmd, string_address), objet=name)
            confimation_message = ''
        except Exception as e:
            self.log.error('Error %s for %s from %s' % (str(e), cmd, string_address), objet=name)
            confimation_message = ''

        if (cmd == LISTE_MR_ON) or (cmd == LISTE_MR_OFF) or re.search(LOAD_MR, cmd) or re.search(SET_MR, cmd) or re.search(APPLY_ALL, cmd) or re.search(STATUS_MR, cmd) or re.search(STATUS_ALL, cmd):
            if (len(confimation_message) > 0):
                digit_string = confimation_message.decode('utf-8').strip('\r\n')
                if (digit_string.isdigit()):
                    nb_frame = int(digit_string)
                    for i in range(nb_frame):
                        if (verbose):
                            print("waiting for frame %d / %d " % (i, nb_frame-1))
                        try:
                            recv = sock.recv(1024)
                            self.log.log('Received %s from %s' % (recv, string_address), objet=name)
                        except socket.timeout as err:
                            self.log.error('TimeoutError %s for %s[%d] from %s' % (err, cmd, i, string_address), objet=name)
                        except socket.error as err:
                            self.log.error('Socket error %s for %s[%d] from %s' % (err, cmd, i, string_address), objet=name)
                else:
                    self.log.warning('Can\'t undestand %s from %s as a digit' % (confimation_message, string_address), objet=name)
            else:
                self.log.log('The nb of frame was not received from %s' % (string_address), objet=name)
                nb_frame = 0
        elif len(confimation_message) > 0:
            if (confimation_message.upper() == ACQ_MSG):
                self.log.log('Received acknowledgement of receipt from %s' % (string_address), objet=name)
            elif (confimation_message.upper() == BAD_ACQ_MSG):
                self.log.warning('Received a \'non OK\' acknowledgement of receipt from %s' % (string_address), objet=name)
            else:
                self.log.warning('Can\'t undestand acknowledgement of receipt %s from %s' % (confimation_message, string_address), objet=name)
        else:
            self.log.warning('No Acknowledgement of reception for %s from %s' % (cmd, string_address), objet=name)
            sock.close()
            return 0
        sock.close()
        return 1

    def listen_tcp(self, server_address, message_expected=[], name='TCP_listen'):
        #new_thread = mp.Process(target=self.listen_core, args=(server_address, message_expected))
        # new_thread.start()
        new_thread = Thread(self.listen_core, args=(server_address,), kwargs={'message_expected': message_expected, 'name': name}, name=name)
        new_thread.start()
        self.all_thread.append(new_thread)
        time.sleep(0.25)  # TODO wait on event in Thread

    def listen_core(self, server_address, message_expected=[], name='TCP_listen'):
        # Create a TCP/IP socket
        global RUN_THREAD
        if(message_expected is str):
            message_expected = [message_expected]
        string_ip_port = ("ip:%s port:%d" % (server_address[0], server_address[1]))
        if (DEBUG):
            self.log.log("Launch on %s" % (string_ip_port), objet=name)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(server_address)
            sock.listen(1000)
            self.log.log("Bind on %s" % (string_ip_port), objet=name)
        except Exception as err:
            self.log.error('TCP configuration error: %s' % str(err), objet=name)
            RUN_THREAD = False

        self.all_TCP_socket.append(sock)
        while RUN_THREAD:
            try:
                client, adresseClient = sock.accept()
                message = client.recv(1024).upper()
                if (DEBUG):
                    self.log.log(str(message), objet=name)
            except Exception as err:
                self.log.error('error : %s' % str(err), objet=name)
                RUN_THREAD = False
                message = None

            if(message is not None):
                # print(message_expected)
                exp = False
                for message_exp in message_expected:
                    if re.search(message_exp, message):
                        exp = True
                if (exp):
                    for message_exp in message_expected:
                        if re.search(message_exp, message):
                            self.log.log('Received %s on %s' % (message, string_ip_port), objet=name)
                            if (message == START_CMD):
                                self.__reply_START_CMD(client, name=name)
                            else:
                                self.log.error('This error 755 in debug_DAPOI.py should never append')
                elif (message == ABORT_CMD):
                    self.log.log('Received STOP on %s' % (string_ip_port), objet=name)
                    try:
                        client.send(ACQ_MSG)
                    except Exception as err:
                        self.log.error('error while sending ACQ_MSG:  %s' % str(err), objet=name)
                    sock.close()
                    return
                elif (message == KILL_MSG):
                    self.log.log('KILL received on %s' % (string_ip_port), objet=name)
                    try:
                        client.send(ACQ_MSG)
                    except Exception as err:
                        self.log.error('error while sending ACQ_MSG:  %s' % str(err), objet=name)
                    sock.close()
                    return
                else:
                    self.log.warning('Unexpected message: %s on %s' % (message, string_ip_port), objet=name)
                    try:
                        client.send(BAD_ACQ_MSG)
                    except Exception as err:
                        self.log.error('error while sending BAD_ACQ_MSG:  %s' % str(err), objet=name)

    def __reply_START_CMD(self, client, name='TCP_reply'):
        self.log.log('Reply %s to START' % (ACQ_MSG), objet=name)
        try:
            client.send(ACQ_MSG)
        except Exception as err:
            self.log.error('error while sending ACQ_MSG:  %s' % str(err), objet=name)


class Read_INI():
    def __init__(self, ini_file, log_obj=None):
        if log_obj is None:
            self.log = Log_class()
        else:
            self.log = log_obj
        self.methode = Methode(log_obj=self.log)
        self.methode.check_file_validity(ini_file)
        self.ini_file = ini_file
        self.dico = {}
        ini_file_obj = open(self.ini_file, "r")
        for line in ini_file_obj:
            if not re.search('^;', line) and not re.search('^\n', line) and not re.search('^\t\n', line):
                # print(line.strip('\n').strip('\t').strip(' '))
                if re.search('^\[', line):
                    last_sector = line.strip('\n').strip('\t').strip(' ').strip('[').rstrip(']')
                    self.dico[last_sector] = {}
                elif re.search("=", line):
                    line = line.strip('\n').strip('\t').strip(' ').split('=')
                    obj = line[0].strip(' ')
                    result = line[1].strip(' ').strip('\'')
                    self.dico[last_sector][obj] = result
                else:
                    self.log.error("do not understand :\"" + line + '\"', objet='Read_INI')
        ini_file_obj.close()

    def get_config(self, sector, obj):  # dico['MR']['LOG_FIRE']
        '''  get an object from INI_FILE
        Arguments:
            object = PREFIX PREFIX_DATA LOG_FIRE IP PORT
            sector = PATH LOG BACKEND MR POINTAGE_AUTO_SERVICE
                     BACKEND_AUTO_SERVICE POINTAGE_LISTEN_SERVICE'''
        return self.dico[sector][obj]

    def get_Daily_dir(self):
        return self.get_config('HOST', 'DATADAM_IP_PRIVE') + self.get_config('PATH', 'DATADAM_POINTAGE_WEB') + self.get_config('DAILY', 'LOG')

    def get_Fire_log(self):
        file = 'nda_pointage_fire.log'
        time_string = datetime.now()
        time_string = time_string.strftime("%Y%m%d") + '_'
        return [self.get_Daily_dir() + file, self.get_Daily_dir() + time_string + file]

    def get_Pointage_auto_log(self):
        file = str(date.today()) + '_Pointage_auto.log'
        return self.get_config('PATH', 'PREFIX') + self.get_config('MR', 'LOG_POINTAGE_AUTO') + file

    def get_Pointage_log(self):
        time_string = datetime.now()
        time_string = time_string.strftime("%Y%m%d")
        file = time_string + '_pointage.log'
        return self.get_config('PATH', 'PREFIX') + self.get_config('POINTAGE_AUTO_SERVICE', 'PATH_POI') + file

    def get_Listen_log(self):
        time_string = datetime.now()
        time_string = time_string.strftime("%Y%m%d")
        file = time_string + '_natif.log'
        return self.get_config('PATH', 'PREFIX') + self.get_config('POINTAGE_LISTEN_SERVICE', 'PATH_NATIF_LOG') + file

    def get_obs_current_dir(self):
        return self.get_config('HOST', 'DATADAM_IP_PRIVE') + self.get_config('PATH', 'DATADAM_POINTAGE_WEB') + self.get_config('POINTAGE', 'CURRENT')

    def get_pou_new_dir(self):
        return self.get_config('HOST', 'DATADAM_IP_PRIVE') + self.get_config('PATH', 'DATADAM_POINTAGE_WEB') + self.get_config('POINTAGE', 'NEW')

    def get_rou_new_dir(self):
        return self.get_config('HOST', 'DATADAM_IP_PRIVE') + self.get_config('PATH', 'DATADAM_ROUTINE_WEB') + self.get_config('POINTAGE', 'NEW')

    def get_obs_rejected_dir(self):
        return self.get_config('HOST', 'DATADAM_IP_PRIVE') + self.get_config('PATH', 'DATADAM_POINTAGE_WEB') + self.get_config('POINTAGE', 'REJECTED')

    def get_pointage_listen_address(self):
        IP = self.get_config('POINTAGE_LISTEN', 'IP')
        port = int(self.get_config('POINTAGE_LISTEN', 'LISTEN_PORT'))
        return ((IP, port))

    def get_pointage_auto_address(self):
        IP = self.get_config('POINTAGE_AUTO', 'IP')
        port = int(self.get_config('POINTAGE_AUTO', 'PORT'))
        return ((IP, port))

    def get_log_directory(self):
        directory = self.get_Daily_dir() + "Debug_DAPOI\\"
        self.methode.check_directory_validity(directory)
        return directory


class Thread (threading.Thread):
    def __init__(self, func, args=((),), kwargs={}, name=None):
        threading.Thread.__init__(self)  # init mother class
        self.func2thread = func
        self.args = args
        self.kwargs = kwargs
        self.name = name

    def run(self):
        self.func2thread(*self.args, **self.kwargs)


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR
