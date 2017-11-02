#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


""" 
 ======================================================================================================================
 These functions create one video playback panel.
 Webcam is not available because it cannot end acquisition of data.
======================================================================================================================
"""


import os
import numpy as np
import winsound
import wx                               # needs installation
import cv2, cv2.cv                      # needs installation
import configurator as cfg              # part of this program - handles configuration parameters
import pysolovideoGlobals as gbl        # part of this program - contains global variables and functions
import cPickle

# TODO: prevent flicker when refreshing video

""" ========================================== NOT IN USE =========================== capture frames from a video camera
"""
class realCam(object):                                  # don't use global variables for this object due to threading
    """
    realCam class is NOT IN USE, but is left here for restoration if desired.
    realCam class will provide images from a webcam connected to the system
    """
    #  ------------------------------------------------------------------------------------------- initialize the camera
    def __init__(self_realCam, mon_ID=gbl.mon_ID, fps=gbl.source_fps, devnum=0):
        self_realCam.mon_ID = mon_ID                                    # don't use gbl nicknames due to threading
        self_realCam.source = devnum                                    # source is the device number
        self_realCam.fps = fps

        self_realCam.currentFrame = 0
        self_realCam.loop = True                   # cameras don't really loop, and shouldn't stop

        try:    # ------ may fail to start camera
            self_realCam.captureVideo = cv2.VideoCapture(self_realCam.source)  # only one camera (device 0) is supported
                                                                    # argument is required even though it's "unexpected"
            retrn, self_realCam.frame = self_realCam.captureVideo.read()
        except:     # ------ notify user and set capture to None
            self_realCam.captureVideo = None                          # capture failed
            gbl.statbar.SetStatusText('Real Cam capture failed.')
            winsound.Beep(600,200)
            return

        # ----------------------------------------------------------------------------- collect camera properties
        self_realCam.initialSize = self_realCam.getCamFrameSize()
        self_realCam.lastFrame = 0                                      # cameras don't have a last frame

    # -------------------------------------------------------------------------------------------- get camera frame size
    def getCamFrameSize(self_realCam):
        """
        Return real size
        """
        self_realCam.rows, self_realCam.cols, channels = self_realCam.frame.shape
        return int(self_realCam.cols), int(self_realCam.rows)

    # --------------------------------------------------------------------------------------------------- get next frame
    def getImage(self_realCam):  # capture and prepare the next frame
        """
        for live cameras
        """
        try:    # ------ may fail to read frame
            retrn, self_realCam.frame = self_realCam.captureVideo.read()
        except:     # ------ notify user and set frame to None.
            self_realCam.frame = None
            gbl.statbar.SetStatusText('Real Cam capture failed.')
            winsound.Beep(600, 200)

        self_realCam.currentFrame += 1          # there is no last frame
        return self_realCam.frame

""" =================================================================================== capture frames from a video file
"""
class virtualCamMovie(object):
    """
    A Virtual cam provides images from a movie file (avi, mov)
    self_vMovie is used instead of self to help reduce confusion over functions with identical names in different classes.
    Identical naming of functions allows program to process input the same way for each video input class.  
    """
    # ---------------------------------------------------------------------------------------------- open the video file
    def __init__(self_vMovie, mon_ID=gbl.mon_ID, fps=gbl.source_fps, source=gbl.source, loop=True):
        self_vMovie.mon_ID = mon_ID                            # don't use gbl nicknames after init due to threading
        self_vMovie.source = source             # video file path and name
        self_vMovie.fps = fps                   # speed at which video was recorded
        self_vMovie.loop = loop                 # true if video should loop back at end of file
        self_vMovie.currentFrame = 0

        try:    # ------ video may not open
            self_vMovie.captureVideo = cv2.VideoCapture(self_vMovie.source)
            flag, self_vMovie.frame = self_vMovie.captureVideo.read()
        except: # ------ capture failed
            self_vMovie.captureVideo = None
            gbl.statbar.SetStatusText('Video Cam capture failed.')
            winsound.Beep(600, 200)
            return

        self_vMovie.initialSize = self_vMovie.getVideoCamSize()                         # get frame size from video
        self_vMovie.lastFrame = self_vMovie.captureVideo.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)  # and length of video

    # --------------------------------------------------------------------------------------------- get movie frame size
    def getVideoCamSize(self_vMovie):
        try:    # ------ frame is sometimes a NoneType object
            self_vMovie.rows, self_vMovie.cols, channels = self_vMovie.frame.shape
            return int(self_vMovie.cols), int(self_vMovie.rows)
        except:
            gbl.statbar.SetStatusText('No video frame available in videoMonitor.py, getVideoCamSize')
            winsound.Beep(600,200)
            return 500, 500     # randomly chosen substitute values for size

