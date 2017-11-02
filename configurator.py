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



#   There are three types of configuration parameter storage used:
#       1. ConfigParser configuration file which is loaded into cfg_obj    - involves I/O to disk (slow)
#               cfg_Obj is handled in the Configuration Class
#       2. Configuration dictionary in the global gbl.cfg_dict list    - more convenient representation of whole configuration
#       3. Global variables  (gbl)    - easy to reference variables that don't affect the dictionary until applied
#


# ----------------------------------------------------------------------------   Imports
import wx                               # GUI controls
import os                               # system controls
import winsound
from os.path import expanduser          # get user's home directory
import ConfigParser                     # configuration file handler
import wx.lib.newevent                  # mouse click event handling functions
import pysolovideoGlobals as gbl


# --------------------------------------------------------------------- configuration functions available to all modules
#   The following functions transfer values from one type of storage to another:


""" ================================================================================= functions related to configuration 
"""
# -------------------------------------------------------------- copy configuration global nickname values into cfg_dict
def cfg_nicknames_to_dicts():
    gbl.cfg_dict[0]['monitors'] =   gbl.monitors
#    gbl.cfg_dict[0]['webcams'] =    gbl.webcams
    gbl.cfg_dict[0]['thumb_size'] = gbl.thumb_size
    gbl.cfg_dict[0]['thumb_fps'] =  gbl.thumb_fps
    gbl.cfg_dict[0]['cfg_path'] =   gbl.cfg_path

# ------------------------------------------------------------- copy configuration cfg_dict values into global nicknames
def cfg_dict_to_nicknames():
    gbl.monitors =      gbl.cfg_dict[0]['monitors']
#    gbl.webcams =       gbl.cfg_dict[0]['webcams']
    gbl.thumb_size =    gbl.cfg_dict[0]['thumb_size']
    gbl.thumb_fps =     gbl.cfg_dict[0]['thumb_fps']
    gbl.cfg_path =      gbl.cfg_dict[0]['cfg_path']

# ------------------------------------------------ copy monitor global nickname values into cfg_dict for current monitor
def mon_nicknames_to_dicts(mon_ID):
    gbl.cfg_dict[mon_ID]['mon_name'] =          gbl.mon_name
    gbl.cfg_dict[mon_ID]['source_type'] =       gbl.source_type
    gbl.cfg_dict[mon_ID]['source'] =            gbl.source
    gbl.cfg_dict[mon_ID]['source_fps'] =        gbl.source_fps
    gbl.cfg_dict[mon_ID]['source_mmsize'] =     gbl.source_mmsize
    gbl.cfg_dict[mon_ID]['preview_size'] =      gbl.preview_size
    gbl.cfg_dict[mon_ID]['preview_fps'] =       gbl.preview_fps
    gbl.cfg_dict[mon_ID]['preview_font'] =      gbl.preview_font
    gbl.cfg_dict[mon_ID]['preview_RGBcolor'] =  gbl.preview_RGBcolor
    gbl.cfg_dict[mon_ID]['line_thickness'] =    gbl.line_thickness
    gbl.cfg_dict[mon_ID]['video_on'] =          gbl.video_on
#    gbl.cfg_dict[mon_ID]['issdmonitor'] =       gbl.issdmonitor        # NOT IN USE
    gbl.cfg_dict[mon_ID]['start_datetime'] =    gbl.start_datetime
    gbl.cfg_dict[mon_ID]['track'] =             gbl.track
    gbl.cfg_dict[mon_ID]['track_type'] =        gbl.track_type
    gbl.cfg_dict[mon_ID]['mask_file'] =         gbl.mask_file
    gbl.cfg_dict[mon_ID]['data_folder'] =       gbl.data_folder

# ------------------------------------------------------------------- copy monitor cfg_dict values into global nicknames
def mon_dict_to_nicknames():
    gbl.mon_name =          gbl.cfg_dict[gbl.mon_ID]['mon_name']
    gbl.source_type =       gbl.cfg_dict[gbl.mon_ID]['source_type']
    gbl.source =            gbl.cfg_dict[gbl.mon_ID]['source']
    gbl.source_fps =        gbl.cfg_dict[gbl.mon_ID]['source_fps']
    gbl.source_mmsize =     gbl.cfg_dict[gbl.mon_ID]['source_mmsize']
    gbl.preview_size =      gbl.cfg_dict[gbl.mon_ID]['preview_size']
    gbl.preview_fps =       gbl.cfg_dict[gbl.mon_ID]['preview_fps']
    gbl.preview_font =      gbl.cfg_dict[gbl.mon_ID]['preview_font']
    gbl.preview_RGBcolor =  gbl.cfg_dict[gbl.mon_ID]['preview_RGBcolor']
    gbl.line_thickness =    gbl.cfg_dict[gbl.mon_ID]['line_thickness']
    gbl.video_on =          gbl.cfg_dict[gbl.mon_ID]['video_on']
