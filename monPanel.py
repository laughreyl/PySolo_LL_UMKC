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


import wx                               # GUI controls
import os
import winsound
import wx.lib.masked as masked
from filebrowser_LL import filebrowser_LL, folderbrowser_LL
from wx.lib.masked import NumCtrl

import configurator as cfg
import videoMonitor as VM
import pysolovideoGlobals as gbl

# TODO:  first time opened, preview panel is doubled

""" ================================================================================= Create monitor configuration panel
"""
class monPanel(wx.Panel):
    """
    A monitor configuration page.
    cfg settings won't change unless configuration is changed, which will kill this object
    mon settings may change due to threading, so these settings will be assigned here and cfg_dict updated 
        after any changes
    """
    # ------------------------------------------------------------------------ initialize the monitor configuration page
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(640,480), name=gbl.mon_name)

        self.parent =           parent
        self.mon_ID =           gbl.mon_ID

        self.update_from_dicts()                      # copy all configuration parameters to local variables

        gbl.shouldSaveMask =   False
        gbl.shouldSaveCfg =    False

        self.widgets()
        self.binders()
        self.sizers()

    def update_from_dicts(self):
        cfg.cfg_dict_to_nicknames()  # update program configuation
        cfg.mon_dict_to_nicknames()  # load information for current monitor

        self.monitors = gbl.monitors
        self.mon_name = gbl.mon_name
        self.source = gbl.source
        self.source_type = gbl.source_type
        self.source_fps = gbl.source_fps
        self.source_mmsize = gbl.source_mmsize
        self.start_datetime = gbl.start_datetime
        #        self.issdmonitor =      gbl.issdmonitor        # NOT IN USE
        self.preview_size = gbl.preview_size
        self.preview_fps = gbl.preview_fps
        self.preview_font = gbl.preview_font
        self.preview_RGBcolor = gbl.preview_RGBcolor
        self.line_thickness = gbl.line_thickness
        self.mask_file = gbl.mask_file
        self.video_on = gbl.video_on
        self.data_folder = gbl.data_folder
        self.track_type = gbl.track_type
        self.track = gbl.track

    # order of creation dictates order of tab movement
    def widgets(self):

        # ------------------------------------------------------------------------------------------ video preview panel
        # the video is not applied to this panel until the page is in focus.
        self.previewPanel = VM.monitorPanel(self, mon_ID=self.mon_ID, panelType='preview', loop=True)   # TODO: not displaying preview panel at start

        # -------------------------------------------------------------------------------------------- video display options
        self.previewFontLabel = wx.StaticText(self, wx.ID_ANY, 'preview font =')         # --------- preview video fps
        self.previewFont = wx.TextCtrl(self, wx.ID_ANY, str(self.preview_font),
                                              style=wx.TE_PROCESS_ENTER, name='previewFont')

        self.previewRGBColorLabel = wx.StaticText(self, wx.ID_ANY, 'preview color (RGB) =')         # --------- preview video fps
        self.previewRGBColor = wx.TextCtrl(self, wx.ID_ANY, str(self.preview_RGBcolor),
                                              style=wx.TE_PROCESS_ENTER, name='previewRGBColor')

        self.lineThicknessLabel = wx.StaticText(self, wx.ID_ANY, 'ROI line thickness =')  # --------- preview ROI line thickness
        self.lineThickness = wx.TextCtrl(self, wx.ID_ANY, str(self.line_thickness),
                                              style=wx.TE_PROCESS_ENTER, name='lineThickness')

        self.previewSizeLabel = wx.StaticText(self, wx.ID_ANY, 'frame size =')           # ------ preview frame size
        self.previewSize = wx.TextCtrl (self, wx.ID_ANY, str(self.preview_size),
                                            style=wx.TE_PROCESS_ENTER, name='previewSize')

        self.previewFPSLabel = wx.StaticText(self, wx.ID_ANY, 'preview fps =')         # --------- preview video fps
        self.previewFPS = wx.TextCtrl(self, wx.ID_ANY, str(self.preview_fps),
                                              style=wx.TE_PROCESS_ENTER, name='previewFPS')




        # ------------------------------------------------------------------------------------------- Date & Time
        # I prefer the wx.datepickerctrl and masked.timectrl widgets, but the date and time handling in wxDateTime is
        # buggy.
        #       1. if the month didn't change, wxDateTime.GetValue() fails
        #       2. wx.DateTime.AddTS() resets the date to 1/1/1970
        #
        # Therefore, dates and times are converted to python datetime for manipulation.

        self.txtDate = wx.StaticText(self, wx.ID_ANY, "Date: ")                        # ---------------- start date
        wxdt = gbl.pydatetime2wxdatetime(self.start_datetime)
        self.startDate = wx.DatePickerCtrl(self, wx.ID_ANY, dt=wxdt,
                                            style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.TE_PROCESS_ENTER, name='startDate')


        self.txtTime = wx.StaticText(self, wx.ID_ANY, 'Time (24-hr):  ')                 # ---------------- start time
        self.btnSpin = wx.SpinButton(self, wx.ID_ANY, wx.DefaultPosition, (-1, 20), wx.SP_VERTICAL)
        starttime = gbl.wxdatetime2timestring(wxdt)
        self.startTime = masked.TimeCtrl(self, wx.ID_ANY, value=starttime,
                                          name='time: \n24 hour control', fmt24hr=True,
                                          spinButton=self.btnSpin, style=wx.TE_PROCESS_ENTER)

        # -------------------------------------------------------------------------------------- source video attributes
        self.txtSourceMMSize = wx.StaticText(self, wx.ID_ANY, 'Frame Size (mm)')  # ---------- source field size in mm
        self.sourceMMSize = wx.TextCtrl(self, wx.ID_ANY, str(self.source_mmsize),
                                        style=wx.TE_PROCESS_ENTER, name='sourceMMSize')

        self.txtSourceFPS = wx.StaticText(self, wx.ID_ANY, 'Speed (fps) =')  # ---------------------------- source fps
        self.sourceFPS = wx.TextCtrl(self, wx.ID_ANY, str(self.source_fps),
                                     style=wx.TE_PROCESS_ENTER, name='sourceFPS')


        """     NOT IN USE
    # ------------------------------------------------------------------------------------------------ activate tracking
        self.trackBox = wx.CheckBox(self, wx.ID_ANY, 'Activate Tracking')
        self.trackBox.Enable(True)
        self.trackBox.ChangeValue(str(self.track))

    # ---------------------------------------------------------------------------------------- sleep deprivation monitor
        self.isSDMonitor = wx.CheckBox(self, wx.ID_ANY, 'Sleep Deprivation Monitor')
        self.isSDMonitor.Enable(True)
        self.isSDMonitor.ChangeValue(str(self.issdmonitor))

    # ---------------------------------------------------------------------------------------------------- tracking type
        self.trackChoice = [(wx.RadioButton(self, wx.ID_ANY, 'Activity as distance traveled', style=wx.RB_GROUP)),
                            (wx.RadioButton(self, wx.ID_ANY, 'Activity as midline crossings count')),
                            (wx.RadioButton(self, wx.ID_ANY, 'Only position of flies'))]

        for count in range(0, len(self.trackChoice)):
            self.trackChoice[count].Enable(True)
            if self.trackType == count:
                self.trackChoice[count].ChangeValue(True)
            else:
                self.trackChoice[count].ChangeValue(False)
        """

        # -------------------------------------------------------------------------------------------- instructional diagram
        self.diagram = wx.Bitmap(os.path.join(gbl.exec_dir, 'maskmakerdiagram.bmp'), wx.BITMAP_TYPE_BMP)
        self.diagramctl = wx.StaticBitmap(self, -1, self.diagram)

        # --------------------------------------------------------------------------------------- ROI Coordinates Input Grid
        self.instruction = wx.StaticText(self, wx.ID_ANY,
                'Click on video to select top left coordinates.')

        self.rowLabels = [wx.StaticText(self, -1, ' '),
                           wx.StaticText(self, -1, 'Number'),  # row labels
                           wx.StaticText(self, -1, 'Top Left'),
                           wx.StaticText(self, -1, 'Span'),
                           wx.StaticText(self, -1, 'Gap'),
                           wx.StaticText(self, -1, 'Tilt')
                           ]
        self.X = []
        self.Y = []
        self.X.append(wx.StaticText(self, wx.ID_ANY, "Columns (X)"))  # column header for columns
        self.Y.append(wx.StaticText(self, wx.ID_ANY, "Rows (Y)"))  # column header for rows
        for cnt in range(0, 5):
            self.X.append(NumCtrl(self, wx.ID_ANY, 0, name='xy'))
            self.Y.append(NumCtrl(self, wx.ID_ANY, 0, name='xy'))

        # ------------------------------------------------------------------------------------ mask generator & save buttons
        self.btnMaskGen = wx.Button(self, wx.ID_ANY, label="Generate Mask", size=(130, 25))
        self.btnMaskGen.Enable(True)

        self.btnSaveMask = wx.Button(self, wx.ID_ANY, label="Save Mask", size=(130, 25))
        self.btnSaveMask.Enable(True)

        # ---------------------------------------------------------------------------------------  Save Configuration Button
        self.btnSaveCfg = wx.Button(self, wx.ID_ANY, label='Save Configuration', size=(130, 25))
        if self.source != '':
            self.btnSaveCfg.Enable(True)  # don't allow save if no source is selected
        else:
            self.btnSaveCfg.Enable(False)

        # ---------------------------------------------------------------------------------------  Delete Monitor Button

        self.btnRemoveMonitor = wx.Button(self, wx.ID_ANY, label='Delete Monitor', size=(130, 25))
        if self.monitors == 1:  # don't allow last monitor to be deleted
            self.btnRemoveMonitor.Enable(False)
        else:
            self.btnRemoveMonitor.Enable(True)

        # -------------------------------------------------------------------------------------------------------- source
        self.txt_source = wx.StaticText(self, wx.ID_ANY, "Source:  ")
        if self.source is not None:  # get current source
            self.currentSource = wx.TextCtrl(self, wx.ID_ANY, self.source, style=wx.TE_READONLY, name='currentSource')
        else:
            self.currentSource = wx.TextCtrl(self, wx.ID_ANY, 'None Selected', style=wx.TE_READONLY)

            # -------------------------------------------------------------------------------  Webcam selection combobox
            #        if len(gbl.webcams_inuse) >= gbl.webcams:                          # only one webcam implemented at this time
            #            self.WebcamsList = ['No more webcams available.']
            #        else:
            #        self.WebcamsList = ['Webcam %s' % (int(w) + 1) for w in range(gbl.webcams)]
            #        self.WebcamsList = ['Webcam 1']

        # ------------------------------------------------------------------------------------------- source options
        self.source_IDs = [wx.ID_ANY, wx.ID_ANY, wx.ID_ANY]
        self.sources = ['placeholder for webcams',
                        #                         (wx.ComboBox(self, id=self.source_IDs[0], choices=self.WebcamsList, name='sources0',  # webcam
                        #                                     style=wx.EXPAND | wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)),
                        (filebrowser_LL(self, id=self.source_IDs[1],                    # video file - source[1]
                                          name='sources1',
                                          btn_label='Browse', label_label='',
                                          message='Choose a video file',
                                          defaultDir=self.data_folder,
                                          defaultFile='',
                                          wildcard='*.*', dlg_style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                                          changeCallback=self.onChangeSource1
                                          )),
                        (folderbrowser_LL(self, id=self.source_IDs[2],
                                          name='sources2',                              # folder of images - source[2]
                                          btn_label='Browse', label_label='',
                                          message='Choose a video file',
                                          defaultDir=self.data_folder,
                                          changeCallback=self.onChangeSource2
                                         ))
                        ]
        if self.source_type == 1: self.sources[1].textbox.ChangeValue(str(self.source))
        elif self.source_type ==2: self.sources[2].textbox.ChangeValue(str(self.source))


        # --------------------------------------------------------------------------------  source type radio buttons
        #        self.rbs = [(wx.RadioButton(self, wx.ID_ANY, 'Camera', style=wx.RB_GROUP)),
        self.rbs = ['placeholder for camera radiobutton',
                    (wx.RadioButton(self, wx.ID_ANY, 'File')),
                    (wx.RadioButton(self, wx.ID_ANY, 'Folder'))
                    ]

        # ------------------------------------------------------------------------------------------------ mask file browser
        wildcard = 'PySolo Video mask file (*.msk)|*.msk|' \
                   'All files (*.*)|*.*'  # adding space in here will mess it up!

        if self.mask_file is None:
            startDirectory = self.data_folder  # Default directory for file dialog startup
            initialValue = 'None Selected'
        elif os.path.isfile(self.mask_file):
            startDirectory = os.path.split(self.mask_file)[0]  # Default directory for file dialog startup
            initialValue = self.mask_file
        else:
            startDirectory = self.data_folder  # Default directory for file dialog startup
            initialValue = 'None Selected'

        self.pickMaskBrowser = filebrowser_LL(self, id=wx.ID_ANY,
                                          name='pickMaskBrowser',
                                          btn_label='Browse', label_label='Mask File: ',
                                          message='Choose a mask file',
                                          defaultDir=startDirectory,
                                          defaultFile=initialValue,
                                          wildcard=wildcard, dlg_style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                                          changeCallback=self.onChangeMask)
        self.pickMaskBrowser.textbox.ChangeValue(str(self.mask_file))

        # -------------------------------------------------------------------------------------------- output folder browser
        if self.data_folder is None:
            startDirectory = self.data_folder = gbl.cfg_path  # Default directory is config directory
        elif os.path.isdir(self.data_folder):
            startDirectory = self.data_folder  # Default directory from config file
        else:
            startDirectory = self.data_folder = gbl.cfg_path  # Default directory is config directory

        self.pickOutputBrowser = folderbrowser_LL(self, id=wx.ID_ANY,
                                               name='pickOutputBrowser',
                                               btn_label='Browse', label_label='Output Folder:  ',
                                               message='Choose an output folder',
                                               defaultDir=self.data_folder,
                                               changeCallback=self.onChangeOutput)
        self.pickOutputBrowser.textbox.ChangeValue(str(self.data_folder))

        # ------------------------------------------------------------------ turns on frame-by-frame video for debugging
        self.videoOn = wx.CheckBox(self, id=wx.ID_ANY, label='Watch Video Tracking',
                                   name='videoOn')  # ---- watch video frame-by-frame while tracking
        self.videoOn.SetValue(self.video_on)

    def binders(self):  # -------------------------------------------------------------------------------- Event Binders

