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



import wx
import os
import cv2
import numpy as np
import copy
import pysolovideoGlobals as gbl
import configurator as cfg
import videoMonitor as VM
import math
import datetime
from itertools import repeat  # generate tab-delimited zeroes to fill in extra columns
import winsound
import cPickle



""" =================================================================================================== Tracking console
Textctrl panel that reports tracking progress
"""
class consolePanel(wx.TextCtrl):
    # -------------------------------------------------------------------------------------- initialize the Textctrl box
    def __init__(self, parent, size=(200, 200)):    # parent is the cfgPanel
        self.mon_ID = gbl.mon_ID                    # keep track of which monitor this console is for
        style = wx.TE_MULTILINE | wx.TE_RICH | wx.TE_AUTO_SCROLL | wx.HSCROLL | wx.VSCROLL | wx.TE_READONLY
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, size=size, style=style, name=gbl.mon_name)

    # ----------------------------------------------------- writes message to the Textctrl box and refreshes the display
    def writemsg(self, message):
        self.AppendText(message + '\n')
        self.Parent.SetSizer(self.Parent.thumbGridSizer)
        self.Refresh()
        self.Layout()


""" ====================================================================================================== Tracked video
Tracks objects in the video, producing distance traveled report.
"""
class monitorPanel(object):
    # -------------------------------------------------------------------------------------------- initialize the object
    def __init__(self, parent, mon_ID, videoOn=False):
        self.parent =           parent
        self.mon_ID =           gbl.mon_ID = mon_ID  # make sure the settings for this monitor are in the nicknames
        self.videoOn =          videoOn             # normally don't want to watch frame by frame during tracking

        cfg.mon_dict_to_nicknames()
        # ---------------------------------------------- copy source settings to self to protect from threading
        self.mon_name =         gbl.mon_name
        self.source_type =      gbl.source_type
        self.source =           gbl.source
        self.devnum =           0                         # only one camera is currently supported
        self.mmsize =           gbl.source_mmsize
        self.fps =              gbl.source_fps
        self.preview_size =     gbl.preview_size            # used to set console size
        self.start_datetime =   gbl.start_datetime
        self.mask_file =        gbl.mask_file
        self.data_folder =      gbl.data_folder

        # ------ variables unique to this class
        self.loop =             False                       # never loop tracking
        self.keepPlaying =      False                # don't start yet
        self.outputprefix =     os.path.join(self.data_folder, self.mon_name)
        self.console =          consolePanel(parent, size=gbl.thumb_size)                    # the output console

        # ------------------------------------ use the sourcetype to create the correct type of object for capture
        if self.source_type == 0:
            self.captureMovie = VM.realCam(self.mon_ID, 1, devnum=0)        # NOT IN USE
        elif self.source_type == 1:
            self.captureMovie = VM.virtualCamMovie(self.mon_ID, 1, self.source, loop=False)
        elif self.source_type == 2:
            self.captureMovie = VM.virtualCamFrames(self.mon_ID, 1, self.source, loop=False)

        (self.cols, self.rows) =  self.size = self.captureMovie.initialSize
        self.distscale =         (float(self.mmsize[0])/float(self.size[0]), float(self.mmsize[1])/float(self.size[1]))
        self.areascale =          self.distscale[0] * self.distscale[1]

        self.haveMask = self.loadROIsfromMaskFile()  # -----------------------------------------------ROIs

    def loadROIsfromMaskFile(self):
        # returns empty list if mask file doesn't load
        # identical to function in videoMonitor.py

        if self.mask_file is None:
            gbl.statbar.SetStatusText('Mask file not found')
            winsound.Beep(600, 200)
            return False                                    # sets the haveMask flag to show that mask was not loaded

        if os.path.isfile(self.mask_file):  # if mask file is there, try to load ROIs
            try:  # ------ mask file could be corrupt
                cf = open(self.mask_file, 'r')  # read mask file
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

        self.rois = []
        # ------------------------------------------------------------------------------------------ make gbl.ROIs
        for roi in ROItuples:  # complete each rectangle by adding first coordinate to end of list
            roiList = []  # clear for each rectangle
            for coordinate in roi:  # add each coordinate to the list for the rectangle
                roiList.append(coordinate)
            roiList.append(roi[0])
            self.rois.append(roiList)  # add the rectangle lists to the list of ROIs

        return  True                                    # sets the haveMask flag to show that mask was loaded

    # --------------------------------------------------------------------------------------------------- begin tracking
    def startTrack(self, show_raw_diff=False, drawPath=True):
        """
        Collect the locations of the flies in each frame of the video
        Calculate the distance between locations from one frame to the next
        If a fly disappears, use the prior location so that distance == 0
        Sum the distances
        """

        # ------------------------------------------------------------------------ notify user that tracking has started
        gbl.statbar.SetStatusText('Tracking started: ' + self.mon_name)
        self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Start tracking monitor %d.' % self.mon_ID)

        # ------------------------------------------------------------------------------- locate and calculate distances
        fly_coords = self.getCoordsArray()                  # find coordinates of flies in each ROI in each frame
        distByMinute = self.calcDistances(fly_coords)       # calculate distance each fly travelled in each minute
        outputArrays = self.colSplit32(distByMinute)        # split data into 32 ROI groups for output to files

        # ---------------------------------------------------------------------------------------------- output the data
        self.outputprefix = self.checkFilenames(len(outputArrays))      # prevent overwriting of files

        for batch in range(0, len(outputArrays)):
            outputfile = self.outputprefix + str(batch + 1) + '.txt'    # create a filename for saving

            f_out = open(outputfile, 'a')                                                                       # TODO: if output fails, notify user
            for rownum in range(0, len(outputArrays[batch])):
                f_out.write(outputArrays[batch][rownum])                # output the data
            f_out.close()

            outputfile = os.path.split(self.outputprefix)[1]            # print output filename to console for user
            self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Output file names start with:  %s' % outputfile)
