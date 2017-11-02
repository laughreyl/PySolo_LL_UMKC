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


import numpy as np                      # for ROIs
import wx                               # GUI controls
import os                               # system controls
import cv2
import cv2.cv
from os.path import expanduser          # get user's home directory
import datetime                         # date and time handling functions
import sys
import cPickle
import winsound
import wx.lib.inspection

"""=====================================================================================================================
 Global Variable Declarations 
 
 Since there are multiple files containing functions that operate on the same information, creating global variables 
 significantly simplified the code.  The variables contain information for the current state of the system based on 
 the gbl.mon_ID number which indicates the monitor being used.  gbl.mon_ID == 0 indicates that the configuration page
 is currently showing instead of a monitor configuration page.
 
 In classes that are threaded, all global variables are copied into the object itself on initiation since global 
 variables could change during a threaded process.
"""

exec_dir = sys.path[0]                              # folder containing the scripts for this program


""" --------------------------------------------------------------------- nicknames for general configuration parameters
"""
global monitors, \
    thumb_size, \
    thumb_fps, \
    cfg_path, \
    thumbPanels, \
    threadsStarted, \
    timersStarted, \
    trackers, \
    statbar

monitors = 1                                    # number of videos include in the configuration
# webcams = 1       #    NOT IN USE              # number of webcams attached to the system
thumb_size = (320,240)                          # size of video playback panels and console panels on config page
thumb_fps = 5                                   # speed of video playback on config page
cfg_path = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')       # location for saving configuration files
thumbPanels = ['thumb panels']                  # list of thumbnail panels used in scrolled window on configuration page
                                                # element 0 identifies the type of list and allows 1-indexed referencing

statbar = ''                    # status bar at the bottom of the window for messages to user
                                # this is a place holder which will be replaced with a wx.StatusBar in PySolo_Video_Main
                                # class mainFrame
                                # it's created here to make it global, but has to be initialized inside a wxpanel class

""" ------------------------------------------------------------------ nicknames for configuration of **current** mon_ID
"""
# mon_ID = 0 refers to the main configuration page
global mon_ID, \
    mon_name, \
    source_type, \
    source, \
    source_fps, \
    source_mmsize, \
    preview_size, \
    preview_fps, \
    preview_font, \
    preview_RGBcolor, \
    line_thickness, \
    video_on, \
    issdmonitor, \
    start_datetime, \
    track, \
    track_type, \
    mask_file, \
    data_folder

mon_ID = 1                                  # always at least one monitor.  use it to initialize.
mon_name = 'Monitor1'                       # name of the monitor
source_type = 1                             # type of video source.  webcam=0, file=1, folder=2
source = None                               # path & filename of the source
source_fps = 0.5                            # rate at which source was obtained
source_mmsize = (300,300)                   # actual size of field view in millimeters (for conversion from pixels
preview_size = (480, 480)                   # size of video playback on monitor configuration page
preview_fps = 1                             # rate of playback on monitor configuration page
preview_font = 24                           # size of numbering of ROIs on video playback.
                                                # font is relative to source size and has no relation to typeface fonts
preview_RGBcolor = (255, 0, 0)              # color of ROIs and numbers on the video playback
line_thickness = 2                          # thickness of lines on the video playback
video_on = False                            # indicates if video should be shown frame-by-frame during tracking
                                            # shows original ROI, B&W ROI, and contour image
                                            # only for debugging purposes.  runs far too slow for real acquisition
#issdmonitor = False                         # NOT USED
start_datetime = datetime.datetime.now()    # date and time video recording started
track_type = 0                              # track distances
track = True                                # do track this monitor
mask_file = None                            # file containing ROI coordinates
data_folder = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')    # folder where output should go


""" ----------------------------------------------------------------------- cfg_dict contains all configuration settings
"""
global cfg_dict

cfg_dict = [{                                              # create the default config dictionary
        'monitors'      : monitors,                        # element 0 is the options dictionary
#        'webcams'       : webcams,                        # number of webcams available, NOT IN USE
        'thumb_size'    : thumb_size,
        'thumb_fps'     : thumb_fps,
        'cfg_path'      : cfg_path
        },
        {                                       # all additional elements are the monitor dictionaries (1-indexed)
        'mon_name'      : mon_name,
        'source_type'   : source_type,
        'source'        : source,
        'source_fps'    : source_fps,
        'source_mmsize' : source_mmsize,
        'preview_size'  : preview_size,
        'preview_fps'   : preview_fps,
        'preview_font'  : preview_font,
        'preview_RGBcolor' : preview_RGBcolor,
#        'issdmonitor'   : issdmonitor,         # NOT IN USE
        'start_datetime': start_datetime,
        'track'         : track,
        'track_type'    : track_type,
        'mask_file'     : mask_file,
        'data_folder'   : data_folder,
        'line_thickness': line_thickness,
        'video_on'      : video_on
        }]

""" ---------------------------------------------------------------------------------------------- miscellaneous globals
"""
global rois, genmaskflag, shouldSaveMask, shouldSaveCfg

