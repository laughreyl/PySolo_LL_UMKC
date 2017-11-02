#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Major revisions by Caitlin A Laughrey and Loretta E Laughrey in 2016-2017.
#
#       pvg_acquire.py
#
#       Copyright 2011 Giorgio Gilestro <giorgio@gilest.ro>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

__author__ = "Giorgio Gilestro <giorgio@gilest.ro>"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2011/08/16 21:57:19 $"
__copyright__ = "Copyright (c) 2011 Giorgio Gilestro"
__license__ = "Python"



import os
import wx
import wx.grid as gridlib
import winsound
import subprocess                       # for DAMFileScan110X

import pysolovideoGlobals as gbl
import configurator as cfg
import scrollingWindow as SW
from wx.lib.newevent import NewCommandEvent
ThumbnailClickedEvt, EVT_THUMBNAIL_CLICKED = wx.lib.newevent.NewCommandEvent()

""" ========================================================================================= Create configuration panel
The configuration page.
"""
class cfgPanel(wx.Panel):
    #  ---------------------------------------------------------------------------------------- initialize the cfg panel
    # Uses threading, so copy globals into self
    def __init__(self, parent, size=(800,200)):

        wx.Panel.__init__(self, parent, size=size, name='cfgPanel')
        self.parent = parent
        self.mon_ID = 0                                    # the config page has mon_ID == 0
        cfg.cfg_dict_to_nicknames()

        self.monitors = gbl.cfg_dict[0]['monitors']
        self.panelType = 'thumb'            # always start out with playback thumbnails

        self.makeWidgets()                          # start, stop, and browse buttons
        self.binders()                              # bind event handlers
        self.sizers()                               # Set sizers

    def update_from_dicts(self):
        cfg.cfg_dict_to_nicknames()
        self.monitors = gbl.cfg_dict[0]['monitors']
        self.panelType = 'thumb'            # always start out with playback thumbnails

    # ----------------------------------------------------------------------------------------------- create the widgets
    def makeWidgets(self):
        self.cfgBrowseWidget()                                  # browse to find another config file
        self.tableWidget()                                      # display table of config information
        self.btnsWidget()                                       # buttons
        self.settingsWidget()                                   # adjust thumbnail size and playback rate
        self.videosWidget()                                     # video thumbnails for each monitor in a scrolled window

    # -------------------------------------------------------------- file browser to select different configuration file
    def cfgBrowseWidget(self):
        self.pickCFGtxt = wx.StaticText(self, wx.ID_ANY, 'Configuration File: ')
        self.pickCFGfile = wx.TextCtrl(self, wx.ID_ANY, size=(700,25), style=wx.TE_PROCESS_ENTER, name='cfgname')
        self.pickCFGfile.ChangeValue(self.TopLevelParent.config.filePathName)
        self.pickBrowseBtn = wx.Button(self, wx.ID_ANY, size=(130,25), label='Browse')
        self.pickBrowseBtn.Enable(True)

    # -------------------------------------------------------------------------- summary table of configuration monitors
    def tableWidget(self):
        self.colLabels = ['Monitor', 'Track type', 'Track', 'Source', 'Mask File', 'Output Prefix']
        self.cfgTable = gridlib.Grid(self)
        self.cfgTable.CreateGrid(gbl.monitors, len(self.colLabels))
        self.cfgTable.SetRowLabelSize(0)                                    # no need to show row numbers
        self.cfgTable.EnableEditing(False)                                  # user should not make changes here         TODO: allow changes from cfgTable?
        for colnum in range(0, len(self.colLabels)):
            self.cfgTable.SetColLabelValue(colnum, self.colLabels[colnum])  # apply labels to columns
        self.fillTable()                                                    # fill the table using config info

    # ---------------------------------------------------------------------------------------------------------- buttons
    def btnsWidget(self):
        self.btnAddMonitor = wx.Button(self, wx.ID_ANY, size=(130,25), label='Add Monitor')
        self.btnAddMonitor.Enable(True)

        self.btnSaveCfg = wx.Button(self, wx.ID_ANY, size=(130,25), label='Save Configuration')
        self.btnSaveCfg.Enable(True)

        self.btnStart = wx.Button(self, wx.ID_ANY, size=(130,25), label='Start Acquisition')
        self.btnStart.Enable(True)

        self.btnDAMFS = wx.Button(self, wx.ID_ANY, size=(130,25), label='DAMFileScan110X')                 # start DAMFileScan110X
        self.btnDAMFS.Enable(True)

        # self.btnSCAMP = wx.Button(self, wx.ID_ANY, size=(130,25), label='SCAMP')      # start SCAMP - NOT IN USE
        # self.btnSCAMP.Enable(True)

        self.btnVideos = wx.Button(self, wx.ID_ANY, size=(130,25), label='View Monitors')
        self.btnVideos.Enable(True)

    # ---------------------------------------------------------------------------------------------- scrolled thumbnails
    def videosWidget(self):                         # create scrolling window of monitor panels for playback/consoles
        self.scrolledThumbs = SW.scrollingWindow(self)

    # -----------------------------------------------------------------------------------------  monitor display options
    def settingsWidget(self):
        self.thumbSizeTxt = wx.StaticText(self, wx.ID_ANY, 'Thumbnail Size:')
        self.thumbSize = wx.TextCtrl (self, wx.ID_ANY, str(gbl.thumb_size), style=wx.TE_PROCESS_ENTER, name='thumbSize')

        self.thumbFPSTxt = wx.StaticText(self, wx.ID_ANY, 'Thumbnail FPS:')
        self.thumbFPS = wx.TextCtrl (self, wx.ID_ANY, str(gbl.thumb_fps), style=wx.TE_PROCESS_ENTER, name='thumbFPS')

    # ---------------------------------------------------------------------------------------------------------- binders
    def binders(self):
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeCfgFile,   self.pickCFGfile)           # change configuration
        self.Bind(wx.EVT_BUTTON,        self.onBrowseCfgFile,   self.pickBrowseBtn)         # change configuration
        self.Bind(wx.EVT_BUTTON,        self.onAddMonitor,      self.btnAddMonitor)         # add monitor
        self.Bind(wx.EVT_BUTTON,        self.onStartAcquisition,self.btnStart)              # start data acquisition
        self.Bind(wx.EVT_BUTTON,        self.onSaveCfg,         self.btnSaveCfg)            # save configuration
        self.Bind(wx.EVT_BUTTON,        self.onDAMFileScan110X, self.btnDAMFS)              # start binning pgm
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeThumbFPS,  self.thumbFPS)              # update thumbnail FPS
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeThumbSize, self.thumbSize)             # update thumbnail size
        self.Bind(wx.EVT_BUTTON,        self.onMonitorVideos,   self.btnVideos)             # switch to monitors view

        self.Bind(wx.EVT_LEFT_UP,       self.onLeftUp)          # left clicks on this panel shouldn't do anything
                                                                # this prevents the clicks from being picked up by a
                                                                # monitor panel
        self.Bind(wx.EVT_NAVIGATION_KEY, self.onTab)        # processes changes after tab key press

    # ------------------------------------------------------------------------------------------------- process tab keys
    #                                                         direct binding sends control to the wrong function
    def onTab(self, event):
        if   event.CurrentFocus.Name == 'thumbFPS':              self.onChangeThumbFPS(event)
        elif event.CurrentFocus.Name == 'thumbSize':             self.onChangeThumbSize(event)


    # ----------------------------------------------------------------------------------------------------------- sizers
    def sizers(self):
        self.cfgPanelSizer  = wx.BoxSizer(wx.VERTICAL)          # covers whole page
        self.upperSizer     = wx.BoxSizer(wx.HORIZONTAL)        # config table, browser, and buttons
        self.pickCFGsizer   = wx.BoxSizer(wx.HORIZONTAL)        # config browser
        self.tableSizer     = wx.BoxSizer(wx.VERTICAL)          # for browse button and config table
        self.btnSizer       = wx.BoxSizer(wx.VERTICAL)          # for button controls
        self.lowerSizer     = wx.BoxSizer(wx.VERTICAL)          # scrolled windows and settings
        self.scrolledSizer  = wx.BoxSizer(wx.HORIZONTAL)        # scrolling window of thumbnails
        self.settingsSizer  = wx.BoxSizer(wx.HORIZONTAL)        # fps and size settings

        # ------------------------------------------------------------------------------------ browser control and table
        self.pickCFGsizer.Add(self.pickCFGtxt,      0, wx.ALIGN_LEFT, 2)
        self.pickCFGsizer.Add(self.pickCFGfile,     0, wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.pickCFGsizer.Add(self.pickBrowseBtn,   0, wx.ALIGN_RIGHT, 2)

        self.tableSizer.Add(self.pickCFGsizer,      0, wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.tableSizer.Add(self.cfgTable,          1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 2)

        # ------------------------------------------------------------------------------------------------------ buttons
        self.btnSizer.Add(self.btnSaveCfg,          1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnAddMonitor,       1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnStart,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnVideos,           1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnDAMFS,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
#        self.btnSizer.Add(self.btnSCAMP,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2) - NOT IN USE

        # -------------------------------------------------------------------------------------------------- upper sizer
        self.upperSizer.AddSpacer(40)
        self.upperSizer.Add(self.tableSizer,         0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 2)
        self.upperSizer.Add(self.btnSizer,           0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, 2)

        # --------------------------------------------------------------------------------------- scrolling window sizer
        self.scrolledSizer.Add(self.scrolledThumbs,  1, wx.ALL | wx.ALIGN_CENTER, 2)

        # ---------------------------------------------------------------------------------------------- settings sizer
        self.settingsSizer.Add(self.thumbSizeTxt,    0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.Add(self.thumbSize,       0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.AddSpacer(5)
        self.settingsSizer.Add(self.thumbFPSTxt,     0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.Add(self.thumbFPS,        0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.AddSpacer(5)

        # -------------------------------------------------------------------------------------------------- lower sizer
        self.lowerSizer.Add(self.scrolledSizer,      1, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.lowerSizer.AddSpacer(50)

        self.lowerSizer.Add(self.settingsSizer,      0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)

        # --------------------------------------------------------------------------------------------- main panel sizer
        self.cfgPanelSizer.Add(self.upperSizer,      1, wx.ALL | wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.cfgPanelSizer.Add(self.lowerSizer,      1, wx.ALL | wx.EXPAND | wx.ALIGN_BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 2)

        self.SetSizer(self.cfgPanelSizer)
        self.Layout()

    def onScreenUpdate(self,event):
        event.Skip()                                        # continue processing of event
        self.SetSizer(self.cfgPanelSizer)
        self.scrolledThumbs.EnableScrolling(1, 1)
        self.Update()
        self.Layout()


    # ------------------------------------------------------------------------------------------- catch left mouse click
    def onLeftUp(self, event):
        event.Skip()                # catches left clicks to prevent actions from monPanel

    # ---------------------------------------------------------------------------------------------------- add a monitor
    def onAddMonitor(self, event):
        """
        more than 9 monitors creates issues due to differences between alphabetical and numerical sorting.
        Avoiding problems by not allowing more than 9 monitors.
        """
        gbl.shouldSaveCfg = True
        cfg.cfg_nicknames_to_dicts()            # save current cfg settings to dictionary

        if gbl.monitors >= 9:                   # no more than 9 monitors allowed
            self.TopLevelParent.SetStatusText('Too many monitors.  Cannot add another.')
            winsound.Beep(600, 200)
            return False

        # --------------------------------------------------------------- put new monitor settings in gbl nicknames
        gbl.cfg_dict.append({})                          # add a dictionary to the cfg_dict list
        cfg.cfg_dict_to_nicknames()

        gbl.monitors += 1                                # increase the number of monitors
        gbl.mon_ID = gbl.monitors                        # update the current mon_ID
        gbl.mon_name = 'Monitor%d' % gbl.mon_ID          # update the monitor name

#        if gbl.source_type == 0:                       # create new webcam name if this is a webcam - NOT IN USE
#            gbl.webcams_inuse.append(gbl.mon_name)     # only one webcam is supported, but multiple monitors can use it
#            gbl.webcams += 1
#            gbl.source = 'Webcam%d' % gbl.webcams
#            gbl.source = 'Webcam1'                     # only one webcam is supported, but multiple monitors can use it

        cfg.cfg_nicknames_to_dicts()    # ---------------------------------- save new configuration settings to cfg_dict
        cfg.mon_nicknames_to_dicts(gbl.mon_ID)  # ----------------------------------------- apply new monitor settings to cfg_dict

        self.parent.addMonitorPage()    # -------------------------------------------- add monitor page to notebook

        gbl.mon_ID = gbl.cfg_dict[0]['monitors']                # copy information from last monitor to make this one
        cfg.mon_dict_to_nicknames()
        self.Parent.notebookPages[0].fillTable()                # update the configuration table
        self.scrolledThumbs.refreshGrid()                  # create the thumbnail window
        self.scrolledThumbs.EnableScrolling(1, 1)
        self.Layout()

        gbl.mon_ID = 0                                          # reset ID to configuration page

    # ------------------------------------------------------------------------------------- Save configuration to a file
    def onSaveCfg(self, event):
        cfg.cfg_nicknames_to_dicts()                    # save any new settings to dictionary
        if gbl.mon_ID != 0:
            cfg.mon_nicknames_to_dicts(gbl.mon_ID)      # save current monitor settings to dictionary

        r = self.TopLevelParent.config.cfgSaveAs(self)  # save the configuration
        if r:
            self.pickCFGfile.ChangeValue(r)
            gbl.shouldSaveCfg = False
            gbl.statbar.SetStatusText('Configuration saved.')
            winsound.Beep(300,200)

        else:
            gbl.statbar.SetStatusText('Configuration not saved.')
            winsound.Beep(600,200)

    # -------------------------------------------------------------------------- fill in the summary configuration table
    def fillTable(self):                                                        # using the cfg dictionary
        """
        columns are: 'Monitor', 'Track type', 'Track', 'Source', 'Mask', 'Output'
        row numbers are 0-indexed
        """
        # ------------------------------------------------------ clear the current grid and resize for new configuration
        currentrows = self.cfgTable.GetNumberRows()                             # get number of rows in current table
        self.cfgTable.AppendRows(gbl.monitors, updateLabels=False)              # add new rows to end for each monitor
        self.cfgTable.DeleteRows(0, currentrows, updateLabels=False)            # delete old rows from beginning

        # --------------------------------------------------------------------- fill in table
        for gbl.mon_ID in range(1, gbl.monitors +1):        # one monitor to a row
            cfg.mon_dict_to_nicknames()                     # get this monitor's settings

            # ---------------------------------------------- table uses 0-indexing in following steps
            self.cfgTable.SetCellValue(gbl.mon_ID -1,       0, gbl.mon_name)
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   0,  wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            if gbl.track_type == 0:   track_typeTxt = 'Distance'                 # track type
            elif gbl.track_type == 1: track_typeTxt = 'Virtual BM'               # only distance tracking is implemented
            elif gbl.track_type == 2: track_typeTxt = 'Position'
            else:
                gbl.statbar.SetStatusText('Track_type is out of range.')
                winsound.Beep(600,200)
                track_typeTxt = 'None'

            self.cfgTable.SetCellValue(gbl.mon_ID -1,       1, track_typeTxt)
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   1, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            self.cfgTable.SetCellValue(gbl.mon_ID -1,       2, str(gbl.track))                # all monitors are tracked
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   2, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            if gbl.source is not None:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,       3, gbl.source)                                  # source
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,       3, 'None Selected')


            if gbl.mask_file is not None:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,    4, os.path.split(gbl.mask_file)[1])             # mask_file
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID - 1,   4, 'None Selected')

            if gbl.data_folder is not None:
                outfile = os.path.join(gbl.data_folder, gbl.mon_name)                                 # output file name
                self.cfgTable.SetCellValue(gbl.mon_ID - 1, 5, outfile)
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID - 1,   4, 'None Selected')

        gbl.mon_ID = 0                              # reset ID to configuration value
        self.cfgTable.AutoSize()                    # reset cell size based on contents
        self.Layout()

    # ------------------------------------------------------------------------ Change playback rate (fps) for thumbnails
    def onChangeThumbFPS(self, event):
        input = gbl.correctType(self.thumbFPS.GetValue(), 'thumbFPS')

        if input <> self.thumbFPS:
            if not (type(input) == int or type(input) == float):
                input = gbl.thumb_fps              # don't change the value if input wasn't a number

            gbl.cfg_dict[self.mon_ID]['thumb_fps'] = gbl.thumb_fps = input

            for mon_ID in range(1, gbl.monitors+1):
                self.scrolledThumbs.thumbPanels[mon_ID].monitorPanel.interval = 1000/ input
                if self.scrolledThumbs.thumbPanels[mon_ID].monitorPanel.playTimer.IsRunning():
                    self.scrolledThumbs.thumbPanels[mon_ID].monitorPanel.playTimer.Stop()
                    self.scrolledThumbs.thumbPanels[mon_ID].monitorPanel.playTimer.Start(1000/ input)

            self.thumbFPS.ChangeValue(str(input))
            gbl.shouldSaveCfg = True

        self.scrolledThumbs.clearGrid(self.panelType)
        self.scrolledThumbs.refreshGrid(self.panelType)
        self.onScreenUpdate(event)
    # ---------------------------------------------------------------------------------------- Change size of thumbnails
    def onChangeThumbSize(self, event):
        gbl.shouldSaveCfg = True
        input = gbl.correctType(self.thumbSize.GetValue(), 'thumbSize')
        if type(input) != tuple:
            input = gbl.preview_size                # don't change anything if input was not a tuple

        self.thumbSize.ChangeValue(str(input))
        gbl.cfg_dict[self.mon_ID]['thumb_size'] = gbl.thumb_size = input           # update self & cfg_dict
        cfg.cfg_nicknames_to_dicts()

        for mon_ID in range(1, gbl.monitors+1):
            self.scrolledThumbs.thumbPanels[mon_ID].monitorPanel.panelSize = input

        self.scrolledThumbs.clearGrid(self.panelType)
        self.scrolledThumbs.refreshGrid(self.panelType)
        self.onScreenUpdate(event)

    # ---------------------------------------------------------------- locate a new configuration file using filebrowser
    def onBrowseCfgFile(self, event):
        cfg.cfg_nicknames_to_dicts()                            # save current settings to dictionary

        # ----------------------------------------------------------------------------- select a different config file
        wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                   "All files (*.*)|*.*"  # adding space in here will mess it up!

        dlg = wx.FileDialog(self,
                            message = "Select Configuration File ...",
                            defaultDir = gbl.cfg_path,
                            wildcard = wildcard,
                            style = (wx.FD_OPEN)
                            )

        # load new configuration file
        if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
            self.filePathName = dlg.GetPath()  # get the path from the save dialog
        else:
            winsound.Beep(600,200)
            gbl.statbar.SetStatusText('Configuration file selection failed in cfgPanel.')
            return

        self.changeConfig()             # load the new configuration file

    # --------------------------------------------------------------  new configuration filename entered in text control
    def onChangeCfgFile(self, event):
        cfg.cfg_nicknames_to_dicts()                                # save current settings to dictionary

        # make sure file exists
        self.filePathName = self.TopLevelParent.config.cfgGetFilePathName(self, possiblePathName=self.pickCFGfile.GetValue())

        self.changeConfig()             # load the new configuration file

    # ---------------------------------------------------------------------------------  switch to the new configuration
    def changeConfig(self):             # TODO doesn't erase consoles
        # ------------------------------ see if user wants to save current configuration before changing to another one.
        if gbl.shouldSaveCfg:
            cfg.Q_wantToSave(self)                                  # asks user if config should be saved, & if so, saves

        gbl.shouldSaveCfg = False

        gbl.cfg_dict = [gbl.cfg_dict[0], gbl.cfg_dict[1]]       # remove all but monitors 1 from dictionary

        self.GrandParent.config.loadConfigFile(self.filePathName)   # load the new file
        gbl.mon_ID = 1
        cfg.cfg_dict_to_nicknames()                             # copy config parameters to nicknames
        cfg.mon_dict_to_nicknames()                             # copy monitor 1 parameters to nicknames

        # -------------------------------------------------------------------- clear out previous scrolled window panels
        self.scrolledThumbs.clearGrid(self.panelType)

        # -------------------------------------------------------- load new configuration into table and scrolled window
        self.fillTable()                                    # put new configuration into the table
        self.pickCFGfile.ChangeValue(self.filePathName)        # update the config file text control

        cfg.cfg_dict_to_nicknames()                         # load configuration page parameters
        self.fillTable()                                    # update the configuration table
        self.scrolledThumbs.refreshGrid()              # update and start the thumbnails window
        self.parent.repaginate()                            # add monitor pages to notebook & end on config page

        self.scrolledThumbs.EnableScrolling(1, 1)
        self.Layout()

    # ------------------------------------------------------------------------------  start tracking and collecting data
    def onStartAcquisition(self, event=None):
        """
        replace scrolled thumbnails with progress windows
        start tracking
        """
        if gbl.shouldSaveCfg:
            answer = cfg.Q_wantToSave('go')    # ask about saving configuration
            if answer <> 'go':      # --------------------------------------------- user cancelled acquisition request
                return

        gbl.shouldSaveCfg = False
        gbl.statbar.SetStatusText('Tracking %d Monitors' % gbl.monitors)
        self.acquiring = True

        self.thumbFPSTxt.Hide()
        self.thumbFPS.Hide()

        self.scrolledThumbs.clearGrid(self.panelType)
        self.panelType = 'console'
        self.scrolledThumbs.refreshGrid(self.panelType)   # replace thumbnails with progress consoles and start tracking

        self.scrolledThumbs.EnableScrolling(1, 1)
        self.Layout()

    # ------------------------------------------------------------- restore monitor thumbnail views after acquiring data
    def onMonitorVideos(self, event):

        self.Parent.notebookPages[0].scrolledThumbs.clearGrid(self.panelType)
        self.panelType = 'thumb'
        self.Parent.notebookPages[0].scrolledThumbs.refreshGrid(self.panelType)

        self.scrolledThumbs.EnableScrolling(1, 1)
        self.SetSizer(self.cfgPanelSizer)
        self.Layout()

    # -------------------------------------------------------------------------------------------- start DAMFileScan110X
    def onDAMFileScan110X(self, event):

        cmd = os.path.join(gbl.exec_dir, 'DAMFileScan110X', 'DAMFileScan110.exe')
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()

        self.scrolledThumbs.EnableScrolling(1, 1)
        self.Layout()


# ------------------------------------------------------------------------------------------ Stand alone test code
#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, None, id=wx.ID_ANY, size=(1000,200))

        config = cfg.Configuration(self, gbl.cfg_path)
        frame_acq = cfgPanel(self)  # Create the main window.
        app.SetTopWindow(frame_acq)

        print('done.')


if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#

