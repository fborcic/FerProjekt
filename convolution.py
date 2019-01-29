import math

import numpy as np
import scipy.signal

from constants import *
from base import BuhlmannCompartment, BuhlmannDeco

class ConvolutionBuhlmannCompartment(BuhlmannCompartment):
    def __init__(self, halftime, a, b, loading=None):
        super(ConvolutionBuhlmannCompartment, self).__init__(halftime, a, b)
        self._state = 341.9
        self.sample_queue = []
        self._k = LOG2/(halftime*60)

    def add_sample(self, time, depth):
        self.sample_queue.append((time, depth))

    def calculate_ceiling(self):
        if not self.sample_queue:
            return self._psat_to_ceiling(self.p_sat)
        times, depths = zip(*self.sample_queue)
        self.sample_queue = []
        last_time = self.time_elapsed
        self.time_elapsed = times[-1]
        last_depth = self.current_depth
        self.current_depth = depths[-1]

        times = np.array((last_time,)+times, dtype=np.float64)-last_time
        pressures = R_N2*(np.array((last_depth,)+depths, dtype=np.float64)*BAR_PER_METER+P_AMB-P_WATER)
        simres = scipy.signal.lsim(([],[-self._k],self._k), pressures, times, self._state)
        self.p_sat = simres[1][-1]
        self._state = simres[2][-1]
        return self._psat_to_ceiling(self.p_sat)


class ConvolutionBuhlmannDeco(BuhlmannDeco):
    COMPARTMENT_FACTORY = ConvolutionBuhlmannCompartment
    COEFFICIENT_SET = ZHL16C_COEFF
    PRESENTABLE_NAME = "LTI system model"
