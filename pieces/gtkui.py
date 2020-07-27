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

from __future__ import division, unicode_literals, absolute_import

import logging
import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk
from deluge.ui.client import client
from deluge.plugins.pluginbase import Gtk3PluginBase
import deluge.component as component
from deluge.ui.gtk3.torrentdetails import Tab
from .common import get_resource
from six.moves import range
from .multi_square import MultiSquare
from .colors import Colors
from twisted.internet import reactor

log = logging.getLogger(__name__)

class PiecesTab(Tab):
    def __init__(self):
        Tab.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(get_resource('pieces_tab.ui'))

        self._name = "Pieces"
        self._child_widget = builder.get_object("pieces_tab")
        self._tab_label = builder.get_object("pieces_tab_label")

        self._ms = MultiSquare(0,
                               display=self._child_widget.get_display(),
                               menu=builder.get_object("priority_menu"))

        vb = Gtk.VBox()
        vb.add(self._ms)
        self.cb = Gtk.CheckButton(label="Set priority of first few un-downloaded pieces to High")
        self.cb.connect("toggled",self.onPrioTogg)
        vb.pack_end(self.cb,expand=False,fill=False,padding=5)

        vp = Gtk.Viewport()
        vp.set_shadow_type(Gtk.ShadowType.NONE)
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
        md = Gtk.MessageDialog(component.get("MainWindow").get_builder().get_object("main_window"),
                               Gtk.DialogFlags.MODAL,
                               Gtk.MessageType.WARNING,
                               Gtk.ButtonsType.OK,
                               "Using this option for torrents with an unhealthy swarm is rather unsocial and not particularly good for the swarm.\n\nPlease use with care.")
        md.connect('response', self.__dest)
        md.show_all()

        return False

    def set_config(self, config):
        self._ms.set_colors(Colors(config))
        self._ms.set_square_size(config['square_size'])
        self._ms.set_square_border_size(config['square_border_size'])

    def clear(self):
        self._ms.clear()
        self._current = None

    def __update_callback(self, args):
        (is_fin, num_pieces, pieces, curdl) = args
        if (num_pieces == 0):
            return
        if (is_fin):
            self._ms.set_num_squares(num_pieces)
            for i in range (0,num_pieces):
                self._ms.set_square_color(i, 1)
            return

        self._ms.set_num_squares(num_pieces)

        cdll = len(curdl)
        cdli = 0
        if (cdll == 0):
            cdli = -1

        for i,p in enumerate(pieces):
            if p:
                self._ms.set_square_color(i, 1)
            elif (cdli != -1 and i == curdl[cdli]):
                self._ms.set_square_color(i, 2)
                cdli += 1
                if cdli >= cdll:
                    cdli = -1
            else:
                self._ms.set_square_color(i, 0)

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()
        # Only use the first torrent in the list or return if None selected
        if len(selected) != 0:
            selected = selected[0]
            if(selected != self._current):
                #new torrent selected, clear the selected pieces, update priority checkbox
                self._ms.reset_selected()
                self._current = selected
                client.pieces.is_priority_torrent(self._current).addCallback(self.cb.set_active)
        else:
            # No torrent is selected in the torrentview
            return

        client.pieces.get_torrent_info(selected).addCallback(self.__update_callback)


class GtkUI(Gtk3PluginBase):
    def __init__(self, plugin_name):
        super().__init__(plugin_name)
        self._pieces_tab = PiecesTab()
        self.builder_cfg = Gtk.Builder()

    def enable(self):
        log.info("Enabling Pieces Tab...")
        self.builder_cfg.add_from_file(get_resource('config.ui'))

        component.get("TorrentDetails").add_tab(self._pieces_tab)
        client.pieces.get_config().addCallback(self.set_config)

        component.get("Preferences").add_page("Pieces", self.builder_cfg.get_object("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

    def disable(self):
        log.info("Disabling Pieces Tab...")
        component.get("Preferences").remove_page("Pieces")
        component.get("TorrentDetails").remove_tab("Pieces")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        config = {
            "not_dled_color":self.builder_cfg.get_object("not_dl_button").get_color().to_string(),
            "dled_color":self.builder_cfg.get_object("dl_button").get_color().to_string(),
            "dling_color":self.builder_cfg.get_object("dling_button").get_color().to_string(),
            "hover_border": self.builder_cfg.get_object("hover_border").get_color().to_string(),
            "selected_border": self.builder_cfg.get_object("selected_border").get_color().to_string(),
            "square_size": self.builder_cfg.get_object("square_size").get_value(),
            "square_border_size": self.builder_cfg.get_object("square_border_size").get_value()
        }
        client.pieces.set_config(config)
        client.pieces.get_config().addCallback(self.set_config)

    def on_show_prefs(self):

        client.pieces.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.builder_cfg.get_object("not_dl_button").set_color(Gdk.color_parse(config["not_dled_color"]))
        self.builder_cfg.get_object("dl_button").set_color(Gdk.color_parse(config["dled_color"]))
        self.builder_cfg.get_object("dling_button").set_color(Gdk.color_parse(config["dling_color"]))
        self.builder_cfg.get_object("hover_border").set_color(Gdk.color_parse(config["hover_border"]))
        self.builder_cfg.get_object("selected_border").set_color(Gdk.color_parse(config["selected_border"]))
        self.builder_cfg.get_object("square_size").\
            configure(Gtk.Adjustment(config["square_size"], 5, 100, 1, 0, 0), 1, 0)
        self.builder_cfg.get_object("square_border_size"). \
            configure(Gtk.Adjustment(config["square_border_size"], 0, 100, 1, 0, 0), 1, 0)

    def set_config(self, config):
        self._pieces_tab.set_config(config)
