#!/usr/bin/env python3

import numpy as np
import datetime
import os, re

from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
import astropy.units as u

from astropy.utils import iers


from debug_DAPOI.log_class import Log_class 

iers.conf.auto_download = False


version = '00.14.00'  # 8 characters
global ANABEAM_POINTING
global HIGHEST_BEAMLET, NANCAY, ZENITH_COORD
global ANABEAM_MIN_DURATION, OBS_MIN_DURATION

ANABEAM_POINTING_START_DELAY = 5  # sec (comparatively to obs start)
ANABEAM_POINTING_STOP_DELAY = 5  # sec (comparatively to obs stop)

ANABEAM_MIN_DURATION = 30
OBS_MIN_DURATION = ANABEAM_MIN_DURATION + ANABEAM_POINTING_START_DELAY + ANABEAM_POINTING_STOP_DELAY

ANABEAM_POINTING = 30  # sec

nbMA = 80

NANCAY = EarthLocation(lat=47.37583 * u.deg, lon=2.1925 * u.deg,
                       height=139 * u.m)
ZENITH_COORD = SkyCoord(alt=90 * u.degree, az=0 * u.degree, frame='altaz')


class Observation:
    def __init__(self, *args, **kwargs):

        try:
            self.log = kwargs['log_obj']
        except KeyError:
            self.log = Log_class()

        self.log.log("Observation initialisation", objet='Gen_pou_rou')

        self.__default_values(args, kwargs)
        self.__check_error()

        # pointing conversion
        self.pointing_altaz = self.pointing.copy().transform_to(AltAz(obstime=self.start_time, location=NANCAY))
        self.pointing_icrs = self.pointing.transform_to('icrs')
        self.pointing_ra = self.pointing_icrs.to_string("hmsdms").split(' ')[0].replace("h", ":").replace("m", ":").replace("s", "")
        self.pointing_dec = self.pointing_icrs.to_string("hmsdms").split(' ')[1].replace("d", ":").replace("m", ":").replace("s", "")

        # start_time conversion and round to 10 sec
        self.conv_round_start_time()

        # file name formating
        self.pouname = ''
        self.rouname = ''
        if (self.pou_directory != 'current'):
            self.pouname = self.pou_directory
        if (self.rou_directory != 'current'):
            self.rouname = self.rou_directory
        # 220512_220512_043327_220512_123337_J_1000.pou
        self.pouname += self.start_date_str + '_' + self.stop_date_str + '_' + self.start_hour_str + '_' + self.start_date_str + '_' + self.stop_hour_str + '_J_1000'
        self.rouname += self.start_date_str + '_' + self.stop_date_str + '_' + self.start_hour_str + '_' + self.start_date_str + '_' + self.stop_hour_str + '_J_1000'
        # self.filename += self.start_time_str + '_' + self.stop_time_str + '_' + self.name

        self.log.log("New observation %s at %s for %d sec" % (os.path.basename(self.pouname), self.start_hour_str, self.duration_ana) , objet='Gen_pou_rou')
        # self.log.log("New observation %s at %s for %d sec" % (os.path.basename(self.rouname), self.start_hour_str, self.duration_ana) , objet='Gen_pou_rou')

    def __default_values(self, args, kwargs):
        try:
            self.verbose = kwargs['verbose']
            if(self.verbose):
                self.log.log("verbose: Verbose is activated", objet='Gen_pou_rou')
        except KeyError:
            self.verbose = False

        try:
            self.title = kwargs['title'].strip('\"')
            if (self.title != ''):
                self.title = '\"' + self.title + '\"'
            if(self.verbose):
                self.log.log("verbose: Title is set to %s" % (self.title), objet='Gen_pou_rou')
        except KeyError:
            self.title = 'title'

        try:
            self.name = kwargs['name']
            if(self.verbose):
                self.log.log("verbose: Name is set to %s" % (self.name), objet='Gen_pou_rou')
        except KeyError:
            self.name = 'name'

        try:
            self.pou_directory = kwargs['pou_directory']
            if(self.verbose):
                self.log.log("verbose: pou_directory is set to %s" % (self.pou_directory), objet='Gen_pou_rou')
        except KeyError:
            self.pou_directory = 'current'

        try:
            self.rou_directory = kwargs['rou_directory']
            if(self.verbose):
                self.log.log("verbose: rou_directory is set to %s" % (self.rou_directory), objet='Gen_pou_rou')
        except KeyError:
            self.rou_directory = 'current'

        try:
            self.target = kwargs['target']
            if(self.verbose):
                self.log.log("verbose: target is set to %s" % (self.target), objet='Gen_pou_rou')
        except KeyError:
            self.target = 'mypointing'

        try:
            self.contactName = kwargs['contactName']
            if(self.verbose):
                self.log.log("verbose: contactName is set to %s" % (self.contactName), objet='Gen_pou_rou')
        except KeyError:
            self.contactName = 'debugeur_name'

        try:
            self.contactEmail = kwargs['contactEmail']
            if(self.verbose):
                self.log.log("verbose: contactEmail is set to %s" % (self.contactEmail), objet='Gen_pou_rou')
        except KeyError:
            self.contactEmail = 'nenufarobs@obs-nancay.fr'

        try:
            self.topic = kwargs['topic']
            if(self.verbose):
                self.log.log("verbose: topic is set to %s" % (self.topic), objet='Gen_pou_rou')
        except KeyError:
            self.topic = 'ES03 PULSARS'

        try:
            self.todo = kwargs['todo']
            if(self.verbose):
                self.log.log("verbose: todo is set to %s" % (self.todo), objet='Gen_pou_rou')
        except KeyError:
            self.todo = 'pulsar'

        try:
            self.optFrq = kwargs['optFrq']
            if(self.verbose):
                self.log.log("verbose: optFrq is set to %d" % (int(self.optFrq)), objet='Gen_pou_rou')
        except KeyError:
            self.optFrq = 20

        try:
            self.diode = kwargs['diode']
            if(self.verbose):
                self.log.log("verbose: diode is set to %s" % (self.diode), objet='Gen_pou_rou')
        except KeyError:
            self.diode = 'calib.cur'

        try:
            self.duration = kwargs['duration']
            if(self.verbose):
                self.log.log("verbose: duration is set to %d sec" % (int(self.duration)), objet='Gen_pou_rou')
        except KeyError:
            self.duration = 30

        try:
            self.trackingtype = kwargs['trackingtype']
            if(self.verbose):
                self.log.log("verbose: trackingtype is set to %s" % (int(self.trackingtype)), objet='Gen_pou_rou')
        except KeyError:
            self.trackingtype = 'tracking'

        try:
            self.madisabled = kwargs['madisabled']
            if(self.verbose):
                self.log.log("verbose: madisabled is set to %s" % ('['+ ', '.join(self.madisabled)+']'), objet='Gen_pou_rou')
        except KeyError:
            self.madisabled = [3, 5]

        try:
            self.start_time = kwargs['start_time']
            if(self.verbose):
                self.log.log("verbose: start_time is set to %s" % self.start_time.isot, objet='Gen_pou_rou')
        except KeyError:
            self.start_time = Time.now() + TimeDelta(15, format='sec')   # time obj (default in 1 min)

        try:
            self.pointing = kwargs['pointing']
            if(self.verbose):
                str_pointing = str(self.pointing.ra) + ' ' + str(self.pointing.dec)
                self.log.log("verbose: pointing is set to %s" % str_pointing, objet='Gen_pou_rou')
        except KeyError:
            self.pointing = SkyCoord(ra=326.46025 * u.degree, dec=-7.8384688 * u.degree)  # ZENITH_COORD

        array_keys = ['malist', 'attlist']
        for key, value in kwargs.items():
            for valide_key in array_keys:
                if (key == valide_key):
                    array_length = len(value)
                    if 'array_length' in locals():
                        if(array_length != len(value)):
                            self.log.error("Input size %d of %s is not compatible with arrray size %d" % (np.size(value), valide_key, array_length), objet='Gen_pou_rou')
                            raise NameError('invalide array configuration')

        if not ('array_length' in locals()):
            array_length = 4

        try:
            self.malist = kwargs['malist']
            if(self.verbose):
                self.log.log("verbose: malist is set to %s" % ('['+ ', '.join(self.malist)+']'), objet='Gen_pou_rou')
        except KeyError:
            self.malist = np.arange(nbMA)

        # Default random values for attlist
        self.attlist = np.random.randint(40, high=64, size=np.size(self.malist))

        # Default random values for antlist
        self.antlist = np.arange(1, 9)

    def __check_error(self):
        # check array param size
        n_error = 0
        if (len(self.malist) != len(self.attlist)):
            self.log.error("arrray size of malist and attlist are not compatible", objet='Gen_pou_rou')
            n_error += 1
        if(n_error >= 1):
            raise NameError('invalide array configuration')

    def conv_round_start_time(self):
        if isinstance(self.start_time, datetime.datetime):  # not instance of astropy Time
            self.start_time = Time(datetime.isoformat(), format='isot', scale='utc')
        elif isinstance(self.start_time, str):
            self.start_time = Time(self.start_time, format='iso', scale='utc')
        self.start_time = Time(self.start_time.unix - (self.start_time.unix % 10), format='unix', scale='utc')
        self.start_time_ana = Time(self.start_time.unix - (self.start_time.unix % 10) + ANABEAM_POINTING_START_DELAY, format='unix', scale='utc')
        self.duration = self.duration - (self.duration % 10)
        self.duration_ana = self.duration - ANABEAM_POINTING_START_DELAY - ANABEAM_POINTING_STOP_DELAY
        if(self.duration < OBS_MIN_DURATION):
            self.duration = OBS_MIN_DURATION
            self.duration_ana = ANABEAM_MIN_DURATION
        self.stop_time = Time(self.start_time.unix + self.duration, format='unix', scale='utc')
        self.stop_time_ana = Time(self.start_time_ana.unix + self.duration_ana, format='unix', scale='utc')
        self.mid_time = Time(self.start_time_ana.unix + self.duration_ana / 2., format='unix', scale='utc')

        # string formating for file name
        self.start_date_str = self.start_time.isot.replace('-', '').replace(':', '').split('T')[0][2:]
        self.stop_date_str = self.stop_time.isot.replace('-', '').replace(':', '').split('T')[0][2:]
        self.start_hour_str = self.start_time.isot.replace('-', '').replace(':', '').split('T')[1].split('.')[0]
        self.stop_hour_str = self.stop_time.isot.replace('-', '').replace(':', '').split('T')[1].split('.')[0]
        self.start_time_str = self.start_time.isot.replace('-', '').replace(':', '').replace('T', '_').split('.')[0]
        self.stop_time_str = self.stop_time.isot.replace('-', '').replace(':', '').replace('T', '_').split('.')[0]

    def generate_pou_file(self):
        self.generate_pou_file_fast()

    def generate_pou_file_fast(self):
        if(self.verbose):
            self.log.log("    generate_pou_file", objet='Gen_pou_rou')
        self.pou_name = self.pouname + '.pou'
        fid = open(self.pou_name, 'w')
        fid.write(''.join(['#                    Source: Jupiter\n',
                  '#                  Méridien: %s\n' % (self.start_time_ana.isot.replace('-', '/').replace('T', ' ')),
                  '#               Déclinaison: -00,9 degrés\n',
                  '#              ier pointage: %s\n' % (self.start_time_ana.isot.replace('-', '/').replace('T', ' ')),
                  '#          dernier pointage: %s\n' % (self.stop_time_ana.isot.replace('-', '/').replace('T', ' ')),
                  '#  Fréquence d\'optimisation: 25 MHz\n',
                  '#            Filtre Terrain:  8-45 MHz\n',
                  '#                            Pas de changement\n',
                  '#    Filtre Labo Sortie RDH: 14 MHz\n',
                  '#                            Pas de changement\n',
                  '#    Filtre Labo Sortie   2: 14 MHz\n',
                  '#                            Pas de changement\n',
                  '#    Filtre Labo Sortie   3: 14 MHz\n',
                  '#                            Pas de changement\n',
                  '#    Filtre Labo Sortie DAM: 14 MHz\n',
                  '#                            Pas de changement\n',
                  '#          Type de pointage: Poursuite\n',
                  '#   Temps entre 2 pointages: 1000 msec (si entrelacé)\n',
                  '#        hh:mm:ss phase_rd rew rns f f f f f at phase_rg rew rns f f f f f at rir\n']))
        #          12/05/22 04:33:32 04737362 000 146 2 3 3 3 3 OF 73626251 000 146 2 3 3 3 3 OF 023
        #          12/05/22 04:33:42 04737362 000 146 2 3 3 3 3 30 73626251 000 146 2 3 3 3 3 30 023
        #          12/05/22 04:33:52 04737362 000 146 2 3 3 3 3 20 73626251 000 146 2 3 3 3 3 20 023
        poufile_source = os.path.dirname(os.path.realpath(__file__)) + '\\poufile.pou'
        timer = self.start_time_ana
        for line in open(poufile_source, 'r'):
            if not re.search('^#', line):
                if (timer < self.stop_time_ana):
                    line = line.strip("\n").strip("\r").strip("\n")
                    timer_str = timer.isot.replace('-', '/').replace('T', ' ').split('.')[0][2:]
                    parameters = ' '.join(line.split(' ')[2:])
                    fid.write("%s %s\n" % (timer_str, parameters))
                    timer += TimeDelta(ANABEAM_POINTING, format='sec')
        fid.close

    def generate_rou_file(self):
        self.rou_name = self.rouname + '.rou'
        fid = open(self.rou_name, 'w')
        if(self.verbose):
            self.log.log("    generate_rou_file", objet='Gen_pou_rou')
        start_date = self.start_time.isot.replace('-', '/').split('T')[0][2:]
        stop_date = self.stop_time.isot.replace('-', '/').split('T')[0][2:]
        start_hour = self.start_time.isot.split('T')[1][:5]
        stop_hour = self.stop_time.isot.split('T')[1][:5]

        fid.write("S %s %s %s %s %s 10 80 1 07:49 0 00:00 0 00:00" % (start_date, start_hour, stop_date, start_hour, stop_hour))
        fid.close
