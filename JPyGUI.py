#!/usr/bin/python2.7 -tt

import sys
if sys.version_info < (2, 7):
    print "Must use python 2.7 or greater\n"
    sys.exit()

try:
	import wx
except ImportError:
	print "You do not appear to have wxpython installed.\n"
	print "Without wxpython, this program cannot run.\n"
	print "You can download wxpython at: http://www.wxpython.org/download.php#stable \n"
	sys.exit()
from os.path import expanduser
from os.path import realpath
from os.path import isfile
from os.path import dirname
from threading import Thread
import wx.lib.scrolledpanel as scrolled
import glob

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

WIDTH_MIN = 500
WIDTH_INITIAL = 500
HEIGHT_MIN = 400
HEIGHT_INITIAL = 400

SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]

INDEXED_FILES = []

class JPyGUI(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(JPyGUI, self).__init__(*args, **kwargs)

		self.CUR_INDEX = 0
		self.TOTAL_LEN = 0
		self.displays = (wx.Display(i) for i in range(wx.Display.GetCount()))
		self.sizes = [display.GetGeometry().GetSize() for display in self.displays]

		dt = FileDrop(self)
		dt.SetFrame(self)
		self.SetDropTarget(dt)

		self.Bind(wx.EVT_CLOSE, self.Exit)

		self.SetBackgroundColour(wx.BLACK)
		self.SetTitle("JPy-Reader")
		self.SetIcon(wx.Icon('jr.png', wx.BITMAP_TYPE_PNG))
		self.SetSize((WIDTH_INITIAL,HEIGHT_INITIAL));
		self.SetMinSize((WIDTH_MIN,HEIGHT_MIN))
		self.InitUI()

	def InitUI(self):

		self.ConstructMenu();
		self.spanel = wx.PyScrolledWindow(self)
		self.spanel.SetScrollbars(1,1,1,1)
		self.spanel.SetScrollRate(1,1)
		self.spanel.SetPosition((0,0));
		self.spanel.SetBackgroundColour(wx.BLACK)

		self.panel = wx.StaticBitmap(self.spanel)

		self.panel.Bind(wx.EVT_LEFT_UP, self.Next)
		self.Bind(wx.EVT_LEFT_UP, self.Next)
		self.panel.Bind(wx.EVT_RIGHT_UP, self.Previous)
		self.Bind(wx.EVT_RIGHT_UP, self.Previous)
		self.panel.SetPosition((0,0));

		self.Show(True)

	def ConstructMenu(self):

		self.menubar = wx.MenuBar();
		menuFile = wx.Menu()
		menuView = wx.Menu()
		menuCommands = wx.Menu()
		menuSettings = wx.Menu()

		self.SetMenuItem(menuFile, FILE_OPEN_DIRECTORY, '&Open\tCtrl+O', self.Import);
		self.SetMenuItem(menuFile, FILE_OPEN_ARCHIVE, '&Open Archive\tCtrl+Z', self.Export);
		menuFile.AppendSeparator()
		self.SetMenuItem(menuFile, FILE_CLOSE, '&Quit\tCtrl+Q', self.Exit);

		self.SetMenuItem(menuView, VIEW_HIDE_MENU, '&Hide Menu\tCtrl+H', self.HideMenu);
		self.SetMenuItem(menuView, VIEW_HIDE_STATUS, 'Hide &Status\tCtrl+Shift+H', self.HideStatus);
		self.SetMenuItem(menuView, VIEW_MAXIMIZE, '&Maximize\tCtrl+M', self.Max);
		self.SetMenuItem(menuView, VIEW_FULLSCREEN, '&Fullscreen\tCtrl+F', self.Full);

		self.SetMenuItem(menuCommands, CMD_PREVIOUS, '&Previous\tCtrl+LEFT', self.Previous);
		self.SetMenuItem(menuCommands, CMD_NEXT, '&Next\tCtrl+RIGHT', self.Next);
		self.SetMenuItem(menuCommands, CMD_FIRST, '&First\tCtrl+Shift+LEFT', self.First);
		self.SetMenuItem(menuCommands, CMD_LAST, '&Last\tCtrl+Shift+RIGHT', self.Last);

		#menuItemOpen.SetBitmap(wx.Bitmap('file.png'))

		self.menubar.Append(menuFile, '&File')
		self.menubar.Append(menuView, '&View')
		self.menubar.Append(menuCommands, '&Commands')
		self.menubar.Append(menuSettings, '&Settings')

		self.statusbar = self.CreateStatusBar()
		self.SetMenuBar(self.menubar);

	def SetMenuItem(self, menu, idn, text, event):
		mItem = wx.MenuItem(menu, idn, text)
		menu.AppendItem(mItem)
		self.Bind(wx.EVT_MENU, event, id=idn)

	def Import(self, e):
		openFileDialog = wx.FileDialog(self, "Open Image file", "", "", "Image files (*.jpg;*.jpeg;*.png;*.gif;*.bmp)|*.jpg;*.jpeg;*.png;*.gif;*bmp", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		self.DisplayImage(openFileDialog.GetPath())

	def Export(self, e):
		openFileDialog = wx.DirDialog(self, "Select folder containing images to view")
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		self.URLList.LoadFile(openFileDialog.GetPath())

	def Exit(self, e):
		wx.Exit()

	def Max(self, e):
		if (self.IsMaximized()):
			self.Maximize(False);
			self.panel.SetPosition((0,0))
		else:
			self.Maximize(True);
			self.CenterImage();

	def Min(self, e):
		self.Iconize(not self.IsIconized())

	def Full(self, e):
		if (self.IsFullScreen()):
			self.ShowFullScreen(False);
			self.panel.SetPosition((0,0))
		else:
			self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL);
			self.CenterImage();

	def CenterImage(self):
		psize = self.panel.GetSize()
		monitor = self.sizes[self.GetMonitor()]
		x = psize.GetWidth()
		x2 = monitor.GetWidth()
		y = psize.GetHeight()
		y2 = monitor.GetHeight()

		width = 0 if (x > x2) else (x2 / 2 - x / 2)
		height = 0 if (y > y2) else (y2 / 2 - y / 2)
		self.panel.SetPosition((width, height))

	def GetMonitor(self):
		posx, posy = self.GetScreenPosition()
		count = 0;
		for monitor in self.sizes:
			if posx < monitor.GetWidth():
				return count;
			count += 1
			posx -= monitor.GetWidth()
		return 0

	def Next(self, e):
		total = self.TOTAL_LEN - 1;
		self.SwitchImage(total, 0, 1, total);

	def Previous(self, e):
		total = self.TOTAL_LEN - 1
		self.SwitchImage(0, total, -1, total);

	def First(self, e):
		total = self.TOTAL_LEN - 1
		if (total > 0):
			self.CUR_INDEX = 0;
			self.DisplayImageAtIndex();

	def Last(self, e):
		total = self.TOTAL_LEN - 1
		if (total > 0):
			self.CUR_INDEX = total;
			self.DisplayImageAtIndex();

	def SwitchImage(self, indexOne, indexTwo, inc, total):
		if (total > 0):
			self.CUR_INDEX = indexTwo if self.CUR_INDEX == indexOne else self.CUR_INDEX + inc
			self.DisplayImageAtIndex();

	def IsSupportedImage(self, image):
		for format in SUPPORTED_FORMATS:
			if image[-len(format):] == format:
				return True
		return False

	def DisplayImage(self, imageFile): 
		if not self.IsSupportedImage(imageFile):
			return False
		curdir = dirname(realpath(imageFile))
		INDEXED_FILES[:] = []
		for format in SUPPORTED_FORMATS:
			INDEXED_FILES.extend(glob.glob(curdir + "/*" + format));
		self.CUR_INDEX = 0
		for filec in INDEXED_FILES:
			if (filec == imageFile):
				break;
			self.CUR_INDEX += 1
		self.TOTAL_LEN = len(INDEXED_FILES)
		if self.CUR_INDEX >= self.TOTAL_LEN:
			self.CUR_INDEX = 0
		return self.DisplayImageAtIndex()

	def DisplayImageAtIndex(self):
		tmpIndex = INDEXED_FILES[self.CUR_INDEX]
		try:
			self.Freeze()
			jpg1 = wx.Image(tmpIndex, wx.BITMAP_TYPE_ANY).ConvertToBitmap();
			self.spanel.FitInside();
			self.panel.SetBitmap(jpg1);
			self.panel.SetClientSize(jpg1.GetSize());
			
			self.statusbar.SetStatusText(str(self.CUR_INDEX + 1) + "/" + str(self.TOTAL_LEN) + " - " + tmpIndex)
			
			#self.spanel.SetClientSize(self.panel.GetSize() + (width, height))
			self.spanel.SetVirtualSize(jpg1.GetSize())
			self.spanel.SetClientSize(jpg1.GetSize())
			#self.SetClientSize((1920,1080))
			self.SetClientSize(jpg1.GetSize())
			#self.SetSize((1920,1080))
			#self.Fit();

			self.spanel.SetScrollRate(20,20)
			self.spanel.SetScrollbars(1,1,1,1)
			self.spanel.FitInside();
			self.Thaw()
			return True
		except IOError:
			print "Image file %s not found" % tmpIndex
			self.Thaw()
			return False

	def HideMenu(self, e):
		self.HideBar(self.menubar)

	def HideStatus(self, e):
		self.HideBar(self.statusbar)

	def HideBar(self, bar):
		siz = bar.GetSize()
		fsiz = self.panel.GetSize()
		width = fsiz.GetWidth()
		height = fsiz.GetHeight()
		if bar.IsShown():
			bar.Hide();
			height += siz.GetHeight()
		else:
			bar.Show()
			height -= siz.GetHeight()
		self.panel.SetSize((width, height))
		print "before: " + str(fsiz)
		print "after: " + str(self.panel.GetSize())

	def onKey(self, event): 
	    keycode = event.GetKeyCode() 
	    print keycode
	    if keycode == wx.WXK_LEFT: 
	            print 'You pressed left arrow!' 
	    event.Skip() 

class FileDrop(wx.FileDropTarget):
	def __init__(self, window):
		wx.FileDropTarget.__init__(self)
		self.window = window

	def SetFrame(self, frame):
		self.frame = frame;

	def OnDropFiles(self, x, y, filenames):

		for name in filenames:
			if (self.frame.DisplayImage(name)):
				return;