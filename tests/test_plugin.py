import requests
import time
import json
import logging

import pytest


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

    
@pytest.mark.xfail
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
    
def test_dummy(dispatcher_live_fixture):
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
