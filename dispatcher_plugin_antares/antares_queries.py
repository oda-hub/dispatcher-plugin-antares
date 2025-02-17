__author__ = "Andrea Tramacere, Denys Savchenko"

import os

import  json
import pathlib
import numpy as np
from astropy.io import ascii
from astropy.units import Unit

from cdci_data_analysis.analysis.queries import ProductQuery, SourceQuery, InstrumentQuery
from cdci_data_analysis.analysis.products import BaseQueryProduct,QueryOutput, QueryProductList
from cdci_data_analysis.analysis.parameters import Angle, ParameterTuple, String, Float 
from oda_api.data_products import  ODAAstropyTable

from .antares_dataserver_dispatcher import ANTARESDispatcher,ANTARESAnalysisException
from cdci_data_analysis.analysis.plot_tools import  ScatterPlot

class AntaresInstrumentQuery(InstrumentQuery):
    def __init__(self, name):
        super().__init__(name)
        self._parameters_list = []
        self._build_par_dictionary()
        
class AntaresSourceQuery(SourceQuery):
    def __init__(self, name):
        RA = Angle(value=265.97845833, units='deg', name='RA')
        DEC = Angle(value=-29.74516667, units='deg', name='DEC', min_value=-80, max_value=50)

        sky_coords = ParameterTuple([RA, DEC], 'sky_coords')

        try:
            token = String(name_format='str', name='token', value=None, is_optional=True)
        except TypeError:
            token = String(name_format='str', name='token', value=None)

        parameters_list=[sky_coords, token]
        super(SourceQuery, self).__init__(name, parameters_list)

class ANTARESpectrumQuery(ProductQuery):

    def __init__(self, name):
        radius = Angle(value=2.5, units='deg', name='radius', min_value=0.1, max_value=2.5)
        index_min = Float(value=1.5,  name='index_min', min_value = 1.5, max_value=3.0)
        index_max = Float(value=3.0,  name='index_max', min_value = 1.5, max_value=3.0)

        super(ANTARESpectrumQuery, self).__init__(name, parameters_list=[radius, index_min, index_max])
        self.product_type='antares_spectrum'

    def build_product_list(self, instrument, res, out_dir, prod_prefix='',api=False):
        prod_list = ANTARESTable.build_from_res(res, out_dir=out_dir)
        return prod_list

    def get_data_server_query(self, instrument, config=None):

        RA = instrument.get_par_by_name('RA').value
        DEC = instrument.get_par_by_name('DEC').value
        ROI = instrument.get_par_by_name('radius').value

        index_min=instrument.get_par_by_name('index_min').value
        index_max=instrument.get_par_by_name('index_max').value

        param_dict=self.set_instr_dictionaries(ra=RA,
                                               dec=DEC,
                                               roi=ROI,
                                               index_min=index_min,
                                               index_max=index_max)

        q = ANTARESDispatcher(instrument=instrument,config=config,param_dict=param_dict,task='api/v1.0/antares/get-ul-table')

        return q

    def set_instr_dictionaries(self,
                               ra=None,
                               dec=None,
                               roi=None,
                               index_min=1.5,
                               index_max=3.0):

        return  dict(ra=ra,
                     dec=dec,
                     roi=roi,
                     index_min=index_min,
                     index_max=index_max,
                     get_products=True)


    def process_product_method(self, instrument, prod_list,api=False,config=None):

        
        query_prod = prod_list.prod_list[0]
        query_prod.write()
        
        query_prod_1 = prod_list.prod_list[1]
        query_prod_1.write()


        plot_dict = {}
        plot_dict['image'] = query_prod.get_html_draw()
        plot_dict['header_text'] = ''
        plot_dict['table_text'] = ''
        plot_dict['footer_text'] = ''

        _n=query_prod.name+'_%s'%query_prod.file_path.name
        _s = pathlib.PurePosixPath(_n).suffix
        _n=_n.replace(_s,'')
        _names = _n
        _table_path = str(query_prod.file_path.name)
        _html_fig = plot_dict

        if api is True:
            _data_list = [query_prod.data.encode(use_binary=False), query_prod_1.data.encode(use_binary=False)]


        query_out = QueryOutput()

        if api == True:
            query_out.prod_dictionary['astropy_table_product_ascii_list'] = _data_list

        else:
            query_out.prod_dictionary['name'] = _names
            query_out.prod_dictionary['file_name'] = _table_path
            query_out.prod_dictionary['image'] = _html_fig
            query_out.prod_dictionary['download_file_name'] = 'antares_table.fits.gz'

        query_out.prod_dictionary['prod_process_message'] = ''


        return query_out
    
    def get_dummy_products(self, instrument, config=None, **kwargs):
        res = DummyAntaresResponse(os.path.join(config.dummy_cache, 'ant_ul.txt'),
                                   os.path.join(config.dummy_cache, 'byind_ant_ul.txt'))
        prod_list = ANTARESTable.build_from_res(res)
        prod_list = QueryProductList(prod_list=prod_list)
        return prod_list


