import requests
import json
import logging

import pytest
from astropy.io import fits

logger = logging.getLogger(__name__)

default_params = dict(
                    query_status="new",
                    query_type="Real",
                    instrument="antares",
                    product_type="antares_spectrum",
                    RA=280.229167,
                    DEC=-5.55,
                    radius=2.,
                    index_min=1.5,
                    index_max=3.,
                    async_dispatcher=False,
                 )

dummy_params = dict(
                    query_status="new",
                    query_type="Dummy",
                    instrument="antares",
                    product_type="antares_spectrum",
                    async_dispatcher=False,
                 )


def test_discover_plugin():
    import cdci_data_analysis.plugins.importer as importer

    assert 'dispatcher_plugin_antares' in  importer.cdci_plugins_dict.keys()

def test_dummy(dispatcher_live_fixture):
    server = dispatcher_live_fixture

    logger.info("constructed server: %s", server)
    c = requests.get(server + "/run_analysis",
                     params = dummy_params)

    logger.info("content: %s", c.text)
    jdata = c.json()
    logger.info(json.dumps(jdata, indent=4, sort_keys=True))
    logger.info(jdata)
    assert c.status_code == 200

    assert jdata['job_status'] == 'done'
    
def test_default(dispatcher_live_fixture):
    server = dispatcher_live_fixture

    logger.info("constructed server: %s", server)
    c = requests.get(server + "/run_analysis",
                     params = default_params)

    logger.info("content: %s", c.text)
    jdata = c.json()
    logger.info(json.dumps(jdata, indent=4, sort_keys=True))
    logger.info(jdata)
    assert c.status_code == 200

    assert jdata['job_status'] == 'done'

@pytest.mark.depends(on=['test_default'])
def test_file_download(dispatcher_live_fixture):
    server = dispatcher_live_fixture

    logger.info("constructed server: %s", server)
    c = requests.get(server + "/run_analysis",
                     params = default_params)

    logger.info("content: %s", c.text)
    jdata = c.json()
    logger.info(json.dumps(jdata, indent=4, sort_keys=True))
    logger.info(jdata)
    
    d = requests.get(server + "/download_products",
                    params = {
                        'session_id': jdata['job_monitor']['session_id'],
                        'download_file_name': jdata['products']['download_file_name'],
                        'file_list': jdata['products']['file_name'],
                        'query_status': 'ready',
                        'job_id': jdata['job_monitor']['job_id'],
                        'instrument': 'antares'
                    })
    assert d.status_code == 200

    with open('tmp.fits.gz', 'wb') as fd:
        fd.write(d.content)

    with fits.open('tmp.fits.gz', 'readonly') as fd:
        for ext in fd:
            logger.info(ext.header)
            logger.info(ext.data)