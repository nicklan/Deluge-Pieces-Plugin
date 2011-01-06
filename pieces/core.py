#
# core.py
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

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

from twisted.internet.task import LoopingCall, deferLater
from twisted.internet import reactor
from priority_thread import priority_loop

DEFAULT_PREFS = {
    "not_dled_color":"#000000",
    "dled_color":"#FF0000",
    "dling_color":"#0000FF"
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("pieces.conf", DEFAULT_PREFS)
        self.not_dled_color = self.config['not_dled_color']
        self.dled_color = self.config['dled_color']
        self.dling_color = self.config['dling_color']
        self.priority_loop = None
        self.priority_torrents = {}
        deferLater(reactor, 5, self.enable_priority_loop)

    def enable_priority_loop(self):
        self.priority_loop = LoopingCall(priority_loop,self.get_priority_torrents)
        self.priority_loop.start(2)

    def disable(self):
        if self.priority_loop and self.priority_loop.running:
            self.priority_loop.stop()

    def update(self):
        pass

    @export 
    def get_torrent_info(self, tid):
        tor = component.get("TorrentManager").torrents[tid]
        self.__handle_cache = tor.handle
        stat = tor.status

        plen = len(stat.pieces)
        if (plen <= 0):
            if (stat.num_pieces == 0):
                return (True, 0, None, None)
            if (stat.state == stat.seeding or stat.state == stat.finished):
                return (True, stat.num_pieces, None, None)

        peers = tor.handle.get_peer_info()
        curdl = []
        for peer in peers:
            if peer.downloading_piece_index != -1:
                curdl.append(peer.downloading_piece_index)

        curdl = dict.fromkeys(curdl).keys() 
        curdl.sort()

        return (False, plen, stat.pieces, curdl)

    @export
    def get_piece_priority(self, pid):
        return pid,self.__handle_cache.piece_priority(pid)

    @export
    def piece_priorities(self, selected, priority):
        for i in selected:
            if selected[i]: 
                self.__handle_cache.piece_priority(i,priority)

    @export
    def add_priority_torrent(self, torr):
        "add a torrent to have first un-downloaded piece priority boosted"
        self.priority_torrents[torr] = True

    @export
    def del_priority_torrent(self, torr):
        "stop a torrent trom having its first un-downloaded piece priority boosted"
        if self.priority_torrents.get(torr):
            del self.priority_torrents[torr]

    @export
    def is_priority_torrent(self, torr):
        "return True if torrent is in list of torrents to prioritize first un-downloaded piece, else False"
        if self.priority_torrents.get(torr):
            return True
        else:
            return False

    @export
    def get_priority_torrents(self):
        "get dict of torrents with first un-downloaded piece priority boosted"
        return self.priority_torrents

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
