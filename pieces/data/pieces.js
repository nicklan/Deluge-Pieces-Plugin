/*
Script: pieces.js
    The client-side javascript code for the Pieces plugin.

Copyright:
    (C) Nick Lanham 2009 <nick@afternight.org>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, write to:
        The Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor
        Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/

Ext.namespace('Deluge.pieces');
var dh = Ext.DomHelper;

Deluge.pieces.PiecesTab = Ext.extend(Ext.Panel, {
		title: _('Pieces'),

		constructor: function() {
			Deluge.pieces.PiecesTab.superclass.constructor.call(this);
			this.updateConfig();
			this.tdtpl = new Ext.Template('<td id="ptd{0}" title="Piece {0}" style="background-color:{1};" width="8" height="10"></td>');
			this.tdtpl.compile();
			this.trtpl = new Ext.Template('<tr id="{id}"></tr>');
			this.trtpl.compile();
			this.curTorrent = null;
			this.lastDone = false;
			this.tableBox = this.add({
					xtype: 'box',
					autoEl: {
						tag: 'table',
						id: 'pieces_table',
						style: 'table-layout: fixed',
						cellspacing: 2
					}
				});
			this.needRebuild = true;
		},
		
		updateConfig: function() {
			deluge.client.pieces.get_config({
					success: function(config) {
						var ctmp = config['dling_color'].split("");
						this.dlingColor = "#"+ctmp[1]+ctmp[2]+ctmp[5]+ctmp[6]+ctmp[9]+ctmp[10];
						ctmp = config['dled_color'].split("");
						this.dledColor = "#"+ctmp[1]+ctmp[2]+ctmp[5]+ctmp[6]+ctmp[9]+ctmp[10];
						ctmp = config['not_dled_color'].split("");
						this.notDledColor = "#"+ctmp[1]+ctmp[2]+ctmp[5]+ctmp[6]+ctmp[9]+ctmp[10];
					},
					scope: this
				});
		},


		buildTable: function(numPieces, done, pieces, curdl) {
			var w = this.getWidth();
			var nc = Math.ceil(w/12);
			var nr = Math.ceil(numPieces/nc);
			var pid = 0;
			var cdi = 0;
			if (done || cdi >= curdl.length)
				cdi = -1;
			this.clear();
			for (i = 0;i < nr;i++) {
				var rid = "pr"+i;
				this.trtpl.append('pieces_table',{id:rid});
				for (j = 0;j < nc;j++) {
					if (cdi != -1 && curdl[cdi] == pid) {
						cdi++;
						if (cdi >= curdl.length)
							cdi = -1;
						this.tdtpl.append(rid,[pid,this.dlingColor]);
					}
					else if (done)
						this.tdtpl.append(rid,[pid,this.dledColor]);
					else
						this.tdtpl.append(rid,[pid,pieces[pid]?this.dledColor:this.notDledColor]);

					pid++;
					if (pid >= numPieces)
						break;
				}
				if (pid >= numPieces)
					break;
			}
		},

		updateTable: function(numPieces, done, pieces, curdl) {
			var cdi = 0;
			if (done || cdi >= curdl.length)
				cdi = -1;
			for (pid = 0;pid < numPieces;pid++) {
				var td = Ext.DomQuery.selectNode("td[id=ptd"+pid+"]");
				if (cdi != -1 && curdl[cdi] == pid) {
					cdi++;
					if (cdi >= curdl.length)
						cdi = -1;
					td.style.backgroundColor = this.dlingColor;
				}
				else if (pieces[pid])
					td.style.backgroundColor = this.dledColor;
				else
					td.style.backgroundColor = this.notDledColor;
			}
		},

		onTorrentInfo: function(info) {
			if (this.needRebuild) {
				this.buildTable(info[1],info[0],info[2],info[3]);
				this.needRebuild = false;
				this.lastDone = info[0];
			} else {
				if (!this.lastDone)
					this.updateTable(info[1],info[0],info[2],info[3]);
				this.lastDone = info[0];
			}
		},

		clear: function() {
			if (!this.tblnode)
				this.tblnode = Ext.DomQuery.selectNode("table[id=pieces_table]");
			if (this.tblnode)
				this.tblnode.innerHTML = "";
			this.needRebuild = true;
		},

		update: function(torrentId) {
			if (torrentId != this.curTorrent) {
				this.needRebuild = true;
				this.curTorrent = torrentId;
			}
			deluge.client.pieces.get_torrent_info(torrentId, {
					success: this.onTorrentInfo,
					scope: this,
					torrentId: torrentId
				});
		}
		
});

Deluge.pieces.PiecesPlugin = Ext.extend(Deluge.Plugin, {
		name:"Pieces",

		onDisable: function() {

		},

		onEnable: function() {
			deluge.details.add(new Deluge.pieces.PiecesTab());
		}

});
Deluge.registerPlugin('Pieces',Deluge.pieces.PiecesPlugin);