# ------------------------------------------------------------------------------------------------------- get next frame

    # --------------------------------------------------------------------------------------------------- get next frame
    def getImage(self_vMovie):
        """
        for input from video file
        """
        if (self_vMovie.currentFrame >= self_vMovie.lastFrame) and self_vMovie.loop:    # reached end of file
            self_vMovie.currentFrame = 0
            self_vMovie.captureVideo = cv2.VideoCapture(self_vMovie.source)  # restart the video (source is required)

        elif (self_vMovie.currentFrame >= self_vMovie.lastFrame) and not self_vMovie.loop:
            self_vMovie.frame = None                                         # stop video
            gbl.statbar.SetStatusText('End of Video File.')
            winsound.Beep(300, 200)
            return
        else: pass

        # -------------------------------------------------------------------- read next frame
        try:    # ------ may fail to read frame
            flag, self_vMovie.frame = self_vMovie.captureVideo.read()
        except:     # ------ notify user and set frame to None
            self_vMovie.frame = None
            gbl.statbar.SetStatusText('Capture failed.')
            winsound.Beep(600, 200)
            return

        self_vMovie.currentFrame += 1
        return self_vMovie.frame

""" ========================================================================== capture frames from 2D images in a folder
"""
class virtualCamFrames(object):
    """
    A Virtual cam to be used to pick images from a folder rather than a webcam
    Images are handled through OpenCV
    File types accepted are .tif and .jpg
    """
    # ------------------------------------------------------------------------------------------------ prepare file list
    def __init__(self_vFrames, mon_ID = gbl.mon_ID, fps= gbl.source_fps, source=gbl.source, loop=True):
        """
        files will be shown in alphabetical order
        """
        self_vFrames.mon_ID = mon_ID
        self_vFrames.source = source
        self_vFrames.fps = fps

        self_vFrames.currentFrame = 0
        self_vFrames.loop = loop

        # -------------------------------------------------------------------------- initialize file manager
        self_vFrames.fileList = self_vFrames.__populateList__()         # get list of files

        self_vFrames.lastFrame = len(self_vFrames.fileList)
        if self_vFrames.lastFrame == 0:
            self_vFrames.captureVideo = None                            # no files found.  capture failed.
            gbl.statbar.SetStatusText('No images in folder.')
            winsound.Beep(600, 200)
            return

        filepath = os.path.join(self_vFrames.source, self_vFrames.fileList[0])
        self_vFrames.frame = cv2.imread(filepath, cv2.cv.CV_LOAD_IMAGE_COLOR)       # read first image
        self_vFrames.initialSize = self_vFrames.getFramesSize()                     # get frame size

    # ---------------------------------------------------------------------------------- create list of files to be used
    def __populateList__(self_vFrames):
        """
        Populate the file list
        """
        fileList = []
        fileListTmp = os.listdir(self_vFrames.source)

        for fileName in fileListTmp:
            if '.tif' in fileName or '.jpg' in fileName:
                fileList.append(fileName)

        fileList.sort()
        return fileList

    # ----------------------------------------------------------------------------------- get image size from first file
    def getFramesSize(self_vFrames):
        self_vFrames.rows, self_vFrames.cols, channels = self_vFrames.frame.shape
        return int(self_vFrames.cols), int(self_vFrames.rows)

    # --------------------------------------------------------------------------------------------------- get next frame
    def getImage(self_vFrames):
        """
        for folder of 2D images
        """
        if self_vFrames.currentFrame >= self_vFrames.lastFrame and self_vFrames.loop:
            self_vFrames.currentFrame = 0                                      # loop if requested

        elif self_vFrames.currentFrame > self_vFrames.lastFrame and not self_vFrames.loop:
            self_vFrames.frame = None
            gbl.statbar.SetStatusText('End of File List.')                      # stop if not looping
            winsound.Beep(300, 200)
            return

        try:    # ------ may fail to find files in folder
            filepath = os.path.join(self_vFrames.source, self_vFrames.fileList[self_vFrames.currentFrame])
            self_vFrames.frame = cv2.imread(filepath, cv2.cv.CV_LOAD_IMAGE_COLOR)
        except:     # ------ set capture to None
            self_vFrames.frame = None
            gbl.statbar.SetStatusText('Error loading file ' +
                                      self_vFrames.source +
                                      '(' + str(self_vFrames.currentFrame) + ')')
            winsound.Beep(600, 200)
            return

        self_vFrames.currentFrame += 1
        return self_vFrames.frame

