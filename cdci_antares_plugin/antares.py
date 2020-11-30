

from __future__ import absolute_import, division, print_function

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy

# Dependencies
# eg numpy
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f


from cdci_antares_plugin import conf_file, conf_dir

from cdci_data_analysis.analysis.queries import *
from cdci_data_analysis.analysis.instrument import Instrument
from cdci_data_analysis.analysis.parameters import *

from .antares_dataserver_dispatcher import ANTARESDispatcher

from .antares_table_query import ANTARESTableQuery,ANTARESpectrumQuery


def common_instr_query():
   # not exposed to frontend
   # TODO make a special class
   # max_pointings=Integer(value=50,name='max_pointings')

    #E1_keV = SpectralBoundary(value=0., E_units='keV', name='E1_keV')
    #E2_keV = SpectralBoundary(value=10000., E_units='keV', name='E2_keV')
    #spec_window = ParameterRange(E1_keV, E2_keV, 'spec_window')
    #instr_query_pars = [spec_window]

    radius = Angle(value=5.0, units='deg', name='radius')
    use_internal_resolver= Parameter(value='False',name='use_internal_resolver',allowed_values=['False','True'])
    instr_query_pars = [radius,use_internal_resolver]

    return instr_query_pars


def antares_factory():
    print('--> ANTARES Factory')
    src_query = SourceQuery('src_query')

    instr_query_pars = common_instr_query()

    instr_query = InstrumentQuery(name=' ',
                                  extra_parameters_list=instr_query_pars,
                                  input_prod_list_name=None,
                                  input_prod_value=None,
                                  catalog=None,
                                  catalog_name='user_catalog')

    antares_spectrum_query= ANTARESpectrumQuery('antares_spectrum_query')


    query_dictionary = {}
    query_dictionary['antares_spectrum'] = 'antares_spectrum_query'

    # query_dictionary['update_image'] = 'update_image'

    print('--> conf_file', conf_file)
    print('--> conf_dir', conf_dir)

    return Instrument('magic', asynch=False,
                      data_serve_conf_file=conf_file,
                      src_query=src_query,
                      instrumet_query=instr_query,
                      product_queries_list=[antares_table_query,antares_spectrum_query],
                      data_server_query_class=ANTARESDispatcher,
                      query_dictionary=query_dictionary)

