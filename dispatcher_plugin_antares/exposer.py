__author__ = "Andrea Tramacere, Denys Savchenko"

from . import conf_file
from cdci_data_analysis.analysis.instrument import Instrument

from .antares_dataserver_dispatcher import ANTARESDispatcher
from .antares_queries import ANTARESpectrumQuery, AntaresInstrumentQuery, AntaresSourceQuery

def antares_factory():    
    src_query = AntaresSourceQuery('source_query')
    instr_query = AntaresInstrumentQuery('instrument_query')
    antares_spectrum_query= ANTARESpectrumQuery('antares_spectrum_query')

    query_dictionary = {}
    query_dictionary['antares_spectrum'] = 'antares_spectrum_query'

    return Instrument('antares', asynch=False,
                      data_serve_conf_file=conf_file,
                      src_query=src_query,
                      instrumet_query=instr_query,
                      product_queries_list=[antares_spectrum_query],
                      data_server_query_class=ANTARESDispatcher,
                      query_dictionary=query_dictionary)

instr_factory_list=[antares_factory]
