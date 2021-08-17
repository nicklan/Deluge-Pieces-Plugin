# multi_square.py
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

from __future__ import absolute_import

import logging
import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk
from deluge.ui.client import client
from six.moves import range

log = logging.getLogger(__name__)

class MultiSquare(Gtk.DrawingArea):
    def __init__(self, num_squares=0, display=None, menu=None):
        super(MultiSquare, self).__init__()

        self.colors = None
        self.square_size = 10
        self.square_border_size = 4
        self.num_squares = num_squares
        self.selected = {}
        self.last_selected = -1
        self.color_index = {}
        self.menu = menu
        self.display = display
        self.squares_per_row = 0
        self.hovered_square = None
        self.button1_in = False

        for item in menu.get_children():
            item.connect("activate", self.priority_activate)

        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK)

        self.connect("draw", self.draw)
        self.set_property("has-tooltip", True)

        self.connect("query-tooltip", self.query_tooltip_handler)
        self.connect("motion-notify-event", self.mouse_hover_handler)
        self.connect("button-press-event", self.button_press_event_handler)
        self.connect("button-release-event", self.button_release_event_handler)

    def mouse_hover_handler(self, widget, event):
        if self.button1_in:
            # set the draged over square selected
            idx = self.get_index(event.x, event.y)
            if idx == -1:
                return
            self.selected[idx] = True
            self.last_selected = idx
            self.queue_draw()

        return True

    def query_tooltip_handler(self, widget, x, y, keyboard_mode, tooltip):
        square = self.get_index(x, y)
        self.hovered_square = square

        if square == -1:
            return False

        def __qtt_callback(args):
            (square, priority) = args
            pris = {
                0: lambda: "Do Not Download",  # Skip
                1: lambda: "Normal (1)",  # Low
                2: lambda: "High (2)",
                3: lambda: "High (3)",
                4: lambda: "High (4)",  # Normal
                5: lambda: "Higher (5)",
                6: lambda: "Higher (6)",
                7: lambda: "Highest (7)"  # High
            }[priority]()
            text = "Piece: %i (%s)" % (square, pris)

            tooltip.set_text(text)

        self.queue_draw()

        text = "Piece: %i (%s)" % (square, "Loading...")
        tooltip.set_text(text)
        client.pieces.get_piece_priority(square).addCallback(__qtt_callback)

        return True

    def button_press_event_handler(self, widget, event):
        if event.button == 3 and self.menu != None:
            index = self.get_index(event.x, event.y)
            if index == -1:
                return False
            if not self.is_selected(index):
                if not (event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)):
                    self.reset_selected()
                self.selected[index] = True
            self.last_selected = index
            self.menu.popup(None,
                            None,
                            None,
                            None,
                            event.button,
                            Gtk.get_current_event_time())

        # set button in true
        # clear the current selection and set this square as selected
        if event.button == 1:
            self.button1_in = True
            index = self.get_index(event.x, event.y)
            if (event.state & Gdk.ModifierType.SHIFT_MASK) and (self.last_selected != -1):
                if index != -1:
                    for i in range(self.last_selected, index):
                        self.selected[i] = True
            else:
                if not (event.state & Gdk.ModifierType.CONTROL_MASK):
                    self.reset_selected()
                if index != -1:
                    self.selected[index] = True
                    self.last_selected = index
            self.queue_draw()

        return False

    def button_release_event_handler(self, widget, event):
        if event.button == 1:
            self.button1_in = False

        return False

    def get_index(self, x, y):
        cell_size = self.get_cell_size()
        row_len = self.squares_per_row * cell_size
        if x < row_len:
            rows = int(y / cell_size)
            columns = int(x / cell_size)

            index = self.squares_per_row * rows + columns

            if index < self.num_squares:
                return index

        return -1

    def set_colors(self, colors):
        self.colors = colors
        self.queue_draw()

    def set_square_size(self, square_size):
        self.square_size = square_size
        self.queue_draw()

    def set_square_border_size(self, square_border_size):
        self.square_border_size = square_border_size
        self.queue_draw()

    def clear(self):
        self.num_squares = 0
        self.queue_draw()

    def reset_selected(self):
        '''resets the selected squares'''
        self.selected = {}
        self.last_selected = -1
        self.queue_draw()

    def set_num_squares(self, numSquares):
        if self.num_squares != numSquares:
            self.num_squares = numSquares
            self.queue_draw()

    def set_square_color(self, square, color):
        self.color_index[square] = color
        self.queue_draw()

    def draw(self, widget, cairoContext):
        rect = widget.get_allocation()
        first = 0
        last = self.num_squares
        columns = 0
        # half of the width of the border overlaps with the square; we must thus draw the squares
        # half of the border width away from the edge in order to avoid borders adjacent to the top
        # and left edges being partially hidden.
        offset = int(self.square_border_size / 2)
        if self.square_border_size & 1:
            offset = offset + 1
        x = offset
        y = offset
        cell_size = self.get_cell_size()
        self.squares_per_row = int(rect.width / cell_size)

        rows = int(self.num_squares / self.squares_per_row)
        if (rows * self.squares_per_row) != self.num_squares:
            rows = rows + 1

        widget.set_size_request(rect.width, rows * cell_size)

        for square in range(first, last):

            try:
                color = self.get_color(self.color_index[square])
            except KeyError:
                color = self.get_color(0)

            cairoContext.set_source_rgb(color.red_float, color.green_float, color.blue_float)
            cairoContext.rectangle(x, y, self.square_size, self.square_size)

            if not self.is_selected(square) and not self.is_hovered(square):
                cairoContext.fill()

            if self.is_selected(square) or self.is_hovered(square):
                color = self.colors.get_hover_border().get_color()
                if self.is_selected(square):
                    color = self.colors.get_selected_border().get_color()

                cairoContext.fill_preserve()
                cairoContext.set_line_width(self.square_border_size)
                cairoContext.set_source_rgb(color.red_float, color.green_float, color.blue_float)
                cairoContext.stroke()

            x = x + cell_size
            columns = columns + 1
            if columns == self.squares_per_row:
                columns = 0
                x = offset
                y = y + cell_size

        return False

    def get_cell_size(self):
        return self.square_border_size + self.square_size + 1

    def is_selected(self, square):
        return square in self.selected

    def is_hovered(self, square):
        return square == self.hovered_square

    def get_color(self, index):
        switcher = {
            0: self.colors.get_not_downloaded_color().get_color(),
            1: self.colors.get_downloaded_color().get_color(),
            2: self.colors.get_downloading_color().get_color()
        }

        return switcher.get(index, Gdk.Color(0, 0, 0))

    def priority_activate(self, widget):
        '''set the priorities of the selected squares'''
        label = widget.get_label()
        priority = None
        if label == "Normal":
            priority = 1
        elif label == "High":
            priority = 2
        elif label == "Higher":
            priority = 5
        elif label == "Highest":
            priority = 7
        elif label == "Do Not Download":
            priority = 0

        # update every selected piece
        if isinstance(priority, int):
            client.pieces.piece_priorities(self.selected, priority)

        self.reset_selected()

        return False
