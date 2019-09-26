#!/usr/bin/env python

# AddNet for pcbnew 
# This is the plugin WX dialog
# (c) Michele Santucci 2019
#

import wx
import pcbnew

from viastitching_gui import viastitching_gui

__version__ = "0.1"

class ViaStitchingDialog(viastitching_gui):
    """Class that gathers all the Gui control"""

    def __init__(self, board):
        #TODO: set unit conversion based on user preferences
        """Init the brand new instance"""
        super(ViaStitchingDialog, self).__init__(None)
        self.SetTitle("ViaStitching v{0}".format(__version__))
        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
        self.m_btnCancel.Bind(wx.EVT_BUTTON, self.onCloseWindow)
        self.m_btnOk.Bind(wx.EVT_BUTTON, self.onProcessAction)
        self.board = pcbnew.GetBoard()
        via_dim_list = self.board.GetViasDimensionsList()
        via_dims = via_dim_list.pop()
        self.m_txtViaSize.SetValue("%.3f" % pcbnew.ToMM(via_dims.m_Diameter))
        self.m_txtViaDrillSize.SetValue("%.3f" % pcbnew.ToMM(via_dims.m_Drill))
        via_dim_list.push_back(via_dims)
        self.area = None
        self.net = None
        if not self.GetAreaConfig():
            wx.MessageBox("Please select a valid area")
            self.Destroy()
        else:
            self.PopulateNets()


    def GetAreaConfig(self):
        for i in range(0, self.board.GetAreaCount()):
            area = self.board.GetArea(i)
            if area.IsSelected():
                if not area.IsOnCopperLayer():
                    return False
                elif area.GetDoNotAllowCopperPour():
                    return False
                self.area = area
                self.net = area.GetNetname()
                return True
        return False


    def PopulateNets(self):
        modules = self.board.GetModules()
        self.m_cbNet.Clear()
        for mod in modules:
            pads = mod.Pads()
            for pad in pads:
                netname = pad.GetNetname()
                if netname != None and netname != "":
                    if self.m_cbNet.FindString(netname) == wx.NOT_FOUND:
                        self.m_cbNet.Append(netname)
        if self.net != None:
            index = self.m_cbNet.FindString(self.net)
            self.m_cbNet.Select(index)

    def FillupArea(self):
        drillsize = pcbnew.FromMM(float(self.m_txtViaDrillSize.GetValue()))
        viasize = pcbnew.FromMM(float(self.m_txtViaSize.GetValue()))
        bbox = self.area.GetBoundingBox()
        top = bbox.GetTop()
        bottom = bbox.GetBottom()
        right = bbox.GetRight()
        left = bbox.GetLeft()
        step_x = pcbnew.FromMM(float(self.m_txtHSpacing.GetValue()))
        step_y = pcbnew.FromMM(float(self.m_txtVSpacing.GetValue()))
        netname = self.m_cbNet.GetStringSelection()
        netcode = self.board.GetNetcodeFromNetname(netname)
        viacount = 0
        x = left
        while x <= right:
            y = top
            while y <= bottom:
                if(self.area.HitTestInsideZone(pcbnew.wxPoint(x,y))):
                    via = pcbnew.VIA(self.board)
                    via.SetPosition(pcbnew.wxPoint(x,y))
                    via.SetLayer(self.area.GetLayer())
                    via.SetNetCode(netcode)
                    self.board.Add(via)
                    viacount +=1
                y += step_y
            x += step_x
        if viacount > 0:
            wx.MessageBox("Implanted: %d vias!" % viacount)
            pcbnew.Refresh()

    def onProcessAction(self, event):
        self.FillupArea()
        self.Destroy()

    def onCloseWindow(self, event):
        self.Destroy()

def InitViaStitchingDialog(board):
    """Launch the dialog"""
    dlg = ViaStitchingDialog(board)
    dlg.Show(True)
    return dlg
