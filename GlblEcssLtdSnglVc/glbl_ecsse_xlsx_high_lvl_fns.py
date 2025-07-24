"""
#-------------------------------------------------------------------------------
# Name:        hwsd_glblecsse_fns.py
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# Description:
#   comprises two functions:
#       def _generate_ecosse_files(form, climgen, num_band)
#       def generate_banded_sims(form)
#-------------------------------------------------------------------------------
#
"""
__prog__ = 'glbl_ecsse_xlsx_high_lvl_fns.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from os.path import isfile
from math import isnan

import make_ltd_data_files
import getClimGenNC
import hwsd_bil
from prepare_ecosse_files import make_ecosse_file
from getClimGenFns import check_clim_nc_limits, associate_climate
from litter_and_orchidee_fns import check_xls_crds_fname, check_xls_lttr_fname, fetch_nc_litter, resize_yrs_pi
from glbl_ecsse_high_level_fns import simplify_soil_recs

WARN_STR = '*** Warning *** '

def generate_sims_from_xls_or_nc(form):
    """
    called from GUI - generates ECOSSE simulation files for one site
    """
    func_name = __prog__ + ' generate_simulation_files'
    mess_cant_run = ' does not exist - cannot run simulations'
    mess_no_cells = ' no cells - cannot run simulations'

    snglPntFlag = True
    cells = form.cells
    if cells is None:
        print(WARN_STR + mess_no_cells)
        return

    if form.w_use_xlsx.isChecked():
        fname = form.w_xls_lttr_fn.text()
        if not isfile(fname):
            print(WARN_STR + fname + mess_cant_run)
            return
        yrs_pi = check_xls_lttr_fname(fname, form.w_xls_lttr_nrecs, data_flag=True)
    else:
        fname = form.w_nc_lttr_fn.text()
        if not isfile(fname):
            print(WARN_STR + fname + mess_cant_run)
            return
        yrs_pi = fetch_nc_litter(form, fname)     # w_nc_extnt is number of lats and lons label
        if yrs_pi is None:
            return

    study = form.w_study.text()
    wthr_rsrce = form.combo10w.currentText()

    # extract required values from the HWSD database
    # ==============================================
    hwsd = hwsd_bil.HWSD_bil(form.lgr, form.hwsd_dir)

    print('Gathering soil and climate data for study {}...\t\tin {}'.format(study, func_name))
    completed = 0
    skipped = 0
    for lat, lon, unique_id in zip(cells['Lattitude-N'], cells['Longitude-E'], cells['Unique identifier']):

        if isnan(lat) or isnan(lon):
            continue

        nvals_read = hwsd.read_bbox_mu_globals([lon, lat], snglPntFlag)

        # retrieve dictionary mu_globals and number of occurrences
        # ========================================================
        mu_globals = hwsd.get_mu_globals_dict()
        if mu_globals is None:
            print('No soil records for ' + unique_id + '\n')
            continue

        # create and instantiate a new class NB this stanza enables single site
        # ==================================
        form.hwsd_mu_globals = type('test', (), {})()
        soil_recs = hwsd.get_soil_recs(mu_globals)
        form.hwsd_mu_globals.soil_recs = simplify_soil_recs(soil_recs, use_dom_soil_flag=True)
        if len(mu_globals) == 0:
            print('No soil data for this area\n')
            return

        mu_globals_props = {next(iter(mu_globals)): 1.0}

        mess = 'Retrieved {} values  of HWSD grid consisting of {} rows and {} columns: ' \
              '\n\tnumber of unique mu_globals: {}'.format(nvals_read, hwsd.nlats, hwsd.nlons, len(mu_globals))
        form.lgr.info(mess); print(mess)

        # check requested AOI coordinates against extent of the weather resource dataset
        # ==============================================================================
        bbox_aoi = list([lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01])
        if check_clim_nc_limits(form, wthr_rsrce, bbox_aoi):
            print('Selected ' + wthr_rsrce)
            historic_weather_flag = wthr_rsrce
            future_climate_flag = wthr_rsrce
        else:
            print(WARN_STR + 'Coordinate with lat/long: {} {} lies outwith ' + wthr_rsrce + ' limits'.format(lat, lon))
            continue

        form.historic_weather_flag = historic_weather_flag
        form.future_climate_flag = future_climate_flag
        climgen = getClimGenNC.ClimGenNC(form)
        yrs_pi = resize_yrs_pi(climgen.sim_start_year, climgen.sim_end_year, yrs_pi)
        # ==============================================================

        # generate weather dataset indices which enclose the AOI for this band
        num_band = 0
        aoi_indices_fut, aoi_indices_hist = climgen.genLocalGrid(bbox_aoi, hwsd, snglPntFlag)

        # historic weather and future climate
        # ===================================
        print('Getting future data for study {}'.format(study))
        wthr_rsrc = climgen.weather_resource
        if wthr_rsrc == 'HARMONIE':
            pettmp_fut = climgen.fetch_harmonie_NC_data(aoi_indices_fut, num_band)

        elif wthr_rsrc == 'EObs':
            pettmp_fut = climgen.fetch_eobs_NC_data(aoi_indices_fut, num_band)

        elif wthr_rsrc in form.amma_2050_allowed_gcms:
            pettmp_fut = climgen.fetch_ewembi_NC_data(aoi_indices_fut, num_band)
        else:
            pettmp_fut = climgen.fetch_cru_future_NC_data(aoi_indices_fut, num_band)

        print('Getting historic data for study {}'.format(study))
        # =======================================================
        if wthr_rsrc == 'HARMONIE':
            pettmp_fut = climgen.fetch_harmonie_NC_data(aoi_indices_fut, num_band)

        elif wthr_rsrc == 'EObs':
            pettmp_hist = climgen.fetch_eobs_NC_data(aoi_indices_fut, num_band)

        elif wthr_rsrc in form.amma_2050_allowed_gcms:
            pettmp_hist = climgen.fetch_ewembi_NC_data(aoi_indices_hist, num_band, future_flag = False)
        else:
            pettmp_hist = climgen.fetch_cru_historic_NC_data(aoi_indices_hist, num_band)

        print('Creating simulation files for unique_id {}...'.format(unique_id))
        #      =========================================

        # Initialise the limited data object with general settings that do not change between simulations
        ltd_data = make_ltd_data_files.MakeLtdDataFiles(form, climgen, yrs_pi)  # creates limited data object

        # generate sets of Ecosse files for each site where each site has one or more soils
        # each soil can have one or more dominant soils
        # =======================================================================
        area = 1.0
        site_rec = list([hwsd.nrow1, hwsd.ncol1, lat, lon, area, mu_globals_props])

        # yield_set = associate_yield(form)
        pettmp_grid_cell = associate_climate(site_rec, climgen, pettmp_hist, pettmp_fut)
        if len(pettmp_grid_cell) == 0:
            skipped += 1
        else:
            make_ecosse_file(form, climgen, ltd_data, site_rec, study, pettmp_grid_cell)
            completed += 1

        print('Created {} simulation set in {}'.format(completed, form.sims_dir))

    return
