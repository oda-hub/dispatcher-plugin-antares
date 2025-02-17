__author__ = "Andrea Tramacere, Denys Savchenko"

import requests
import  logging
from dispatcher_plugin_antares import conf_file as plugin_conf_file
from cdci_data_analysis.configurer import DataServerConf
from cdci_data_analysis.analysis.queries import  *
from cdci_data_analysis.analysis.products import  QueryOutput

from cdci_data_analysis.analysis.exceptions import APIerror
import time

logger = logging.getLogger(__name__)

class ANTARESAnalysisException(Exception):

    def __init__(self, message='ANTARES analysis exception', debug_message=''):
        super(ANTARESAnalysisException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message



class ANTARESException(Exception):


    def __init__(self, message='ANTARES  exception', debug_message=''):
        super(ANTARESException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message


class ANTARESUnknownException(ANTARESException):

    def __init__(self,message='ANTARES unknown exception',debug_message=''):
        super(ANTARESUnknownException, self).__init__(message, debug_message)




class ANTARESDispatcher(object):

    def __init__(self,config=None,task=None,param_dict=None,instrument=None):
        logger.info(f'--> building class ANTARESDispatcher for the instrument {instrument} with the config: {config}')
        #simple_logger.log()
        #simple_logger.logger.setLevel(logging.ERROR)

        self.task = task
        self.param_dict = param_dict

        for k in instrument.data_server_conf_dict.keys():
           logger.info(f'dict: {k} - {instrument.data_server_conf_dict[k]}')

        config = DataServerConf.from_conf_dict(instrument.data_server_conf_dict)

        logger.info(f'--> config passed to init: {config}')

        if config is not None:
            pass

        elif instrument is not None and hasattr(instrument,'data_server_conf_dict'):

            logger.info('--> from data_server_conf_dict')
            try:
                config = DataServerConf.from_conf_dict(instrument.data_server_conf_dict)

                for v in vars(config):
                    logger.debug('attr:', v, getattr(config, v))

            except Exception as e:
                raise RuntimeError("failed to use config ", e)

        elif instrument is not None:
            try:
                logger.info(f'--> plugin_conf_file: {plugin_conf_file}')
                config=instrument.from_conf_file(plugin_conf_file)

            except Exception as e:
                raise RuntimeError("failed to use config ", e)

        else:
            raise ANTARESException(message='instrument cannot be None', debug_message='instrument set to None in ANTARESDispatcher __init__')

        try:
            self.data_server_url = config.data_server_url

        except Exception as e:
            raise RuntimeError("failed to use config ", e)

        logger.info(f'data_server_url: {self.data_server_url}')
        logger.info('--> done')

    def test_communication(self, max_trial=10, sleep_s=1,logger=None):
        print('--> start test connection')

        query_out = QueryOutput()
        no_connection = True
        debug_message='OK'

        url = "%s/%s" % (self.data_server_url, 'api/v1.0/antares/test-connection')
        logger.info(f'url: {url}')

        for i in range(max_trial):
            try:
                res = requests.get("%s" % (url), params=None)
                logger.info(f'status_code: {res.status_code}')
                if res.status_code !=200:
                    no_connection =True
                    e = ConnectionError(f"Backend connection failed: {res.status_code}")
                else:
                    no_connection=False

                    message = 'Connection OK'
                    query_out.set_done(message=message, debug_message=str(debug_message))
                    break
            except Exception as e:
                no_connection = True

            time.sleep(sleep_s)

        if no_connection:
            message = 'no data server connection'
            debug_message = 'no data server connection'
            connection_status_message = 'no data server connection'

            query_out.set_failed(failed_operation='data server connection',
                                 message=f'connection_status={connection_status_message} trying to access {url}',
                                 logger=logger,
                                 excep=None,
                                 e_message=message,
                                 debug_message=debug_message)

            raise ANTARESException('Connection Error', debug_message)

        logger.info('-> test connections passed')

        return query_out

    def test_has_input_products(self,instrument,logger=None):

        query_out = QueryOutput()
        query_out.set_done(message='OK', debug_message='OK')
        return query_out, []


    def run_query(self,call_back_url=None, run_asynch=False, logger=None, task=None, param_dict=None):

        res = None
        message = ''
        debug_message = ''
        query_out = QueryOutput()

        try:
            logger.info('--ANTARES disp--')
            logger.info(f'fcall_back_url: {call_back_url}')
            logger.info(f'data_server_url: {self.data_server_url}')
            logger.info(f'*** run_asynch: {run_asynch}')

            if task is None:
                task=self.task

            if param_dict is None:
                param_dict=self.param_dict
            
            # we want to pass job_id to backend but it is not in this scope, so deduce  
            # TODO: it shouldn't be necessary
            try:
                job_id = call_back_url[call_back_url.index('job_id=')+7:].split('&')[0]
                param_dict['job_id'] = job_id
            except:
                pass

            url = "%s/%s" % (self.data_server_url, task)
            logger.info(f'url: {url}\nparam_dic: {param_dict}')

            res = requests.get("%s" % (url), params = param_dict)
            query_out.set_done(message=message, debug_message=str(debug_message), job_status='done')



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

        except ANTARESAnalysisException as e:
            run_query_message = 'ANTARES Analysis Exception in run_query'
            query_out.set_failed('run query ',
                                 message='run query message=%s' % run_query_message,
                                 logger=logger,
                                 excep=e,
                                 job_status='failed',
                                 e_message=run_query_message,
                                 debug_message=e)

            raise ANTARESException(message=run_query_message, debug_message=e)

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


