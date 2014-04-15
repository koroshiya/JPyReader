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

from os.path import dirname
from os.path import realpath
import glob

SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
INDEXED_FILES = []

class ImageManager():

	def __init__(self):
		self.CUR_INDEX = 0
		self.TOTAL_LEN = 0
		self.SCALE = 1
		self.CACHE = [["",""],["",""],["",""]]

	def SetFrame(self, frame):
		self.frame = frame;

	def Max(self, e):
		if (self.frame.IsMaximized()):
			self.frame.Maximize(False);
			self.frame.panel.SetPosition((0,0))
			#hug image
			try:
				x, y = wx.Image(INDEXED_FILES[self.CUR_INDEX], wx.BITMAP_TYPE_ANY).GetSize()
				self.frame.SetSize(x,y)
			except Exception, e:
				pass
			else:
				pass
			finally:
				pass
		else:
			self.frame.Maximize(True);
			self.CenterImage();

		print self.frame.panel.GetPosition();

	def Min(self, e):
		self.frame.Iconize(not self.IsIconized())

	def Full(self, e):
		if (self.frame.IsFullScreen()):
			self.frame.ShowFullScreen(False);
			if (not self.frame.IsMaximized()):
				self.frame.panel.SetPosition((0,0))
		else:
			self.frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL);
			self.CenterImage();

	def CenterImage(self):
		x, y = self.frame.panel.GetSize()
		x2, y2 = self.frame.sizes[self.frame.GetMonitor()]

		width = 0 if (x > x2) else (x2 / 2 - x / 2)
		height = 0 if (y > y2) else (y2 / 2 - y / 2)
		self.frame.panel.SetPosition((width, height))

	def Next(self, e):
		self.SwitchImage(True);

	def Previous(self, e):
		self.SwitchImage(False);

	def First(self, e):
		self.MoveToImage(0);

	def Last(self, e):
		self.MoveToImage(self.TOTAL_LEN);

	def MoveToImage(self, target):
		if (self.TOTAL_LEN > 0):
			self.CUR_INDEX = target;
			self.CACHE = [["",""],["",""],["",""]]
			self.DisplayImageAtIndex();

	def JumpToPage(self, e):
		if self.TOTAL_LEN >= 0:
			td = wx.TextEntryDialog(self,"Enter number of page to skip to")
			td.ShowModal();
			val = td.GetValue()
			if (len(val) > 0 and val.isdigit()):
				val = int(val) - 1
				if val >= 0 and val <= self.TOTAL_LEN:
					self.CUR_INDEX = val
					self.DisplayImageAtIndex();

	def SwitchImage(self, boolForward):
		total = self.TOTAL_LEN;

		if self.IsArchiveInUse():
			indexOne, indexTwo, inc = (total, 0, 1) if boolForward else (0, total, -1)
			self.CUR_INDEX = indexTwo if self.CUR_INDEX == indexOne else self.CUR_INDEX + inc
			self.DisplayRAMImage(self.CUR_INDEX)
		else:
			indexOne, indexTwo, inc, cachePrimary, cacheSecondary = (total, 0, 1, 2, 0) if boolForward else (0, total, -1, 0, 2)
			self.CACHE[cacheSecondary] = self.CACHE[1];

			if (self.CACHE[cachePrimary] != ""):
				self.CACHE[1] = self.CACHE[cachePrimary];
				self.CACHE[cachePrimary] = "";
			self.CUR_INDEX = indexTwo if self.CUR_INDEX == indexOne else self.CUR_INDEX + inc
			if (self.CACHE[1] != ""):
				self.DisplayImageAtIndex();
			else:
				self.DisplayCachedImage(1);

	def IsSupportedImage(self, image):
		for format in SUPPORTED_FORMATS:
			if image[-len(format):] == format:
				return True
		return False

	def IndexFilesInDirectory(self, curdir):
		INDEXED_FILES[:] = []
		print "Indexing files in "+curdir
		for format in SUPPORTED_FORMATS:
			INDEXED_FILES.extend(glob.glob(curdir + "/*" + format));
		INDEXED_FILES.sort();

	def DisplayRAMImage(self, findex=0):
		if self.frame.rar[0] == 2:
			target = self.frame.rar
		else:
			target = self.frame.zip

		self.frame.Freeze()
		
		tmpFile = target[1][findex]
		x, y = tmpFile.GetSize()
		jpg1 = tmpFile.Scale(x * self.SCALE, y * self.SCALE).ConvertToBitmap()
		self.frame.SetTitle("JPy-Reader - Page "+str(self.CUR_INDEX+1)+" of "+str(self.TOTAL_LEN+1)+" - "+target[2][findex])
		self.PaintImage(jpg1)
		
		self.frame.Thaw()

	def InitRAMImage(self):
		self.CUR_INDEX = 0
		self.TOTAL_LEN = len(self.frame.rar[1]) - 1 if self.frame.rar[0] == 2 else len(self.frame.zip[1]) - 1
		print "Total:", self.TOTAL_LEN
		self.DisplayRAMImage(0)

	def IsArchiveInUse(self):
		return self.frame.rar[0] != 0 or self.frame.zip[0] != 0

	def DisplayImage(self, imageFile): 
		if not self.IsSupportedImage(imageFile):
			return False
		self.IndexFilesInDirectory(dirname(realpath(imageFile)))
		self.CUR_INDEX = 0
		for filec in INDEXED_FILES:
			if (filec == imageFile):
				break;
			self.CUR_INDEX += 1
		self.TOTAL_LEN = len(INDEXED_FILES) - 1
		if self.CUR_INDEX > self.TOTAL_LEN:
			self.CUR_INDEX = 0
		return self.DisplayImageAtIndex()

	def DisplayImageAtIndex(self):
		tmpIndex = INDEXED_FILES[self.CUR_INDEX]
		self.frame.Freeze()
		try:
			self.CACHE[1][0] = wx.Image(tmpIndex, wx.BITMAP_TYPE_ANY)
			self.CACHE[1][1] = tmpIndex
			x, y = self.CACHE[1][0].GetSize()
			jpg1 = self.CACHE[1][0].Scale(x * self.SCALE, y * self.SCALE).ConvertToBitmap()
			self.frame.SetTitle("JPy-Reader - "+tmpIndex)
			self.PaintImage(jpg1)

			self.frame.Thaw()
			return True
		except IOError:
			print "Image file %s not found" % tmpIndex
			self.frame.Thaw()
			return False

	def DisplayCachedImage(self, index):
		if (self.TOTAL_LEN > -1):
			tmpIndex = INDEXED_FILES[self.CUR_INDEX]
			self.frame.Freeze()
			try:
				jpg1 = self.CACHE[index][0]
				x, y = jpg1.GetSize()
				jpg1 = jpg1.Scale(x * self.SCALE, y * self.SCALE).ConvertToBitmap()
				self.frame.SetTitle("JPy-Reader - "+tmpIndex)
				self.PaintImage(jpg1)

				self.frame.Thaw()
				return True
			except IOError:
				print "Image file %s not found" % tmpIndex
				self.frame.Thaw()
				return False

	def PaintImage(self, jpg1):
		self.frame.statusbar.SetStatusText(str(self.CUR_INDEX + 1) + "/" + str(self.TOTAL_LEN + 1) + " - " + self.CACHE[1][1])
		self.frame.spanel.FitInside();
		self.frame.spanel.SetScrollbars(1,1,1,1)
		self.frame.spanel.SetScrollRate(20,20)
		
		self.frame.spanel.SetClientSize(jpg1.GetSize())
		self.frame.spanel.SetVirtualSize((1920, 1080))
		self.frame.spanel.SetVirtualSize(jpg1.GetSize())
		self.frame.panel.SetBitmap(jpg1);
		self.frame.panel.SetClientSize(jpg1.GetSize());
		self.frame.SetClientSize(jpg1.GetSize())
		if (self.frame.IsFullScreen() or self.frame.IsMaximized()):
			self.CenterImage()

		self.frame.spanel.FitInside();