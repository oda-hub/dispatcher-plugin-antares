

from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pickle

import os

import  numpy as np
from astropy.table import Table
import  json
import pathlib
from astropy.io import ascii
import base64
from astropy.units import Unit

from cdci_data_analysis.analysis.queries import ProductQuery
from cdci_data_analysis.analysis.products import BaseQueryProduct,QueryOutput, QueryProductList
from oda_api.data_products import  ODAAstropyTable

from .antares_dataserver_dispatcher import ANTARESDispatcher,ANTARESAnalysisException
from .plot_tools import  ScatterPlot




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
        pass

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






class ANTARESpectrumQuery(ProductQuery):

    def __init__(self, name):

        super(ANTARESpectrumQuery, self).__init__(name)
        self.product_type='antares_spectrum'

    def build_product_list(self, instrument, res, out_dir, prod_prefix='',api=False):

        #delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        #print('-> res',res.json())
        prod_list = ANTARESTable.build_from_res(res, out_dir=out_dir)

        # print('spectrum_list',spectrum_list)

        return prod_list

    def check_roi(self,v):
        if v < 0.1 or v > 2.5:
            m = 'par ROI=%e outside range [0.1 - 2.5]' % v
            raise ANTARESAnalysisException(message=m, debug_message=m)
        else:
            pass

    def check_index(self,v):
        if v < 1.5 or v > 3.0:
            m = 'par index=%e outside range [1.5 - 3.0]' % v
            raise ANTARESAnalysisException(message=m, debug_message=m)
        else:
            pass

    def check_decl(self,v):
        if v < -80 or v > 50:
            m = 'par decl=%e outside range [-80.0 - 50.0]' % v
            raise ANTARESAnalysisException(message=m, debug_message=m)
        else:
            pass

    def get_data_server_query(self, instrument, config=None):

        src_name = instrument.get_par_by_name('src_name').value

        RA = instrument.get_par_by_name('RA').value
        DEC = instrument.get_par_by_name('DEC').value
        ROI = instrument.get_par_by_name('radius').value

        index_min=instrument.get_par_by_name('index_min').value
        index_max=instrument.get_par_by_name('index_max').value
        #TODO move this to be self-consistent with Antares backend conf
        self.check_decl(DEC)
        self.check_index(index_min)
        self.check_index(index_max)
        self.check_roi(ROI)

        param_dict=self.set_instr_dictionaries(ra=RA,
                                               dec=DEC,
                                               roi=ROI,
                                               index_min=index_min,
                                               index_max=index_max)

        #print ('build here',config,instrument)
        q = ANTARESDispatcher(instrument=instrument,config=config,param_dict=param_dict,task='api/v1.0/antares/get-ul-table')

        return q

    def set_instr_dictionaries(self,ra=None,
                                   dec=None,
                                   roi=None,
                                   #use_internal_resolver=False,
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


        #if api==False:
        #print('--->, query_prod.meta_data',query_prod.meta_data)

        script, div = get_spectrum_plot(query_prod.file_path.path)

        #res, query_out=q.run_query()
        #print('=>>>> figure res ',res.json())
        #res=json.loads(res.json())
        html_dict = {}
        html_dict['script'] = script
        html_dict['div'] = div
        plot_dict = {}
        plot_dict['image'] = html_dict
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


def get_spectrum_plot(file_path):

        try:
            size=100
            ul_table= ANTARESAstropyTable.from_file(file_path=file_path,format='fits').table

            if len(ul_table)>0:

                e_range = ul_table["E"]
                ul_sed = ul_table["flux_UL * E^2"]
            
                sp1 = ScatterPlot(w=600, h=400, x_label=str(e_range.unit), y_label=str(ul_sed.unit),
                                  y_axis_type='log', x_axis_type='log',title='UL')

                sp1.add_line(e_range, ul_sed)
            else:
                sp1 = ScatterPlot(w=600, h=400, x_label=str(Unit('GeV')), y_label='',
                                  y_axis_type='log', x_axis_type='log', title='UL')

            script, div = sp1.get_html_draw()
            #print('-> s,d',script,div)

            return script, div

        except Exception as e:
            #print('qui',e)
            raise ANTARESAnalysisException(message='problem in plot production',debug_message=repr(e))

