#-------------------------------------------------------------------------------
# Name:        litter_and_orchidee_fns.py
# Purpose:     script to create objects describing NC data sets
# Author:      Mike Martin
# Created:     31/05/2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'litter_and_orchidee_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import exists, isfile
from math import isnan
from netCDF4 import Dataset, num2date
from pandas import read_excel, DataFrame
from mngmnt_fns_and_class import ManagementSet

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '
CNVRSN_FACT = 10000 * 365 / 1000  # gC/m**2/day to kgC/ha/yr

def resize_yrs_pi(sim_strt_yr, sim_end_yr, yrs_pi):
    """
    patch to enable adjust yrs_pi to correspond to user specified simulation period
    """
    yr_frst = yrs_pi['yrs'][0]
    yr_last = yrs_pi['yrs'][-1]

    pi_frst = yrs_pi['pis'][0]
    pi_last = yrs_pi['pis'][-1]

    sim_yrs = list(range(sim_strt_yr, sim_end_yr + 1))

    sim_pis = []
    for iyr, yr in enumerate(sim_yrs):
        if yr < yr_frst:
            sim_pis.append(pi_frst)
        elif yr > yr_last:
            sim_pis.append(pi_last)
        else:
            sim_pis.append(yrs_pi['pis'][iyr])

    new_yrs_pi = {'yrs': sim_yrs, 'pis': sim_pis}

    return new_yrs_pi

def fetch_nc_litter(form, fname):
    """
    currently permit only a single cell
    """
    if not exists(fname):
        if fname.isspace() or fname == '':
            pass
        else:
            print(WARN_STR + 'ORCHIDEE NetCDF litter file ' + fname + ' does not exist')
        return None

    cells = form.cells
    if cells is None:
        return

    pfts = form.pfts

    nc_dset = Dataset(fname)    # defaults to mode='r'
    lats = nc_dset.variables['lat'][:]
    lons = nc_dset.variables['lon'][:]
    form.w_nc_extnt.setText('lats: {}\tlons: {}'.format(len(lats), len(lons)))

    litter_defn = ManagementSet(fname, 'litter')

    if hasattr(form, 'w_combo_pfts'):
        pft_name = form.w_combo_pfts.currentText()
        value = {elem for elem in pfts if pfts[elem] == pft_name}
        pft_indx = int(list(value)[0]) - 1   # convert set to a list
    else:
        pft_indx = 0

    # stanza to get start of time series
    # ==================================
    time_var_name = 'time_centered'
    time_var = nc_dset.variables[time_var_name]
    start_date = num2date(int(time_var[0]), units=time_var.units, calendar=time_var.calendar)
    start_year = start_date.year
    nyears = len(time_var)

    # ===================
    lat_last, lat_frst, lon_last, lon_frst = (litter_defn.lat_last, litter_defn.lat_frst, litter_defn.lon_last,
                                              litter_defn.lon_frst)
    out_lims = ' is outside limits of ORCHIDEE dataset'
    plnt_inpts = {'yrs': [], 'pis': []}

    for lat, lon, unique_id in zip(cells['Lattitude-N'], cells['Longitude-E'], cells['Unique identifier']):

        if isnan(lat) or isnan(lon):
            continue

        if lat > lat_last or lat < lat_frst:
            print(WARN_STR + 'latitude: {} {}: {} {}'.format(lat, out_lims, lat_frst, lat_last))
            continue

        if lon > lon_last or lon < lon_frst:
            print(WARN_STR + 'longitude: {} {}: {} {}'.format(lon, out_lims, lon_frst, lon_last))
            continue

        # fetch nearest values
        # ====================
        lat_indx, lon_indx, ret_code = litter_defn.get_nc_coords(lat, lon)
        vals = nc_dset.variables['TOTAL_BM_LITTER_c'][:, pft_indx, lat_indx, lon_indx]
        cell_lat = nc_dset.variables['lat'][lat_indx]
        cell_lon = nc_dset.variables['lon'][lon_indx]

        mess = ('Study lat/lon: {} {}\tCell lat/lon: {} {}'.format(lat, lon, cell_lat, cell_lon))
        print(mess)

        # find average of litter carbon
        # =============================
        plnt_inpts['yrs'] = [yr for yr in range(start_year, start_year + nyears)]
        plnt_inpts['pis'] = [CNVRSN_FACT * val for val in vals]

        ave_val = sum(plnt_inpts['pis'])/nyears
        form.w_ave_val.setText('Average value: ' + str(round(float(ave_val), 2)))

    nc_dset.close()

    if len(plnt_inpts['yrs']) == 0:
        return None
    else:
        return plnt_inpts

