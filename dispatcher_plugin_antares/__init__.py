__author__ = "Andrea Tramacere, Denys Savchenko"

import os

conf_dir=os.path.dirname(__file__)+'/config_dir'

if conf_dir is not None:
    conf_dir=conf_dir

def find_config():
    config_file_resolution_order=[
        os.environ.get('CDCI_ANTARES_PLUGIN_CONF_FILE','.antares_data_server_conf.yml'),
        os.path.join(conf_dir,'data_server_conf.yml'),
        "/dispatcher/conf/conf.d/antares_data_server_conf.yml",
    ]

    for conf_file in config_file_resolution_order:
        if conf_file is not None and os.path.exists(conf_file): # and readable?
            return conf_file

    raise RuntimeError("no antares config found tried: "+", ".join(config_file_resolution_order))

conf_file=find_config()
