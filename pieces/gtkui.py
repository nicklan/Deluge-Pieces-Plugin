# gtkui.py
#
# Copyright (C) 2009 Nick Lanham <nick@afternight.org>
# Copyright (C) 2010 Jens Timmerman <jens.timmerman@gmail.com>
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

from twisted.internet import reactor

from common import get_resource

class MultiSquare(gtk.DrawingArea):
    def __init__(self, numSquares=0, colors=['#000000'],display=None,menu=None):
        gtk.DrawingArea.__init__(self)
        self.numSquares = numSquares
        self.menu = menu
        self.display = display
        self.button1_in = False

        for item in menu.get_children():
            item.connect("activate",self.priority_activate)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.BUTTON1_MOTION_MASK)
        colormap = self.get_colormap()
        self.colors = []
        alpha_fg = colormap.alloc_color("#3EBDD6",True,True)
        self.alpha_colors = []
        for color in colors:
            cc = colormap.alloc_color(color, True, True)
            self.colors.append(cc)
            self.alpha_colors.append(self.alpha_blend(alpha_fg,cc,0.5))

        self.bg_sel_color = self.alpha_blend(alpha_fg,self.style.bg[0],0.5)

        self.colorIndex = {}
        self.selected = {}
        self.last_selected = -1
        self.__sq = -1

        self.connect("expose_event", self.expose)
        self.set_property("has-tooltip",True)
        self.connect("query-tooltip",self.qtt)
        self.connect("button-press-event",self.bpe)
        self.connect("button-release-event",self.bre)
        self.connect('motion-notify-event', self.mne)


    def alpha_blend(self,fg, bg, alpha):
        '''Alpha blend some colors.'''
        fg_vals = []
        bg_vals = []

        am = (1 - alpha)

        target_red = am * bg.red_float + (alpha * fg.red_float)
        target_green = am * bg.green_float + (alpha * fg.green_float)
        target_blue = am * bg.blue_float + (alpha * fg.blue_float)

        return self.get_colormap().alloc_color(int(round(target_red * 65535)),
                                               int(round(target_green * 65535)),
                                               int(round(target_blue * 65535)),
                                               True,True)

    def resetSelected(self):
        '''resets the selected squares'''
        self.selected = {}
        self.last_selected = -1

    def mne(self, widget, event):
        '''called on motion notify event'''
        if (self.window == None or event.x < 0 or event.y < 0):
            return
        if (self.button1_in):
            #set the draged over square selected
            idx = self.getIndex(event.x, event.y)
            if (idx >= self.numSquares):
                return
            self.selected[idx] = True
            self.last_selected = idx
            self.queue_draw()
        return True

    def __qtt_callback(self, (sq,pri)):
        pris = {
            0: lambda : "Do Not Download",
            1: lambda : "Normal (1)",
            2: lambda : "High (2)",
            3: lambda : "High (3)",
            4: lambda : "High (4)",
            5: lambda : "Higher (5)",
            6: lambda : "Higher (6)",
            7: lambda : "Highest (7)"
            }[pri]()
        self.__sq = sq
        self.__tooltip_text = "Piece: %i (%s)" % (sq, pris)
        gtk.tooltip_trigger_tooltip_query(self.display)

    def qtt(self, widget, x, y, keyboard_mode, tooltip):
        '''called on query tooltip'''
        if (self.window == None):
            return
        sq = self.getIndex(x,y)
        if (sq >= self.numSquares):
            return False

        if (sq != self.__sq):
            self.__tooltip_text = "Piece: %i (%s)" % (sq,"Loading...")
            client.pieces.get_piece_priority(sq).addCallback(self.__qtt_callback)
        tooltip.set_text(self.__tooltip_text)
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
            index = self.getIndex(event.x, event.y)
            if ((event.state & gtk.gdk.SHIFT_MASK) and (self.last_selected != -1)):
                index += 1
                end = min(index,self.numSquares)
                for i in range(self.last_selected,end):
                    self.selected[i] = True
            else:
                if not(event.state & gtk.gdk.CONTROL_MASK):
                    self.resetSelected()
                if index < self.numSquares:
                    self.selected[index] = True
                    self.last_selected = index
            self.queue_draw()
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
        client.pieces.piece_priorities(self.selected,priority)
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

    def clear(self):
        self.numSquares = 0
        self.queue_draw()
    
    def draw(self, context):
        rect = self.get_allocation()
        plen = self.numSquares

        width =  rect.width
        numAcross = width / 12 
        height = ((plen / (width / 12)) + 1)*12
        width -= 12
        self.set_size_request(width,height)

        setColor = False
        context.set_foreground(self.colors[0])

        visrect = self.window.get_visible_region().get_clipbox()
        first = (visrect.y/12)*numAcross
        last = first + (visrect.height/12 + 2)*numAcross
        last = min(last,self.numSquares)

        x = 0
        y = visrect.y - (visrect.y%12)

	for i in range(first,last):
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

            #if this square is selected,visualize this
            try:
                if self.selected[i]:
                    context.set_foreground(self.bg_sel_color)
                    self.window.draw_rectangle(context, True,x,y,12,12)
                    try:
                        color = self.colorIndex[i]
                        context.set_foreground(self.alpha_colors[color])
                    except KeyError: # no key for this index
                        context.set_foreground(self.alpha_colors[0])
                    setColor = True
                    self.window.draw_rectangle(context, True,x,y,10,10)
            except KeyError:
                pass

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

        self._ms = MultiSquare(0,['#000000','#FF0000','#0000FF'],
                               display=self._child_widget.get_display(),
                               menu=glade_tab.get_widget("priority_menu"))

        vb = gtk.VBox()
        vb.add(self._ms)
        self.cb = gtk.CheckButton(label="Set priority of first un-downloaded piece to High")
        self.cb.connect("toggled",self.onPrioTogg)
        vb.pack_end(self.cb,expand=False,fill=False,padding=5)

        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(vb)


        self._child_widget.add(vp)
        self._child_widget.get_parent().show_all()

        #keep track of the current selected torrent
        self._current = -1

        self._showed_prio_warn = False


    def onPrioTogg(self,widget):
        if (self._current):
            if (widget.get_active()):
                if not(self._showed_prio_warn):
                    reactor.callLater(0,self._showPrioWarn)
                    self._showed_prio_warn = True
                client.pieces.add_priority_torrent(self._current)
            else:
                client.pieces.del_priority_torrent(self._current)
        else:
            widget.set_active(False)

    def __dest(self, widget, response):
        widget.destroy()

    def _showPrioWarn(self):
        md = gtk.MessageDialog(component.get("MainWindow").main_glade.get_widget("main_window"),
                               gtk.DIALOG_MODAL,
                               gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_OK,
                               "Using this option is rather unsocial and not particularly good for the torrent protocol.\n\nPlease use with care, and seed the torrent afterwards if you use this.")
        md.connect('response', self.__dest)
        md.show_all()
        return False


    def setColors(self,colors):
        self._ms.setColors(colors)

    def clear(self):
        self._ms.clear()
        self._current = None

    def __update_callback(self, (is_fin, num_pieces, pieces, curdl)):
        if (num_pieces == 0):
            return
        if (is_fin):
            self._ms.setNumSquares(num_pieces)
            for i in range (0,num_pieces):
                self._ms.setSquareColor(i,1)
            return

        self._ms.setNumSquares(num_pieces)

        cdll = len(curdl)
        cdli = 0
        if (cdll == 0):
            cdli = -1

	for i,p in enumerate(pieces):
            if p:
                self._ms.setSquareColor(i,1)
            elif (cdli != -1 and i == curdl[cdli]):
                self._ms.setSquareColor(i,2)
                cdli += 1
                if cdli >= cdll:
                    cdli = -1
            else:
                self._ms.setSquareColor(i,0)


    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(selected) != 0:
            selected = selected[0]
            if(selected != self._current):
                #new torrent selected, clear the selected pieces, update priority checkbox
                self._ms.resetSelected()
                self._current = selected
                client.pieces.is_priority_torrent(self._current).addCallback(self.cb.set_active)
        else:
            # No torrent is selected in the torrentview
            return

        client.pieces.get_torrent_info(selected).addCallback(self.__update_callback)


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
