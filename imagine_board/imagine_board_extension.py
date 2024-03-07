# Imagine Board is a Krita plugin to displays and organizes images.
# Copyright ( C ) 2022  Ricardo Jeremias.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# ( at your option ) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#region Import Modules

from krita import *
from PyQt5 import Qt, QtWidgets, QtCore, QtGui, QtSvg, uic
from PyQt5.Qt import Qt

#endregion


class ImagineBoard_Extension( Extension ):
    SIGNAL_BROWSE = QtCore.pyqtSignal( int )

    #region Initialize

    def __init__( self, parent ):
        super().__init__( parent )
    def setup( self ):
        pass

    #endregion
    #region Actions

    def createActions( self, window ):
        # Create Menu
        menu_imagine_board = QtWidgets.QMenu( "imagine_board_menu", window.qwindow() )
        action_imagine_board = window.createAction( "imagine_board_menu", "Imagine Board", "tools/scripts" )
        action_imagine_board.setMenu( menu_imagine_board )

        # Actions
        action_browse_minus = window.createAction( "imagine_board_extension_browse_minus", "Browse Minus", "tools/scripts/imagine_board_menu" )
        action_browse_minus.triggered.connect( self.Browse_Minus )

        action_browse_plus = window.createAction( "imagine_board_extension_browse_plus", "Browse Plus", "tools/scripts/imagine_board_menu" )
        action_browse_plus.triggered.connect( self.Browse_Plus )

    #endregion
    #region Functions

    def Browse_Minus( self ):
        self.SIGNAL_BROWSE.emit( -1 )
    def Browse_Plus( self ):
        self.SIGNAL_BROWSE.emit( +1 )

    #endregion
