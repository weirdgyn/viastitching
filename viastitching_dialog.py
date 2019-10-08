#!/usr/bin/env python

# AddNet for pcbnew 
# This is the plugin WX dialog
# (c) Michele Santucci 2019
#

import wx
import pcbnew
import gettext
import math

from viastitching_gui import viastitching_gui
from math import sqrt

_ = gettext.gettext
__version__ = "0.1"
__timecode__= 1972

class ViaStitchingDialog(viastitching_gui):
    def __init__(self, board):
        super(ViaStitchingDialog, self).__init__(None)
        self.SetTitle(_(u"ViaStitching v{0}").format(__version__))
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
            self.m_lblUnit1.SetLabel(_(u"mils"))
            self.m_lblUnit2.SetLabel(_(u"mils"))
            self.m_txtVSpacing.SetValue("40")
            self.m_txtHSpacing.SetValue("40")
        elif units_mode == 1:
            self.ToUserUnit = pcbnew.ToMM
            self.FromUserUnit = pcbnew.FromMM
            self.m_lblUnit1.SetLabel(_(u"mm"))
            self.m_lblUnit2.SetLabel(_(u"mm"))
            self.m_txtVSpacing.SetValue("1")
            self.m_txtHSpacing.SetValue("1")
        elif units_mode == -1:
            wx.MessageBox(_(u"Not a valid frame"))
            self.Destroy()
        via_dim_list = self.board.GetViasDimensionsList()
        via_dims = via_dim_list.pop()
        self.m_txtViaSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Diameter))
        self.m_txtViaDrillSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Drill))
        via_dim_list.push_back(via_dims)
        self.area = None
        self.net = None
        if not self.GetAreaConfig():
            wx.MessageBox(_(u"Please select a valid area"))
            self.Destroy()
        else:
            #self.CollectOverlappingItems()
            self.PopulateNets() 

    def CollectOverlappingItems(self):
        modules = self.board.GetModules()
        for mod in modules:
            pass

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
        undo = self.m_chkClearOwn.IsChecked()
        drillsize = self.FromUserUnit(float(self.m_txtViaDrillSize.GetValue()))
        viasize = self.FromUserUnit(float(self.m_txtViaSize.GetValue()))
        netname = self.m_cbNet.GetStringSelection()
        netcode = self.board.GetNetcodeFromNetname(netname)
        #commit = pcbnew.COMMIT()
        viacount = 0
        for item in self.board.GetTracks():
            if type(item) is pcbnew.VIA:
                if undo and (item.GetTimeStamp() == __timecode__):
                    self.board.Remove(item)
                    viacount+=1
                    #commit.Remove(item)
                elif not undo and self.area.HitTestInsideZone(item.GetPosition()) and item.GetDrillValue() == drillsize and item.GetWidth() == viasize and item.GetNetname() == netname:
                    self.board.Remove(item)
                    viacount+=1
                    #commit.Remove(item)
        if viacount > 0:
            wx.MessageBox(_(u"Removed: %d vias!") % viacount)
            #commit.Push()
            pcbnew.Refresh()

    def CheckClearance(self, p1, area, clearance):
        corners = area.GetNumCorners()
        #Calculate minimum distance from corners
        for i in range(0, corners):
            corner = area.GetCornerPosition(i)
            p2 = corner.getWxPoint()
            distance = sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
            if distance < clearance:
                return False

        #Calculate minimum distance from edges
        for i in range(0, corners):
            if i == corners-1:
                corner1 = area.GetCornerPosition(corners-1)
                corner2 = area.GetCornerPosition(0)
            else:
                corner1 = area.GetCornerPosition(i)
                corner2 = area.GetCornerPosition(i+1)
            pc1 = corner1.getWxPoint()
            pc2 = corner2.getWxPoint()
            if pc1.x != pc2.x:
                m = (pc1.y - pc2.y)/(pc1.x - pc2.x)
                q = pc1.y - (m*pc1.x)
                distance = math.fabs(p1.y-m*p1.x-q)/math.sqrt(1+m**2)
            else:
                distance = math.fabs(pc1.x - p1.x)
            if distance < clearance:
                return False

        return True     

    def FillupArea(self):
        drillsize = self.FromUserUnit(float(self.m_txtViaDrillSize.GetValue()))
        viasize = self.FromUserUnit(float(self.m_txtViaSize.GetValue()))
        step_x = self.FromUserUnit(float(self.m_txtHSpacing.GetValue()))
        step_y = self.FromUserUnit(float(self.m_txtVSpacing.GetValue()))
        clearance = self.FromUserUnit(float(self.m_txtClearance.GetValue()))
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
                if self.area.HitTestInsideZone(pcbnew.wxPoint(x,y)):
                    via = pcbnew.VIA(self.board)
                    p = pcbnew.wxPoint(x,y)
                    via.SetPosition(p)
                    via.SetLayer(self.area.GetLayer())
                    via.SetNetCode(netcode)
                    via.SetDrill(drillsize)
                    via.SetWidth(viasize)
                    via.SetTimeStamp(__timecode__)
                    if (clearance == 0) or (self.CheckClearance(p, self.area, clearance)):
                        self.board.Add(via)
                        #commit.Add(via)
                        viacount +=1
                y += step_y
            x += step_x
        if viacount > 0:
            wx.MessageBox(_(u"Implanted: %d vias!") % viacount)
            #commit.Push()
            pcbnew.Refresh()
        else:
            wx.MessageBox(_(u"No vias implanted!"))

    def onProcessAction(self, event):
        if(self.m_rFill.GetValue()):
            self.FillupArea()
        else:
            self.ClearArea()
        self.Destroy()

    def onCloseWindow(self, event):
        self.Destroy()

def InitViaStitchingDialog(board):
    dlg = ViaStitchingDialog(board)
    dlg.Show(True)
    return dlg
