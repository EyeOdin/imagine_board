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


#region Imports

# Python Modules
import inspect
import sys
import copy
import math
import random
import os
import time
import stat
import webbrowser
import zipfile
import pathlib
import re
import shutil
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Plugin Modules
from .imagine_board_constants import *
from .imagine_board_calculations import *
from .imagine_board_extension import ImagineBoard_Extension
from .imagine_board_modulo import (
    ImagineBoard_Preview,
    ImagineBoard_Grid,
    ImagineBoard_Reference,
    List_Data,
    Drive_TreeView,
    )

#endregion


class ImagineBoard_Docker( DockWidget ):
    """
    Display and Organize Images
    """

    #region Initialize

    def __init__( self ):
        super( ImagineBoard_Docker, self ).__init__()

        # Construct
        self.User_Interface()
        self.Variables()
        self.Connections()
        self.Modules()
        self.Style()
        self.Extension()
        self.Kritarc_Load()
        self.Plugin_Setup()

    def User_Interface( self ):
        # Window
        self.setWindowTitle( DOCKER_NAME  )
        # Path Name
        self.directory_plugin = str( os.path.dirname( os.path.realpath( __file__ ) ) )
        docker_url = os.path.join( self.directory_plugin, "imagine_board_docker.ui" )
        dialog_url = os.path.join( self.directory_plugin, "imagine_board_settings.ui" )
        # Widget Docker
        self.layout = uic.loadUi( docker_url, QWidget( self ) )
        self.setWidget( self.layout )
        # Settings
        self.dialog = uic.loadUi( dialog_url, QDialog( self ) )
        self.dialog.setWindowTitle( f"{ DOCKER_NAME } : Settings" )
    def Variables( self ):
        # Pykrita
        self.imagine_pyid = "pykrita_imagine_board_docker"

        # Paths
        self.directory_code = os.path.join( self.directory_plugin, "CODE" )

        # State
        self.state_load = False
        self.state_maximized = False
        self.state_inside = False
        self.state_transparent = False
        self.state_cycle = False

        # UI
        self.mode_index = 0
        self.extra_control = False
        # Search
        self.search_string = str()
        self.search_input = str()
        self.search_index = 0
        self.search_key = list()

        # Menu
        self.press_time = 500 # 1000=1sec
        self.menu_hold = None

        # Items
        self.sync_list = "Directory" # "Directory" "Recent Documents" "Reference"
        self.sync_type = "Normal" # "Normal" "Backup~"
        self.sync_sort = "Name"
        self.directory_show = False
        self.directory_recursive = False
        self.sort_reverse = False
        # Folder
        self.folder_url = str()
        self.folder_shift = list()
        # Lists
        self.list_url = list()
        self.list_krita = list()
        self.list_reference = list()
        # Files
        self.file_found = False
        self.file_extension = file_normal
        self.file_sort = QDir.Name

        # Preview
        self.preview_state = None # None "FILE" "IMG" "ANIM" "PDF" "COMP" "DIR" "WEB"
        self.preview_index = 0
        self.preview_name = str()
        self.preview_max = 0
        self.preview_playpause = True  # True=Play  False=Pause
        # Preview Slidshow
        self.preview_slideshow_sequence = "Linear" # "Linear" "Random"
        self.preview_slideshow_rate = 1000 # 1000ms = 1second
        self.preview_slideshow_list = list()
        self.preview_slideshow_index = 0
        # Preview Overlay
        self.preview_gridline_x = 3
        self.preview_gridline_y = 3
        self.preview_gridline_state = False
        self.preview_underlayer_color = "#7f7f7f"
        self.preview_underlayer_state = False
        # Preview Controller
        self.preview_pc_value = 0
        self.preview_pc_max = 0

        # Grid
        self.grid_thumb = 200
        self.grid_clean = 0 # image units
        self.grid_precache = 200 # Mb
        # Bookmark
        self.bookmark_list = list()

        # Reference Board
        self.ref_lock = False
        self.ref_camera_position = [ 1, 1 ]
        self.ref_camera_zoom = 1
        self.ref_hex_pen = "#ffffff"
        self.ref_hex_bg = "#000000"
        # Reference Dialog
        self.ref_import_size = False
        self.ref_rebase_recursive = False # Rebase recursive search

        # Timers
        self.qtimer_watcher = QtCore.QTimer( self )
        self.qtimer_reference = QtCore.QTimer( self )
        self.SlideShow_Timer()
        # Threads
        self.cycle_qthread = QtCore.QThread()
        self.qthread_keyenter = QtCore.QThread()
        self.qthread_reorder = QtCore.QThread()

        # Keyenter
        self.keyenter_mode = "NONE" # "KEY_ADD" "KEY_REMOVE" "KEY_REPLACE" "KEY_CLEAN"
        self.keyenter_list_key = list()
        self.keyenter_list_url = list()
        # Reorder
        self.reorder_mode = "FILE_RENAME" # "FILE_RENAME" "COMPRESSED_RENAME" "WEB_DOWNLOAD"
        self.reorder_string = "image"
        self.reorder_number = 0
        self.reorder_source_url = str()
        self.reorder_destination_url = str()
        self.reorder_zip_url = None
        self.reorder_list_url = list()

        # Drive
        self.drive_url = str() # No input for the root is my input
        self.drive_model = None
        self.drive_tree_view = None
        self.drive_sort = QDir.LocaleAware

        # System
        self.sow_imagine = False
        self.sow_dockers = False
        self.sys_transparent = False
        self.sys_insert_original_size = False
        self.sys_pixelart = False

        # Color Picker Module
        self.pigmento_picker = None
        self.pigmento_sampler = None
        self.pigmento_picker_pyid = "pykrita_pigment_o_picker_docker"
        self.pigmento_sampler_pyid = "pykrita_pigment_o_sampler_docker"
        # Colors
        self.color_white = "#ffffff"
        self.color_black = "#000000"
    def Connections( self ):
        #region Layout

        # Preview Control
        self.layout.pc_slider.valueChanged.connect( self.Preview_Slider )
        self.layout.pc_back.clicked.connect( self.Preview_Back )
        self.layout.pc_playpause.toggled.connect( self.Preview_PlayPause )
        self.layout.pc_forward.clicked.connect( self.Preview_Forward )
        self.layout.pc_slideshow.toggled.connect( self.Preview_SlideShow )
        # Grid Control
        self.layout.bookmark_open.pressed.connect( self.Hold_Bookmark )
        self.layout.bookmark_open.released.connect( self.Release_Bookmark )
        # Reference Control
        self.layout.label_text.clicked.connect( self.Label_Text )
        self.layout.label_font.currentTextChanged.connect( self.Label_Font )
        self.layout.label_letter.valueChanged.connect( self.Label_Letter )
        self.layout.label_pen.clicked.connect( self.Label_Pen )
        self.layout.label_bg.clicked.connect( self.Label_BG )
        # Layout
        self.layout.index_slider.valueChanged.connect( self.Index_Slider )
        self.layout.index_slider.sliderPressed.connect( lambda: self.Slider_Press( True ) )
        self.layout.index_slider.sliderReleased.connect( lambda: self.Slider_Press( False ) )
        self.layout.folder.pressed.connect( self.Hold_Folder )
        self.layout.folder.released.connect( self.Release_Folder )
        self.layout.lock.toggled.connect( self.Reference_Lock )
        self.layout.colorpicker.toggled.connect( self.ColorPicker )
        self.layout.control.toggled.connect( self.Extra_Control )
        self.layout.search.textChanged.connect( self.Search_Completer )
        self.layout.search.returnPressed.connect( self.Filter_Search )
        self.layout.index_number.valueChanged.connect( self.Index_Number )
        self.layout.settings.clicked.connect( self.Menu_Settings )

        #endregion
        #region Display

        # Drive
        self.dialog.sync_list.currentTextChanged.connect( self.Sync_List )
        self.dialog.sync_type.currentTextChanged.connect( self.Sync_Type )
        self.dialog.sync_sort.currentTextChanged.connect( self.Sync_Sort )
        self.dialog.directory_show.toggled.connect( self.Folder_Show )
        self.dialog.directory_recursive.toggled.connect( self.Folder_Recursive )
        self.dialog.sort_reverse.toggled.connect( self.Sort_Reverse )
        # Preview
        self.dialog.preview_slideshow_sequence.currentTextChanged.connect( self.SlideShow_Sequence )
        self.dialog.preview_slideshow_rate.timeChanged.connect( self.SlideShow_Rate )
        self.dialog.preview_gridline_x.valueChanged.connect( self.Gridline_X )
        self.dialog.preview_gridline_y.valueChanged.connect( self.Gridline_Y )
        self.dialog.preview_gridline_state.toggled.connect( self.Gridline_State )
        self.dialog.preview_underlayer_color.clicked.connect( self.Underlayer_Color_Dialog )
        self.dialog.preview_underlayer_state.toggled.connect( self.Underlayer_State )
        # Grid
        self.dialog.grid_thumb.valueChanged.connect( self.Grid_Thumbnail )
        self.dialog.grid_clean.valueChanged.connect( self.Grid_Clean )
        self.dialog.grid_precache.valueChanged.connect( self.Grid_Precache )
        # Reference
        self.dialog.ref_import_size.toggled.connect( self.Reference_Import_Size )
        self.dialog.ref_rebase_recursive.toggled.connect( self.Reference_Rebase_Recursive )

        #endregion
        #region KeyEnter

        # String
        self.dialog.keyenter_string.returnPressed.connect( self.Keyenter_String )
        self.dialog.keyenter_mode.currentTextChanged.connect( self.Keyenter_Operation )
        self.dialog.keyenter_run.clicked.connect( self.Keyenter_Run )

        # List Image
        self.Keyenter_WidgetList()
        self.keyenter_widget_url.LIST_URL.connect( self.Keyenter_Url_Add )
        self.keyenter_widget_url.LIST_FILES.connect( self.Keyenter_Url_Folder )
        self.keyenter_widget_url.LIST_REMOVE.connect( self.Keyenter_Url_Remove )
        self.keyenter_widget_url.LIST_CLEAR.connect( self.Keyenter_Url_Clear )

        #endregion
        #region Reorder

        # Input
        self.dialog.reorder_mode.currentTextChanged.connect( self.Reorder_Mode )
        self.dialog.reorder_string.clicked.connect( self.Reorder_String )
        self.dialog.reorder_number.clicked.connect( self.Reorder_Number )
        self.dialog.reorder_source_url.textChanged.connect( self.Reorder_Source_Url )
        self.dialog.reorder_source_dialog.clicked.connect( self.Reorder_Source_Dialog )
        self.dialog.reorder_destination_url.textChanged.connect( self.Reorder_Destination_Url )
        self.dialog.reorder_destination_dialog.clicked.connect( self.Reorder_Destination_Dialog )
        # List
        self.Reorder_WidgetList()
        self.reorder_widget_url.LIST_URL.connect( self.Reorder_Url_Add )
        self.reorder_widget_url.LIST_FILES.connect( self.Reorder_Url_Files )
        self.reorder_widget_url.LIST_REMOVE.connect( self.Reorder_Url_Remove )
        self.reorder_widget_url.LIST_CLEAR.connect( self.Reorder_Url_Clear )
        # Sort
        self.dialog.reorder_sort_name.clicked.connect( self.Reorder_Sort_Name )
        self.dialog.reorder_sort_time.clicked.connect( self.Reorder_Sort_Time )
        self.dialog.reorder_sort_reverse.clicked.connect( self.Reorder_Sort_Reverse )
        self.dialog.reorder_run.clicked.connect( self.Reorder_Run )

        #endregion
        #region Drive

        self.Drive_Widget()
        self.drive_tree_view.clicked.connect( self.Drive_Click )

        #endregion
        #region System

        # Dialog System Options
        self.dialog.sow_imagine.toggled.connect( self.ShowOnWelcome_Imagine )
        self.dialog.sow_dockers.toggled.connect( self.ShowOnWelcome_Dockers )
        self.dialog.sys_transparent.toggled.connect( self.Transparent_Docker )
        self.dialog.sys_insert_original_size.toggled.connect( self.Insert_Original_Size )
        self.dialog.sys_pixelart.toggled.connect( self.Display_Pixelated )

        # Notices
        self.dialog.manual.clicked.connect( self.Menu_Manual )
        self.dialog.license.clicked.connect( self.Menu_License )

        #endregion
        #region Filters

        # Event Layout
        self.layout.preview_view.installEventFilter( self )
        self.layout.grid_view.installEventFilter( self )
        self.layout.reference_view.installEventFilter( self )
        self.layout.footer.installEventFilter( self )
        self.layout.mode.installEventFilter( self )
        self.layout.search.installEventFilter( self )
        self.layout.settings.installEventFilter( self ) # Photoshoot
        # Event Dialog
        self.dialog.keyenter_widget_key.installEventFilter( self )

        #endregion
    def Modules( self ):
        #region System

        # File Watcher
        self.file_system_watcher = QFileSystemWatcher( self )
        self.file_system_watcher.directoryChanged.connect( self.Watcher_Display )

        #endregion
        #region Notifier

        self.notifier = Krita.instance().notifier()
        self.notifier.windowCreated.connect( self.Window_Created )

        #endregion
        #region Preview

        self.panel_preview = ImagineBoard_Preview( self.layout.preview_view )
        # General
        self.panel_preview.PREVIEW_PARENT.connect( self.Folder_Parent )
        self.panel_preview.PREVIEW_LOAD.connect( self.Folder_Load )
        self.panel_preview.PREVIEW_MODE.connect( self.Mode_Index )
        self.panel_preview.PREVIEW_DROP.connect( self.Drop_Inside )
        self.panel_preview.PREVIEW_INCREMENT.connect( self.Preview_Increment )
        # Menu
        self.panel_preview.PREVIEW_PIN_INSERT.connect( self.Pin_Insert )
        self.panel_preview.PREVIEW_RANDOM.connect( self.Preview_Random )
        self.panel_preview.PREVIEW_FULL_SCREEN.connect( self.Screen_Maximized )
        # Preview Control UI
        self.panel_preview.PREVIEW_PC_VALUE.connect( self.PreviewControl_Slider_Value )
        self.panel_preview.PREVIEW_PC_MAX.connect( self.PreviewControl_Slider_Maximum )
        self.panel_preview.PREVIEW_PB_VALUE.connect( self.ProgressBar_Value )
        self.panel_preview.PREVIEW_PB_MAX.connect( self.ProgressBar_Maximum )

        #endregion
        #region Grid

        self.panel_grid = ImagineBoard_Grid( self.layout.grid_view )
        # General
        self.panel_grid.GRID_PARENT.connect( self.Folder_Parent )
        self.panel_grid.GRID_LOAD.connect( self.Folder_Load )
        self.panel_grid.GRID_MODE.connect( self.Mode_Index )
        self.panel_grid.GRID_DROP.connect( self.Drop_Inside )
        self.panel_grid.GRID_INDEX.connect( self.Display_Number )
        # Menu
        self.panel_grid.GRID_PIN_INSERT.connect( self.Pin_Insert )
        self.panel_grid.GRID_CYCLE.connect( self.Cycle_Process )
        self.panel_grid.GRID_FULL_SCREEN.connect( self.Screen_Maximized )
        # UI
        self.panel_grid.GRID_PB_VALUE.connect( self.ProgressBar_Value )
        self.panel_grid.GRID_PB_MAX.connect( self.ProgressBar_Maximum )

        #endregion
        #region Reference

        self.panel_reference = ImagineBoard_Reference( self.layout.reference_view )
        # General
        self.panel_reference.REFERENCE_DROP.connect( self.Drop_Inside )
        # Menu
        self.panel_reference.REFERENCE_PIN_INSERT.connect( self.Pin_Insert )
        self.panel_reference.REFERENCE_FULL_SCREEN.connect( self.Screen_Maximized )
        # UI
        self.panel_reference.REFERENCE_PB_VALUE.connect( self.ProgressBar_Value )
        self.panel_reference.REFERENCE_PB_MAX.connect( self.ProgressBar_Maximum )
        self.panel_reference.REFERENCE_LABEL.connect( self.Reference_Label )
        self.panel_reference.REFERENCE_CAMERA.connect( self.Reference_Camera_Display )
        self.panel_reference.REFERENCE_PACKER.connect( self.Lock_State )

        #endregion
    def Style( self ):
        self.Style_Icon()
        self.Style_Tooltip()
        self.Style_Theme()
    def Extension( self ):
        # Install Extension for Docker
        extension = ImagineBoard_Extension( parent = Krita.instance() )
        Krita.instance().addExtension( extension )
        # Connect Extension Signals
        extension.SIGNAL_BROWSE.connect( self.Shortcut_Browse )
        extension.SIGNAL_FRAME.connect( self.Shortcut_Frame )
    def Kritarc_Load( self ):
        # Layout
        self.mode_index                     = Kritarc_Read( DOCKER_NAME, "mode_index", self.mode_index, int )
        self.preview_index                  = Kritarc_Read( DOCKER_NAME, "preview_index", self.preview_index, int )
        self.folder_url                     = Kritarc_Read( DOCKER_NAME, "folder_url", self.folder_url, str )
        self.ref_lock                       = Kritarc_Read( DOCKER_NAME, "ref_lock", self.ref_lock, eval )
        self.search_string                  = Kritarc_Read( DOCKER_NAME, "search", self.search_string, str )
        self.bookmark_list                  = Kritarc_Read( DOCKER_NAME, "bookmark_list", self.bookmark_list, eval )

        # Dialog Drive
        self.sync_list                      = Kritarc_Read( DOCKER_NAME, "sync_list", self.sync_list, str )
        self.sync_type                      = Kritarc_Read( DOCKER_NAME, "sync_type", self.sync_type, str )
        self.sync_sort                      = Kritarc_Read( DOCKER_NAME, "sync_sort", self.sync_sort, str )
        self.directory_show                 = Kritarc_Read( DOCKER_NAME, "directory_show", self.directory_show, eval )
        self.directory_recursive            = Kritarc_Read( DOCKER_NAME, "directory_recursive", self.directory_recursive, eval )
        self.sort_reverse                   = Kritarc_Read( DOCKER_NAME, "sort_reverse", self.sort_reverse, eval )
        # Dialog Preview
        self.preview_slideshow_sequence     = Kritarc_Read( DOCKER_NAME, "preview_slideshow_sequence", self.preview_slideshow_sequence, str )
        self.preview_slideshow_rate         = Kritarc_Read( DOCKER_NAME, "preview_slideshow_rate", self.preview_slideshow_rate, int )
        self.preview_gridline_x             = Kritarc_Read( DOCKER_NAME, "preview_gridline_x", self.preview_gridline_x, int )
        self.preview_gridline_y             = Kritarc_Read( DOCKER_NAME, "preview_gridline_y", self.preview_gridline_y, int )
        self.preview_gridline_state         = Kritarc_Read( DOCKER_NAME, "preview_gridline_state", self.preview_gridline_state, eval )
        self.preview_underlayer_color       = Kritarc_Read( DOCKER_NAME, "preview_underlayer_color", self.preview_underlayer_color, str )
        self.preview_underlayer_state       = Kritarc_Read( DOCKER_NAME, "preview_underlayer_state", self.preview_underlayer_state, eval )
        # Dialog Grid
        self.grid_thumb                     = Kritarc_Read( DOCKER_NAME, "grid_thumb", self.grid_thumb, int )
        self.grid_clean                     = Kritarc_Read( DOCKER_NAME, "grid_clean", self.grid_clean, int )
        self.grid_precache                  = Kritarc_Read( DOCKER_NAME, "grid_precache", self.grid_precache, int )
        # Dialog Reference
        self.ref_import_size                = Kritarc_Read( DOCKER_NAME, "ref_import_size", self.ref_import_size, eval )
        self.ref_rebase_recursive           = Kritarc_Read( DOCKER_NAME, "ref_rebase_recursive", self.ref_rebase_recursive, eval )

        # Keyenter
        self.keyenter_list_key              = Kritarc_Read( DOCKER_NAME, "keyenter_list_key", self.keyenter_list_key, eval )

        # Reorder
        self.reorder_mode                   = Kritarc_Read( DOCKER_NAME, "reorder_mode", self.reorder_mode, str )
        self.reorder_string                 = Kritarc_Read( DOCKER_NAME, "reorder_string", self.reorder_string, str )
        self.reorder_number                 = Kritarc_Read( DOCKER_NAME, "reorder_number", self.reorder_number, int )
        self.reorder_source_url             = Kritarc_Read( DOCKER_NAME, "reorder_source_url", self.reorder_source_url, str )
        self.reorder_destination_url        = Kritarc_Read( DOCKER_NAME, "reorder_destination_url", self.reorder_destination_url, str )

        # Dialog System
        self.sow_imagine                    = Kritarc_Read( DOCKER_NAME, "sow_imagine", self.sow_imagine, eval )
        self.sow_dockers                    = Kritarc_Read( DOCKER_NAME, "sow_dockers", self.sow_dockers, eval )
        self.sys_transparent                = Kritarc_Read( DOCKER_NAME, "sys_transparent", self.sys_transparent, eval )
        self.sys_insert_original_size       = Kritarc_Read( DOCKER_NAME, "sys_insert_original_size", self.sys_insert_original_size, eval )
        self.sys_pixelart                   = Kritarc_Read( DOCKER_NAME, "sys_pixelart", self.sys_pixelart, eval )
    def Plugin_Setup( self ):
        try:
            self.Settings()
        except Exception as e:
            Message_Warnning( "ERROR", f"\n{ e }" )
            self.Variables()
            self.Settings()
    def Settings( self ):
        #region Dialog Display

        # Item
        self.dialog.sync_list.setCurrentText( self.sync_list )
        self.dialog.sync_type.setCurrentText( self.sync_type )
        self.dialog.sync_sort.setCurrentText( self.sync_sort )
        self.dialog.directory_show.setChecked( self.directory_show )
        self.dialog.directory_recursive.setChecked( self.directory_recursive )
        self.dialog.sort_reverse.setChecked( self.sort_reverse )

        # Preview
        self.dialog.preview_slideshow_sequence.setCurrentText( self.preview_slideshow_sequence )
        time = QTime( 0,0,0 ).addMSecs( self.preview_slideshow_rate )
        self.dialog.preview_slideshow_rate.setTime( time )
        self.dialog.preview_gridline_x.setValue( self.preview_gridline_x )
        self.dialog.preview_gridline_y.setValue( self.preview_gridline_y )
        self.dialog.preview_gridline_state.setChecked( self.preview_gridline_state )
        self.Display_Underlayer_Color( self.preview_underlayer_color )
        self.dialog.preview_underlayer_state.setChecked( self.preview_underlayer_state )
        # Grid
        self.dialog.grid_thumb.setValue( self.grid_thumb )
        self.dialog.grid_clean.setValue( self.grid_clean )
        self.dialog.grid_precache.setValue( self.grid_precache )
        # Reference
        self.dialog.ref_import_size.setChecked( self.ref_import_size )
        self.dialog.ref_rebase_recursive.setChecked( self.ref_rebase_recursive )

        # Preview Control Boot
        self.Extra_Control( False )

        #endregion
        #region Keyenter

        self.Keyenter_Key_Load( self.keyenter_list_key )

        #endregion
        #region Reorder

        self.dialog.reorder_mode.setCurrentText( self.reorder_mode )
        self.dialog.reorder_string.setText( self.reorder_string )
        self.dialog.reorder_number.setText( str( self.reorder_number ).zfill( zf ) )
        self.dialog.reorder_source_url.setText( self.reorder_source_url )
        self.dialog.reorder_destination_url.setText( self.reorder_destination_url )

        #endregion
        #region Dialog System

        self.dialog.sow_imagine.setChecked( self.sow_imagine )
        self.dialog.sow_dockers.setChecked( self.sow_dockers )
        self.dialog.sys_transparent.setChecked( self.sys_transparent )
        self.dialog.sys_insert_original_size.setChecked( self.sys_insert_original_size )
        self.dialog.sys_pixelart.setChecked( self.sys_pixelart )

        #endregion
        #region Layout

        # Index
        self.Mode_Index( self.mode_index, True )
        self.Folder_Load( self.folder_url, None, self.preview_index )
        # Icons
        self.layout.lock.setChecked( self.ref_lock )
        self.layout.search.setText( self.search_string )
        # Bookmark
        self.Bookmark_ComboBox( self.bookmark_list )

        #endregion

    #endregion
    #region Interface Layout

    # User Interface
    def Mode_Index( self, index, update ):
        # States
        if index == 0:
            self.layout.mode.setIcon( self.qicon_preview )
            self.layout.stackedwidget_panel.setCurrentIndex( 0 )
            self.Footer_Widgets( slider=True, folder=True, drive=True )
        if index == 1:
            self.layout.mode.setIcon( self.qicon_grid )
            self.layout.stackedwidget_panel.setCurrentIndex( 1 )
            self.Footer_Widgets( slider=True, folder=True, drive=True )
            self.layout.pc_slideshow.setChecked( False )
        if index == 2:
            self.layout.mode.setIcon( self.qicon_reference )
            self.layout.stackedwidget_panel.setCurrentIndex( 2 )
            self.Footer_Widgets( slider=False, lock=True, label=True )
            self.layout.pc_slideshow.setChecked( False )
        # update cycle
        if self.mode_index != index or update == True:
            self.mode_index = index
            self.Size_Update()
            self.Display_Update( False )
            self.Theme_Changed()
            self.PreviewControl_Control( self.preview_state )
            self.Style_PreviewControl( self.preview_state )
        # Save
        Kritarc_Write( DOCKER_NAME, "mode_index", self.mode_index )
    def Mode_Press( self, event ):
        # Menu
        qmenu = QMenu( self )
        # Actions
        action_preview = qmenu.addAction( "Preview" )
        action_grid = qmenu.addAction( "Grid" )
        action_reference = qmenu.addAction( "Reference" )
        # Icons
        action_preview.setIcon( self.qicon_preview )
        action_grid.setIcon( self.qicon_grid )
        action_reference.setIcon( self.qicon_reference )

        # Execute
        geo = self.layout.mode.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.footer.mapToGlobal( qpoint )
        action = qmenu.exec_( position )
        # Triggers
        if action == action_preview:
            self.Mode_Index( 0, False )
        if action == action_grid:
            self.Mode_Index( 1, False )
        if action == action_reference:
            self.Mode_Index( 2, False )
    def Mode_Wheel( self, event ):
        increment = 0
        value = 20
        delta = event.angleDelta()
        delta_y = delta.y()
        if delta_y > +value: increment = -1
        if delta_y < -value: increment = +1
        if increment in [ -1, +1 ]:
            new_index = Limit_Range( self.mode_index + increment, 0, 2 )
            if self.mode_index != new_index:
                self.Mode_Index( new_index, False )
    def Footer_Widgets( self, slider=False, folder=False, lock=False, drive=False, label=False ):
        # Top
        self.layout.index_slider.setEnabled( slider )
        # Icons
        self.layout.folder.setMinimumWidth( int( folder * 20 ) )
        self.layout.folder.setMaximumWidth( int( folder * 20 ) )
        self.layout.lock.setMinimumWidth( int( lock * 20 ) )
        self.layout.lock.setMaximumWidth( int( lock * 20 ) )
        # Middle
        self.layout.option_drive.setMaximumWidth( int( drive * qt_max ) )
        self.layout.option_reference.setMaximumWidth( int( label * qt_max ) )
        # Layout
        self.layout.option_drive_layout.setSpacing( int( drive * 5 ) )
        self.layout.option_reference_layout.setSpacing( int( label * 5 ) )
    def Screen_Maximized( self, boolean ):
        if boolean == True:
            # Full Screen
            self.setFloating( True )
            self.showMaximized()
        else:
            # Place it on the Docker
            self.setFloating( False )
            self.showNormal()
            # Raise Docker to be Visable
            plugin = "pykrita_imagine_board_docker"
            dockers = Krita.instance().dockers()
            for i in range( 0, len( dockers ) ):
                item = dockers[i]
                if item.objectName() == plugin:
                    item.raise_()
                    break
        # Update
        self.Size_Update()
    # Icon
    def ColorPicker( self, boolean ):
        # Variables
        self.colorpicker = boolean
        # Panels
        self.panel_preview.Set_ColorPicker( self.colorpicker )
        self.panel_grid.Set_ColorPicker( self.colorpicker )
        self.panel_reference.Set_ColorPicker( self.colorpicker )
        # Style
        if boolean == True:
            self.layout.colorpicker.setIcon( self.qicon_colorpicker_on )
        else:
            self.layout.colorpicker.setIcon( self.qicon_colorpicker_off )
    def Extra_Control( self, boolean ):
        # Variables
        self.extra_control = boolean
        if boolean == True:
            self.layout.control.setIcon( self.qicon_control_down )
        if boolean == False:
            self.layout.control.setIcon( self.qicon_control_up )
        # Widgets
        self.layout.preview_control.setMaximumHeight( int( boolean * qt_max ) )
        self.layout.grid_control.setMaximumHeight( int( boolean * qt_max ) )
        self.layout.reference_control.setMaximumHeight( int( boolean * qt_max ) )

    # Progress Bar
    def ProgressBar_Value( self, value ):
        self.layout.progress_bar.setValue( value )
    def ProgressBar_Maximum( self, value ):
        self.layout.progress_bar.setMaximum( value )
    def ProgressBar_Reset( self ):
        self.layout.progress_bar.setValue( 0 )
        self.layout.progress_bar.setMaximum( 1 )
    # Slider
    def Slider_Press( self, boolean ):
        if self.mode_index == 0:pass
        if self.mode_index == 1:self.panel_grid.Set_Press( boolean )
    # Search
    def Search_Label( self, string ):
        self.layout.search.setPlaceholderText( string )

    # Menu
    def Menu_Settings( self ):
        # Display
        self.dialog.show()
        # Resize Geometry
        qmw = Krita.instance().activeWindow().qwindow()
        px = qmw.x()
        py = qmw.y()
        w2 = qmw.width() * 0.5
        h2 = qmw.height() * 0.5
        size = 500
        self.dialog.setGeometry( int( px + w2 - size * 0.5 ), int( py + h2 - size * 0.5 ), int( size ), int( size ) )

    # Widgets Updates
    def Clear_Focus( self ):
        self.layout.label_font.clearFocus()
        self.layout.label_letter.clearFocus()
        self.layout.search.clearFocus()
        self.layout.index_number.clearFocus()
    def Widget_Enable( self, boolean ):
        self.layout.setEnabled( boolean )

    # Size
    def Size_Print( self ):
        width = self.width()
        height = self.height()
        Message_Log( "SIZE", f"{ width } x { height }" )
    def Size_Standard( self ):
        if self.isFloating() == True:
            self.resize( QSize( 500, 500 ) )
            self.Size_Update()
    def Size_Update( self ):
        # Variables
        self.state_maximized = self.isMaximized()
        # Modules
        if self.mode_index == 0:
            ps = self.layout.preview_view.size()
            self.panel_preview.Set_Size( ps.width(), ps.height(), self.state_maximized )
        if self.mode_index == 1:
            gs = self.layout.grid_view.size()
            self.panel_grid.Set_Size( gs.width(), gs.height(), self.state_maximized, self.grid_thumb, self.extra_control )
        if self.mode_index == 2:
            rs = self.layout.reference_view.size()
            self.panel_reference.Set_Size( rs.width(), rs.height(), self.state_maximized )

    # Style
    def Style_Icon( self ):
        # Variables
        ki = Krita.instance()
        # Icons
        self.qicon_anim_play = ki.icon( "animation_play" )
        self.qicon_anim_pause = ki.icon( "animation_pause" )
        self.qicon_slideshow_play = ki.icon( "media-playback-start" )
        self.qicon_slideshow_stop = ki.icon( "media-playback-stop" )
        self.qicon_preview = ki.icon( "folder-pictures" )
        self.qicon_grid = ki.icon( "gridbrush" )
        self.qicon_reference = ki.icon( "zoom-fit" )
        self.qicon_folder_on = ki.icon( "document-open" )
        self.qicon_folder_off = ki.icon( "tool_zoom" )
        self.qicon_colorpicker_on = ki.icon( "pivot-point" )
        self.qicon_colorpicker_off = ki.icon( "krita_tool_color_sampler" )
        self.qicon_stop_idle = ki.icon( "showColoringOff" )
        self.qicon_stop_abort = ki.icon( "snapshot-load" )
        self.qicon_control_up = ki.icon( "arrowup" )
        self.qicon_control_down = ki.icon( "arrowdown" )
        self.qicon_lock_true = ki.icon( "layer-locked" )
        self.qicon_lock_false_1 = ki.icon( "layer-unlocked" )
        self.qicon_lock_false_2 = ki.icon( "media-record" )
        self.qicon_lock_false = self.qicon_lock_false_1

        # Preview Control
        self.layout.pc_back.setIcon( ki.icon( "prevframe" ) )
        self.layout.pc_playpause.setIcon( self.qicon_anim_pause )
        self.layout.pc_forward.setIcon( ki.icon( "nextframe" ) )
        self.layout.pc_slideshow.setIcon( self.qicon_slideshow_play )
        # Grid Control
        self.layout.bookmark_open.setIcon( ki.icon( "bookmarks" ) )
        # Reference Control
        self.layout.label_text.setIcon( ki.icon( "draw-text" ) )
        # Layout
        self.layout.folder.setIcon( self.qicon_folder_on )
        self.layout.lock.setIcon( self.qicon_lock_false_1 )
        self.layout.colorpicker.setIcon( self.qicon_colorpicker_off )
        self.layout.control.setIcon( self.qicon_control_up )
        self.layout.settings.setIcon( ki.icon( "settings-button" ) )
        # Dialog
        self.dialog.reorder_run.setIcon( ki.icon( "arrow-right" ) )
        self.dialog.reorder_source_dialog.setIcon( self.qicon_folder_on )
        self.dialog.reorder_destination_dialog.setIcon( self.qicon_folder_on )
    def Style_Tooltip( self ):
        # ToolTips Preview Control
        self.layout.pc_back.setToolTip( "Frame Backward" )
        self.layout.pc_playpause.setToolTip( "Frame Play/Pause" )
        self.layout.pc_forward.setToolTip( "Frame Forward" )
        self.layout.pc_slideshow.setToolTip( "File SlideShow" )
        # ToolTips Reference Control
        self.layout.label_text.setToolTip( "Text" )
        self.layout.label_font.setToolTip( "Font" )
        self.layout.label_letter.setToolTip( "Letter" )
        self.layout.label_pen.setToolTip( str( self.ref_hex_pen ) )
        self.layout.label_bg.setToolTip( str( self.ref_hex_bg ) )
        # ToolTips Layout
        self.layout.mode.setToolTip( "Mode" )
        self.layout.folder.setToolTip( "Open Directory" )
        self.layout.lock.setToolTip( "Lock" )
        self.layout.colorpicker.setToolTip( "Color Picker [RGB]" )
        self.layout.control.setToolTip( "Control Options" )
        self.layout.search.setToolTip( "Search Contents" )
        self.layout.index_number.setToolTip( "Index" )
        self.layout.settings.setToolTip( "Settings" )
    def Style_Theme( self ):
        """
        Theme Breeze Dark
        w_alternate     = #31363b
        w_base          = #232629
        w_button        = #31363b
        w_dark          = #1d2023
        w_light         = #464d54
        w_mid           = #2b3034
        w_midlight      = #3c4248
        w_shadow        = #151719
        w_tool_tip      = #31363b
        w_window        = #31363b
        t_bright        = #ffffff
        t_button        = #eff0f1
        t_highlighted   = #eff0f1
        t_placeholder   = #eff0f1
        t_text          = #eff0f1
        t_tool_tip      = #eff0f1
        t_window        = #eff0f1
        c_highlight     = #3daee9
        c_link          = #2980b9
        c_visited       = #7f8c8d

        Theme Breeze Ligh
        w_alternate     = #f8f7f6
        w_base          = #fcfcfc
        w_button        = #eff0f1
        w_dark          = #888e93
        w_light         = #ffffff
        w_mid           = #c4c8cc
        w_midlight      = #f6f7f7
        w_shadow        = #474a4c
        w_tool_tip      = #fcfcfc
        w_window        = #eff0f1
        t_bright        = #ffffff
        t_button        = #31363b
        t_highlighted   = #fcfcfc
        t_placeholder   = #31363b
        t_text          = #31363b
        t_tool_tip      = #31363b
        t_window        = #31363b
        c_highlight     = #3daee9
        c_link          = #0057ae
        c_visited       = #452886
        """
        # Read
        palette = QApplication.palette()
        base = palette.base().color()
        # Window
        w_alternate     = palette.alternateBase().color().name()
        w_base          = palette.base().color().name()
        w_button        = palette.button().color().name()
        w_dark          = palette.dark().color().name()
        w_light         = palette.light().color().name()
        w_mid           = palette.mid().color().name()
        w_midlight      = palette.midlight().color().name()
        w_shadow        = palette.shadow().color().name()
        w_tool_tip      = palette.toolTipBase().color().name()
        w_window        = palette.window().color().name()
        # Text
        t_bright        = palette.brightText().color().name()
        t_button        = palette.buttonText().color().name()
        t_highlighted   = palette.highlightedText().color().name()
        t_placeholder   = palette.placeholderText().color().name()
        t_text          = palette.text().color().name()
        t_tool_tip      = palette.toolTipText().color().name()
        t_window        = palette.windowText().color().name()
        # Color
        c_highlight     = palette.highlight().color().name()
        c_link          = palette.link().color().name()
        c_visited       = palette.linkVisited().color().name()
        # c_accent        = palette.accent().color().name() # qt6
        # Alpha ( Transparent )
        a_base          = f"rgba( { base.red() }, { base.green() }, { base.blue() }, 30 )"
        a_black         = "#00000000"

        # Colors
        win = palette.window().color().getHsvF()
        hue = palette.highlight().color().getHsvF()
        m2 = +0.03; m3 = -0.03
        if win[2] > 0.5:    d2 = +0.20; d3 = -0.05; t3 = -0.30 # Light Theme
        else:               d2 = +0.10; d3 = +0.10; t3 = +0.30 # Dark Theme
        backdrop = QColor().fromHsvF( win[0], win[1] + 0,  win[2] - 0.05 ).name()
        menu     = QColor().fromHsvF( hue[0], win[1] + m2, win[2] + m3 ).name()
        dim      = QColor().fromHsvF( hue[0], win[1] + d2, win[2] + d3 ).name()
        text     = QColor().fromHsvF( win[0], win[1] + 0,  win[2] + t3 ).name()

        # Self Variables
        self.w_light    = w_light
        self.w_mid      = w_mid
        self.w_midlight = w_midlight
        self.a_black    = a_black

        # Modules
        self.panel_preview.Set_Theme( w_light, w_window, c_highlight, t_button )
        self.panel_grid.Set_Theme( w_light, w_window, c_highlight, c_link )
        self.panel_reference.Set_Theme( w_light, w_window, c_highlight, c_link )

        # Layout
        if self.mode_index in [ 0, 1 ]: qs_ss = self.Style_Slider( w_light, w_mid, dim, w_mid )
        elif self.mode_index == 2:      qs_ss = self.Style_Slider( a_black, a_black, w_mid, w_mid )
        self.layout.index_slider.setStyleSheet( qs_ss )
        self.layout.pc_slider.setStyleSheet( qs_ss )

        # StyleSheets Panels
        if self.state_transparent == True:
            # Panel Preview
            pv_ss = "#preview_view{ background-color: " + a_base + "; }"
            pc_ss = "#preview_control{ background-color: " + a_base + "; }"
            pp_ss = "#panel_preview{ background-color: " + a_black + "; }"
            # Panel Grid
            gv_ss = "#grid_view{ background-color: " + a_base + "; }"
            gc_ss = "#grid_control{ background-color: " + a_base + "; }"
            pg_ss = "#panel_grid{ background-color: " + a_black + "; }"
            # Panel Reference
            rv_ss = "#reference_view{ background-color: " + a_base + "; }"
            rc_ss = "#reference_control{ background-color: " + a_base + "; }"
            pr_ss = "#panel_reference{ background-color: " + a_black + "; }"
            # Progress Bar
            progress_bar_style_sheet = self.Style_ProgressBar( c_highlight, a_base )
        else:
            # Panel Preview
            pv_ss = "#preview_view{ background-color: " + backdrop + "; }"
            pc_ss = "#preview_control{ background-color: " + backdrop + "; }"
            pp_ss = "#panel_preview{ background-color: " + backdrop + "; }"
            # Panel Grid
            gv_ss = "#grid_view{ background-color: " + backdrop + "; }"
            gc_ss = "#grid_control{ background-color: " + backdrop + "; }"
            pg_ss = "#panel_grid{ background-color: " + backdrop + "; }"
            # Panel Reference
            rv_ss = "#reference_view{ background-color: " + backdrop + "; }"
            rc_ss = "#reference_control{ background-color: " + backdrop + "; }"
            pr_ss = "#panel_reference{ background-color: " + backdrop + "; }"
            # Progress Bar
            progress_bar_style_sheet = self.Style_ProgressBar( c_highlight, backdrop )

        self.layout.preview_view.setStyleSheet( pv_ss )
        self.layout.preview_control.setStyleSheet( pc_ss )
        self.layout.panel_preview.setStyleSheet( pp_ss )
        # Panel Grid
        self.layout.grid_view.setStyleSheet( gv_ss )
        self.layout.grid_control.setStyleSheet( gc_ss )
        self.layout.panel_grid.setStyleSheet( pg_ss )
        # Panel Reference
        self.layout.reference_view.setStyleSheet( rv_ss )
        self.layout.reference_control.setStyleSheet( rc_ss )
        self.layout.panel_reference.setStyleSheet( pr_ss )

        # Progress Bar
        self.layout.progress_bar.setStyleSheet( progress_bar_style_sheet )
        # Search
        self.layout.search.setStyleSheet( "#search{ color: " + text + "; background-color: " + backdrop + "; border-radius: 5px; }" )
        # Numbers
        self.layout.index_number.setStyleSheet( "#index_number{ color: " + text + "; background-color: " + w_base + "; }" )
        self.layout.ref_info.setStyleSheet( "#ref_info{ color: " + text + "; background-color: " + w_base + "; }" )

        # layout Stylesheet
        self.layout.folder.setStyleSheet( "#folder::checked{ background-color : " + w_light + "; }" )
        self.layout.lock.setStyleSheet( "#lock::checked{ background-color : " + w_light + "; }" )
        self.layout.colorpicker.setStyleSheet( "#colorpicker::checked{ background-color : " + w_light + "; }" )
        self.layout.control.setStyleSheet( "#control::checked{ background-color : " + w_light + "; }" )
        # Dialog Stylesheet
        self.dialog.scroll_area_contents_display.setStyleSheet( "#scroll_area_contents_display{ background-color: " + menu + "; }" )
        self.dialog.tab_keyenter.setStyleSheet( "#tab_keyenter{ background-color: " + menu + "; }" )
        self.dialog.tab_reorder.setStyleSheet( "#tab_reorder{ background-color: " + menu + "; }" )
        self.dialog.tab_drive.setStyleSheet( "#tab_drive{ background-color: " + menu + "; }" )
        self.dialog.scroll_area_contents_system.setStyleSheet( "#scroll_area_contents_system{ background-color: " + menu + "; }" )

        # Progressbar
        progress_style_sheet = self.Style_ProgressBar( c_highlight, a_black )
        self.dialog.progress_bar.setStyleSheet( progress_style_sheet )
    def Style_PreviewControl( self, state ):
        show = state in [ "ANIM", "COMP" ]
        if show == True:    pc_ss = self.Style_Slider( self.w_light, self.w_mid, self.w_midlight, self.w_mid )
        else:               pc_ss = self.Style_Slider( self.a_black, self.a_black, self.w_mid, self.w_mid )
        self.layout.pc_slider.setStyleSheet( pc_ss )
    def Style_ProgressBar( self, percentage, background ):
        style_sheet = str()
        style_sheet += "QProgressBar { background-color: " + background + "; border-radius: 0px; }"
        style_sheet += "QProgressBar::chunk { background-color: " + percentage + "; }"
        return style_sheet
    def Style_Slider( self, handle, border, page_sub, page_add ):
        style_sheet = str()
        style_sheet += "QSlider::groove:horizontal { border: 1px solid; height: 2px; }"
        style_sheet += "QSlider::handle:horizontal { background-color: " + handle + "; width: 10px; height: 10px; margin: -5px 2px; border: 1px solid " + border + "; border-radius: 5px; }"
        style_sheet += "QSlider::sub-page:horizontal { background-color: " + page_sub + "; }" # Left Side
        style_sheet += "QSlider::add-page:horizontal { background-color: " + page_add + "; }" # Right Side
        return style_sheet

    #endregion
    #region Interface Dialog

    # Items Sync
    def Sync_List( self, sync_list ):
        # Checks
        self.sync_list = sync_list
        # Watcher
        self.Refresh_Documents( False )
        self.Refresh_Reference( False )
        # Display
        if self.state_load == True:
            self.Filter_Search()
        # Finish
        Kritarc_Write( DOCKER_NAME, "sync_list", self.sync_list )
    def Sync_Type( self, sync_type ):
        # Directory
        self.sync_type = sync_type
        if sync_type == "Normal":   self.file_extension = file_normal
        if sync_type == "BackUp~":  self.file_extension = file_backup
        if sync_type == "All":      self.file_extension = file_all
        # Display
        if self.state_load == True:
            self.Filter_Search()
        # Save
        Kritarc_Write( DOCKER_NAME, "sync_type", self.sync_type )
    def Sync_Sort( self, sync_sort ):
        # Sorting
        if self.state_load == True and self.sync_sort != sync_sort:
            self.sync_sort = sync_sort
            self.Sort_Update( self.list_url, self.sync_sort, self.sort_reverse )
        # Drive Tree View
        self.Drive_Model()
        self.Drive_Tree_View()
        # Save
        Kritarc_Write( DOCKER_NAME, "sync_sort", self.sync_sort )
    # Item Modifiers
    def Folder_Show( self, boolean ):
        self.directory_show = boolean
        if self.state_load == True:
            self.Filter_Search()
        Kritarc_Write( DOCKER_NAME, "directory_show", self.directory_show )
    def Folder_Recursive( self, boolean ):
        self.directory_recursive = boolean
        self.dialog.directory_show.setEnabled( not boolean )
        if self.state_load == True:
            self.Filter_Search()
        Kritarc_Write( DOCKER_NAME, "directory_recursive", self.directory_recursive )
    def Sort_Reverse( self, boolean ):
        self.sort_reverse = boolean
        if self.state_load == True:
            self.Sort_Update( self.list_url, self.sync_sort, self.sort_reverse )
        Kritarc_Write( DOCKER_NAME, "sort_reverse", self.sort_reverse )
    # Sorting
    def Sort_Update( self, list_url, sync_sort, sort_reverse ):
        sort_list = self.Sort_List( list_url, sync_sort, sort_reverse )
        self.list_url.clear()
        self.list_url = sort_list
        self.Display_Number( 0 )

    # System Show on Welcome
    def ShowOnWelcome_Imagine( self, sow_imagine ):
        self.sow_imagine = sow_imagine
        try:self.setProperty( "ShowOnWelcomePage", sow_imagine )
        except:pass
        Kritarc_Write( DOCKER_NAME, "sow_imagine", self.sow_imagine )
    def ShowOnWelcome_Dockers( self, sow_dockers ):
        self.sow_dockers = sow_dockers
        Kritarc_Write( DOCKER_NAME, "sow_dockers", self.sow_dockers )
    def Welcome_Dockers( self ):
        # Imagine Board
        if self.sow_imagine == True:
            try:self.setProperty( "ShowOnWelcomePage", True )
            except:pass
        # Dockers
        if self.sow_dockers == True:
            dockers = Krita.instance().dockers()
            for d in dockers:
                try:d.setProperty( "ShowOnWelcomePage", True )
                except:pass
    # System Transparent
    def Transparent_Docker( self, sys_transparent ):
        self.sys_transparent = sys_transparent
        self.Transparent_Shift( self.state_inside )
        Kritarc_Write( DOCKER_NAME, "sys_transparent", self.sys_transparent )
    def Transparent_Shift( self, boolean ):
        # Settings
        if self.sys_transparent == True and self.isFloating() == True:
            state_transparent = not boolean
            self.Footer_Scale( boolean )
            self.setAttribute( Qt.WA_TranslucentBackground, not boolean )
            self.setAttribute( Qt.WA_NoSystemBackground, not boolean )
        else:
            state_transparent = False
            self.Footer_Scale( True )
            self.setAttribute( Qt.WA_TranslucentBackground, False )
            self.setAttribute( Qt.WA_NoSystemBackground, False )
        # Variables
        if self.state_transparent != state_transparent:
            self.state_transparent = state_transparent
            self.Theme_Changed()
        # Update
        self.update()
    def Footer_Scale( self, boolean ):
        self.layout.footer.setMinimumHeight( int( boolean * 37 ) )
        self.layout.footer.setMaximumHeight( int( boolean * 37 ) )
        self.Size_Update()
    # System Insert Image
    def Insert_Original_Size( self, boolean ):
        self.sys_insert_original_size = boolean
        self.panel_preview.Set_Insert_Original_Size( boolean )
        self.panel_grid.Set_Insert_Original_Size( boolean )
        self.panel_reference.Set_Insert_Original_Size( boolean )
        Kritarc_Write( DOCKER_NAME, "sys_insert_original_size", self.sys_insert_original_size )
    # Scaling Method
    def Display_Pixelated( self, boolean ):
        # Variables
        self.sys_pixelart = boolean
        if boolean == True: pixelart = Qt.FastTransformation
        else:               pixelart = Qt.SmoothTransformation
        # Panels
        self.panel_preview.Set_Scale_Method( pixelart )
        self.panel_grid.Set_Scale_Method( pixelart )
        self.panel_reference.Set_Scale_Method( pixelart )
        # Save
        Kritarc_Write( DOCKER_NAME, "sys_pixelart", self.sys_pixelart )

    # Progress Bar
    def Dialog_ProgressBar_Value( self, value ):
        self.dialog.progress_bar.setValue( value )
    def Dialog_ProgressBar_Max( self, value ):
        self.dialog.progress_bar.setMaximum( value )
    def Dialog_ProgressBar_Reset( self ):
        self.dialog.progress_bar.setValue( 0 )
        self.dialog.progress_bar.setMaximum( 1 )

    # Dialogs
    def Menu_Manual( self ):
        url = "https://github.com/EyeOdin/imagine_board/wiki"
        webbrowser.open_new( url )
    def Menu_License( self ):
        url = "https://github.com/EyeOdin/imagine_board/blob/main/LICENSE"
        webbrowser.open_new( url )

    #endregion
    #region Management

    # Import Modules
    def Import_Pigment_O( self ):
        # Variables
        self.pigmento_picker = None
        self.pigmento_sampler = None
        style_text = "Color Picker [SRGB]"

        # Search Dockers
        docker_list = Krita.instance().dockers()
        for docker in docker_list:
            try: # Module Picker
                if docker.objectName() == self.pigmento_picker_pyid:
                    self.pigmento_picker = docker
                    style_text = "Color Picker [P]"
            except:
                pass
            try: # Module Sampler
                if docker.objectName() == self.pigmento_sampler_pyid:
                    self.pigmento_sampler = docker
            except:
                pass
        # Modules
        self.panel_preview.Set_Pigment_O( self.pigmento_picker, self.pigmento_sampler )
        self.panel_grid.Set_Pigment_O( self.pigmento_picker, self.pigmento_sampler )
        self.panel_reference.Set_Pigment_O( self.pigmento_picker, self.pigmento_sampler )
        # Style
        self.layout.colorpicker.setToolTip( style_text )

    # String
    def Path_Components( self, url ):
        directory = os.path.dirname( url ) # dir
        basename = os.path.basename( url ) # name.ext
        split_text = os.path.splitext( basename )
        name = split_text[0] # name
        extension = split_text[1] # .ext
        return directory, basename, name, extension
    def File_Extension( self, url ):
        if url == None:
            extension = None
        else:
            extension = pathlib.Path( url ).suffix
            extension = extension.replace( ".", "" )
        return extension

    # File Items
    def Directory_List_Url( self, directory, filters, recursive ):
        # Variables
        list_url = list()
        # Settings
        if filters == "DIR_FILE":   filters = QDir.AllDirs | QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot
        elif filters == "DIR":      filters = QDir.AllDirs | QDir.NoSymLinks | QDir.NoDotAndDotDot
        elif filters == "FILE":     filters = QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot
        if recursive == True:       recursive = QDirIterator.Subdirectories
        else:                       recursive = QDirIterator.NoIteratorFlags
        # Directory
        qdir = QDir()
        qdir.setPath( directory )
        qdir.setFilter( filters )
        qdir.setNameFilters( self.file_extension )
        # Files
        it = QDirIterator( qdir, recursive )
        while( it.hasNext() ):
            url = os.path.normpath( it.next() )
            list_url.append( url )
        # Return
        return list_url
    # File Dialog
    def Open_Directory( self, string, directory ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        folder_url = file_dialog.getExistingDirectory( self, string, directory )
        folder_url = os.path.normpath( folder_url )
        return folder_url
    def Open_File( self, string, directory, extension ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        file_url = file_dialog.getOpenFileName( self, string, directory, f"File( *.{ extension } )" )[0]
        file_url = os.path.normpath( file_url )
        return file_url

    # QTimer Hold Menu
    def Menu_Timer_Start( self, function ):
        self.menu_hold = QtCore.QTimer()
        self.menu_hold.setSingleShot( True )
        self.menu_hold.setInterval( self.press_time )
        self.menu_hold.timeout.connect( function )
        self.menu_hold.start()
    def Menu_Timer_Stop( self ):
        try:self.menu_hold.stop()
        except:pass

    # Icons
    def Label_Icon( self, widget, hex_color ):
        qpixmap = QPixmap( 20, 20 )
        qpixmap.fill( QColor( hex_color ) )
        qicon = QIcon( qpixmap )
        widget.setIcon( qicon )

    # Widget
    def WidgetList_Setting( self, widget ):
        # Variables
        size = 50
        # Widget Settings
        widget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Expanding )
        widget.setFocusPolicy( Qt.NoFocus )
        # QFrame
        widget.setFrameShape( QFrame.NoFrame )
        widget.setFrameShadow( QFrame.Plain )
        widget.setLineWidth( 0 )
        # QAbstractScrollArea
        widget.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        # QAbstractItemView
        widget.setEditTriggers( QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked )
        widget.setDropIndicatorShown( True )
        widget.setDragEnabled( True )
        widget.setDragDropMode( QAbstractItemView.DragDrop )
        widget.setDefaultDropAction( Qt.MoveAction )
        widget.setAlternatingRowColors( True )
        widget.setSelectionMode( QAbstractItemView.ExtendedSelection )
        widget.setIconSize( QSize( size, size ) )
        # QListView
        widget.setSelectionRectVisible( True )
        # QListWidget
    def WidgetList_Item( self, url, icon ):
        item = QListWidgetItem()
        item.setText( os.path.basename( url ) )
        item.setToolTip( url )
        if icon != None:
            item.setIcon( icon )
        return item
    def WidgetList_Icon_File( self, url ):
        try:
            reader = QImageReader( url )
            reader.setAutoTransform( True )
            reader.setScaledSize( QSize( icon_size, icon_size ) )
            qpixmap = QPixmap().fromImageReader( reader )
            qicon = QIcon( qpixmap )
        except:
            qicon = None
        return qicon

    #endregion
    #region Signals

    # Mouse Stylus
    def Drop_Inside( self, lista ):
        if len( lista ) > 0:
            # Variables
            item = lista[0]
            # Check Source
            if Check_Html( item ):
                self.Display_Internet( item )
            else:
                # Checks
                item = os.path.normpath( item )
                check_dir = os.path.isdir( item )
                check_file = os.path.isfile( item )
                # Logic
                if check_dir == True:
                    directory = item
                    basename = None
                if check_file == True:
                    directory = os.path.dirname( item )
                    basename = os.path.basename( item )
                # Open
                if self.folder_url != directory:
                    self.Folder_Load( directory, None, 0 )
                self.Display_String( basename )

    # Extension
    def Shortcut_Browse( self, browse ):
        if self.mode_index == 0:
            self.Preview_Increment( browse )
        if self.mode_index == 1:
            self.Grid_Increment( browse )
        if self.mode_index == 2:
            self.Reference_Zoom_Step( browse )
    def Shortcut_Frame( self, frame ):
        if frame > 0:
            self.Preview_Forward()
        if frame < 0:
            self.Preview_Back()

    #endregion
    #region API

    def API_Preview_QPixmap( self, url, qpixmap ):
        # Set Image to Render ( ignores "animation" and "compressed" )
        self.panel_preview.Preview_QPixmap( url, qpixmap )
    def Imagine_Sample_Script( self ):
        """
        import krita

        pyid = "pykrita_imagine_board_docker"
        list_docker = Krita.instance().dockers()
        for docker in list_docker:
            if docker.objectName() == pyid:
                imagine_board = docker
                break
        url = str()
        qpixmap = QPixmap( url )
        imagine_board.API_Preview_QPixmap( url, qpixmap )
        """

    #endregion
    #region Files

    # Interaction
    def Hold_Folder( self ):
        self.Menu_Timer_Stop()
        self.Menu_Timer_Start( self.Folder_Menu )
    def Release_Folder( self ):
        self.Menu_Timer_Stop()
        self.Folder_Open()

    # Folder
    def Folder_Menu( self ):
        locked = self.Folder_Lock()
        if locked == False:
            if self.folder_url == None:
                self.Folder_Open()
            else:
                # Menu
                qmenu = QMenu( self )
                qmenu.setMinimumWidth( 8 * len( self.folder_url ) )
                # Title
                qmenu.addSection( self.folder_url )
                # Parent Dir
                parent = f"🖿 { os.path.basename( os.path.dirname( self.folder_url ) ) }"
                qmenu_parent = qmenu.addAction( parent )
                qmenu.addSection( " " )
                # Child Dirs
                action_list = list()
                for item in self.folder_shift:
                    child = f"⤷ { os.path.basename( item ) }"
                    action = qmenu.addAction( child )
                    action_list.append( action )
                # Execute
                geo = self.layout.folder.geometry()
                qpoint = geo.bottomLeft()
                position = self.layout.icon_buttons.mapToGlobal( qpoint )
                action = qmenu.exec_( position )
                # Triggers
                url = None
                if action == qmenu_parent:
                    self.Folder_Parent()
                for i in range( 0, len( action_list ) ):
                    if action == action_list[i]:
                        url = self.folder_shift[i]
                        self.Folder_Load( url, None, 0 )
                        break
            # Layout Clean Up
            self.layout.folder.setDown( False )
    def Folder_Shift( self, directory ):
        self.folder_shift = list()
        self.folder_shift = self.Directory_List_Url( directory, "DIR", False )
        if len( self.folder_shift ) > 0:
            self.folder_shift.sort()
    def Folder_Parent( self ):
        dirname = os.path.dirname( self.folder_url )
        basename = os.path.basename( self.folder_url )
        self.Folder_Load( dirname, basename, 0 )
    def Folder_Open( self ):
        locked = self.Folder_Lock()
        if locked == False:
            folder_url = self.Open_Directory( "Select Directory", self.folder_url )
            if folder_url not in invalid:
                self.Folder_Load( folder_url, None, 0 )
    def Folder_Load( self, folder_url, file_name, file_index ):
        if folder_url not in invalid and self.state_cycle == False:
            folder_url = os.path.normpath( folder_url )
            exists = os.path.exists( folder_url )
            if exists == True:
                # Variables
                self.folder_url = folder_url
                self.preview_slideshow_list.clear()
                # UI
                string = f"Folder : { os.path.basename( self.folder_url ) }"
                self.layout.folder.setToolTip( string )
                # Operation
                self.Filter_Files( self.search_string, file_name, file_index )
                self.Folder_Shift( folder_url )
                self.Watcher_Update()
            else:
                self.folder_url = ""
            # Save
            Kritarc_Write( DOCKER_NAME, "folder_url", self.folder_url )
    def Folder_Lock( self ):
        locked = not self.layout.folder.isFlat()
        if locked == True:
            message = "Continue Operation ?"
            boolean = QMessageBox.question( QWidget(), DOCKER_NAME, message, QMessageBox.Yes, QMessageBox.Abort )
            if boolean == QMessageBox.Abort:
                self.cycle_worker.Stop()
        return locked

    # Filter
    def Filter_Search( self ):
        self.search_string = self.layout.search.text().lower()
        self.Filter_Files( self.search_string, None, 0 )
        Kritarc_Write( DOCKER_NAME, "search", self.search_string )
    def Filter_Files( self, search, file_name=None, file_index=None ):
        try:
            # Watcher
            try:self.qtimer_watcher.stop()
            except:pass

            # Variables
            str_list = self.sync_list
            location = ""
            str_search = search

            # Time Watcher
            start = QtCore.QDateTime.currentDateTimeUtc()

            # Lists
            list_url, count, location = self.Request_Lists()

            # Progress Bar
            self.ProgressBar_Value( 0 )
            self.ProgressBar_Maximum( count )

            # Filter Keywords
            list_url = self.Request_Keywords( list_url, count, search )
            list_url = self.Sort_List( list_url, self.sync_sort, self.sort_reverse )

            # Progress Bar
            self.ProgressBar_Value( 0 )
            self.ProgressBar_Maximum( 1 )

            # Variables
            self.list_url.clear()
            self.list_url = list_url
            self.preview_max = len( list_url )
            self.preview_slideshow_index = 0
            self.preview_slideshow_list = list()

            # Variables
            if self.preview_max > 0:
                self.file_found = True
                self.Index_Range( 1, self.preview_max )
            else:
                self.file_found = False
                self.Index_Range( 0, 0 )

            # Update List and Display
            if   file_name  != None:    self.Display_String( file_name )
            elif file_index != None:    self.Display_Number( file_index )

            # Time Watcher
            time = QtCore.QTime( 0,0 ).addMSecs( start.msecsTo( QtCore.QDateTime.currentDateTimeUtc() ) )
            Message_Log( "TIME", f"{ time.toString( 'hh:mm:ss.zzz' ) } | LIST { str_list } | LOCATION { location } | SEARCH { str_search }" )
        except Exception as e:
            self.Filter_Null()
    def Filter_Null( self ):
        self.Index_Range( 0, 0 )
        self.Index_Values( 0 )

    # Search
    def Search_Completer( self, search_string ):
        if len( self.search_string ) < len( search_string ): # Letter was added
            count = len( search_string )
            rsplit = search_string.lower().rsplit( " ", 1 )
            # previous = rsplit[0]
            word = rsplit[-1]
            if word is not invalid and len( word ) > 2:
                # Matches
                self.search_key = list()
                for key in self.keyenter_list_key:
                    if key.startswith( word ) == True:
                        self.search_key.append( key )
                # Widget
                if len( self.search_key ) > 0:
                    self.search_index = 0
                    key = self.search_key[0]
                    letters = key.replace( word, "" )
                    # Insert Match
                    self.layout.search.blockSignals( True )
                    self.layout.search.insert( letters )
                    self.layout.search.blockSignals( False )
                    # Cursor
                    self.layout.search.setCursorPosition( count )
                    self.layout.search.cursorWordForward( True )
        # Variables
        self.search_string = search_string
    def Search_Swap( self, value ):
        try:
            # Signals
            self.layout.search.blockSignals( True )
            # Key
            self.search_index = Limit_Loop( self.search_index + value, len( self.search_key ) - 1 )
            key = self.search_key[self.search_index]
            # String
            string = self.layout.search.text()
            cursor = self.layout.search.selectionStart()
            try:
                w = string.rindex( " " )
                previous = string[0:w]
                texto = previous + " " + key
            except:
                texto = key
            # Widget
            self.layout.search.setText( texto )
            self.layout.search.setCursorPosition( cursor )
            self.layout.search.cursorWordForward( True )
            # Signals
            self.layout.search.blockSignals( False )
        except:
            pass

    # Requests
    def Request_Lists( self ):
        if self.sync_list == "Directory":
            location = os.path.basename( self.folder_url )
            list_url, count = self.Lists_Directory()
        elif self.sync_list == "Recent Documents":
            location = "Recent Documents"
            list_url, count = self.Lists_Krita()
        elif self.sync_list == "Reference":
            location = self.panel_reference.Get_File_Name()
            list_url, count = self.Lists_Reference()
        else:
            location = "None"
            list_url = list()
            count = 0
        return list_url, count, location
    def Request_Keywords( self, list_url, count, search ):
        # Variables
        search_list = list()
        # Search
        if len( search ) > 0:
            # Variables
            nao = "not"
            marker = False
            accept = list()
            remove = list()

            # Keywords
            lower = search.lower()
            split = lower.split( " " )
            for word in split:
                if word == nao:         marker = True
                elif marker == False:   accept.append( word )
                elif marker == True:    remove.append( word )
            # Logic Case
            check_logic = split[0] == nao

            # Cycle
            for i in range( 0, count ):
                # Progress Bar
                self.ProgressBar_Value( i + 1 )
                # Variables
                fp = list_url[i]
                fn = os.path.basename( fp ).lower()
                md = Metadata_Read( fp )
                # Logic
                if check_logic == True: # case: not B
                    check = True
                    for rem in remove:
                        if rem in fn or rem in md:
                            check = False
                            break
                else: # case: A not B
                    check = False
                    for key in accept:
                        if key in fn or key in md:
                            check = True
                            break
                    for rem in remove:
                        if rem in fn or rem in md:
                            check = False
                            break
                # Construct
                if check == True:
                    search_list.append( fp )
        else:
            search_list = list_url
        # Return
        return search_list
    # Lists
    def Lists_Directory( self ):
        # Variables
        file_info = list()
        list_url = list()
        # Settings
        if self.directory_show == True and self.directory_recursive == False:
            filters = "DIR_FILE"
        else:
            filters = "FILE"
        list_url = self.Directory_List_Url( self.folder_url, filters, self.directory_recursive )
        count = len( list_url )
        # Return
        return list_url, count
    def Lists_Krita( self ):
        list_url = list()
        for doc in self.list_krita:
            url = os.path.normpath( doc )
            list_url.append( url )
        count = len( list_url )
        return list_url, count
    def Lists_Reference( self ):
        list_url = list()
        self.list_reference = self.panel_reference.Get_Pin()
        for pin in self.list_reference:
            tipo = pin["tipo"]
            url = pin["url"]
            if tipo == "image":
                if os.path.isfile( url ):
                    url = os.path.normpath( url ) # Local ( internet does not need to change )
                list_url.append( url )
        count = len( list_url )
        return list_url, count

    # Sort
    def Sort_File( self, sync_sort ):
        file_sort = QDir.LocaleAware
        if sync_sort == "Name":         file_sort = QDir.Name
        elif sync_sort == "Time":       file_sort = QDir.Time
        elif sync_sort == "Size":       file_sort = QDir.Size
        elif sync_sort == "Type":       file_sort = QDir.Type
        elif sync_sort == "Unsorted":   file_sort = QDir.Unsorted
        elif sync_sort == "NoSort":     file_sort = QDir.NoSort
        elif sync_sort == "Reversed":   file_sort = QDir.Reversed
        elif sync_sort == "IgnoreCase": file_sort = QDir.IgnoreCase
        return file_sort
    def Sort_List( self, list_url, sync_sort, sort_reverse ):
        if sync_sort in [ "Name", "Time", "Size", "Type", "Dimension" ]:
            # Variables
            boolean = False
            list_dir = list()
            list_file = list()
            list_web = list()
            # Descrimination
            for url in list_url:
                if os.path.isdir( url ):
                    list_dir.append( url ) # Directory
                elif os.path.isfile( url ): # File
                    if sync_sort == "Name":
                        name = os.path.basename( url ).lower()
                        item = [ name, url ]
                    elif sync_sort == "Time":
                        boolean = True
                        time = os.path.getmtime( url )
                        item = [ time, url ]
                    elif sync_sort == "Size":
                        boolean = True
                        size = os.path.getsize( url )
                        item = [ size, url ]
                    elif sync_sort == "Type":
                        tipo = os.path.splitext( url )[1]
                        item = [ tipo, url ]
                    elif sync_sort == "Dimension":
                        size = QImageReader( url ).size()
                        dim = size.width() * size.height()
                        item = [ dim, url ]
                        del size
                    else:
                        boolean = True
                        item = [ i, url ]
                    list_file.append( item )
                else: # Internet
                    list_web.append( url )
            # Sort
            list_dir.sort()
            list_file.sort( reverse=boolean )
            list_web.sort()
            if sort_reverse == True:
                list_dir.reverse()
                list_file.reverse()
                list_web.reverse()
            # Clean List
            list_url = list()
            if self.directory_show == True:
                for url in list_dir:
                    list_url.append( url )
            for url in list_file:
                list_url.append( url[1] )
            for url in list_web:
                list_url.append( url )
        return list_url

    # Recent Documents
    def Refresh_Documents( self, update=False ):
        if self.sync_list == "Recent Documents":
            # Variables
            list_new = list()
            # Read
            recent_doc = krita.Krita.instance().recentDocuments()
            recent_doc.sort()
            for rd in recent_doc:
                if rd != "":
                    list_new.append( rd )
            if set( self.list_krita ) != set( list_new ):
                self.list_krita = list_new
                if self.state_load == True or update == True:
                    self.Filter_Search()
    def Refresh_Reference( self, update=False ):
        if self.sync_list == "Reference":
            list_new = self.panel_reference.Get_Pin()
            if self.list_reference != list_new:
                self.list_reference = list_new
                if self.state_load == True or update == True:
                    self.Filter_Search()

    #endregion
    #region Index

    # Index
    def Index_Block( self, boolean ):
        self.layout.index_slider.blockSignals( boolean )
        self.layout.index_number.blockSignals( boolean )
    def Index_Range( self, minimum, maximum ):
        # Signals
        self.Index_Block( True )
        # Slider
        self.layout.index_slider.setMinimum( minimum )
        self.layout.index_slider.setMaximum( maximum )
        # Number
        self.layout.index_number.setMinimum( minimum )
        self.layout.index_number.setMaximum( maximum )
        self.Index_Suffix()
        # Signals
        self.Index_Block( False )
    def Index_Suffix( self ):
        maxi = self.preview_max
        string = f":{ maxi }"
        if self.mode_index == 0 and self.preview_state in [ "ANIM", "COMP" ]:
            pc_maxi = str( self.preview_pc_max )
            pc_value = str( self.preview_pc_value ).zfill( len( pc_maxi ) )
            string += f" [{ pc_value }:{ pc_maxi }]"
        self.layout.index_number.setSuffix( string )
    def Index_Values( self, value ):
        self.Index_Block( True )
        self.layout.index_slider.setValue( value + 1 )
        self.layout.index_number.setValue( value + 1 )
        self.Index_Block( False )
    def Index_Slider( self, value ):
        self.Index_Name( value - 1 ) # Humans start at 1 and script starts at 0
        self.layout.index_number.blockSignals( True )
        self.layout.index_number.setValue( value )
        self.layout.index_number.blockSignals( False )
        if self.file_found == True:
            self.Display_Update( False )
    def Index_Number( self, value ):
        self.Index_Name( value - 1 ) # Humans start at 1 and script starts at 0
        self.layout.index_slider.blockSignals( True )
        self.layout.index_slider.setValue( value )
        self.layout.index_slider.blockSignals( False )
        if self.file_found == True:
            self.Display_Update( False )
    def Index_Name( self, preview_index ):
        # Variables
        if self.file_found == True:
            self.preview_index = Limit_Range( preview_index, 0, self.preview_max )
            url = self.list_url[ self.preview_index ]
            self.preview_name = os.path.basename( url )
            self.preview_state = self.Index_State( url )
            string = f"{ self.preview_state } : { self.preview_name }"
        else:
            self.preview_name = None
            self.preview_state = None
            string = "NONE"
    def Index_State( self, url ):
        # State
        state = None
        if os.path.isfile( url ):
            state = "FILE"
            reader = QImageReader( url )
            check_read = reader.canRead() == True
            check_anim = reader.supportsAnimation() == True
            check_pdf = False
            check_comp = zipfile.is_zipfile( url ) == True
            if check_comp == False:
                if check_read == True and check_anim == False:
                    state = "IMG"
                elif check_read == True and check_anim == True:
                    state = "ANIM"
                elif check_read == True and check_pdf == True:
                    state = "PDF"
            elif check_comp == True:
                state = "COMP"
        elif os.path.isdir( url ) == True:
            state = "DIR"
        elif Check_Html( url ) == True:
            state = "WEB"
        # Widgets
        self.PreviewControl_Control( state )
        self.Style_PreviewControl( state )
        # Return
        return state

    # Replace ( signals )
    def Replace_Index( self, index, url ):
        if self.file_found == True and self.sync_list == "Directory":
            self.list_url[index] = url
    def Replace_Name( self, url_old, url_new ):
        if url_old in self.list_url:
            index = self.list_url.index( url_old )
            self.list_url[index] = url_new

    #endregion
    #region Display

    # Display Channels
    def Display_Number( self, index ):
        self.Index_Name( index )
        self.Index_Values( index )
        self.Display_Update( False )
    def Display_String( self, file_name ):
        index = 0
        for i in range( 0, len( self.list_url ) ):
            url = self.list_url[i]
            basename = os.path.basename( url )
            if basename == file_name:
                index = i
                break
        self.Index_Name( index )
        self.Index_Values( index )
        self.Display_Update( True )
    def Display_Internet( self, url ):
        qpixmap = Download_QPixmap( url )
        if qpixmap != None:
            self.Mode_Index( 0, False )
            self.panel_preview.Preview_QPixmap( url, qpixmap )

    # Display Update
    def Display_Update( self, update ):
        self.Display_Sync()
        if self.mode_index == 0:self.Display_Preview( update )
        if self.mode_index == 1:self.Display_Grid( update )
        if self.mode_index == 2:self.Display_Reference( update )
    # Display Actions
    def Display_Sync( self ):
        Kritarc_Write( DOCKER_NAME, "preview_index", self.preview_index )
    def Display_Preview( self, update ):
        if self.file_found == True:
            self.Index_Name( self.preview_index )
            self.panel_preview.Preview_Path( self.list_url[ self.preview_index ], self.preview_state, update )
        else:
            self.Index_Name( None )
            self.panel_preview.Preview_Default()
    def Display_Grid( self, update ):
        if self.file_found == True:
            self.Index_Name( self.preview_index )
            self.panel_grid.Grid_Line( self.preview_index, self.list_url, update )
        else:
            self.Index_Name( None )
            self.panel_grid.Grid_Default()
    def Display_Reference( self, update ):
        pass

    #endregion
    #region Preview

    # Docker Slidshow
    def SlideShow_Sequence( self, preview_slideshow_sequence ):
        self.preview_slideshow_sequence = preview_slideshow_sequence
        Kritarc_Write( DOCKER_NAME, "preview_slideshow_sequence", self.preview_slideshow_sequence )
    def SlideShow_Rate( self, qtime ):
        self.preview_slideshow_rate = QTime( 0, 0, 0 ).msecsTo( qtime )
        Kritarc_Write( DOCKER_NAME, "preview_slideshow_rate", self.preview_slideshow_rate )
    # Docker Gridline
    def Gridline_X( self, preview_gridline_x ):
        self.preview_gridline_x = preview_gridline_x
        self.panel_preview.Set_Gridline_Division( self.preview_gridline_x, self.preview_gridline_y)
        Kritarc_Write( DOCKER_NAME, "preview_gridline_x", self.preview_gridline_x )
    def Gridline_Y( self, preview_gridline_y ):
        self.preview_gridline_y = preview_gridline_y
        self.panel_preview.Set_Gridline_Division( self.preview_gridline_x, self.preview_gridline_y)
        Kritarc_Write( DOCKER_NAME, "preview_gridline_y", self.preview_gridline_y )
    def Gridline_State( self, boolean ):
        self.preview_gridline_state = boolean
        self.panel_preview.Set_Gridline_State( self.preview_gridline_state )
        Kritarc_Write( DOCKER_NAME, "preview_gridline_state", self.preview_gridline_state )
    # Docker Underlayer
    def Underlayer_Color_Dialog( self ):
        color_dialog = QtWidgets.QColorDialog( self )
        qcolor = color_dialog.getColor( QColor( self.preview_underlayer_color ) )
        if qcolor.isValid() == True:
            self.Display_Underlayer_Color( qcolor.name() )
    def Display_Underlayer_Color( self, hex_string ):
        self.preview_underlayer_color = hex_string
        self.dialog.preview_underlayer_color.setText( self.preview_underlayer_color )
        self.Label_Icon( self.dialog.preview_underlayer_color, self.preview_underlayer_color ) # Button
        self.panel_preview.Set_Underlayer_Color( self.preview_underlayer_color )
        Kritarc_Write( DOCKER_NAME, "preview_underlayer_color", self.preview_underlayer_color )
    def Underlayer_State( self, boolean ):
        self.preview_underlayer_state = boolean
        self.panel_preview.Set_Underlayer_State( self.preview_underlayer_state )
        Kritarc_Write( DOCKER_NAME, "preview_underlayer_state", self.preview_underlayer_state )

    # Preview Operations
    def Preview_Increment( self, increment ):
        if self.file_found == True:
            index = Limit_Range( self.preview_index + increment, 0, self.preview_max - 1 )
            self.Display_Number( index )
    def Preview_Random( self ):
        if self.file_found == True:
            random_value = self.preview_index
            while random_value == self.preview_index:
                random_value = Random_Range( self.preview_max - 1 )
            self.Display_Number( random_value )
    def Preview_SlideShow( self, boolean ):
        if boolean == True:
            self.qtimer_slideshow.start( self.preview_slideshow_rate )
            self.layout.pc_slideshow.setIcon( self.qicon_slideshow_stop )
        elif boolean == False:
            self.qtimer_slideshow.stop()
            self.layout.pc_slideshow.setIcon( self.qicon_slideshow_play )

    # Preview Control Enable
    def PreviewControl_Control( self, state ):
        if   state == "ANIM":   self.PreviewControl_Widget_Enable( False, False, True )
        elif state == "COMP":   self.PreviewControl_Widget_Enable( True, True, False )
        else:                   self.PreviewControl_Widget_Enable( False, False, False )
    def PreviewControl_Widget_Enable( self, slider, frame, play ):
        # Enables
        self.layout.pc_slider.setEnabled( slider )
        self.layout.pc_back.setEnabled( frame )
        self.layout.pc_forward.setEnabled( frame )
        self.layout.pc_playpause.setEnabled( play )
        # Play button
        self.layout.pc_playpause.setChecked( False )
        self.layout.pc_playpause.setIcon( self.qicon_anim_play )
    def PreviewControl_Pause_Enable( self, boolean ):
        self.layout.pc_slider.setEnabled( boolean )
        self.layout.pc_back.setEnabled( boolean )
        self.layout.pc_forward.setEnabled( boolean )
    # Preview Control Update
    def PreviewControl_Slider_Value( self, value ):
        self.preview_pc_value = value
        self.layout.pc_slider.blockSignals( True )
        self.layout.pc_slider.setValue( value )
        self.layout.pc_slider.blockSignals( False )
        self.Index_Suffix()
    def PreviewControl_Slider_Maximum( self, value ):
        self.preview_pc_max = value
        self.layout.pc_slider.blockSignals( True )
        self.layout.pc_slider.setMaximum( value )
        self.layout.pc_slider.blockSignals( False )

    # Animation & Compact
    def Preview_Play( self ):
        if self.preview_state == "ANIM":
            self.layout.pc_playpause.setChecked( False )
    def Preview_PlayPause( self, preview_playpause ):
        if self.preview_state == "ANIM":
            self.preview_playpause = preview_playpause
            if preview_playpause == True: # Paused
                self.layout.pc_playpause.setIcon( self.qicon_anim_pause )
                self.PreviewControl_Pause_Enable( True )
                self.panel_preview.Anim_Pause()
            if preview_playpause == False: # Playing
                self.layout.pc_playpause.setIcon( self.qicon_anim_play )
                self.PreviewControl_Pause_Enable( False )
                self.panel_preview.Anim_Play()
    def Preview_Back( self ):
        if self.preview_state == "ANIM":    self.panel_preview.Anim_Back()
        if self.preview_state == "COMP":    self.panel_preview.Comp_Back()
    def Preview_Forward( self ):
        if self.preview_state == "ANIM":    self.panel_preview.Anim_Forward()
        if self.preview_state == "COMP":    self.panel_preview.Comp_Forward()
    def Preview_Slider( self, value ):
        if self.preview_state == "ANIM":    self.panel_preview.Anim_Frame( value )
        if self.preview_state == "COMP":    self.panel_preview.Comp_Index( value )

    # Slideshow
    def SlideShow_Timer( self ):
        self.qtimer_slideshow = QtCore.QTimer( self )
        self.qtimer_slideshow.timeout.connect( self.Slideshow_Increment )
        self.qtimer_slideshow.stop()
    def Slideshow_Increment( self ):
        if self.file_found == True:
            if self.preview_slideshow_sequence == "Linear":
                number = Limit_Loop( self.preview_index + 1, self.preview_max - 1 )
                self.Display_Number( number )
            if self.preview_slideshow_sequence == "Random":
                # List
                if self.preview_slideshow_index == 0:
                    self.preview_slideshow_list = list()
                    for i in range( 0, self.preview_max ):
                        self.preview_slideshow_list.append( i )
                    random.shuffle( self.preview_slideshow_list )
                # Cycle
                self.preview_slideshow_index = Limit_Loop( self.preview_slideshow_index + 1, self.preview_max - 1 )
                self.Display_Number( self.preview_slideshow_list[ self.preview_slideshow_index ] )

    #endregion
    #region Grid

    # Docker Grid
    def Grid_Thumbnail( self, grid_thumb ):
        self.grid_thumb = grid_thumb
        self.Size_Update()
        Kritarc_Write( DOCKER_NAME, "grid_thumb", self.grid_thumb )
    def Grid_Precache( self, grid_precache ):
        self.grid_precache = grid_precache
        self.panel_grid.Set_Precache( self.grid_precache )
        Kritarc_Write( DOCKER_NAME, "grid_precache", self.grid_precache )
    def Grid_Clean( self, grid_clean ):
        self.grid_clean = grid_clean
        self.panel_grid.Set_Clean( self.grid_clean )
        Kritarc_Write( DOCKER_NAME, "grid_clean", self.grid_clean )

    # Grid Operations
    def Grid_Increment( self, increment ):
        self.panel_grid.Grid_Increment( increment )

    #endregion
    #region Reference

    # Lock
    def Reference_Lock( self, boolean ):
        self.ref_lock = boolean
        if boolean == False:
            self.layout.lock.setIcon( self.qicon_lock_false )
            self.panel_reference.Packer_Interrupt()
        if boolean == True:
            self.layout.lock.setIcon( self.qicon_lock_true )
        self.panel_reference.Set_Lock( self.ref_lock )
        Kritarc_Write( DOCKER_NAME, "ref_lock", self.ref_lock )
    def Lock_State( self, boolean ):
        # Icon
        if boolean == False:    self.layout.lock.setIcon( self.qicon_lock_false )
        if boolean == True:     self.layout.lock.setIcon( self.qicon_lock_true )
        # Check
        self.layout.lock.blockSignals( True )
        self.layout.lock.setChecked( boolean )
        self.layout.lock.blockSignals( False )
    def Lock_Canvas( self, canvas ):
        # Variables
        ki = Krita.instance()
        annotation_type = list()
        self.qicon_lock_false = self.qicon_lock_false_1
        ad = None
        # Canvas
        if canvas != None:
            ad = ki.activeDocument()
            if ad != None:annotation_type = ad.annotationTypes()
            if DOCKER_NAME in annotation_type:self.qicon_lock_false = self.qicon_lock_false_2
        # Layout Icons
        check = self.layout.lock.isChecked()
        if check == False:  self.layout.lock.setIcon( self.qicon_lock_false )
        if check == True:   self.layout.lock.setIcon( self.qicon_lock_true )
        # Reference Active Document
        self.panel_reference.Set_Link_Document( ad )

    # Dialog
    def Reference_Import_Size( self, boolean ):
        self.ref_import_size = boolean
        Kritarc_Write( DOCKER_NAME, "ref_import_size", self.ref_import_size )
    def Reference_Rebase_Recursive( self, boolean ):
        self.ref_rebase_recursive = boolean
        self.panel_reference.Set_Rebase( self.ref_rebase_recursive )
        Kritarc_Write( DOCKER_NAME, "ref_rebase_recursive", self.ref_rebase_recursive )

    # Camera
    def Reference_Camera_Display( self, ref_camera_position, ref_camera_zoom, select_count, len_board ):
        # Variables
        self.ref_camera_position = ref_camera_position
        self.ref_camera_zoom = ref_camera_zoom
        # Interface User
        self.layout.ref_info.setText( f"{ select_count }:{ len_board }" )
    def Reference_Zoom_Step( self, zoom ):
        self.panel_reference.Camera_Zoom_Step( zoom )

    # Board
    def Board_Timer( self ):
        if self.qtimer_reference.isActive() == False:
            check_eo  = self.panel_reference.Get_EO_State() and self.state_load == False
            check_kra = self.panel_reference.Get_KRA_State()
            if check_eo == True or check_kra == True:
                self.state_load = True
                self.qtimer_reference = QTimer( self )
                self.qtimer_reference.setSingleShot( True )
                self.qtimer_reference.timeout.connect( self.Board_Load )
                self.qtimer_reference.start( 3000 )
    def Board_Load( self ):
        self.panel_reference.Board_Refresh()
    # Pin
    def Pin_Insert( self, tipo, bx, by, text, url, clip ):
        # Variables
        qpixmap = None
        width = 0
        height = 0
        # Clip
        if clip["cstate"] == True:
            cstate = clip["cstate"]
            cl = clip["cl"]
            ct = clip["ct"]
            cw = clip["cw"]
            ch = clip["ch"]
        else:
            cstate = False
            cl = 0
            ct = 0
            cw = 1
            ch = 1
        # Dimensions
        if tipo == "label": # Label
            width = 200
            height = 100
        else: # Image
            if os.path.isfile( url ) == True: # Local
                url = os.path.normpath( url )
                reader = QImageReader( url )
                if reader.canRead() == True:
                    qpixmap = QPixmap().fromImageReader( reader )
                    # Size
                    width = int( qpixmap.width() )
                    height = int( qpixmap.height() )
                    # Clip
                    qpixmap = qpixmap.copy( int( width*cl ), int( height*ct ), int( width*cw ), int( height*ch ) )
                    # Size
                    width = int( qpixmap.width() )
                    height = int( qpixmap.height() )
            elif Check_Html( url ): # Internet
                qpixmap = Download_QPixmap( url )
                if qpixmap != None:
                    width = int( qpixmap.width() )
                    height = int( qpixmap.height() )
        # Action
        if ( width > 0 ) and ( height > 0 ):
            # Fit
            if ( tipo == "image" ) and ( self.ref_import_size == False ):
                side = 200
                if width > 0 and height > 0:
                    fx = side / width
                    fy = side / height
                else:
                    width = side
                    height = side
                    fx = 1
                    fy = 1
                if width >= height:
                    sx = width * fy
                    sy = side
                else:
                    sx = side
                    sy = height * fx
                width = int( sx )
                height = int( sy )
            # Variables
            w2 = width * 0.5
            h2 = height * 0.5
            # Bounding Box
            bl = int( bx - w2 )
            br = int( bl + width )
            bt = int( by - h2 )
            bb = int( bt + height )
            bw = int( width )
            bh = int( height )
            # ID
            index = self.panel_reference.Get_Count() + 1
            # State
            render = True
            active = False
            select = False
            pack = False
            # Transform
            rotation_z = 0
            scale_constant = Trig_2D_Points_Distance( 0, 0, bw, bh )
            scale_width = bw
            scale_height = bh
            # Dimensions
            area = bw * bh
            perimeter = ( 2 * bw ) + ( 2 * bh )
            ratio = bw / bh
            pack = False
            # Edits
            edit_grayscale = False
            edit_flip_x = False
            edit_flip_y = False
            # Text
            font = "Consolas"
            letter = 20
            # Colors
            pen = self.color_white
            bg = self.color_black
            # QPixmap & Draw
            if tipo == "image" and qpixmap != None:
                draw = qpixmap.scaled( int( bw * self.ref_camera_zoom ), int( bh * self.ref_camera_zoom ), Qt.IgnoreAspectRatio, Qt.FastTransformation )
            else:
                qpixmap = None
                draw = None
            zarchive = None
            # Pin Object
            pin = {
                # ID
                "index"     : index, # integer
                # Type
                "tipo"      : tipo, # string ("image" "label")
                # State
                "render"    : render, # bool
                "active"    : active, # bool
                "select"    : select, # bool
                "pack"      : pack, # bool
                # Transform
                "trz"       : rotation_z, # float
                "tsk"       : scale_constant, # float ( diameter of circle )
                "tsw"       : scale_width, # float ( width with no rotation )
                "tsh"       : scale_height, # float ( height with no rotation )
                # Bound Box
                "bx"        : bx, # float ( center x )
                "by"        : by, # float ( center y )
                "bl"        : bl, # float ( left )
                "br"        : br, # float ( right )
                "bt"        : bt, # float ( top )
                "bb"        : bb, # float ( bottom )
                "bw"        : bw, # float ( width )
                "bh"        : bh, # float ( height )
                # Clip
                "cstate"    : cstate, # bool
                "cl"        : cl, # float
                "ct"        : ct, # float
                "cw"        : cw, # float
                "ch"        : ch, # float
                # Dimensions
                "area"      : area, # float
                "perimeter" : perimeter, # float
                "ratio"     : ratio, # float
                # Edits
                "egs"       : edit_grayscale, # bool
                "efx"       : edit_flip_x, # bool
                "efy"       : edit_flip_y, # bool
                # Text
                "text"      : text, # string
                "font"      : font, # string
                "letter"    : letter, # integer
                "pen"       : pen, # string
                "bg"        : bg, # string
                # Pixmap
                "url"       : url, # string
                "qpixmap"   : qpixmap, # QPixmap
                "draw"      : draw, # QPixmap
                "zarchive"  : zarchive, # string of bytes
                }
            # Emit
            self.panel_reference.Pin_Insert( pin )
            # Garbage
            del qpixmap, draw, pin

    # Preview Control Interface
    def ReferenceControl_UI( self, boolean ):
        if self.mode_index == 2 and boolean == True:
            value = qt_max
        else:
            value = 0
        self.layout.reference_control.setMaximumHeight( value )
    def ReferenceControl_Shrink( self ):
        self.layout.reference_control.setMaximumHeight( 0 )
    # Label Operations
    def Reference_Label( self, info_text, info_font, info_letter, info_pen, info_bg ):
        self.ref_hex_pen = info_pen
        self.ref_hex_bg = info_bg
        # Signals
        self.layout.label_font.blockSignals( True )
        self.layout.label_letter.blockSignals( True )
        self.layout.label_pen.blockSignals( True )
        self.layout.label_bg.blockSignals( True )
        # ToolTip
        self.layout.label_font.setCurrentText( info_font )
        self.layout.label_letter.setValue( info_letter )
        self.layout.label_pen.setToolTip( info_pen )
        self.layout.label_bg.setToolTip( info_bg )
        # Modules
        self.Label_Icon( self.layout.label_pen, self.ref_hex_pen )
        self.Label_Icon( self.layout.label_bg, self.ref_hex_bg )
        # Signals
        self.layout.label_font.blockSignals( False )
        self.layout.label_letter.blockSignals( False )
        self.layout.label_pen.blockSignals( False )
        self.layout.label_bg.blockSignals( False )
    def Label_Text( self ):
        previous = self.panel_reference.Get_Label_Infomation()
        if previous != None:
            string, ok = QInputDialog.getMultiLineText( self, DOCKER_NAME, "Input Text", previous["text"] )
            if ( ok == True and string != None ):
                self.panel_reference.Set_Label_Text( string )
    def Label_Font( self, font ):
        self.panel_reference.Set_Label_Font( font )
    def Label_Letter( self, letter ):
        self.panel_reference.Set_Label_Letter( letter )
    def Label_Pen( self ):
        color_dialog = QtWidgets.QColorDialog( self )
        qcolor = color_dialog.getColor( QColor( self.ref_hex_pen ) )
        if qcolor.isValid() == True:
            self.ref_hex_pen = qcolor.name()
            self.Label_Icon( self.layout.label_pen, self.ref_hex_pen ) # Button
            self.panel_reference.Set_Label_Pen( self.ref_hex_pen ) # Panel
    def Label_BG( self ):
        color_dialog = QtWidgets.QColorDialog( self )
        qcolor = color_dialog.getColor( QColor( self.ref_hex_bg ) )
        if qcolor.isValid() == True:
            self.ref_hex_bg = qcolor.name()
            self.Label_Icon( self.layout.label_bg, self.ref_hex_bg ) # Button
            self.panel_reference.Set_Label_Bg( self.ref_hex_bg ) # Panel

    #endregion
    #region Bookmark

    # Interaction
    def Hold_Bookmark( self ):
        self.Menu_Timer_Stop()
        self.Menu_Timer_Start( self.Bookmark_Menu )
    def Release_Bookmark( self ):
        self.Menu_Timer_Stop()
        self.Bookmark_Open()

    # Context Menu
    def Bookmark_Menu( self ):
        # QMenu
        qmenu = QMenu( self )
        action_bookmark_save = qmenu.addAction( "Save" )
        action_bookmark_delete = qmenu.addAction( "Delete")
        # Geometry
        geo = self.layout.bookmark_open.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.grid_control.mapToGlobal( qpoint )
        action = qmenu.exec_( position )
        # Actions
        if action == action_bookmark_save:
            self.Bookmark_Save()
        if action == action_bookmark_delete:
            self.Bookmark_Delete()
        self.layout.bookmark_open.setDown( False )
    # Operators
    def Bookmark_Open( self ):
        if len( self.bookmark_list ) > 0:
            index = self.layout.bookmark_entries.currentIndex()
            folder_url = self.bookmark_list[index]
            self.Folder_Load( folder_url, None, 0 )
    def Bookmark_Save( self ):
        if self.folder_url not in self.bookmark_list:
            self.bookmark_list.append( self.folder_url )
            self.bookmark_list.sort()
            self.Bookmark_ComboBox( self.bookmark_list )
            self.layout.bookmark_entries.setCurrentText( os.path.basename( self.folder_url ) )
    def Bookmark_Delete( self ):
        index = self.layout.bookmark_entries.currentIndex()
        if index >= 0:
            self.bookmark_list.pop( index )
            self.Bookmark_ComboBox( self.bookmark_list )
    def Bookmark_ComboBox( self, lista ):
        self.layout.bookmark_entries.clear()
        for item in lista:
            basename = os.path.basename( item )
            self.layout.bookmark_entries.addItem( basename )
        Kritarc_Write( DOCKER_NAME, "bookmark_list", self.bookmark_list )

    #endregion
    #region Cycle

    def Cycle_Process( self, mode ):
        thread = True
        if thread == False: self.Cycle_Single( mode )
        if thread == True:  self.Cycle_Thread( mode )
    def Cycle_Connect( self ):
        self.state_cycle = True
        self.cycle_worker = Worker_Cycle()
        self.cycle_worker.SIGNAL_INDEX_URL.connect( self.Replace_Index )
        self.cycle_worker.SIGNAL_TEXT.connect( self.Search_Label )
        self.cycle_worker.SIGNAL_PB_VALUE.connect( self.ProgressBar_Value )
        self.cycle_worker.SIGNAL_PB_MAX.connect( self.ProgressBar_Maximum )
        self.cycle_worker.SIGNAL_PB_RESET.connect( self.ProgressBar_Reset )
        self.cycle_worker.SIGNAL_FINISH.connect( self.Cycle_Finish )
    def Cycle_Single( self, mode ):
        self.Cycle_Connect()
        self.cycle_worker.run( self, mode, False )
    def Cycle_Thread( self, mode ):
        # Thread
        self.cycle_qthread = QtCore.QThread()
        # Worker
        self.Cycle_Connect()
        self.cycle_worker.moveToThread( self.cycle_qthread )
        # Thread
        self.cycle_qthread.started.connect( lambda : self.cycle_worker.run( self, mode, True ) )
        self.cycle_qthread.start()
    def Cycle_Finish( self ):
        self.state_cycle = False
        self.Display_Update( True )
        QApplication.beep()

    #endregion
    #region Keyenter

    # Widget
    def Keyenter_WidgetList( self ):
        # Reorder QlistWidget ( Promoted Widgets dont work, so construct a widget by code )
        self.keyenter_widget_url = List_Data( self ) # Promoted Widget
        self.keyenter_widget_url.setObjectName( "keyenter_widget_url" )
        self.dialog.keyenter_container_layout.addWidget( self.keyenter_widget_url )
        # List Data Settings
        self.WidgetList_Setting( self.keyenter_widget_url )
    def Keyenter_Block( self, boolean ):
        self.dialog.keyenter_run.setEnabled( boolean )

    # Keyword String
    def Keyenter_String( self ):
        string_key = self.dialog.keyenter_string.text()
        list_key = string_key.split()
        self.Keyenter_Key_Add( list_key )
        self.dialog.keyenter_string.clear()
    # List KEY Menu
    def Keyenter_Key_Menu( self, event ):
        qmenu = QMenu( self )
        action_construct = qmenu.addAction( "Construct from Folder" )
        action_remove = qmenu.addAction( "Remove Selected" )
        action_clear = qmenu.addAction( "Clear List" )
        action = qmenu.exec_( self.dialog.keyenter_widget_key.mapToGlobal( event.pos() ) )
        if action == action_construct:
            self.Keyenter_Key_Construct()
        if action == action_remove:
            self.Keyenter_Key_Remove()
        if action == action_clear:
            self.Keyenter_Key_Clear()
    def Keyenter_Key_Construct( self ):
        list_key = list()
        for i in range( 0, self.preview_max ):
            url = self.list_url[i]
            meta_data = Metadata_Read( url )
            split = meta_data.split( " " )
            for key in split:
                if ( key not in invalid ) and ( key not in list_key ):
                    list_key.append( key )
        self.Keyenter_Key_Add( list_key )
    def Keyenter_Key_Remove( self ):
        list_select = self.dialog.keyenter_widget_key.selectedItems()
        for item in list_select:
            # List
            try:
                string = item.text()
                index = self.keyenter_list_key.index( string )
                self.keyenter_list_key.pop( index )
            except:
                pass
            # Widget
            try:
                row = self.dialog.keyenter_widget_key.row( item )
                self.dialog.keyenter_widget_key.takeItem( row )
            except:
                pass
        Kritarc_Write( DOCKER_NAME, "keyenter_list_key", self.keyenter_list_key )
    def Keyenter_Key_Clear( self ):
        self.keyenter_list_key.clear()
        self.dialog.keyenter_widget_key.clear()
        Kritarc_Write( DOCKER_NAME, "keyenter_list_key", self.keyenter_list_key )
    # List KEY Operators
    def Keyenter_Key_Load( self, list_key ):
        for text in list_key:
            self.dialog.keyenter_widget_key.addItem( text )
    def Keyenter_Key_Add( self, list_key ):
        for key in list_key:
            if key not in self.keyenter_list_key:
                self.keyenter_list_key.append( key )
                self.dialog.keyenter_widget_key.addItem( key )
        Kritarc_Write( DOCKER_NAME, "keyenter_list_key", self.keyenter_list_key )

    # Keyenter Operator
    def Keyenter_Operation( self, mode ):
        self.keyenter_mode = mode
    # List URL Menu Signals
    def Keyenter_Url_Folder( self ):
        directory = self.Open_Directory( "Select Directory", self.folder_url )
        if directory not in invalid:
            list_url = self.Directory_List_Url( directory, "FILE", False )
            self.Keyenter_Url_Add( list_url )
    def Keyenter_Url_Remove( self ):
        list_select = self.keyenter_widget_url.selectedItems()
        for item in list_select:
            # List
            try:
                url = item.toolTip()
                index = self.keyenter_list_url.index( url )
                self.keyenter_list_url.pop( index )
            except:
                pass
            # Widget
            try:
                row = self.keyenter_widget_url.row( item )
                self.keyenter_widget_url.takeItem( row )
            except:
                pass
    def Keyenter_Url_Clear( self ):
        self.keyenter_list_url.clear()
        self.keyenter_widget_url.clear()
    # List URL Operators
    def Keyenter_Url_Add( self, lista ):
        # Variables
        count = len( lista )
        # Progress Bar
        self.Keyenter_Block( False )
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( count )
        # Cycle
        for i in range( 0, count ):
            index = i + 1
            url = lista[i]
            check_file = os.path.isfile( url )
            if check_file == True and url not in self.keyenter_list_url:
                self.keyenter_list_url.append( url )
                qicon = self.WidgetList_Icon_File( url )
                item = self.WidgetList_Item( url, qicon )
                self.keyenter_widget_url.addItem( item )
            if i % 10 == 0:
                self.Dialog_ProgressBar_Value( index )
                QApplication.processEvents()
        # Progress Bar
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( 1 )
        self.Keyenter_Block( True )
        # Update
        self.update()

    # Run
    def Keyenter_Run( self ):
        # Variables
        list_key = list()
        list_select = self.dialog.keyenter_widget_key.selectedItems()
        for item in list_select:
            list_key.append( item.text() )
        list_url = self.keyenter_list_url
        # Process
        check_write = self.keyenter_mode not in [ "NONE", "KEY_CLEAN" ] and len( list_key ) > 0 and len( list_url ) > 0
        check_clean = self.keyenter_mode == "KEY_CLEAN" and len( list_url ) > 0
        if check_write == True or check_clean == True:
            self.Keyenter_Process( list_key, list_url )
    # Reorder Worker
    def Keyenter_Process( self, list_key, list_url ):
        thread = True
        if thread == False: self.Keyenter_Single( list_key, list_url )
        if thread == True:  self.Keyenter_Thread( list_key, list_url )
    def Keyenter_Connect( self ):
        self.keyenter_worker = Worker_Keyenter()
        self.keyenter_worker.SIGNAL_TEXT.connect( self.Search_Label )
        self.keyenter_worker.SIGNAL_PB_VALUE.connect( self.Dialog_ProgressBar_Value )
        self.keyenter_worker.SIGNAL_PB_MAX.connect( self.Dialog_ProgressBar_Max )
        self.keyenter_worker.SIGNAL_PB_RESET.connect( self.Dialog_ProgressBar_Reset )
        self.keyenter_worker.SIGNAL_FINISH.connect( self.Reorder_Finish )
    def Keyenter_Single( self, list_key, list_url ):
        self.Keyenter_Connect()
        self.keyenter_worker.run(
            self,
            self.keyenter_mode,
            list_key,
            list_url,
            False,
            )
    def Keyenter_Thread( self, list_key, list_url ):
        # Thread
        self.keyenter_qthread = QtCore.QThread()
        # Worker
        self.Keyenter_Connect()
        self.keyenter_worker.moveToThread( self.keyenter_qthread )
        # Thread
        self.keyenter_qthread.started.connect(
            lambda : self.keyenter_worker.run(
                self,
                self.keyenter_mode,
                list_key,
                list_url,
                True,
                )
            )
        self.keyenter_qthread.start()
    def Keyenter_Finish( self ):
        self.Display_Update( True )
        QApplication.beep()

    #endregion
    #region Reorder

    # Widgets
    def Reorder_WidgetList( self ):
        # Reorder QlistWidget ( Promoted Widgets dont work, so construct a widget by code )
        self.reorder_widget_url = List_Data( self ) # Promoted Widget
        self.reorder_widget_url.setObjectName( "reorder_widget_url" )
        self.dialog.reorder_container_layout.addWidget( self.reorder_widget_url )
        # List Data Settings
        self.WidgetList_Setting( self.reorder_widget_url )
    def Reorder_Block( self, boolean ):
        self.dialog.reorder_sort_name.setEnabled( boolean )
        self.dialog.reorder_sort_time.setEnabled( boolean )
        self.dialog.reorder_sort_reverse.setEnabled( boolean )
        self.dialog.reorder_run.setEnabled( boolean )

    # Header
    def Reorder_Mode( self, mode ):
        self.reorder_mode = mode
        self.Reorder_Url_Clear()
        Kritarc_Write( DOCKER_NAME, "reorder_mode", self.reorder_mode )
    def Reorder_String( self ):
        texto = self.dialog.reorder_string.text()
        reorder_string, ok = QInputDialog.getText( self, "Input Name String", "String", QLineEdit.Normal, texto, Qt.Dialog, Qt.ImhNone )
        if ok == True:
            self.reorder_string = reorder_string
            self.dialog.reorder_string.setText( reorder_string )
            Kritarc_Write( DOCKER_NAME, "reorder_string", self.reorder_string )
    def Reorder_Number( self ):
        numero = self.dialog.reorder_number.text()
        reorder_number, ok = QInputDialog.getInt( self, "Input Start Number", "Number", int( numero ), 0, 100000, 1, Qt.Dialog )
        if ok == True:
            self.reorder_number = reorder_number
            self.dialog.reorder_number.setText( str( reorder_number ).zfill( zf ) )
            Kritarc_Write( DOCKER_NAME, "reorder_number", self.reorder_number )
    # Dialogs
    def Reorder_Source_Dialog( self ):
        url = self.Open_Directory( "Select Directory", self.folder_url )
        if url not in invalid:
            self.Reorder_Source_Url( url )
    def Reorder_Source_Url( self, url ):
        self.reorder_source_url = url
        self.dialog.reorder_source_url.setText( self.reorder_source_url )
        Kritarc_Write( DOCKER_NAME, "reorder_source_url", self.reorder_source_url )
    def Reorder_Destination_Dialog( self ):
        url = self.Open_Directory( "Select Directory", self.folder_url )
        if url not in invalid:
            self.Reorder_Destination_Url( url )
    def Reorder_Destination_Url( self, url ):
        self.reorder_destination_url = url
        self.dialog.reorder_destination_url.setText( self.reorder_destination_url )
        Kritarc_Write( DOCKER_NAME, "reorder_destination_url", self.reorder_destination_url )

    # List Operators
    def Reorder_Url_Add( self, lista ):
        # Variables
        count = len( lista )
        # Progress Bar
        self.Reorder_Block( False )
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( count )
        # Cycles
        if self.reorder_mode == "FILE_RENAME":
            for i in range( 0, count ):
                url = lista[i]
                basename = os.path.basename( url )
                extension = basename.split( "." )[-1]
                if extension in file_static:
                    find = self.reorder_widget_url.findItems( basename, Qt.MatchExactly )
                    if len( find ) == 0:
                        qicon = self.WidgetList_Icon_File( url )
                        item = self.WidgetList_Item( url, qicon )
                        self.reorder_widget_url.addItem( item )
                if i % 10 == 0:
                    self.Dialog_ProgressBar_Value( i + 1 )
                    QApplication.processEvents()
        if self.reorder_mode == "COMPRESSED_RENAME":
            if zipfile.is_zipfile( lista[0] ):
                self.Reorder_Url_Clear()
                self.reorder_zip_url = lista[0]
                comp_path = list()
                archive = zipfile.ZipFile( self.reorder_zip_url, "r" )
                name_list = archive.namelist()
                for name in name_list:
                    basename = os.path.basename( name )
                    extension = basename.split( "." )[-1]
                    if extension in file_search:
                        comp_path.append( name )
                if len( comp_path ) > 0:
                    comp_order = Compressed_Sort( comp_path )
                    for i in range( 0, len( comp_order ) ):
                        path = comp_path[i]
                        buffer = Compressed_Buffer( archive, path )
                        reader = QImageReader( buffer )
                        if reader.canRead():
                            reader.setAutoTransform( True )
                            reader.setScaledSize( QSize( icon_size, icon_size ) )
                            qpixmap = QPixmap().fromImageReader( reader )
                            qicon = QIcon( qpixmap )
                            item = self.WidgetList_Item( path, qicon )
                            self.reorder_widget_url.addItem( item ) # Widget
                        if i % 10 == 0:
                            self.Dialog_ProgressBar_Value( i + 1 )
                            QApplication.processEvents()
        if self.reorder_mode == "WEB_DOWNLOAD":
            for i in range( 0, count ):
                url = lista[i]
                if Check_Html( url ):
                    basename = os.path.basename( url )
                    qpixmap = Download_QPixmap( url )
                    find = self.reorder_widget_url.findItems( basename, Qt.MatchExactly )
                    if qpixmap != None and len( find ) == 0:
                        qpixmap = qpixmap.scaled( icon_size, icon_size, Qt.IgnoreAspectRatio, Qt.FastTransformation  )
                        qicon = QIcon( qpixmap )
                        item = self.WidgetList_Item( url, qicon )
                        self.reorder_widget_url.addItem( item ) # Widget
                if i % 10 == 0:
                    self.Dialog_ProgressBar_Value( i + 1 )
                    QApplication.processEvents()
        # Progress Bar
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( 1 )
        self.Reorder_Block( True )
        # Update
        self.update()
    def Reorder_Url_Files( self ):
        directory = self.Open_Directory( "Select Directory", self.folder_url )
        if directory not in invalid:
            list_url = self.Directory_List_Url( directory, "FILE", False )
            self.Reorder_Url_Add( list_url )
    def Reorder_Url_Remove( self ):
        list_select = self.reorder_widget_url.selectedItems()
        for item in list_select:
            row = self.reorder_widget_url.row( item )
            self.reorder_widget_url.takeItem( row )
    def Reorder_Url_Clear( self ):
        self.reorder_zip_url = None
        self.reorder_list_url.clear()
        self.reorder_widget_url.clear()

    # Sorting
    def Reorder_Sort_Name( self ):
        list_url = list()
        count = self.reorder_widget_url.count()
        for i in range( 0, count ):
            item = self.reorder_widget_url.takeItem( 0 )
            url = item.toolTip()
            basename = os.path.basename( url )
            list_url.append( [ basename, item ] )
        list_url.sort()
        self.Reorder_Sort_Item( list_url )
    def Reorder_Sort_Time( self ):
        list_url = list()
        count = self.reorder_widget_url.count()
        for i in range( 0, count ):
            item = self.reorder_widget_url.takeItem( 0 )
            url = item.toolTip()
            time = os.path.getmtime( url )
            list_url.append( [ time, item ] )
        list_url.sort( reverse=True )
        self.Reorder_Sort_Item( list_url )
    def Reorder_Sort_Reverse( self ):
        list_url = list()
        count = self.reorder_widget_url.count()
        for i in range( 0, count ):
            item = self.reorder_widget_url.takeItem( 0 )
            list_url.append( [ i, item ] )
        list_url.reverse()
        self.Reorder_Sort_Item( list_url )
    def Reorder_Sort_Item( self, lista ):
        # Variables
        count = len( lista )
        # Progress Bar
        self.Reorder_Block( False )
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( count )
        # Cycle
        for i in range( 0, count ):
            self.reorder_widget_url.addItem( lista[i][1] )
            if i % 10 == 0:
                self.Dialog_ProgressBar_Value( i + 1 )
                QApplication.processEvents()
        # Progress Bar
        self.Dialog_ProgressBar_Value( 0 )
        self.Dialog_ProgressBar_Max( 1 )
        self.Reorder_Block( True )
        # Update
        self.update()

    # Run
    def Reorder_Run( self ):
        # List construct
        lista = list()
        # Source
        if self.reorder_mode == "FILE_RENAME":
            list_source = self.Directory_List_Url( self.reorder_source_url, "FILE", False )
            lista.extend( list_source )
        # Files
        count = self.reorder_widget_url.count()
        for i in range( 0, count ):
            item = self.reorder_widget_url.item( i )
            url = item.toolTip()
            lista.append( url )
        # Worker
        self.Reorder_Process( lista )
    # Reorder Worker
    def Reorder_Process( self, lista ):
        thread = False
        if thread == False: self.Reorder_Single( lista )
        if thread == True:  self.Reorder_Thread( lista )
    def Reorder_Connect( self ):
        self.reorder_worker = Worker_Reorder()
        self.reorder_worker.SIGNAL_NAME_URL.connect( self.Replace_Name )
        self.reorder_worker.SIGNAL_TEXT.connect( self.Search_Label )
        self.reorder_worker.SIGNAL_PB_VALUE.connect( self.Dialog_ProgressBar_Value )
        self.reorder_worker.SIGNAL_PB_MAX.connect( self.Dialog_ProgressBar_Max )
        self.reorder_worker.SIGNAL_PB_RESET.connect( self.Dialog_ProgressBar_Reset )
        self.reorder_worker.SIGNAL_FINISH.connect( self.Reorder_Finish )
    def Reorder_Single( self, lista ):
        self.Reorder_Connect()
        self.reorder_worker.run(
            self,
            self.reorder_mode,
            lista,
            self.reorder_string,
            self.reorder_number,
            self.reorder_destination_url,
            self.reorder_zip_url,
            False,
            )
    def Reorder_Thread( self, lista ):
        # Thread
        self.reorder_qthread = QtCore.QThread()
        # Worker
        self.Reorder_Connect()
        self.reorder_worker.moveToThread( self.reorder_qthread )
        # Thread
        self.reorder_qthread.started.connect(
            lambda : self.reorder_worker.run(
                self,
                self.reorder_mode,
                lista,
                self.reorder_string,
                self.reorder_number,
                self.reorder_destination_url,
                self.reorder_zip_url,
                True,
                )
            )
        self.reorder_qthread.start()
    def Reorder_Finish( self ):
        self.Reorder_Url_Clear()
        self.Watcher_Display()
        QApplication.beep()

    #endregion
    #region Drive

    def Drive_Widget( self ):
        # Drive Model
        self.Drive_Model()

        # Drive Tree View ( Promoted Widgets dont work, so construct a widget by code )
        self.drive_tree_view = Drive_TreeView( self ) # Promoted Widget
        self.drive_tree_view.setObjectName( "tree_view" )
        self.dialog.tab_drive_layout.addWidget( self.drive_tree_view )
        # Widget Settings
        self.drive_tree_view.setFocusPolicy( Qt.NoFocus )
        self.drive_tree_view.setAcceptDrops( True )
        self.drive_tree_view.setFrameShape( QFrame.NoFrame )
        self.drive_tree_view.setFrameShadow( QFrame.Plain )
        self.drive_tree_view.setLineWidth( 0 )
        self.drive_tree_view.setEditTriggers( QAbstractItemView.AllEditTriggers )
        self.drive_tree_view.setDropIndicatorShown( True )
        self.drive_tree_view.setDragEnabled( True )
        self.drive_tree_view.setDragDropOverwriteMode( True )
        self.drive_tree_view.setDragDropMode( QAbstractItemView.DragDrop )
        # self.drive_tree_view.setDefaultDropAction( Qt.MoveAction )
        self.drive_tree_view.setAlternatingRowColors( True )
        self.drive_tree_view.setSelectionMode( QAbstractItemView.ExtendedSelection )
        self.drive_tree_view.setSortingEnabled( True )
        # Model View
        self.Drive_Tree_View()
        # Event Filters
        self.drive_tree_view.installEventFilter( self )
    def Drive_Model( self ):
        self.drive_model = QFileSystemModel()
        self.drive_model.setRootPath( self.drive_url )
        self.drive_model.setOption( QFileSystemModel.DontUseCustomDirectoryIcons )
        # self.drive_model.sort( self.Sort_File( self.drive_sort ) )
        self.drive_model.sort( self.drive_sort )
    def Drive_Tree_View( self ):
        self.drive_tree_view.Set_File_Sort( self.Sort_File( self.drive_sort ) )
        self.drive_tree_view.setModel( self.drive_model )
        self.drive_tree_view.setRootIndex( self.drive_model.index( self.drive_url ) )
        self.drive_tree_view.setColumnWidth( 0, 400 )

    # Signals
    def Drive_Click( self, url ):
        try:QtCore.qDebug( f"url = { url.data() }" )
        except:QtCore.qDebug( f"url = { url }" )
    def Drive_Menu( self, event ):
        qmenu = QMenu( self )
        action_move = qmenu.addAction( "Move Selected Here" )
        action = qmenu.exec_( self.drive_tree_view.mapToGlobal( event.pos() ) )
        if action == action_move:
            self.Drive_Move()
    # Actions
    def Drive_Move( self ):
        # Variables
        preview_index = self.preview_index
        model_index = self.drive_tree_view.currentIndex()
        path = os.path.normpath( self.drive_model.filePath( model_index ) )
        if os.path.isfile( path ) == True:  directory = os.path.dirname( path )
        else:                               directory = path
        # Panel
        if self.mode_index == 0:    list_url = [ self.list_url[ preview_index ] ]
        if self.mode_index == 1:    list_url = self.panel_grid.Selection_List()
        if self.mode_index == 2:    list_url = self.panel_reference.Pin_Selected()
        # Cycle
        for url in list_url:
            basename = os.path.basename( url )
            destination = os.path.normpath( os.path.join( directory, basename ) )
            qfile = QFile( url )
            boolean = qfile.rename( destination )
            if boolean == True: Message_Log( "MOVE", destination )
            else:               Message_Log( "ERROR", destination )
        # Refresh
        if self.mode_index in [ 0, 1 ]:
            preview_index = Limit_Range( preview_index - 1, 0, self.preview_max - 1 )
            self.Filter_Files( self.search_string, None, preview_index )
        if self.mode_index == 2:
            self.panel_reference.Board_Refresh()

    #endregion
    #region Watcher

    # Folder
    def Watcher_Display( self ):
        # Delete Previous instance in multiple calls cases
        try:self.qtimer_watcher.stop()
        except:pass
        # Progress Bar
        self.ProgressBar_Value( 0 )
        self.ProgressBar_Maximum( 0 )
        # Create new Instance to Update
        try:
            self.qtimer_watcher = QTimer( self )
            self.qtimer_watcher.timeout.connect( lambda:self.Filter_Files( self.search_string, self.preview_name, None ) )
            self.qtimer_watcher.start( 2000 )
        except Exception as e:
            self.Filter_Search()
    def Watcher_State( self, boolean ):
        # Blocks Imagine Board from updating to changes to the Directory while Keyenter works
        if boolean == False: self.Watcher_Remove() # Stop
        if boolean == True:  self.Watcher_Add()    # Start
    def Watcher_Update( self ):
        self.Watcher_Remove()
        self.Watcher_Add()
    def Watcher_Remove( self ):
        directories = self.file_system_watcher.directories()
        files = self.file_system_watcher.files()
        clean_url = list()
        for d in range( 0, len( directories ) ):
            clean_url.append( directories[d] )
        for f in range( 0, len( files ) ):
            clean_url.append( files[f] )
        if len( clean_url ) > 0:
            self.file_system_watcher.removePaths( clean_url )
    def Watcher_Add( self ):
        # Variables
        list_url = list()
        # Add Folder Path
        folder = self.folder_url
        if folder != "":
            list_url.append( folder )
        # Add Recent Documents
        for url in self.list_krita:
            dirname = os.path.dirname( url )
            if ( dirname != folder and url not in list_url ):
                list_url.append( url )
        # Watch these Files
        for url in list_url:
            exists = os.path.exists( url )
            if exists == True:
                self.file_system_watcher.addPath( url )

    #endregion
    #region Notifier

    # Notifier
    def Window_Created( self ):
        # Module
        self.window = Krita.instance().activeWindow()
        # Signals
        self.window.activeViewChanged.connect( self.View_Changed )
        self.window.themeChanged.connect( self.Theme_Changed )
        self.window.windowClosed.connect( self.Window_Closed )

    def View_Changed( self ):
        # Lists
        self.Refresh_Documents( True )
        # Reference
        self.Board_Timer()
    def Theme_Changed( self ):
        self.Style_Icon()
        self.Style_Theme()
    def Window_Closed( self ):
        pass

    #endregion
    #region Widget Events

    def showEvent( self, event ):
        self.Welcome_Dockers()
        self.Import_Pigment_O()
        self.Board_Timer()
        self.Theme_Changed()
    def moveEvent( self, event ):
        if self.state_maximized != self.isMaximized():
            self.Size_Update()
    def resizeEvent( self, event ):
        # self.Size_Print()
        self.Size_Update()
    def enterEvent( self, event ):
        self.state_inside = True
        self.Transparent_Shift( self.state_inside )
        self.update()
    def leaveEvent( self, event ):
        self.state_inside = False
        self.Transparent_Shift( self.state_inside )
        self.Clear_Focus()
        self.update()
    def closeEvent( self, event ):
        # Variables
        self.pigmento_picker = None
        self.pigmento_sampler = None
        # Timers
        try:self.qtimer_slideshow.stop()
        except:pass
        try:self.qtimer_watcher.stop()
        except:pass
        try:self.qtimer_reference.stop()
        except:pass
        # Threads
        try:self.cycle_qthread.quit()
        except:pass
        try:self.keyenter_qthread.quit()
        except:pass
        try:self.reorder_qthread.quit()
        except:pass

    def eventFilter( self, source, event ):
        # Event
        et = event.type()
        modifier_all = QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier
        # Widgets Resize
        widgets = [
            self.layout.preview_view,
            self.layout.grid_view,
            self.layout.reference_view,
            self.layout.footer,
            ]
        if ( et == QEvent.Resize and source in widgets ):
            self.Size_Update()
        # Mode
        if ( et == QEvent.MouseButtonPress and source is self.layout.mode ):
            self.Mode_Press( event )
        if ( et == QEvent.Wheel and source is self.layout.mode ):
            self.Mode_Wheel( event )
        # Search
        if ( et == QEvent.Wheel and source is self.layout.search ):
            delta_y = event.angleDelta().y()
            angle = 5
            if delta_y >= +angle:   self.Search_Swap( -1 )
            if delta_y <= -angle:   self.Search_Swap( +1 )
        # Settings
        if ( et == QEvent.MouseButtonPress and event.modifiers() == modifier_all and source is self.layout.settings ):
            self.Size_Standard()
        # Keyenter
        if ( et == QEvent.ContextMenu and source is self.dialog.keyenter_widget_key ):
            self.Keyenter_Key_Menu( event )
        # Drive
        if ( et == QEvent.ContextMenu and source is self.drive_tree_view ):
            self.Drive_Menu( event )
        return super().eventFilter( source, event )

    def canvasChanged( self, canvas ):
        self.Lock_Canvas( canvas )

    #endregion
    #region Notes

    """
    # Label Message
    self.layout.label.setText( "message" )

    # Pop Up Message
    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( "message" ) )

    # Log Viewer Message
    QtCore.qDebug( f"value = { value }" )
    QtCore.qDebug( "message" )
    QtCore.qWarning( "message" )
    QtCore.qCritical( "message" )
    """

    """
    mime_data = sorted( mime_data, key=lambda d: d['name'] )
    """

    """
    # QImage to ByteData
    def import_to_layer( image_path, layer_node, width, height):
        qimage = QImage( image_path )
        qimage = qimage.scaled(width, height, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        if not qimage.isNull():
            qimage.convertToFormat(QImage.Format_RGBA8888)
            ptr = qimage.constBits()
            ptr.setsize( qimage.byteCount() )
            layer_node.setPixelData( bytes( ptr.asarray() ), 0, 0, qimage.width(), qimage.height() )
    """

    """
    qwindow = Krita.instance().activeWindow().qwindow()
    central = qwindow.centralWidget()
    index = central.currentIndex()
    central.currentChanged.connect( self.Link_Clear )
    """

    """
    zarchive = self.Bytes_QPixmap( qpixmap )
    zarchive = self.Bytes_Python( path )
    """

    """
    reader = QImageReader( path )
    keys = reader.textKeys()
    if len( keys ) > 0:
        for k in keys:
            QtCore.qDebug( f"key = { k } = { reader.text( k ) }" )
    """

    """
    QSlider::groove:horizontal {
        border: 1px solid #999999;
        height: 2px;
        }
    QSlider::handle:horizontal {
        background: #2a2a2a;
        width: 10px;
        margin: -5px -1px;
        border-radius: 5px;
        border: 1px solid #2a2a2a;
        }
    QSlider::add-page:horizontal {
        background-color: red;
        }
    QSlider::sub-page:horizontal {
        background-color: black;
        }
    """

    """
    def Check_Html( url ):
        boolean = False
        result = urllib.parse.urlparse( url )
        scheme = result.scheme
        if scheme == "https":
            boolean = True
        return boolean
    """

    """
    qimage.convertTo( QImage.Format_ARGB32_Premultiplied )
    """

    """
    # Detect Drives
    self.drive_url = list()
    list_drive = QtCore.QDir().drives()
    for drive in list_drive:
        path = os.path.normpath( drive.filePath() )
        self.drive_url.append( path )
    """

    #endregion

class Worker_Cycle( QtCore.QObject ):
    SIGNAL_INDEX_URL = QtCore.pyqtSignal( int, str )
    SIGNAL_TEXT = QtCore.pyqtSignal( str )
    SIGNAL_PB_VALUE = QtCore.pyqtSignal( int )
    SIGNAL_PB_MAX = QtCore.pyqtSignal( int )
    SIGNAL_PB_RESET = QtCore.pyqtSignal()
    SIGNAL_FINISH = QtCore.pyqtSignal()

    # Run
    def run( self, source, mode, thread ):
        # Recieve
        self.source = source
        self.mode = mode
        # Variables
        self.cancel = "Cycle Cancel"
        self.cycle = True
        self.qfile = QFile()
        self.list_url = self.source.list_url
        try:self.anchor = self.list_url[ self.source.preview_index ]
        except:self.anchor = None
        self.count = self.source.preview_max
        # Tags
        self.tag_null = " [NULL]"
        self.tag_original = " [ORIGINAL]"
        self.tag_copy = " [COPY]"

        if thread == True:
            self.source.cycle_qthread.setPriority( QThread.HighestPriority )

        # Operation spacing
        try:QtCore.qDebug( str( self.mode ) )
        except:pass

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()
        # Cycle
        self.Cycle_Mode()
        # Time Watcher
        time = QTime( 0,0 ).addMSecs( start.msecsTo( QtCore.QDateTime.currentDateTimeUtc() ) )
        try:QtCore.qDebug( f"{ DOCKER_NAME } | SEARCH { str( self.mode ).lower() } { time.toString( 'hh:mm:ss.zzz' ) }" )
        except:pass

        # Stop Worker
        if thread == True:
            self.source.cycle_qthread.quit()
        self.SIGNAL_FINISH.emit()
    def Stop( self ):
        self.cycle = False

    # Cycle
    def Cycle_Mode( self ):
        # Interface
        self.source.Watcher_State( False )
        self.source.dialog.group_drive.setEnabled( False )
        self.source.layout.folder.setFlat( False )
        self.source.layout.folder.setIcon( self.source.qicon_folder_off )
        self.SIGNAL_PB_VALUE.emit( 0 )
        self.SIGNAL_PB_MAX.emit( self.count )
        # Operation Cycle
        if self.mode == "NULL":                         self.Cycle_Null()
        elif self.mode == "COPY":                       self.Cycle_Copy()
        elif self.mode == "CLEAN":                      self.Cycle_Clean()
        elif self.mode in [ "FIX", "PRE_MULTIPLY" ]:    self.Cycle_Modify()
        # Interface
        self.SIGNAL_TEXT.emit( "Search" )
        self.SIGNAL_PB_VALUE.emit( self.count )
        self.SIGNAL_PB_RESET.emit()
        self.source.layout.folder.setIcon( self.source.qicon_folder_on )
        self.source.layout.folder.setFlat( True )
        self.source.dialog.group_drive.setEnabled( True )
        self.source.Watcher_State( True )
    def Cycle_Null( self ):
        found = 0
        self.SIGNAL_TEXT.emit( f"Null Search" )
        for i in range( 0, self.count ):
            # Index
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            index = i + 1
            # Null
            url_old = self.list_url[i]
            if os.path.isfile( url_old ) == True:
                url_new = self.Path_Null( url_old )
                found = self.File_Rename( url_old, url_new, found, index, 1 )
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
    def Cycle_Copy( self ):
        # Variables
        found = 0
        count = self.count

        # Dictionary Construct
        index = 0
        search_dict = dict()
        for i in range( 0, count ):
            # Index
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            index = i + 1
            # Sorting Image
            path = self.list_url[i]
            if os.path.isfile( path ) == True:
                qimage = QImageReader( path ).read()
                key = f"{ qimage.width() }x{ qimage.height() }"
                item = [ index, path ]
                try:    search_dict[ key ].append( item )
                except: search_dict[ key ] = [ item ]
                # Clean Up
                del qimage
            # Interface
            self.SIGNAL_TEXT.emit( f"Sort Files - { index }:{ count }" )
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
        for key in search_dict:
            search_dict[key].sort()
        # Progress Reset
        self.SIGNAL_PB_VALUE.emit( 0 )
        QApplication.processEvents()

        # File Verification
        if self.cycle == True:
            index = 0
            key_list = list( search_dict.keys() )
            for key in key_list:
                # Variabels
                if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
                lista = search_dict[ key ]
                chunk = len( lista )
                # Cycle
                for i in range( 0, chunk ):
                    # Index
                    if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
                    index += 1
                    # Read
                    index_i = lista[i][0]
                    url_old_i = lista[i][1]
                    # Check Images
                    qimage_i = QImageReader( url_old_i ).read()
                    for j in range( i + 1, chunk ):
                        # Index
                        if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
                        index_j = lista[j][0]
                        url_old_j = lista[j][1]
                        # Check QImages
                        qimage_j = QImageReader( url_old_j ).read()
                        check_image = qimage_i == qimage_j
                        if check_image == True:
                            # File I
                            url_new_i = self.Path_Copy( url_old_i, self.tag_original )
                            found = self.File_Rename( url_old_i, url_new_i, found, index_i, 0 )
                            # File J
                            url_new_j = self.Path_Copy( url_old_j, self.tag_copy )
                            found = self.File_Rename( url_old_j, url_new_j, found, index_j, 1 )
                        # Interface
                        self.SIGNAL_TEXT.emit( f"Copy Search - { i }:{ chunk } - { index }:{ count }" )
                        if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
                        # Clean up J
                        del qimage_j
                    # Clean up I
                    del qimage_i
    def Cycle_Clean( self ):
        found = 0
        self.SIGNAL_TEXT.emit( f"Tag Clean" )
        for i in range( 0, self.count ):
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            index = i + 1
            url_old = self.list_url[i]
            url_new = self.Path_Clean( url_old )
            found = self.File_Rename( url_old, url_new, found, index, 1 )
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
    def Cycle_Modify( self ):
        message = f"{ self.mode } will Modify files ( JPG/JPEG/JFIF/PNG )\n"
        if self.mode == "FIX":
            message += "- Color Space Profile ( to SRGB when NONE )\n- Size Sanity\n- Format Orientation\n- Offset Alignment"
        elif self.mode == "PRE_MULTIPLY":
            message += "- Channels & Alpha Channel"
        boolean = QMessageBox.warning( QWidget(), DOCKER_NAME, message, QMessageBox.Yes, QMessageBox.Abort )
        if boolean == QMessageBox.Yes:
            self.SIGNAL_TEXT.emit( f"Modifying Images" )
            for i in range( 0, self.count ):
                if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
                index = i + 1
                url = self.list_url[i]
                check_file = os.path.isfile( url )
                check_format = url.endswith( ( "jpg", "jpeg", "jfif", "png" ) )
                if check_file and check_format:
                    try:
                        # Variables
                        process = True
                        # Reader
                        reader = QImageReader( url )
                        device = reader.device()
                        formato = reader.format()
                        quality = reader.quality()
                        sub_type = reader.subType()
                        text_keys = reader.textKeys()
                        transformation = reader.transformation()
                        image_format = reader.imageFormat()

                        # Mode
                        if self.mode == "FIX":
                            """
                            Errors to Fix:
                            - fromIccProfile: failed minimal tag size sanity
                            - fromIccProfile: invalid tag offset alignment
                            - libpng warning: iCCP: known incorrect sRGB profile
                            """
                            # Image
                            transformation = QImageIOHandler.TransformationNone
                            # Rotation
                            reader.setAutoTransform( True )
                            qimage = reader.read()
                            # Color Space
                            named_color_space = qimage.colorSpace().NamedColorSpace()
                            if named_color_space == 0:
                                color_space = QColorSpace( QColorSpace.SRgb ) # What about images in Grayscale ?
                                qimage.setColorSpace( color_space )
                        elif self.mode == "PRE_MULTIPLY":
                            qimage = reader.read()
                            format_premult = self.Format_PreMult( image_format )
                            check_alpha = qimage.hasAlphaChannel()
                            if format_premult == None or check_alpha == False:
                                process = False
                            else:
                                qimage.convertTo( format_premult )

                        # Writer
                        writer = QImageWriter()
                        if formato in writer.supportedImageFormats() and process == True:
                            writer.setCompression( 0 )
                            writer.setDevice( device )
                            writer.setFileName( url )
                            writer.setFormat( formato )
                            writer.setOptimizedWrite( False )
                            writer.setProgressiveScanWrite( False )
                            writer.setQuality( quality )
                            writer.setSubType( sub_type )
                            for key in text_keys:
                                writer.setText( key, reader.text( key ) )
                            writer.setTransformation( transformation )
                            writer.write( qimage )
                            string = f"{ DOCKER_NAME } | { self.mode } { os.path.basename( url ) }"
                        else:
                            string = f"{ DOCKER_NAME } | IGNORED { os.path.basename( url ) }"
                        # Print
                        try:QtCore.qDebug( string )
                        except:pass
                    except Exception as e:
                        string = f"{ DOCKER_NAME } | ERROR { os.path.basename( url ) } | { e }"
                        try:QtCore.qDebug( string )
                        except:pass
                if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
    # Path
    def Path_Null( self, url_old ):
        url_new = None
        reader = QImageReader( url_old )
        if reader.canRead() == False:
            directory, basename, name, extension = self.source.Path_Components( url_old )
            if name.endswith( self.tag_null ) == False:
                basename_new = name + self.tag_null + extension
                url_new = os.path.normpath( os.path.join( directory, basename_new ) )
        return url_new
    def Path_Copy( self, url_old, suffix ):
        url_new = None
        directory, basename, name, extension = self.source.Path_Components( url_old )
        if name.endswith( suffix ) == False:
            basename_new = name + suffix + extension
            url_new = os.path.normpath( os.path.join( directory, basename_new ) )
        return url_new
    def Path_Clean( self, url_old ):
        url_new = None
        directory, basename, name, extension = self.source.Path_Components( url_old )
        basename = basename.replace( self.tag_null, "" )
        basename = basename.replace( self.tag_original, "" )
        basename = basename.replace( self.tag_copy, "" )
        basename = basename.replace( " - Copy", "2" ) # Windows clean up
        url_new = os.path.normpath( os.path.join( directory, basename ) )
        return url_new

    # File
    def File_Rename( self, url_old, url_new, found, index, increment ):
        try:
            if url_new != None:
                # Variables
                underscore = "_"
                # Checks
                check_exists = os.path.exists( url_new ) == False
                check_url = url_old != url_new
                # Rename
                if check_exists == True and check_url == True:
                    boolean = self.qfile.rename( url_old, url_new )
                    if boolean == True:
                        # Variables
                        found += increment
                        self.SIGNAL_INDEX_URL.emit( index - 1, url_new )
                        # Anchor Find
                        if self.anchor == url_old:
                            self.anchor = url_new
                        # String
                        string = DOCKER_NAME
                        if increment == 0:string += f" | FOUND { underscore * len( str( found ) ) }"
                        if increment == 1:string += f" | FOUND { found }"
                        string += f" | INDEX { index }"
                        string += f" | RENAME { os.path.basename( url_old ) } >> { os.path.basename( url_new ) }"
                        try:QtCore.qDebug( string )
                        except:pass
        except:
            pass
        return found
    # Format
    def Format_Fix( self, value ):
        format_fix = None
        # if value in [ 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,  25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35 ]:
        if value in range( 4, 22 ) or value in range( 25, 35 ):
            format_fix = QImage.Format_RGB32
        return format_fix
    def Format_PreMult( self, value ):
        """
        if   value == 0:  QImage.Format_Invalid
        elif value == 1:  QImage.Format_Mono
        elif value == 2:  QImage.Format_MonoLSB
        elif value == 3:  QImage.Format_Indexed8
        elif value == 4:  QImage.Format_RGB32
        elif value == 5:  QImage.Format_ARGB32
        elif value == 6:  QImage.Format_ARGB32_Premultiplied
        elif value == 7:  QImage.Format_RGB16
        elif value == 8:  QImage.Format_ARGB8565_Premultiplied
        elif value == 9:  QImage.Format_RGB666
        elif value == 10: QImage.Format_ARGB6666_Premultiplied
        elif value == 11: QImage.Format_RGB555
        elif value == 12: QImage.Format_ARGB8555_Premultiplied
        elif value == 13: QImage.Format_RGB888
        elif value == 14: QImage.Format_RGB444
        elif value == 15: QImage.Format_ARGB4444_Premultiplied
        elif value == 16: QImage.Format_RGBX8888
        elif value == 17: QImage.Format_RGBA8888
        elif value == 18: QImage.Format_RGBA8888_Premultiplied
        elif value == 19: QImage.Format_BGR30
        elif value == 20: QImage.Format_A2BGR30_Premultiplied
        elif value == 21: QImage.Format_RGB30
        elif value == 22: QImage.Format_A2RGB30_Premultiplied
        elif value == 23: QImage.Format_Alpha8
        elif value == 24: QImage.Format_Grayscale8
        elif value == 28: QImage.Format_Grayscale16
        elif value == 25: QImage.Format_RGBX64
        elif value == 26: QImage.Format_RGBA64
        elif value == 27: QImage.Format_RGBA64_Premultiplied
        elif value == 29: QImage.Format_BGR888
        elif value == 30: QImage.Format_RGBX16FPx4
        elif value == 31: QImage.Format_RGBA16FPx4
        elif value == 32: QImage.Format_RGBA16FPx4_Premultiplied
        elif value == 33: QImage.Format_RGBX32FPx4
        elif value == 34: QImage.Format_RGBA32FPx4
        elif value == 35: QImage.Format_RGBA32FPx4_Premultiplied
        elif value == 36: QImage.Format_CMYK8888
        """
        # None means there is no equivalent Color Space to Change with that becomes premultiplied
        format_premult = None
        if   value in [ 5, 6 ]:     format_premult = QImage.Format_ARGB32_Premultiplied
        elif value in [ 17, 18 ]:   format_premult = QImage.Format_RGBA8888_Premultiplied
        elif value in [ 26, 27 ]:   format_premult = QImage.Format_RGBA64_Premultiplied
        elif value in [ 31, 32 ]:   format_premult = QImage.Format_RGBA16FPx4_Premultiplied
        elif value in [ 34, 35 ]:   format_premult = QImage.Format_RGBA32FPx4_Premultiplied
        return format_premult

class Worker_Keyenter( QtCore.QObject ):
    SIGNAL_TEXT = QtCore.pyqtSignal( str )
    SIGNAL_PB_VALUE = QtCore.pyqtSignal( int )
    SIGNAL_PB_MAX = QtCore.pyqtSignal( int )
    SIGNAL_PB_RESET = QtCore.pyqtSignal()
    SIGNAL_FINISH = QtCore.pyqtSignal()

    # Run
    def run( self, source, mode, list_key, list_url, thread ):
        # Recieve
        self.source = source
        self.mode = mode
        self.list_key = list_key
        self.list_url = list_url
        # Variables
        self.cancel = "Search Cancelled"
        self.cycle = True
        self.qfile = QFile()
        self.count = len( list_url )

        # Thread
        if thread == True:
            self.source.keyenter_qthread.setPriority( QThread.HighestPriority )

        # Operation spacing
        try:QtCore.qDebug( str( self.mode ) )
        except:pass

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()
        # Cycle
        self.Cycle_Mode()
        # Time Watcher
        time = QTime( 0,0 ).addMSecs( start.msecsTo( QtCore.QDateTime.currentDateTimeUtc() ) )
        try:QtCore.qDebug( f"{ DOCKER_NAME } | KEYENTER { str( self.mode ).lower() } { time.toString( 'hh:mm:ss.zzz' ) }" )
        except:pass

        # Stop Worker
        if thread == True:
            self.source.keyenter_qthread.quit()
        self.SIGNAL_FINISH.emit()
    def Stop( self ):
        self.cycle = False

    # Cycle
    def Cycle_Mode( self ):
        # Interface
        self.source.Watcher_State( False )
        self.SIGNAL_PB_VALUE.emit( 0 )
        self.SIGNAL_PB_MAX.emit( self.count )
        # Operation Cycle
        for i in range( 0, self.count ):
            # Variables
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            index = i + 1
            # Writer
            Metadata_Write( self.mode, self.list_key, self.list_url[i] )
            # Interface
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
        # Interface
        self.SIGNAL_TEXT.emit( "Search" )
        self.SIGNAL_PB_VALUE.emit( self.count )
        self.SIGNAL_PB_RESET.emit()
        self.source.Watcher_State( True )

    # Metadata

class Worker_Reorder( QtCore.QObject ):
    SIGNAL_NAME_URL = QtCore.pyqtSignal( str, str )
    SIGNAL_TEXT = QtCore.pyqtSignal( str )
    SIGNAL_PB_VALUE = QtCore.pyqtSignal( int )
    SIGNAL_PB_MAX = QtCore.pyqtSignal( int )
    SIGNAL_PB_RESET = QtCore.pyqtSignal()
    SIGNAL_FINISH = QtCore.pyqtSignal()

    # Run
    def run( self, source, mode, lista, string, number, destination, zip_url, thread ):
        # Recieve
        self.source = source
        self.mode = mode
        self.lista = lista
        self.string = string
        self.number = number
        self.destination = destination
        self.zip_url = zip_url
        # Variables
        self.cancel = "Search Cancelled"
        self.cycle = True
        self.qfile = QFile()
        self.count = len( lista )

        # Thread
        if thread == True:
            self.source.cycle_qthread.setPriority( QThread.HighestPriority )

        # Operation spacing
        try:QtCore.qDebug( str( self.mode ) )
        except:pass

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()
        # Cycle
        self.Cycle_Mode()
        # Time Watcher
        time = QTime( 0,0 ).addMSecs( start.msecsTo( QtCore.QDateTime.currentDateTimeUtc() ) )
        try:QtCore.qDebug( f"{ DOCKER_NAME } | REORDER { str( self.mode ).lower() } { time.toString( 'hh:mm:ss.zzz' ) }" )
        except:pass

        # Stop Worker
        if thread == True:
            self.source.cycle_qthread.quit()
        self.SIGNAL_FINISH.emit()
    def Stop( self ):
        self.cycle = False

    # Cycle
    def Cycle_Mode( self ):
        # Interface
        self.source.Watcher_State( False )
        self.SIGNAL_PB_VALUE.emit( 0 )
        self.SIGNAL_PB_MAX.emit( self.count )
        # Operation Cycle
        if self.mode == "FILE_RENAME":          self.Cycle_File_Rename()
        elif self.mode == "COMPRESSED_RENAME":  self.Cycle_Compressed_Rename()
        elif self.mode == "WEB_DOWNLOAD":       self.Cycle_Web_Download()
        # Interface
        self.SIGNAL_TEXT.emit( "Search" )
        self.SIGNAL_PB_VALUE.emit( self.count )
        self.SIGNAL_PB_RESET.emit()
        self.source.Watcher_State( True )
    def Cycle_File_Rename( self ):
        self.SIGNAL_TEXT.emit( f"FILE_RENAME" )
        for i in range( 0, self.count ):
            # Cycle
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            # Variables
            index = i + 1
            numero = str( self.number + i ).zfill( zf )
            url_old = self.lista[i]
            url_new = None
            # New String
            dirname, basename, name, extension = self.Path_Components( url_old )
            url_new = self.String_Path( dirname, self.string, numero, extension )
            self.File_Rename( url_old, url_new )
            # Interface
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
    def Cycle_Compressed_Rename( self ):
        self.SIGNAL_TEXT.emit( f"COMPRESSED_RENAME" )
        # Archive Paths
        original_zip = self.zip_url
        output_zip = self.zip_url + "2"
        # Variables
        i = -1
        index = 0
        # Compressed
        with zipfile.ZipFile( original_zip, 'r' ) as zin:
            with zipfile.ZipFile( output_zip, 'w', zipfile.ZIP_DEFLATED ) as zout:
                for item in zin.infolist():
                    # Cycle
                    if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
                    # Read
                    file_name = item.filename
                    file_data = zin.read( file_name )
                    # Check
                    if file_name in self.lista:
                        # Variables
                        i = self.lista.index( file_name )
                        index = i + 1
                        numero = str( self.number + i ).zfill( zf )
                        url_old = file_name
                        url_new = None
                        # New String
                        dirname, basename, name, extension = self.Path_Components( url_old )
                        url_new = self.String_Path( dirname, self.string, numero, extension )
                        # Write
                        zout.writestr( url_new, file_data )
                    else:
                        zout.writestr( file_name, file_data )
                    # Interface
                    if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()
        zout.close()
        zin.close()
        # Manage Files
        self.qfile.moveToTrash( original_zip )
        self.qfile.rename( output_zip, original_zip )
    def Cycle_Web_Download( self ):
        self.SIGNAL_TEXT.emit( f"Web Download to Destination" )
        for i in range( 0, self.count ):
            # Cycle
            if self.cycle == False: self.SIGNAL_TEXT.emit( self.cancel ); break
            # Variables
            index = i + 1
            numero = str( self.number + i ).zfill( zf )
            url_web = self.lista[i]
            url_new = None
            # New String
            dirname, basename, name, extension = self.Path_Components( url_web )
            url_new = self.String_Path( self.destination, self.string, numero, extension )
            self.File_Download( url_web, url_new )
            # Interface
            if i % 5 == 0: self.SIGNAL_PB_VALUE.emit( index ); QApplication.processEvents()

    # Strings
    def Path_Components( self, url ):
        dirname = os.path.dirname( url ) # dir
        basename = os.path.basename( url ) # name.ext
        split_text = os.path.splitext( basename )
        name = split_text[0] # name
        extension = split_text[1] # .ext
        return dirname, basename, name, extension
    def String_Path( self, dirname, string, numero, extension ):
        name_new = self.string + "_" + numero + extension
        url_new = os.path.normpath( os.path.join( dirname, name_new ) )
        return url_new
    def Print_String( self, string ):
        try:QtCore.qDebug( string )
        except:pass
    # Files
    def File_Rename( self, url_old, url_new ):
        check_new = url_new != None
        check_exist = os.path.exists( url_new ) == False
        check_diff = url_old != url_new
        if check_new and check_exist and check_diff:
            boolean = self.qfile.rename( url_old, url_new )
            if boolean == True:
                self.Print_String( f"{ DOCKER_NAME } | RENAME { os.path.basename( url_old ) } >> { os.path.basename( url_new ) }" )
                self.SIGNAL_NAME_URL.emit( url_old, url_new )
            else:
                self.Print_String( f"{ DOCKER_NAME } | ERROR { os.path.basename( url_old ) }" )
    def File_Download( self, url_web, url_new ):
        check_new = url_new != None
        check_exist = os.path.exists( url_new ) == False
        check_web = Check_Html( url_web ) == True
        if check_new and check_exist and check_web:
            qpixmap = Download_QPixmap( url_web )
            if qpixmap != None:
                boolean = qpixmap.save( url_new )
                if boolean == True: self.Print_String( f"{ DOCKER_NAME } | DOWNLOAD { os.path.basename( url_new ) }" )
                else:               self.Print_String( f"{ DOCKER_NAME } | ERROR { os.path.basename( url_web ) }" )


"""
Known Krita Bugs:
- Importing reference with alpha crops image size
- QtCore.qDebug is not able to print non ascii characters on the "Log Viewer" docker.
    file path or name that is not fully ascii can break on print.
    Scripter is able to print those strings though.
- Krita does not allow "Promoted Widgets" so you need to construct the widget via script
- Signals interupt worker progress_bar

Bugs:
- not isn't a searchable word. alternative "!"
- Drive does nothing usefull really

ToDo:
- Grid Selection menu operations: Stitcher
- Send or copy Board from EO to KRA and vice-versa
- qpixmap.createMaskFromColor(  )
- Reference Rebase does not Repalce images

Testes:
- EO file
- KRA file
- new menus for Lock

New:
- Color Picker is a button now
- Color Analyze is inside Color menu
- Grid Mode refactored
- Small Browsing Tweaks
- Footer UI refactor
- Preview Information can expose the compressed file name and the name of the image inside it too
- Drive Tree View Explorer
- Bug Fix: operation Python Script for Keyenter
- watcher permanance fixed
- frame extension shortcut
- better filtering and sorting
- I must warn People: variables names changed delete kritarc
- Overlay Grid Lines
- Overlay Background Color
- Pixelated display ( preview limitation )
- Precache returns and works with a memory size limit
- New Slideshow math and button
- Grid selections
- Display and Openning Folders
- Information improvements
- Theme corrections
- Packer Corrections ( faster packing optimal )
- Reference Board Loads and Saves dont corrupt data by multi access
- Load and Lock buttons react with click and hold click. no RMB required.
- Folder Searches are Abortable
- Reorder Operations: File Rename, Zip Rename and Web Download
- Grid Bookmarks
- Modify images:
    - Fix Images ( Grayscale images are wrong to be sRGB ? )
    - Pre Multiply Images
- Display Bundle files
- Reference now handles its own memory and files
- Send Files to Pigmento Sampler to have a LUT applied to it
"""
