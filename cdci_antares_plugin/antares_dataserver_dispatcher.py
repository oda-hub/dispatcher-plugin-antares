from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy
import  ast
import requests
# Dependencies
# eg numpy 
# absolute import eg: import numpy as np
import json

# Project
# relative import eg: from .mod import f
import  logging
import  simple_logger
from cdci_antares_plugin import conf_file as plugin_conf_file
from cdci_data_analysis.configurer import DataServerConf
from cdci_data_analysis.analysis.queries import  *
from cdci_data_analysis.analysis.job_manager import  Job
from cdci_data_analysis.analysis.io_helper import FilePath
from cdci_data_analysis.analysis.products import  QueryOutput

from cdci_data_analysis.analysis.exceptions import APIerror

import json
import traceback
import time
from ast import literal_eval
import os
from contextlib import contextmanager

# @contextmanager
# def silence_stdout():
#     new_target = open(os.devnull, "w")
#     old_target, sys.stdout = sys.stdout, new_target
#     try:
#         yield new_target
#     finally:
#         sys.stdout = old_target
#
#
#
# def redirect_out(path):
#     #print "Redirecting stdout"
#     sys.stdout.flush() # <--- important when redirecting to files
#     newstdout = os.dup(1)
#     devnull = os.open('%s/SED.log'%path, os.O_CREAT)
#     os.dup2(devnull, 1)
#     os.close(devnull)
#     sys.stdout = os.fdopen(newstdout, 'w')

#def view_traceback():
#    ex_type, ex, tb = sys.exc_info()
#    traceback.print_tb(tb)
#    del tb





class ANTARESAnalysisException(Exception):

    def __init__(self, message='ANTARES analysis exception', debug_message=''):
        super(ANTARESAnalysisException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message



class ANTARESException(Exception):

    def __init__(self, message='ANTARES analysis exception', debug_message=''):
        super(ANTARESException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message


class ANTARESUnknownException(ANTARESException):

    def __init__(self,message='ANTARES unknown exception',debug_message=''):
        super(ANTARESUnknownException, self).__init__(message, debug_message)




class ANTARESDispatcher(object):

    def __init__(self,config=None,task=None,param_dict=None,instrument=None):
        print('--> building class ANTARESDispatcher',instrument,config)
        #simple_logger.log()
        #simple_logger.logger.setLevel(logging.ERROR)

        self.task = task
        self.param_dict = param_dict

        #print ('TEST')
        #for k in instrument.data_server_conf_dict.keys():
        #   print ('dict:',k,instrument.data_server_conf_dict[k ])
        
        
        config = DataServerConf.from_conf_dict(instrument.data_server_conf_dict)
        #for v in vars(config):
        #   print('attr:', v, getattr(config, v))


        print('--> config passed to init',config)

        if config is not None:
            
            pass


        elif instrument is not None and hasattr(instrument,'data_server_conf_dict'):

            print('--> from data_server_conf_dict')
            try:
                config = DataServerConf.from_conf_dict(instrument.data_server_conf_dict)

                print('config', config)
                for v in vars(config):
                    print('attr:', v, getattr(config, v))



            except Exception as e:
                #    #print(e)

                print("ERROR->")
                raise RuntimeError("failed to use config ", e)

        elif instrument is not None:
            try:
                print('--> plugin_conf_file',plugin_conf_file )
                config=instrument.from_conf_file(plugin_conf_file)

            except Exception as e:
                #    #print(e)

                print("ERROR->")
                raise RuntimeError("failed to use config ", e)

        else:

            raise ANTARESException(message='instrument cannot be None', debug_message='instrument se to None in ANTARESDispatcher __init__')

        try:
            _data_server_url = config.data_server_url

        except Exception as e:
            #    #print(e)

            print("ERROR->")
            raise RuntimeError("failed to use config ", e)

        self.config(_data_server_url)



        print("data_server_url:", self.data_server_url)
        #print("dataserver_cache:", self.dataserver_cache)
        print('--> done')



    def config(self,data_server_url):

        print('configuring method')
        print('config done in config method')

        self.data_server_url= data_server_url

        print ('DONE CONF',self.data_server_url)

    def test_communication(self, max_trial=10, sleep_s=1,logger=None):
        print('--> start test connection')

        query_out = QueryOutput()
        no_connection = True
        debug_message='OK'

        #client = self._get_client(self.data_server_url)
        url = "%s/%s" % (self.data_server_url, 'test-connection')
        print('url', url)

        for i in range(max_trial):
            try:
                res = requests.get("%s" % (url), params=None)
                if res.status_code != 200:
                    no_connection = True
                else:
                    no_connection = False
                    message = 'Connection OK'
                    query_out.set_done(message=message, debug_message=str(debug_message))
                    break
            except Exception as e:
                no_connection = True

            time.sleep(sleep_s)

        if no_connection is True:
            message = 'no data server connection'
            debug_message = 'no data server connection'
            connection_status_message = 'no data server connection'

            query_out.set_failed(message,
                                 message='connection_status=%s' % connection_status_message,
                                 logger=logger,
                                 excep=e, # may be referenced before assignment
                                 e_message=message,
                                 debug_message=debug_message)

            raise ANTARESException('Connection Error', debug_message)

        print('-> test connections passed')

        return query_out

    def test_has_input_products(self,instrument,logger=None):

        query_out = QueryOutput()
        has_data=True
        try:
            url = "%s/%s" % (self.data_server_url, 'test-connection')
            print('url', url)
            res = requests.get("%s" % (url), params=None)
            if res.status_code != 200:
                has_data = False
        except Exception as e:
            has_data = False



        if has_data is False:
            message = 'no data on backend'
            debug_message = 'no data on backend'
            query_out.set_failed(message, message=message, logger=logger, excep=e,
                                 e_message=message, debug_message=debug_message)

            raise ANTARESException('Connection Error', debug_message)


        message = 'OK'
        debug_message = 'OK'
        query_out.set_done(message=message, debug_message=str(debug_message))


        print('-> test_has_input_products passed')
        return query_out,[1]




    def run_query(self,call_back_url=None,run_asynch=False,logger=None,task=None,param_dict=None,):

        res = None
        # status = 0
        message = ''
        debug_message = ''
        query_out = QueryOutput()

        try:

            #simple_logger.logger.setLevel(logging.ERROR)


            print('--ANTARES disp--')
            print('call_back_url',call_back_url)
            print('data_server_url', self.data_server_url)
            print('*** run_asynch', run_asynch)

            if task is None:
                task=self.task

            if param_dict is None:
                param_dict=self.param_dict

            url = "%s/%s" % (self.data_server_url, task)
            print('url', url,param_dict)

            res = requests.get("%s" % (url), params=param_dict)
            query_out.set_done(message=message, debug_message=str(debug_message),job_status='done')



        # TODO: how can it be thrown?
        except APIerror as e:
            run_query_message = 'API Exception on ANTARES backend'
            debug_message = e.message

            query_out.set_failed('run query ',
                                 message='run query message=%s' % run_query_message,
                                 logger=logger,
                                 excep=repr(e),
                                 job_status='failed',
                                 e_message=run_query_message,
                                 debug_message=debug_message)

            raise ANTARESException(message=run_query_message, debug_message=debug_message)
        except Exception as e:
            run_query_message = 'ANTARES UnknownException in run_query'
            query_out.set_failed('run query ',
                                 message='run query message=%s' % run_query_message,
                                 logger=logger,
                                 excep=e,
                                 job_status='failed',
                                 e_message=run_query_message,
                                 debug_message=e)

            raise ANTARESUnknownException(message=run_query_message, debug_message=e)

        return res,query_out


