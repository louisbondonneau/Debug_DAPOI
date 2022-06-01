#!/usr/bin/env python3

import time
import sys
import traceback

from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np

from debug_DAPOI import debug_DAPOI

START_CMD = b"START\r\n"

if __name__ == "__main__":
    debug_obj = debug_DAPOI.Debug_DAPOI(logname='Debug_Fire')
    try:
        # ------------------------------Debug Fire service------------------------------
        for Fire_log in debug_obj.ini_file.get_Fire_log():
            debug_obj.methode.tail(Fire_log, refresh=0.1, name='Fire_log', timing=False)
        # debug_obj.generate_nOBS(verbose=False,
        #                        observation_directory=debug_obj.ini_file.get_obs_new_dir(),
        #                        start_time=Time.now() + TimeDelta(20, format='sec'),
        #                        dt=30,
        #                        nOBS=10)

        # debug_obj.simult_Pointage_auto_service()
        pointage_auto_address = debug_obj.ini_file.get_pointage_auto_address()
        debug_obj.methode.listen_tcp(pointage_auto_address, message_expected=[START_CMD], name='Simu_Pointage_auto')
        # debug_obj.methode.send_tcp(debug_obj.ini_file.get_pointage_auto_address(), START_CMD.encode('utf-8'), name='CMD')
        # debug_obj.start_Pointage_auto_service(delay=10)

        # debug_obj.methode.wait()
        time.sleep(24*3600)
    except KeyboardInterrupt:
        debug_obj.log.log("Keyboard interuption", objet='PYTHON', timing=True)
        debug_obj.methode.close()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback_print = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for tb in traceback_print:
            debug_obj.log.error(tb, objet='PYTHON', timing=True)
        debug_obj.methode.close()


    # ------------------------------interesting methodes------------------------------
