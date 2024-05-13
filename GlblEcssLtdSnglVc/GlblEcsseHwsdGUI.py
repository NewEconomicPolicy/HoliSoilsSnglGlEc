# -------------------------------------------------------------------------------
# Name:
# Purpose:     Creates a GUI with five adminstrative levels plus country
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# -------------------------------------------------------------------------------

__prog__ = 'GlblEcsseHwsdGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from os import system, getcwd
from time import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit,
                             QRadioButton, QButtonGroup, QComboBox, QPushButton, QCheckBox, QFileDialog, QTextEdit)

from common_componentsGUI import (exit_clicked, commonSection, change_config_file, studyTextChanged, save_clicked)
from glbl_ecsse_xlsx_high_lvl_fns import generate_sims_from_xls_or_nc

from weather_datasets import change_weather_resource
from initialise_funcs import read_config_file
from initialise_common_funcs import initiation, build_and_display_studies, write_runsites_config_file
from litter_and_orchidee_fns import (check_xls_crds_fname, check_xls_lttr_fname, fetch_nc_litter, orchidee_pfts,
                                     change_pft)
from set_up_logging import OutLog

STD_BTN_SIZE_100 = 100
STD_BTN_SIZE_80 = 80
STD_FLD_SIZE_180 = 180

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

# ========================

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'HWSD_grid'
        initiation(self, '_vc')
        self.pfts = orchidee_pfts()
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)  # set spacing between widgets

        # line 0
        # ======
        irow = 0
        lbl00 = QLabel('Study:')
        lbl00.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl00, irow, 0)

        w_study = QLineEdit()
        w_study.setFixedWidth(STD_FLD_SIZE_180)
        grid.addWidget(w_study, irow, 1, 1, 2)
        self.w_study = w_study

        lbl00s = QLabel('studies:')
        lbl00s.setAlignment(Qt.AlignRight)
        helpText = 'list of studies'
        lbl00s.setToolTip(helpText)
        grid.addWidget(lbl00s, irow, 3)

        combo00s = QComboBox()
        for study in self.studies:
            combo00s.addItem(study)
        grid.addWidget(combo00s, irow, 4, 1, 2)
        combo00s.currentIndexChanged[str].connect(self.changeConfigFile)
        self.combo00s = combo00s

        # soil switches
        # =============
        irow += 1
        lbl04 = QLabel('Options:')
        lbl04.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl04, irow, 0)

        w_use_dom_soil = QCheckBox('Use most dominant soil')
        helpText = 'Each HWSD grid cell can have up to 10 soils. Select this option to use most dominant soil and\n' \
                   ' discard all others. The the most dominant soil is defined as having the highest percentage coverage ' \
                   ' of all the soils for that grid cell'
        w_use_dom_soil.setToolTip(helpText)
        grid.addWidget(w_use_dom_soil, irow, 1, 1, 2)
        self.w_use_dom_soil = w_use_dom_soil

        w_use_high_cover = QCheckBox('Use highest coverage soil')
        helpText = 'Each meta-cell has one or more HWSD mu global keys with each key associated with a coverage expressed \n' \
                   ' as a proportion of the area of the meta cell. Select this option to use the mu global with the highest coverage,\n' \
                   ' discard the others and aggregate their coverages to the selected mu global'
        w_use_high_cover.setToolTip(helpText)
        grid.addWidget(w_use_high_cover, irow, 3, 1, 2)
        self.w_use_high_cover = w_use_high_cover

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # create weather and grid resolution
        # ==================================
        irow = commonSection(self, grid, irow)

        irow += 1
        w_xls_pshb = QPushButton('Excel file of coords')
        helpText_xls = 'Use a Excel file comprising a list of grid coordinates'
        w_xls_pshb.setToolTip(helpText_xls)
        w_xls_pshb.clicked.connect(self.fetchXlsCoordsFile)
        grid.addWidget(w_xls_pshb, irow, 0)

        w_xls_crds_fn = QLabel('')
        grid.addWidget(w_xls_crds_fn, irow, 1, 1, 4)
        self.w_xls_crds_fn = w_xls_crds_fn

        w_ncrds_lbl = QLabel('')  # number of coordinates
        grid.addWidget(w_ncrds_lbl, irow, 6)
        self.w_ncrds_lbl = w_ncrds_lbl

        # ===========================

        irow += 1
        w_lbl06b = QLabel('Litter resource:')
        w_lbl06b.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl06b, irow, 0)

        w_use_nc = QRadioButton('Use NetCDF')
        helpText_nc = 'Use a NetCDF file comprising spatial and temporal biomass to litter data'
        w_use_nc.setToolTip(helpText_nc)
        grid.addWidget(w_use_nc, irow, 1)
        self.w_use_nc = w_use_nc

        w_use_xlsx = QRadioButton("Excel")
        helpText = 'Use a Excel file comprising a list of grid coordinates'
        w_use_xlsx.setToolTip(helpText)
        grid.addWidget(w_use_xlsx, irow, 2)
        self.w_use_xlsx = w_use_xlsx

        w_inpts_choice = QButtonGroup()
        w_inpts_choice.addButton(w_use_nc)
        w_inpts_choice.addButton(w_use_xlsx)
        self.w_inpts_choice = w_inpts_choice

        # ===========================

        irow += 1
        w_xls_lttr_pshb = QPushButton('Excel file of plant litter')
        w_xls_lttr_pshb.setToolTip('Use a Excel file comprising plant litters')
        w_xls_lttr_pshb.clicked.connect(lambda: self.fetchXlsCoordsFile(True))
        grid.addWidget(w_xls_lttr_pshb, irow, 0)

        w_xls_lttr_fn = QLabel('')  # full path name of Excel plant litter file
        grid.addWidget(w_xls_lttr_fn, irow, 1, 1, 4)
        self.w_xls_lttr_fn = w_xls_lttr_fn

        w_xls_lttr_nrecs = QLabel('')  # number of records
        grid.addWidget(w_xls_lttr_nrecs, irow, 6)
        self.w_xls_lttr_nrecs = w_xls_lttr_nrecs

        # ===========================

        irow += 1
        w_nc_lttr_pshb = QPushButton('NetCDF file of plant litter')
        w_nc_lttr_pshb.setToolTip(helpText_nc)
        w_nc_lttr_pshb.clicked.connect(self.fetchNcLitterFile)
        grid.addWidget(w_nc_lttr_pshb, irow, 0)

        w_nc_lttr_fn = QLabel('')
        grid.addWidget(w_nc_lttr_fn, irow, 1, 1, 4)
        self.w_nc_lttr_fn = w_nc_lttr_fn

        w_nc_extnt = QLabel('')  # number of lat lons
        grid.addWidget(w_nc_extnt, irow, 6)
        self.w_nc_extnt = w_nc_extnt

        # ======== PFTs ==========
        irow += 1
        w_lbl_pfts = QLabel('Plant functional types:')
        w_lbl_pfts.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl_pfts, irow, 0)

        w_combo_pfts = QComboBox()
        for pft in self.pfts:
            w_combo_pfts.addItem(self.pfts[pft])
        grid.addWidget(w_combo_pfts, irow, 1, 1, 2)
        w_combo_pfts.currentIndexChanged[str].connect(self.changePlntFncType)
        self.w_combo_pfts = w_combo_pfts

        w_ave_val = QLabel('')
        w_ave_val.setFixedWidth(STD_FLD_SIZE_180)
        grid.addWidget(w_ave_val, irow, 3)
        self.w_ave_val = w_ave_val

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # command line
        # ============
        irow += 1
        icol = 0
        w_create_files = QPushButton("Create sim files")
        helpText = 'Generate ECOSSE simulation file sets corresponding to ordered HWSD global mapping unit set in CSV file'
        w_create_files.setToolTip(helpText)
        w_create_files.setFixedWidth(STD_BTN_SIZE_100)
        grid.addWidget(w_create_files, irow, icol)
        w_create_files.clicked.connect(self.createSimsClicked)
        self.w_create_files = w_create_files

        icol += 1
        w_auto_spec = QCheckBox('Auto run Ecosse')
        helpText = 'Select this option to automatically run Ecosse'
        w_auto_spec.setToolTip(helpText)
        grid.addWidget(w_auto_spec, irow, icol)
        self.w_auto_spec = w_auto_spec

        icol += 1
        w_run_ecosse = QPushButton('Run Ecosse')
        helpText = 'Select this option to create a configuration file for the spec.py script and run it.\n' \
                   + 'The spec.py script runs the ECOSSE programme'
        w_run_ecosse.setToolTip(helpText)
        w_run_ecosse.setFixedWidth(STD_BTN_SIZE_80)
        w_run_ecosse.clicked.connect(self.runEcosseClicked)
        grid.addWidget(w_run_ecosse, irow, icol)
        self.w_run_ecosse = w_run_ecosse

        icol += 1
        w_clr_psh = QPushButton('Clear')
        helpText = 'Clear reporting window'
        w_clr_psh.setToolTip(helpText)
        w_clr_psh.setFixedWidth(STD_BTN_SIZE_80)
        grid.addWidget(w_clr_psh, irow, icol)
        w_clr_psh.clicked.connect(self.clearReporting)

        icol += 1
        w_save = QPushButton("Save")
        helpText = 'Save configuration and study definition files'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(STD_BTN_SIZE_80)
        grid.addWidget(w_save, irow, icol)
        w_save.clicked.connect(self.saveClicked)

        icol += 1
        w_cancel = QPushButton("Cancel")
        helpText = 'Leaves GUI without saving configuration and study definition files'
        w_cancel.setToolTip(helpText)
        w_cancel.setFixedWidth(STD_BTN_SIZE_80)
        grid.addWidget(w_cancel, irow, icol)
        w_cancel.clicked.connect(self.cancelClicked)

        icol += 1
        w_exit = QPushButton("Exit", self)
        grid.addWidget(w_exit, irow, icol)
        w_exit.setFixedWidth(STD_BTN_SIZE_80)
        w_exit.clicked.connect(self.exitClicked)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.fname_png))
        lbl20.setScaledContents(True)
        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

        # add reporting
        # =============
        bot_hbox = QHBoxLayout()
        w_report = QTextEdit()
        w_report.verticalScrollBar().minimum()
        w_report.setMinimumHeight(225)
        w_report.setMinimumWidth(1000)
        w_report.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        bot_hbox.addWidget(w_report, 1)
        self.w_report = w_report

        sys.stdout = OutLog(self.w_report, sys.stdout)

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch=1)

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        # posx, posy, width, height
        self.setGeometry(200, 100, 690, 250)
        self.setWindowTitle('Global Ecosse Ver 2b - generate sets of ECOSSE input files based on HWSD grid')

        # reads and set values from last run
        # ==================================
        read_config_file(self)

        self.combo10w.currentIndexChanged[str].connect(self.weatherResourceChanged)

    def changePlntFncType(self):
        """
        C
        """
        fname = self.w_nc_lttr_fn.text()
        fetch_nc_litter(self, fname)

    def clearReporting(self):
        """
        C
        """
        self.w_report.clear()

    def keyPress(self, bttnWdgtId):
        """
        C
        """
        pass
        # print("Key was pressed, id is: ", self.w_inpt_choice.id(bttnWdgtId))

    def fetchNcLitterFile(self):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
        """
        fname = self.w_nc_lttr_fn.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'NetCDF files (*.nc)')
        if fname != '':
            self.w_nc_lttr_fn.setText(fname)
            fetch_nc_litter(self, fname)

    def fetchXlsCoordsFile(self, litter_flag=False):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
        """
        if litter_flag:
            fname = self.w_xls_lttr_fn.text()
            fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'Excel files (*.xlsx)')
            if fname != '':
                self.w_xls_lttr_fn.setText(fname)
                check_xls_lttr_fname(fname, self.w_xls_lttr_nrecs)
        else:
            fname = self.w_xls_crds_fn.text()
            fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'Excel files (*.xlsx)')
            if fname != '':
                self.w_xls_crds_fn.setText(fname)
                check_xls_crds_fname(self, fname)

    def weatherResourceChanged(self):

        change_weather_resource(self)

    def studyTextChanged(self):

        studyTextChanged(self)

    def createSimsClicked(self):
        """
        C
        """
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
            return

        # check for spaces
        # ================
        if study.find(' ') >= 0:
            print('*** study name must not have spaces ***')
            return

        generate_sims_from_xls_or_nc(self)

        # run further steps...
        if self.w_auto_spec.isChecked():
            self.runEcosseClicked()

    def runEcosseClicked(self):
        """
        components of the command string have been checked at startup
        """
        if write_runsites_config_file(self):
            # run the make simulations script
            # ===============================
            print('Working dir: ' + getcwd())
            start_time = time()
            cmd_str = self.python_exe + ' ' + self.runsites_py + ' ' + self.runsites_config_file
            system(cmd_str)
            end_time = time()
            print('Time taken: {}'.format(round(end_time - start_time)))
            return

    def saveClicked(self):
        """
        C
        """

        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                save_clicked(self)
                build_and_display_studies(self)

    def cancelClicked(self):
        """
        C
        """
        exit_clicked(self, write_config_flag=False)

    def exitClicked(self):
        """
        exit cleanly
        """
        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                exit_clicked(self)

    def changeConfigFile(self):
        """
        permits change of configuration file
        """
        change_config_file(self)

def main():
    """

    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form()  # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()  # paint form
    sys.exit(app.exec_())  # start event loop


if __name__ == '__main__':
    main()
