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
import threading
import configurator as cfg
import videoMonitor as VM
import track
import pysolovideoGlobals as gbl
# from wx.lib.newevent import NewCommandEvent
# ThumbnailClickedEvt, EVT_THUMBNAIL_CLICKED = wx.lib.newevent.NewCommandEvent()  # NOT USED - click on thumbnail goes unnoticed

# TODO:  make click on thumbnail change to monitor configuration page

""" ============================================================================================== Video playback thread
"""
class videoThread (threading.Thread):                       # threading speeds up video processing
    def __init__(self, monitorPanel, (name)):
        threading.Thread.__init__(self)
        self.monitorPanel = monitorPanel                            # the video panel to be played in the panel
        self.name = name

    def run(self):
        self.monitorPanel.PlayMonitor()                             # start playing the video
        print('pause')

""" ============================================================================================= Object tracking thread
"""
class trackingThread (threading.Thread):                    # Thread that processes the video input
    def __init__(self, monitorPanel, (name)):
        threading.Thread.__init__(self)
        self.monitorPanel = monitorPanel                # the tracking object
        self.name = name

    def run(self):
        self.monitorPanel.startTrack()                    # starts tracking process


""" =================================================================================== Scrolling window of video panels
"""
class scrollingWindow(wx.ScrolledWindow):     # --------------------- contails a list of thumbnails in a scrolled window
    """
    Object is a scrolling window with either video preview panels or output consoles for tracking.
    """
    # ------------------------------------------------------------------------------------- initialize a scrolled window
    def __init__(self, parent):
        """
        Thumbs may be videoMonitor panels or console panels.  They are contained in the self.thumbPanels list
        and are mutually exclusive.
        """
        # --------------------------------------------------------------------------- Set up scrolling window
        self.parent = parent                                                                                            # TODO: can I just use .Parent instead of passing parent?

        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY, size=(-1, 300))
        self.SetScrollbars(1, 1, 1, 1)
        self.SetScrollRate(10, 10)

        self.thumbGridSizer = wx.GridSizer(3, 3, 5, 5)              # will contain the panels

        self.refreshGrid('thumb')       # -- put thumbnails in gridsizer and display in scrolled window
                                           # setsizer is done in calling program (cfgPanel)

    # --------------------------------------------------------------------- remove all video panels from scrolled window
    def clearGrid(self, panelType):     # TODO: console remains under thumbnail after view monitors
                                        # TODO: loop not turned back on in view monitors
        """ 
        threads must be stopped and panels must be destroyed or they will keep running in the background and cause          
        display problems                    
        """
        old_ID = gbl.mon_ID
        if len(self.thumbPanels) > 1:  # don't remove the 0th element, which is just a descriptor that allows 1-indexing
            for gbl.mon_ID in range(len(self.thumbPanels) -1, 0, -1):
                                                            # reverse order avoids issues with list renumbering
                self.thumbPanels[gbl.mon_ID]._Thread__stop()                                # stop the thread
                self.thumbPanels[gbl.mon_ID].monitorPanel.keepPlaying = False               # stop playing video

                # ------ the following actions may or may not work depending on the type of panel.
                # try all of them even if one fails.
                try: self.thumbPanels[gbl.mon_ID].monitorPanel.playTimer.Stop()             # stop the timer
                except: pass

                try: self.thumbPanels[gbl.mon_ID].monitorPanel.Hide()                       # hide panel from display
                except: pass

                try: self.thumbPanels[gbl.mon_ID].monitorPanel.console.Destroy()  # prevents dbld up images & flickering
                except: pass                            # hangs around if not destroyed before monitorPanel is destroyed

                try: self.thumbPanels[gbl.mon_ID].monitorPanel.Destroy()       # prevents doubled up images & flickering
                except: pass

            del self.thumbPanels[gbl.mon_ID]                                  # delete the panel from the list.

        self.thumbGridSizer.Clear()                                         # clear out gridsizer
        gbl.mon_ID = old_ID

    # ---------------------------------------------------------- Make list of thumbnails to populate the scrolled window
    def refreshGrid(self, panelType='thumb'):
        oldMonID = gbl.mon_ID

        if panelType == 'thumb':
            self.Parent.thumbFPSTxt.Show()
            self.Parent.thumbFPS.Show()            # restore these if they were hidden (not used for viewing consoles)

        self.thumbPanels = ['thumb panels']         # fill element 0 so monitors are 1-indexed

        # --------------------------------------------- go through each monitor configuration and make a thumbnail panel
        for gbl.mon_ID in range(1, gbl.monitors + 1):
            cfg.mon_dict_to_nicknames()

            if panelType == 'thumb':                        # 'preview' will never be used in the grid
                # create thread with thumbnail panel and add to grid
                self.thumbPanels.append(videoThread(VM.monitorPanel(self, mon_ID=gbl.mon_ID, panelType='thumb',
                                                                    loop=True), (gbl.mon_name)))
                self.thumbGridSizer.Add(self.thumbPanels[gbl.mon_ID].monitorPanel, 1, wx.ALIGN_CENTER_HORIZONTAL, 5)
                self.thumbPanels[gbl.mon_ID].start()                        # start the thread (before starting timer)

                interval = self.thumbPanels[gbl.mon_ID].monitorPanel.interval
                if not self.thumbPanels[gbl.mon_ID].monitorPanel.playTimer.IsRunning():
                    self.thumbPanels[gbl.mon_ID].monitorPanel.playTimer.Start(interval)     # start the timer

            elif panelType == 'console':
                self.thumbPanels.append(trackingThread(track.monitorPanel(self, mon_ID=gbl.mon_ID, videoOn=False),(gbl.mon_name)))
                self.thumbGridSizer.Add(self.thumbPanels[gbl.mon_ID].monitorPanel.console, 1, wx.ALIGN_CENTER_HORIZONTAL, 5)
                self.thumbPanels[gbl.mon_ID].start()                        # start the thread; no timer needed


        self.SetSizerAndFit(self.thumbGridSizer)
        self.Parent.Layout()                            # rearranges thumbnails into grid
                                                        # must use Parent to get display numbers in the right place

        gbl.mon_ID = oldMonID                           # go back to same page we came from
        if gbl.mon_ID != 0:
            cfg.mon_dict_to_nicknames()                 # restore nicknames to current monitor values



    def ignoreEvent(self, event):
        event.skip()
# ------------------------------------------------------------------------------------------ Stand alone test code

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        whatsit = scrollingWindow(self)

        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.


