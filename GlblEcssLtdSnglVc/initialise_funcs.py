"""
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'initialise_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import exists, isfile, join
from json import dump as json_dump, load as json_load

from initialise_common_funcs import write_default_config_file
from weather_datasets import change_weather_resource, record_weather_settings
from litter_and_orchidee_fns import check_xls_crds_fname, check_xls_lttr_fname, fetch_nc_litter

MIN_GUI_LIST = ['weatherResource', 'aveWthrFlag', 'bbox', 'use_nc', 'use_xlsx']
CMN_GUI_LIST = ['study', 'histStrtYr', 'histEndYr', 'climScnr', 'futStrtYr', 'futEndYr', 'eqilMode',
                'plntFncTyp', 'ncLitterFname', 'xlsLitterFname', 'xlsCoordsFname']
sleepTime = 5
ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

# ===========================================

def read_config_file(form):
    """
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    """

    # flag set when reading setup file
    # ===============================
    if form.ecosse_run_flag:
        form.w_auto_spec.setEnabled(True)
        form.w_run_ecosse.setEnabled(True)
    else:
        form.w_run_ecosse.setEnabled(False)
        form.w_auto_spec.setEnabled(False)

    config_file = form.config_file
    if exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json_load(fconfig)
                print('Read config file ' + config_file)
        except (OSError, IOError) as err:
            print(err)
            return False
    else:
        config = write_default_config_file(config_file)

    grp = 'minGUI'
    for key in MIN_GUI_LIST:
        if key not in config[grp]:
            if key == 'use_nc' or key == 'use_xlsx':
                config[grp]['use_nc'] = 'True'
                config[grp]['use_xlsx'] = 'False'
            else:
                print(ERROR_STR + 'setting {} is required in group {} of config file {}'.format(key, grp, config_file))
                return False

    weather_resource = config[grp]['weatherResource']
    ave_weather = config[grp]['aveWthrFlag']

    form.combo10w.setCurrentText(weather_resource)
    change_weather_resource(form, weather_resource)

    # TODO: improve understanding of check boxes
    # ==========================================
    if config[grp]['use_xlsx']:
        form.w_use_xlsx.setChecked(True)
    else:
        form.w_use_xlsx.setChecked(False)

    if config[grp]['use_nc']:
        form.w_use_nc.setChecked(True)
    else:
        form.w_use_nc.setChecked(False)

    # common area
    # ===========
    grp = 'cmnGUI'
    for key in CMN_GUI_LIST:
        if key not in config[grp]:
            if key == 'ncLitterFname' or key == 'xlsLitterFname':
                config[grp][key] = ''
            elif key == 'plntFncTyp':
                config[grp][key] = 'SoilBareGlobal'
            else:
                print(ERROR_STR + 'setting {} is required in group {} of config file {}'.format(key, grp, config_file))
                return False

    form.w_study.setText(str(config[grp]['study']))
    hist_strt_year = config[grp]['histStrtYr']
    hist_end_year = config[grp]['histEndYr']
    scenario = config[grp]['climScnr']
    sim_strt_year = config[grp]['futStrtYr']
    sim_end_year = config[grp]['futEndYr']
    form.w_equimode.setText(str(config[grp]['eqilMode']))

    xls_fn = config[grp]['xlsCoordsFname']
    form.w_xls_crds_fn.setText(xls_fn)
    check_xls_crds_fname(form, xls_fn)

    xls_lttr_fn = config[grp]['xlsLitterFname']
    form.w_xls_lttr_fn.setText(xls_lttr_fn)
    check_xls_lttr_fname(xls_lttr_fn, form.w_xls_lttr_nrecs)

    nc_fn = config[grp]['ncLitterFname']
    form.w_nc_lttr_fn.setText(nc_fn)
    fetch_nc_litter(form, nc_fn)
    form.w_combo_pfts.setCurrentText(config[grp]['plntFncTyp'])

    # record weather settings
    # =======================
    form.wthr_settings_prev[weather_resource] = record_weather_settings(scenario, hist_strt_year, hist_end_year,
                                                                        sim_strt_year, sim_end_year)
    form.combo09s.setCurrentText(hist_strt_year)
    form.combo09e.setCurrentText(hist_end_year)
    form.combo10.setCurrentText(scenario)
    form.combo11s.setCurrentText(sim_strt_year)
    form.combo11e.setCurrentText(sim_end_year)

    # set check boxes
    # ===============
    if ave_weather:
        form.w_ave_weather.setCheckState(2)
    else:
        form.w_ave_weather.setCheckState(0)

    # avoids errors when exiting
    # ==========================
    form.req_resol_deg = None
    form.req_resol_granul = None
    form.w_use_dom_soil.setChecked(True)
    form.w_use_high_cover.setChecked(True)

    return True

def write_config_file(form, message_flag=True):
    """
    write current selections to config file
    """
    study = form.w_study.text()

    # facilitate multiple config file choices
    # =======================================
    glbl_ecsse_str = form.glbl_ecsse_str
    config_file = join(form.config_dir, glbl_ecsse_str + study + '.txt')

    # TODO: might want to consider where else in the work flow to save these settings
    weather_resource = form.combo10w.currentText()
    scenario = form.combo10.currentText()
    hist_strt_year = form.combo09s.currentText()
    hist_end_year = form.combo09e.currentText()
    sim_strt_year = form.combo11s.currentText()
    sim_end_year = form.combo11e.currentText()
    form.wthr_settings_prev[weather_resource] = record_weather_settings(scenario, hist_strt_year, hist_end_year,
                                                                        sim_strt_year, sim_end_year)
    config = {
        'minGUI': {
            'bbox': None,
            'use_nc': form.w_use_nc.isChecked(),
            'use_xlsx': form.w_use_xlsx.isChecked(),
            'snglPntFlag': False,
            'weatherResource': weather_resource,
            'aveWthrFlag': form.w_ave_weather.isChecked()
        },
        'cmnGUI': {
            'study': form.w_study.text(),
            'histStrtYr': hist_strt_year,
            'histEndYr': hist_end_year,
            'climScnr': scenario,
            'futStrtYr': sim_strt_year,
            'futEndYr': sim_end_year,
            'eqilMode': form.w_equimode.text(),
            'ncLitterFname': form.w_nc_lttr_fn.text(),
            'plntFncTyp': form.w_combo_pfts.currentText(),
            'study': study,
            'xlsCoordsFname': form.w_xls_crds_fn.text(),
            'xlsLitterFname': form.w_xls_lttr_fn.text()
        }
    }
    if isfile(config_file):
        descriptor = 'Overwrote existing'
    else:
        descriptor = 'Wrote new'
    if study != '':
        with open(config_file, 'w') as fconfig:
            json_dump(config, fconfig, indent=2, sort_keys=True)
            fconfig.close()
            if message_flag:
                print('\n' + descriptor + ' configuration file ' + config_file)
            else:
                print()
    return

def write_study_definition_file(form):
    """
    write study definition file
    """

    # do not write study def file
    # ===========================
    if 'LandusePI' not in form.lu_pi_content:
        return

    # prepare the bounding box
    # ========================
    ll_lon = 0.0;
    ll_lat = 0.0
    try:
        ll_lon = float(form.w_ll_lon.text())
        ll_lat = float(form.w_ll_lat.text())
        ur_lon = float(form.w_ur_lon.text())
        ur_lat = float(form.w_ur_lat.text())
    except ValueError:
        ur_lon = 0.0
        ur_lat = 0.0
    bbox = list([ll_lon, ll_lat, ur_lon, ur_lat])
    study = form.w_study.text()

    weather_resource = form.combo10w.currentText()
    if weather_resource == 'CRU':
        fut_clim_scen = form.combo10.currentText()
    else:
        fut_clim_scen = weather_resource

    # convert resolution to granular then to decimal
    # ==============================================
    study_defn = {
        'studyDefn': {
            'bbox': bbox,
            "luPiJsonFname": None,
            'study': study,
            'histStrtYr': form.combo09s.currentText(),
            'histEndYr': form.combo09e.currentText(),
            'climScnr': fut_clim_scen,
            'futStrtYr': form.combo11s.currentText(),
            'futEndYr': form.combo11e.currentText(),
            'province': 'xxxx',
            'shpe_file': 'xxxx',
            'version': form.version
        }
    }

    # copy to sims area
    # =================
    if study == '':
        print(WARN_STR + 'study not defined  - could not write study definition file')
    else:
        study_defn_file = join(form.sims_dir, study + '_study_definition.txt')
        with open(study_defn_file, 'w') as fstudy:
            json_dump(study_defn, fstudy, indent=2, sort_keys=True)
            print('\nWrote study definition file ' + study_defn_file)

    return
