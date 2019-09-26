#!/usr/bin/env python

# AddNet for pcbnew
# This is the action plugin interface
# (c) Michele Santucci 2019
#

import wx
import os
import pcbnew

from pcbnew import ActionPlugin, GetBoard
from viastitching_dialog import InitViaStitchingDialog

class ViaStitchingPlugin(ActionPlugin):
    """Class that gathers the actionplugin stuff"""
    def defaults(self):
        self.name = "ViaStitching"
        self.category = "Modify PCB"
        self.description = "Create a vias stitching pattern"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'viastitching.png')

    def Run(self):
        InitViaStitchingDialog(pcbnew.GetBoard())
