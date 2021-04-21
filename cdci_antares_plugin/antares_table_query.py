

from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy
import os

# Dependencies
# eg numpy
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f



# Project
# relative import eg: from .mod import f
import  numpy as np
#import pandas as pd
from astropy.table import Table
import  json
import pathlib
from astropy.io import ascii
import base64

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pickle



from astropy.io import fits as pf
from cdci_data_analysis.analysis.io_helper import FitsFile
from cdci_data_analysis.analysis.queries import ProductQuery
from cdci_data_analysis.analysis.products import BaseQueryProduct,QueryProductList,QueryOutput
from cdci_data_analysis.analysis.io_helper import FilePath
from oda_api.data_products import NumpyDataProduct,NumpyDataUnit,BinaryData
from cdci_data_analysis.configurer import DataServerConf

from .antares_dataserver_dispatcher import ANTARESDispatcher
from .antares_dataserver_dispatcher import  ANTARESAnalysisException




class ANTARESAstropyTable(object):
    def __init__(self,
                 name,
                 table,
                 meta_data,
                 src_name):

        self.src_name=src_name
        self.name=name
        self._table=table
        self.meta_data=meta_data






    @property
    def table(self):
        return self._table


    def decode(self,enc_table):
        pass




    def encode(self, use_binary=False, to_json=False):

        _o_dict = {}
        _o_dict['binary'] = None
        _o_dict['ascii'] = None

        if use_binary is True:
            _binarys = base64.b64encode(pickle.dumps(self.table, protocol=2)).decode('utf-8')
            _o_dict['binary'] = _binarys
        else:
            fh = StringIO()
            self.table.write(fh, format='ascii.ecsv')
            _text = fh.getvalue()
            fh.close()
            _o_dict['ascii'] = _text

        _o_dict['name'] = self.name
        _o_dict['meta_data'] = json.dumps(self.meta_data)

        if to_json == True:
            _o_dict = json.dumps(_o_dict)
        return _o_dict


    def write(self,name,format='fits',overwrite=True):
        self._table.write(name,format=format,overwrite=overwrite)

    def write_fits_file(self, file_name,overwrite=True):
        return self.write(name=file_name,overwrite=overwrite)

    @classmethod
    def from_ecsv_file(cls, file_name,):
        return cls.from_table(Table.read(file_name, format='ascii.ecsv'))


    @classmethod
    def from_fits_file(cls,file_name):
        return cls.from_table(Table.read(file_name,format='fits'))

    @classmethod
    def from_file(cls,file_name):
        format_list=['ascii.ecsv','fits']
        cat=None
        for f in format_list:
            try:
                cat= cls.from_table(Table.read(file_name,format=f))
            except:
                pass

        if cat is None:
            raise RuntimeError('file format for catalog not valid')
        return cat



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


        MWL_files=[]
        ANTARES_files=[]
        #for


        prod_list = []

        if out_dir is None:
            out_dir = './'

        if prod_prefix is None:
            prod_prefix=''

        _o_dict = json.loads(res.json())

        src_name='test'
        t_rec = ascii.read(_o_dict['astropy_table']['ascii'])


        try:
            filename, file_extension = os.path.splitext(_o_dict['file_path'])
        except:
            filename = src_name

        file_name=filename+'.fits'
        print('->file_name',file_name)
        antares_table = cls(name=src_name,
                          file_name=file_name,
                          table=t_rec,
                          src_name=src_name,
                          meta_data=t_rec.meta,
                          out_dir=out_dir)

        prod_list.append(antares_table)

        return prod_list






class ANTARESTableQuery(ProductQuery):

    def __init__(self, name):

        super(ANTARESTableQuery, self).__init__(name)
        self.product_type='antares_table'

    def build_product_list(self, instrument, res, out_dir, prod_prefix='',api=False):

        #delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        print('-> res',res.json())
        prod_list = ANTARESTable.build_from_res(res, out_dir=out_dir)

        # print('spectrum_list',spectrum_list)

        return prod_list


    def get_data_server_query(self, instrument,config=None):


        src_name = instrument.get_par_by_name('src_name').value

        RA = instrument.get_par_by_name('RA').value
        DEC = instrument.get_par_by_name('DEC').value
        ROI = instrument.get_par_by_name('radius').value
        index_min = instrument.get_par_by_name('index_min').value
        index_max = instrument.get_par_by_name('index_max').value
        use_internal_resolver= eval(instrument.get_par_by_name('use_internal_resolver').value)
        param_dict=self.set_instr_dictionaries(target_name=src_name,
                                               ra=RA,
                                               dec=DEC,
                                               roi=ROI,
                                               index_min=index_min,
                                               index_max=index_max,
                                               product_type=self.product_type,
                                               use_internal_resolver=use_internal_resolver)

        #print ('build here',config,instrument)
        q = ANTARESDispatcher(instrument=instrument,config=config,param_dict=param_dict,task='api/v1.0/antares/get-ul-table')

        return q


    def set_instr_dictionaries(self, target_name,
                               paper_id=None,
                               ra=None,
                               dec=None,
                               roi=None,
                               product_type='antares_table',
                               use_internal_resolver=False):
        _prod_name_map_={}
        _prod_name_map_['antares_spectrum'] = 'sed'
        _prod_name_map_['antares_table'] = 'table'
        return  dict(
            target_name=target_name,
            paper_id=paper_id,
            ra=ra,
            dec=dec,
            roi=roi,
            product_type=_prod_name_map_[product_type],
            get_products=True,
            resolve=use_internal_resolver)


    def process_product_method(self, instrument, prod_list,api=False,config=None):

        _names = []
        _table_path = []
        _html_fig = []

        _data_list=[]
        _binary_data_list=[]
        for query_prod in prod_list.prod_list:

            print('query_prod',vars(query_prod))
            query_prod.write()



            #if api==False:
            print('--->, query_prod.meta_data',config,query_prod.meta_data)
            param_dict={}
            param_dict['file_name']=''


            param_dict['file_name']=query_prod.meta_data['Filename']

            q = ANTARESDispatcher(instrument=instrument,
                                config=config,
                                param_dict=param_dict,
                                task='/api/v1.0/antares/plot-ul-envelope')

            res, query_out=q.run_query()
            #print('=>>>> figure res ',res.json())
            res=json.loads(res.json())
            html_dict = {}
            html_dict['script'] = res['script']
            html_dict['div'] = res['div']
            plot_dict = {}
            plot_dict['image'] = html_dict
            plot_dict['header_text'] = ''
            plot_dict['table_text'] = ''
            plot_dict['footer_text'] = ''

            _n=query_prod.name+'_%s'%query_prod.file_path.name
            _s = pathlib.PurePosixPath(_n).suffix
            _n=_n.replace(_s,'')
            _names.append(_n)
            _table_path.append(str(query_prod.file_path.name))
            _html_fig.append(plot_dict)

            if api is True:
                _data_list.append(query_prod.data.encode(use_binary=False))


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


class ANTARESpectrumQuery(ANTARESTableQuery):

    def __init__(self, name):

        super(ANTARESpectrumQuery, self).__init__(name)
        self.product_type='antares_spectrum'

class ANTARESLCQuery(ANTARESTableQuery):
    def __init__(self, name):

        super(ANTARESLCQuery, self).__init__(name)
        self.product_type = 'antares_lc'

class ANTARESImageQuery(ANTARESTableQuery):
    def __init__(self, name):

        super(ANTARESImageQuery, self).__init__(name)
        self.product_type = 'antares_image'
