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
import os
from rarfile import rarfile
import zipfile
import cStringIO
import glob

INDEXED_FILES = []

class ImageManager():

	def __init__(self):
		self.CUR_INDEX = 0
		self.TOTAL_LEN = 0
		self.SCALE = 1
		self.CACHE = [["",""],["",""],["",""]]
		self.isMaximized = False

	def SetFrame(self, frame):
		self.frame = frame;
		
	def Resize(self, e):
		if self.isMaximized and not self.frame.IsMaximized():
			self.isMaximized = False
			self.frame.panel.SetPosition((0,0))
			#hug image
			try:
				x, y = wx.Image(INDEXED_FILES[self.CUR_INDEX], wx.BITMAP_TYPE_ANY).GetSize()
				self.frame.SetSize(x,y)
			except Exception, ex:
				pass
			else:
				pass
			finally:
				pass
		elif self.frame.IsMaximized():
			self.isMaximized = True
			self.CenterImage()
		else:
			self.isMaximized = False
		e.Skip()

	def Max(self, e):
		if (self.frame.IsMaximized()):
			self.isMaximized = False
			self.frame.Maximize(False)
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
			self.isMaximized = True
			self.frame.Maximize(True)
			self.CenterImage()

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
		print "width", width
		print "height", height
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

		if self.IsArchiveInUse() or self.IsArchiveHeld():
			indexOne, indexTwo, inc = (total, 0, 1) if boolForward else (0, total, -1)
			self.CUR_INDEX = indexTwo if self.CUR_INDEX == indexOne else self.CUR_INDEX + inc
			if self.IsArchiveHeld():
				self.DisplayHeldImage(self.CUR_INDEX)
			else:
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
		for format in self.frame.SUPPORTED_FORMATS:
			if image[-len(format):].lower() == format:
				return True
		return False

	def IndexFilesInDirectory(self, curdir):
		INDEXED_FILES[:] = []
		print "Indexing files in "+curdir
		for root, dirs, files in os.walk(curdir):
			for name in files:
				ext = os.path.splitext(name)[1].lower()
				if ext.lower() in self.frame.SUPPORTED_FORMATS:
					if os.path.isfile(curdir+"/"+name):
						INDEXED_FILES.append(curdir+"/"+name)
		INDEXED_FILES.sort();

	def DisplayHeldImage(self, findex=0):
		if self.frame.rar[0] == 1:
			target = self.frame.rar
			name = target[2][findex]
			stream = cStringIO.StringIO(rarfile.RarFile(self.frame.rar[1]).read(name))
		else:
			target = self.frame.zip
			name = target[2][findex]
			stream = cStringIO.StringIO(zipfile.ZipFile(self.frame.zip[1], 'r').read(name))

		#stream = cStringIO.StringIO(target.read(name))
		tmpFile = wx.ImageFromStream(stream)

		self.frame.Freeze()
		
		x, y = tmpFile.GetSize()
		jpg1 = tmpFile.Scale(x * self.SCALE, y * self.SCALE).ConvertToBitmap()
		self.frame.SetTitle("JPy-Reader - Page "+str(self.CUR_INDEX+1)+" of "+str(self.TOTAL_LEN+1)+" - "+target[2][findex])
		self.PaintImage(jpg1)

		self.frame.Thaw()

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
		self.InitIndex(2)
		self.DisplayRAMImage(0)

	def InitHeldImage(self):
		self.InitIndex(1)
		self.DisplayHeldImage(0)

	def InitIndex(self, index):
		self.CUR_INDEX = 0
		self.TOTAL_LEN = len(self.frame.rar[2]) - 1 if self.frame.rar[0] == index else len(self.frame.zip[2]) - 1
		print "Total:", self.TOTAL_LEN

	def IsArchiveInUse(self):
		return self.frame.rar[0] == 2 or self.frame.zip[0] == 2

	def IsArchiveHeld(self):
		return self.frame.rar[0] == 1 or self.frame.zip[0] == 1

	def DisplayImage(self, imageFile):
		if not self.IsSupportedImage(imageFile):
			return False
		self.IndexFilesInDirectory(dirname(realpath(imageFile)))
		print dirname(realpath(imageFile))
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
		#print INDEXED_FILES
		tmpIndex = INDEXED_FILES[self.CUR_INDEX]
		print tmpIndex
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
		xy = self.frame.sizes[self.frame.GetMonitor()]
		self.frame.SetMaxSize(xy)
		self.frame.statusbar.SetStatusText(str(self.CUR_INDEX + 1) + "/" + str(self.TOTAL_LEN + 1) + " - " + self.CACHE[1][1])
		self.frame.spanel.FitInside();
		self.frame.spanel.SetScrollbars(1,1,1,1)
		self.frame.spanel.SetScrollRate(20,20)
		
		xy2 = jpg1.GetSize()
		if xy2[0] > xy[0] or xy2[1] > xy[1]:
			self.frame.spanel.SetClientSize((0,0))
		self.frame.spanel.SetClientSize(xy2)
		self.frame.spanel.SetVirtualSize((1920, 1080))
		if xy2[0] > xy[0] or xy2[1] > xy[1]:
			self.frame.spanel.SetVirtualSize((0, 0))
		self.frame.spanel.SetVirtualSize(xy2)
		if xy2[0] > xy[0] or xy2[1] > xy[1]:
			self.frame.spanel.SetVirtualSize((0,0))
		self.frame.panel.SetBitmap(jpg1);
		if xy2[0] > xy[0] or xy2[1] > xy[1]:
			self.frame.panel.SetClientSize((0,0));
		self.frame.panel.SetClientSize(xy2);
		if xy2[0] > xy[0] or xy2[1] > xy[1]:
			self.frame.SetClientSize((0,0))
		self.frame.SetClientSize(xy2)
		if (self.frame.IsFullScreen() or self.frame.IsMaximized()):
			self.CenterImage()

		self.frame.spanel.FitInside();
