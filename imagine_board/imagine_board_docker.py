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
import sys
import copy
import math
import random
import os
import subprocess
import time
import stat
import webbrowser
import zipfile
import pathlib
import re
import urllib
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Plugin Modules
from .imagine_board_calculations import *
from .imagine_board_extension import ImagineBoard_Extension
from .imagine_board_modulo import (
    ImagineBoard_Preview,
    ImagineBoard_Grid,
    ImagineBoard_Reference,
    Picker_Block,
    Picker_Color_HUE,
    Picker_Color_HSV,
    Function_Process,
    )

#endregion
#region Global Variables

# Plugin
DOCKER_NAME = "Imagine Board"
imagine_board_version = "2025_04_20"

# File Formats
extensions = [
    # Native
    "kra",
    "krz",
    "ora",
    # Static
    "bmp",
    "jpg",
    "jpeg",
    "png",
    "pbm",
    "pgm",
    "ppm",
    "xbm",
    "xpm",
    "tiff",
    "jfif",
    "psd",
    # Vector
    "svg",
    "svgz",
    # Animation
    "gif",
    "webp",
    # Compressed
    "zip",
    ]
# File Sort
file_normal = []
for e in extensions:
    file_normal.append( f"*.{ e }" )
file_backup = []
for e in extensions:
    file_backup.append( f"*.{ e }~" )
# File Type ( Preview )
file_static = []
file_anima = [ "gif", "webp" ]
file_compact = [ "zip" ]
for e in extensions:
    if ( e not in file_anima and e not in file_compact ):
        file_static.append( f"{ e }" )
file_vector = [ "svg", "svgz" ]
file_search = []
for e in extensions:
    if e not in file_compact:
        file_search.append( f"{ e }" )

# Variables
qt_max = 16777215
encode = "utf-8"

#endregion