def check_xls_crds_fname(form, fname):
    """
    C
    """
    form.w_create_files.setEnabled(False)

    if not exists(fname):
        if fname.isspace() or fname == '':
            pass
        else:
            print('File ' + fname + ' does not exist')
        return None

    nrecs = 0
    if isfile(fname):
        results = read_excel(fname)
        nrecs = len(results)

    if 'Lattitude-N' in results.columns and 'Longitude-E' in results.columns:
        print('valid coordinates file - Lattitude-N and Longitude-E fields are present')
        form.w_create_files.setEnabled(True)
    else:
        print(ERROR_STR + 'invalid coordinates file - must have Lattitude-N and Longitude-E fields')
        results = None
        nrecs = 0

    form.w_ncrds_lbl.setText('records: {}'.format(nrecs))
    form.cells = results

    return

def check_xls_lttr_fname(fname, w_xls_lttr_nrecs, data_flag = False):
    """
    C
    """
    if not exists(fname):
        if fname.isspace() or fname == '':
            pass
        else:
            print('File ' + fname + ' does not exist')
        return None

    nrecs = 0
    sht_nm = 'Plant litter_timeseries'
    plnt_inpts = {}
    pi_col = 'Plant litter input (Aggregate)'
    time_col = 'time'
    if isfile(fname):
        try:
            sheet_df = read_excel(fname, sheet_name=sht_nm)
        except (KeyError, ValueError) as err:
            print(ERROR_STR + str(err) + ' sheet ' + sht_nm + ' must be in ' + fname )
            return None

        if time_col in sheet_df and pi_col in sheet_df:
            plnt_inpts['yrs'] = sheet_df[time_col].to_list()
            plnt_inpts['pis'] = [val for val in sheet_df[pi_col].to_list()]
            nrecs = len(plnt_inpts['yrs'])
        else:
            print(ERROR_STR + ' columns ' + time_col + ' and ' + pi_col + ' must be in ' + fname)
            return None

    w_xls_lttr_nrecs.setText('records: {}'.format(nrecs))

    # ensure years are sequential
    # ===========================
    strt_yr = plnt_inpts['yrs'][0]
    yrs = [yr + strt_yr for yr in range(len(plnt_inpts['yrs']))]
    plnt_inpts['yrs'] = yrs

    if data_flag:
        return plnt_inpts
    else:
        return nrecs

def change_pft(form):
    """
    C
    """
    if hasattr(form, 'w_combo_pfts'):
        print(form.w_combo_pfts.currentText())

def orchidee_pfts():
    """
    C
    """
    pfts = {'01': 'SoilBareGlobal',
            '02': 'BroadLeavedEvergreenTropical',
            '03': 'BroadLeavedRaingreenTropical',
            '04': 'NeedleleafEvergreenTemperate',
            '05': 'BroadLeavedEvergreenTemperate',
            '06': 'BroadLeavedSummergreenTemperate',
            '07': 'NeedleleafEvergreenBoreal',
            '08': 'BroadLeavedSummergreenBoreal',
            '09': 'LarixSpBoreal',
            '10': 'C3GrassTemperate',
            '11': 'C4GrassTemperate',
            '12': 'C3AgricultureTemperate',
            '13': 'C4AgricultureTemperate',
            '14': 'C3GrassTropical',
            '15': 'C3GrassBoreal'}

    return pfts
