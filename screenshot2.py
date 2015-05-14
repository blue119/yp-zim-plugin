# -*- coding: utf-8 -*-

# Copyright 2009-2014 Jaap Karssenberg <jaap.karssenberg@gmail.com>
# Copyright 2014 Andri Kusumah


import time
from platform import os

import gtk

from zim.plugins import PluginClass, WindowExtension, extends
from zim.actions import action
from zim.fs import TmpFile
from zim.applications import Application
from zim.gui.widgets import ui_environment, Dialog, ErrorDialog

ui_actions = (
	# name, stock id, label, accelerator, tooltip, read only
	('insert_screenshot2', None, _('_Screenshot2...'), 'F8', '', False),
		# T: menu item for insert screenshot plugin
)

PLATFORM = os.name
if ui_environment['platform'] == 'maemo':  # don't know what os.name return on maemo
	PLATFORM = 'maemo'

"""
TESTED:
	- import (imagemagick)
	- scrot
UNTESTED:
	- boxcutter (windows, http://keepnote.org/boxcutter/)
	- screenshot-tool (maemo)
"""
COMMAND = 'import'
SUPPORTED_COMMANDS_BY_PLATFORM = dict([
	('posix', ('import', 'scrot')),
	('nt', ('boxcutter',)),
	('maemo', ('screenshot-tool',)),
])
SUPPORTED_COMMANDS = SUPPORTED_COMMANDS_BY_PLATFORM[PLATFORM]
if len(SUPPORTED_COMMANDS):
	COMMAND = SUPPORTED_COMMANDS[0]  # set first available tool as default

class InsertScreenshot2Plugin(PluginClass):
	plugin_info = {
		'name': _('Insert Screenshot2'),  # T: plugin name
		'description': _('''\
This plugin  allows taking a screenshot and directly insert it
in a zim page.

This is a core plugin shipping with zim.
'''),  # T: plugin description
		'author': 'Jaap Karssenberg',
		'help': 'Plugins:Insert Screenshot',
	}
	plugin_preferences = (
		# key, type, label, default
		('screenshot_command', 'choice', _('Screenshot Command'), COMMAND, SUPPORTED_COMMANDS), # T: plugin preference
	)
	screenshot_cmd = COMMAND

	def __init__(self, config=None):
		PluginClass.__init__(self, config)
		self.on_preferences_changed(self.preferences)
		self.preferences.connect('changed', self.on_preferences_changed)

	def on_preferences_changed(self, preferences):
		self.screenshot_cmd = preferences['screenshot_command']

	@classmethod
	def check_dependencies(cls):
		cmds = []
		is_ok = False
		if len(SUPPORTED_COMMANDS):
			for cmd in SUPPORTED_COMMANDS:
				has_tool = Application(cmd).tryexec()
				if has_tool:
					is_ok = True
					cmds.append((cmd, True, False))
				else:
					cmds.append((cmd, False, False))
		return is_ok, cmds

@extends('MainWindow')
class MainWindowExtension(WindowExtension):
	uimanager_xml = '''
	<ui>
		<menubar name='menubar'>
			<menu action='insert_menu'>
				<placeholder name='plugin_items'>
					<menuitem action='insert_screenshot2'/>
				</placeholder>
			</menu>
		</menubar>
	</ui>
	'''
	screenshot_command = COMMAND
	plugin = None

	def __init__(self, plugin, window):
		WindowExtension.__init__(self, plugin, window)
		self.on_preferences_changed(plugin.preferences)
		self.connectto(plugin.preferences, 'changed', self.on_preferences_changed)
		self.plugin = plugin
		self.ui = window.ui
		self.ui.add_actions(ui_actions, self)

	def on_preferences_changed(self, preferences):
		if preferences['screenshot_command']:
			self.screenshot_command = preferences['screenshot_command']

    #  @action(_('_Screenshot2...'))  # T: menu item for insert screenshot plugin
	def insert_screenshot2(self):
		self.notebook = self.window.ui.notebook  # XXX
		self.page = self.window.ui.page  # XXX
		self.ui = self.window.ui  # XXX
		tmpfile = TmpFile('insert-screenshot.png')
		delay = 0
		selection_mode = True

		helper = Application((self.screenshot_command,))

		def callback(status, tmpfile):
			name = time.strftime('screenshot_%Y-%m-%d-%H%M%S.png')
			imgdir = self.notebook.get_attachments_dir(self.page)
			imgfile = imgdir.new_file(name)
			tmpfile.rename(imgfile)
			pageview = self.ui.mainwindow.pageview
			pageview.insert_image(imgfile, interactive=False, force=True)

		tmpfile.dir.touch()
		helper.spawn((tmpfile,), callback, tmpfile)

