#
# priority_thread.py
#
# Copyright (C) 2010 Nick Lanham <nick@afternight.org>
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

from deluge.ui.client import client
import deluge.component as component

__target_priority = 5
__last_first = {}
__n_extra = 15

def priority_loop(meth):
    torrents = meth()

    for t in torrents: #go through all torrents
        tor = component.get("TorrentManager").torrents[t]

        if tor.status.state == tor.status.downloading:
            #get first piece corresponding to this torrent
            #stored from last looping call
            lf = __last_first.get(t)

            if not(lf):
                lf = 0
            try:
                #pick up where we left off in the last looping call
                i_piece = tor.status.pieces.index(False,lf)
                prios = tor.handle.piece_priorities()

                #loop until we've marked the next undownloaded piece
                while (tor.handle.have_piece(i_piece) == True): #downloaded by now
                    i_piece += 1

                    #find number of pieces after i_piece that are marked for download
                    #i=index (starting at i_piece), p=priority
                    for (i,p) in enumerate(prios[i_piece:]):
                        if p > 0:
                            i_piece = i + i_piece
                            break

                j_piece = 0
                n = 0
                #loop again and mark __n_extra pieces for higher priority
                for (i,p) in enumerate(prios[i_piece:]):
                    if n >= __n_extra:
                        break

                    if p > 0: #marked for download
                        j_piece = i + i_piece

                        if (tor.handle.have_piece(j_piece) == False): #not downloaded yet
                            n += 1

                            if (tor.handle.piece_priority(j_piece) < __target_priority):
                                tor.handle.piece_priority(j_piece, __target_priority)

                __last_first[t] = i_piece

            except ValueError:
                continue