#        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeRb,               self.rbs[0])       # webcams NOT IN USE
#        self.Bind(wx.EVT_COMBOBOX,      self.onChangeSource0,          self.sources[0])       # Webcams NOT IN USE
#        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeTrackType,        self.trackChoice[0])   # only track distance is used
#        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeTrackType,        self.trackChoice[1])
#        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeTrackType,        self.trackChoice[2])
        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeRb,               self.rbs[1])
        self.Bind(wx.EVT_RADIOBUTTON,   self.onChangeRb,               self.rbs[2])
        self.Bind(wx.EVT_BUTTON,        self.onSaveCfg,                self.btnSaveCfg)
        self.Bind(wx.EVT_BUTTON,        self.onRemoveMonitor,          self.btnRemoveMonitor)
        self.Bind(wx.EVT_BUTTON,        self.onMaskGen,                self.btnMaskGen)
        self.Bind(wx.EVT_BUTTON,        self.onSaveMask,               self.btnSaveMask)
        self.Bind(wx.EVT_CHECKBOX,      self.onChangeVideoOn,          self.videoOn)

        # ------------------------------------------------------------------------------------- process enter keys
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangePreviewFont,      self.previewFont)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangePreviewRGBColor,  self.previewRGBColor)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeLineThickness,    self.lineThickness)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangePreviewSize,      self.previewSize)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangePreviewFPS,       self.previewFPS)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeSourceMMSize,     self.sourceMMSize)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeSourceFPS,        self.sourceFPS)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeDate,             self.startDate)
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeTime,             self.startTime)
#        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeSource1,          self.sources[1])
#        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeSource2,          self.sources[2])
#        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeMask,             self.pickMaskBrowser)
#        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeOutput,           self.pickOutputBrowser)

        # -------------------------------------------------------------------------------- process other navigation keys


        self.previewFont.Bind(wx.EVT_KILL_FOCUS,        self.onChangePreviewFont)
        self.previewRGBColor.Bind(wx.EVT_KILL_FOCUS,    self.onChangePreviewRGBColor)
        self.lineThickness.Bind(wx.EVT_KILL_FOCUS,      self.onChangeLineThickness)
        self.previewSize.Bind(wx.EVT_KILL_FOCUS,        self.onChangePreviewSize)
        self.previewFPS.Bind(wx.EVT_KILL_FOCUS,         self.onChangePreviewFPS)
        self.sourceMMSize.Bind(wx.EVT_KILL_FOCUS,       self.onChangeSourceMMSize)
        self.sourceFPS.Bind(wx.EVT_KILL_FOCUS,          self.onChangeSourceFPS)
        self.startDate.Bind(wx.EVT_KILL_FOCUS,          self.onChangeDate)
        self.startTime.Bind(wx.EVT_KILL_FOCUS,          self.onChangeTime)

    def sizers(self):
        self.mainSizer              = wx.BoxSizer(wx.HORIZONTAL)                                #   Main
        self.right_Sizer            = wx.BoxSizer(wx.VERTICAL)                                  #   |   right_
        self.sb_selectsource        = wx.StaticBox(self, wx.ID_ANY, 'Select Source')            #   |   |   source selection text
        self.sbSizer_selectsource   = wx.StaticBoxSizer(self.sb_selectsource, wx.VERTICAL)      #   |   |   select box
        self.sourceGridSizer        = wx.FlexGridSizer(5, 2, 2, 2)                              #   |   |   |   |   grid of rbs & sources
        self.sourceGridSizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.sourceGridSizer.AddGrowableCol(1)
        self.sb_maskNoutput         = wx.StaticBox(self, wx.ID_ANY, '')                         #   |   |   monitor selection text
        self.sbSizer_maskNoutput    = wx.StaticBoxSizer(self.sb_maskNoutput, wx.VERTICAL)       #   |   |   |   select box
        self.maskBrowserSizer       = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   |   mask browser
        self.outputDirSizer         = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   |   output dir browser
        self.right_MiddleSizer      = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   right_ middle
        self.sb_timeSettings        = wx.StaticBox(self, wx.ID_ANY, 'Time Settings')            #   |   |   |   time settings text
        self.sbSizer_timeSettings   = wx.StaticBoxSizer(self.sb_timeSettings, wx.VERTICAL)      #   |   |   |   time settings box
        self.dt_Sizer               = wx.FlexGridSizer(3, 2, 2, 2)                              #   |   |   |   |   |   datetimefps widgets
        self.sb_SourceParms         = wx.StaticBox(self, wx.ID_ANY, 'Source Parameters')        #   |   |   |   source parameters text
        self.sbSizer_SourceParms    = wx.StaticBoxSizer(self.sb_SourceParms, wx.VERTICAL)       #   |   |   |   source parameters box
        self.source_Sizer           = wx.FlexGridSizer(2, 2, 2, 2)                              #   |   |   |   |   |   source options widgets
