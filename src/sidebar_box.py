# cover_box.py
#
# Copyright 2018 Gerben Droogers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib, GObject
from .gi_composites import GtkTemplate

from .section_grid import SectionGrid

import threading

@GtkTemplate(ui='/nl/g4d/Girens/sidebar_box.ui')
class SidebarBox(Gtk.Box):
    __gtype_name__ = 'sidebar_box'

    __gsignals__ = {
        'home-button-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'playlists-button-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'player-button-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'section-clicked': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    _server_box = GtkTemplate.Child()
    _section_list = GtkTemplate.Child()

    def __init__(self, plex, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

        self._plex = plex

        self._plex.connect('servers-retrieved', self.__on_servers_retrieved)
        self._plex.connect('sections-retrieved', self.__on_sections_retrieved)

        self._section_list.connect("row-selected", self.__on_section_clicked)

    def refresh(self):
        thread = threading.Thread(target=self._plex.get_servers)
        thread.daemon = True
        thread.start()

        for item in self._section_list.get_children():
            self._section_list.remove(item)

        thread = threading.Thread(target=self._plex.get_sections)
        thread.daemon = True
        thread.start()

    def unselect_all(self):
        self._section_list.unselect_all()

    def __on_servers_retrieved(self, plex, servers):
        GLib.idle_add(self.__process_servers, servers)

    def __on_sections_retrieved(self, plex, sections):
        GLib.idle_add(self.__process_section, sections)

    def __process_section(self, sections):
        section_grid = SectionGrid()
        section_grid.set_title('Player')
        self._section_list.add(section_grid)
        section_grid = SectionGrid()
        section_grid.set_title('Home')
        self._section_list.add(section_grid)
        section_grid = SectionGrid()
        section_grid.set_title('Playlists')
        self._section_list.add(section_grid)
        for section in sections:
            if(section.type == 'movie' or section.type == 'show' or section.type == 'artist'):
                section_grid = SectionGrid()
                section_grid.set_title(section.title)
                section_grid.set_data(section)
                self._section_list.add(section_grid)
        self.show()

    def __process_servers(self, servers):
        self._server_store = Gtk.ListStore(object, str)

        for server in servers:
            self._server_store.append([server, server.name])

        self._server_box.clear()
        self._server_box.set_model(self._server_store)
        self._server_box.set_id_column(1)
        renderer_text = Gtk.CellRendererText()
        self._server_box.pack_start(renderer_text, True)
        self._server_box.add_attribute(renderer_text, "text", 1)
        self._server_box.set_active_id(server.name)

    def __on_section_clicked(self, listbox, listboxrow):
        if(listboxrow != None):
            child = listboxrow.get_child()
            if (child.get_data() != None):
                self.emit('section-clicked', listboxrow.get_child().get_data())
            else:
                if (child.get_title() == 'Home'):
                    self.emit('home-button-clicked')
                elif (child.get_title() == 'Playlists'):
                    self.emit('playlists-button-clicked')
                elif (child.get_title() == 'Player'):
                    self.emit('player-button-clicked')
