import math

from constants import *
from base import BuhlmannCompartment, BuhlmannDeco
from helper_functions import linear_two_points


class IntegerBuhlmannCompartment(BuhlmannCompartment):
    def __init__(self, halftime, a, b, loading=None):
        super(IntegerBuhlmannCompartment, self).__init__(halftime, a, b)
        """This uses halftime just to look up the constants. a and b are ignored"""
        self._factor, self._int_a, self._int_b = ZHL16_INT[halftime]
        self._int_p_sat = I_INIT_LOADING

    @staticmethod
    def _apply_factor(factor, pressure):
        ret = (pressure/INVFACT_MULTIPLIER)*factor
        assert ret<pressure
        return ret

    def add_sample(self, time, depth):
        last_depth = self.current_depth
        self.current_depth = depth
        last_time = self.time_elapsed
        self.time_elapsed = time
        interval = time-last_time

        inst_time = 0.
        depth_func = linear_two_points((0., last_depth), (interval, depth)) 
        while inst_time < interval:
            inst_depth = depth_func(inst_time)
            self._process_sample(int((inst_depth*BAR_PER_METER+P_AMB)*PRESSURE_FACTOR))
            inst_time += I_SAMPLING_INTERVAL

    def _process_sample(self, pressure):
        ip_alv = self._apply_factor(IF_N2, pressure-IP_WATER)
        if ip_alv < self._int_p_sat:
            self._int_p_sat -= self._apply_factor(self._factor, (self._int_p_sat-ip_alv))
        else:
            self._int_p_sat += self._apply_factor(self._factor, (ip_alv-self._int_p_sat))

    def calculate_ceiling(self):
        if self._int_p_sat < self._int_a:
            return -1
        return (self._apply_factor(self._int_b, self._int_p_sat-self._int_a)-IP_AMB)/\
                float(PRESSURE_FACTOR)/BAR_PER_METER

class IntegerBuhlmannDeco(BuhlmannDeco):
    COMPARTMENT_FACTORY = IntegerBuhlmannCompartment
    COEFFICIENT_SET = ZHL16C_COEFF
    PRESENTABLE_NAME = "Integer instantaneous model"