#        self.sb_trackingParms       = wx.StaticBox(self, wx.ID_ANY, 'Tracking Parameters')     #   |   |   |   tracking parameters text
#        self.sbSizer_trackingParms  = wx.StaticBoxSizer(self.sb_trackingParms, wx.VERTICAL)    #   |   |   tracking parameters box
#        self.trackOptionsSizer      = wx.BoxSizer(wx.VERTICAL)                                 #   |   |   |   |   |   tracking options widgets
        self.calcbox_sizer          = wx.BoxSizer(wx.VERTICAL)                                  #   |   |   |   |   |   calculations widgets
#        self.right_BottomSizer      = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   right_ bottom
        self.sb_MaskGen             = wx.StaticBox(self, wx.ID_ANY, 'Mask Generator')           #   |   |   |   mask generator text
        self.sbSizer_MaskGen        = wx.StaticBoxSizer(self.sb_MaskGen, wx.HORIZONTAL)         #   |   |   |   mask generator box
        self.diagramSizer           = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   diagram
        self.tableSizer             = wx.BoxSizer(wx.VERTICAL)                                  #   |   |   |   table
        self.coordSizer             = wx.FlexGridSizer(6, 3, 1, 5)                              #   |   |   |   |   cooridnates
        self.button_sizer           = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   |   buttons