""" ======================================================================================== generic video display panel
"""
class monitorPanel(wx.Panel):
    """
    One video playback panel (monitor) to be used as a thumbnail, or a preview panel
    - Avoid gbl nicknames, except for cfg_dict and flags, due to threading
    - don't actually apply or start playbacks until page that contains the panel is in focus
    - self_MP designates this as the monitorPanel class for easier discernment of which class is being described
    """
    # ------------------------------------------------------------------------------------------- initialize the monitor
    def __init__(self_MP, parent, mon_ID=gbl.mon_ID, panelType='thumb', loop=True, rois=[]):
        # ----- variables that were passed
        self_MP.parent = parent
        self_MP.mon_ID = mon_ID
        self_MP.panelType = panelType                             # 'thumb' or 'preview'
        self_MP.loop = loop                                       # flag to loop or not at end of video
        self_MP.rois = rois                                       # regions of interest coordinates

        # ----- variables that describe the monitor
        self_MP.mon_name        = gbl.cfg_dict[self_MP.mon_ID]['mon_name']
        self_MP.source_type     = gbl.cfg_dict[self_MP.mon_ID]['source_type']
        self_MP.source          = gbl.cfg_dict[self_MP.mon_ID]['source']

                                                                    # ----- decide on panel size and fps
        if panelType == 'preview':
            self_MP.panelSize   = gbl.cfg_dict[self_MP.mon_ID]['preview_size']
            self_MP.fps         = gbl.cfg_dict[self_MP.mon_ID]['preview_fps']
        elif panelType == 'thumb':
            self_MP.panelSize   = gbl.cfg_dict[0]['thumb_size']
            self_MP.fps         = gbl.cfg_dict[0]['thumb_fps']
        else:
            gbl.statbar.SetStatusText('Unexpected panel type in class monitorPanel')
            winsound.Beep(600,200)
            self_MP.panelSize = (320,240)    # choose arbitrary values
            self_MP.fps = 1

        self_MP.interval        = 1000/ self_MP.fps
        self_MP.preview_font    = gbl.cfg_dict[self_MP.mon_ID]['preview_font']
        self_MP.preview_RGBcolor = gbl.cfg_dict[self_MP.mon_ID]['preview_RGBcolor']
        self_MP.line_thickness  = gbl.cfg_dict[self_MP.mon_ID]['line_thickness']
        self_MP.video_on        = gbl.cfg_dict[self_MP.mon_ID]['video_on']

        self_MP.mask_file       = gbl.cfg_dict[self_MP.mon_ID]['mask_file']
        if self_MP.rois == []:                       # if no ROIs were passed from the calling function, load mask file
            try:    # ------ mask file may be corrupt
                self_MP.rois    = self_MP.loadROIsfromMaskFile()
            except: # ------ ROIs is an empty list
                pass

        # ------ class specific variables
        self_MP.keepPlaying = False                               # flag to start and stop video playback


        # ------ initialize the panel
        wx.Panel.__init__(self_MP, parent, id=wx.ID_ANY, size=self_MP.panelSize, name=self_MP.mon_name)


        """# ---------------------------------------------------------------------------------------------- WEBCAM NOT USED
        #        if self_MP.source_type == 0:     # get the device number if the panel source is a webcam  
        #            self_MP.source = 0 -----------------------------------------------------------------------------------
        """


        # ------ lay out the panel
        self_MP.widgetMaker()                   # create widgets
        self_MP.sizers()                        # set up panel layout
        self_MP.binders()                       # bind event handlers

        self_MP.SetSize(self_MP.panelSize)
        self_MP.SetMinSize(self_MP.GetSize())    # if panel should now be smaller this makes sure old panel isn't left in background
        self_MP.SetBackgroundColour('#A9A9A9')

    # ---------------------------------------------------------------------------------------------- bind event handlers
    def binders(self_MP):
        # -------------------------------------- for mask maker preview panel, enable mouse coordinate selection
        if gbl.mon_ID != 0:
            self_MP.Bind(wx.EVT_LEFT_UP, self_MP.onLeftUp)

        # -------------------------------------------------------------- create a timer that will play the video
        self_MP.Bind(wx.EVT_PAINT, self_MP.onPaint)
        self_MP.Bind(wx.EVT_TIMER, self_MP.onNextFrame)
        self_MP.playTimer = wx.Timer(self_MP, id=wx.ID_ANY)

    # ----------------------------------------------------------------------- create monitor number to display in corner
    def widgetMaker(self_MP):
        monfont = wx.Font(25, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self_MP.monDisplayNumber = wx.StaticText(self_MP, wx.ID_ANY, ' %s' % self_MP.mon_ID)
        self_MP.monDisplayNumber.SetFont(monfont)

    # -------------------------------------------------------------------------------- place number in upper left corner
    def sizers(self_MP):
        self_MP.numberSizer = wx.BoxSizer(wx.HORIZONTAL)
        self_MP.numberSizer.Add(self_MP.monDisplayNumber, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 20)
        self_MP.SetSizer(self_MP.numberSizer)
        self_MP.Layout()

    # ------------------------------------------ create mask frames to lay over video images for viewing during playback
    def makeMaskFrames(self_MP, rois, initialSize, font, RGBcolor, line_thickness):
        # creates a transparent 2D frame called mask to wipe out current color values
        # draws the ROIs and numbers on the frame called RGBmask in colors to lay over the mask
        # returns both mask and frame

        # ---------------------------------------------------------------------------------------- create frame on ones
        npsize = (initialSize[1], initialSize[0])  # opencv and np use opposite order
        mask_frame = np.ones(npsize, np.uint8)  # binary frame for creating mask

        if not rois: rois = []
        # ------------------------------------------------------------------ draw ROIs and numbers on frame using zeros
        # zeros in regions that will be masked, ones in regions that won't
        roiNum = 0  # I know it seems backwards, but ones are places where video frame value is used.
        lastY = 0  # It makes the math easier.
        for roi in rois:
            roiNum = roiNum + 1  # use 1-indexed ROI numbers
            for count in range(0, 4):  # draw the ROI
                cv2.line(mask_frame, roi[count], roi[count + 1], 0, line_thickness)
            # ----------------------------------------------------------------------- only number the top row of ROIs
            if lastY >= roi[0][1] or lastY == 0:  # indicates a new column has started
                roiWidth = abs(roi[1][0] - roi[0][0])
                numPosition = (roi[0][0], roi[0][1] - 5 * line_thickness)
                fontScale = font * roiWidth * 10 / initialSize[0]  # fontscale has no relation to typefont sizes
                cv2.putText(mask_frame, str(roiNum), org=numPosition,
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=fontScale,
                            color=(0), thickness=line_thickness)

            lastY = roi[0][1]

        # stack 3 mask_frames so each color has ROIs that won't be covered by other colors
        mask = np.dstack((mask_frame, mask_frame, mask_frame))  # this mask zeroes out pixels in the original image
        mask = mask.astype(np.uint8)

        redmask = (1 - mask_frame) * RGBcolor[0]
        greenmask = (1 - mask_frame) * RGBcolor[1]
        bluemask = (1 - mask_frame) * RGBcolor[2]

        RGBmask = np.dstack((redmask, greenmask, bluemask))  # this mask applies colors to pixels in the image

        return mask, RGBmask

    # ------------------------------------------------------------------------------- generate ROIs from user parameters
    def onMaskGen(self_MP, X, Y):                                          # TODO: add ability to draw one ROI at a time
        # putting this generator in monPanel.py makes it difficult to keep ROIs with their own monitors.

        self_MP.X = X
        self_MP.Y = Y

        # ------ make sure supplied parameters are reasonable: reject if 0 rows, 0 columns, or 0 width or height
        if self_MP.X[1].GetValue() == 0:
            winsound.Beep(600, 200)
            gbl.statbar.SetStatusText('Zero dimensions specified for rows.')
            return
        elif self_MP.Y[1].GetValue() == 0 :
            winsound.Beep(600, 200)
            gbl.statbar.SetStatusText('Zero dimensions specified for columns.')
            return
        elif  self_MP.X[3].GetValue() == 0 :
            winsound.Beep(600, 200)
            gbl.statbar.SetStatusText('Zero dimensions specified for width.')
            return
        elif self_MP.Y[3].GetValue() == 0:
            winsound.Beep(600,200)
            gbl.statbar.SetStatusText('Zero dimensions specified for height.')
            return

        # ------ generate roi coordinates for immediate use, and an array to be saved as the mask file.
        mask = []     # holds rows for output to a mask file
        rois = []     # holds tuples for drawing ROIs in the videoMonitor panel

        mask_dict = {}
        mask_keys = ['cols', 'x1', 'x_len', 'x_sep', 'x_tilt', 'rows', 'y1', 'y_len', 'y_sep', 'y_tilt']

        for count in range(0,5):
            mask_dict[mask_keys[count]] = int(self_MP.X[count+1].GetValue())               # x column

        for count in range(5,10):
            mask_dict[mask_keys[count]] = int(self_MP.Y[count-4].GetValue())               # y column

        ROI = 1  # counter; numbers the ROIs

        # every ROI list will contain:  [(ax,ay),(bx,by),(cx,cy),(dx,dy),(ax,ay)]
        # number the ROIs vertically for easier use of output since flies of same genotype are unusally loaded vertically

        # x-coordinates change through cols
        # (x1, y1) is the top left corner of the top left ROI
        for col in range(0, int(mask_dict['cols'])):
            # x-coordinates change through columns
            # y-coordinates change through rows
            for row in range(0, mask_dict['rows']):
                ax = mask_dict['x1'] + \
                     col*(mask_dict['x_len'] +mask_dict['x_sep'] + mask_dict['x_tilt']) + \
                     row*mask_dict['x_tilt']
                bx = ax + mask_dict['x_len']                # add width
                cx = bx
                dx = ax
                ay = mask_dict['y1'] + \
                     col*mask_dict['y_tilt'] + \
                     row*(mask_dict['y_len'] + mask_dict['y_sep'] + mask_dict['y_tilt'])
                by = ay
                cy = ay + mask_dict['y_len']                # add height
                dy = cy

                # --------------------------------------------------- create the mask coordinates for this ROI
                if row == 0 and col == 0:
                    mask.append(  # for saving to mask file
                        '(lp1\n((I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\n' % (ax, ay, bx, by, cx, cy, dx, dy))
                else:
                    mask.append(
                        'ttp%d\na((I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\n' % (
                        ROI, ax, ay, bx, by, cx, cy, dx, dy))

                rois.append([(ax, ay), (bx, by), (cx, cy), (dx, dy), (ax, ay)])  # for immediate use by program

                ROI += 1                                    # increment ROI number

        mask.append('ttp%d\na.(lp1\nI1\n' % (ROI + 1))                             # for saving as mask file
        mask.append('aI1\n' * mask_dict['rows'] * (mask_dict['cols'] -1))
        mask.append('a.\n\n\n')

        gbl.shouldSaveMask = True                           # ask about saving before next refreshVideo
        gbl.shouldSaveCfg = True

        return rois, mask

    # --------------------------------------------------------------------------------------------------- read Mask file
    def loadROIsfromMaskFile(self_MP):
        # returns empty list if mask file doesn't load
        # identical to function in track.py

        if self_MP.mask_file is None:
            gbl.statbar.SetStatusText('Mask file not found')
            winsound.Beep(600, 200)
            return False                                    # sets the haveMask flag to show that mask was not loaded

        if os.path.isfile(self_MP.mask_file):  # if mask file is there, try to load ROIs
            try:  # ------ mask file could be corrupt
                cf = open(self_MP.mask_file, 'r')  # read mask file
                ROItuples = cPickle.load(cf)  # list of 4 tuple sets describing rectangles on the image
                cf.close()
            except:
                gbl.statbar.SetStatusText('Mask failed to load')
                winsound.Beep(600, 200)
                return False                            # sets the haveMask flag to show that mask was not loaded
        else:
            gbl.statbar.SetStatusText('Mask file not found')
            winsound.Beep(600, 200)
            return  False                               # sets the haveMask flag to show that mask was not loaded

        rois = []
        # ------------------------------------------------------------------------------------------ make gbl.ROIs
        for roi in ROItuples:  # complete each rectangle by adding first coordinate to end of list
            roiList = []  # clear for each rectangle
            for coordinate in roi:  # add each coordinate to the list for the rectangle
                roiList.append(coordinate)
            roiList.append(roi[0])
            rois.append(roiList)  # add the rectangle lists to the list of ROIs

        return  rois

    # ------------------------------------------------------------------------------------------ start playing the video
    def PlayMonitor(self_MP):

        # ------------------------------------------------------------------------------------------ prepare for capture
        # ----- use the sourcetype to create the correct type of object for capture
        """if gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 0:  # !!!!!  NOT USED because webcams have no end           
            gbl.statbar.SetStatusText('Webcam not available.')
            winsound.Beep(600, 200)
            return  # ------------------------- to restore webcam delete notification to user and uncomment next line
            self_MP.captureVideo = realCam(self_MP.mon_ID, self_MP.fps, devnum=0)"""
        if gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 1:                                                # video file
            self_MP.captureVideo = virtualCamMovie(self_MP.mon_ID, self_MP.fps, self_MP.source, loop=self_MP.loop)

        elif gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 2:                                        # folder of images
            self_MP.captureVideo = virtualCamFrames(self_MP.mon_ID, self_MP.fps, self_MP.source, loop=self_MP.loop)

        # ------ get actual frame size
        self_MP.initialSize = (self_MP.initialCols, self_MP.initialRows) = self_MP.captureVideo.initialSize

        # ------ if panel size desired is bigger than input size
        if self_MP.panelSize > self_MP.captureVideo.initialSize:
            winsound.Beep(600, 200)
            gbl.statbar.SetStatusText('Input frame size is only ' + str(self_MP.initialSize))
            self_MP.panelSize = self_MP.captureVideo.initialSize  # reduce it to the input size
            if self_MP.panelType == 'thumb':
                gbl.thumb_size = self_MP.panelSize
            elif self_MP.panelType == 'preview':
                gbl.preview_size = self_MP.panelSize
            cfg.cfg_nicknames_to_dicts()
            self_MP.SetSize(self_MP.panelSize)  # set panel size to fit desired frame size

        # ------ handle no source
        if self_MP.source == None:                                  # make a blank frame
            npsize = (self_MP.panelSize[1], self_MP.panelSize[0])   # opencv and np use opposite order
            self_MP.initialSize = self_MP.panelSize
            oneDframe = np.ones(npsize, np.uint8)
            self_MP.frame = np.dstack((oneDframe, oneDframe, oneDframe))  # binary frame for creating mask

        else:
            # ------ each of the 3 video input classes has a "getImage" function
            self_MP.frame = self_MP.captureVideo.getImage()

        try: self_MP.rois               # if there are no ROIs yet, make an empty list
        except:
            self_MP.rois = self_MP.loadROIsfromMaskFile()     # try to load from maskfile

        # ------------------------------------------------------------------ create masks for overlaying ROIs onto image
        #                    ROI frame will zero out masked area and RGBmask will fill in masked area with color
        self_MP.ROIframe, self_MP.RGBmask = self_MP.makeMaskFrames(self_MP.rois,
                                        self_MP.initialSize, self_MP.preview_font, self_MP.preview_RGBcolor,
                                        self_MP.line_thickness)


        # ----------------------------------------- multiply element by element to leave zeros where lines will be drawn
        self_MP.frame2 = np.multiply(self_MP.frame.copy(), self_MP.ROIframe)

        # ---------------------------------------------------------------------- add RGBmask to frame to color the lines
        self_MP.frame3 = np.add(self_MP.frame2.copy(), self_MP.RGBmask)

        # ---------------------------------------------------------------------------- resize the image to fit the panel
        self_MP.newframe = cv2.resize(self_MP.frame3.copy(), dsize=self_MP.panelSize)

        # ------------------------------------------------------------------------------ create bitmap from masked image
        self_MP.bmp = wx.BitmapFromBuffer(self_MP.panelSize[0], self_MP.panelSize[1], self_MP.newframe.tostring())

#        self_MP.playTimer.Start(self_MP.interval)   # timer cannot be started here.  must start in main thread

        self_MP.keepPlaying = True
        self_MP.Show()                  # display the image

    # ----------------------------------------------------------------------------- captures next frame and applies mask
    def onNextFrame(self_MP, evt):

        # if ROIframe is not available, playMonitor() was probably not run before the playtimer started

        self_MP.frame = self_MP.captureVideo.getImage()
        if self_MP.frame == None:
            npsize = (self_MP.initialSize[1], self_MP.initialSize[0])   # opencv and np use opposite order
            oneDframe = np.ones(npsize, np.uint8)
            self_MP.frame = np.dstack((oneDframe, oneDframe, oneDframe))  # binary frame for creating mask

        frame2 = np.multiply(self_MP.frame.copy(), self_MP.ROIframe)        # apply mask to image
        frame3 = np.add(frame2.copy(), self_MP.RGBmask)

        self_MP.newframe = cv2.resize(frame3.copy(), dsize=self_MP.panelSize)    # resize the frame before copy from buffer
                                                                            # since too large a frame will be corrupted

        try:    # ------ copy from buffer may fail
            self_MP.bmp.CopyFromBuffer(self_MP.newframe.tostring())         # copies data from buffer to bitmap
            self_MP.Refresh()                                               # triggers EVT_PAINT

        except:     # ------ if something goes wrong, stop playback & notify user
            gbl.statbar.SetStatusText('Could not paint image.')
            self_MP.keepPlaying = False
            self_MP.playTimer.Stop()
            winsound.Beep(300,200)
            return

    # ----------------------------------------------------------------------------------- paints new image to the screen
    def onPaint(self_MP, evt):
        # BufferedPaintDC only works inside an event method.  ClientDC doesn't seem to do the job.
        try: self_MP.bmp    # ------ may have failed to create .bmp file
        except: pass
        else:
            thePanel = evt.GetEventObject()     # eventobject is the monitorPanel
            thePanel.SetSize(self_MP.panelSize)      # sometimes the event object is still not the right size.  Reset it just in case
            dc = wx.BufferedPaintDC(thePanel)       # create a buffered paint device context (DC)
            dc.DrawBitmap(self_MP.bmp, 0, 0, True)  # draw bitmap on the buffered DC

        evt.Skip()      # allow any other processing to complete

    # ------------- get mouse pointer coordinates in the preview panel and set upper left coordinates for mask generator
    def onLeftUp(self, event):
        try:    # ------ may have been clicked somewhere else, so don't fail
            (x_mouse, y_mouse) = event.GetPosition()
            x_source = x_mouse * self.initialSize[0] / self.panelSize[0]
            y_source = y_mouse * self.initialSize[1] / self.panelSize[1]

            self.parent.X[2].ChangeValue(x_source)                 # put values in (X,Y) on mask generator table
            self.parent.Y[2].ChangeValue(y_source)
        except: # ------ ignore the click
            pass

        event.Skip()        # continue any other processes for the click


# ------------------------------------------------------------------------------------------ Stand alone test code
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        gbl.mask_file = 'C:\Users\Lori\Documents\PyCharmProjects\Data\oneROI.msk'
        self.config = cfg.Configuration(self,'C:\Users\Lori\Documents\PyCharmProjects\Data\oneROI.cfg')
        thumb = monitorPanel(self, mon_ID=1, panelType='thumb', loop=True, rois=[])
        thumb.PlayMonitor()

        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "", (10,10), (600,400))           # Create the main window.    id, title, pos, size, style, name
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#
