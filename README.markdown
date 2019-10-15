# Pieces Plugin
https://github.com/nicklan/Deluge-Pieces-Plugin

(c)2010 by Nick Lanham <nick@afternight.org>
Thanks to Jens Timmerman <jens.timmerman@gmail.com> for some of the
code to select multiple pieces
Thanks to Lex Leonard <lexman098@gmail.com> for some of the
code to enhance streaming of pieces

## Description

This plugin adds a tab that will show the status of each piece of the
torrent.

There are three states for each piece: 
not downloaded (black), downloaded (red), or currently downloading (blue). 
These are indicated by color.

The plugin works in "Classic" mode, client/server mode, and with the
webui.  However, in the webui piece priority setting and display are
not yet supported.

## Piece Priorities

If you are using the gtkui you can easily set the priority of a piece
or a set of pieces by selecting them, right-click and set the
priority.

You can select multiple pieces in a few ways:  

* Click the first piece you want to select.  Hold Shift and click the last piece you want to select.  All pieces in between will be selected.  
* Clicking and dragging over the pieces you want to select  
* Holding Ctrl will start selecting pieces without unselecting the ones you have already selected  


Underneath all the pieces is a checkbox that will allow you to always
prioritize the first un-downloaded pieces of the torrent. This lets you
start watching a movie while it is still downloading. 


To install this plugin in deluge: go to edit, preferences, plugins,
install plugin and select the .egg file.

# Version Info

## Version 0.6
* Added streaming of more than 1 piece (set to 15)

## Version 0.5
* Plugin works in client/server and "Classic" mode
* Webui support (just piece info, cannot set/view piece priorities
yet)
* Minor bug fixes

## Version 0.4
* Fix a nasty segfault bug from 0.3
* Easy select of multiple pieces using Shift/Ctrl
* Big speed improvement for torrents with lots of pieces
* Ability to always set first un-downloaded piece priority to high to
enable watching of movies before they are completely downloaded.

## Version 0.3
* Support multi-piece selection
* Don't use this version, it has a bug that will cause deluge (libtorrent) to segfault

## Version 0.3
* Finished/Seeding torrents now display correctly
* Tooltip to show which piece you are hovering over
* Ability to set priorities for individual pieces (via right click menu)