#        self.left_Sizer             = wx.BoxSizer(wx.VERTICAL)                                 #   |   left_
        self.sb_Monitor             = wx.StaticBox(self, wx.ID_ANY, self.mon_name)              #   |   |   |   mask generator text
        self.sbSizer_Monitor        = wx.StaticBoxSizer(self.sb_Monitor, wx.VERTICAL)           #   |   |   |   mask generator box
#        self.titleSizer             = wx.BoxSizer(wx.HORIZONTAL)                               #   |   |   Monitor title
        self.videoSizer             = wx.BoxSizer(wx.VERTICAL)                                  #   |   |   video panel
        self.settingsSizer          = wx.FlexGridSizer(2, 6, 2, 2)                              #   |   |   preview settings
        self.saveNdeleteSizer       = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   save and delete buttons

        # ------------------------------------------------------------------------------ left_ Side  Video Preview Panel
        #                                      this sizer saves the spot in left_Sizer in case video is changed later
        self.videoSizer.Add(self.previewPanel,                          1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL |
                                                                                    wx.ALIGN_CENTER_VERTICAL, 5)

        self.settingsSizer.Add(self.previewFontLabel,                   0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewFont,                        0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewRGBColorLabel,               0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewRGBColor,                    0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.lineThicknessLabel,                 0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.lineThickness,                      0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewSizeLabel,                   0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewSize,                        0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewFPSLabel,                    0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewFPS,                         0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.AddSpacer(10)
        self.settingsSizer.Add(self.videoOn,                            0, wx.ALL, 5)

        self.saveNdeleteSizer.Add(self.btnSaveCfg,                      1, wx.ALL, 5)
        self.saveNdeleteSizer.Add(self.btnRemoveMonitor,                1, wx.ALL, 5)


 #       self.sbSizer_Monitor.Add(self.title,                                 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 1)
        self.sbSizer_Monitor.Add(self.settingsSizer,                         0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        self.sbSizer_Monitor.Add(self.saveNdeleteSizer,                      0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.ALIGN_BOTTOM, 5)
        self.sbSizer_Monitor.Add(self.videoSizer,                            1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, 5)


# ------------------------------------------------------------------------------------------------------------right_ SIDE
    # -------------------------------------------------------------------------------------------- select source box

        self.sourceGridSizer.Add(self.txt_source,                       0, wx.ALL | wx.LEFT,     5)
        self.sourceGridSizer.Add(self.currentSource,                    1, wx.ALL | wx.EXPAND,   5)

        for count in range(1, len(self.rbs)):                   # -------- source 0 (webcams) is not being used
            self.sourceGridSizer.Add(self.rbs[count],                   0, wx.ALL | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.sourceGridSizer.Add(self.sources[count],               1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        self.sbSizer_selectsource.Add(self.sourceGridSizer,             1, wx.ALL | wx.EXPAND,   5)

        # -------------------------------------------------------------------------- mask browser, output folder browser
        self.sbSizer_maskNoutput.Add(self.pickMaskBrowser,              1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        self.sbSizer_maskNoutput.Add(self.pickOutputBrowser,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        # --------------------------------------------------------------------------- time, source, tracking buttons row
        # ------------------------------------------------------------------------ date / time  grid
        self.dt_Sizer.Add(self.txtDate,                                 0, wx.ALL, 5)
        self.dt_Sizer.Add(self.startDate,                               0, wx.ALL, 5)

        self.dt_Sizer.Add(self.txtTime,                                 0, wx.ALL, 5)
        self.addWidgets(self.dt_Sizer, [self.startTime, self.btnSpin])

        # fill video start date and time box
        self.sbSizer_timeSettings.Add(self.dt_Sizer,                    0, wx.ALL, 5)

        # -------------------------------------------------------------------------------- source options
        self.source_Sizer.Add(self.txtSourceMMSize,               0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.source_Sizer.Add(self.sourceMMSize,                  0, wx.ALL | wx.ALIGN_LEFT, 5)

        self.source_Sizer.Add(self.txtSourceFPS,                  0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.source_Sizer.Add(self.sourceFPS,                     0, wx.ALL | wx.ALIGN_LEFT, 5)

        self.sbSizer_SourceParms.Add(self.source_Sizer)

        """ NOT IN USE
        # -------------------------------------------------------------------------------- tracking options
        self.trackOptionsSizer.Add(self.trackBox,                       0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.trackOptionsSizer.Add(self.isSDMonitor,                    0, wx.ALL | wx.ALIGN_LEFT, 5)

        for count in range(0, len(self.trackChoice)):
            self.calcbox_sizer.Add(self.trackChoice[count],             0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.trackOptionsSizer.Add(self.calcbox_sizer,                  0, wx.ALL | wx.ALIGN_LEFT, 5)

        # fill tracking box
        self.sbSizer_trackingParms.Add(self.trackOptionsSizer,          0, wx.ALL, 5)
        """

        # fill middle row
        self.right_MiddleSizer.Add(self.sbSizer_timeSettings,           2, wx.ALL | wx.EXPAND, 5)
        self.right_MiddleSizer.Add(self.sbSizer_SourceParms,                 2, wx.ALL | wx.EXPAND, 5)
#        self.right_MiddleSizer.Add(self.sbSizer_trackingParms,          2, wx.ALL | wx.EXPAND, 5)
        # ---------------------------------------------------------------------------------------------- mask generator
        self.diagramSizer.Add(self.diagramctl,                          0, wx.ALL | wx.ALIGN_CENTER, 2)


        for row in range(0, len(self.rowLabels)):
            self.coordSizer.Add(self.rowLabels[row],                    1, wx.ALL | wx.EXPAND, 5)  # column headers
            self.coordSizer.Add(self.X[row],                            1, wx.ALL | wx.EXPAND, 5)  # X column entries
            self.coordSizer.Add(self.Y[row],                            1, wx.ALL | wx.EXPAND, 5)  # Y column entries

        self.button_sizer.Add(self.btnMaskGen,                          1, wx.ALL, 5)
        self.button_sizer.Add(self.btnSaveMask,                         1, wx.ALL, 5)

        self.tableSizer.Add(self.instruction,                           0, wx.ALL | wx.ALIGN_BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.tableSizer.Add(self.coordSizer,                            1, wx.ALL | wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 2)
        self.tableSizer.Add(self.button_sizer,                          0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)


        # ------------------------------------------------------------------------------------------ fill right_ bottom
        self.sbSizer_MaskGen.Add(self.tableSizer,                     0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.sbSizer_MaskGen.Add(self.diagramSizer,                   0, wx.ALL | wx.ALIGN_CENTER, 2)

        self.right_Sizer.Add(self.sbSizer_selectsource,               1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.sbSizer_maskNoutput,                1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.right_MiddleSizer,                  1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.sbSizer_MaskGen,                    1, wx.ALL | wx.EXPAND,   5)

   # ------------------------------------------------------------------------------------------- right_ & left_ sides
        self.mainSizer.Add(self.sbSizer_Monitor,                       1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, 2)
        self.mainSizer.Add(self.right_Sizer,                           1, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 2)

        self.SetSizer(self.mainSizer)
        self.Layout()

    def addWidgets(self, mainSizer ,widgets):       # ---------------------------------------  used for datetime widgets

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for widget in widgets:
            if isinstance(widget, wx.StaticText):
                sizer.Add(widget,                           0, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, 1)
            else:
                sizer.Add(widget,                           0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 1)
        mainSizer.Add(sizer)

    def onRemoveMonitor(self, event):  # ------------------------------------------------------   Remove current monitor
        gbl.shouldSaveCfg = True

        if self.monitors < 1:                                                    # don't remove the last monitor
            self.TopLevelParent.SetStatusText('Cannot remove last monitor.')
            winsound.Beep(600, 200)
            return False

        old_mon = self.mon_ID                          # keep track of monitor to be removed

        gbl.cfg_dict.pop(old_mon)                         # delete monitor from dictionary; renumbers list automatically

#        if self.source[0:6] == 'Webcam':                  # if needed change global copy of number of webcams
#            gbl.webcams -= 1  # change number of webcams
#            gbl.webcams_inuse.remove(self.mon_name)       # remove name from webcam list

        # ------------------------------------------------------------------------ reset higher numbered monitors' names
        for mon_count in range(old_mon, self.monitors):
            gbl.cfg_dict[mon_count]['mon_name'] = 'Monitor%d' % (mon_count)  # change monitor names
#            if gbl.cfg_dict[mon_count]['source'][0:6] == 'Webcam':
#                gbl.cfg_dict[mon_count]['source'][0:6] = 'Webcam%d' % mon_count    # rename webcam    ->  only 1 webcam currently supported

        gbl.monitors -= 1  # ------------------------------------------------------ Change global settings
        if old_mon > gbl.monitors:          # change current monitor number only if last monitor was deleted
            self.mon_ID = old_mon - 1

        gbl.mon_ID = self.mon_ID

        cfg.cfg_nicknames_to_dicts()       # -------------------------- update config dictionary to change # of monitors
        cfg.mon_dict_to_nicknames()         # ------------------------------------------------- get new monitor settings

        self.parent.repaginate()            # this will delete the notebook pages and recreate the notebook

    def onSaveCfg(self, event):
        if gbl.shouldSaveMask:
            self.Q_shouldSaveMask(self.mon_ID)      # if masked changed, see if it should be saved.

        cfg.cfg_nicknames_to_dicts()  # -------------------------------------------------- update config dictionary
        r = self.TopLevelParent.config.cfgSaveAs(self)
        if r:                                                               # TODO: progress indicator of some sort?
            self.TopLevelParent.SetStatusText('Configuration saved.')
            winsound.Beep(300,200)
        else:
            self.TopLevelParent.SetStatusText('Configuration not saved.')
            winsound.Beep(600, 200)

    def clearVideo(self):
        # don't save nicknames, you don't know whose been using them
        # -------------------------------------------------------------------------------------- stop old monitor panel  TODO: Update mask & settings
        try:    # ------ object may have been deleted earlier
            self.previewPanel.keepPlaying = False
            self.previewPanel.playTimer.Stop()
            self.previewPanel.Hide()
            self.previewPanel.Destroy()                  # panel must be destroyed or it will linger and cause flick
        except:
            gbl.statbar.SetStatusText('Preview panel can''t be cleared.')
            winsound.Beep(600,200)
            pass

        self.videoSizer.Clear()

    def refreshVideo(self):
        # if new video has different size than previous, mask may be outside the image and won't show in previewpanel
        try: self.rois
        except: self.rois = []
        self.previewPanel = VM.monitorPanel(self, mon_ID=self.mon_ID, panelType='preview', loop=True, rois=self.rois)

        self.previewPanel.PlayMonitor()
        self.previewPanel.playTimer.Start()                                         # PlayMonitor() can't start timer
        self.videoSizer.Clear(True)                                 # removes old previewPanel and allows resize
        self.videoSizer.SetMinSize(self.preview_size)
        self.videoSizer.Add(self.previewPanel, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        if self.previewPanel.playTimer.IsRunning():
            self.previewPanel.playTimer.Stop()
            self.previewPanel.playTimer.Start(1000 / float(self.previewFPS.GetValue()))

        self.SetSizer(self.mainSizer)
        self.Layout()

    def screenUpdate(self, event):
        # does not update preview panel.  call refreshVideo() to do that.
        try: event.Skip()                                        # continue processing of event
        except: pass
        self.SetSizer(self.mainSizer)
        self.Update()
        self.Layout()                                       # refresh the display

    def onChangePreviewFont(self, event):
        input = gbl.correctType(self.previewFont.GetValue(), 'preview_font')        # get new value

        if not (type(input) == int or type(input) == float):    # revert the value if input wasn't a number
            self.previewFont.ChangeValue(str(self.preview_font))

        elif input <> self.preview_font:                        # update the variables
            gbl.cfg_dict[self.mon_ID]['preview_font'] = gbl.preview_font = self.preview_font = input

            self.previewPanel.preview_font = input              # change previewPanel setting
                                                                # make new masks with new font size
            self.previewPanel.ROIframe, self.previewPanel.RGBmask = \
                    self.previewPanel.makeMaskFrames(self.previewPanel.rois, self.previewPanel.initialSize,
                                             self.previewPanel.preview_font, self.previewPanel.preview_RGBcolor,
                                             self.previewPanel.line_thickness)
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangePreviewRGBColor(self, event):
        input = gbl.correctType(self.previewRGBColor.GetValue(), 'preview_RGBcolor')        # get new value

        if type(input) != tuple:                                # revert the value if input wasn't a tuple
            self.previewRGBColor.ChangeValue(str(self.preview_RGBcolor))

        elif input <> self.preview_RGBcolor:                    # update the variables
            gbl.cfg_dict[self.mon_ID]['preview_RGBcolor'] = gbl.preview_RGBcolor = self.preview_RGBcolor = input

            self.previewPanel.preview_RGBcolor = input          # change previewPanel setting
                                                                # make new masks with new color
            self.previewPanel.ROIframe, self.previewPanel.RGBmask = \
                self.previewPanel.makeMaskFrames(self.previewPanel.rois, self.previewPanel.initialSize,
                                                 self.previewPanel.preview_font, self.previewPanel.preview_RGBcolor,
                                                 self.previewPanel.line_thickness)
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangeLineThickness(self, event):
        input = gbl.correctType(self.lineThickness.GetValue(), 'line_thickness')            # get new value

        if not (type(input) == int or type(input) == float):    # don't change the value if input wasn't a number
            self.lineThickness.ChangeValue(str(self.line_thickness))

        elif input <> self.line_thickness:                      # update the variables
            gbl.cfg_dict[self.mon_ID]['line_thickness'] = gbl.line_thickness = self.line_thickness = input

            self.previewPanel.line_thickness = input            # change previewPanel setting
                                                                # make new masks with new line thickness
            self.previewPanel.ROIframe, self.previewPanel.RGBmask = \
                self.previewPanel.makeMaskFrames(self.previewPanel.rois, self.previewPanel.initialSize,
                                    self.previewPanel.preview_font, self.previewPanel.preview_RGBcolor,
                                    self.previewPanel.line_thickness)
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangePreviewSize(self, event):
        input = gbl.correctType(self.previewSize.GetValue(), 'preview_size')            # get new value

        if type(input) != tuple:                                # revert the value if input wasn't a tuple
            self.previewSize.ChangeValue(str(self.preview_size))

        elif input <> self.preview_size:
            gbl.cfg_dict[self.mon_ID]['preview_size'] = gbl.preview_size = self.preview_size = input
            self.previewPanel.panelSize = input                 # update the value in the monitorPanel
            self.clearVideo()                                   # remove monitorPanel and recreate with new size
            self.refreshVideo()

            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangePreviewFPS(self, event):
        input = gbl.correctType(self.previewFPS.GetValue(), 'preview_fps')              # get new value

        if not (type(input) == int or type(input) == float):    # don't change the value if input wasn't a number
            self.previewFPS.ChangeValue(str(self.preview_fps))

        elif input <> self.preview_fps:                         # update the variables
            gbl.cfg_dict[self.mon_ID]['preview_fps'] = gbl.preview_fps = self.preview_fps = input

            self.previewPanel.interval = 1000/input             # change previewPanel setting  (fps is converted to interval)
            if self.previewPanel.playTimer.IsRunning():         # stop and restart the timer if it was running
                self.previewPanel.playTimer.Stop()
                self.previewPanel.playTimer.Start(1000/input)

            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangeVideoOn(self, event):         # setting focus to videoOn checkbox causes navigation problems, so skip it
        input = self.videoOn.GetValue()                                                 # get new value

        gbl.cfg_dict[self.mon_ID]['video_on'] = gbl.video_on = self.video_on = input
        gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangeDate(self, event):                  # TODO date & time not being saved w/ configuration
        try:
            newdate = self.startDate.GetValue()                                         # get new value
        except:                 # ------ bug in wxDateTimePickerCtrl: m_date not in sync occurs if month not changed
            newdate = self.start_datetime
            gbl.statbar.SetStatusText('Due to a KNOWN BUG: month must be changed to enter a new date.')
            winsound.Beep(600, 200)
        newdate = newdate.FormatISODate()                       # convert date to string

        newtime = self.start_datetime.strftime('%H:%M:%S')      # get time as string (update datetime)

        # cannot use wxDateTime.AddTS because it changes date to 1/1/1970.  Instead, convert date & time to strings,
        # then convert back to python datetime for manipulations
        input = gbl.strdatetime2pydatetime(newdate, newtime)    # combine string date & time into python datetime object

        if input <> self.start_datetime:                        #  update all datetime values
            gbl.start_datetime = gbl.cfg_dict[self.mon_ID]['start_datetime'] = self.start_datetime = input

                                                                # no effect on screen
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangeTime(self, event):
        newtime = self.startTime.GetValue()                                             # gets time as string

        newdate = self.start_datetime.strftime('%Y-%m-%d')      # get date as string (update datetime)


        # cannot use wxDateTime.AddTS because it changes date to 1/1/1970.  Instead, convert date & time to strings,
        # then convert back to python datetime for manipulations
        input = gbl.strdatetime2pydatetime(newdate, newtime)    # combine string date & time into python datetime object

        if input <> self.start_datetime:                        #  update all datetime values
            gbl.start_datetime = gbl.cfg_dict[self.mon_ID]['start_datetime'] = self.start_datetime = input

                                                                # no effect on screen
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    # -------------------------------------------------------------------- get the date and time values from the widgets
    def onChangeSourceFPS(self, event):
        input = gbl.correctType(self.sourceFPS.GetValue(), 'source_fps')                # get new value

        if not (type(input) == int or type(input) == float):    # don't change the value if input wasn't a number
            self.sourceFPS.ChangeValue(str(self.source_fps))

        elif input <> self.source_fps:                            # update the variables
            gbl.cfg_dict[self.mon_ID]['source_fps'] = gbl.source_fps = gbl.source_fps = input

                                                                # no effect on screen
            gbl.shouldSaveCfg = True                           # configuration has changed

        self.screenUpdate(event)                                # skip event & refresh the screen

    def onChangeSourceMMSize(self, event):
        input = gbl.correctType(self.sourceMMSize.GetValue(), 'source_mmsize')               # get new value

        if not (type(input) == tuple):                          # don't change the value if input wasn't a number
            self.sourceMMSize.ChangeValue(str(self.source_mmsize))

        elif input <> self.source_mmsize:                       # update the variables
            gbl.cfg_dict[self.mon_ID]['source_mmsize'] = gbl.source_mmsize = gbl.source_mmsize = input

            # no effect on screen
            gbl.shouldSaveCfg = True  # configuration has changed

        self.screenUpdate(event)  # skip event & refresh the screen

    """def onChangeTrackType(self, event):    # NOT IN USE
        gbl.shouldSaveCfg = True
        gbl.cfg_dict[self.mon_ID]['track_type'] = gbl.track_type = self.track_type = event.Selection         # update self & cfg_dict
        event.Skip()
    """

    def onChangeRb(self, event):
        RbSelected = event.EventObject.Label
        if RbSelected == 'Camera':                                              # update self source_type
            self.source_type = 0
        elif RbSelected == 'File':
            self.source_type = 1
        elif RbSelected == 'Folder':
            self.source_type = 2
        else:
            gbl.statbar.SetStatusText('Invalid RB number in monPanel.py.')
            winsound.Beep(600,200)

        # FileBrowseButton prevents invalid input other than ''
        if self.sources[self.source_type].textbox.GetValue() != '':                     # update self sources
            self.source = self.sources[self.source_type].textbox.GetValue()

        self.currentSource.ChangeValue(str(self.source))                                # update currentSource field
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source                # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type                # update cfg_dict

        self.clearVideo()
        self.refreshVideo()
        gbl.shouldSaveCfg = True
        self.screenUpdate(event)

    """def onChangeSource0(self, event):         # TODO: if possible, get calling object from event & combine the three onChangeSource functions
        gbl.shouldSaveCfg = True
        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                    # if it was a webcam, remove from list
            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)                 # only one webcam implemented at this time
            gbl.webcams -= 1

        self.source_type = 0                                                    # update self source_type
        self.source = self.sources[self.source_type].GetValue()                 # update self source

        gbl.webcams_inuse.append(self.mon_name)              # add this monitor to webcam list (only one webcam implemented at this time)
        gbl.webcams += 1

        self.currentSource.ChangeValue(str(self.source))                                # update currentSource field
        self.rbs[0].ChangeValue(True)                                              # update RBs
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type             # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source

        self.screenUpdate(event)
        """

    def onChangeSource1(self, input):                       # passing the event doesn't pass the value
        if input == '':
            if self.source_type == 1:
                self.sources[1].textbox.ChangeValue(str(self.currentSource.GetValue()))
            elif self.source_type == 2:
                self.sources[1].textbox.ChangeValue('')
            return

        if input <> self.currentSource:

    #        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                # if it was a webcam, remove from list
    #            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)          # webcam NOT IN USE
    #            gbl.webcams -= 1
            gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type = 1
            gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source = input

            self.currentSource.ChangeValue(str(self.source))                       # update currentSource field
            self.rbs[1].SetValue(True)                                     # update RBs

            self.clearVideo()
            self.refreshVideo()
            gbl.shouldSaveCfg = True
        self.screenUpdate(None)

    def onChangeSource2(self, input):                               # passing the event doesn't pass the value
        if input == '':
            if self.source_type == 1:
                self.sources[2].textbox.ChangeValue('')
            elif self.source_type == 2:
                self.sources[2].textbox.ChangeValue(str(self.currentSource.GetValue()))
            return

        if input <> self.currentSource:

#        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                   # if it was a webcam, remove from list
#            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)               # only one webcam implemented at this time
#            gbl.webcams -= 1
            gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type = 2
            gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source = input

            self.currentSource.ChangeValue(str(self.source))  # update currentSource field
            self.rbs[2].SetValue(True)  # update RBs

            self.clearVideo()
            self.refreshVideo()
            gbl.shouldSaveCfg = True

        self.screenUpdate(None)

    # --------------------------------------------------------------------------------------------- change output folder
    def onChangeOutput(self, input):                                  # passing the event doesn't pass the value
        if input == '':
            self.pickOutputBrowser.textbox.ChangeValue(str(self.data_folder))
            return

        if input <> self.data_folder:
            gbl.cfg_dict[self.mon_ID]['data_folder'] = gbl.data_folder = self.data_folder = input
            gbl.shouldSaveCfg = True

        self.screenUpdate(None)

    # ------------------------------------------------------------------------------------------ change mask file & ROIs
    def onChangeMask(self, input):                                     # passing the event doesn't pass the value
        if input == '':
            self.pickMaskBrowser.textbox.ChangeValue(str(self.mask_file))
            return

        gbl.cfg_dict[self.mon_ID]['mask_file'] = gbl.mask_file = self.mask_file = input

        self.previewPanel.mask_file = input
        self.rois = self.previewPanel.loadROIsfromMaskFile()
        self.clearVideo()                       # update the video
        self.refreshVideo()                                         # TODO: mask not changing
        gbl.shouldSaveCfg = True
        self.screenUpdate(None)

    def onMaskGen(self, event):
        self.Q_shouldSaveMask(self.mon_ID)                  # check to see if mask should be saved, ask, & save
        self.rois, self.maskFileContents = self.previewPanel.onMaskGen(self.X, self.Y)             # run the mask generator for this preview panel
        self.clearVideo()
        self.refreshVideo()
        self.screenUpdate(event)
        gbl.shouldSaveMask = True

    def Q_shouldSaveMask(self, nextPage):
        if gbl.shouldSaveMask:  # mask generated.  prompt user to save it.
            dlg = wx.MessageDialog(self, 'Do you want to save the current mask first?',
                                   style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
            answer = dlg.ShowModal()
            dlg.Destroy()
            if answer == wx.ID_YES:
                self.onSaveMask(self)
            elif answer == wx.ID_NO:
                self.rois = self.previewPanel.loadROIsfromMaskFile()            # reload mask from mask_file
                self.clearVideo()                                               # update the video
                self.refreshVideo()
            elif answer == wx.ID_CANCEL:
                return gbl.mon_ID                                               # stay on same page and do nothing

        gbl.shouldSaveMask = False
        return  nextPage

    def onSaveMask(self, event):            # ---------------------------------------------------  Save new mask to file
        """
        Lets user select file and path where mask will be saved.
        """
        # set file types for find dialog
        wildcard = "PySolo Video config file (*.msk)|*.msk|" \
                   "All files (*.*)|*.*"  # adding space in here will mess it up!

        dlg = wx.FileDialog(self,
                            message="Save mask as file ...",
                            defaultDir=self.data_folder,
                            wildcard=wildcard,
                            style=(wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                            )

        if not(dlg.ShowModal() == wx.ID_OK):                    # show the file browser window
            return False
        else:
            input = dlg.GetPath()                   # get the path from the save dialog

            if os.path.isfile(input):
                os.remove(input)                    # get rid of old file before appending data

            with open(input, 'a') as mask_file:
                for roi in self.maskFileContents:
                    mask_file.write(roi)                          # write to file line by line

        gbl.shouldSaveMask = False                              # mask is saved
        gbl.shouldSaveCfg = True

        dlg.Destroy()
        mask_file.close()

        self.pickMaskBrowser.textbox.ChangeValue(str(input))                                # update variables and textctrl
        self.screenUpdate(event)

    """def onClearMask(self, event):                # NOT USED
        gbl.shouldSaveCfg = True
        self.rois = []
        cfg.mon_nicknames_to_dicts(self.mon_ID)

        self.clearVideo()
        self.refreshVideo()
        self.screenUpdate(event)"""

"""# ------------------------------------------------------------------------------------------ Stand alone test code
#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        config = cfg.Configuration(self)
        whole = monPanel(self)




        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#
"""