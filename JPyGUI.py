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
from os.path import realpath
import cStringIO
import wx.lib.scrolledpanel as scrolled
import Settings
from rarfile import rarfile
import ImageManager

FILE_OPEN_DIRECTORY = 650
FILE_OPEN_ARCHIVE = 651
FILE_CLOSE = 666

VIEW_HIDE_MENU = 700
VIEW_HIDE_STATUS = 701
VIEW_MAXIMIZE = 702
VIEW_FULLSCREEN = 703
VIEW_ZOOM = 704

ZOOM_ONE = 100
ZOOM_TWO_THIRD = 67
ZOOM_HALF = 50

CMD_PREVIOUS = 801
CMD_NEXT = 802
CMD_FIRST = 803
CMD_LAST = 804
CMD_JUMP = 805

CMD_ZIP = 810
CMD_ZIP_EXTRACT = 811
CMD_ZIP_READ = 812
CMD_ZIP_RAM = 813

CMD_RAR = 820
CMD_RAR_EXTRACT = 821
CMD_RAR_READ = 822
CMD_RAR_RAM = 823

HELP_ABOUT = 900
HELP_HOTKEYS = 901

class JPyGUI(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(JPyGUI, self).__init__(*args, **kwargs)

		self.Freeze()

		self.SetDoubleBuffered(True)
		self.displays = (wx.Display(i) for i in range(wx.Display.GetCount()))
		self.sizes = [display.GetGeometry().GetSize() for display in self.displays]
		self.image_manager = ImageManager.ImageManager()
		self.image_manager.SetFrame(self)

		self.rar = [0, [], []]
		self.zip = [0, [], []]
		self.SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
		self.SUPPORTED_ARCHIVE_FORMATS = [".zip", ".cbz", ".rar", ".cbr"]

		dt = FileDrop(self)
		dt.SetFrame(self)
		self.SetDropTarget(dt)

		self.Bind(wx.EVT_CLOSE, self.Exit)
		self.Bind(wx.EVT_MAXIMIZE, self.image_manager.Max)
		self.Bind(wx.EVT_SIZE, self.image_manager.Resize)

		self.SetBackgroundColour(wx.BLACK)
		self.SetTitle("JPy-Reader")
		try:
			os.chdir(os.path.dirname(__file__))
			self.SetIcon(wx.Icon('jr.png', wx.BITMAP_TYPE_PNG))
		except:
			pass
		self.Settings = Settings.Settings()
		self.SetSize(self.Settings.size_init)
		self.SetMinSize(self.Settings.size_min)
		self.SetPosition(self.Settings.screen_pos)
		self.InitUI()

		rarMode = self.Settings.rarMode
		if rarMode == 1:
			self.RarExtractMode_01.Check()
		elif rarMode == 2:
			self.RarExtractMode_02.Check()

		zipMode = self.Settings.zipMode
		if zipMode == 1:
			self.ZipExtractMode_01.Check()
		elif zipMode == 2:
			self.ZipExtractMode_02.Check()

		if len(sys.argv) > 1:
			for name in sys.argv:
				if not self.CheckArg(name):
					break

		if self.Settings.fullscreen:
			self.image_manager.Full("")
		elif self.Settings.maximized:
			self.image_manager.Max("")
		self.Thaw()

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
		self.spanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.spanel.SetFocus()
		self.panel.Bind(wx.EVT_SET_FOCUS, self.onFocus)
		self.Bind(wx.EVT_SET_FOCUS, self.onFocus)

		self.Show(True)
	
	def onFocus(self, event):
		self.spanel.SetFocus()

	def OnKeyDown(self, e):
		key = e.GetKeyCode()
        
		if key == wx.WXK_ESCAPE:
			self.Exit(e)
		elif key == wx.WXK_RIGHT:
			self.image_manager.Next(e)
		elif key == wx.WXK_LEFT:
			self.image_manager.Previous(e)
		else:
			print "Pressed key", key

	def Print(self, e):
		if e.ControlDown():
			rotation = e.GetWheelRotation()
			if rotation > 0:
				if self.image_manager.SCALE < 5:
					self.image_manager.SCALE += 0.25
			else:
				if self.image_manager.SCALE > 0.25:
					self.image_manager.SCALE -= 0.25
			self.image_manager.DisplayImageAtIndex();
		else:
			e.Skip()

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
		self.SetMenuItem(menuView, VIEW_HIDE_STATUS, '&Show/Hide Status\tCtrl+Shift+H', self.HideStatus);
		self.SetMenuItem(menuView, VIEW_MAXIMIZE, '&Maximize\tCtrl+M', self.image_manager.Max);
		self.SetMenuItem(menuView, VIEW_FULLSCREEN, '&Fullscreen\tCtrl+F', self.image_manager.Full);

		zoomMenu = wx.Menu()
		self.Zoom_100 = zoomMenu.Append(ZOOM_ONE, '100%', kind=wx.ITEM_RADIO) #self.image_manager.SetZipMode(0)
		self.Zoom_66 = zoomMenu.Append(ZOOM_TWO_THIRD, '66%', kind=wx.ITEM_RADIO)
		self.Zoom_50 = zoomMenu.Append(ZOOM_HALF, '50%', kind=wx.ITEM_RADIO)
		menuView.AppendMenu(VIEW_ZOOM, "Zoom", zoomMenu)

		self.Bind(wx.EVT_MENU, self.ChangeZoom, id=ZOOM_ONE)
		self.Bind(wx.EVT_MENU, self.ChangeZoom, id=ZOOM_TWO_THIRD)
		self.Bind(wx.EVT_MENU, self.ChangeZoom, id=ZOOM_HALF)

		self.SetMenuItem(menuCommands, CMD_PREVIOUS, '&Previous\tLEFT', self.image_manager.Previous);
		self.SetMenuItem(menuCommands, CMD_NEXT, '&Next\tRIGHT', self.image_manager.Next);
		self.SetMenuItem(menuCommands, CMD_FIRST, '&First\tCtrl+LEFT', self.image_manager.First);
		self.SetMenuItem(menuCommands, CMD_LAST, '&Last\tCtrl+RIGHT', self.image_manager.Last);
		menuCommands.AppendSeparator();
		self.SetMenuItem(menuCommands, CMD_JUMP, '&Jump to page...\tCtrl+J', self.image_manager.JumpToPage)

		zipMenu = wx.Menu()
		self.ZipExtractMode_00 = zipMenu.Append(CMD_ZIP_EXTRACT, '&Extract to temp', kind=wx.ITEM_RADIO) #self.image_manager.SetZipMode(0)
		self.ZipExtractMode_01 = zipMenu.Append(CMD_ZIP_READ, '&Read directly from ZIP', kind=wx.ITEM_RADIO)
		self.ZipExtractMode_02 = zipMenu.Append(CMD_ZIP_RAM, '&Load into RAM', kind=wx.ITEM_RADIO)
		menuSettings.AppendMenu(CMD_ZIP, "ZIP Files", zipMenu)
		#TODO: setting for zip mode, load on start, save on exit

		rarMenu = wx.Menu()
		self.RarExtractMode_00 = rarMenu.Append(CMD_RAR_EXTRACT, '&Extract to temp', kind=wx.ITEM_RADIO) #self.image_manager.SetZipMode(0)
		self.RarExtractMode_01 = rarMenu.Append(CMD_RAR_READ, '&Read directly from RAR', kind=wx.ITEM_RADIO)
		self.RarExtractMode_02 = rarMenu.Append(CMD_RAR_RAM, '&Load into RAM', kind=wx.ITEM_RADIO)
		menuSettings.AppendMenu(CMD_RAR, "RAR Files", rarMenu)

		self.SetMenuItem(menuHelp, HELP_ABOUT, '&About', self.About);
		self.SetMenuItem(menuHelp, HELP_HOTKEYS, '&Hotkeys', self.Hotkeys);

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

	def ChangeZoom(self, evt):
	    if self.Zoom_50.IsChecked():
	    	self.image_manager.SCALE = 0.5
	    elif self.Zoom_66.IsChecked():
	    	self.image_manager.SCALE = 0.67
	    else:
	    	self.image_manager.SCALE = 1
	    self.image_manager.DisplayImageAtIndex()

	def OpenArchive(self, e):
		openFileDialog = wx.FileDialog(self, "Open Archive file", "", "", "Archives (zip, cbz, rar, cbr)|*.zip;*.cbz;*.rar;*.cbr", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		name = openFileDialog.GetPath()
		tmpDir = tempfile.gettempdir()+"/jpyreader/"+name.rsplit('/',1)[1]+"/"
		if not os.path.exists(tmpDir):
			os.makedirs(tmpDir)
		print tmpDir

		self.CloseArchives()
		if os.path.splitext(name)[1].lower() in [".rar", ".cbr"]:
			self.ExtractRarFile(name, tmpDir)
		else:
			self.ExtractZipFile(name, tmpDir)

	def OpenFolder(self, e):
		openFileDialog = wx.DirDialog(self, "Select folder containing images to view")
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		self.LoadFolder(openFileDialog.GetPath())

	def LoadFolder(self, folder):
		for root, dirs, files in os.walk(folder):
			files.sort()
			for name in files:
				print "File:", folder + "/" + name
				ext = os.path.splitext(name)[1].lower()
				if ext in self.SUPPORTED_FORMATS:
					print "Ext:", ext
					if (self.DisplayImage(folder + "/" + name)):
						print "Displaying image:", name
					return

	def ExtractRarFile(self, filePath, tmpDir):
		#needs_password()
		if self.RarExtractMode_00.IsChecked() or self.RarExtractMode_02.IsChecked():
			rf = rarfile.RarFile(filePath)
			for f in rf.infolist():
				name = f.filename
				ext = os.path.splitext(name)[1].lower()
				if ext in self.SUPPORTED_FORMATS:
					try:
						if self.RarExtractMode_00.IsChecked():
							rf.extract(name, tmpDir)
						else:
							stream = cStringIO.StringIO(rf.read(name))
							tmpFile = wx.ImageFromStream(stream)
							self.rar[1].append(tmpFile)
						name = name.replace("\\", "/")
						self.rar[2].append(name)
					except rarfile.RarCRCError, rc:
						print "Archive is password-protected or corrupt"
					except rarfile.RarExecError, re:
						raise
						print "unrar does not appear to be installed"
					except Exception, e:
						raise
					else:
						pass
					finally:
						pass
			rf.close()
			if len(self.rar[2]) == 0:
				print "No applicable files found"
			else:
				print "Displaying image "+tmpDir+self.rar[2][0]
				if self.RarExtractMode_00.IsChecked():
					self.image_manager.DisplayImage(tmpDir+self.rar[2][0])
				else:
					self.rar[0] = 2
					self.image_manager.InitRAMImage()
		elif self.RarExtractMode_01.IsChecked(): #Read directly
			rf = rarfile.RarFile(filePath)
			self.rar[0] = 1
			self.rar[1] = filePath
			for f in rf.infolist():
				name = f.filename
				ext = os.path.splitext(name)[1].lower()
				if ext in self.SUPPORTED_FORMATS:
					self.rar[2].append(name)
			self.image_manager.InitHeldImage()
		else:
			print "Rar extraction mode not set"

	def ExtractZipFile(self, filePath, tmpDir):
		if self.ZipExtractMode_00.IsChecked() or self.ZipExtractMode_02.IsChecked():
			zfile = zipfile.ZipFile(filePath, "r")
			for name in zfile.namelist():
				ext = os.path.splitext(name)[1].lower()
				if ext in self.SUPPORTED_FORMATS:
					try:
						self.zip[2].append(name)
						if self.ZipExtractMode_02.IsChecked():
							stream = cStringIO.StringIO(zfile.read(name))
							tmpFile = wx.ImageFromStream(stream)
							self.zip[1].append(tmpFile)
						else:
							zfile.extract(name, tmpDir)
					except Exception, e:
						raise
					else:
						pass
					finally:
						pass
			zfile.close()

			if len(self.zip[2]) == 0:
				print "No applicable files found"
			else:
				if self.ZipExtractMode_00.IsChecked():
					self.image_manager.DisplayImage(tmpDir+self.zip[2][0])
				else:
					self.zip[0] = 2
					self.image_manager.InitRAMImage()
		elif self.ZipExtractMode_01.IsChecked():
			rf = zipfile.ZipFile(filePath)
			self.zip[0] = 1
			self.zip[1] = filePath
			for name in rf.namelist():
				ext = os.path.splitext(name)[1].lower()
				if ext in self.SUPPORTED_FORMATS:
					self.zip[2].append(name)
			self.image_manager.InitHeldImage()
		else:
			print "Zip extraction mode not set"

	def CloseArchives(self):
		for tp in (self.zip, self.rar):
			if tp[0] == 1:
				try:
					tp[1].close()
				except AttributeError, ae:
					pass
				except Exception, e:
					raise
				else:
					pass
				finally:
					pass
			tp[0] = 0
			tp[1] = []
			tp[2] = []

	def Exit(self, e):
		self.CloseArchives()
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
		info.SetDescription("A lightweight image viewer aimed at manga/comics.")
		info.SetCopyright("(C) 2013 Koroshiya")
		info.SetWebSite("https://github.com/koroshiya/JPyReader")

		f = open ("./LICENSE.txt","r")
		data = f.read()
		data = """An easy to understand explanation of the MIT license can be found here:
https://tldrlegal.com/license/mit-license

		""" + data
		f.close()
		info.SetLicense(data)
		#info.SetModal(True)
		wx.AboutBox(info)

	def Hotkeys(self, e):
		hotkeys = """
		File
Ctrl + O            Open Folder
Ctrl + Z            Open Archive
Ctrl + Q            Exit

		Commands
Right Arrow         Next Image
Left Arrow          Previous Image
Ctrl + Right        Last Image
Ctrl + Left         First Image
Ctrl + J            Jump to Image

		View
Ctrl + Shift + H    Hide Menu
Ctrl + M            Maximize
Ctrl + F            Fullscreen
Ctrl + Scroll       Zoom in/out
		"""
		wx.MessageBox(hotkeys, 'Hotkeys', wx.OK | wx.ICON_INFORMATION)

	def DisplayImage(self, name):
		self.image_manager.DisplayImage(name)

	def CheckArg(self, name):
		name = realpath(name)
		ext = os.path.splitext(name)[1].lower()
		if ext in self.SUPPORTED_FORMATS:
			self.CloseArchives()
			if (self.DisplayImage(name)):
				return False
		elif os.path.isdir(name):
			self.CloseArchives()
			self.LoadFolder(name)
			return False
		elif ext in self.SUPPORTED_ARCHIVE_FORMATS:
			self.CloseArchives()
			tmpDir = tempfile.gettempdir()+"/jpyreader/"+name.rsplit('/',1)[1]+"/"
			if ext in [".rar", ".cbr"]:
				self.ExtractRarFile(name, tmpDir)
			else:
				self.ExtractZipFile(name, tmpDir)
			return False
		else:
			return True
class FileDrop(wx.FileDropTarget):
	def __init__(self, window):
		wx.FileDropTarget.__init__(self)
		self.window = window

	def SetFrame(self, frame):
		self.frame = frame;

	def OnDropFiles(self, x, y, filenames):

		for name in filenames:
			if not self.frame.CheckArg(name):
				break
