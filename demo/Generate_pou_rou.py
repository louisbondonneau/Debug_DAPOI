#!/usr/bin/env python3

import time
import sys
import traceback

from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np

from debug_DAPOI import debug_DAPOI


if __name__ == "__main__":
    debug_obj = debug_DAPOI.Debug_DAPOI(logname='Generate_pou_rou')
    try:
        # ------------------------------Debug Fire service------------------------------
        # debug_obj.generate_POU(verbose=False,
        #                        pou_directory=debug_obj.ini_file.get_pou_new_dir(),
        #                        rou_directory=debug_obj.ini_file.get_rou_new_dir(),
        #                        start_time=Time.now() + TimeDelta(20, format='sec'),
        #                        duration=120)
        debug_obj.generate_nPOU(verbose=False,
                               pou_directory=debug_obj.ini_file.get_pou_new_dir(),
                               rou_directory=debug_obj.ini_file.get_rou_new_dir(),
                               start_time=Time.now() + TimeDelta(60, format='sec'),
                               dt=30,
                               nOBS=10)
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
