#!/usr/bin/env python

# ViaStitching for pcbnew 
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
    '''Class that gathers all the Gui controls.'''

    def __init__(self, board):
        '''Initialize the brand new instance.'''

        super(ViaStitchingDialog, self).__init__(None)
        self.SetTitle(_(u"ViaStitching v{0}").format(__version__))
        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
        self.m_btnCancel.Bind(wx.EVT_BUTTON, self.onCloseWindow)
        self.m_btnOk.Bind(wx.EVT_BUTTON, self.onProcessAction)
        self.m_rClear.Bind(wx.EVT_RADIOBUTTON, self.onRadioButtonCheck)
        self.m_rFill.Bind(wx.EVT_RADIOBUTTON, self.onRadioButtonCheck)
        self.board = pcbnew.GetBoard()
        #Use the same unit set int PCBNEW
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

        #Get default Vias dimensions
        via_dim_list = self.board.GetViasDimensionsList()
        via_dims = via_dim_list.pop()
        self.m_txtViaSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Diameter))
        self.m_txtViaDrillSize.SetValue("%.6f" % self.ToUserUnit(via_dims.m_Drill))
        via_dim_list.push_back(via_dims)
        self.area = None
        self.net = None
        self.overlappings = None

        #Check for selected area
        if not self.GetAreaConfig():
            wx.MessageBox(_(u"Please select a valid area"))
            self.Destroy()
        else:
            #Get overlapping items
            self.GetOverlappingItems()
            #Populate nets checkbox
            self.PopulateNets() 


    def GetOverlappingItems(self):
        """Collect overlapping items.
            Every item found inside are bounding box is a candidate to be inspected for overlapping.
        """

        area_bbox = self.area.GetBoundingBox()
        modules = self.board.GetModules()
        tracks = self.board.GetTracks()

        self.overlappings = []

        for item in tracks:
            if (type(item) is pcbnew.VIA) and (item.GetBoundingBox().Intersects(area_bbox)):
                self.overlappings.append(item)

        for item in modules:
            if item.GetBoundingBox().Intersects(area_bbox):
                for pad in item.Pads():
                    self.overlappings.append(pad)

        #TODO: change algorithm to 'If one of the candidate area's edges overlaps with target area declare candidate as overlapping' 
        for i in range(0, self.board.GetAreaCount()):
            item = self.board.GetArea(i)
            if item.GetBoundingBox().Intersects(area_bbox):
                if item.GetNetname() != self.net:
                    self.overlappings.append(item)


    def GetAreaConfig(self):
        """Check selected area (if any) and verify if it is a valid container for vias.

        Returns:
            bool: Returns True if an area/zone is selected and match implant criteria, False otherwise.  
        """

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
        '''Populate nets widget.'''

        nets = self.board.GetNetsByName()

        #Tricky loop, the iterator should return two values, unluckly I'm not able to use the
        #first value of the couple so I'm recycling it as netname.
        for netname, net in nets.items():
            netname = net.GetNetname()
            if (netname != None) and (netname != ""):
                self.m_cbNet.Append(netname)

        #Select the net used by area (if any)
        if self.net != None:
            index = self.m_cbNet.FindString(self.net)
            self.m_cbNet.Select(index)                        


    def ClearArea(self):
        '''Clear selected area.'''

        undo = self.m_chkClearOwn.IsChecked()
        drillsize = self.FromUserUnit(float(self.m_txtViaDrillSize.GetValue()))
        viasize = self.FromUserUnit(float(self.m_txtViaSize.GetValue()))
        netname = self.m_cbNet.GetStringSelection()
        netcode = self.board.GetNetcodeFromNetname(netname)
        #commit = pcbnew.COMMIT()
        viacount = 0

        for item in self.board.GetTracks():
            if type(item) is pcbnew.VIA:
                #If the user selected the Undo action only signed vias are removed, 
                #otherwise are removed vias matching values set in the dialog.
                if undo and (item.GetTimeStamp() == __timecode__):
                    self.board.Remove(item)
                    viacount+=1
                    #commit.Remove(item)
                elif (not undo) and self.area.HitTestInsideZone(item.GetPosition()) and (item.GetDrillValue() == drillsize) and (item.GetWidth() == viasize) and (item.GetNetname() == netname):
                    self.board.Remove(item)
                    viacount+=1
                    #commit.Remove(item)

        if viacount > 0:
            wx.MessageBox(_(u"Removed: %d vias!") % viacount)
            #commit.Push()
            pcbnew.Refresh()


    def CheckClearance(self, p1, area, clearance):
        """Check if position specified by p1 comply with given clearance in area.

        Parameters:
            p1 (wxPoint): Position to test
            area (pcbnew.ZONE_CONTAINER): Area
            clearance (int): Clearance value

        Returns:
            bool: True if p1 position comply with clearance value False otherwise.

        """

        corners = area.GetNumCorners()
        #Calculate minimum distance from corners
        #TODO: remove?
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


    def CheckOverlap(self, via):
        """Check if via overlaps or interfere with other items on the board.

        Parameters:
            via (pcbnew.VIA): Via to be checked

        Returns:
            bool: True if via overlaps with an item, False otherwise.
        """

        for item in self.overlappings:
            if type(item) is pcbnew.D_PAD:
                if item.GetBoundingBox().Intersects( via.GetBoundingBox() ):
                    return True
            elif type(item) is pcbnew.VIA:
                #Overlapping with vias work best if checking is performed by intersection
                if item.GetBoundingBox().Intersects( via.GetBoundingBox() ):
                    return True
            elif type(item) is pcbnew.ZONE_CONTAINER:
                if item.HitTestInsideZone( via.GetPosition() ):
                    return True
        
        return False


    def FillupArea(self):
        '''Fills selected area with vias.'''        

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

        #Cycle trough area bounding box checking and implanting vias
        layer = self.area.GetLayer()
        while x <= right:
            y = top
            while y <= bottom:
                p = pcbnew.wxPoint(x,y)
                if self.area.HitTestInsideZone(p):
                    via = pcbnew.VIA(self.board)
                    via.SetPosition(p)
                    via.SetLayer(layer)
                    via.SetNetCode(netcode)
                    via.SetDrill(drillsize)
                    via.SetWidth(viasize)
                    via.SetTimeStamp(__timecode__)
                    if not self.CheckOverlap(via):
                        #Check clearance only if clearance value differs from 0 (disabled)
                        if (clearance == 0) or self.CheckClearance(p, self.area, clearance):
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
        '''Manage main button (Ok) click event.'''

        if(self.m_rFill.GetValue()):
            self.FillupArea()
        else:
            self.ClearArea()

        self.Destroy()

    
    def onRadioButtonCheck(self, event):
        '''Manage radio button state change event.'''

        if self.m_rClear.GetValue():
            self.m_chkClearOwn.Enable()
        else:
            self.m_chkClearOwn.Disable()


    def onCloseWindow(self, event):
        '''Manage Close button click event.'''

        self.Destroy()


def InitViaStitchingDialog(board):
    '''Initalize dialog.'''

    dlg = ViaStitchingDialog(board)
    dlg.Show(True)
    return dlg
