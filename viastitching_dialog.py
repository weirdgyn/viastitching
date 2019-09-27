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
        self.ToUserUnit = None
        self.FromUserUnit = None
        units_mode = pcbnew.GetUserUnits()
        if units_mode == 0:
            self.ToUserUnit = pcbnew.ToMils
            self.FromUserUnit = pcbnew.FromMils
            self.m_lblUnit1.SetLabel("mils")
            self.m_lblUnit2.SetLabel("mils")
            self.m_txtVSpacing.SetValue("40")
            self.m_txtHSpacing.SetValue("40")
        elif units_mode == 1:
            self.ToUserUnit = pcbnew.ToMM
            self.FromUserUnit = pcbnew.FromMM
            self.m_lblUnit1.SetLabel("mm")
            self.m_lblUnit2.SetLabel("mm")
            self.m_txtVSpacing.SetValue("1")
            self.m_txtHSpacing.SetValue("1")
        elif units_mode == -1:
            wx.MessageBox("Not a valid frame")
            self.Destroy()
        via_dim_list = self.board.GetViasDimensionsList()
        via_dims = via_dim_list.pop()
        self.m_txtViaSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Diameter))
        self.m_txtViaDrillSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Drill))
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
        nets = self.board.GetNetsByName()
        for netname, net in nets.items():
            netname = net.GetNetname()
            if netname != None and netname != "":
                self.m_cbNet.Append(netname)
        if self.net != None:
            index = self.m_cbNet.FindString(self.net)
            self.m_cbNet.Select(index)                        

    def ClearArea(self):
        drillsize = self.FromUserUnit(float(self.m_txtViaDrillSize.GetValue()))
        viasize = self.FromUserUnit(float(self.m_txtViaSize.GetValue()))
        bbox = self.area.GetBoundingBox()
        netname = self.m_cbNet.GetStringSelection()
        netcode = self.board.GetNetcodeFromNetname(netname)
        #commit = pcbnew.COMMIT()
        viacount = 0
        for item in self.board.GetTracks():
            if type(item) is pcbnew.VIA:
                if self.area.HitTestInsideZone(item.GetPosition()) and item.GetDrillValue() == drillsize and item.GetWidth() == viasize and item.GetNetname() == netname:
                    self.board.Remove(item)
                    #commit.Remove(item)
                    viacount+=1
        if viacount > 0:
            wx.MessageBox("Removed: %d vias!" % viacount)
            #commit.Push()
            pcbnew.Refresh()

    def FillupArea(self):
        drillsize = self.FromUserUnit(float(self.m_txtViaDrillSize.GetValue()))
        viasize = self.FromUserUnit(float(self.m_txtViaSize.GetValue()))
        step_x = self.FromUserUnit(float(self.m_txtHSpacing.GetValue()))
        step_y = self.FromUserUnit(float(self.m_txtVSpacing.GetValue()))
        bbox = self.area.GetBoundingBox()
        top = bbox.GetTop()
        bottom = bbox.GetBottom()
        right = bbox.GetRight()
        left = bbox.GetLeft()
        netname = self.m_cbNet.GetStringSelection()
        netcode = self.board.GetNetcodeFromNetname(netname)
        #commit = pcbnew.COMMIT()
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
                    via.SetDrill(drillsize)
                    via.SetWidth(viasize)
                    self.board.Add(via)
                    #commit.Add(via)
                    viacount +=1
                y += step_y
            x += step_x
        if viacount > 0:
            wx.MessageBox("Implanted: %d vias!" % viacount)
            #commit.Push()
            pcbnew.Refresh()

    def onProcessAction(self, event):
        if(self.m_rFill.GetValue()):
            self.FillupArea()
        else:
            self.ClearArea()
        self.Destroy()

    def onCloseWindow(self, event):
        self.Destroy()

def InitViaStitchingDialog(board):
    """Launch the dialog"""
    dlg = ViaStitchingDialog(board)
    dlg.Show(True)
    return dlg
