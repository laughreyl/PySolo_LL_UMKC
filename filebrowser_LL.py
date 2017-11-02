import wx
import os

class filebrowser_LL(wx.Panel):
    def __init__(self, parent,
                 id=wx.ID_ANY,
                 name='fileBrowser',                  # object name for filebrowser panel
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
        # button
                 btn_label="Browse",
                 btn_style=wx.BORDER_RAISED,
        # label
                 label_label='File Browser',                      # Text for label to left of text field
                 label_style=wx.ALIGN_LEFT | wx.DEFAULT,
        # text box
                 txt_style=wx.TE_PROCESS_ENTER | wx.TE_RICH,
        # file dialog box
                 message="Choose a file",
                 defaultDir=".",
                 defaultFile="",                      # possible filename
                 wildcard="*.*",
                 dlg_style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        # callback function
                 changeCallback=lambda x: x          # Optional callback called for all changes in value of the control
                 ):

        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=pos, size=size, style=0, name=name)

        self.changeCallback = changeCallback            # used to call a function if textctrl value changes

        # these parameters will need to be available to the browse button function
        self.parent      = parent
        self.message     = message
        self.defaultDir  = defaultDir
        self.defaultFile = defaultFile
        self.wildcard    = wildcard
        self.dlg_style   = dlg_style

        # create widgets
        self.labelbox  = wx.StaticText(self,  wx.ID_ANY, style=label_style, label=label_label, name=name + '_label')
        self.textbox   = wx.TextCtrl(self,    wx.ID_ANY, style=txt_style, name=name + '_textbox', size=size)
        self.browsebtn = wx.Button(self,      wx.ID_ANY, style=btn_style, label=btn_label,  name=name + '_button')

        self.browsebtn.Bind(wx.EVT_BUTTON,              self.onBrowseBtn)           # catches button click

        self.textbox.Bind(wx.EVT_TEXT_ENTER,            self.onChangeText)          # catches enter
        self.textbox.Bind(wx.EVT_KILL_FOCUS,            self.onChangeText)          # catches click in another widget
#        self.Bind(wx.EVT_NAVIGATION_KEY,                self.onChangeText)          # catches tab

        self.mainSizer = wx.FlexGridSizer(1,3,2,2)
        self.mainSizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.mainSizer.AddGrowableCol(1)

        self.txtctrlSizer = wx.BoxSizer(wx.VERTICAL)
        self.txtctrlSizer.Add(self.textbox,                 1, wx.ALL | wx.EXPAND, 2)

        self.mainSizer.Add(self.labelbox,                   0, wx.ALL | wx.EXPAND, 2)
        self.mainSizer.Add(self.txtctrlSizer,               1, wx.ALL | wx.EXPAND, 2)
        self.mainSizer.Add(self.browsebtn,                  0, wx.ALL | wx.EXPAND, 2)

        self.SetSizer(self.mainSizer)
        self.Layout()

    def onChangeText(self, event):
        filePathName = self.textbox.GetValue()

        if not os.path.isfile(filePathName):                   # clear textctrl if this was not a file
            filePathName = ''

        self.changeCallback(filePathName)               # passing the event doesn't pass the value

        event.Skip()                                            # moves cursor to next widget


    def onBrowseBtn(self, event):
        dlg = wx.FileDialog(self.parent, message=self.message,
                                  defaultDir=self.defaultDir,
                                  defaultFile=self.defaultFile,
                                  wildcard=self.wildcard,
                                  style=self.dlg_style)

        if dlg.ShowModal() == wx.ID_OK:
            filePathName = dlg.GetPath()       # get the path from the save dialog
            self.textbox.ChangeValue(filePathName)
            if self.changeCallback != 0:  # otherwise, call the callback function
                self.changeCallback(filePathName)              # passing the event doesn't pass the value

        dlg.Destroy()

        event.Skip()                                            # moves cursor to next widget

class folderbrowser_LL(wx.Panel):
    def __init__(self, parent,
                 id=wx.ID_ANY,
                 name='folderBrowser',  # object name for filebrowser panel
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
            # button
                 btn_label="Browse",
                 btn_style=wx.BORDER_RAISED,
            # label
                 label_label='Folder Browser',  # Text for label to left of text field
                 label_style=wx.ALIGN_LEFT | wx.DEFAULT,
            # text box
                 txt_style=wx.TE_PROCESS_ENTER | wx.TE_RICH,
            # file dialog box
                 message="Choose a folder.",
                 defaultDir=".",
                 dlg_style=wx.DD_DIR_MUST_EXIST,
            # callback function
                 changeCallback=lambda x: x  # Optional callback called for all changes in value of the control
                 ):

        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=pos, size=size, style=0, name=name)

        self.changeCallback = changeCallback  # used to call a function if textctrl value changes

        # these parameters will need to be available to the browse button function
        self.parent = parent
        self.message = message
        self.defaultDir = defaultDir
        self.dlg_style = dlg_style

        # create widgets
        self.labelbox = wx.StaticText(self, wx.ID_ANY, style=label_style, label=label_label, name=name + '_label')
        self.textbox = wx.TextCtrl(self, wx.ID_ANY, style=txt_style, name=name + '_textbox')
        self.browsebtn = wx.Button(self, wx.ID_ANY, style=btn_style, label=btn_label, name=name + '_button')

        self.browsebtn.Bind(wx.EVT_BUTTON, self.onBrowseBtn)  # catches button click
        self.textbox.Bind(wx.EVT_TEXT_ENTER, self.onChangeText)  # catches enter
        self.textbox.Bind(wx.EVT_KILL_FOCUS, self.onChangeText)  # catches click in another widget
        self.Bind(wx.EVT_NAVIGATION_KEY, self.onChangeText)  # catches tab

        self.mainSizer = wx.FlexGridSizer(1,3,2,2)
        self.mainSizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.mainSizer.AddGrowableCol(1)

        self.txtctrlSizer = wx.BoxSizer(wx.VERTICAL)
        self.txtctrlSizer.Add(self.textbox,                 1, wx.ALL | wx.EXPAND, 2)

        self.mainSizer.Add(self.labelbox,                   0, wx.ALL | wx.EXPAND, 2)
        self.mainSizer.Add(self.txtctrlSizer,               1, wx.ALL | wx.EXPAND, 2)
        self.mainSizer.Add(self.browsebtn,                  0, wx.ALL | wx.EXPAND, 2)

        self.SetSizer(self.mainSizer)
        self.Layout()

    def onChangeText(self, event):
        filePathName = self.textbox.GetValue()

        if not os.path.isdir(filePathName):  # clear textctrl if this was not a file
            filePathName = ''

        self.changeCallback(filePathName)                   # event does not contain value

        event.Skip()


    def onBrowseBtn(self, event):
        dlg = wx.DirDialog(self.parent, message=self.message,
                           defaultPath=self.defaultDir,
                           style=self.dlg_style)

        if dlg.ShowModal() == wx.ID_OK:
            filePathName = dlg.GetPath()  # get the path from the save dialog
            self.textbox.ChangeValue(filePathName)
            if self.changeCallback != 0:  # otherwise, call the callback function
                self.changeCallback(filePathName)

        dlg.Destroy()

        event.Skip()


# ------------------------------------------------------------------------------------------ Stand alone test code

#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        newfile = filebrowser_LL(self)
        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.