class ImagineBoard_Docker( DockWidget ):

    #region Initialize

    def __init__( self ):
        super( ImagineBoard_Docker, self ).__init__()

        # Construct
        self.User_Interface()
        self.Variables()
        self.Connections()
        self.Modules()
        self.Style()
        self.Timer()
        self.Extension()
        self.Settings()
        self.Plugin_Load()

    def User_Interface( self ):
        # Window
        self.setWindowTitle( DOCKER_NAME )

        # Operating System
        self.OS = str( QSysInfo.kernelType() ) # WINDOWS=winnt & LINUX=linux
        if self.OS == 'winnt': # Unlocks icons in Krita for Menu Mode
            QApplication.setAttribute( Qt.AA_DontShowIconsInMenus, False )

        # Path Name
        self.directory_plugin = str( os.path.dirname( os.path.realpath( __file__ ) ) )

        # Widget Docker
        self.layout = uic.loadUi( os.path.join( self.directory_plugin, "imagine_board_docker.ui" ), QWidget( self ) )
        self.setWidget( self.layout )

        # Settings
        self.dialog = uic.loadUi( os.path.join( self.directory_plugin, "imagine_board_settings.ui" ), QDialog( self ) )
        self.dialog.setWindowTitle( "Imagine Board : Settings" )

        # Preview Extra Panels Boot
        self.ExtraPanel_Shrink()
        self.LabelPanel_Shrink()

        # Custom Color Picker Dialog
        self.picker = uic.loadUi( os.path.join( self.directory_plugin, "imagine_board_picker.ui" ), QWidget( self ) )
        self.picker.setParent( self )
        self.picker.close()
    def Variables( self ):
        # Pykrita
        self.imagine_pyid = "pykrita_imagine_board_docker"

        # Paths
        self.directory_reference = os.path.join( self.directory_plugin, "REFERENCE" )
        self.directory_code = os.path.join( self.directory_plugin, "CODE" )

        # State
        self.state_load = False
        self.state_inside = False
        self.state_maximized = False

        # UI
        self.mode_index = 0
        self.search = ""

        # Items
        self.sync_list = "Folder" # "Folder" "Reference" "Document"(recent documents)
        self.sync_type = "Normal" # "Normal" "Backup~"
        self.sync_sort = "Local Aware"
        self.search_recursive = False
        self.insert_size = False
        self.insert_scale = 1 # Photobask legacy
        self.scale_method = False
        # Lists
        self.list_folder = []
        self.list_krita = []
        self.list_reference = []
        # Folder
        self.folder_path = None
        self.folder_shift = []
        # Files
        self.file_path = [ None ]
        self.file_qpixmap = [ None ]
        self.file_found = False
        self.file_extension = file_normal
        self.file_sort = QDir.LocaleAware

        # Preview
        self.preview_state = "NULL" # "NULL" "STATIC" "ANIM" "COMPACT"
        self.preview_index = 0
        self.preview_max = 0
        self.preview_playpause = True  # True=Play  False=Pause
        # Preview Slidshow
        self.slideshow_sequence = "Linear" # "Linear" "Random"
        self.slideshow_time = 1000
        self.slideshow_play = False
        self.slideshow_lottery = []
        # Preview Display
        self.preview_display = False

        # Grid
        self.grid_size = 200
        self.grid_fit = False

        # Reference
        self.ref_locked = False
        self.ref_kra = False
        self.ref_import = False
        self.ref_position = [ 1, 1 ]
        self.ref_zoom = 1
        self.ref_board = ""
        self.ref_doc = None
        # Label Picker
        self.picker_mode = None
        self.picker_pen = QColor( 0, 0, 0 )
        self.picker_bg = QColor( 0, 0, 0 )
        self.picker_cancel = QColor( 0, 0, 0 )

        # System
        self.sow_imagine = False
        self.sow_dockers = False
        self.transparent = False

        # Color Picker Module
        self.pigment_o_module = None
        self.pigment_o_pyid = "pykrita_pigment_o_docker"

        # Function>>
        self.function_path_source = None
        self.function_path_destination = None
        self.function_operation = "NONE"
        self.function_string = []
        self.function_keyword = []
        self.function_number = 1
        self.function_python_index = 0
        self.function_python_path = []
        self.function_python_name = []
        self.function_python_script = ""
    def Connections( self ):
        # Extra Connections
        self.layout.extra_playpause.toggled.connect( self.Preview_PlayPause )
        self.layout.extra_back.clicked.connect( self.Preview_Back )
        self.layout.extra_forward.clicked.connect( self.Preview_Forward )
        self.layout.extra_slider.valueChanged.connect( self.Preview_Slider )
        # Label Connections
        self.layout.label_text.clicked.connect( self.Label_Text )
        self.layout.label_font.currentTextChanged.connect( self.Label_Font )
        self.layout.label_letter.valueChanged.connect( self.Label_Letter )
        self.picker.hex_code.returnPressed.connect( self.Picker_HEX )
        self.picker.button_ok.clicked.connect( self.Picker_Ok )
        # Layout Connections
        self.layout.index_slider.valueChanged.connect( self.Index_Slider )
        self.layout.folder.clicked.connect( self.Folder_Open )
        self.layout.slideshow.toggled.connect( self.Preview_SlideShow_Switch )
        self.layout.stop.clicked.connect( self.Reference_Stop_Cycle )
        self.layout.link.toggled.connect( self.Link_KRA )
        self.layout.search.returnPressed.connect( self.Filter_Search )
        self.layout.index_number.valueChanged.connect( self.Index_Number )
        self.layout.settings.clicked.connect( self.Menu_Settings )

        # Dialog Display Item
        self.dialog.sync_list.currentTextChanged.connect( self.Sync_List )
        self.dialog.sync_type.currentTextChanged.connect( self.Sync_Type )
        self.dialog.sync_sort.currentTextChanged.connect( self.Sync_Sort )
        self.dialog.search_recursive.toggled.connect( self.Search_Recursive )
        self.dialog.insert_size.toggled.connect( self.Insert_Size )
        self.dialog.scale_method.toggled.connect( self.Scale_Method )
        # Dialog Display Preview
        self.dialog.slideshow_sequence.currentTextChanged.connect( self.Menu_SlideShow_Sequence )
        self.dialog.slideshow_time.timeChanged.connect( self.Menu_SlideShow_Time )
        self.dialog.preview_display.toggled.connect( self.Preview_Display )
        # Dialog Display Grid
        self.dialog.grid_size.valueChanged.connect( self.Menu_Grid_Size )
        self.dialog.grid_fit.toggled.connect( self.Menu_Grid_Fit )
        # Dialog Display Reference
        self.dialog.ref_import.toggled.connect( self.Menu_Ref_Import )

        # Dialog Function> Path
        self.dialog.function_path_source.textChanged.connect( self.Function_Path )
        self.dialog.function_path_destination.textChanged.connect( self.Function_Path )
        self.dialog.function_run.clicked.connect( self.Function_Run )
        # Dialog Function> Options
        self.dialog.function_operation.currentTextChanged.connect( self.Function_Operation )
        self.dialog.function_string.returnPressed.connect( self.Function_String_Add )
        self.dialog.function_number.valueChanged.connect( self.Function_Number )
        self.dialog.function_keyword.itemPressed.connect( self.Function_String_List )
        self.dialog.function_reset_operation.clicked.connect( self.Function_Reset_Operation )
        self.dialog.function_reset_number.clicked.connect( self.Function_Reset_Number )
        self.dialog.function_reset_string.clicked.connect( self.Function_Reset_String )
        # Dialog Function> Python
        self.dialog.function_python_name.currentIndexChanged.connect( self.Function_Python_Code )
        self.dialog.function_python_script.textChanged.connect( self.Function_Python_Editor )

        # Dialog System Options
        self.dialog.sow_imagine.toggled.connect( self.ShowOnWelcome_Imagine )
        self.dialog.sow_dockers.toggled.connect( self.ShowOnWelcome_Dockers )
        self.dialog.transparent.toggled.connect( self.Menu_Transparent )

        # Notices
        self.dialog.manual.clicked.connect( self.Menu_Manual )
        self.dialog.license.clicked.connect( self.Menu_License )

        # Event Filter Resize
        self.layout.preview_view.installEventFilter( self )
        self.layout.imagine_grid.installEventFilter( self )
        self.layout.reference_view.installEventFilter( self )
        self.dialog.function_drop_run.installEventFilter( self )
        self.layout.footer.installEventFilter( self )
        # Event Filter Others
        self.layout.mode.installEventFilter( self )
        self.layout.folder.installEventFilter( self )
        self.layout.link.installEventFilter( self )
        self.dialog.function_keyword.installEventFilter( self )
        self.picker.installEventFilter( self )
    def Modules( self ):
        #region System

        # Directory
        self.qdir = QDir( self.directory_plugin )
        # File Watcher
        self.file_system_watcher = QFileSystemWatcher( self )
        self.file_system_watcher.directoryChanged.connect( self.Watcher_Display )

        #endregion
        #region Notifier

        self.notifier = Krita.instance().notifier()
        self.notifier.windowCreated.connect( self.Window_Created )

        #endregion
        #region Preview

        self.imagine_preview = ImagineBoard_Preview( self.layout.preview_view )
        self.imagine_preview.Set_FileSearch( file_search )
        # General
        self.imagine_preview.SIGNAL_DRAG.connect( self.Drag_Drop )
        self.imagine_preview.SIGNAL_DROP.connect( self.Drop_Inside )
        # Preview
        self.imagine_preview.SIGNAL_MODE.connect( self.Mode_Index )
        self.imagine_preview.SIGNAL_INCREMENT.connect( self.Preview_Increment )
        # Menu
        self.imagine_preview.SIGNAL_FUNCTION.connect( self.Function_Process )
        self.imagine_preview.SIGNAL_PIN_IMAGE.connect( self.Pin_Image )
        self.imagine_preview.SIGNAL_RANDOM.connect( self.Preview_Random )
        self.imagine_preview.SIGNAL_FULL_SCREEN.connect( self.Screen_Maximized )
        self.imagine_preview.SIGNAL_LOCATION.connect( self.File_Location )
        self.imagine_preview.SIGNAL_ANALYSE.connect( self.Color_Analyse )
        self.imagine_preview.SIGNAL_NEW_DOCUMENT.connect( self.Insert_Document )
        self.imagine_preview.SIGNAL_INSERT_LAYER.connect( self.Insert_Layer )
        self.imagine_preview.SIGNAL_INSERT_REFERENCE.connect( self.Insert_Reference )
        # Extra UI
        self.imagine_preview.SIGNAL_EXTRA_LABEL.connect( self.Preview_Logger )
        self.imagine_preview.SIGNAL_EXTRA_PANEL.connect( self.Preview_ExtraPanel )
        self.imagine_preview.SIGNAL_EXTRA_VALUE.connect( self.Extra_Slider_Value )
        self.imagine_preview.SIGNAL_EXTRA_MAX.connect( self.Extra_Slider_Maximum )

        #endregion
        #region Grid

        self.imagine_grid = ImagineBoard_Grid( self.layout.imagine_grid )
        self.imagine_grid.Set_FileSearch( file_search )
        # General
        self.imagine_grid.SIGNAL_DRAG.connect( self.Drag_Drop )
        self.imagine_grid.SIGNAL_DROP.connect( self.Drop_Inside )
        # Preview
        self.imagine_grid.SIGNAL_MODE.connect( self.Mode_Index )
        self.imagine_grid.SIGNAL_INDEX.connect( self.Preview_Index )
        # Menu
        self.imagine_grid.SIGNAL_FUNCTION.connect( self.Function_Process )
        self.imagine_grid.SIGNAL_PIN_IMAGE.connect( self.Pin_Image )
        self.imagine_grid.SIGNAL_FULL_SCREEN.connect( self.Screen_Maximized )
        self.imagine_grid.SIGNAL_LOCATION.connect( self.File_Location )
        self.imagine_grid.SIGNAL_ANALYSE.connect( self.Color_Analyse )
        self.imagine_grid.SIGNAL_NEW_DOCUMENT.connect( self.Insert_Document )
        self.imagine_grid.SIGNAL_INSERT_LAYER.connect( self.Insert_Layer )
        self.imagine_grid.SIGNAL_INSERT_REFERENCE.connect( self.Insert_Reference )

        #endregion
        #region Reference

        self.imagine_reference = ImagineBoard_Reference( self.layout.reference_view )
        self.imagine_reference.Set_File_Extension( file_normal )
        # General
        self.imagine_reference.SIGNAL_DRAG.connect( self.Drag_Drop )
        self.imagine_reference.SIGNAL_DROP.connect( self.Drop_Inside )
        # Reference
        self.imagine_reference.SIGNAL_PIN_IMAGE.connect( self.Pin_Image )
        self.imagine_reference.SIGNAL_PIN_LABEL.connect( self.Pin_Label )
        self.imagine_reference.SIGNAL_PIN_SAVE.connect( self.Pin_Save )
        self.imagine_reference.SIGNAL_BOARD_SAVE.connect( self.File_Save_St )
        self.imagine_reference.SIGNAL_CAMERA.connect( self.Reference_Camera )
        # Menu
        self.imagine_reference.SIGNAL_LOCKED.connect( self.Reference_Locked )
        self.imagine_reference.SIGNAL_REFRESH.connect( lambda: self.File_Load( self.ref_board ) )
        self.imagine_reference.SIGNAL_FULL_SCREEN.connect( self.Screen_Maximized )
        self.imagine_reference.SIGNAL_LOCATION.connect( self.File_Location )
        self.imagine_reference.SIGNAL_ANALYSE.connect( self.Color_Analyse )
        self.imagine_reference.SIGNAL_NEW_DOCUMENT.connect( self.Insert_Document )
        self.imagine_reference.SIGNAL_INSERT_LAYER.connect( self.Insert_Layer )
        self.imagine_reference.SIGNAL_INSERT_REFERENCE.connect( self.Insert_Reference )
        # UI
        self.imagine_reference.SIGNAL_PB_VALUE.connect( self.Progress_Value )
        self.imagine_reference.SIGNAL_PB_MAX.connect( self.Progress_Max )
        self.imagine_reference.SIGNAL_PACK_STOP.connect( self.Reference_Pack_Stop )
        self.imagine_reference.SIGNAL_LABEL_PANEL.connect( self.Reference_Label )
        self.imagine_reference.SIGNAL_LABEL_INFO.connect( self.Reference_Information )

        #endregion
        #region Panel Color

        self.block_pen = Picker_Block( self.layout.label_pen )
        self.block_pen.Set_Color( QColor( "#e5e5e5" ) )
        self.block_pen.SIGNAL_COLOR.connect( self.Block_Pen )

        self.block_bg = Picker_Block( self.layout.label_bg )
        self.block_bg.Set_Color( QColor( "#191919" ) )
        self.block_bg.SIGNAL_COLOR.connect( self.Block_Bg )

        self.color_hue = Picker_Color_HUE( self.picker.panel_hue )
        self.color_hue.SIGNAL_COLOR.connect( self.Picker_HSV_1 )

        self.color_hsv = Picker_Color_HSV( self.picker.panel_hsv )
        self.color_hsv.SIGNAL_COLOR.connect( self.Picker_HSV_23 )

        #endregion
        #region Function Drop Run

        self.function_process = Function_Process( self.dialog.function_drop_run )
        self.function_process.SIGNAL_DROP.connect( self.Function_Process )

        #endregion
    def Style( self ):
        # Icon Mode
        self.qicon_preview = Krita.instance().icon( "folder-pictures" )
        self.qicon_grid = Krita.instance().icon( "gridbrush" )
        self.qicon_reference = Krita.instance().icon( "zoom-fit" )
        # Icon Packer
        self.qicon_stop_idle = Krita.instance().icon( "showColoringOff" )
        self.qicon_stop_abort = Krita.instance().icon( "snapshot-load" )
        # Icon Animation
        self.qicon_anim_play = Krita.instance().icon( "animation_play" )
        self.qicon_anim_pause = Krita.instance().icon( "animation_pause" )
        # Icon Link
        self.qicon_link_false = Krita.instance().icon( "chain-broken-icon" )
        self.qicon_link_true = Krita.instance().icon( "chain-icon" )
        # Icon Function
        self.qicon_function_run = Krita.instance().icon( "arrow-right" )
        self.qicon_function_disable = Krita.instance().icon( "animation_stop" )

        # Widgets Animation
        self.layout.extra_playpause.setIcon( self.qicon_anim_pause )
        self.layout.extra_back.setIcon( Krita.instance().icon( "prevframe" ) )
        self.layout.extra_forward.setIcon( Krita.instance().icon( "nextframe" ) )
        # Widgets Layout
        self.layout.mode.setIcon( self.qicon_preview )
        self.layout.folder.setIcon( Krita.instance().icon( "document-open" ) )
        self.layout.slideshow.setIcon( Krita.instance().icon( "media-playback-start" ) )
        self.layout.stop.setIcon( self.qicon_stop_idle )
        self.layout.link.setIcon( self.qicon_link_false )
        self.layout.settings.setIcon( Krita.instance().icon( "settings-button" ) )
        # Widget Dialog
        self.dialog.function_run.setIcon( self.qicon_function_disable )

        # ToolTips Layout
        self.layout.mode.setToolTip( "Mode" )
        self.layout.folder.setToolTip( "Open Directory" )
        self.layout.slideshow.setToolTip( "SlideShow Play" )
        self.layout.stop.setToolTip( "Stop" )
        self.layout.link.setToolTip( "Link" )
        self.layout.search.setToolTip( "Search Contents" )
        self.layout.index_number.setToolTip( "Index" )
        self.layout.settings.setToolTip( "Settings" )
        # ToolTips Extra Panel
        self.layout.extra_playpause.setToolTip( "Play / Pause" )
        self.layout.extra_back.setToolTip( "Backwards" )
        self.layout.extra_forward.setToolTip( "Forwards" )
        # ToolTips Label Panel
        self.layout.label_text.setToolTip( "Text" )
        self.layout.label_font.setToolTip( "Font" )
        self.layout.label_letter.setToolTip( "Letter" )
        self.layout.label_pen.setToolTip( "#ffffff" )
        self.layout.label_bg.setToolTip( "#000000" )

        # StyleSheets
        self.layout.extra_panel.setStyleSheet( "#extra_panel{ background-color: rgba( 0, 0, 0, 50 ); }" )
        self.layout.label_panel.setStyleSheet( "#label_panel{ background-color: rgba( 0, 0, 0, 50 ); }" )
        self.layout.progress_bar.setStyleSheet( "#progress_bar{ background-color: rgba( 0, 0, 0, 50 ); }" )
        self.dialog.scroll_area_contents_display.setStyleSheet( "#scroll_area_contents_display{ background-color: rgba( 0, 0, 0, 20 ); }" )
        self.dialog.scroll_area_contents_function.setStyleSheet( "#scroll_area_contents_function{ background-color: rgba( 0, 0, 0, 20 ); }" )
        self.dialog.tab_python.setStyleSheet( "#tab_python{ background-color: rgba( 0, 0, 0, 20 ); }" )
        self.dialog.scroll_area_contents_system.setStyleSheet( "#scroll_area_contents_system{ background-color: rgba( 0, 0, 0, 20 ); }" )
        self.dialog.progress.setStyleSheet( "#progress{ background-color: rgba( 0, 0, 0, 0 ); }" )

        # Function Operations
        self.Combobox_Operations()
        self.Combobox_Code()
    def Timer( self ):
        self.qtimer = QtCore.QTimer( self )
        self.qtimer.timeout.connect( self.Preview_SlideShow_Timer )
    def Extension( self ):
        # Install Extension for Docker
        extension = ImagineBoard_Extension( parent = Krita.instance() )
        Krita.instance().addExtension( extension )
        # Connect Extension Signals
        extension.SIGNAL_BROWSE.connect( self.Shortcut_Browse )
    def Settings( self ):
        #region Layout

        self.mode_index = self.Set_Read( "INT", "mode_index", self.mode_index )
        self.preview_index = self.Set_Read( "INT", "preview_index", self.preview_index )
        self.folder_path = self.Set_Read( "STR", "folder_path", self.folder_path )
        self.search = self.Set_Read( "STR", "search", self.search )

        #endregion
        #region Dialog Display

        # Items
        self.sync_list = self.Set_Read( "STR", "sync_list", self.sync_list )
        self.sync_type = self.Set_Read( "STR", "sync_type", self.sync_type )
        self.sync_sort = self.Set_Read( "STR", "sync_sort", self.sync_sort )
        self.search_recursive = self.Set_Read( "EVAL", "search_recursive", self.search_recursive )
        self.insert_size = self.Set_Read( "EVAL", "insert_size", self.insert_size )
        self.scale_method = self.Set_Read( "EVAL", "scale_method", self.scale_method )
        # Preview
        self.slideshow_sequence = self.Set_Read( "STR", "slideshow_sequence", self.slideshow_sequence )
        self.slideshow_time = self.Set_Read( "INT", "slideshow_time", self.slideshow_time )
        # Grid
        self.grid_size = self.Set_Read( "INT", "grid_size", self.grid_size )
        self.grid_fit = self.Set_Read( "EVAL", "grid_fit", self.grid_fit )
        # Reference
        self.ref_import = self.Set_Read( "EVAL", "ref_import", self.ref_import )

        #endregion
        #region Dialog Function

        self.function_string = self.Set_Read( "EVAL", "function_string", self.function_string  )
        self.preview_display = self.Set_Read( "EVAL", "preview_display", self.preview_display )

        #endregion
        #region Dialog System

        self.sow_imagine = self.Set_Read( "EVAL", "sow_imagine", self.sow_imagine )
        self.sow_dockers = self.Set_Read( "EVAL", "sow_dockers", self.sow_dockers )
        self.transparent = self.Set_Read( "EVAL", "transparent", self.transparent )

        #endregion
        #region Reference

        self.ref_locked = self.Set_Read( "EVAL", "ref_locked", self.ref_locked )
        self.ref_kra = self.Set_Read( "EVAL", "ref_kra", self.ref_kra )
        self.ref_position = self.Set_Read( "EVAL", "ref_position", self.ref_position )
        self.ref_zoom = self.Set_Read( "EVAL", "ref_zoom", self.ref_zoom )
        self.ref_board = self.Set_Read( "STR", "ref_board", self.ref_board )

        #endregion
    def Plugin_Load( self ):
        try:
            self.Loader()
        except Exception as e:
            self.Message_Warnning( "ERROR", f"Load\n{ e }" )
            self.Variables()
            self.Loader()

    def Loader( self ):
        #region Dialog Display

        # Item
        self.dialog.sync_list.setCurrentText( self.sync_list )
        self.dialog.sync_type.setCurrentText( self.sync_type )
        self.dialog.sync_sort.setCurrentText( self.sync_sort )
        self.dialog.search_recursive.setChecked( self.search_recursive )
        self.dialog.insert_size.setChecked( self.insert_size )
        self.dialog.scale_method.setChecked( self.scale_method )
        # Preview
        self.dialog.slideshow_sequence.setCurrentText( self.slideshow_sequence )
        tempo = QTime( 0,0,0 ).addMSecs( self.slideshow_time )
        self.dialog.slideshow_time.setTime( tempo )
        self.dialog.preview_display.setChecked( self.preview_display )
        # Grid
        self.dialog.grid_size.setValue( self.grid_size )
        self.dialog.grid_fit.setChecked( self.grid_fit )
        # Reference
        self.dialog.ref_import.setChecked( self.ref_import )

        #endregion
        #region Dialog Function

        for item in self.function_string:
            self.dialog.function_keyword.addItem( item )

        #endregion
        #region Dialog System

        self.dialog.sow_imagine.setChecked( self.sow_imagine )
        self.dialog.sow_dockers.setChecked( self.sow_dockers )
        self.dialog.transparent.setChecked( self.transparent )

        #endregion
        #region Layout

        # Folder
        self.Folder_Load( self.folder_path, self.preview_index )
        self.layout.search.setText( self.search )

        # Board
        self.layout.link.setChecked( self.ref_kra )

        # Index
        self.Mode_Index( self.mode_index )
        # Reference
        self.imagine_reference.Set_Locked( self.ref_locked )

        #endregion
    def Set_Read( self, mode, entry, default ):
        setting = Krita.instance().readSetting( "Imagine Board", entry, "" )
        if setting == "":
            read = default
        else:
            try:
                if mode == "EVAL":
                    read = eval( setting )
                elif mode == "STR":
                    read = str( setting )
                elif mode == "INT":
                    read = int( setting )
            except:
                read = default
        Krita.instance().writeSetting( "Imagine Board", entry, str( read ) )
        return read

    #endregion
    #region Interface

    # User Interface
    def Mode_Index( self, index ):
        # Variables
        h_bar = 15
        w_icon = 20
        w_number = 180

        # States
        if index == 0:
            self.layout.stacked_widget.setCurrentIndex( 0 )
            self.layout.mode.setIcon( self.qicon_preview )
            self.Footer_Widgets( slider=h_bar, folder=w_icon, slideshow=w_icon, index=w_number )
        if index == 1:
            self.layout.stacked_widget.setCurrentIndex( 1 )
            self.layout.mode.setIcon( self.qicon_grid )
            self.Footer_Widgets( slider=h_bar, folder=w_icon, slideshow=w_icon, index=w_number )
        if index == 2:
            self.layout.stacked_widget.setCurrentIndex( 2 )
            self.layout.mode.setIcon( self.qicon_reference )
            self.Footer_Widgets( stop=w_icon, link=w_icon, search=False, zoom=w_number )

        # update cycle
        if self.mode_index != index:
            self.mode_index = index
            self.Display_Update()
            self.Update_Size()
        # Save
        Krita.instance().writeSetting( "Imagine Board", "mode_index", str( self.mode_index ) )
    def Footer_Widgets( self, slider=0, folder=0, slideshow=0, stop=0, link=0, search=True, index=0, zoom=0 ):
        # Top
        self.layout.index_slider.setMinimumHeight( slider )
        self.layout.index_slider.setMaximumHeight( slider )

        # Icons
        self.layout.folder.setMinimumWidth( folder )
        self.layout.folder.setMaximumWidth( folder )
        self.layout.slideshow.setMinimumWidth( slideshow )
        self.layout.slideshow.setMaximumWidth( slideshow )
        self.layout.stop.setMinimumWidth( stop )
        self.layout.stop.setMaximumWidth( stop )
        self.layout.link.setMinimumWidth( link )
        self.layout.link.setMaximumWidth( link )

        # Middle
        self.layout.search.setEnabled( search )
        self.layout.index_number.setMaximumWidth( index )
        self.layout.zoom.setMaximumWidth( zoom )

        # Update
        self.update()
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
        self.Update_Size()

    # Items
    def Sync_List( self, sync_list ):
        # Checks
        self.sync_list = sync_list
        # Watcher
        if self.sync_list == "Krita":
            self.Recent_Documents( self.list_krita )
        # Display
        if self.state_load == True:
            self.Filter_Search()
        # Finish
        Krita.instance().writeSetting( "Imagine Board", "sync_list", str( self.sync_list ) )
        # self.update()
    def Sync_Type( self, sync_type ):
        # Directory
        self.sync_type = sync_type
        if sync_type == "Normal": self.file_extension = file_normal
        if sync_type == "BackUp~":self.file_extension = file_backup
        # Display
        if self.state_load == True:
            self.Filter_Search()
        # Save
        Krita.instance().writeSetting( "Imagine Board", "sync_type", str( self.sync_type ) )
    def Sync_Sort( self, sync_sort ):
        # Sorting
        self.sync_sort = sync_sort
        if sync_sort == "Local Aware": self.file_sort = QDir.LocaleAware
        if sync_sort == "Name":        self.file_sort = QDir.Name
        if sync_sort == "Time":        self.file_sort = QDir.Time
        if sync_sort == "Size":        self.file_sort = QDir.Size
        if sync_sort == "Type":        self.file_sort = QDir.Type
        if sync_sort == "Unsorted":    self.file_sort = QDir.Unsorted
        if sync_sort == "No Sort":     self.file_sort = QDir.NoSort
        if sync_sort == "Reversed":    self.file_sort = QDir.Reversed
        if sync_sort == "Ignore Case": self.file_sort = QDir.IgnoreCase
        # Display
        if self.state_load == True:
            self.Filter_Search()
        # Save
        Krita.instance().writeSetting( "Imagine Board", "sync_sort", str( self.sync_sort ) )
    def Search_Recursive( self, search_recursive ):
        self.search_recursive = search_recursive
        if self.state_load == True:
            self.Filter_Search()
        Krita.instance().writeSetting( "Imagine Board", "search_recursive", str( self.search_recursive ) )
    def Insert_Size( self, insert_size ):
        self.insert_size = insert_size
        Krita.instance().writeSetting( "Imagine Board", "insert_size", str( self.insert_size ) )
    def Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        if scale_method == False:
            method = Qt.FastTransformation
        if scale_method == True:
            method = Qt.SmoothTransformation
        self.imagine_preview.Set_Scale_Method( method )
        self.imagine_grid.Set_Scale_Method( method )
        self.imagine_reference.Set_Scale_Method( method )
        Krita.instance().writeSetting( "Imagine Board", "scale_method", str( self.scale_method ) )

    # Preview
    def Menu_SlideShow_Sequence( self, slideshow_sequence ):
        self.slideshow_sequence = slideshow_sequence
        Krita.instance().writeSetting( "Imagine Board", "slideshow_sequence", str( self.slideshow_sequence ) )
    def Menu_SlideShow_Time( self, qtime ):
        self.slideshow_time = QTime( 0, 0, 0 ).msecsTo( qtime )
        Krita.instance().writeSetting( "Imagine Board", "slideshow_time", str( self.slideshow_time ) )
    def Preview_Display( self, boolean ):
        self.preview_display = boolean
        self.imagine_preview.Set_Display( self.preview_display )
        Krita.instance().writeSetting( "Imagine Board", "preview_display", str( self.preview_display ) )
    # Grid
    def Menu_Grid_Size( self, value ):
        self.grid_size = value
        self.imagine_grid.Grid_Size( self.grid_size )
        self.Display_Update()
        Krita.instance().writeSetting( "Imagine Board", "grid_size", str( self.grid_size ) )
    def Menu_Grid_Fit( self, boolean ):
        self.grid_fit = boolean
        self.imagine_grid.Grid_Fit( self.grid_fit )
        Krita.instance().writeSetting( "Imagine Board", "grid_fit", str( self.grid_fit ) )
    # Reference
    def Menu_Ref_Import( self, ref_import ):
        self.ref_import = ref_import
        Krita.instance().writeSetting( "Imagine Board", "ref_import", str( self.ref_import ) )

    # Combobox
    def Combobox_Operations( self ):
        self.dialog.function_operation.addItem( "NONE" )
        self.dialog.function_operation.insertSeparator( 1 )
        self.dialog.function_operation.addItem( "KEY_ADD" )
        self.dialog.function_operation.addItem( "KEY_REPLACE" )
        self.dialog.function_operation.addItem( "KEY_REMOVE" )
        self.dialog.function_operation.addItem( "KEY_CLEAN" )
        self.dialog.function_operation.insertSeparator( 6 )
        self.dialog.function_operation.addItem( "RENAME_ORDER" )
        self.dialog.function_operation.addItem( "RENAME_EXTENSION" )
        self.dialog.function_operation.insertSeparator( 9 )
        self.dialog.function_operation.addItem( "SAVE_ORDER" )
        self.dialog.function_operation.addItem( "SAVE_ORIGINAL" )
        self.dialog.function_operation.insertSeparator( 12 )
        self.dialog.function_operation.addItem( "SEARCH_KEY" )
        self.dialog.function_operation.addItem( "SEARCH_NULL" )
        self.dialog.function_operation.addItem( "SEARCH_COPY" )
        self.dialog.function_operation.insertSeparator( 16 )
        self.dialog.function_operation.addItem( "PYTHON_SCRIPT" )
    def Combobox_Code( self ):
        # Files
        qdir = QDir( self.directory_code )
        qdir.setSorting( QDir.LocaleAware )
        qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
        qdir.setNameFilters( [ "*.py" ] )
        python_files = qdir.entryInfoList()

        # ComboBox Construct
        function_python_path = []
        for i in range( 0, len( python_files ) ):
            item = os.path.abspath( python_files[i].filePath() )
            function_python_path.append( item )

        # Replace
        if self.function_python_path != function_python_path:
            # Variables
            self.function_python_path = function_python_path
            # Create Name
            self.dialog.function_python_name.clear()
            for path in self.function_python_path:
                name = os.path.basename( path )
                self.dialog.function_python_name.addItem( name )

            # Editor
            self.Python_Read( self.function_python_path[0] )

    # Show on Welcome
    def ShowOnWelcome_Imagine( self, sow_imagine ):
        self.sow_imagine = sow_imagine
        try:self.setProperty( "ShowOnWelcomePage", sow_imagine )
        except:pass
        Krita.instance().writeSetting( "Imagine Board", "sow_imagine", str( self.sow_imagine ) )
    def ShowOnWelcome_Dockers( self, sow_dockers ):
        self.sow_dockers = sow_dockers
        Krita.instance().writeSetting( "Imagine Board", "sow_dockers", str( self.sow_dockers ) )
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
    # Transparent
    def Menu_Transparent( self, transparent ):
        self.transparent = transparent
        self.Transparent_Shift()
        Krita.instance().writeSetting( "Imagine Board", "transparent", str( self.transparent ) )

    # Transparent
    def Transparent_Shift( self ):
        if self.transparent == True and self.isFloating() == True and self.state_inside == False:
            self.Footer_Scale( False )
            self.setAttribute( Qt.WA_TranslucentBackground, True )
        else:
            self.Footer_Scale( True )
            self.setAttribute( Qt.WA_TranslucentBackground, False )
            self.setAttribute( Qt.WA_NoSystemBackground, False )
        self.update()
    def Footer_Scale( self, boolean ):
        # Progress Bar
        if boolean == True:
            self.layout.progress_bar.setMinimumHeight( 5 )
            self.layout.progress_bar.setMaximumHeight( 5 )
        else:
            self.layout.progress_bar.setMinimumHeight( 0 )
            self.layout.progress_bar.setMaximumHeight( 0 )

        # Slider
        if ( boolean == True and self.mode_index in ( 0, 1 ) ):
            self.layout.index_slider.setMinimumHeight( 15 )
            self.layout.index_slider.setMaximumHeight( 15 )
        else:
            self.layout.index_slider.setMinimumHeight( 0 )
            self.layout.index_slider.setMaximumHeight( 0 )

        # Footer
        if boolean == True:
            self.layout.footer_widget.setMinimumHeight( 25 )
            self.layout.footer_widget.setMaximumHeight( 25 )
        else:
            self.layout.footer_widget.setMinimumHeight( 0 )
            self.layout.footer_widget.setMaximumHeight( 0 )

        # Update
        self.Update_Size()

    # Progress Bar
    def Progress_Value( self, value ):
        self.layout.progress_bar.setValue( value )
    def Progress_Max( self, value ):
        self.layout.progress_bar.setMaximum( value )

    # Dialogs
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
        # Updates
        self.Combobox_Code()
    def Menu_Manual( self ):
        url = "https://github.com/EyeOdin/imagine_board/wiki"
        webbrowser.open_new( url )
    def Menu_License( self ):
        url = "https://github.com/EyeOdin/imagine_board/blob/main/LICENSE"
        webbrowser.open_new( url )

    # Menu
    def Menu_Mode_Press( self, event ):
        # Menu
        qmenu = QMenu( self )
        # Actions
        cmenu_preview = qmenu.addAction( "Preview" )
        cmenu_grid = qmenu.addAction( "Grid" )
        cmenu_reference = qmenu.addAction( "Reference" )
        # Icons
        cmenu_preview.setIcon( self.qicon_preview )
        cmenu_grid.setIcon( self.qicon_grid )
        cmenu_reference.setIcon( self.qicon_reference )

        # Execute
        geo = self.layout.mode.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.footer_widget.mapToGlobal( qpoint )
        action = qmenu.exec_( position )
        # Triggers
        if action == cmenu_preview:
            self.Mode_Index( 0 )
        if action == cmenu_grid:
            self.Mode_Index( 1 )
        if action == cmenu_reference:
            self.Mode_Index( 2 )
    def Menu_Mode_Wheel( self, event ):
        increment = 0
        value = 20
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            delta_y = delta.y()
            if delta_y > value:
                increment = -1
            if delta_y < -value:
                increment = 1
            if ( increment == -1 or increment == 1 ):
                new_index = Limit_Range( self.mode_index + increment, 0, 2 )
                if self.mode_index != new_index:
                    self.Mode_Index( new_index )

    # Widgets
    def Clear_Focus( self ):
        self.layout.search.clearFocus()
        self.layout.index_number.clearFocus()
        self.layout.label_font.clearFocus()
        self.layout.label_letter.clearFocus()
    def Widget_Enable( self, boolean ):
        self.layout.setEnabled( boolean )
    def Update_Size( self ):
        # Variables
        ps = self.layout.preview_view.size()
        gs = self.layout.imagine_grid.size()
        rs = self.layout.reference_view.size()
        ds = self.dialog.function_drop_run.size()
        self.state_maximized = self.isMaximized()

        # Modules
        self.imagine_preview.Set_Size( ps.width(), ps.height(), self.state_maximized )
        self.imagine_grid.Set_Size( gs.width(), gs.height(), self.state_maximized )
        self.imagine_reference.Set_Size( rs.width(), rs.height(), self.state_maximized )
        self.function_process.Set_Size( ds.width(), ds.height() )

        # Color Picker Swatches
        self.block_pen.Set_Size( self.layout.label_pen.width(), self.layout.label_pen.height() )
        self.block_bg.Set_Size( self.layout.label_bg.width(), self.layout.label_bg.height() )
        # Color Picker Location
        if self.picker.isVisible() == True:
            self.Picker_Geometry()
    def Update_Size_Display( self ):
        width = self.width()
        height = self.height()
        self.Message_Log( "SIZE", f"{ width } x { height }" )

    #endregion
    #region Management

    # Communication
    def Message_Log( self, operation, message ):
        string = f"Imagine Board | { operation } { message }"
        try:QtCore.qDebug( string )
        except:pass
    def Message_Warnning( self, operation, message ):
        string = f"Imagine Board | { operation } { message }"
        QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )
    def Message_Float( self, operation, message, icon ):
        ki = Krita.instance()
        string = f"Imagine Board | { operation } { message }"
        ki.activeWindow().activeView().showFloatingMessage( string, ki.icon( icon ), 5000, 0 )

    # Import Modules
    def Import_Pigment_O( self ):
        try:
            dockers = Krita.instance().dockers()
            for d in dockers:
                if d.objectName() == self.pigment_o_pyid:
                    self.pigment_o_module = d
                    break
        except:
            self.pigment_o_module = None
        self.imagine_preview.Set_Pigment_O( self.pigment_o_module )
        self.imagine_grid.Set_Pigment_O( self.pigment_o_module )
        self.imagine_reference.Set_Pigment_O( self.pigment_o_module )

    # String
    def Path_Components( self, path ):
        directory = os.path.dirname( path ) # dir
        basename = os.path.basename( path ) # name.ext
        extension = os.path.splitext( path )[1] # .ext
        n = basename.find( extension )
        base = basename[:n] # name
        return directory, basename, extension, base
    def File_Extension( self, path ):
        if path == None:
            extension = None
        else:
            extension = pathlib.Path( path ).suffix
            extension = extension.replace( ".", "" )
        return extension

    # Lists
    def Recent_Documents( self, list_old ):
        # Krita Read
        recent_doc = krita.Krita.instance().recentDocuments()
        recent_doc.sort()
        # List
        list_new = []
        for rd in recent_doc:
            if rd != "":
                list_new.append( rd )
        if len( list_new ) != len( list_old ):
            self.list_krita = list_new
            if self.state_load == True and self.sync_list == "Krita":
                self.Filter_Search()

    # Internet
    def Download_QPixmap( self, url ):
        data = self.Download_Data( url )
        try:
            qpixmap = QPixmap()
            qpixmap.loadFromData( data )
        except:
            qpixmap = None
        return qpixmap
    def Download_Data( self , url ):
        try:
            request = urllib.request.Request( url, headers={ "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5" } )
            response = urllib.request.urlopen( request )
            data = response.read()
        except:
            data = None
        return data
    def Check_Html( self, url ):
        boolean = False
        result = urllib.parse.urlparse( url )
        scheme = result.scheme
        if scheme == "https":
            boolean = True
        return boolean

    # Bytes
    def Bytes_QPixmap( self, qpixmap ):
        extension = "PNG" # "PNG" "JPG"
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer( ba )
        buffer.open( QtCore.QIODevice.WriteOnly )
        ok = qpixmap.save( buffer, extension )
        assert ok
        pixmap_bytes = ba.data()
        return pixmap_bytes
    def Bytes_Python( self, path ):
        with open( path, "rb" ) as f:
            data = f.read()
        return data

    #endregion
    #region Signals

    # File
    def File_Location( self, image_path ):
        kernel = str( QSysInfo.kernelType() ) # WINDOWS=winnt & LINUX=linux
        if kernel == "winnt": # Windows
            FILEBROWSER_PATH = os.path.join( os.getenv( 'WINDIR' ), 'explorer.exe' )
            subprocess.run( [ FILEBROWSER_PATH, '/select,', image_path ] )
        elif kernel == "linux": # Linux
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( image_path ) ) )
        elif kernel == "darwin": # MAC
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( image_path ) ) )
        else:
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( image_path ) ) )
        self.Message_Log( "FILE LOCATION", f"{ image_path }" )

    # Mouse Stylus
    def Drop_Inside( self, lista ):
        if len( lista ) > 0:
            # Variables
            item = lista[0]
            # Check Source
            check_html = self.Check_Html( item )
            if check_html == True:
                self.Preview_Internet( item )
            else:
                # Checks
                item = os.path.abspath( item )
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
                if self.folder_path != directory:
                    self.Folder_Load( directory, 0 )
                self.Preview_String( basename )
    def Drag_Drop( self, image_path, clip ):
        # New Documents only consider the path so it excludes clip
        qimage = self.Image_Clip( image_path, clip )
        check_vector = image_path.endswith( tuple( file_vector ) )
        if check_vector == True:
            # Read SVG
            svg_shape = ""
            file_item = open( image_path, "r", encoding="UTF-8" )
            for line in file_item:
                svg_shape += line
            # Drag and Drop
            if svg_shape != "":
                # Clipboard
                clipboard = QApplication.clipboard().setText( svg_shape )
                # MimeData
                mimedata = QMimeData()
                url = QUrl().fromLocalFile( image_path )
                mimedata.setUrls( [ url ] )
                mimedata.setText( svg_shape )
                mimedata.setImageData( qimage )
                # Thumbnail
                self.Drag_Thumbnail( qimage, mimedata )
        else:
            if qimage.isNull() == False:
                # Clipboard
                clipboard = QApplication.clipboard().setImage( qimage )
                # MimeData
                mimedata = QMimeData()
                url = QUrl().fromLocalFile( image_path )
                mimedata.setUrls( [ url ] )
                mimedata.setText( image_path )
                mimedata.setImageData( qimage )
                # Thumbnail
                self.Drag_Thumbnail( qimage, mimedata )
    def Drag_Thumbnail( self, qimage, mimedata ):
        # Display
        size = 200
        thumb = QPixmap().fromImage( qimage )
        if thumb.isNull() == False:
            thumb = thumb.scaled( size, size, Qt.KeepAspectRatio, Qt.FastTransformation )
        # Drag
        drag = QDrag( self )
        drag.setMimeData( mimedata )
        drag.setPixmap( thumb )
        drag.setHotSpot( QPoint( int( thumb.width() * 0.5 ), int( thumb.height() * 0.5 ) ) )
        drag.exec( Qt.CopyAction )

    # Insert
    def Insert_Document( self, image_path, clip ):
        if image_path not in ( "", None ):
            # Create Document
            ki = Krita.instance()
            document = ki.openDocument( image_path )
            Application.activeWindow().addView( document )
            w = document.width()
            h = document.height()
            # Crop
            if clip["cstate"] == True:
                ad = Krita.instance().activeDocument()
                ad.crop( int( w * clip["cl"] ), int( h * clip["ct"] ), int( w * clip["cw"] ), int( h * clip["ch"] ) )
                ad.waitForDone()
                ad.refreshProjection()
                Krita.instance().action('reset_display').trigger()
            # Show Message
            self.Message_Float( "INSERT", "New Document", "document-new" )
        else:
            self.Message_Float( "REPORT", "Null Image", "broken-preset" )
    def Insert_Layer( self, image_path, clip ):
        if image_path not in ( "", None ) and ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            check_vector = image_path.endswith( tuple( file_vector ) )
            if check_vector == True:
                self.Insert_Vector( image_path )
            else:
                self.Insert_Pixel( image_path, clip )
        else:
            self.Message_Float( "REPORT", "Null Image", "broken-preset" )
    def Insert_Reference( self, image_path, clip ):
        if image_path not in ( "", None ) and ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            # Image
            qimage = self.Image_Clip( image_path, clip )
            if qimage.isNull() == False:
                # MimeData
                mimedata = QMimeData()
                url = QUrl().fromLocalFile( image_path )
                mimedata.setUrls( [ url ] )
                mimedata.setImageData( qimage )
                mimedata.setData( image_path, image_path.encode() )
                # Clipboard
                clipboard = QApplication.clipboard().setMimeData( mimedata )
                # Place Image
                Krita.instance().action( 'paste_as_reference' ).trigger()
                Krita.instance().activeDocument().refreshProjection()
                # Message
                self.Message_Float( "INSERT", "Reference", "krita_tool_reference_images" )
            else:
                self.Message_Float( "REPORT", "Null Image", "broken-preset" )
        else:
            self.Message_Float( "REPORT", "Null Image", "broken-preset" )
    def Insert_Vector( self, image_path ):
        report = "Vector"
        try:
            # Variables
            basename = os.path.basename( image_path )
            # Read SVG
            svg_shape = ""
            file_item = open( image_path, "r", encoding="UTF-8" )
            for line in file_item:
                svg_shape += line
            # Create Layer
            ad = Krita.instance().activeDocument()
            rn = ad.rootNode()
            vl = ad.createVectorLayer( basename )
            rn.addChildNode( vl, None )
            # Input Shape to Layer
            vl.addShapesFromSvg( svg_shape )
        except Exception as e:
            report = e
        self.Message_Float( "INSERT", report, "vectorLayer" )
    def Insert_Pixel( self, image_path, clip ):
        report = "Pixel"
        try:
            # Variables
            basename = os.path.basename( image_path )
            # Create Layer
            ad = Krita.instance().activeDocument()
            rn = ad.rootNode()
            pl = ad.createNode( basename, "paintLayer" )
            rn.addChildNode( pl, None )
            # Qimage Data
            qimage = self.Image_Clip( image_path, clip )
            ptr = qimage.constBits()
            ptr.setsize( qimage.byteCount() )
            pl.setPixelData( bytes( ptr.asarray() ), 0, 0, qimage.width(), qimage.height() )
            ad.refreshProjection()
        except Exception as e:
            report = e
        self.Message_Float( "INSERT", report, "paintLayer" )
    def Image_Clip( self, image_path, clip ):
        qimage = QImage( image_path )
        if qimage.isNull() == False:
            if clip["cstate"] == True:
                w = qimage.width()
                h = qimage.height()
                qimage = qimage.copy( int( w * clip["cl"] ), int( h * clip["ct"] ), int( w * clip["cw"] ), int( h * clip["ch"] ) )
            if ( self.insert_size == False ) and ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
                ad = Krita.instance().activeDocument()
                iw = ad.width()
                ih = ad.height()
            else:
                size = max( qimage.size().width(), qimage.size().height() )
                iw = size
                ih = size
            qimage = qimage.scaled( iw * self.insert_scale, ih * self.insert_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation )
        return qimage

    # Color
    def Color_Analyse( self, qimage ):
        if ( self.pigment_o_module != None and qimage.isNull() == False ):
            report = self.pigment_o_module.API_Image_Analyse( qimage )
            self.Message_Log( "ANALYSE", f"{ report }" )
        else:
            self.Message_Log( "ERROR", "Pigment.O not present" )

    # Extension
    def Shortcut_Browse( self, browse ):
        if self.mode_index == 0:
            self.Preview_Increment( browse )
        if self.mode_index == 1:
            self.Grid_Increment( browse )
        if self.mode_index == 2:
            self.Reference_Increment( browse )

    #endregion
    #region API

    def API_Preview_QPixmap( self, qpixmap ):
        # UI Extra Panels
        self.ExtraPanel_Shrink()
        self.LabelPanel_Shrink()
        # Set Image to Render ( ignores "animation" and "compressed" )
        self.imagine_preview.Display_QPixmap( qpixmap )

    def Imagine_Sample_Script( self ):
        """
        import krita

        pyid = "pykrita_imagine_board_docker"
        dockers = Krita.instance().dockers()
        for i in range( 0, len( dockers ) ):
            if dockers[i].objectName() == pyid:
                imagine_board = dockers[i]
                break
        imagine_board.API_Preview_QPixmap( qpixmap )
        """

    #endregion
    #region Files

    def Folder_Menu( self, event ):
        if self.folder_path == None:
            self.Folder_Open()
        else:
            # Menu
            qmenu = QMenu( self )
            qmenu.setMinimumWidth( 8 * len( self.folder_path ) )

            # Title
            qmenu.addSection( self.folder_path )
            # Parent Dir
            parent = f"🖿 { os.path.basename( os.path.dirname( self.folder_path ) ) }"
            cmenu_parent = qmenu.addAction( parent )
            qmenu.addSection( " " )
            # Child Dirs
            actions = {}
            for i in range( 0, len( self.folder_shift ) ):
                child = f"⮩ { os.path.basename( self.folder_shift[i] ) }"
                actions[i] = qmenu.addAction( child )

            # Execute
            geo = self.layout.folder.geometry()
            qpoint = geo.bottomLeft()
            position = self.layout.icon_buttons.mapToGlobal( qpoint )
            action = qmenu.exec_( position )

            # Triggers
            path = None
            if action == cmenu_parent:
                path = os.path.dirname( self.folder_path )
            for i in range( 0, len( self.folder_shift ) ):
                if action == actions[i]:
                    path = str( self.folder_shift[i] )
                    break
            # Emit
            if path != None:
                self.Folder_Load( path, 0 )
    def Folder_Shift( self, directory ):
        self.folder_shift = []
        dir_list = os.listdir( directory )
        path_list = map( lambda name: os.path.join( directory, name ), dir_list )
        for path in path_list:
            if os.path.isdir( path ):
                self.folder_shift.append( path )
        if len( self.folder_shift ) > 0:
            self.folder_shift.sort()

    def Folder_Open( self ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        folder_path = file_dialog.getExistingDirectory( self, "Select Directory", self.folder_path )
        if folder_path not in [ "", ".", None ]:
            self.Folder_Load( folder_path, 0 )
    def Folder_Load( self, folder_path, index ):
        try:
            exists = os.path.exists( folder_path )
            if exists == True:
                # Variables
                self.folder_path = folder_path
                self.slideshow_lottery.clear()
                # UI
                string = f"Folder : { os.path.basename( self.folder_path ) }"
                self.layout.folder.setToolTip( string )
                # Operation
                self.Filter_Keywords( self.search, index )
                self.Folder_Shift( folder_path )
                self.Watcher_Update()
        except:
            self.folder_path = ""
        # Save
        Krita.instance().writeSetting( "Imagine Board", "folder_path", str( self.folder_path ) )

    def Filter_Search( self ):
        self.search = self.layout.search.text().lower()
        self.Filter_Keywords( self.search, 0 )
        Krita.instance().writeSetting( "Imagine Board", "search", str( self.search ) )
    def Filter_Keywords( self, search, index ):
        try:
            # Time Watcher
            start = QtCore.QDateTime.currentDateTimeUtc()

            # Lists
            active_list = self.sync_list.upper()
            if self.sync_list == "Folder":
                # Variables
                active_location = os.path.basename( self.folder_path )
                # Files
                self.qdir.setPath( self.folder_path )
                self.qdir.setSorting( self.file_sort )
                self.qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
                self.qdir.setNameFilters( self.file_extension )
                # Recursive Files
                if self.search_recursive == True:
                    files = list()
                    it = QDirIterator( self.folder_path, QDirIterator.Subdirectories )
                    while( it.hasNext() ):
                        file_path = it.filePath()
                        ext = f"*{ os.path.splitext( file_path )[1] }"
                        if ext in self.file_extension:
                            files.append( it.fileInfo() )
                        it.next()
                else:
                    files = self.qdir.entryInfoList()
                # Variables
                count = len( files )
            elif self.sync_list == "Krita":
                # Variables
                active_location = None
                # Files
                files = []
                for doc in self.list_krita:
                    files.append( doc )
                files = self.Filter_Sort( files, self.sync_sort )
                count = len( files )
            elif self.sync_list == "Reference":
                # Variables
                active_location = None
                # Files
                files = []
                for pin in self.list_reference:
                    path = pin["path"]
                    web = pin["web"]
                    if path != None:
                        files.append( pin["path"] )
                    elif web != None:
                        files.append( pin["web"] )
                files = self.Filter_Sort( files, self.sync_sort )
                count = len( files )
            else:
                active_list = None
                active_location = None
                files = []
                count = 0

            # Progress Bar
            self.Progress_Value( 0 )
            self.Progress_Max( count )

            # Keywords
            keywords = []
            remove = []
            elements = r'[0-9A-Za-z\\/|!"#$%&()=?@£§{[\]\}\'«»,;.:-_çºª¨´~^*-+]+'
            words = re.findall( elements, search )
            try:
                n = words.index( "not" )
                keywords = words[:n]
                remove = words[n+1:]
            except:
                keywords = words
            len_key = len( keywords )
            len_rem = len( remove )

            # Search Cycle
            path_new = []
            for i in range( 0, count ):
                # Progress Bar
                self.Progress_Value( i + 1 )

                # Variables
                item = files[i]
                if self.sync_list in ( "Krita", "Reference" ):
                    fn = os.path.basename( item ).lower()
                    fp = os.path.abspath( item )
                else:
                    fn = item.fileName().lower()
                    fp = os.path.abspath( item.filePath() )
                # Logic
                if ( len_key == 0 and len_rem == 0 ):
                    path_new.append( fp )
                else:
                    # Variables
                    check_add = False
                    check_rem = False
                    # Add
                    for key in keywords:
                        if key in fn:
                            check_add = True
                            break
                    # Remove
                    for rem in remove:
                        if rem in fn:
                            check_rem = True
                            break
                    # Operation
                    if ( check_add == True and check_rem == False ):
                        path_new.append( fp )

            # Variables
            self.file_path.clear()
            self.file_path = copy.deepcopy( path_new )
            self.preview_max = len( path_new )
            if len( path_new ) > 0:
                self.file_found = True
                self.Index_Range( 1, self.preview_max )
            else:
                self.file_found = False
                self.Index_Range( 0, 0 )

            # Reset Display
            index_type = type( index )
            if index_type is int:
                self.Preview_Index( index )
            elif index_type is str:
                self.Preview_String( index )

            # Update List and Display
            self.Display_Update()

            # Progress Bar
            self.Progress_Value( 0 )
            self.Progress_Max( 1 )

            # Time Watcher
            end = QtCore.QDateTime.currentDateTimeUtc()
            delta = start.msecsTo( end )
            time = QTime( 0,0 ).addMSecs( delta )
            self.Message_Log( "FILTER", f"{ time.toString( 'hh:mm:ss.zzz' ) } | { active_list } { active_location } | SEARCH { search }" )
        except Exception as e:
            self.Filter_Null()
    def Filter_Null( self ):
        self.Index_Range( 0, 0 )
        self.Index_Values( 0 )
    def Filter_Sort( self, files, sort ):
        # Variables
        boolean = False
        order = []
        # Descrimination
        for i in range( 0, len( files ) ):
            path = files[i]
            if sort == "Name":
                name = os.path.basename( path )
                item = [ name, path ]
            elif sort == "Time":
                boolean = True
                time = os.path.getmtime( path )
                item = [ time, path ]
            elif sort == "Size":
                boolean = True
                size = os.path.getsize( path )
                item = [ size, path ]
            elif sort == "Type":
                tipo = os.path.splitext( path )[1]
                item = [ tipo, path ]
            else:
                item = [ i, path ]
            order.append( item )
        order.sort( reverse=boolean )
        # Clean List
        for i in range( 0, len( order ) ):
            files[i] = order[i][1]
        # Return
        return files

    #endregion
    #region Display

    def Display_Update( self ):
        self.Display_Sync()
        self.Display_Preview()
        self.Display_Grid()
        self.Display_Reference()

    def Display_Sync( self ):
        Krita.instance().writeSetting( "Imagine Board", "preview_index", str( self.preview_index ) )
    def Display_Preview( self ):
        if self.mode_index == 0:
            # UI Extra Panel
            self.Preview_ExtraPanel( False )
            self.layout.extra_slider.setEnabled( False )
            self.Extra_PlayPause_Enable( False )

            # Display
            if self.file_found == True:
                # Variables
                image_path = self.file_path[ self.preview_index ]
                extension = self.File_Extension( image_path )
                # Display Preview
                if extension in file_anima:
                    self.preview_state = "ANIM"
                    self.Extra_PlayPause_Enable( True )
                    self.imagine_preview.Display_Animation( image_path )
                    self.Preview_Play()
                elif extension in file_compact:
                    self.preview_state = "COMPACT"
                    self.layout.extra_slider.setEnabled( True )
                    self.imagine_preview.Display_Compact( image_path )
                else:
                    self.preview_state = "STATIC"
                    self.imagine_preview.Display_Path( image_path )
            else:
                self.preview_state = "NULL"
                self.imagine_preview.Display_Default()
    def Display_Grid( self ):
        if self.mode_index == 1:
            # Display
            if self.file_found == True:
                self.imagine_grid.Display_Path( self.file_path, self.preview_index )
            else:
                self.imagine_grid.Display_Default()
    def Display_Reference( self ):
        if self.mode_index == 2:
            pass

    #endregion
    #region Index

    # Widgets
    def Index_Block( self, boolean ):
        self.layout.index_slider.blockSignals( boolean )
        self.layout.index_number.blockSignals( boolean )
    def Index_Range( self, minimum, maximum ):
        # Slider
        self.layout.index_slider.setMinimum( minimum )
        self.layout.index_slider.setMaximum( maximum )
        # Number
        self.layout.index_number.setMinimum( minimum )
        self.layout.index_number.setMaximum( maximum )
        self.layout.index_number.setSuffix( f":{ maximum }" )
    def Index_Values( self, value ):
        self.Index_Block( True )
        self.layout.index_slider.setValue( value + 1 )
        self.layout.index_number.setValue( value + 1 )
        self.Index_Block( False )
    def Index_Slider( self, value ):
        self.Index_Block( True )
        self.preview_index = value - 1 # Humans start at 1 and script starts at 0
        self.layout.index_number.setValue( value )
        if self.file_found == True:
            self.Display_Update()
        self.Index_Block( False )
    def Index_Number( self, value ):
        self.Index_Block( True )
        self.preview_index = value - 1 # Humans start at 1 and script starts at 0
        self.layout.index_slider.setValue( value )
        if self.file_found == True:
            self.Display_Update()
        self.Index_Block( False )

    #endregion
    #region Preview

    # Preview Operations
    def Preview_Increment( self, increment ):
        if self.file_found == True:
            if self.preview_state == "COMPACT":
                if increment < 0:
                    self.imagine_preview.Comp_Back()
                if increment > 0:
                    self.imagine_preview.Comp_Forward()
            else:
                index = Limit_Range( self.preview_index + increment, 0, self.preview_max - 1 )
                self.Preview_Index( index )
    def Preview_Index( self, index ):
        if ( self.file_found == True and self.preview_index != index ):
            self.preview_index = Limit_Range( index, 0, self.preview_max )
            self.Index_Values( index )
            self.Display_Update()
    def Preview_String( self, file_name ):
        if ( self.file_found == True and file_name != None ):
            for i in range( 0, len( self.file_path ) ):
                path = self.file_path[i]
                basename = os.path.basename( path )
                if basename == file_name:
                    self.Preview_Index( i )
                    break
    def Preview_Random( self ):
        random_value = self.preview_index
        while random_value == self.preview_index:
            random_value = Random_Range( self.preview_max - 1 )
        self.Preview_Index( random_value )
    def Preview_Internet( self, url ):
        qpixmap = self.Download_QPixmap( url )
        if qpixmap != None:
            self.Mode_Index( 0 )
            self.imagine_preview.Display_QPixmap( qpixmap )

    # SlideShow
    def Preview_SlideShow_Switch( self, slideshow_play ):
        self.slideshow_play = slideshow_play
        if self.slideshow_play == True:
            # UI
            self.layout.slideshow.setIcon( Krita.instance().icon( 'media-playback-stop' ) )
            self.layout.slideshow.setToolTip( "SlideShow Stop" )
            # Timer
            self.qtimer.start( self.slideshow_time )
        else:
            # UI
            self.layout.slideshow.setIcon( Krita.instance().icon( 'media-playback-start' ) )
            self.layout.slideshow.setToolTip( "SlideShow Play" )
            # Timer
            self.qtimer.stop()
    def Preview_SlideShow_Timer( self ):
        if self.slideshow_sequence == "Linear":
            index = Limit_Loop( self.preview_index + 1, self.preview_max - 1 )
            self.Preview_Index( index )
        if self.slideshow_sequence == "Random":
            # Clear for a full Cycle
            if len( self.slideshow_lottery ) == self.preview_max:
                self.slideshow_lottery.clear()
            # Lottery Random
            while True:
                number = random.randint( 0, self.preview_max - 1 )
                if number not in self.slideshow_lottery:
                    self.slideshow_lottery.append( number )
                    self.Preview_Index( number )
                    break

    # Extra Interface
    def Preview_ExtraPanel( self, boolean ):
        if self.mode_index == 0 and boolean == True:
            value = qt_max
        else:
            value = 0
        self.layout.extra_panel.setMaximumHeight( value )
    def ExtraPanel_Shrink( self ):
        # Container
        self.layout.extra_panel.setMaximumHeight( 0 )
        # Widgets
        self.layout.extra_slider.setEnabled( False )
    # Extra Slider
    def Extra_PlayPause_Enable( self, boolean ):
        self.layout.extra_playpause.setEnabled( boolean )
        self.layout.extra_playpause.setChecked( False )
        self.layout.extra_playpause.setIcon( self.qicon_anim_play )
    def Extra_Slider_Value( self, value ):
        self.layout.extra_slider.blockSignals( True )
        self.layout.extra_slider.setValue( value )
        self.layout.extra_slider.blockSignals( False )
    def Extra_Slider_Maximum( self, value ):
        self.layout.extra_slider.setMaximum( value )

    # Animation & Compact
    def Preview_Play( self ):
        if self.preview_state == "ANIM":
            self.layout.extra_playpause.setChecked( False )
    def Preview_PlayPause( self, preview_playpause ):
        if self.preview_state == "ANIM":
            self.preview_playpause = preview_playpause
            if preview_playpause == True: # Paused
                self.layout.extra_playpause.setIcon( self.qicon_anim_pause )
                self.Preview_Enable( True )
                self.imagine_preview.Anim_Pause()
            if preview_playpause == False: # Playing
                self.layout.extra_playpause.setIcon( self.qicon_anim_play )
                self.Preview_Enable( False )
                self.imagine_preview.Anim_Play()
    def Preview_Enable( self, boolean ):
            self.layout.extra_back.setEnabled( boolean )
            self.layout.extra_forward.setEnabled( boolean )
            self.layout.extra_slider.setEnabled( boolean )
    def Preview_Back( self ):
        if self.preview_state == "ANIM":
            self.imagine_preview.Anim_Back()
        if self.preview_state == "COMPACT":
            self.imagine_preview.Comp_Back()
    def Preview_Forward( self ):
        if self.preview_state == "ANIM":
            self.imagine_preview.Anim_Forward()
        if self.preview_state == "COMPACT":
            self.imagine_preview.Comp_Forward()
    def Preview_Slider( self, value ):
        if self.preview_state == "ANIM":
            self.imagine_preview.Anim_Frame( value )
        if self.preview_state == "COMPACT":
            self.imagine_preview.Comp_Index( value )
    def Preview_Logger( self, string ):
        self.layout.extra_label.setText( string )

    #endregion
    #region Grid

    def Grid_Increment( self, increment ):
        self.imagine_grid.Grid_Increment( increment )

    #endregion
    #region Reference

    # Reference Operations
    def Reference_Locked( self, ref_locked ):
        self.ref_locked = ref_locked
        # Save
        Krita.instance().writeSetting( "Imagine Board", "ref_locked", str( self.ref_locked ) )
    def Reference_Increment( self, increment ):
        pass

    # Pin
    def Pin_Image( self, pin, clip ):
        image_path = pin["image_path"]
        check_html = self.Check_Html( image_path )

        if check_html == True:
            clip[ "cstate" ] = False
            self.Pin_Insert( tipo="image", bx=pin["bx"], by=pin["by"], text=None, path=None, web=image_path, clip=clip )
        else:
            self.Pin_Insert( tipo="image", bx=pin["bx"], by=pin["by"], text=None, path=image_path, web=None, clip=clip )
    def Pin_Label( self, pin ):
        clip_none = { "cstate":False, "cl":0, "cr":0, "cw":1, "ch":1 }
        self.Pin_Insert( tipo="label", bx=pin["bx"], by=pin["by"], text="Text", path=None, web=None, clip=clip_none )
    def Pin_Insert( self, tipo, bx, by, text, path, web, clip ):
        # Variables
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

        # Image
        if tipo == "image" and path != None:
            path = os.path.abspath( path )
            qpixmap = QPixmap( path )
            if qpixmap.isNull() == False:
                # Size
                width = int( qpixmap.width() )
                height = int( qpixmap.height() )
                # Clip
                qpixmap = qpixmap.copy( int(width*cl), int(height*ct), int(width*cw), int(height*ch) )
                # Size
                width = int( qpixmap.width() )
                height = int( qpixmap.height() )
        if tipo == "image" and web != None:
            qpixmap = self.Download_QPixmap( web )
            try:
                width = int( qpixmap.width() )
                height = int( qpixmap.height() )
            except:
                self.Message_Warnning( "ERROR", "access failed")
        # Label
        if tipo == "label":
            qpixmap = None
            width = 200
            height = 100

        # Valid Reference Pin
        if ( width > 0 and height > 0 ):
            # Fit
            if ( tipo == "image" and self.ref_import == False ):
                side = 200
                fx = side / width
                fy = side / height
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
            br = int( bx + w2 )
            bt = int( by - h2 )
            bb = int( by + h2 )
            bw = int( abs( br - bl ) )
            bh = int( abs( bb - bt ) )

            # ID
            index = len( self.list_reference )
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
            pen = self.color_1.name()
            bg = self.color_2.name()
            # QPixmap & Draw
            if tipo == "image":
                draw = qpixmap.scaled( int( bw * self.ref_zoom ), int( bh * self.ref_zoom ), Qt.IgnoreAspectRatio, Qt.FastTransformation )
            else:
                qpixmap = None
                draw = None
            zdata = None

            # PIN
            pin = {
                # ID
                "index"      : index, # integer
                # Type
                "tipo"      : tipo, # string ("image" "label")
                # State
                "render"     : render, # bool
                "active"     : active, # bool
                "select"     : select, # bool
                "pack"       : pack, # bool
                # Transform
                "trz"        : rotation_z, # float
                "tsk"        : scale_constant, # float ( diameter of circle )
                "tsw"        : scale_width, # float ( width with no rotation )
                "tsh"        : scale_height, # float ( height with no rotation )
                # Bound Box
                "bx"         : bx, # float ( center x )
                "by"         : by, # float ( center y )
                "bl"         : bl, # float ( left )
                "br"         : br, # float ( right )
                "bt"         : bt, # float ( top )
                "bb"         : bb, # float ( bottom )
                "bw"         : bw, # float ( width )
                "bh"         : bh, # float ( height )
                # Clip
                "cstate"     : cstate, # bool
                "cl"         : cl, # float
                "ct"         : ct, # float
                "cw"         : cw, # float
                "ch"         : ch, # float
                # Dimensions
                "area"       : area, # float
                "perimeter"  : perimeter, # float
                "ratio"      : ratio, # float
                # Edits
                "egs"        : edit_grayscale, # bool
                "efx"        : edit_flip_x, # bool
                "efy"        : edit_flip_y, # bool
                # Text
                "text"       : text, # string
                "font"       : font, # string
                "letter"     : letter, # integer
                "pen"        : pen, # string
                "bg"         : bg, # string
                # Pixmap
                "path"       : path, # string
                "web"        : web, # string
                "qpixmap"    : qpixmap, # QPixmap
                "draw"       : draw, # QPixmap
                "zdata"      : zdata, # string of bytes
                }

            # Emit
            self.imagine_reference.Pin_Insert( pin )

            # Garbage
            del qpixmap, draw, pin
    def Pin_Save( self, qpixmap ):
        # File Dialog
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        file_path = file_dialog.getSaveFileName( self, "Save Pin Location", "", "File( *.png *.jpg *.jpeg *.bmp *.ppm *.xpm *.xbm )" )[0]
        if file_path not in [ "", ".", None ]:
            qpixmap.save( file_path )

    # Menu
    def Reference_Menu( self, event ):
        #region Variables

        # Title
        path = self.ref_board
        if path not in [ "", ".", None]:
            name = ( os.path.basename( path ) ).split( "." )[0]
            file_path = f" [ { name } ]"
        else:
            file_path = ""
        # KRA Document available
        ad = Krita.instance().activeDocument()
        if ad not in [ "", ".", None]:
            basename = os.path.basename( ad.fileName() )
            link_doc = f" [ { basename } ]"
            check_krita = basename.endswith( ( "kra", "krz" ) ) == True
        else:
            link_doc = ""
            check_krita = False

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )

        # File
        menu_file = qmenu.addMenu( f"File{ file_path }" )
        action_file_new = menu_file.addAction( "New" )
        action_file_open = menu_file.addAction( "Open" )
        action_file_save_as = menu_file.addAction( "Save As" )
        action_file_export = menu_file.addAction( "Export" )
        action_file_download = menu_file.addAction( "Download" )
        # Color
        menu_link = qmenu.addMenu( f"Link{ link_doc }" )
        action_link_load = menu_link.addAction( "Load" )
        action_link_save = menu_link.addAction( "Save" )

        # Disable General
        if ( link_doc == None or check_krita == False ):
            menu_link.setEnabled( False )

        #endregion
        #region Action

        # Mapping
        geo = self.layout.link.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.icon_buttons.mapToGlobal( qpoint )
        action = qmenu.exec_( position )

        # File
        if action == action_file_new:
            self.File_New()
        if action == action_file_open:
            self.File_Open()
        if action == action_file_save_as:
            self.File_Save_As()
        if action == action_file_export:
            self.File_Export()
        if action == action_file_download:
            self.File_Download()

        # Link
        if action == action_link_load:
            self.Link_Load()
        if action == action_link_save:
            self.Link_Save()

        #endregion

    # File
    def File_Load( self, path ):
        # Board
        if os.path.exists( path ) == True:
            self.EO_Load( path )
        else:
            self.ref_board = ""
        self.Data_Kritarc()
        # Variables
        self.state_load = True
    def File_Save_St( self, list_reference ):
        if self.state_load == True:
            # Variabels
            self.list_reference = list_reference
            # Save
            self.EO_Save( self.ref_board )
            self.Data_Kritarc()
    def File_New( self ):
        ref_board = self.Dialog_Save( "New File Location", "board_000000" )
        if ref_board != None:
            self.ref_board = ref_board
            self.imagine_reference.Board_Clear()
        self.Data_Kritarc()
    def File_Open( self ):
        ref_board = self.Dialog_Load( "Open File Location" )
        if ref_board != None:
            self.EO_Load( ref_board )
        self.Data_Kritarc()
    def File_Save_As( self ):
        ref_board = self.Dialog_Save( "Save File Location", "board_000000" )
        if ref_board != None:
            self.ref_board = ref_board
            self.EO_Save( self.ref_board )
        self.Data_Kritarc()
    def File_Export( self ):
        export_path = self.Dialog_Save( "Export File Location", "export_000000" )
        self.EO_Export( export_path )
    def File_Download( self ):
        download_folder = self.Dialog_Directory( "Download Folder Location" )
        if download_folder not in [ "", ".", None ]:
            for item in self.list_reference:
                tipo = item["tipo"]
                qpixmap = item["qpixmap"]
                if tipo == "image":
                    # Variables
                    path = item["path"]
                    web = item["web"]
                    if path != None:
                        qpixmap = QPixmap( path )
                        name = os.path.basename( path )
                        save_path = os.path.join( download_folder, name )
                    if web != None:
                        qpixmap = self.Download_QPixmap( web )
                        name = os.path.split( urllib.parse.urlparse( web ).path )[1]
                        save_path = os.path.join( download_folder, name )
                    # Save
                    if os.path.exists( save_path ) == False:
                        qpixmap.save( save_path )
                    else:
                        self.Message_Log( "ERROR", f"Path already exists { save_path }" )

    # Dialog
    def Dialog_Load( self, title ):
        if self.ref_board in [ "", ".", None ]:
            directory = self.directory_reference
        else:
            directory = self.ref_board
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        file_path = file_dialog.getOpenFileName( self, title, directory, "File( *.eo )" )[0]
        if file_path in [ "", ".", None ]:
            file_path = None
        return file_path
    def Dialog_Save( self, title, name ):
        # Variabels
        directory = self.directory_reference
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            file_name = Krita.instance().activeDocument().fileName()
            directory = os.path.dirname( file_name )
            basename = os.path.basename( file_name )
            name = os.path.splitext( basename )[0]
        directory = os.path.join( directory, f"{ name }.eo")
        # File Dialog
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        file_path = file_dialog.getSaveFileName( self, title, directory, "File( *.eo )" )[0]
        if file_path in [ "", ".", None ]:
            file_path = None
        return file_path
    def Dialog_Directory( self, title ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        folder_path = file_dialog.getExistingDirectory( self, title, "" )
        if folder_path in [ "", ".", None ]:
            folder_path = None
        return folder_path
    # EO file
    def EO_Load( self, path ):
        if ( path not in [ "", ".", None ] and os.path.exists( path ) == True ):
            with open( path, "r", encoding=encode ) as f:
                board = f.readlines()
                self.Data_Load( board, path )
    def EO_Save( self, path ):
        if path not in [ "", ".", None ]:
            data = self.Data_Save()
            with open( path, "w", encoding=encode ) as f:
                f.write( data )
    def EO_Export( self, path ):
        if path not in [ "", ".", None ]:
            data = self.Data_Export()
            with open( path, "w", encoding=encode ) as f:
                f.write( data )

    # Link
    def Link_KRA( self, boolean ):
        self.ref_kra = boolean
        if boolean == False:
            self.layout.link.setIcon( self.qicon_link_false )
        if boolean == True:
            self.layout.link.setIcon( self.qicon_link_true )
            self.Link_Live()
        Krita.instance().writeSetting( "Imagine Board", "ref_kra", str( self.ref_kra ) )
    def Link_Live( self ):
        if self.ref_kra == True:
            try:
                ref_doc = Krita.instance().activeDocument().fileName()
                if ( self.ref_doc != ref_doc ) or ( self.ref_doc == None ):
                    self.ref_doc = ref_doc
                    self.Link_Load()
            except:
                pass
    def Link_Load( self ):
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            doc = Krita.instance().activeDocument()
            annotation = doc.annotation( "Imagine Board" )
            decode = bytes( annotation ).decode( encode )
            board = decode.split( "\n" )
            self.Data_Load( board, self.ref_board )
    def Link_Save( self ):
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            data = self.Data_Save()
            doc = Krita.instance().activeDocument()
            doc.setAnnotation( 'Imagine Board', "Document", QByteArray( data.encode() ) )
            doc.save()

    # Data
    def Data_Load( self, board, ref_board ):
        # Variables
        count = len( board )
        # Progress Bar
        self.Progress_Value( 0 )
        self.Progress_Max( count )
        # Construct Board
        lista = []
        ref_zoom = 1
        ref_position = [ 0.5, 0.5 ]
        if len( board ) > 0:
            if board[0].startswith( "Imagine Board" ) == True:
                for i in range( 1, count ):
                    try:
                        # Progress Bar
                        self.Progress_Value( i )
                        QApplication.processEvents()
                        # Formating
                        line = board[i]
                        if line.endswith("\n") == True:
                            line = line[:-1]
                        # Evaluation
                        if line == "connect": # Export
                            self.ref_board = ref_board
                        elif line.startswith( "ref_position=" ) == True: # Camera Position
                            n = len( "ref_position=" )
                            ref_position = eval( line[n:] )
                        elif line.startswith( "ref_zoom=" ) == True: # Camera Scale
                            n = len( "ref_zoom=" )
                            ref_zoom = float( line[n:] )
                        else: # Pin
                            line = eval( line )
                            # Clip
                            cl = line["cl"]
                            ct = line["ct"]
                            cw = line["cw"]
                            ch = line["ch"]
                            # QPixmap
                            path = line["path"]
                            url = line["web"]
                            zdata = line["zdata"]
                            # Load
                            if path != None: # Local
                                qpixmap = QPixmap( path )
                            elif url != None: # Internet
                                qpixmap = self.Download_QPixmap( url )
                            elif zdata != None: # Import
                                qpixmap = QPixmap()
                                qpixmap.loadFromData( zdata )
                            # Clip
                            if qpixmap.isNull() == False:
                                w = qpixmap.width()
                                h = qpixmap.height()
                                qpixmap = qpixmap.copy( int(w*cl), int(h*ct), int(w*cw), int(h*ch) )
                                line["qpixmap"] = qpixmap
                            lista.append( line )
                    except:
                        pass
        if len( lista ) > 0:
            # Preview & Grid
            self.list_reference = lista
            if self.sync_list != "Folder":
                self.Filter_Search()
            # Reference
            self.imagine_reference.Board_Insert( lista )
            self.imagine_reference.Set_Camera( ref_position, ref_zoom )
        # Progress Bar
        self.Progress_Value( 0 )
        self.Progress_Max( 1 )
    def Data_Save( self ):
        # Header
        data = "Imagine Board"
        # Type of save
        data += f"\nconnect"
        # Camera
        data += f"\nref_position={ self.ref_position }"
        data += f"\nref_zoom={ self.ref_zoom }"
        for item in self.list_reference:
            # Clean
            item["qpixmap"] = None
            item["draw"] = None
            item["zdata"] = None
            # String
            data += f"\n{ item }"
        return data
    def Data_Export( self ):
        # Header
        data = "Imagine Board"
        # Type of save
        data += f"\ndata"
        # Camera
        data += f"\nref_position={ self.ref_position }"
        data += f"\nref_zoom={ self.ref_zoom }"
        for item in self.list_reference:
            # ZData
            path = item["path"]
            web = item["web"]
            if path != None:
                item["zdata"] = self.Bytes_Python( path )
            elif web != None:
                item["zdata"] = self.Download_Data( web )
            else:
                item["zdata"] = None
            # Clean
            item["qpixmap"] = None
            item["draw"] = None
            # String
            data += f"\n{ item }"
        return data
    def Data_Kritarc( self ):
        self.imagine_reference.Set_File_Path( self.ref_board )
        Krita.instance().writeSetting( "Imagine Board", "ref_board", str( self.ref_board ) )

    # Label Operations
    def Reference_Label( self, boolean ):
        if boolean == True:
            value = qt_max
        else:
            value = 0
        self.layout.label_panel.setMaximumHeight( value )
    def LabelPanel_Shrink( self ):
        self.layout.label_panel.setMaximumHeight( 0 )
    def Reference_Information( self, info ):
        # Variables
        info_text = info["text"]
        info_font = info["font"]
        info_letter = info["letter"]
        info_pen = info["pen"]
        info_bg = info["bg"]
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
        self.block_pen.Set_Color( QColor( info_pen ) )
        self.block_bg.Set_Color( QColor( info_bg ) )
        # Signals
        self.layout.label_font.blockSignals( False )
        self.layout.label_letter.blockSignals( False )
        self.layout.label_pen.blockSignals( False )
        self.layout.label_bg.blockSignals( False )
    def Label_Text( self ):
        previous = self.imagine_reference.Get_Label_Infomation()
        if previous != None:
            string, ok = QInputDialog.getMultiLineText( self, "Imagine Board", "Input Text", previous["text"] )
            if ( ok == True and string != None ):
                self.imagine_reference.Set_Label_Text( string )
    def Label_Font( self, font ):
        self.imagine_reference.Set_Label_Font( font )
    def Label_Letter( self, letter ):
        self.imagine_reference.Set_Label_Letter( letter )

    # Packer
    def Reference_Pack_Stop( self, boolean ):
        if boolean == True:
            self.layout.stop.setIcon( self.qicon_stop_abort )
        elif boolean == False:
            self.layout.stop.setIcon( self.qicon_stop_idle )
    def Reference_Stop_Cycle( self ):
        self.imagine_reference.Set_Stop_Cycle()

    # Camera
    def Reference_Camera( self, ref_position, ref_zoom, len_board ):
        # Variables
        self.ref_position = ref_position
        self.ref_zoom = ref_zoom
        # Interface
        self.layout.zoom.setText( f"z{ ref_zoom }:{ len_board }" )
        # Save
        Krita.instance().writeSetting( "Imagine Board", "ref_position", str( self.ref_position ) )
        Krita.instance().writeSetting( "Imagine Board", "ref_zoom", str( self.ref_zoom ) )

    #endregion
    #region Color Picker

    def Block_Pen( self, qcolor ):
        self.picker_pen = qcolor
        self.picker_cancel = qcolor
        self.Picker_Show( qcolor, "PEN" )
    def Block_Bg( self, qcolor ):
        self.picker_bg = qcolor
        self.picker_cancel = qcolor
        self.Picker_Show( qcolor, "BG" )
    def Picker_Show( self, qcolor, mode ):
        if self.picker.isVisible() == False:
            # Variabels
            self.picker_mode = mode
            # Interface
            self.Picker_Geometry()
            self.picker.show()
            # Modules
            self.color_hue.Set_Color( qcolor )
            self.color_hsv.Set_Color( qcolor )
            self.picker.hex_code.setText( qcolor.name() )
        else:
            self.picker_mode = None
            self.picker.close()

    def Picker_Geometry( self ):
        # Read
        label = self.layout.label_panel.geometry()
        panel = self.picker.geometry()
        # Variables
        ly = label.y()
        lw = label.width()
        pw = panel.width()
        ph = panel.height()
        # Calculations
        gx = lw * 0.5 - pw * 0.5
        gy = ly - ph - 10
        # Update
        self.picker.setGeometry( int( gx ), int( gy ), int( pw ), int( ph ) )
    def Picker_Cancel( self ):
        # Interface
        self.picker.close()
        # Modules
        if self.picker_mode == "PEN":
            self.picker_pen = self.picker_cancel
            self.block_pen.Set_Color( self.picker_cancel )
        if self.picker_mode == "BG":
            self.picker_bg = self.picker_cancel
            self.block_bg.Set_Color( self.picker_cancel )
        hex_code = self.picker_cancel.name()
        self.picker.hex_code.setText( hex_code )
        # Apply
        self.Picker_Apply( hex_code )
        # Variables
        self.picker_mode = None

    def Picker_HSV_1( self, qcolor ):
        # Variables
        if self.picker_mode == "PEN":
            self.picker_pen = qcolor
        if self.picker_mode == "BG":
            self.picker_bg = qcolor
        hex_code = qcolor.name()
        # Modules
        self.color_hsv.Set_Color( qcolor )
        self.picker.hex_code.setText( hex_code )
        # Apply
        self.Picker_Apply( hex_code )
    def Picker_HSV_23( self, qcolor ):
        # Variables
        if self.picker_mode == "PEN":
            self.picker_pen = qcolor
        if self.picker_mode == "BG":
            self.picker_bg = qcolor
        hex_code = qcolor.name()
        # Modules
        self.color_hue.Set_Color( qcolor )
        self.picker.hex_code.setText( hex_code )
        # Apply
        self.Picker_Apply( hex_code )

    def Picker_HEX( self ):
        hex_code = self.picker.hex_code.text()
        qcolor = QColor( hex_code )
        if self.picker_mode == "PEN":
            self.picker_pen = qcolor
            self.block_pen.Set_Color( qcolor )
        if self.picker_mode == "BG":
            self.picker_bg = qcolor
            self.block_bg.Set_Color( qcolor )
        self.picker.hex_code.setText( hex_code )
        # Apply
        self.Picker_Apply( hex_code )
    def Picker_Ok( self ):
        if self.picker_mode == "PEN":
            self.picker_cancel = self.picker_pen
        if self.picker_mode == "BG":
            self.picker_cancel = self.picker_bg

    def Picker_Apply( self, hex_code ):
        if self.picker_mode == "PEN":
            self.layout.label_pen.setToolTip( hex_code )
            self.imagine_reference.Set_Label_Pen( hex_code )
        if self.picker_mode == "BG":
            self.layout.label_bg.setToolTip( hex_code )
            self.imagine_reference.Set_Label_Bg( hex_code )

    #endregion
    #region Function>>

    def Function_Module( self ):
        # Variables
        string = self.function_operation
        if string == "NONE":
            string = ""
        # Modules
        self.imagine_preview.Set_Function( string )
        self.imagine_grid.Set_Function( string )
        self.imagine_reference.Set_Function( string )

    def Function_Path( self ):
        # Read
        source = self.dialog.function_path_source.text()
        destination = self.dialog.function_path_destination.text()
        # Exists
        exist_source = os.path.exists( source )
        exist_destination = os.path.exists( destination )
        # Logic
        if exist_source == True:self.function_path_source = source
        else:self.function_path_source = None
        if exist_destination == True:self.function_path_destination = destination
        else:self.function_path_destination = None
        # UI
        if ( exist_source == True and ( exist_destination == True or destination == "" ) ):
            self.dialog.function_run.setEnabled( True )
            self.dialog.function_run.setIcon( self.qicon_function_run )
        else:
            self.dialog.function_run.setEnabled( False )
            self.dialog.function_run.setIcon( self.qicon_function_disable )
    def Function_Run( self ):
        # Variable
        file_list = []
        # Checks
        check_dir = os.path.isdir( self.function_path_source )
        check_file = os.path.isfile( self.function_path_source )
        # Logic
        if check_dir == True:
            # Search Directory
            qdir = QDir( self.function_path_source )
            qdir.setSorting( self.file_sort )
            qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            qdir.setNameFilters( self.file_extension )
            files = qdir.entryInfoList()
            # List Path
            for item in files:
                file_list.append( item.filePath() )
        if check_file == True:
            file_list.append( self.function_path_source )
        # Process
        if len( file_list ) > 0:
            self.Function_Process( file_list )

    def Function_Operation( self, operation ):
        # Variables
        self.function_operation = operation
        # Modules
        self.Function_Module()
        # Requirements
        request = ""
        if ( "ORIGINAL" not in operation and "CLEAN" not in operation ):
            if operation.startswith( ( "KEY", "RENAME", "SAVE" ) ) == True:
                request += "S"
            if ( "ORDER" in operation or "COPY" in operation ):
                request += " N"
        if "PYTHON" in operation:
            request += "PY"
        self.dialog.function_reset_operation.setText( request )
    def Function_Number( self, number ):
        self.function_number = number

    def Function_String_Context( self, event ):
        qmenu = QMenu( self )
        action_clear = qmenu.addAction( "Clear Selection" )
        action = qmenu.exec_( self.dialog.function_keyword.mapToGlobal( event.pos() ) )
        if action == action_clear:
            self.Function_String_Clear()
    def Function_String_Add( self ):
        # String Widget
        item = self.dialog.function_string.text().lower().replace( " ", "_" )
        self.dialog.function_string.clear()
        # Keyword Widget
        self.dialog.function_keyword.addItem( item )
        # Variable
        self.Function_String_List()
    def Function_String_Clear( self ):
        # String Widget
        self.dialog.function_string.clear()
        # Keyword Widget
        remove_list = self.dialog.function_keyword.selectedItems()
        for rem in remove_list:
            count = self.dialog.function_keyword.count()
            for i in range( 0, count ):
                if self.dialog.function_keyword.item( i ) == rem:
                    self.dialog.function_keyword.takeItem( i )
                    break
        # Variable
        self.Function_String_List()
    def Function_String_List( self ):
        # Selected Items
        self.function_keyword = []
        keyword_list = self.dialog.function_keyword.selectedItems()
        for keyword in keyword_list:
            self.function_keyword.append( keyword.text() )
        # All Items
        self.function_string = []
        count = self.dialog.function_keyword.count()
        for i in range( 0, count ):
            string = self.dialog.function_keyword.item( i ).text()
            self.function_string.append( string )
        Krita.instance().writeSetting( "Imagine Board", "function_string", str( self.function_string ) )

    def Function_Python_Code( self, index ):
        # Variables
        self.function_python_index = index
        # Editor
        py_path = self.function_python_path[index]
        self.Python_Read( py_path )
    def Python_Read( self, py_path ):
        self.dialog.function_python_script.clear()
        with open( py_path, encoding=encode ) as f:
            read_data = f.read()
            self.dialog.function_python_script.setPlainText( read_data )
            self.function_python_script = read_data
    def Function_Python_Editor( self ):
        self.function_python_script = self.dialog.function_python_script.toPlainText()

    def Function_Process( self, file_list ):
        # Run Process
        if ( len( file_list ) > 0 and self.function_operation != "NONE" ):
            thread = True
            if thread == False:self.Function_Single_Start( file_list )
            if thread == True:self.Function_Thread_Start( file_list )
    def Function_Single_Start( self, file_list ):
        self.worker_function = Worker_Function()
        self.worker_function.run(
            self,
            "SINGLE",
            self.function_path_source,
            self.function_path_destination,
            file_list,
            self.function_operation,
            self.function_number,
            self.function_keyword,
            self.function_python_script,
            )
    def Function_Thread_Start( self, file_list ):
        # Thread
        self.thread_function = QThread()
        # Worker
        self.worker_function = Worker_Function()
        self.worker_function.moveToThread( self.thread_function )
        # Thread
        self.thread_function.started.connect( lambda : self.worker_function.run(
            self,
            "THREAD",
            self.function_path_source,
            self.function_path_destination,
            file_list,
            self.function_operation,
            self.function_number,
            self.function_keyword,
            self.function_python_script,
            ) )
        self.thread_function.start()
    def Function_Thread_Quit( self ):
        self.thread_function.quit()
        self.update()

    # Resets
    def Function_Reset_Operation( self ):
        self.dialog.function_operation.setCurrentIndex( 0 )
    def Function_Reset_Number( self ):
        self.dialog.function_number.setValue( 1 )
    def Function_Reset_String( self ):
        self.dialog.function_keyword.clear()

    #endregion
    #region Watcher

    def Watcher_Display( self ):
        try:
            image_path = self.file_path[ self.preview_index ]
            self.Filter_Keywords( self.search, image_path )
        except Exception as e:
            if self.state_load == True:
                self.Filter_Search()

    def Watcher_State( self, boolean ):
        # Blocks Imagine Board from updating to changes to the Directory while Function>> works
        if boolean == False: # Stop
            self.Watcher_Remove()
        if boolean == True: # Start
            self.Watcher_Add()
    def Watcher_Update( self ):
        self.Watcher_Remove()
        self.Watcher_Add()

    def Watcher_Remove( self ):
        directories = self.file_system_watcher.directories()
        files = self.file_system_watcher.files()
        paths_clean = []
        for d in range( 0, len( directories ) ):
            paths_clean.append( directories[d] )
        for f in range( 0, len( files ) ):
            paths_clean.append( files[f] )
        if len( paths_clean ) > 0:
            self.file_system_watcher.removePaths( paths_clean )
    def Watcher_Add( self ):
        # Variables
        path_list = []

        # Add Folder Path
        folder = self.folder_path
        if folder != "":
            path_list.append( folder )

        # Add Recent Documents
        for path in self.list_krita:
            dirname = os.path.dirname( path )
            if ( dirname != folder and path not in path_list ):
                path_list.append( path )

        # Watch these Files
        for path in path_list:
            exists = os.path.exists( path )
            if exists == True:
                self.file_system_watcher.addPath( path )

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
        # Start Position
        self.Theme_Changed()

    def View_Changed( self ):
        # Lists
        self.Recent_Documents( self.list_krita )
        # Reference
        self.Link_Live()
    def Theme_Changed( self ):
        # Krita Theme
        theme_value = QApplication.palette().color( QPalette.Window ).value()
        if theme_value > 128:
            self.color_1 = QColor( "#191919" )
            self.color_2 = QColor( "#e5e5e5" )
        else:
            self.color_1 = QColor( "#e5e5e5" )
            self.color_2 = QColor( "#191919" )
        # Update
        self.imagine_preview.Set_Theme( self.color_1, self.color_2 )
        self.imagine_grid.Set_Theme( self.color_1, self.color_2 )
        self.imagine_reference.Set_Theme( self.color_1, self.color_2 )
        self.function_process.Set_Theme( self.color_1, self.color_2 )
    def Window_Closed( self ):
        pass

    #endregion
    #region Widget Events

    def showEvent( self, event ):
        # Dockers
        self.Welcome_Dockers()
        # Pigmento Module
        self.Import_Pigment_O()

        # Reference
        if self.state_load == False:
            # QTimer
            start_up = QtCore.QTimer( self )
            start_up.setSingleShot( True )
            start_up.timeout.connect( lambda: self.File_Load( self.ref_board ) )
            start_up.start( 3000 )
    def moveEvent( self, event ):
        if self.state_maximized != self.isMaximized():
            self.Update_Size()
    def resizeEvent( self, event ):
        # self.Update_Size_Display()
        self.Update_Size()
    def enterEvent( self, event ):
        # Variables
        self.state_inside = True
        # Widget
        self.Transparent_Shift()
        # Update
        self.update()
    def leaveEvent( self, event ):
        # Variables
        self.state_inside = False
        # Widgets
        self.Clear_Focus()
        self.Transparent_Shift()
        self.update()
    def closeEvent( self, event ):
        # Variables
        self.pigment_o_module = None
        # Lists
        self.Function_String_List()
        # Threads
        try:
            self.thread_function.quit()
        except:
            pass

    def eventFilter( self, source, event ):
        # Widgets
        widgets = [
            self.layout.preview_view,
            self.layout.imagine_grid,
            self.layout.reference_view,
            self.layout.footer,
            self.dialog.function_drop_run,
            ]
        if ( event.type() == QEvent.Resize and source in widgets ):
            self.Update_Size()
            return True

        # Mode
        if ( event.type() == QEvent.MouseButtonPress and source is self.layout.mode ):
            self.Menu_Mode_Press( event )
            return True
        if ( event.type() == QEvent.Wheel and source is self.layout.mode ):
            self.Menu_Mode_Wheel( event )
            return True

        # Folder
        if ( event.type() == QEvent.ContextMenu and source is self.layout.folder ):
            self.Folder_Menu( event )
            return True
        # Link
        if ( event.type() == QEvent.ContextMenu and source is self.layout.link ):
            self.Reference_Menu( event )
            return True

        # Lists
        if ( event.type() == QEvent.ContextMenu and source is self.dialog.function_keyword ):
            self.Function_String_Context( event )
            return True
        if ( event.type() == QEvent.Leave and source is self.dialog.function_keyword ):
            self.Function_String_List()
            return True

        # Picker
        if ( event.type() == QEvent.Leave and source is self.picker ):
            self.Picker_Cancel()
            return True

        return super().eventFilter( source, event )

    def canvasChanged( self, canvas ):
        pass

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
    if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
        pass
    """

    """
    found_qpixmap = qpixmap.scaled( self.tn_size, self.tn_size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation )
    """

    """
    mime_data = sorted( mime_data, key=lambda d: d['name'] )
    """

    """
    reader = QImageReader( folder_files )
    if reader.canRead() == True:
        image_path.append( folder_files )
    del reader
    """

    """
    OS.PATH notes
    - Exists os.path.samefile( path1, path2 ) for the Function when applying changes
    - Directory and Name os.path.split( path )
    - Extension os.path.splitext( f )
    """

    """
    sql = f"SELECT DISTINCT {column} FROM {ref_table};"
    """

    """
    # Screen
    screen = QtWidgets.QDesktopWidget().screenGeometry( 0 ) # Size of monitor zero 0
    screen_width = screen.width()
    screen_height = screen.height()
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
    qimage.convertToFormat( QImage.Format_RGBA8888 )
    """

    """
    # Scale Pins
    fx = board_w / self.ww
    fy = board_h / self.hh
    factor = 1 / ( max( fx, fy ) * self.cz )
    for i in range( 0, count ):
        self.Scale_Factor( self.pin_list, i, nx, ny, factor )
        self.Pin_Draw_QPixmap( self.pin_list, i )
    """

    """
    qwindow = Krita.instance().activeWindow().qwindow()
    central = qwindow.centralWidget()
    index = central.currentIndex()
    central.currentChanged.connect( self.Link_Clear )
    """

    """
    zdata = self.Bytes_QPixmap( qpixmap )
    zdata = self.Bytes_Python( path )
    """

    #endregion

class Worker_Function( QObject ):

    #region Run
    # Run Function operation to files in Batch ( KEY ENTER = name number [ keyword ].ext )

    def run( self, source, mode, path_source, path_destination, file_list, operation, number, keyword, python_script ):
        # Variables
        self.source = source
        self.path_source = path_source
        self.path_destination = path_destination
        file_total = len( file_list )

        # Anchor
        try:self.anchor_path = self.source.file_path[ self.source.preview_index ]
        except:self.anchor_path = None
        self.anchor_new = None

        # Modules
        self.qfile = QFile()
        self.qdir = QDir()

        # Operation spacing
        try:QtCore.qDebug( "" )
        except:pass

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # Progress Bar
        self.source.dialog.progress.setValue( 0 )
        self.source.dialog.progress.setMaximum( file_total )

        # Operation Cycle
        self.source.Watcher_State( False )
        self.Cycle_Operation( file_total, file_list, operation, number, keyword, python_script )
        self.source.Watcher_State( True )

        # Progress Bar
        self.source.dialog.progress.setValue( 0 )
        self.source.dialog.progress.setMaximum( 1 )

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo( end )
        time = QTime( 0,0 ).addMSecs( delta )
        try:QtCore.qDebug( f"Imagine Board | FUNCTION>> { time.toString( 'hh:mm:ss.zzz' ) } | OPERATION { str( operation ).lower() }" )
        except:pass

        # Update
        self.source.Filter_Keywords( self.source.search, self.anchor_new )

        # Stop Worker
        if mode == "THREAD":source.Function_Thread_Quit()

    #endregion
    #region Cycle

    def Cycle_Operation( self, file_total, file_list, operation, number, keyword, python_script ):
        # Variables
        collection = []
        found = 0

        # Operation Type
        if ( "KEY" in operation ) or ( "RENAME" in operation ) or ( operation == "SEARCH_NULL" ) or ( operation == "SEARCH_COPY" ):
            operation_type = "rename"
        if "SAVE" in operation:
            operation_type = "save"

        # Operation
        if operation == "KEY_ADD":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Key_Add( path, keyword )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        if operation == "KEY_REPLACE":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Key_Replace( path, keyword )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        if operation == "KEY_REMOVE":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Key_Remove( path, keyword )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        if operation == "KEY_CLEAN":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Key_Clean( path )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        # Rename
        if operation == "RENAME_ORDER":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                numi = number + i
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Rename_Order( path, keyword, numi )
                self.source.dialog.function_number.setValue( numi + 1 )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        if operation == "RENAME_EXTENSION":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                numi = number + i
                path = file_list[i]
                path_new = None
                # New String
                path_new = self.String_Rename_Extension( path, keyword, numi )
                self.source.dialog.function_number.setValue( numi + 1 )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        # Save
        if self.path_destination != None:
            if operation == "SAVE_ORDER":
                for i in range( 0, file_total ):
                    # Variables
                    index = i + 1
                    numi = number + i
                    path = file_list[i]
                    path_new = None
                    # New String
                    path_new = self.String_Save_Order( path, keyword, numi )
                    self.source.dialog.function_number.setValue( numi + 1 )
                    self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
            if operation == "SAVE_ORIGINAL":
                for i in range( 0, file_total ):
                    # Variables
                    index = i + 1
                    path = file_list[i]
                    path_new = None
                    # New String
                    keyword = os.path.basename( path )
                    path_new = self.String_Save_Original( path, keyword )
                    self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        # Search
        if operation == "SEARCH_KEY":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                key = self.String_Search_Key( path )
                if key != None:
                    collection.extend( key )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )

            # Collection
            collection = list( set( collection ) )
            collection.sort()
            for item in collection:
                self.source.dialog.function_keyword.addItem( item )
        if operation == "SEARCH_NULL":
            for i in range( 0, file_total ):
                # Variables
                index = i + 1
                path = file_list[i]
                path_new = None
                # New String
                path_new, found = self.String_Search_Null( path, found )
                self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
        if operation == "SEARCH_COPY":
            self.Cycle_Search( number, operation_type, file_total, file_list, found )

        # Python
        if operation == "PYTHON_SCRIPT":
            self.String_Python_Script( python_script, path, self.path_destination )
            self.Cycle_Action( operation_type, path, path_new, index, file_total, found )
    def Cycle_Search( self, number, operation_type, file_total, file_list, found ):
        # Variabels
        copy = " [ copy ]"

        # Search
        if number < file_total:
            for i in range( number, file_total - 1 ):
                # Variables
                index = i + 2

                # File
                file_i = file_list[i]
                if copy not in file_i:
                    qimage_i = QImageReader( file_i ).read()

                    # Cycle
                    for j in range( i + 1, file_total ):
                        # File
                        file_j = file_list[j]
                        if copy not in file_j:
                            qimage_j = QImageReader( file_j ).read()

                            # Check QImages
                            path_new = None
                            check = qimage_i == qimage_j
                            if check == True:
                                # Found
                                found += 1
                                # String Components
                                directory, basename, name, extension = self.Path_Components( file_j )
                                # construct keywords
                                a = name.rfind( " [ " )
                                b = name.rfind( " ]" )
                                if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                                    name = name[:a]
                                # Create new path name
                                basename_new = f"{ name } [ copy ]{ extension }"
                                path_new = os.path.join( directory, basename_new )

                            # Feedback
                            if path_new != None:
                                file_list[i] = path_new
                            self.Cycle_Action( operation_type, file_j, path_new, index, file_total, found )

                        del qimage_j
                    del qimage_i
        else:
            pass
    def Cycle_Action( self, operation_type, path, path_new, index, file_total, found ):
        try:
            # Action
            if path_new != None:
                # Exists
                exists = os.path.exists( path_new )
                if ( path != path_new and exists == False ):
                    if operation_type == "rename":
                        boolean = self.qfile.rename( path, path_new )
                        if boolean == True:
                            try:QtCore.qDebug( f"Imagine Board | RENAME { os.path.basename( path ) } >> { os.path.basename( path_new ) }" )
                            except:pass
                    if operation_type == "save":
                        qpixmap = QPixmap( path )
                        if qpixmap.isNull() == True:
                            response = urllib.request.urlopen( path )
                            data = response.read()
                            qpixmap = QPixmap()
                            qpixmap.loadFromData( data )
                        boolean = qpixmap.save( path_new )
                        if boolean == True:
                            try:QtCore.qDebug( f"Imagine Board | SAVE { path_new }" )
                            except:pass
                # Anchor Find
                if path == self.anchor_path:
                    self.anchor_new = path_new

            # Feedback
            self.Progress_String( index, file_total, found )
            self.source.dialog.progress.setValue( index )
            QApplication.processEvents()
        except:
            pass

    #endregion
    #region Edit

    # Keywords
    def String_Key_Add( self, path, keyword ):
        if len( keyword ) == 0:
            path_new = path
        else:
            # String Components
            directory, basename, name, extension = self.Path_Components( path )

            # Construct keywords
            a = name.rfind( " [ " )
            b = name.rfind( " ]" )
            if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                identity = name[:a]
                c = name[a+3:b].split()
                d = list( set( c ).union( set( keyword ) ) )
            else: # No Keys Exist
                identity = name
                d = keyword
            d.sort()
            keys = " [ "
            for i in range( 0, len( d ) ):
                keys += f"{ d[i] } "
            keys += "]"

            # Create new path
            base_new = identity + keys + extension
            path_new = os.path.join( directory, base_new )
        return path_new
    def String_Key_Replace( self, path, keyword ):
        if len( keyword ) == 0:
            path_new = path
        else:
            # String Components
            directory, basename, name, extension = self.Path_Components( path )

            # Construct keywords
            a = name.rfind( " [ " )
            b = name.rfind( " ]" )
            if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                identity = name[:a]
            else: # No Keys Exist
                identity = name
            d = keyword
            d.sort()
            keys = " [ "
            for i in range( 0, len( d ) ):
                keys += f"{ d[i] } "
            keys += "]"

            # Create new path
            base_new = identity + keys + extension
            path_new = os.path.join( directory, base_new )
        return path_new
    def String_Key_Remove( self, path, keyword ):
        if len( keyword ) == 0:
            path_new = path
        else:
            # String Components
            directory, basename, name, extension = self.Path_Components( path )

            # Construct keywords
            a = name.rfind( " [ " )
            b = name.rfind( " ]" )
            if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                identity = name[:a]
                c = name[a+3:b].split()
                d = list( set( c ).difference( set( keyword ) ) )
            else: # No Keys Exist
                identity = name
                d = keyword
            d.sort()

            # Keys left to display
            if len( d ) >= 1:
                keys = " [ "
                for i in range( 0, len( d ) ):
                    keys += f"{ d[i] } "
                keys += "]"
            else:
                keys = ""

            # Create new path
            base_new = identity + keys + extension
            path_new = os.path.join( directory, base_new )
        return path_new
    def String_Key_Clean( self, path ):
        # String Components
        directory, basename, name, extension = self.Path_Components( path )

        # Construct keywords
        a = name.rfind( " [ " )
        b = name.rfind( " ]" )
        if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
            identity = name[:a]
        else: # No Keys Exist
            identity = name

        # Create new path
        base_new = identity + extension
        path_new = os.path.join( directory, base_new )
        # Return
        return path_new
    # Rename
    def String_Rename_Order( self, path, keyword, number ):
        if len( keyword ) == 0:
            path_new = path
        else:
            # String Components
            directory, basename, name, extension = self.Path_Components( path )

            # Construct keywords
            a = name.rfind( " [ " )
            b = name.rfind( " ]" )
            if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                identity = name[:a-1]
                keys = name[a:]
            else: # No Keys Exist
                identity = name
                keys = ""

            # Generate Names
            name_new = f"{ keyword[0] } { str( number ).zfill( 6 ) }"

            # Create new path
            base_new = name_new + keys + extension
            path_new = os.path.join( directory, base_new )
        return path_new
    def String_Rename_Extension( self, path, keyword, number ):
        if len( keyword ) == 0:
            path_new = path
        else:
            # String Components
            directory, basename, name, extension = self.Path_Components( path )

            # Extension Composite
            if keyword[0].startswith( "." ) == True:
                ext = keyword[0]
            else:
                ext = "." + keyword[0]

            # Create new path
            base_new = name + ext
            path_new = os.path.join( directory, base_new )
        return path_new
    # Save
    def String_Save_Order( self, path, keyword, number ):
        if len( keyword ) == 0:
            identity = "image.png"
        else:
            identity = keyword[0]
        num = str( number ).zfill( 6 )
        base_new = f"{ identity } { num }.png"
        path_new = os.path.join( self.path_destination, base_new )
        return path_new
    def String_Save_Original( self, path, keyword ):
        path_new = os.path.join( self.path_destination, keyword )
        return path_new
    # Search
    def String_Search_Key( self, path ):
        # String Components
        directory, basename, name, extension = self.Path_Components( path )

        # construct keywords
        a = name.rfind( " [ " )
        b = name.rfind( " ]" )
        if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
            keys = f"{ name[a+3:b] }"
            keys = keys.split( " " )
            return keys
    def String_Search_Null( self, path, found ):
        reader = QImageReader( path )
        if reader.canRead() == True:
            path_new = None
        else:
            # Found
            found += 1
            # String Components
            directory, basename, name, extension = self.Path_Components( path )
            # construct keywords
            a = name.rfind( " [ " )
            b = name.rfind( " ]" )
            if ( a >= 0 and b >= 0 and a < b ): # Keys Exist
                name = name[:a]
            # Create new path name
            basename_new = f"{ name } [ null ]{ extension }"
            path_new = os.path.join( directory, basename_new )
        # Return
        return path_new, found

    # Python
    def String_Python_Script( self, python_script, path, path_destination ):
        worker_python = Worker_Python()
        worker_python.run( python_script, path, path_destination )

    # Assitance
    def Path_Components( self, path ):
        directory = os.path.dirname( path ) # dir
        basename = os.path.basename( path ) # name.ext
        split_text = os.path.splitext( basename )
        name = split_text[0] # name
        extension = split_text[1] # .ext
        return directory, basename, name, extension
    def Progress_String( self, index, total, found ):
        text_results = f"index:{ index }  total:{ total }"
        if found > 0:
            text_results += f"  found:{ found }"
        self.source.dialog.function_label.setText( text_results )

    #endregion

class Worker_Python( QObject ):

    def run( self, python_script, image_file, path_destination ):
        # Implicit Paths
        # image_file = path_source files or file collection, given by Imagine Board
        # path_destination = directory path to save files into, given by Imagine Board
        try:
            exec( python_script )
        except Exception as e:
            try:QtCore.qDebug( f"Imagine Board | ERROR Python script\nimage_file={ image_file } path_destination={ path_destination }\n{ e }" )
            except:pass


"""
Known Krita Bugs:
- Importing reference with alpha crops image size

"""
