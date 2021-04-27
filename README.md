ANTARES cdci plugin
==========================================
*ANTARES plugin for cdci_data_analysis*


What's the license?
-------------------

ANTARES cdci plugin is distributed under the terms of The MIT License.

Who's responsible?
-------------------
Denys Savchenko, Andrea Tramacere

ISDC Data Centre for Astrophysics, Astronomy Department of the University of Geneva, Chemin d'Ecogia 16, CH-1290 Versoix, Switzerland

Configuration for deployment
----------------------------
- copy the `conf_file` from `cdci_antares_plugin/config_dir/data_server_conf.yml' and place in given directory
- set the environment variable `CDCI_ANTARES_PLUGIN_CONF_FILE` to the path of the file conf_file 
- edit the in `conf_file` the two keys:
    - `data_server_url:`  
    
    these two keys must correspond to those in the antares-backend conf_file i.e.:
   
    - `data_server_url:`  -> `url:`
   
    respectively
