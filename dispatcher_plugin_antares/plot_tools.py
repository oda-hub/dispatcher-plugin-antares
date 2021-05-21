from __future__ import absolute_import, division, print_function

from builtins import (open, str, range,
                      object)

from bokeh.layouts import row, widgetbox, gridplot
from bokeh.models import CustomJS, Slider, HoverTool, ColorBar, LinearColorMapper, LabelSet, ColumnDataSource

from bokeh.embed import components
from bokeh.plotting import figure
from matplotlib import pylab as plt
import numpy as np
from astropy.units import Unit


class DataPlot(object):
    def __init__(self):

        self.fig = plt.figure(figsize=(8, 6))
        self.ax = self.fig.subplots(1, 1)

    def add_data_plot(self,
                      x,
                      y,
                      dx=None,
                      dy=None,
                      label=None,
                      color=None,
                      fmt='o',
                      ms=None,
                      mew=None,
                      loglog=True,
                      grid=False):

        # get x,y,dx,dy from SEDdata
        if dx is None:
            dx = np.zeros(len(x))
        else:
            dx = np.fabs(x - dx)

        if dy is None:
            dy = np.zeros(len(y))
        else:
            dy = np.fabs(y - dy)

        line = self.ax.errorbar(x, y, xerr=dx, yerr=dy, fmt=fmt, label=label, ms=ms, mew=mew, uplims=ul)
        if loglog is True:
            self.ax.set_xscale("log", nonposx='clip')
            self.ax.set_yscale("log", nonposy='clip')

        if grid is True:
            self.ax.grid()

        self.ax.legend()

    def add_sed_ul(self, ul_table, label=None, color=None, size=100):
        if label is None:
            label = 'ra=%2.2f, dec=%2.2%f roi=%2.2f' % (ul_table.meta['RA'], ul_table.meta['DEC'], ul_table.meta['ROI'])

        ul_sed = np.zeros(size)
        e_range = np.logspace(-1, 5, 1000) * Unit('GeV')
        pl_fuction = lambda energy, pl_index, norm: np.power(10, energy * pl_index) * 10 ** norm

        for ID, index in enumerate(ul_table['Index'].value):
            ul_sed[ID] = np.max(pl_fuction(e_range, index, ul_table['1GeV_norm'].value))

        self.add_data_plot(x=e_range,
                           y=ul_sed,
                           label=label,
                           color=color)

        self.ax.set_ylabel(e_range.unit)
        self.ax.set_xlabel(ul_table['1GeV_norm'].unit)


class ScatterPlot(object):

    def __init__(self, w, h, x_label=None, y_label=None, x_range=None, y_range=None, title=None, y_axis_type='linear',
                 x_axis_type='linear'):
        hover = HoverTool(tooltips=[("x", "$x"), ("y", "$y")])

        self.fig = figure(title=title, width=w, height=h, x_range=x_range, y_range=y_range,
                          y_axis_type=y_axis_type,
                          x_axis_type=x_axis_type,
                          tools=[hover, 'pan,box_zoom,box_select,wheel_zoom,reset,save,crosshair'])

        if x_label is not None:
            self.fig.xaxis.axis_label = x_label

        if y_label is not None:
            self.fig.yaxis.axis_label = y_label

        self.fig.add_tools(hover)

    def add_errorbar(self, x, y, xerr=None, yerr=None, color='red',
                     point_kwargs={}, error_kwargs={}):

        self.fig.circle(x, y, color=color, **point_kwargs)

        if xerr is not None:
            x_err_x = []
            x_err_y = []
            for px, py, err in zip(x, y, xerr):
                x_err_x.append((px - err, px + err))
                x_err_y.append((py, py))
            self.fig.multi_line(x_err_x, x_err_y, color=color, **error_kwargs)

        if yerr is not None:
            y_err_x = []
            y_err_y = []
            for px, py, err in zip(x, y, yerr):
                y_err_x.append((px, px))
                y_err_y.append((py - err, py + err))
            self.fig.multi_line(y_err_x, y_err_y, color=color, **error_kwargs)

    def add_step_line(self, x, y, legend=None):
        # print('a')
        self.fig.step(x, y, name=legend, mode="center")
        # print('b')

    def add_line(self, x, y, legend=None, color=None):
        self.fig.line(x, y, legend=legend, line_color=color)

    def get_html_draw(self):
        #self.fig.sizing_mode = 'scale_width'
        layout = row(
            self.fig
        )

        #layout.sizing_mode = 'fixed'
        #layout.width = 500

        return components(layout)
