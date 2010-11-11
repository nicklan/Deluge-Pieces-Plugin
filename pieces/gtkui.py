#
# gtkui.py
#
# Copyright (C) 2009 Nick Lanham <nick@afternight.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common
from deluge.ui.gtkui.torrentdetails import Tab

from common import get_resource

class MultiSquare(gtk.DrawingArea):
    def __init__(self, numSquares=0, colors=['#000000'],menu=None):
        gtk.DrawingArea.__init__(self)
        self.numSquares = numSquares
        self.menu = menu
        self.button1_in = False

        for item in menu.get_children():
            item.connect("activate",self.priority_activate)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.BUTTON1_MOTION_MASK)
        colormap = self.get_colormap()
        self.colors = []
        for color in colors:
            self.colors.append(colormap.alloc_color(color, True, True))
        self.colorIndex = {}
        self.selected = {}

        self.connect("expose_event", self.expose)
        self.set_property("has-tooltip",True)
        self.connect("query-tooltip",self.qtt)
        self.connect("button-press-event",self.bpe)
        self.connect("button-release-event",self.bre)
        self.connect('motion-notify-event', self.mne)

    def resetSelected(self):
        '''resets the selected squares'''
        self.selected = {}

    def mne(self, widget, event):
        '''called on motion notify event'''
        if (self.window == None):
            return
        if (self.button1_in):
            #set the draged over square selected
            self.selected[self.getIndex(event.x, event.y)] = True
            self.queue_draw()
        return True


    def qtt(self,widget, x, y, keyboard_mode, tooltip):
        '''called on query tooltip'''
        if (self.window == None):
            return
        sq = self.getIndex(x,y)
        if (sq >= self.numSquares):
            return False
        pri = self._handle.piece_priority(sq)        
        pris = {
            0: lambda : "Do Not Download",
            1: lambda : "Normal",
            2: lambda : "High",
            5: lambda : "Higher",
            7: lambda : "Highest"
            }[pri]()
        tooltip.set_text("Piece: %i (%s)" % (sq,pris))
        return True

    def bpe(self, widget, event):
        '''called on button press event'''
        if (self.window == None):
            return
        if (event.button == 3 and self.menu != None):
            self._priox = event.x
            self._prioy = event.y
            self.menu.popup(None,
                            None,
                            None,
                            event.button,
                            gtk.get_current_event_time())

        #set button in true
        #clear the current selection and set this square as selected
        if(event.button == 1):
            self.button1_in = True
            for i in range(0,self.numSquares):
                self.selected[i]=False
            index = self.getIndex(event.x, event.y)
            if index < self.numSquares:
                self.selected[index] = True
            self.queue_draw()
        #self.emit("expose-event",  gtk.gdk.Event(gtk.gdk.EXPOSE))


        return False

    def bre(self, widget, event):
        '''called on button release event'''
        if (self.window == None):
            return
        if(event.button == 1):
            self.button1_in = False
        return False

    def getIndex(self,x,y):
        '''returns the index of the square on position x,y'''
        rect = self.get_allocation()
        numAcross =  rect.width / 12
        row = int(y) / 12
        col = int(x) / 12
        return row*numAcross+col

    def priority_activate(self, widget):
        '''set the priorities of the selected squares'''
        if (self.window == None):
            return
        name = widget.get_name()
        if (name == "normal_item"):
            priority = 1
        elif (name == "high_item"):
            priority = 2
        elif (name == "higher_item"):
            priority = 5
        elif (name == "highest_item"):
            priority = 7
        elif (name == "no_item"):
            priority = 0

        #update every selected piece
        for i in self.selected:
            if self.selected[i]: # if actually selected
                self._handle.piece_priority(i,priority)
        return False

    def setSquareColor(self,square,color):
        try:
            if self.colorIndex[square] == color:
                return
        except KeyError:
            pass

        if (color == 0):
            try:
                del self.colorIndex[square]
                self.invalidateSquare(square)
            except KeyError:
                pass
        else:
            self.colorIndex[square] = color
            self.invalidateSquare(square)

    def unsetSquareColor(self,square):
        try:
            del self.colorIndex[square]
            invalidateSquare(square)
        except KeyError:
            pass

    def invalidateSquare(self,square):
        if (self.window == None):
            return
        rect = self.get_allocation()
        numAcross =  rect.width / 12
        x = (square % numAcross)*12
        y = (square / numAcross)*12
        rec = gtk.gdk.Rectangle(x, y,12, 12)
        self.window.invalidate_rect(rec,False)

    def setNumSquares(self,numSquares):
        if (self.numSquares != numSquares):
            self.numSquares = numSquares
            self.queue_draw()

    def setTorrentHandle(self,handle):
        self._handle = handle

    def setColors(self,colors):
        colormap = self.get_colormap()
        self.colors = []
        for color in colors:
            self.colors.append(colormap.alloc_color(color, True, True))
        self.queue_draw()

    def expose(self, widget, event):
        self.context = widget.window.new_gc()
        
        # set a clip region for the expose event
        rec = gtk.gdk.Rectangle(event.area.x, event.area.y,
                                event.area.width, event.area.height)
        self.context.set_clip_rectangle(rec)
        
        self.draw(self.context)
        
        return False
    
    def draw(self, context):
        rect = self.get_allocation()
        plen = self.numSquares

        width =  rect.width
        height = ((plen / (width / 12)) + 1)*12
        width -= 12
        self.set_size_request(width,height)

        x = y = 0
        setColor = False
        context.set_foreground(self.colors[0])
        
	for i in range(0,self.numSquares):
            try:
                #if this square is selected,visualize this
                if self.selected[i]:
                    context.set_foreground( self.get_colormap().alloc_color('#000000', True, True))
                    self.window.draw_rectangle(context, True,x,y,11,11)
                    setColor = True
            except KeyError: # no key for this index
                pass
            
            try:
                color = self.colorIndex[i]
                context.set_foreground(self.colors[color])
                setColor = True
            except KeyError: # no key for this index
                if (setColor):
                    context.set_foreground(self.colors[0])
                    setColor = False
                else:
                    pass
            self.window.draw_rectangle(context,True,x,y,10,10)
            x += 12
            if (x > width):
                x = 0
                y += 12
        return False


class PiecesTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        glade_tab = gtk.glade.XML(get_resource("pieces_tab.glade"))

        self._name = "Pieces"
        self._child_widget = glade_tab.get_widget("pieces_tab")
        self._tab_label = glade_tab.get_widget("pieces_tab_label")

        self._ms = MultiSquare(0,['#000000','#FF0000','#0000FF'],glade_tab.get_widget("priority_menu"))
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        #self._child_widget.connect("motion-notify-event",self.motion)
        #self._child_widget.set_events(vp.get_events() |
        #                              gtk.gdk.MOTION_NOTIFY)
        vp.add(self._ms)
        self._child_widget.add(vp)
        self._child_widget.get_parent().show_all()

        #keep track of the current selected torrent
        self._current = -1


        self._tid_cache = ""
        self._nump_cache = 0

    def motion(self,widget,event):
        print "MOTION"

    def setColors(self,colors):
        self._ms.setColors(colors)

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(selected) != 0:
            selected = selected[0]
            if(selected != self._current):
                #new torrent selected, clear the selected pieces
                self._ms.resetSelected()
                self._current = selected
        else:
            # No torrent is selected in the torrentview
            return

        tor = component.get("TorrentManager").torrents[selected]
        stat = tor.status

        #if (self._tid_cache == selected and
        #    self._nump_cache ==  stat.num_pieces):
        #    return

        self._tid_cache = selected
        self._nump_cache = stat.num_pieces
        self._ms.setTorrentHandle(tor.handle)

        plen = len(stat.pieces)
        self._ms.setNumSquares(plen)
        if (plen <= 0):
            if (stat.num_pieces == 0):
                return
            if (stat.state == stat.seeding or
                stat.state == stat.finished):
                self._ms.setNumSquares(stat.num_pieces)
                for i in range (0,stat.num_pieces):
                    self._ms.setSquareColor(i,1)
                return

        peers = tor.handle.get_peer_info()
        curdl = []
        for peer in peers:
            if peer.downloading_piece_index != -1:
                curdl.append(peer.downloading_piece_index)

        curdl = dict.fromkeys(curdl).keys() 
        curdl.sort()
        cdll = len(curdl)
        cdli = 0
        if (cdll == 0):
            cdli = -1

	for i,p in enumerate(stat.pieces):
            if p:
                self._ms.setSquareColor(i,1)
            elif (cdli != -1 and i == curdl[cdli]):
                self._ms.setSquareColor(i,2)
                cdli += 1
                if cdli >= cdll:
                    cdli = -1
            else:
                self._ms.setSquareColor(i,0)
        #



class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade_cfg = gtk.glade.XML(get_resource("config.glade"))
        self._pieces_tab = PiecesTab()
        component.get("TorrentDetails").add_tab(self._pieces_tab)
        client.pieces.get_config().addCallback(self.set_colors)

        component.get("Preferences").add_page("Pieces", self.glade_cfg.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

    def disable(self):
        component.get("Preferences").remove_page("Pieces")
        component.get("TorrentDetails").remove_tab("Pieces")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Pieces")
        config = {
            "not_dled_color":self.glade_cfg.get_widget("not_dl_button").get_color().to_string(),
            "dled_color":self.glade_cfg.get_widget("dl_button").get_color().to_string(),
            "dling_color":self.glade_cfg.get_widget("dling_button").get_color().to_string()
        }
        client.pieces.set_config(config)
        client.pieces.get_config().addCallback(self.set_colors)

    def on_show_prefs(self):
        client.pieces.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade_cfg.get_widget("not_dl_button").set_color(gtk.gdk.color_parse(config["not_dled_color"]))
        self.glade_cfg.get_widget("dl_button").set_color(gtk.gdk.color_parse(config["dled_color"]))
        self.glade_cfg.get_widget("dling_button").set_color(gtk.gdk.color_parse(config["dling_color"]))

    def set_colors(self, config):
        self._pieces_tab.setColors([
            config["not_dled_color"],
            config["dled_color"],
            config["dling_color"]])
