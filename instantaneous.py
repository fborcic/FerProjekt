import math

from constants import *
from base import BuhlmannCompartment, BuhlmannDeco
from helper_functions import linear_two_points

class InstantaneousBuhlmannCompartment(BuhlmannCompartment):
    def __init__(self, halftime, a, b, loading=None, inst_sample_time=10.):
        super(InstantaneousBuhlmannCompartment, self).__init__(halftime, a, b)
        if loading is not None:
            self.p_sat = loading
        else:
            self.p_sat = R_N2*(P_AMB-P_WATER)
        self.inst_sample_time = inst_sample_time
        self._factor = 1-math.exp(-inst_sample_time/(halftime*60.)*LOG2)

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
            p_abs = inst_depth*BAR_PER_METER+P_AMB
            p_alv = R_N2*(p_abs-P_WATER)
            self.p_sat += self._factor*(p_alv-self.p_sat)
            inst_time += self.inst_sample_time

    def calculate_ceiling(self):
        return self._psat_to_ceiling(self.p_sat)

class InstantaneousBuhlmannDeco(BuhlmannDeco):
    COMPARTMENT_FACTORY = InstantaneousBuhlmannCompartment
    COEFFICIENT_SET = ZHL16C_COEFF
    PRESENTABLE_NAME = "Instantaneous model"