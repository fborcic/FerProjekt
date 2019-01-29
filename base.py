import time
import Tkinter as tk

import numpy as np
from matplotlib.figure import Figure
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import ticker

from constants import *

class BuhlmannCompartment(object):
    def __init__(self, halftime, a, b, loading=None):
        self.current_depth = 0
        self.time_elapsed = 0
        self.halftime = halftime
        self.a = a
        self.b = b

    def _psat_to_ceiling(self, p_sat):
        return ((p_sat-self.a)*self.b-P_AMB)/BAR_PER_METER

    def add_sample(self, time, depth):
        raise NotImplementedError

    def calculate_ceiling(self):
        raise NotImplementedError


class CeilingViolationException(Exception):
    pass


class BuhlmannDeco(object):
    COMPARTMENT_FACTORY = BuhlmannCompartment
    COEFFICIENT_SET = []
    PRESENTABLE_NAME = ''
    def __init__(self, profile,
                 ascent_rate=DEFAULT_ASC_RATE,
                 increment=DEFAULT_DECO_INCR,
                 stop_resolution=DEFAULT_STOP_RES):
        self.profile = profile
        self.profile.refresh_deco = self._load_compartments
        self.ascent_rate = ascent_rate
        self.increment = increment
        self.stop_resolution = stop_resolution
        self.decostops = []
        self._load_compartments()

    def _load_compartments(self):
        self.compartments = [self.COMPARTMENT_FACTORY(*coeff) for coeff in self.COEFFICIENT_SET]
        for sample in self.profile:
            if sample == (0,0):
                continue
            self._load_sample(sample)
        self._check_violation()

    def _load_sample(self, sample):
        for compartment in self.compartments:
            compartment.add_sample(*sample)

    def _get_current_sample(self):
        return self.profile[-1]

    def _check_violation(self):
        _, depth = self._get_current_sample()
        ceiling = self.get_ceiling()
        if depth < ceiling:
            raise CeilingViolationException

    def get_ceiling(self):
        return max(comp.calculate_ceiling() for comp in self.compartments)

    def _append_ascent_to_incr_multiple(self):
        cur_time, cur_depth = self._get_current_sample()
        if cur_depth%3 == 0: return
        next_depth = cur_depth - cur_depth%3
        if next_depth < self.get_ceiling():
            return
        next_time = cur_time + 60.*(cur_depth-next_depth)/self.ascent_rate
        self._load_sample((next_time, next_depth))
        self.profile.add_sample(next_time, next_depth)

    def _append_ascent(self):
        cur_time, cur_depth = self._get_current_sample()
        if cur_depth == 0:
            return

        while self.get_ceiling() < cur_depth - self.increment and not cur_depth <= 0:
            next_depth = cur_depth - self.increment
            if next_depth < 0:
                next_depth = 0
            next_time = cur_time + 60.*(cur_depth-next_depth)/self.ascent_rate
            self._load_sample((next_time, next_depth))
            self.profile.add_sample(next_time, next_depth)
            cur_time, cur_depth = next_time, next_depth

    def _append_stop(self):
        cur_time, cur_depth = self._get_current_sample()
        start_time = cur_time
        if cur_depth == 0:
            return

        while self.get_ceiling() >= cur_depth - self.increment:
            next_time = cur_time+self.stop_resolution*60.
            self._load_sample((next_time, cur_depth))
            self.profile.add_sample(next_time, cur_depth)
            cur_time = next_time
        end_time = cur_time
        self.decostops.append((cur_depth, (end_time-start_time)/60.))

    def append_deco(self):
        start = time.time()
        self._append_ascent_to_incr_multiple()
        while self._get_current_sample()[1] > 0:
            self._append_ascent()
            self._append_stop()
        self.timing = time.time()-start

    def report(self):
        out = '------\n'
        out += self.profile.label + ' modeled in %.2f milliseconds\n'%(self.timing*1000)
        out += '\nDECO STOPS:\n'
        for time, depth in self.decostops:
            out += '\t %d minutes at %.1f meters\n'%(depth, time)
        out += '------\n\n'
        return out


class DepthProfile(object):
    def __init__(self, samples=None, label=''):
        self.label = label
        self.notify_deco = lambda: None
        if samples is not None:
            self.times, self.depths = zip(*samples)
        else:
            self.times = [] 
            self.depths = [] 

    def add_sample(self, time, depth):
        self.times = np.append(self.times, time)
        self.depths = np.append(self.depths, depth)
        self.notify_deco()

    def duplicate(self):
        return DepthProfile(zip(self.times, self.depths), label=self.label)

    def __getitem__(self, i):
        return (self.times[i], self.depths[i])


class DepthProfileFigure(object):
    def __init__(self, profiles=[]):
        self.profiles = profiles

    def add_profile(self, profile):
        self.profiles.append(profile)

    def rm_profile(self, desired_profile):
        for index, profile in enumerate(self.profiles):
            if profile is desired_profile:
                del self.profiles[index]

    def prepare(self, *figargs, **figkwargs):
        fig = Figure(*figargs, **figkwargs)
        fig.gca().invert_yaxis()
        subplot = fig.add_subplot(111)
        subplot.set_ylabel('Depth')
        subplot.set_xlabel('Time')

        xfmt = ticker.FuncFormatter(lambda s, _: '%02d:%02d'%(int(s)/60, s%60))
        subplot.xaxis.set_major_formatter(xfmt)

        for profile in self.profiles:
            subplot.plot(profile.times, profile.depths, label=profile.label)
        subplot.legend()
        return fig


class DepthProfileFigureCanvas(tk.Canvas):
    def __init__(self, master, profile_figure):
        tk.Canvas.__init__(self, master)
        self.figure = profile_figure
        self.redraw()

    def redraw(self):
        self.mpl_figure = self.figure.prepare()
        self.fc = FigureCanvas(self.mpl_figure)
        self.fc.draw()
        self.figure_x, self.figure_y, self.figure_w, self.figure_h = self.mpl_figure.bbox.bounds
        self.figure_w, self.figure_h = int(self.figure_w), int(self.figure_h)
        self.configure(width=self.figure_w, height=self.figure_h)
        self.photo = tk.PhotoImage(master=self, width=self.figure_w, height=self.figure_h)
        self.create_image(self.figure_w/2, self.figure_h/2, image=self.photo)
        tkagg.blit(self.photo, self.fc.get_renderer()._renderer, colormode=2)