#    gbl.issdmonitor =       gbl.cfg_dict[gbl.mon_ID]['issdmonitor']        # NOT IN USE
    gbl.start_datetime =    gbl.cfg_dict[gbl.mon_ID]['start_datetime']
    gbl.track =             gbl.cfg_dict[gbl.mon_ID]['track']
    gbl.track_type =        gbl.cfg_dict[gbl.mon_ID]['track_type']
    gbl.mask_file =         gbl.cfg_dict[gbl.mon_ID]['mask_file']
    gbl.data_folder =       gbl.cfg_dict[gbl.mon_ID]['data_folder']

# -------------------------------------------------- If cfg has changed ask user about saving and save before proceeding
def Q_wantToSave(self, nextpage=None):
    dlg = wx.MessageDialog(self, 'Do you want to save the current configuration?',
                           style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
    answer = dlg.ShowModal()
    if answer == wx.ID_YES:    # ---------------------------------------------------------------- save everything
        cfg_nicknames_to_dicts()                        # save any changes made to the configuration
        mon_nicknames_to_dicts(gbl.mon_ID)              # save any changes made to the monitor
        self.TopLevelParent.config.cfgSaveAs(self)                            # save to cfg file

    elif answer == wx.ID_CANCEL:  # ----------------------------------- leave things alone and go back to same page
        nextpage = gbl.mon_ID

    elif answer == wx.ID_NO:    # --------------------------------- revert to old configuration and go to next page
        self.TopLevelParent.config.cfg_to_dicts()       # read config file and copy to cfg_dict
        cfg_dict_to_nicknames()                         # copy cfg_dict settings to nicknames
        mon_dict_to_nicknames()
        self.update_from_dicts()                        # copy nicknames to local variables
        self.Parent.notebookPages[gbl.mon_ID].rois = []

    dlg.Destroy()

    gbl.shouldSaveCfg = False               # user has decided, config is saved or reverted
    return nextpage



""" ================================================================= Contains and controls all configuration parameters
The configuration page.
"""
class Configuration(object):
    """
    Initiates program configuration
    Uses ConfigParser to store and retrieve

            options     section of configuration that pertains to program operation
            monitor#    section of configuration that pertains to video source #

        ----------  object attributes ---------------
            self.cfg_Obj   ConfigParser object
            cfg_dict       list of dictionaries containing all config parameters and their values, indexed on 'section, key'
                                    cfg_dict[0] contains options
                                    cfg_dict[n] where n is > 0 contains parameters for monitor n
            self.opt_keys       list of configuration option keys
            self.mon_keys       list of configration monitor keys

     """

    # -------------------------------------------------------------------- load a configuration or supply default values
    def __init__(self, parent, possiblePathName=None):
        # default values were loaded by importing pysolovideoGlobals.py

        if possiblePathName is None:
            possiblePathName = gbl.cfg_path         # supply default path if no pathname is provided
        self.parent = parent
        self.assignKeys()                           # creates lists of configuration keywords

    # ------------------------------------------------- make sure the expected file exists or create a default file
        if possiblePathName == '' :
            self.defaultDir = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files') # define a default output directory
            possiblePathName = os.path.join(self.defaultDir, 'pysolo_video.cfg')            # and filename

        self.filePathName = self.cfgGetFilePathName(parent, possiblePathName)   # allow user to select a different configuration
                                                                                # cancelling will leave defaults in place

        if self.filePathName is not None:
            self.loadConfigFile(self.filePathName)              # load the configuration file and copy into cfg_dict
        else:
            self.filePathName = 'None Selected'
            self.cfg_Obj = ConfigParser.RawConfigParser()      # create a ConfigParser object for when it's time to save
            # just keep using the global variables until the user saves the file

    # -------------------------------------------------------------------------------- create lists of cfg_dict keywords
    def assignKeys(self):

        # ----------------------------------------------------------------------------- program options
        self.opt_keys = ['monitors',        # number of monitors in the configuration
#                         'webcams',        # number of available webcams
                         'thumb_size',      # size to use for thumbnails
                         'thumb_fps',       # speed to use for thumbnails
                         'cfg_path']        # folder where configuration file is kept

        # ----------------------------------------------------------------------------- monitor parameters
        self.mon_keys = ['mon_name',        # name of monitor
                         'source_type',     # type of source (webcam = 0, video = 1, folder of images = 2)
                         'source',          # source file or webcam identifier
                         'source_fps',      # speed of video
                         'source_mmsize',   # physical frame size in mm
#                         'issdmonitor',     # is sleep deprivation monitor             # NOT IN USE
                         'preview_size',    # size to use for full size video display
                         'preview_fps',     # speed to use for full size video display
                         'preview_font',    # font to use for display column numbers
                         'preview_RGBcolor',# color to use for video display mask
                         'line_thickness',  # thickness of line around ROIs
                         'video_on',        # show video frame-by-frame while tracking
                         'start_datetime',  # date and time experiment started
                         'track',           # track this monitor or not?
                         'track_type',      # type of tracking to be used
                         'mask_file',       # contains ROI coordinates
                         'data_folder']     # folder where output should be saved

    # -------------------------------------------------------------------------------  get valid config file path & name
    def cfgGetFilePathName(self, parent, possiblePathName=''):
        """
        Lets user select or create a config file, and makes sure it is valid
        """

        # ------ if directory or file name are invalid, start file dialog
        if not(os.path.isfile(possiblePathName)):

            wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                       "All files (*.*)|*.*"  # adding space in here will mess it up!

            dlg = wx.FileDialog(parent,
                                message="Open configuration file ...",
                                defaultDir=gbl.cfg_path,
                                wildcard=wildcard,
                                style=wx.OPEN
                                )

            if dlg.ShowModal() == wx.ID_OK:                         # show the file browser window
                self.filePathName = dlg.GetPath()                   # get the filepath from the save dialog
            else:
                self.filePathName = None                            # no filename was selected

            dlg.Destroy()
        else:                                                   # supplied filename was valid so use it
            self.filePathName = possiblePathName

        if self.filePathName is not None:       # ------ this file's path is valid
            gbl.cfg_dict[0]['cfg_path'] = gbl.cfg_path = os.path.split(self.filePathName)[0]
        else:                                   # ------ no valid pathname.  supply default path.
            gbl.cfg_dict[0]['cfg_path'] = gbl.cfg_path = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')

        return self.filePathName

    # ---------------------------------------------------------------------- use dictionary to build ConfigParser object
    def dict_to_cfg_Obj(self):
        """
        Assumes that dictionaries are up to date.
        :return: Nothing
        """
        # ---------------------------------------------------------------------------------------------- options section
        if not self.cfg_Obj.has_section('Options'):      # make sure the options section exists in the cfg object
            self.cfg_Obj.add_section('Options')

        for key in self.opt_keys:                      # add parameters to options section
            self.cfg_Obj.set('Options', key, gbl.cfg_dict[0][key])

        # --------------------------------------------------------------------------------------------- monitor sections
        gbl.monitors = gbl.cfg_dict[0]['monitors']
        for gbl.mon_ID in range(1, gbl.monitors + 1):  # for each monitor make sure the section exists in cfg_obj
            mon_dict_to_nicknames()
            if not self.cfg_Obj.has_section(gbl.cfg_dict[gbl.mon_ID]['mon_name']):
                self.cfg_Obj.add_section(gbl.cfg_dict[gbl.mon_ID]['mon_name'])

            for key in self.mon_keys:                   # add parameters to this monitor section
                self.cfg_Obj.set(gbl.cfg_dict[gbl.mon_ID]['mon_name'], key, gbl.cfg_dict[gbl.mon_ID][key])

    # --------------------------------------------------------------------- use ConfigParser object to update dictionary
    def cfg_to_dicts(self):
        """
        Create list of dictionaries from cfg for easier lookup of configuration info.
        First element [0] contains Program Options.
        Remaining element's indices indicate monitor number.
        """

#        gbl.webcams_inuse = []  # webcam names will be added to list and counted       # NOT IN USE

        # ------------------------------------------------------------------------------------------------------ Options
        if not self.cfg_Obj.has_section('Options'):         # make sure the options section exists in the cfg object
            self.cfg_Obj.add_section('Options')

        for key in self.opt_keys:                               # fill dictionary with project parameters
            if self.cfg_Obj.has_option('Options', key):
                gbl.cfg_dict[0][key] = self.getValue('Options', key)
            else:
                gbl.cfg_dict[0][key] = None   # add the option to the dictionary even if it wasn't in cfg_Obj

        # ----------------------------------------------------------------------------------------------------- Monitors
        # number of monitors is sections -1 since options is not a monitor
        gbl.monitors = gbl.cfg_dict[0]['monitors'] = len(self.cfg_Obj._sections) -1

        dictSize = len(gbl.cfg_dict)                        # need to add a new dictionaries for any new monitors
        if gbl.monitors >= dictSize:
            for gbl.mon_ID in range(dictSize, gbl.monitors + 1):
                gbl.cfg_dict.append({})

        # --------------------------------------------------------------------------------------- add values to cfg_dict
        for gbl.mon_ID in range(1, gbl.monitors + 1):       # update dictionary using cfg_object values
            gbl.mon_name = gbl.cfg_dict[gbl.mon_ID]['mon_name'] = 'Monitor%d' % gbl.mon_ID

            for key in self.mon_keys:
                if self.cfg_Obj.has_option(gbl.mon_name,key):
                    gbl.cfg_dict[gbl.mon_ID][key] = self.getValue(gbl.mon_name, key)  # copy config info into dictionary
                else:                                               # use setting from monitor 1 if something is missing
                    gbl.cfg_dict[gbl.mon_ID][key] = gbl.cfg_dict[1][key]


#            if gbl.source[0:6] == 'Webcam':  # count the number of webcams
#                gbl.webcams_inuse.append(gbl.mon_name)
#        gbl.webcams = len(gbl.webcams_inuse)

    # -----------------------------------------------------  Load ConfigParser object from file and copy to dictionaries
    def loadConfigFile(self, filePathName=''):

        self.cfg_Obj = ConfigParser.RawConfigParser()       # create a ConfigParser object

        self.filePathName = filePathName
        try:  # -------  file could be corrupted
            self.cfg_Obj.read(self.filePathName)            # read the selected configuration file

        except:                                             # otherwise just use the default config dictionary as is
            gbl.statbar.SetStatusText('Invalid configuration file input.  Creating default.')
            winsound.Beep(600,200)
            self.dict_to_cfg_Obj()                          # apply the default configuration to the cfg object
            self.cfgSaveAs(self.parent)                         # save the cfg object to a cfg file

        self.cfg_to_dicts()                                 # update the config dictionary from the config file

    # ------------------------------------------------------------------------------------------------  Save config file
    def cfgSaveAs(self, parent):
        """
        Dictionary should be up to date before calling this function.
        Lets user select file and path where configuration will be saved. Saves using ConfigParser .write()
        """
        for section in self.cfg_Obj.sections():             # delete all monitors from configuration object
            if section != 'Options':                                # keep the Options section
                self.cfg_Obj.remove_section(section)

        self.dict_to_cfg_Obj()                              # and recreate monitor sections from dictionary

                                                            # get a filename for the configuration file
        wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                   "All files (*.*)|*.*"  # !! adding spaces in here will mess it up !!

        dlg = wx.FileDialog(parent,
                            message = "Save configuration as file ...",
                            defaultDir = gbl.cfg_path,
                            wildcard = wildcard,
                            style = (wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                            )

        if dlg.ShowModal() == wx.ID_OK:             # show the file browser window
            self.filePathName = dlg.GetPath()       # get the path from the save dialog
            dlg.Destroy()

            gbl.cfg_path = os.path.split(self.filePathName)[0]

            try:   # ------ save may fail
                with open(self.filePathName, 'wb') as configfile:
                    self.cfg_Obj.write(configfile)  # ConfigParser write to file
                configfile.close()
                gbl.shouldSaveCfg = False
                return self.filePathName
            except:# ------ failed to save configuration.  notify user
                gbl.statbar.SetStatusText('Failed to save configuration.')
                winsound.Beep(600, 200)
                return False

        else:
            return False            # failed to save configuration


    # ----------------------------------------------------- get cfg object string and convert into value of correct type
    def getValue(self, section, key):
        """
        get value from config file based on section and keyword
        Do some sanity checking to return tuple, integer and strings, datetimes, as required.
        """
        if  not self.cfg_Obj.has_option(section, key):      # does option exist?
            r = None
            return r

        r = self.cfg_Obj.get(section, key)      # get the value from cfg_obj

        r = gbl.correctType(r, key)             # sanity checker

        return r

    # ---------------------------------------------------------------- set a cfg_dict value based on cfg_obj information
    def setValue(self, section, key, value):

        if not self.cfg_Obj.has_section(section):           # find the desired section
            self.cfg_Obj.add_section(section)
        if not self.cfg_Obj.has_option(section, key):
            self.cfg_Obj.set(section, key)                  # if section is missing, create one

        self.cfg_Obj.set(section, key, value)
        element_no = section[7:8]                           # get cfg_dict index number from section name
        if element_no == '': element_no = '0'

        gbl.cfg_dict[int(element_no)][key] = value          # update cfg_dict

# ------------------------------------------------------------------------------------------ Stand alone test code

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

    # get configuration parameters and create dictionaries for each section
        config = Configuration(self)


        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.



