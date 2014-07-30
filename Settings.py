#!/usr/bin/python2.7 -tt

from __future__ import unicode_literals
import ConfigParser
from os.path import expanduser
from os.path import isfile

tmpFile = expanduser("~") + "/.jpygui.ini";

class Settings():

	size_init = (500, 400);
	size_min = (300, 300);
	screen_pos = (0,0)
	rarMode = 0
	zipMode = 0
	maximized = False
	fullscreen = False

	def __init__(self):
		self.Config = ConfigParser.ConfigParser()
		if isfile(tmpFile):
			cfgfile = open(tmpFile);
			self.Config.readfp(cfgfile);

			self.defaults(); #TODO: multiple try blocks, implement error count, if > 0, call defaults()
			#TODO: make defaults() check if fields are defined before overwriting
			
			try:
				self.size_min = (self.Config.getint('Size', 'minwidth'), self.Config.getint('Size', 'minheight'));
				self.size_init = (self.Config.getint('Size', 'initwidth'), self.Config.getint('Size', 'initheight'));
			except:
				self.defaults();
				pass
			try:
				self.screen_pos = (self.Config.getint('Position', 'X'), self.Config.getint('Position', 'Y'));
			except:
				pass
			try:
				self.rarMode = self.Config.getint('ArchiveModeIndex', 'rar')
				self.zipMode = self.Config.getint('ArchiveModeIndex', 'zip')
			except:
				pass
			try:
				self.maximized = self.Config.getboolean('View', 'maximized')
				self.fullscreen = self.Config.getboolean('View', 'fullscreen')
			except Exception, e:
				pass
			#Section_View = ConfigSectionMap('View');

	def write(self, frame):
		sections = ["Size", "Position", "ArchiveModeIndex", "View"]
		for s in sections:
			if not self.Config.has_section(s):
				self.Config.add_section(s)

		cfgfile = open(tmpFile,'w')
		fSize = frame.GetSizeTuple()
		fPos = frame.GetPositionTuple()

		self.Config.set('Size', 'initwidth', fSize[0])
		self.Config.set('Size', 'initheight', fSize[1])
		self.Config.set('Size', 'minwidth', self.size_min[0])
		self.Config.set('Size', 'minheight', self.size_min[1])

		self.Config.set('Position', 'X', fPos[0])
		self.Config.set('Position', 'Y', fPos[1])

		if frame.ZipExtractMode_01.IsChecked():
			zipm = 1
		elif frame.ZipExtractMode_02.IsChecked():
			zipm = 2
		else:
			zipm = 0

		if frame.RarExtractMode_01.IsChecked():
			rarm = 1
		elif frame.RarExtractMode_02.IsChecked():
			rarm = 2
		else:
			rarm = 0

		self.Config.set('ArchiveModeIndex', 'ZIP', zipm)
		self.Config.set('ArchiveModeIndex', 'RAR', rarm)

		#self.Config.add_section('View')
		self.Config.set('View', 'Maximized', frame.IsMaximized())
		self.Config.set('View', 'Fullscreen', frame.IsFullScreen())
		#self.Config.set('View', 'KeepZoom', True)
		#self.Config.set('View', 'CurrentZoom', 100)
		self.Config.write(cfgfile)
		cfgfile.close()

	def defaults(self):
		self.size_min = (300, 300);
		self.size_init = (500, 400);
		self.screen_pos = (0, 0);