rois = []               # temporary storage for ROIs
genmaskflag = False     # true when new mask was created - program will use new mask instead of loading from mask file
shouldSaveMask = False  # true when mask generator has run but mask is not saved
shouldSaveCfg = False   # true when a change has been made to the configuration and configuration has not been saved


""" =============================================================================== functions needed by multiple classes
"""

# ---------------------------------------------- changes string input into appropriate type (int, datetime, tuple, etc.)
def correctType(input, key):
# order of conditional tests is important!
# returns once correct input type is found

    if key == 'start_datetime':     # ----------------------------------------------------- datetime
        if type(input) == type(datetime.datetime.now()):            # good answer
            pass
        elif type(input) == type(''):                               # try string -> datetime value
            try:    # ------  string may not be decipherable
                newForm = datetime.datetime.strptime(input, '%Y-%m-%d %H:%M:%S')
                return newForm                                        # successful conversion
            except:
                pass

        newForm = datetime.datetime.now()                             # failed - use now instead
        return newForm

    if input == 'None' or input is None:   # ------------------------------------------------ None type
        newForm = None
        return newForm                                              # successful conversion

    if input == 'False':  # ------------------------------------------------------------------- boolean
        newForm = False
        return newForm                                              # successful conversion
    elif input == 'True':
        newForm = True                                              # successful conversion
        return newForm

    try:    # --------------------------------------------------------------------------------- integer
        newForm = int(input)
        return newForm                                              # successful conversion
    except:
        pass

    try:    # ------------------------------------------------------------------- floating point number
        newForm = float(input)
        return newForm                                              # successful conversion
    except:
        pass

    if ',' in input:  # ------------------------------------------------ tuple of two or three integers
        if not '(' in input:
            newForm = '(' + input + ')'
        else:
            newForm = input
        try:                                                # only works if it's a tuple of numbers
            newForm = tuple(newForm[1:-1].split(','))           # converts to integer because program doesn't use
            if len(newForm) == 2:                               # floats or strings in tuples
                newForm = (int(newForm[0]), int(newForm[1]))
            elif len(newForm) == 3:
                newForm = (int(newForm[0]), int(newForm[1]), int(newForm[2]))
            return newForm
        except:
            pass

    return input  # ------------------------------------------------- all else has failed:  return as string

# ------------------------------------------------------------------------------------------------------- read Mask file
def loadROIsfromMaskFile(mask_file):
# returns empty list if mask file doesn't load

    rois = []
    if mask_file is None:
        statbar.SetStatusText('Mask file not found')
        winsound.Beep(600, 200)
        return rois

    if os.path.isfile(mask_file):                           # if mask file is there, try to load ROIs
        try:    # ------ mask file could be corrupt
            cf = open(mask_file, 'r')       # read mask file
            ROItuples = cPickle.load(cf)    # list of 4 tuple sets describing rectangles on the image
            cf.close()
        except:
            statbar.SetStatusText('Mask failed to load')
            winsound.Beep(600, 200)
            return rois
    else:
        statbar.SetStatusText('Mask file not found')
        winsound.Beep(600, 200)
        return rois

    # ------------------------------------------------------------------------------------------ make gbl.ROIs
    for roi in ROItuples:  # complete each rectangle by adding first coordinate to end of list
        roiList = []  # clear for each rectangle
        for coordinate in roi:  # add each coordinate to the list for the rectangle
            roiList.append(coordinate)
        roiList.append(roi[0])
        rois.append(roiList)  # add the rectangle lists to the list of ROIs

    return rois


# ---------------------------------------------------------------------- convert python datetime.datetime to wx.datetime
def pydatetime2wxdatetime(pydt):
    dt_iso = pydt.isoformat()
    wxdt = wx.DateTime()
    wxdt.ParseISOCombined(dt_iso, sep='T')
    return wxdt

# ---------------------------------------------------------------------- convert python datetime.datetime to wx.datetime
def strdatetime2pydatetime(date, time):
    pydt = datetime.datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M:%S')
    return pydt

# ------------------------------------------------------------------------------------ convert wxdatetime to time string
def wxdatetime2timestring(datetime):
    strdt = datetime.FormatISOTime()
    return strdt

# ------------------------------------------------------------------------------------------------------------------------------ debug
# shows an image for 2 seconds and allows save (type 's').  Press <esc> to close image and resume program with no further video
def debugimg(img, size=(1200,400), outprefix='test'):
    title = outprefix + '   Press <p> to pause, <s> to save, or <q> to quit debug mode.'
    mini_image = cv2.resize(img, size)

    cv2.imshow(title, mini_image)
    k = cv2.waitKey(2000) & 0xFF            # wait 3 seconds

    while k == ord('p'):
        k = cv2.waitKey(0)                  # if user presses 'p', wait for another keypress

    if k == ord('s'):                     # 's' key means save
        cv2.imwrite('%s.png' % outprefix, mini_image)
        cv2.destroyAllWindows()
    elif k == ord('q'):
        cv2.destroyAllWindows()
        return False                        # stop showing images
    else:
        cv2.destroyAllWindows()             # continue

    return True                             # continue

