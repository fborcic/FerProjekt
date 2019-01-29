import math

from constants import *
from base import BuhlmannCompartment, BuhlmannDeco


class SchreinerBuhlmannCompartment(BuhlmannCompartment):
    def __init__(self, halftime, a, b, loading=None):
        super(SchreinerBuhlmannCompartment, self).__init__(halftime, a, b)
        if loading is not None:
            self.p_sat = loading
        else:
            self.p_sat = R_N2*(P_AMB-P_WATER)
        self._schreiner_k = math.log(2)/self.halftime

    def add_sample(self, time, depth):
        last_depth = self.current_depth
        self.current_depth = depth
        self.last_time = self.time_elapsed
        self.time_elapsed = time
        p_abs = last_depth*BAR_PER_METER+P_AMB
        p_alv = R_N2*(p_abs-P_WATER)
        t = (time-self.last_time)/60.
        change_rate = R_N2*(depth-last_depth)*BAR_PER_METER/t
        self.p_sat = (p_alv +
                      change_rate*(t-1/self._schreiner_k) -
                      (p_alv-self.p_sat-change_rate/self._schreiner_k) *
                           math.exp(-self._schreiner_k*t))

    def calculate_ceiling(self):
        return self._psat_to_ceiling(self.p_sat)


class SchreinerBuhlmannDeco(BuhlmannDeco):
    COMPARTMENT_FACTORY = SchreinerBuhlmannCompartment
    COEFFICIENT_SET = ZHL16C_COEFF
    PRESENTABLE_NAME = "Schreiner equation"