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
			#Section_View = ConfigSectionMap('View');

	def write(self, frame):

		if not self.Config.has_section('Size'):
			self.Config.add_section('Size')
		if not self.Config.has_section('Position'):
			self.Config.add_section('Position')

		cfgfile = open(tmpFile,'w');
		fSize = frame.GetSizeTuple()
		fPos = frame.GetPositionTuple()

		self.Config.set('Size', 'InitWidth', fSize[0])
		self.Config.set('Size', 'InitHeight', fSize[1])
		self.Config.set('Size', 'MinWidth', self.size_min[0])
		self.Config.set('Size', 'MinHeight', self.size_min[1])

		self.Config.set('Position', 'X', fPos[0])
		self.Config.set('Position', 'Y', fPos[1])

		#self.Config.add_section('View')
		#self.Config.set('View', 'KeepZoom', True)
		#self.Config.set('View', 'CurrentZoom', 100)
		self.Config.write(cfgfile)
		cfgfile.close()

	def defaults(self):
		self.size_min = (300, 300);
		self.size_init = (500, 400);
		self.screen_pos = (0, 0);