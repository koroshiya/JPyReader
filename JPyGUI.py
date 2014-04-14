#!/usr/bin/python2.7 -tt

from __future__ import unicode_literals
import sys
if sys.version_info < (2, 7):
    print ("Must use python 2.7 or greater\n")
    sys.exit()
elif sys.version_info[0] > 2:
	print ("Incompatible with Python 3\n")
	sys.exit()

try:
	import wx
except ImportError:
	print ("You do not appear to have wxpython installed.\n")
	print ("Without wxpython, this program cannot run.\n")
	print ("You can download wxpython at: http://www.wxpython.org/download.php#stable \n")
	sys.exit()
from threading import Thread
import tempfile
import zipfile
import os
import wx.lib.scrolledpanel as scrolled
import Settings
import ImageManager

FILE_OPEN_DIRECTORY = 650
FILE_OPEN_ARCHIVE = 651
FILE_CLOSE = 666

VIEW_HIDE_MENU = 700
VIEW_HIDE_STATUS = 701
VIEW_MAXIMIZE = 702
VIEW_FULLSCREEN = 703

CMD_PREVIOUS = 801
CMD_NEXT = 802
CMD_FIRST = 803
CMD_LAST = 804
CMD_JUMP = 805

HELP_ABOUT = 900

class JPyGUI(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(JPyGUI, self).__init__(*args, **kwargs)

		self.SetDoubleBuffered(True)
		self.displays = (wx.Display(i) for i in range(wx.Display.GetCount()))
		self.sizes = [display.GetGeometry().GetSize() for display in self.displays]
		self.image_manager = ImageManager.ImageManager();
		self.image_manager.SetFrame(self);

		dt = FileDrop(self)
		dt.SetFrame(self)
		self.SetDropTarget(dt)

		self.Bind(wx.EVT_CLOSE, self.Exit)

		self.SetBackgroundColour(wx.BLACK)
		self.SetTitle("JPy-Reader")
		self.SetIcon(wx.Icon('jr.png', wx.BITMAP_TYPE_PNG))
		self.Settings = Settings.Settings();
		self.SetSize(self.Settings.size_init);
		self.SetMinSize(self.Settings.size_min);
		self.SetPosition(self.Settings.screen_pos)
		self.InitUI()
		if len(sys.argv) > 1:
			for arg in sys.argv:
				if (self.DisplayImage(arg)):
					break;

	def InitUI(self):

		self.ConstructMenu();
		self.spanel = wx.PyScrolledWindow(self)
		self.spanel.SetDoubleBuffered(True)
		self.spanel.SetScrollbars(1,1,1,1)
		self.spanel.SetScrollRate(1,1)
		self.spanel.SetPosition((0,0));
		self.spanel.SetBackgroundColour(wx.BLACK)

		self.panel = wx.StaticBitmap(self.spanel)

		self.panel.Bind(wx.EVT_LEFT_UP, self.image_manager.Next)
		self.Bind(wx.EVT_LEFT_UP, self.image_manager.Next)
		self.panel.Bind(wx.EVT_RIGHT_UP, self.image_manager.Previous)
		self.Bind(wx.EVT_RIGHT_UP, self.image_manager.Previous)
		self.panel.SetPosition((0,0));

		self.Bind(wx.EVT_MOUSEWHEEL, self.Print)
		self.panel.Bind(wx.EVT_MOUSEWHEEL, self.Print)
		self.spanel.Bind(wx.EVT_MOUSEWHEEL, self.Print)

		self.Show(True)

	def Print(self, e):
		if e.ControlDown():
			rotation = e.GetWheelRotation()
			if rotation > 0:
				if self.SCALE < 5:
					self.SCALE += 0.25
			else:
				if self.SCALE > 0.25:
					self.SCALE -= 0.25
			self.DisplayCachedImage();

	def ConstructMenu(self):

		self.menubar = wx.MenuBar();
		menuFile = wx.Menu()
		menuView = wx.Menu()
		menuCommands = wx.Menu()
		menuSettings = wx.Menu()
		menuHelp = wx.Menu()

		self.SetMenuItem(menuFile, FILE_OPEN_DIRECTORY, '&Open\tCtrl+O', self.OpenFolder);
		self.SetMenuItem(menuFile, FILE_OPEN_ARCHIVE, '&Open Archive\tCtrl+Z', self.OpenArchive);
		menuFile.AppendSeparator()
		self.SetMenuItem(menuFile, FILE_CLOSE, '&Quit\tCtrl+Q', self.Exit);

		#self.SetMenuItem(menuView, VIEW_HIDE_MENU, '&Hide Menu\tCtrl+H', self.HideMenu);
		self.SetMenuItem(menuView, VIEW_HIDE_STATUS, 'Hide &Status\tCtrl+Shift+H', self.HideStatus);
		self.SetMenuItem(menuView, VIEW_MAXIMIZE, '&Maximize\tCtrl+M', self.image_manager.Max);
		self.SetMenuItem(menuView, VIEW_FULLSCREEN, '&Fullscreen\tCtrl+F', self.image_manager.Full);

		self.SetMenuItem(menuCommands, CMD_PREVIOUS, '&Previous\tCtrl+LEFT', self.image_manager.Previous);
		self.SetMenuItem(menuCommands, CMD_NEXT, '&Next\tCtrl+RIGHT', self.image_manager.Next);
		self.SetMenuItem(menuCommands, CMD_FIRST, '&First\tCtrl+Shift+LEFT', self.image_manager.First);
		self.SetMenuItem(menuCommands, CMD_LAST, '&Last\tCtrl+Shift+RIGHT', self.image_manager.Last);
		menuCommands.AppendSeparator();
		self.SetMenuItem(menuCommands, CMD_JUMP, '&Jump to page...\tCtrl+J', self.image_manager.JumpToPage)

		self.SetMenuItem(menuHelp, HELP_ABOUT, '&About', self.About);

		#menuItemOpen.SetBitmap(wx.Bitmap('file.png'))

		self.menubar.Append(menuFile, '&File')
		self.menubar.Append(menuView, '&View')
		self.menubar.Append(menuCommands, '&Commands')
		self.menubar.Append(menuSettings, '&Settings')
		self.menubar.Append(menuHelp, '&Help')

		self.statusbar = self.CreateStatusBar()
		self.SetMenuBar(self.menubar);

	def SetMenuItem(self, menu, idn, text, event):
		mItem = wx.MenuItem(menu, idn, text)
		menu.AppendItem(mItem)
		self.Bind(wx.EVT_MENU, event, id=idn)

	def OpenArchive(self, e):
		openFileDialog = wx.FileDialog(self, "Open Archive file", "", "", "Archives (*.zip;*.cbz)|*.zip;*.cbz", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		tmpDir = tempfile.gettempdir()+"/jpyreader/"+openFileDialog.GetPath().rsplit('/',1)[1]+"/"
		if not os.path.exists(tmpDir):
			os.makedirs(tmpDir)
		print tmpDir
		self.ExtractZipFile(openFileDialog.GetPath(), tmpDir)
		#self.DisplayImage(openFileDialog.GetPath())

	def OpenFolder(self, e):
		openFileDialog = wx.DirDialog(self, "Select folder containing images to view")
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		self.URLList.LoadFile(openFileDialog.GetPath())

	def ExtractZipFile(self, filePath, tmpDir):
		zfile = zipfile.ZipFile(filePath, "r")
		fileList = []
		for name in zfile.namelist():
			ext = os.path.splitext(name)[1].lower()
			extensions = [".jpg", ".jpeg", ".png", ".bmp"]
			if ext in extensions:
				zfile.extract(name, tmpDir)
				fileList.append(name)
		if len(fileList) == 0:
			print "No applicable files found"
		else:
			self.image_manager.DisplayImage(tmpDir+fileList[0])

	def Exit(self, e):
		self.Settings.write(self);
		wx.Exit()

	def GetMonitor(self):
		posx, posy = self.GetScreenPosition()
		count = 0;
		for monitor in self.sizes:
			if posx < monitor.GetWidth():
				return count;
			count += 1
			posx -= monitor.GetWidth()
		return 0

	#def HideMenu(self, e):
	#	self.HideBar(self.menubar)

	def HideStatus(self, e):
		self.HideBar(self.statusbar)

	def HideBar(self, bar):
		bar.Hide() if bar.IsShown() else bar.Show();

	def About(self, e):
		info = wx.AboutDialogInfo()
		info.SetIcon(self.GetIcon()) #wx.Icon('jr.png', wx.BITMAP_TYPE_PNG)
		info.SetName("JPy-Reader")
		info.SetVersion("1.0")
		info.SetDescription("Test description")
		info.SetCopyright("(C) 2013 Koroshiya")
		wx.AboutBox(info)

class FileDrop(wx.FileDropTarget):
	def __init__(self, window):
		wx.FileDropTarget.__init__(self)
		self.window = window

	def SetFrame(self, frame):
		self.frame = frame;

	def OnDropFiles(self, x, y, filenames):

		for name in filenames:
			if (self.frame.image_manager.DisplayImage(name)):
				return;