class DummyAntaresResponse():
    def __init__(self, *dummy_files):
        self.dummy_data = []
        for dummy_file in dummy_files:
            self.dummy_file = dummy_file
            with open(dummy_file, 'r') as fd:
                ascii = fd.read()
                self.dummy_data.append({"astropy_table": 
                       {"binary": None, 
                        "ascii": ascii, 
                        "name": "astropy table", 
                        "meta_data": '{"RA": null, "DEC": null, "ROI": null}'}, 
                      "file_path": self.dummy_file})

    def json(self):
        dummy_json = json.dumps(self.dummy_data)
        return dummy_json


class ANTARESAstropyTable(ODAAstropyTable):
    def __init__(self,
                 table,
                 meta_data,
                 name='antares_table',
                 src_name=''):

        super(ANTARESAstropyTable, self).__init__(table,name,meta_data=meta_data)

        self.src_name=src_name

class ANTARESTable(BaseQueryProduct):
    def __init__(self,
                 name,
                 table,
                 file_name,
                 src_name='None',
                 out_dir=None,
                 prod_prefix=None,
                 meta_data={}):

        self.file_name=file_name
        if meta_data == {} or meta_data is None:
            self.meta_data = {'product': 'ANTARES_TABLE', 'instrument': 'ANTARES', 'src_name': src_name}
        else:
            self.meta_data = meta_data



        super(ANTARESTable, self).__init__(name=name,
                                           data=None,
                                           name_prefix=prod_prefix,
                                           file_dir=out_dir,
                                           file_name=file_name,
                                           meta_data=meta_data)

        self.data = ANTARESAstropyTable(name=name, table=table, src_name=src_name, meta_data=meta_data)

    def get_html_draw(self):
        try:
            size=100
            ul_table= self.data.table


            if len(ul_table)>0:

                e_range = ul_table["E"]
                ul_sed = ul_table["flux_UL * E^2"]

                log_e_range_min = np.log10(e_range.min().value)
                log_e_range_max = np.log10(e_range.max().value)
                x_margin = 0.1 * np.abs(log_e_range_min - log_e_range_max)
                x_range = [10 ** (log_e_range_min - x_margin), 10 ** (log_e_range_max + x_margin)]

                log_ul_sed_min = np.log10(ul_sed.min().value)
                log_ul_sed_max = np.log10(ul_sed.max().value)
                y_margin = 0.1 * np.abs(log_ul_sed_max - log_ul_sed_min)
                y_range = [10 ** (log_ul_sed_min - y_margin), 10 ** (log_ul_sed_max + y_margin)]

                sp1 = ScatterPlot(w=600, h=400, x_label=str(e_range.unit), y_label=str(ul_sed.unit),
                                  y_axis_type='log', x_axis_type='log',
                                  x_range=x_range, y_range=y_range,
                                  title='UL')

                sp1.add_line(e_range, ul_sed, color='black')
            else:
                x_range = []
                y_range = []

                sp1 = ScatterPlot(w=600, h=400, x_label=str(Unit('GeV')), y_label='',
                                  y_axis_type='log', x_axis_type='log',
                                  x_range=x_range, y_range=y_range,
                                  title='UL')

            return sp1.get_html_draw()
            
        except Exception as e:
            raise ANTARESAnalysisException(message='problem in plot production'  + str(e),debug_message=repr(e))

        

    @classmethod
    def build_from_res(cls,res,out_dir=None,prod_prefix='antares_table'):

        prod_list = []
        
        if out_dir is None:
            out_dir = './'

        if prod_prefix is None:
            prod_prefix=''

        _o_list = json.loads(res.json())
        
        for _o_dict in _o_list:
            src_name='src'
            t_rec = ascii.read(_o_dict['astropy_table']['ascii'])


            try:
                filename, file_extension = os.path.splitext(os.path.basename(_o_dict['file_path']))
            except:
                filename = src_name + '_'

            file_name=filename[:filename.find('_job')]+'.fits'
            t_rec.meta['filename']=file_name
            #print('->file_name',file_name)
            antares_table = cls(name=src_name,
                            file_name=file_name,
                            table=t_rec,
                            src_name=src_name,
                            meta_data=t_rec.meta,
                            out_dir=out_dir)

            prod_list.append(antares_table)

        return prod_list