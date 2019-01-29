import math

import scipy.integrate

from constants import *
from base import BuhlmannCompartment, BuhlmannDeco
from helper_functions import linear_two_points

class DiffeqBuhlmannCompartment(BuhlmannCompartment):
    def __init__(self, halftime, a, b, loading=None):
        super(DiffeqBuhlmannCompartment, self).__init__(halftime, a, b)
        if loading is not None:
            self.p_sat = loading
        else:
            self.p_sat = R_N2*(P_AMB-P_WATER)
        self._k = LOG2/(self.halftime*60)

    def add_sample(self, time, depth):
        last_depth = self.current_depth
        self.current_depth = depth
        last_time = self.time_elapsed
        self.time_elapsed = time
        interval = time-last_time
        depth = linear_two_points((0., last_depth), (interval, depth))
        func = lambda pn, t: self._k*(((depth(t)*BAR_PER_METER+P_AMB)-P_WATER)*R_N2-pn)
        odeint_res = scipy.integrate.odeint(func, self.p_sat, (0, interval))
        self.p_sat = odeint_res[-1, 0]

    def calculate_ceiling(self):
        return self._psat_to_ceiling(self.p_sat)

class DiffeqBuhlmannDeco(BuhlmannDeco):
    COMPARTMENT_FACTORY = DiffeqBuhlmannCompartment
    COEFFICIENT_SET = ZHL16C_COEFF
    PRESENTABLE_NAME = "Differential equation"