#            self.parent.trkdConsList[self.mon_ID].SetFocus()

        self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Acquisition of Monitor %d is finished.' % self.mon_ID)
        gbl.statbar.SetStatusText('')

    # -------------------------------------------------------------create table of fly coordinates for entire video
    # every ROI, every frame
    def getCoordsArray(self):
        self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('collecting coordinates for monitor %d' % self.mon_ID)

        keepgoing = True
        fly_coords = []
        self.frameCount = 0

        # ---------------------------------------------------- process first frame, which can't be compared to anything.
        frame = self.captureMovie.getImage()
        try:
            frame[0]        # verify that the frame has data
        except:
            keepgoing = False       # if not, end tracking
            self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('End of video.')
            return fly_coords

        # ------------------------------------------------ make 2D array of fly coordinates for every ROI in every frame
        # first set of previous coordinates - get locations from frame.  if no fly is found, location will be (0,0)
        previousFrame_fly_coords = self.getFrameFlyCoords(frame, [(0,0)]*len(self.rois))

        while keepgoing:                     # goes through WHOLE video
            # each of the 3 video input classes has a "getImage" function.
            # CaptureMovie is either video file, or a folder
            frame = self.captureMovie.getImage()                                    # get image
            try:
                frame[0]                                                            # verify that the frame has data
            except:
                keepgoing = False           # if not, stop tracking
                self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('End of video.')
                return fly_coords

            self.frameCount = self.frameCount + 1
            if self.frameCount/20.0 == int(self.frameCount/20):     # periodically update the console for the user
                self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Frame # %d' % self.frameCount)

            # --------------------------------------------------- collect coordinates for every ROI in this frame
            fly_coords.append(self.getFrameFlyCoords(frame, previousFrame_fly_coords))

            previousFrame_fly_coords = fly_coords[-1]       # save this frame as previous in case fly disappears

        return fly_coords

    # ------------------------------------------------------------------------ returns all fly coordinates for one frame
    def getFrameFlyCoords(self, grey_image, previousCoords):

        fliesInFrame = []
        for self.flyNum in range(0, len(self.rois)):
            ROI = self.rois[self.flyNum]
            ROIimg = grey_image[ROI[0][1]:ROI[2][1],ROI[0][0]:ROI[2][0]]    # make a mini-image of the ROI

            # prepare the ROI for object recognition.
            # By doing the preparation inside the ROI instead of over the whole image, contrast issues are reduced.
            bw_image = self.prepImage(ROIimg)          # convert image to binary b&w

            # ------------------------------------------------------- get coordinates of center of this fly in ROI
            fliesInFrame.append(self.getFlyCoords(bw_image, previousCoords[self.flyNum]))


        return fliesInFrame         # all fly location for each ROI in one frame

    # ------------------------------------------------------------------------------ returns coordinates of a single fly
    def getFlyCoords(self, ROIimg, previousCoords):
        contrimg = copy.deepcopy(ROIimg)                # findcontours overwrites the images, so save a copy for showing
        contours, hierarchy = cv2.findContours(contrimg, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # find contours

        # use the smallest region for the fly
        flyArea = []
        if len(contours) == 3:  # if there's a fly, there will be 3 contours: edge of frame, edge of cell, and fly   # TODO:  why is this different from what happens in adptThreshold?
            for contour in contours:
                flyArea.append(cv2.contourArea(contour))  # find the area of each contour
            # -------------------------------------------------------------------------------------------------------------------------- debug
            # if "Watch Video Tracking" is checked on the monitor configuration page, display the ROI images
            if self.videoOn == True:
                self.debug3img(self.origROIimg, ROIimg, contrimg, contours)  # #
            # --------------------------------------------------------------------------------------------------------------------------

            # smallest contour represents the fly
            val, flyidx = min((val, idx) for (idx, val) in enumerate(flyArea))
            # coordinates (x, y, w, h) of a rectangle around the outside of the contour
            fly_rect = cv2.boundingRect(contours[flyidx])

        else:
            return previousCoords  # no fly found. use coords from previous frame so motion = 0

        # use center of rectangle as center of fly.  # TODO: tracking will not account for turning in place
        return ((fly_rect[0] + fly_rect[2] / 2),  # x-coordinate
                (fly_rect[1] + fly_rect[3] / 2))  # y-coordinate

    # ----------------------------------- displays 3 images: original, B&W, and contours ----------------------------------- debug - shows images
    def debug3img(self, origimg, bwimg, contrimg, contours):                # TODO: videoOn didn't show videos
        # Use this function by checking the box "Watch Video Tracking" on the monitor configuration panel
        # draw bounding rectangles on the contours image, then combine all three images into one and display

        cv2.drawContours(contrimg, contours, -1, (100, 0, 0), 1)        # draws the contours on the frame in gray

        for contour in contours:                            # draw bounding rectangle for each contour
            rect = cv2.boundingRect(contour)
            pt1 = (rect[0], rect[1])                        # upper left corner
            pt2 = (rect[0] + rect[2], rect[1] + rect[3])    # lower right corner
            cv2.rectangle(contrimg, pt1, pt2, 150, 1)       # draw the rectangle in gray with line thickness of 1 pixel

        allimgs = np.hstack((self.origROIimg, bwimg, contrimg))     # combine the images into one array, side-by-side

        # display the combined image.  if it fails, stop showing images.
        self.videoOn = gbl.debugimg(allimgs, outprefix='fly%d-frame%d' % (self.flyNum, self.frameCount))

    # ----------------------------------------------------------------------- convert from gray scale to black and white
    def prepImage(self, frame):
        # ----------blurs edges
        frameBlurred = cv2.GaussianBlur(frame, (3, 3), 0)  # height & width of kernel must be odd and positive
        try:
            grey_image = cv2.cvtColor(frameBlurred, cv2.COLOR_BGR2GRAY)  # remove color & collapse to 2D array
        except:
            self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Cannot cvtColor in track.py prepImage.  Tracking stopped.')
#            self.parent.trkdConsList[self.mon_ID].SetFocus()
            self.keepPlaying = False
            return frame

        #""" -------------------------------------------------------------------------------------------------------------------------------debug
        self.origROIimg = grey_image                    # for comparing images in getFlyCoords
        #""" -------------------------------------------------------------------------------------------------------------------------------

        # select a threshold that reveals a fly-like object (expect 2 contours: edge of cell and fly) & get B&W image
        retvalue, bw_image = self.adptThreshold(grey_image)
        bw_image = cv2.morphologyEx(bw_image, cv2.MORPH_OPEN, (2, 2))           # remove noise (dilate and erode)
        bw_image = 255 - bw_image  # flies need to be white on black background for using cv2.contours

        return bw_image

    # -------------------------- determine which threshold value produces 2 contours in the image and return a B&W image
    def adptThreshold(self, img):
        # goal is to choose threshold value that produces two contours in the image
        # cv2 adaptive threshold function results in messy pictures & can't isolate flies
        # ideally the image should have 2 contours:  the edge of the cell, and the fly

        for testValue in range(45, 150, 5):
            retvalue, bw_image = cv2.threshold(img, testValue, 255, cv2.THRESH_BINARY)  # convert to black & white

            contrimg = copy.deepcopy(bw_image)     # find contours function will write over the image so keep a copy to show
            contours, hierarchy = cv2.findContours(contrimg, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # find contours
            if len(contours) == 2:        # on is cell edge, other is fly              # TODO: why is this different from what happens in getFlyCoords?
                return retvalue, bw_image

        # if no setting produced 2 contours, use value of 75 and move on
        retvalue, bw_image = cv2.threshold(img, 75, 255, cv2.THRESH_BINARY)
        return retvalue, bw_image

    # ----------------------------------------------------- calculate distances travelled in millimeters over one minute
    def calcDistances(self, fly_coords):                # TODO: too many zeroes  (used unsaved config?)

        # Now that all fly coordinates are known, calculate distances

        self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Calculating distances for monitor %d' % self.mon_ID)


        distByMinute =          []  # this is the tracking data we're producing in pixels per minute
        self.previousFrame = fly_coords[0]
        for self.frameCount in range(0, len(fly_coords), int(60 * self.fps)):  # for each one minute interval
            # ------ collect distance values for each ROI for 60 seconds
            subsetCoordinates = fly_coords[self.frameCount:(self.frameCount + int(60 * self.fps))] #one minute worth of frames
            distByMinute.append(self.getDistances(subsetCoordinates, self.frameCount))  # append to array of distance calculations

        return distByMinute

    # ------------------------------------------------------- tabulates distance travelled by every fly between 2 frames
    def getDistances(self, coords, currentFrame):
        totalDists = np.zeros(len(self.rois), dtype=int)  # tabulation of distances travelled in each ROI throughout video
        theseDists = np.zeros(len(self.rois))             # array of distances travelled between 2 frames for each ROI

        for thisFrame in coords:
            d_squareds = np.square(np.subtract(self.previousFrame, thisFrame))  # (x1-x2)^2, (y1-y2)^2 for each element
            d_squareds = d_squareds * self.distscale      # convert pixels to distance in mm based on user provided frame size

            for roiNum in range(0, len(d_squareds)):      # iterate through the ROIs, calculating distances
                flyDist = np.sqrt(d_squareds[roiNum][0] + d_squareds[roiNum][1])  # d = sqrt(x^2 + y^2)

                theseDists[roiNum] = flyDist

            totalDists = totalDists + theseDists            # adds these distances to the running tab

            self.previousFrame = thisFrame                  # store for comparison with next frame
            currentFrame = currentFrame +1                  # keeps track of actual frame number in whole video

        return totalDists

    # ----------------------------------------------- split data into files with 32 ROIs each for use in DAMFileScan110X
    def colSplit32(self, array):
        # cannot use wxDateTime.AddTS because it changes date to 1/1/1970.
        # Instead, use python datatime for generating the datetime stamps for each row of data

        self.parent.thumbPanels[self.mon_ID].monitorPanel.console.writemsg('Splitting monitor %d' % self.mon_ID)
#        self.parent.trkdConsList[self.mon_ID].SetFocus()

        oneMinute = datetime.timedelta(minutes = 1)
        monitorDateTime = self.start_datetime
        rownum = 1

        # ----------------------------------------------------------- determine how many files are needed and prep array
        listofFilesContents = []
        moreFilesNeeded = int(math.ceil((len(array[0]) - 10) / 32.0))    # number of additional files needed
        for num in range(0, 1 + moreFilesNeeded):
            listofFilesContents.append([])                            # create an empty list for each file to be created

        # all the files are being generated at the same time by adding 32 elements of the row to each file before going
        # to the next row.
        for rowdata in array:
            # ------------------------------------------------------------------------- create first 10 columns (prefix)
            if rownum <> 1:
                monitorDateTime = monitorDateTime + oneMinute            # get the date and time for this row of data

            # column 0 is the row number, column 1 is the date
            prefix = str(rownum) + '\t' + datetime.datetime.strftime(monitorDateTime, '%d %b %y\t%H:%M:%S')

            # next 7 columns are not used but DAMFileScan110X does not take 0000000 or 1111111
            prefix = prefix + '\t1\t1\t0\t0\t0\t0\t0'

            # -------------------- split row into 32 ROIs per file
            # last 32 or fewer columns will be handled after this loop
            for batch in range(0, moreFilesNeeded):
                datastring = prefix           # start the row with the prefix

                startcol = batch * 32         # calculate start and end columns for this file (rowdata is 0-indexed)
                endcol = startcol + 32

                for number in rowdata[startcol:endcol]:           # add the 32 data values to the row
                    datastring = datastring + '\t%d' % number

                # append the row to list "listofFilesContents[batch]" for this file
                listofFilesContents[batch].append(datastring + '\n')

            # ------------------------------------------------------------------ handle last 32 or fewer columns of data
            datastring = prefix

            startcol = (moreFilesNeeded) * 32        # all but one file of data from rowdata has been added
            endcol = startcol + len(rowdata)         # include remaining data in this file

            for number in rowdata[startcol:endcol]:                 # add data to the string
                datastring = datastring + '\t%d' % number

            # -------------------------------------------------------- pad with zeros until 32 columns of data are added
            if len(rowdata) != moreFilesNeeded * 32:
                morecols = (moreFilesNeeded+1) * 32 - len(rowdata)        # calculate how many zero columns are needed

                datastring = datastring + '\t' + '\t'.join(list(repeat('0', morecols))) + '\n'      # add the zeros

            listofFilesContents[moreFilesNeeded].append(datastring)  # ----  append data to last batch (0-indexed)

            rownum = rownum +1

        return listofFilesContents          # returns array containing list of all files with their contents

    # -------------------------------------------- requests a different filename prefix to prevent overwritting of files
    def tryNewName(self):
        defaultDir = os.path.split(self.outputprefix)[0]
        wildcard = "File Prefix |*.txt|" \
                       "All files (*.*)|*.*"

        dlg = wx.FileDialog(self.parent,
                            message="Choose a different output prefix for Monitor %d ..." % self.mon_ID,
                            defaultDir=defaultDir, wildcard=wildcard, style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
            self.outputprefix = dlg.GetPath()[0:-4]  # get the filepath & name from the save dialog, don't use extension
        else:
            self.outputprefix = ''

        dlg.Destroy()
        return self.outputprefix

    # -------------------------------------------------------------------- gets valid output name and avoids overwriting
    def checkFilenames(self, moreFilesNeeded):
        goodname = False
        if not os.path.isdir(os.path.split(self.outputprefix)[0]):          # ------ directory must exist
            self.outputprefix = self.tryNewName()

        while not goodname:                                     # test to see if files will be overwritten
            goodname = True     # assume name is good until proven otherwise
            for batch in range(0, moreFilesNeeded):                             # ------ check for each output file
                outputfile = self.outputprefix + str(batch + 1) + '.txt'  # create a filename for saving

                if goodname  and  os.path.isfile(outputfile):
                    gbl.statbar.SetStatusText('Avoid overwrite: File -> ' + outputfile + ' <- already exists.')
                    winsound.Beep(600, 200)
                    goodname = False

            if not goodname:
                self.outputprefix = self.tryNewName()       # ask for a new prefix

        return self.outputprefix

# ------------------------------------------------------------------------------------------ Stand alone test code

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, None, id=wx.ID_ANY, size=(1000,200))



        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#

