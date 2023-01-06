# Imagine Board is a Krita plugin to displays and organizes images.
# Copyright (C) 2022  Ricardo Jeremias.
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


#region Imports ####################################################################
# Python Modules
import sys
import copy
import math
import random
import os
import subprocess
import datetime
import xml
import time
import stat
import webbrowser
import zipfile
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Imagine Board Modules
from .imagine_board_modulo import (
    ImagineBoard_Preview,
    ImagineBoard_Grid,
    ImagineBoard_Reference,
    Menu_Mode,
    OS_Folders,
    )
from .imagine_board_extension import ImagineBoard_Extension
from .imagine_board_calculations import *

#endregion
#region Global Variables ###########################################################
DOCKER_NAME = "Imagine Board"
imagine_board_version = "2023_01_02"

# File Formats
file_normal = [
    "*.kra",
    "*.krz",
    "*.ora",
    "*.bmp",
    "*.gif",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.pbm",
    "*.pgm",
    "*.ppm",
    "*.xbm",
    "*.xpm",
    "*.tiff",
    "*.psd",
    "*.webp",
    "*.svg",
    "*.svgz",
    "*.zip",
    ]
file_backup = [
    "*.kra~",
    "*.krz~",
    "*.ora~",
    "*.bmp~",
    "*.gif~",
    "*.jpg~",
    "*.jpeg~",
    "*.png~",
    "*.pbm~",
    "*.pgm~",
    "*.ppm~",
    "*.xbm~",
    "*.xpm~",
    "*.tiff~",
    "*.webp~",
    "*.svg~",
    "*.svgz~",
    "*.psd~",
    ]
file_anim = [
    "gif",
    "webp",
    ]
file_compress = [
    "zip",
    ]

# Function
valid_functions = [
    "",
    ">>",
    "key_add",
    "key_replace",
    "key_remove",
    "key_clean",
    "key_populate",
    "rename_order",
    "rename_age",
    "rename_random",
    "save_original",
    "save_order",
    "search_null",
    "search_copy",
    ]

# Variables
decimas = 10
qt_max = 16777215
# time constants
segundo = 1 # null
minuto = 60 # seconds
hora = 60 # minutes
dia = 24 # hours
mes = 30.4167 # days
ano = 12 # moths
sec_segundo = segundo
sec_minuto = minuto * sec_segundo
sec_hora = hora * sec_minuto
sec_dia = dia * sec_hora
sec_mes = mes * sec_dia
sec_ano = ano * sec_mes

#endregion


class ImagineBoard_Docker(DockWidget):
    """
    Display and Organize images
    """

    #region Initialize #############################################################
    def __init__(self):
        super(ImagineBoard_Docker, self).__init__()

        # Construct
        self.Variables()
        self.User_Interface()
        self.Connections()
        self.Modules()
        self.Style()
        self.Timer()
        self.Extension()
        self.Settings()

    def Variables(self):
        # Variables
        self.mode_index = 0
        self.widget_display = False
        self.widget_float = False
        self.menu_anim = False
        self.directory_path = ""
        self.file_extension = file_normal
        self.filter_sort = QDir.LocaleAware
        self.insert_size_bool = False
        self.image_scale = 1
        self.images_found = False
        self.transparent = False
        self.is_inside = False
        self.mode_height = 25
        self.footer = 5 + 15 + self.mode_height
        self.watcher_list = {"dir":[], "file":[]}
        self.work_hours = 0
        self.full_screen = False
        self.dirty = 0

        # Color Picker Modules
        self.pigment_o = None
        self.MODULE_pigmento_bool = False
        self.MODULE_pigmento_pyid = "pykrita_pigment_o2"

        # Lists
        self.list_active = "Folder"
        self.list_recentdocument = []
        self.list_pin_ref = []

        # Preview
        self.preview_path = ""
        self.preview_index = 0
        self.preview_max = 0
        # Slideshow
        self.slideshow_play = False
        self.slideshow_sequence = "Linear"
        self.slideshow_time = 1000
        self.slideshow_lottery = []
        # Animation
        self.anim_playpause = True # True=Play  False=Pause
        # Compressed
        self.menu_comp = False
        self.comp_index = 0
        self.comp_max = 0

        # Grid
        self.grid_horz = 3
        self.grid_vert = 3
        self.grid_table = (self.grid_horz * self.grid_vert) - 1
        self.grid_max = 0
        # Thumbnails
        self.tn_fit_ratio = False
        self.tn_smooth_scale = Qt.FastTransformation
        # Lines
        self.line_preview = 0
        self.line_grid = 0
        # Cache amount
        self.cache_load = 0
        self.cache_clean = 0
        self.cache_thread = 1000

        # Reference
        self.ref_original = False
        self.ref_limit = 2000
        self.undocache_size = 100
        self.undocache_index = 0
        self.undocache_list = []

        # Clip
        self.clip_state = False
        self.clip_px = 0.1
        self.clip_py = 0.1
        self.clip_dw = 0.8
        self.clip_dh = 0.8

        # Path and Pixmaps
        self.null_path = ""
        self.null_qpixmap = QPixmap()
        self.found_path = [self.null_path] * self.grid_table
        self.found_qpixmap = [self.null_qpixmap] * self.grid_table

        # Export
        self.export_filename = "file"
        self.export_extension = ".png"

        # Annotations
        self.annotation_kra = False
        self.annotation_file = False

        # Pixmap
        self.export_qpixmap = QPixmap()
    def User_Interface(self):
        # Window
        self.setWindowTitle(DOCKER_NAME)

        # Operating System
        self.OS = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux
        if self.OS == 'winnt': # Unlocks icons in Krita for Menu Mode
            QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)

        # Path Name
        self.directory_plugin = str(os.path.dirname(os.path.realpath(__file__)))

        # Widget Docker
        self.layout = uic.loadUi(os.path.normpath(self.directory_plugin + "/imagine_board_docker.ui"), QWidget())
        self.setWidget(self.layout)

        # Settings
        self.dialog = uic.loadUi(os.path.normpath(self.directory_plugin + "/imagine_board_settings.ui"), QDialog())
        self.dialog.setWindowTitle("Imagine Board : Settings")

        # Animation Panel Boot
        self.CompPanel_Shrink()
        self.AnimPanel_Shrink()
    def Connections(self):
        # Compressed Connections
        self.layout.comp_slider.valueChanged.connect(self.Comp_Slider)
        self.layout.comp_number.valueChanged.connect(self.Comp_Number)
        # Animation Connections
        self.layout.anim_playpause.clicked.connect(lambda: self.Preview_PlayPause(not self.anim_playpause))
        self.layout.anim_frame_back.clicked.connect(self.Preview_Frame_Back)
        self.layout.anim_frame_forward.clicked.connect(self.Preview_Frame_Forward)
        # Layout Connections
        self.layout.index_slider.valueChanged.connect(self.Index_Slider)
        self.layout.screen.toggled.connect(self.Full_Screen)
        self.layout.folder.clicked.connect(self.Folder_Open)
        self.layout.slideshow.toggled.connect(self.Preview_SlideShow_Switch)
        self.layout.thread.clicked.connect(self.Thumbnail_Start)
        self.layout.undo.clicked.connect(self.Reference_Undo)
        self.layout.redo.clicked.connect(self.Reference_Redo)
        self.layout.search.returnPressed.connect(lambda: self.Filter_Keywords(True))
        self.layout.index_number.valueChanged.connect(self.Index_Number)
        self.layout.settings.clicked.connect(self.Menu_Settings)

        # Dialog Display
        self.dialog.menu_transparent.toggled.connect(self.Menu_Transparent)
        self.dialog.menu_insert_size.toggled.connect(self.Insert_Size)
        self.dialog.menu_slideshow_sequence.currentTextChanged.connect(self.Menu_SlideShow_Sequence)
        self.dialog.menu_slideshow_time.timeChanged.connect(self.Menu_SlideShow_Time)
        self.dialog.menu_fit_ratio.toggled.connect(self.Menu_Fit_Ratio)
        self.dialog.menu_smooth_scale.toggled.connect(self.Menu_Smooth_Scale)
        self.dialog.menu_grid_horz.valueChanged.connect(self.Menu_Grid_U)
        self.dialog.menu_grid_vert.valueChanged.connect(self.Menu_Grid_V)
        self.dialog.menu_cache_load.valueChanged.connect(self.Menu_Cache_Load)
        self.dialog.menu_cache_clean.valueChanged.connect(self.Menu_Cache_Clean)
        self.dialog.menu_cache_thread.valueChanged.connect(self.Menu_Cache_Thread)
        self.dialog.menu_ref_original.toggled.connect(self.Menu_Ref_Original)
        self.dialog.menu_ref_limit.valueChanged.connect(self.Menu_Ref_Limit)
        self.dialog.menu_undocache.valueChanged.connect(self.Menu_Ref_Undocache)
        self.dialog.annotation_kra_save.toggled.connect(self.AutoSave_KRA)
        self.dialog.annotation_kra_load.clicked.connect(self.Annotation_KRA_Load)
        self.dialog.annotation_file_save.toggled.connect(self.AutoSave_File)
        self.dialog.annotation_file_load.clicked.connect(self.Annotation_FILE_Load)
        # Sync
        self.dialog.menu_list_active.currentTextChanged.connect(self.List_Active)
        self.dialog.menu_directory.currentTextChanged.connect(self.Menu_Directory)
        self.dialog.menu_sort.currentTextChanged.connect(self.Menu_Sort)
        # Dialog Information
        self.dialog.info_title.textChanged.connect(self.Information_Save)
        self.dialog.info_subject.textChanged.connect(self.Information_Save)
        self.dialog.info_keyword.textChanged.connect(self.Information_Save)
        self.dialog.info_license.textChanged.connect(self.Information_Save)
        self.dialog.info_description.textChanged.connect(self.Information_Save)
        self.dialog.info_abstract.textChanged.connect(self.Information_Save)
        self.dialog.info_language.textChanged.connect(self.Information_Save)
        self.dialog.menu_money_rate.valueChanged.connect(self.Money_Rate)
        self.dialog.menu_money_total.valueChanged.connect(self.Money_Total)
        self.dialog.info_contact.itemClicked.connect(self.Information_Copy)
        # Dialog Save
        self.dialog.export_filename.textChanged.connect(self.Export_Filename)
        self.dialog.export_extension.currentTextChanged.connect(self.Export_Extension)
        self.dialog.export_clipboard_button.clicked.connect(self.Export_Clipboard)
        self.dialog.export_canvas_button.clicked.connect(self.Export_Canvas)
        self.dialog.scale_width_check.toggled.connect(self.Scale_Width_Check)
        self.dialog.scale_height_check.toggled.connect(self.Scale_Height_Check)
        self.dialog.scale_percent_check.toggled.connect(self.Scale_Percent_Check)
        self.dialog.scale_width_value.valueChanged.connect(self.Scale_Width_Value)
        self.dialog.scale_height_value.valueChanged.connect(self.Scale_Height_Value)
        self.dialog.scale_percent_value.valueChanged.connect(self.Scale_Percent_Value)
        # Dialog Function>>
        self.dialog.menu_function_operation.currentTextChanged.connect(self.Menu_Display_Operation)
        self.dialog.menu_function_add.returnPressed.connect(self.Menu_Function_Add)
        self.dialog.menu_function_clear.clicked.connect(self.Menu_Function_Clear)
        self.dialog.menu_function_number.valueChanged.connect(self.Menu_Number)
        self.dialog.menu_function_path.textChanged.connect(self.Menu_Function_Path)
        self.dialog.menu_function_run.clicked.connect(self.Function_ValidPath)
        # Dialog
        self.dialog.tab_widget.tabBarClicked.connect(self.Menu_Tabs)

        # Notices
        self.dialog.manual.clicked.connect(self.Menu_Manual)
        self.dialog.license.clicked.connect(self.Menu_License)
    def Modules(self):
        #region System
        # Directory
        self.dir = QDir(self.directory_plugin)
        # File Watcher
        self.file_system_watcher = QFileSystemWatcher(self)
        self.file_system_watcher.directoryChanged.connect(self.Watcher_Display)

        #endregion
        #region Preview
        self.imagine_preview = ImagineBoard_Preview(self.layout.preview_view)
        # General
        self.imagine_preview.SIGNAL_CLICK.connect(self.Preview_Index_Increment)
        self.imagine_preview.SIGNAL_WHEEL.connect(self.Preview_Index_Increment)
        self.imagine_preview.SIGNAL_STYLUS.connect(self.Preview_Index_Increment)
        self.imagine_preview.SIGNAL_DRAG.connect(self.Drag_Drop)
        self.imagine_preview.SIGNAL_NEUTRAL.connect(self.Click_Neutral)
        # Preview
        self.imagine_preview.SIGNAL_MODE.connect(self.Context_Mode)
        self.imagine_preview.SIGNAL_FRAME.connect(self.Preview_Frame_Display)
        self.imagine_preview.SIGNAL_FUNCTION.connect(self.Function_Run)
        self.imagine_preview.SIGNAL_PIN_PATH.connect(self.Reference_Insert)
        self.imagine_preview.SIGNAL_RANDOM.connect(self.Preview_Random)
        self.imagine_preview.SIGNAL_LOCATION.connect(self.File_Location)
        self.imagine_preview.SIGNAL_COLOR.connect(self.Preview_Color)
        self.imagine_preview.SIGNAL_CLIP.connect(self.File_Clip)
        self.imagine_preview.SIGNAL_NEW_DOCUMENT.connect(self.Insert_Document)
        self.imagine_preview.SIGNAL_INSERT_LAYER.connect(self.Insert_Layer)
        self.imagine_preview.SIGNAL_INSERT_REFERENCE.connect(self.Insert_Reference)
        self.imagine_preview.SIGNAL_ANIM_PANEL.connect(self.Menu_AnimPanel)
        self.imagine_preview.SIGNAL_COMP.connect(self.Preview_Comp_Increment)

        #endregion
        #region Grid
        self.imagine_grid = ImagineBoard_Grid(self.layout.imagine_grid)
        self.imagine_grid.Set_Scale(self.tn_smooth_scale)
        # General
        self.imagine_grid.SIGNAL_CLICK.connect(self.Grid_Index_Increment)
        self.imagine_grid.SIGNAL_WHEEL.connect(self.Grid_Index_Increment)
        self.imagine_grid.SIGNAL_STYLUS.connect(self.Grid_Index_Increment)
        self.imagine_grid.SIGNAL_DRAG.connect(self.Drag_Drop)
        self.imagine_grid.SIGNAL_NEUTRAL.connect(self.Click_Neutral)
        # Grid
        self.imagine_grid.SIGNAL_PREVIEW.connect(self.Grid_Preview)
        self.imagine_grid.SIGNAL_FUNCTION.connect(self.Function_Run)
        self.imagine_grid.SIGNAL_LOCATION.connect(self.File_Location)
        self.imagine_grid.SIGNAL_PIN_PATH.connect(self.Reference_Insert)
        self.imagine_grid.SIGNAL_NAME.connect(self.Grid_Name)
        self.imagine_grid.SIGNAL_NEW_DOCUMENT.connect(self.Insert_Document)
        self.imagine_grid.SIGNAL_INSERT_LAYER.connect(self.Insert_Layer)
        self.imagine_grid.SIGNAL_INSERT_REFERENCE.connect(self.Insert_Reference)

        #endregion
        #region Reference
        self.imagine_reference = ImagineBoard_Reference(self.layout.imagine_reference)
        # General
        self.imagine_reference.SIGNAL_DRAG.connect(self.Drag_Drop)
        self.imagine_reference.SIGNAL_DROP.connect(self.Reference_Insert)
        # Reference
        self.imagine_reference.SIGNAL_SAVE.connect(self.Board_Save)
        self.imagine_reference.SIGNAL_UNDO.connect(self.Reference_Cache)
        self.imagine_reference.SIGNAL_CLIP.connect(self.File_Clip)
        self.imagine_reference.SIGNAL_TEXT.connect(self.Reference_Insert)

        #endregion
        #region UI
        # Mode
        self.mode = Menu_Mode(self.layout.mode)
        self.mode.SIGNAL_MODE.connect(self.Menu_Index)
        # Folders
        self.os_folders = OS_Folders(self.layout.folder)
        self.os_folders.SIGNAL_PATH.connect(self.Folder_Changer)
        #endregion
        #region Thread Function
        self.thread_function = Thread_Function()
        self.thread_function.Docker(self.dialog)
        # General
        self.thread_function.SIGNAL_PBAR_VALUE.connect(self.Function_PBAR_Value)
        self.thread_function.SIGNAL_PBAR_MAX.connect(self.Function_PBAR_Max)
        self.thread_function.SIGNAL_STRING.connect(self.Function_String)
        self.thread_function.SIGNAL_NUMBER.connect(self.Function_Number)
        self.thread_function.SIGNAL_RESET.connect(self.Function_Reset)
        self.thread_function.SIGNAL_ITEM.connect(self.Function_Item)
        self.thread_function.SIGNAL_NEWPATH.connect(self.Function_NewPath)

        #endregion
    def Style(self):
        # Icons
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_pause'))
        self.layout.anim_frame_back.setIcon(Krita.instance().icon('prevframe'))
        self.layout.anim_frame_forward.setIcon(Krita.instance().icon('nextframe'))

        self.layout.mode.setIcon(Krita.instance().icon('folder-pictures'))
        self.layout.screen.setIcon(Krita.instance().icon('zoom-vertical'))
        self.layout.folder.setIcon(Krita.instance().icon('document-open'))
        self.layout.thread.setIcon(Krita.instance().icon('document-import'))
        self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-start'))
        self.layout.undo.setIcon(Krita.instance().icon('draw-arrow-back'))
        self.layout.redo.setIcon(Krita.instance().icon('draw-arrow-forward'))
        self.layout.settings.setIcon(Krita.instance().icon('settings-button'))

        self.dialog.menu_function_clear.setIcon(Krita.instance().icon('edit-clear-16'))

        # ToolTips
        self.layout.mode.setToolTip("Mode")
        self.layout.screen.setToolTip("Screen")
        self.layout.folder.setToolTip("Open Directory")
        self.layout.thread.setToolTip("Thumbnail Cache")
        self.layout.slideshow.setToolTip("SlideShow Play")
        self.layout.undo.setToolTip("Undo")
        self.layout.redo.setToolTip("Redo")
        self.layout.search.setToolTip("Search Contents")
        self.layout.index_number.setToolTip("Image Index")
        self.layout.settings.setToolTip("Settings")

        self.layout.anim_playpause.setToolTip("Play / Pause")
        self.layout.anim_frame_back.setToolTip("Frame Backward")
        self.layout.anim_frame_forward.setToolTip("Frame Forward")

        # StyleSheets
        self.layout.anim_panel.setStyleSheet("#anim_panel{background-color: rgba(0, 0, 0, 50);}")
        self.layout.progress_bar.setStyleSheet("#progress_bar{background-color: rgba(0, 0, 0, 50);}")
        self.dialog.scrollarea_contents_display.setStyleSheet("#scrollarea_contents_display{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scrollarea_contents_sync.setStyleSheet("#scrollarea_contents_sync{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scrollarea_contents_information.setStyleSheet("#scrollarea_contents_information{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scrollarea_contents_export.setStyleSheet("#scrollarea_contents_export{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scrollarea_contents_function.setStyleSheet("#scrollarea_contents_function{background-color: rgba(0, 0, 100, 20);}")

        # Function Operations
        self.dialog.menu_function_operation.addItem(">>")
        self.dialog.menu_function_operation.insertSeparator(1)
        self.dialog.menu_function_operation.addItem("key_add")
        self.dialog.menu_function_operation.addItem("key_replace")
        self.dialog.menu_function_operation.addItem("key_remove")
        self.dialog.menu_function_operation.addItem("key_clean")
        self.dialog.menu_function_operation.addItem("key_populate")
        self.dialog.menu_function_operation.insertSeparator(7)
        self.dialog.menu_function_operation.addItem("rename_order")
        self.dialog.menu_function_operation.addItem("rename_age")
        self.dialog.menu_function_operation.addItem("rename_random")
        self.dialog.menu_function_operation.insertSeparator(11)
        self.dialog.menu_function_operation.addItem("save_original")
        self.dialog.menu_function_operation.addItem("save_order")
        self.dialog.menu_function_operation.insertSeparator(14)
        self.dialog.menu_function_operation.addItem("search_null")
        self.dialog.menu_function_operation.addItem("search_copy")

        # Geometry
        self.layout.screen.setMaximumWidth(0)
    def Timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.Preview_SlideShow_Play)
    def Extension(self):
        # Install Extension for Docker
        extension = ImagineBoard_Extension(parent = Krita.instance())
        Krita.instance().addExtension(extension)
        # Connect Extension Signals
        extension.SIGNAL_FULL_SCREEN.connect(self.Screen_Swap)
        extension.SIGNAL_BROWSE.connect(self.Shortcut_Browse)
        extension.SIGNAL_EXPORT_CLIPBOARD.connect(self.Export_Clipboard)
        extension.SIGNAL_EXPORT_CANVAS.connect(self.Export_Canvas)
    def Settings(self):
        # Menu Mode
        mode_index = Krita.instance().readSetting("Imagine Board", "mode_index", "")
        if mode_index == "":
            Krita.instance().writeSetting("Imagine Board", "mode_index", str(0) )
        else:
            self.mode_index = int(mode_index)

    #endregion
    #region Settings ###############################################################
    def Settings_Load(self):
        if self.widget_display == False:
            # Read
            self.Read_Layout()
            self.Read_Dialog()

            # Control Variable
            self.widget_display = True

            # Setup
            self.Folder_Changer( [self.directory_path, False] )
            self.Preview_GoTo(self.preview_index)
            self.Board_Loader(self.list_pin_ref)

    def Read_Layout(self):
        # Directory Path
        directory_path = str( Krita.instance().readSetting("Imagine Board", "directory_path", "") )
        if directory_path == "":
            Krita.instance().writeSetting("Imagine Board", "directory_path", "")
        else:
            self.directory_path = directory_path

        # Search
        search = str(Krita.instance().readSetting("Imagine Board", "search", ""))
        if search == "":
            Krita.instance().writeSetting("Imagine Board", "search", "")
        else:
            self.layout.search.setText(search)

        # Preview Index
        preview_index = Krita.instance().readSetting("Imagine Board", "preview_index", "")
        if preview_index == "":
            Krita.instance().writeSetting("Imagine Board", "preview_index", str(0) )
        else:
            self.preview_index = int(preview_index)

        # References
        references = Krita.instance().readSetting("Imagine Board", "list_pin_ref", "")
        if references == "":
            Krita.instance().writeSetting("Imagine Board", "list_pin_ref", "")
        else:
            self.list_pin_ref = eval(references)
    def Read_Dialog(self):
        # Dialog Display
        try:
            # Window Transparency
            transparent = Krita.instance().readSetting("Imagine Board", "transparent", "")
            if transparent == "":
                Krita.instance().writeSetting("Imagine Board", "transparent", "False")
            else:
                self.dialog.menu_transparent.setChecked( eval(transparent) )
            # Insert Size
            insert_size = Krita.instance().readSetting("Imagine Board", "insert_size", "")
            if insert_size == "":
                Krita.instance().writeSetting("Imagine Board", "insert_size", "False")
            else:
                self.dialog.menu_insert_size.setChecked( eval(insert_size) )

            # Slideshow Sequence
            slideshow_sequence = Krita.instance().readSetting("Imagine Board", "slideshow_sequence", "")
            if slideshow_sequence == "":
                Krita.instance().writeSetting("Imagine Board", "slideshow_sequence", "Linear")
            else:
                self.dialog.menu_slideshow_sequence.setCurrentText(str(slideshow_sequence))
            # Slideshow Time
            ms = Krita.instance().readSetting("Imagine Board", "slideshow_time", "")
            if ms == "":
                Krita.instance().writeSetting("Imagine Board", "slideshow_time", str(1000) )
            else:
                tempo = QTime(0,0,0).addMSecs(int(ms))
                self.dialog.menu_slideshow_time.setTime(tempo)

            # Thumbnail Fit Ratio
            fit_ratio = Krita.instance().readSetting("Imagine Board", "fit_ratio", "")
            if fit_ratio == "":
                Krita.instance().writeSetting("Imagine Board", "fit_ratio", "False")
            else:
                self.dialog.menu_fit_ratio.setChecked( eval(fit_ratio) )
            # Thumbnail Smooth Scale
            smooth_scale = Krita.instance().readSetting("Imagine Board", "smooth_scale", "")
            if smooth_scale == "":
                Krita.instance().writeSetting("Imagine Board", "smooth_scale", "False")
            else:
                self.dialog.menu_smooth_scale.setChecked( eval(smooth_scale) )
            # Grid U
            grid_u = Krita.instance().readSetting("Imagine Board", "grid_u", "")
            if grid_u == "":
                Krita.instance().writeSetting("Imagine Board", "grid_u", str(3) )
            else:
                self.dialog.menu_grid_horz.setValue(int(grid_u))
            # Grid V
            grid_v = Krita.instance().readSetting("Imagine Board", "grid_v", "")
            if grid_v == "":
                Krita.instance().writeSetting("Imagine Board", "grid_v", str(3) )
            else:
                self.dialog.menu_grid_vert.setValue(int(grid_v))
            # Cache Clean
            cache_clean = Krita.instance().readSetting("Imagine Board", "cache_clean", "")
            if cache_clean == "":
                Krita.instance().writeSetting("Imagine Board", "cache_clean", str(0) )
            else:
                self.dialog.menu_cache_clean.setValue(int(cache_clean))
            # Cache Load
            cache_load = Krita.instance().readSetting("Imagine Board", "cache_load", "")
            if cache_load == "":
                Krita.instance().writeSetting("Imagine Board", "cache_load", str(0) )
            else:
                self.dialog.menu_cache_load.setValue(int(cache_load))
            # Cache Thread
            cache_thread = Krita.instance().readSetting("Imagine Board", "cache_thread", "")
            if cache_thread == "":
                Krita.instance().writeSetting("Imagine Board", "cache_thread", str(0) )
            else:
                self.dialog.menu_cache_thread.setValue(int(cache_thread))

            # Reference Import
            ref_original = Krita.instance().readSetting("Imagine Board", "ref_original", "")
            if ref_original == "":
                Krita.instance().writeSetting("Imagine Board", "ref_original", "False")
            else:
                self.dialog.menu_ref_original.setChecked( eval(ref_original) )
            # Reference Limit
            ref_limit = Krita.instance().readSetting("Imagine Board", "ref_limit", "")
            if ref_limit == "":
                Krita.instance().writeSetting("Imagine Board", "ref_limit", str(1000) )
            else:
                self.dialog.menu_ref_limit.setValue( int(ref_limit) )
            # Undo Cache Size
            undocache_size = Krita.instance().readSetting("Imagine Board", "undocache_size", "")
            if undocache_size == "":
                Krita.instance().writeSetting("Imagine Board", "undocache_size", str(100) )
            else:
                self.dialog.menu_undocache.setValue(int(undocache_size))
        except:
            pass

        # Dialog Sync
        try:
            # Lists
            list_active = Krita.instance().readSetting("Imagine Board", "list_active", "")
            if list_active == "":
                Krita.instance().writeSetting("Imagine Board", "list_active", "")
            else:
                self.dialog.menu_list_active.setCurrentText(str(list_active))
            # Directory File
            directory_file = Krita.instance().readSetting("Imagine Board", "directory_file", "")
            if directory_file == "":
                Krita.instance().writeSetting("Imagine Board", "directory_file", "")
            else:
                self.dialog.menu_directory.setCurrentText(str(directory_file))
            # Sort
            sort = Krita.instance().readSetting("Imagine Board", "sort", "")
            if sort == "":
                Krita.instance().writeSetting("Imagine Board", "sort", "Local Aware")
            else:
                self.dialog.menu_sort.setCurrentText(str(sort))
        except:
            pass

        # Dialog Export
        try:
            # Export File Name
            export_filename = Krita.instance().readSetting("Imagine Board", "export_filename", "")
            if export_filename == "":
                Krita.instance().writeSetting("Imagine Board", "export_filename", "file")
            else:
                self.dialog.export_filename.setText( str(export_filename) )
            self.Export_Filename(export_filename)
            # Export Extension
            export_extension = Krita.instance().readSetting("Imagine Board", "export_extension", "")
            if export_extension == "":
                export_extension = ".png"
                Krita.instance().writeSetting("Imagine Board", "export_extension", str(export_extension))
            else:
                self.dialog.export_extension.setCurrentText( str(export_extension) )
            self.Export_Extension(export_extension)

            # Scale Width Check
            scale_width_check = Krita.instance().readSetting("Imagine Board", "scale_width_check", "")
            if scale_width_check == "":
                Krita.instance().writeSetting("Imagine Board", "scale_width_check", "False")
            else:
                self.dialog.scale_width_check.setChecked( eval(scale_width_check) )
            # Scale Height Check
            scale_height_check = Krita.instance().readSetting("Imagine Board", "scale_height_check", "")
            if scale_height_check == "":
                Krita.instance().writeSetting("Imagine Board", "scale_height_check", "False")
            else:
                self.dialog.scale_height_check.setChecked( eval(scale_height_check) )
            # Scale Percent Check
            scale_percent_check = Krita.instance().readSetting("Imagine Board", "scale_percent_check", "")
            if scale_percent_check == "":
                Krita.instance().writeSetting("Imagine Board", "scale_percent_check", "True")
            else:
                self.dialog.scale_percent_check.setChecked( eval(scale_percent_check) )

            # Scale Width Value
            scale_width_value = Krita.instance().readSetting("Imagine Board", "scale_width_value", "")
            if scale_width_value == "":
                Krita.instance().writeSetting("Imagine Board", "scale_width_value", "1")
            else:
                self.dialog.scale_width_value.setValue( eval(scale_width_value) )
            # Scale Height Value
            scale_height_value = Krita.instance().readSetting("Imagine Board", "scale_height_value", "")
            if scale_height_value == "":
                Krita.instance().writeSetting("Imagine Board", "scale_height_value", "1")
            else:
                self.dialog.scale_height_value.setValue( eval(scale_height_value) )
            # Scale Percent Value
            scale_percent_value = Krita.instance().readSetting("Imagine Board", "scale_percent_value", "")
            if scale_percent_value == "":
                Krita.instance().writeSetting("Imagine Board", "scale_percent_value", "100")
            else:
                self.dialog.scale_percent_value.setValue( eval(scale_percent_value) )
        except:
            pass

        # Dialog Function
        try:
            # Function Operation
            function_operation = Krita.instance().readSetting("Imagine Board", "function_operation", "")
            if function_operation == "":
                Krita.instance().writeSetting("Imagine Board", "function_operation", ">>")
            else:
                self.dialog.menu_function_operation.setCurrentText(str(function_operation))
            # Function String
            keywords = Application.readSetting("Imagine Board", "function_string", "")
            if keywords == "":
                Krita.instance().writeSetting("Imagine Board", "function_string", "")
            else:
                key_split = str(keywords).split(",")
                for k in key_split:
                    if (k != "," and k != ""):
                        self.dialog.menu_function_list.addItem(k)
            # Function Number
            function_number = Krita.instance().readSetting("Imagine Board", "function_number", "")
            if function_number == "":
                Krita.instance().writeSetting("Imagine Board", "function_number", str(0) )
            else:
                self.dialog.menu_function_number.setValue(int(function_number))
            # Function Path
            function_path = Krita.instance().readSetting("Imagine Board", "function_path", "")
            if function_path == "":
                Krita.instance().writeSetting("Imagine Board", "function_path", "")
            else:
                self.dialog.menu_function_path.setText(str(function_path))
        except:
            pass

    #endregion
    #region Menu Signals ###########################################################
    # Basic UI
    def Menu_Index(self, index):
        # Modulo
        self.mode.Set_Mode(index)
        # prepare cycle
        self.Display_Shrink()
        self.AnimPanel_Shrink()
        # Variables
        a = 5
        b = 15
        c = self.mode_height
        d = 20
        # Preview
        if index == 0:
            # Icon
            self.layout.mode.setIcon( Krita.instance().icon('folder-pictures') )
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            # Height
            self.layout.imagine_preview.setMaximumHeight(qt_max)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(0)
            # Width
            self.layout.folder.setMaximumWidth(d)
            self.layout.slideshow.setMaximumWidth(d)
            self.layout.thread.setMaximumWidth(0)
            self.layout.undo.setMaximumWidth(0)
            self.layout.redo.setMaximumWidth(0)
            # Enable
            self.Index_Enable(True)
        # Grid
        if index == 1:
            # Icon
            self.layout.mode.setIcon(Krita.instance().icon('gridbrush'))
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            # Height
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(qt_max)
            self.layout.imagine_reference.setMaximumHeight(0)
            # Width
            self.layout.folder.setMaximumWidth(d)
            self.layout.slideshow.setMaximumWidth(0)
            self.layout.thread.setMaximumWidth(d)
            self.layout.undo.setMaximumWidth(0)
            self.layout.redo.setMaximumWidth(0)
            # Enable
            self.Index_Enable(True)
        # Reference
        if index == 2:
            # Icon
            self.layout.mode.setIcon(Krita.instance().icon('zoom-fit'))
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            # Height
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(qt_max)
            # Width
            self.layout.folder.setMaximumWidth(0)
            self.layout.slideshow.setMaximumWidth(0)
            self.layout.thread.setMaximumWidth(0)
            self.layout.undo.setMaximumWidth(d)
            self.layout.redo.setMaximumWidth(d)
            # Enable
            self.Index_Enable(False)

        # update cycle
        if (self.widget_display == True and self.mode_index != index): # After a search with null results or reference board change, this ensure other modes update
            self.mode_index = index
            self.imagine_preview.Clip_Off()
            self.List_Reference()
            self.Display_Update()
        self.dirty = 5
        # Save
        Krita.instance().writeSetting("Imagine Board", "mode_index", str( self.mode_index ))
    def Display_Shrink(self):
        self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_preview.setMinimumHeight(0)
        self.layout.imagine_grid.setMinimumHeight(0)
        self.layout.imagine_reference.setMinimumHeight(0)
        self.layout.imagine_preview.setMaximumHeight(qt_max)
        self.layout.imagine_grid.setMaximumHeight(qt_max)
        self.layout.imagine_reference.setMaximumHeight(qt_max)
    def Transparent_Shift(self):
        # Variables
        a = 5
        b = 15
        c = self.mode_height
        # Geometry Changes
        if self.transparent == True:
            is_floating = self.isFloating()
            if (is_floating == True and self.is_inside == False):
                tr = True
                pb = 0
                sl = 0
                hb = 0
            else:
                tr = False
                pb = 5
                sl = 15
                hb = self.mode_height
        else:
            tr = False
            pb = 5
            sl = 15
            hb = self.mode_height
        self.setAttribute(Qt.WA_NoSystemBackground, tr)
        self.layout.progress_bar.setMinimumHeight(pb)
        self.layout.progress_bar.setMaximumHeight(pb)
        self.layout.index_slider.setMinimumHeight(sl)
        self.layout.index_slider.setMaximumHeight(sl)
        self.layout.horizontal_buttons.setMinimumHeight(hb)
        self.layout.horizontal_buttons.setMaximumHeight(hb)
        self.dirty = 5

    # Compression
    def Menu_CompPanel(self, comp):
        # State
        if self.mode_index == 0 and comp == True:
            value = 20
            margin = 5
        else:
            value = 0
            margin = 0
        # Widgets
        self.layout.comp_slider.setMinimumHeight(value)
        self.layout.comp_slider.setMaximumHeight(value)
        self.layout.comp_number.setMinimumHeight(value)
        self.layout.comp_number.setMaximumHeight(value)
        self.layout.comp_panel_layout.setContentsMargins(0,0,0,margin)
        # update cycle
        if self.menu_comp != comp:
            self.menu_comp = comp
            self.dirty = 5
    def CompPanel_Shrink(self):
        self.layout.comp_slider.setMinimumHeight(0)
        self.layout.comp_slider.setMaximumHeight(0)
        self.layout.comp_number.setMinimumHeight(0)
        self.layout.comp_number.setMaximumHeight(0)
        self.layout.comp_panel_layout.setContentsMargins(0,0,0,0)
    # Animation
    def Menu_AnimPanel(self, anim):
        # State
        if self.mode_index == 0 and anim == True:
            value = 20
            margin = 5
        else:
            value = 0
            margin = 0
        # Widgets
        self.layout.anim_panel.setMinimumHeight(value)
        self.layout.anim_panel.setMaximumHeight(value)
        self.layout.anim_playpause.setMinimumHeight(value)
        self.layout.anim_playpause.setMaximumHeight(value)
        self.layout.anim_frame_back.setMinimumHeight(value)
        self.layout.anim_frame_back.setMaximumHeight(value)
        self.layout.anim_frame_forward.setMinimumHeight(value)
        self.layout.anim_frame_forward.setMaximumHeight(value)
        self.layout.anim_frame_display.setMinimumHeight(value)
        self.layout.anim_frame_display.setMaximumHeight(value)
        self.layout.anim_panel_layout.setContentsMargins(0,0,0,margin)
        # update cycle
        if self.menu_anim != anim:
            self.menu_anim = anim
            self.dirty = 5
    def AnimPanel_Shrink(self):
        self.layout.anim_panel.setMinimumHeight(0)
        self.layout.anim_panel.setMaximumHeight(0)
        self.layout.anim_playpause.setMinimumHeight(0)
        self.layout.anim_playpause.setMaximumHeight(0)
        self.layout.anim_frame_back.setMinimumHeight(0)
        self.layout.anim_frame_back.setMaximumHeight(0)
        self.layout.anim_frame_forward.setMinimumHeight(0)
        self.layout.anim_frame_forward.setMaximumHeight(0)
        self.layout.anim_frame_display.setMinimumHeight(0)
        self.layout.anim_frame_display.setMaximumHeight(0)
        self.layout.anim_panel_layout.setContentsMargins(0,0,0,0)

    # UI
    def Menu_Transparent(self, boolean):
        self.transparent = boolean
        self.Transparent_Shift()
        # Save
        Krita.instance().writeSetting("Imagine Board", "transparent", str( self.transparent ))
    def Insert_Size(self, boolean):
        self.insert_size_bool = boolean
        # Save
        Krita.instance().writeSetting("Imagine Board", "insert_size", str( self.insert_size_bool ))

    # Preview
    def Menu_SlideShow_Sequence(self, path):
        self.slideshow_sequence = path
        Krita.instance().writeSetting("Imagine Board", "slideshow_sequence", str( self.slideshow_sequence ))
    def Menu_SlideShow_Time(self, time):
        # Read
        hour = self.dialog.menu_slideshow_time.time().hour()
        minute = self.dialog.menu_slideshow_time.time().minute()
        second = self.dialog.menu_slideshow_time.time().second()
        # Calculations
        hr_min = hour * 60
        min_add = minute + hr_min
        min_sec = min_add * 60
        sec_add = second + min_sec
        factor = 1000
        self.slideshow_time = sec_add * factor # 1 x 1000ms = 1second
        # Save
        Krita.instance().writeSetting("Imagine Board", "slideshow_time", str(self.slideshow_time))
    # Grid
    def Menu_Fit_Ratio(self, bool):
        # Variable
        if bool == True:
            self.tn_fit_ratio = True
        else:
            self.tn_fit_ratio = False
        # Update Display
        self.imagine_grid.Set_Fit_Ratio(self.tn_fit_ratio)
        # Save
        Krita.instance().writeSetting("Imagine Board", "fit_ratio", str( bool ))
    def Menu_Smooth_Scale(self, bool):
        # Variable
        if bool == True:
            self.tn_smooth_scale = Qt.SmoothTransformation
        else:
            self.tn_smooth_scale = Qt.FastTransformation
        # Update Display
        self.imagine_grid.Set_Scale(self.tn_smooth_scale)
        # Save
        Krita.instance().writeSetting("Imagine Board", "smooth_scale", str( bool ))
    def Menu_Grid_U(self, value):
        self.grid_horz = int(value)
        Krita.instance().writeSetting("Imagine Board", "grid_u", str( self.grid_horz ))
        if self.widget_display == True:
            self.Menu_Grid_Size()
    def Menu_Grid_V(self, value):
        self.grid_vert = int(value)
        Krita.instance().writeSetting("Imagine Board", "grid_v", str( self.grid_vert ))
        if self.widget_display == True:
            self.Menu_Grid_Size()
    def Menu_Grid_Size(self):
        self.grid_table = (self.grid_horz * self.grid_vert)
        self.imagine_grid.Set_Grid(self.grid_horz, self.grid_vert)
        if self.widget_display == True:
            self.Display_Update()
    def Menu_Cache_Load(self, value):
        self.cache_load = int(value)
        if self.cache_load >= self.cache_clean:
            self.dialog.menu_cache_clean.setValue(self.cache_load)
        Krita.instance().writeSetting("Imagine Board", "cache_load", str( self.cache_load ))
    def Menu_Cache_Clean(self, value):
        self.cache_clean = int(value)
        if self.cache_clean <= self.cache_load:
            self.dialog.menu_cache_load.setValue(self.cache_clean)
        Krita.instance().writeSetting("Imagine Board", "cache_clean", str( self.cache_clean ))
    def Menu_Cache_Thread(self, value):
        self.cache_thread = int(value)
        Krita.instance().writeSetting("Imagine Board", "cache_thread", str( self.cache_thread ))
    # Reference
    def Menu_Ref_Original(self, boolean):
        self.ref_original = boolean
        # Save
        Krita.instance().writeSetting("Imagine Board", "ref_original", str( self.ref_original ))
    def Menu_Ref_Limit(self, value):
        self.ref_limit = int(value)
        # Save
        Krita.instance().writeSetting("Imagine Board", "ref_limit", str( self.ref_limit ))
    def Menu_Ref_Undocache(self, value):
        self.undocache_size = int(value)
        # Save
        Krita.instance().writeSetting("Imagine Board", "undocache_size", str( self.undocache_size ))

    # Sync
    def List_Active(self, list_active):
        # Checks
        self.list_active = str(list_active)
        # Watcher
        if self.list_active == "Recent Documents":
            recentdocuments = krita.Krita.instance().recentDocuments()
            self.list_recentdocument = []
            for i in range(0, len(recentdocuments)):
                if recentdocuments[i] != "":
                    self.list_recentdocument.append(recentdocuments[i])

        # Display
        if self.widget_display == True:
            self.Filter_Keywords(True)
            self.Menu_Tabs()
        # Finish
        Krita.instance().writeSetting("Imagine Board", "list_active", str( self.list_active ))
        # self.update()
    def Menu_Directory(self, text):
        # Directory
        directory = text
        if directory == "Normal":
            self.file_extension = file_normal
        if directory == "BackUp~":
            self.file_extension = file_backup
        # Display
        if self.widget_display == True:
            self.Filter_Keywords(True)
            self.Menu_Tabs()
        # Save
        Krita.instance().writeSetting("Imagine Board", "directory_file", str( directory ))
    def Menu_Sort(self, SIGNAL_SORT):
        # Sorting
        if SIGNAL_SORT == "Local Aware":
            self.filter_sort = QDir.LocaleAware
        if SIGNAL_SORT == "Name":
            self.filter_sort = QDir.Name
        if SIGNAL_SORT == "Time":
            self.filter_sort = QDir.Time
        if SIGNAL_SORT == "Size":
            self.filter_sort = QDir.Size
        if SIGNAL_SORT == "Type":
            self.filter_sort = QDir.Type
        if SIGNAL_SORT == "Unsorted":
            self.filter_sort = QDir.Unsorted
        if SIGNAL_SORT == "No Sort":
            self.filter_sort = QDir.NoSort
        if SIGNAL_SORT == "Reversed":
            self.filter_sort = QDir.Reversed
        if SIGNAL_SORT == "Ignore Case":
            self.filter_sort = QDir.IgnoreCase
        # Display
        if self.widget_display == True:
            self.Filter_Keywords(True)
            self.Menu_Tabs()
        # Save
        Krita.instance().writeSetting("Imagine Board", "sort", str( SIGNAL_SORT ))
    # Function
    def Menu_Display_Operation(self, operation):
        # Text
        if (operation == ">>" or operation == ""):
            text = "Search"
        if operation == "key_add":
            text = "KEY ADD (s)"
        if operation == "key_replace":
            text = "KEY REPLACE (s)"
        if operation == "key_remove":
            text = "KEY REMOVE (s)"
        if operation == "key_clean":
            text = "KEY CLEAN"
        if operation == "key_populate":
            text = "KEY POPULATE"
        if operation == "rename_order":
            text = "RENAME ORDER (s, n)"
        if operation == "rename_age":
            text = "RENAME AGE (s, n)"
        if operation == "rename_random":
            text = "RENAME RANDOM (s)"
        if operation == "save_original":
            text = "SAVE ORIGINAL"
        if operation == "save_order":
            text = "SAVE ORDER (s, n)"
        if operation == "search_null":
            text = "SEARCH NULL"
        if operation == "search_copy":
            text = "SEARCH COPY"
        # Context Menu
        if operation == ">>":
            context = ""
        else:
            context = " " + text
        self.imagine_preview.Set_Operation(context)
        self.imagine_grid.Set_Operation(context)

        # Display Placeholder Text
        self.layout.search.setPlaceholderText(text)

        # Save
        Krita.instance().writeSetting("Imagine Board", "function_operation", str( operation ))
    def Menu_Function_Add(self):
        # Items
        string = self.dialog.menu_function_add.text().lower().replace(" ", "_")
        if string != "":
            self.dialog.menu_function_add.setText("")
            self.dialog.menu_function_list.addItem(string)
        # Save
        self.List_Save()
    def Menu_Function_Clear(self):
        # Items
        self.dialog.menu_function_add.clear()
        remove = self.dialog.menu_function_list.selectedItems()
        count_rem = len(remove)
        if count_rem > 0:
            for r in range(0, count_rem):
                count_itm = self.dialog.menu_function_list.count()
                for i in range(0, count_itm):
                    if self.dialog.menu_function_list.item(i) == remove[r]:
                        self.dialog.menu_function_list.takeItem(i)
                        break
        # Save
        self.List_Save()
    def List_Save(self):
        keywords = ""
        for k in range(0, self.dialog.menu_function_list.count()):
            keywords += self.dialog.menu_function_list.item(k).text()+","
        Krita.instance().writeSetting("Imagine Board", "function_string", str( keywords ))
    def List_Selected(self):
        selection = self.dialog.menu_function_list.selectedItems()
        sel_sort = []
        for i in range(0, len(selection)):
            sel_sort.append( str(selection[i].text()) )
            sel_sort.sort()
        return sel_sort
    def Menu_Number(self, value):
        # Save
        Krita.instance().writeSetting("Imagine Board", "function_number", str( int(value) ))
    def Menu_Function_Path(self, text):
        # Path
        path = self.Clean_Dot(os.path.normpath(text))
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.dialog.menu_function_run.setEnabled(True)
        else:
            self.dialog.menu_function_run.setEnabled(False)
        # Save
        Krita.instance().writeSetting("Imagine Board", "function_path", str( self.dialog.menu_function_path.text() ))
    # Tabs
    def Menu_Tabs(self):
        self.Watcher_Update()
        self.Information_Read()

    # Dialogs
    def Menu_Settings(self):
        # Display
        self.dialog.show()
        # Resize Geometry
        screen_zero = QtWidgets.QDesktopWidget().screenGeometry(0) # Size of monitor zero 0
        width = int(screen_zero.width())
        height = int(screen_zero.height())
        size = 500
        self.dialog.setGeometry( width*0.5-size*0.5, height*0.5-size*0.5, size, size )
    def Menu_Manual(self):
        url = "https://github.com/EyeOdin/imagine_board/wiki"
        webbrowser.open_new(url)
    def Menu_License(self):
        url = "https://github.com/EyeOdin/imagine_board/blob/main/LICENSE"
        webbrowser.open_new(url)

    #endregion
    #region Management #############################################################
    def grid_to_prev(self, gp, gh, sx, sy):
        prev = (gp * gh) + (sy * gh) + sx
        return prev
    def Clean_Dot(self, text):
        if text.startswith(".") == True:
            text = ""
        return text
    def Path_Extension(self, path):
        extension = os.path.splitext(path)[1][1:]
        return extension
    def Path_Components(self, path):
        directory = os.path.dirname(path) # dir
        basename = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = basename.find(extension)
        base = basename[:n] # name
        return directory, basename, extension, base

    def Clear_Focus(self):
        self.layout.search.clearFocus()
        self.layout.index_number.clearFocus()
        self.layout.comp_number.clearFocus()
    def Widget_Enable(self, boolean):
        # Panels
        self.layout.preview_view.setEnabled(boolean)
        self.layout.imagine_grid.setEnabled(boolean)
        self.layout.imagine_reference.setEnabled(boolean)
        # Animations
        self.layout.anim_frame_back.setEnabled(boolean)
        self.layout.anim_playpause.setEnabled(boolean)
        self.layout.anim_frame_forward.setEnabled(boolean)
        # Widgets
        self.layout.index_slider.setEnabled(boolean)
        self.layout.mode.setEnabled(boolean)
        self.layout.folder.setEnabled(boolean)
        self.layout.slideshow.setEnabled(boolean)
        self.layout.thread.setEnabled(boolean)
        self.layout.undo.setEnabled(boolean)
        self.layout.redo.setEnabled(boolean)
        self.layout.search.setEnabled(boolean)
        self.layout.index_number.setEnabled(boolean)
        self.layout.settings.setEnabled(boolean)

    def Update_Size_Corner(self):
        self.imagine_preview.Set_Size(self.layout.preview_view.width(), self.layout.preview_view.height())
        self.imagine_grid.Set_Size(self.layout.imagine_grid.width(), self.layout.imagine_grid.height())
        self.imagine_reference.Set_Size_Corner(self.layout.imagine_reference.width(), self.layout.imagine_reference.height())
    def Update_Sizes_Middle(self):
        self.imagine_preview.Set_Size(self.layout.preview_view.width(), self.layout.preview_view.height())
        self.imagine_grid.Set_Size(self.layout.imagine_grid.width(), self.layout.imagine_grid.height())
        self.imagine_reference.Set_Size_Middle(self.layout.imagine_reference.width(), self.layout.imagine_reference.height())

    def Import_Pigment_O(self):
        self.MODULE_pigmento_bool = False
        try:
            dockers = Krita.instance().dockers()
            # if len(dockers) > 0:
            for i in range(0, len(dockers)):
                if dockers[i].objectName() == self.MODULE_pigmento_pyid:
                    self.pigment_o = dockers[i]
                    self.MODULE_pigmento_bool = True
                    self.imagine_preview.Set_Pigmento(True)
                    break
            else:
                QtCore.qDebug("IB error | Pigment.O module not imported")
        except:
            pass
    def Plugin_Showoff(self):
        # Scripter Code
        """
        import krita
        dockers = Krita.instance().dockers()
        for i in range(0, len(dockers)):
            if dockers[i].objectName() == "pykrita_imagine_board_docker":
                dockers[i].Plugin_Showoff()
        """
        # Geometry Change + Undocked Widget
        qrect = QRect(500, 500, 500, 600)
        value = self.setGeometry(qrect)

    def Progress_Value(self, value):
        self.layout.progress_bar.setValue(value)
    def Progress_Max(self, value):
        self.layout.progress_bar.setMaximum(value)

    def Click_Neutral(self, SIGNAL_NEUTRAL):
        if SIGNAL_NEUTRAL != "":
            self.layout.search.setPlaceholderText(SIGNAL_NEUTRAL)
        else:
            self.Menu_Display_Operation(self.dialog.menu_function_operation.currentText())

    def Screen_Swap(self):
        state = self.layout.screen.isChecked()
        self.layout.screen.setChecked(not state)
    def Full_Screen(self, boolean):
        # Variable
        self.full_screen = boolean
        # UI
        if boolean == True:
            # Float Full Screen
            self.widget_float = True
            self.setFloating(self.widget_float)
            # Monitor Zero Geometry
            screen_zero = QtWidgets.QDesktopWidget().screenGeometry(0) # Size of monitor zero 0
            width = screen_zero.width()
            height = screen_zero.height()
            self.setGeometry(0, 0, width, height)
            # Button
            self.layout.screen.setMaximumWidth(20)
            self.layout.screen.setIcon(Krita.instance().icon('arrow-down'))
        else:
            # Dock
            self.widget_float = False
            self.setFloating(self.widget_float)
            # Button
            self.layout.screen.setMaximumWidth(0)
            self.layout.screen.setIcon(Krita.instance().icon('zoom-vertical'))

    def Dict_Copy(self, active, load):
        keys = list(active.keys())
        for i in range(0, len(active)):
            try:
                active[keys[i]] = load[keys[i]]
            except:
                pass

    #endregion
    #region File Options ###########################################################
    def Folder_Open(self):
        file_dialog = QFileDialog(QWidget(self))
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        directory_path = file_dialog.getExistingDirectory(self, "Select Directory")
        directory_path = os.path.normpath( directory_path )
        if (directory_path != "" and directory_path != "." and self.directory_path != directory_path):
            self.Folder_Changer( [directory_path, True] )
    def Folder_Changer(self, SIGNAL_PATH):
        # Variables
        directory_path = SIGNAL_PATH[0]
        reset = SIGNAL_PATH[1]
        self.directory_path = os.path.normpath( directory_path )

        # Widgets
        self.layout.folder.setToolTip("Dir : " + os.path.basename(self.directory_path))
        if directory_path == "":
            directory = "directory"
        else:
            directory = self.directory_path
        self.dialog.export_directory.setText(directory)
        # Modules
        self.imagine_preview.Set_Directory(self.directory_path)
        self.imagine_preview.Clip_Off()
        self.os_folders.Set_Directory(self.directory_path)
        # Docker
        self.Watcher_Update()
        self.Filter_Keywords(reset)
        # Save
        Krita.instance().writeSetting("Imagine Board", "directory_path", str( self.directory_path ))

    def Filter_Keywords(self, reset):
        if self.widget_display == True:
            # Time Watcher
            start = QtCore.QDateTime.currentDateTimeUtc()

            # Reset to Page Zero
            if reset == True:
                self.comp_index = 0
                self.preview_index = 0
                self.line_preview = 0
                self.line_grid = 0
                self.Index_Values(0)

            search = ""
            if self.directory_path != "":
                if self.list_active == "Recent Documents":
                    files = []
                    for i in range(0, len(self.list_recentdocument)):
                        files.append(self.list_recentdocument[i])
                    files.reverse()
                    count = len(files)
                elif self.list_active == "Reference Images":
                    files = []
                    for i in range(0, len(self.list_pin_ref)):
                        files.append(self.list_pin_ref[i]["path"])
                    files.reverse()
                    count = len(files)
                else: # Folder
                    self.dir.setPath(self.directory_path)
                    self.dir.setSorting(self.filter_sort)
                    self.dir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
                    self.dir.setNameFilters(self.file_extension)
                    files = self.dir.entryInfoList()
                    count = len(files)

                # Progress Bar
                self.Progress_Value(0)
                self.Progress_Max(count)

                # Input parsing
                search = self.layout.search.text()
                Krita.instance().writeSetting("Imagine Board", "search", str( search ))
                keywords = search.split()
                remove = []
                if len(keywords) == 0:
                    keywords = [""]
                try:
                    n = keywords.index("not")
                    remove = keywords[n+1:]
                    keywords = keywords[:n]
                except:
                    remove = []

                # Search Cycle
                paths_new = []
                for k in range(0, len(keywords)):
                    for i in range(0, count):
                        item = files[i]
                        self.Progress_Value(i+1)
                        if (item != None and item != ""):
                            if (self.list_active == "Recent Documents" or self.list_active == "Reference Images"):
                                fn = os.path.basename(item)
                                fp = item
                            else:
                                fn = item.fileName()
                                fp = item.filePath()
                            if keywords[k] in fn and not fp in paths_new:
                                paths_new.append(fp)
                                # Remove Cycle
                                len_remove = len(remove)
                                if len_remove > 0:
                                    for r in range(0, len_remove):
                                        if remove[r] in fn:
                                            try:
                                                paths_new.remove(fp)
                                            except:
                                                pass

                # Construct base variables
                self.found_path = copy.deepcopy(paths_new)
                self.preview_max = len(self.found_path)
                self.grid_max = math.trunc(self.preview_max / self.grid_horz)
                if len(paths_new) > 0:
                    self.images_found = True
                    self.Index_Range(1, self.preview_max)
                else:
                    self.images_found = False
                    self.Index_Range(0, 0)

            # Update List and Display
            self.Display_Clean()
            self.Display_Update()

            # Progress Bar
            self.Progress_Value(0)
            self.Progress_Max(1)

            # Time Watcher
            end = QtCore.QDateTime.currentDateTimeUtc()
            delta = start.msecsTo(end)
            time = QTime(0,0).addMSecs(delta)
            try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Directory: " + os.path.basename(self.directory_path) + " | Search: " + search )
            except:pass
        else:
            self.Filter_Null()
    def Filter_Null(self):
        self.imagine_preview.Set_Default()
        self.dialog.menu_file.setText("")
        self.Index_Range(0, 0)
        self.Index_Values(0)

    def Display_Clean(self):
        if self.images_found == True:
            self.found_qpixmap = [self.null_qpixmap] * self.preview_max
        else:
            self.found_qpixmap = [self.null_qpixmap] * self.grid_table
    def Display_Update(self):
        # Images to Display
        self.Display_Sync()
        self.Display_Cache()
        self.Display_Preview()
        self.Display_Grid()
        self.Display_Reference()

        # Update
        if self.images_found == True:
            self.preview_path = self.found_path[self.preview_index]
            name = os.path.basename(self.preview_path)
            self.dialog.menu_file.setText(name)
        else:
            self.dialog.menu_file.setText("")

    def Display_Sync(self):
        if self.mode_index == 0:
            self.line_preview = math.trunc((self.preview_index) / self.grid_horz)
            if self.line_preview <= self.line_grid:
                self.line_grid = self.line_preview
            if self.line_preview >= (self.line_grid + self.grid_vert):
                self.line_grid = self.line_preview - self.grid_vert + 1
        if self.mode_index == 1:
            line = math.trunc((self.preview_index) / self.grid_horz)
            if line <= self.line_grid:
                self.line_grid = line
            if line >= (self.line_grid + self.grid_vert):
                self.line_grid = line - self.grid_vert + 1
        # Save
        Krita.instance().writeSetting("Imagine Board", "preview_index", str( self.preview_index ))
    def Display_Cache(self):
        # Only Affects Display Grid
        if self.images_found == True:
            # Display list in a build up fashion as you scroll through images
            grid_tl = self.line_grid * self.grid_horz
            grid_br = grid_tl + self.grid_table
            load_left = self.cache_load
            load_right = self.cache_load
            clean_left = self.cache_clean
            clean_right = self.cache_clean
            ll = Limit_Range(grid_tl - load_left, 0, self.preview_max)
            lr = Limit_Range(grid_br + load_right, 0, self.preview_max)
            cl = Limit_Range(grid_tl - clean_left, 0, self.preview_max)
            cr = Limit_Range(grid_br + clean_right, 0, self.preview_max)
            # Send Pixmaps to Modules
            try:
                for i in range(0, self.preview_max):
                    path = self.found_path[i]
                    # Populate Nearby
                    if (i >= ll and i <= lr):
                        if self.found_qpixmap[i].isNull() == True: # From List, Only load if the image is a null
                            qpixmap = QPixmap(path)
                            self.found_qpixmap[i] = qpixmap
                    # Clean Far Away
                    elif (i <= cl or i >= cr): # From List, Clean if image is too far away
                        self.found_qpixmap[i] = self.null_qpixmap
            except:
                pass
        else:
            self.found_qpixmap = [self.null_qpixmap] * self.grid_table
    def Display_Preview(self):
        if self.mode_index == 0:
            # UI Extra Panels
            self.Menu_CompPanel(False)
            self.Menu_AnimPanel(False)

            # Set Image to Render
            if self.images_found == True:

                self.preview_path = self.found_path[self.preview_index]
                extension = self.Path_Extension(self.preview_path)
                if extension in file_anim:
                    if QPixmap(self.preview_path).isNull() == False:
                        self.imagine_preview.Set_Anim_Preview(self.preview_path, self.anim_playpause)
                    else:
                        self.imagine_preview.Set_Default()
                elif extension in file_compress:
                    self.Namelist_Start(self.preview_path)
                else: # Normal Images
                    if QPixmap(self.preview_path).isNull() == False:
                        self.imagine_preview.Set_QPixmap_Preview(self.preview_path)
                    else:
                        self.imagine_preview.Set_Default()
            else:
                self.imagine_preview.Set_Default()
            self.imagine_preview.update()
    def Display_Grid(self):
        if self.mode_index == 1:
            # cunstruct pixmaps
            pixmaps = []
            n = 0
            if self.images_found == True:
                for v in range(0, self.grid_vert):
                    for h in range(0, self.grid_horz):
                        index = (self.line_grid * self.grid_horz) + n
                        try:
                            path = self.found_path[index]
                            extension = self.Path_Extension(path)
                            if extension in file_compress:
                                thumbnail = self.Comp_Thumbnail(path)
                                pixmaps.append([h, v, path, thumbnail])
                            else:
                                pixmaps.append([h, v, path, self.found_qpixmap[index]])
                        except:
                            pixmaps.append([h, v, self.null_path, self.null_qpixmap])
                        n += 1
            else:
                for v in range(0, self.grid_vert):
                    for h in range(0, self.grid_horz):
                        pixmaps.append([h, v, self.null_path, self.null_qpixmap])
            # send pixmaps
            self.imagine_grid.Set_QPixmaps(self.images_found, pixmaps)
            self.imagine_grid.update()
    def Display_Reference(self):
        if self.mode_index == 2:
            self.Board_Loader(self.list_pin_ref)
            self.imagine_reference.update()

    def Search_Previous(self, index_name):
        if self.images_found == True:
            # Default Index
            index = 0
            # Search Path
            for i in range(0, len(self.found_path)):
                if index_name == self.found_path[i]:
                    index = i
                    break
            # Swap Image
            self.Preview_GoTo(index)

    #endregion
    #region Threads ################################################################
    def Thumbnail_Start(self, SIGNAL_LOAD):
        # Prepare Widgets for Thread
        self.Index_Block(True)
        self.Widget_Enable(False)
        self.layout.progress_bar.setMaximum(self.preview_max)
        # Variables
        self.found_qpixmap = []
        self.counter = 0
        self.layout.index_number.setMinimum(0)
        self.layout.index_number.setMaximum(qt_max)

        # Range
        grid_tl = self.line_grid * self.grid_horz
        grid_br = grid_tl + self.grid_table
        limit_l = Limit_Range(grid_tl - self.cache_thread, 0, self.preview_max)
        limit_r = Limit_Range(grid_br + self.cache_thread, 0, self.preview_max)

        # Display
        self.placeholder_text = self.layout.search.placeholderText()
        self.layout.search.setPlaceholderText("Thumbnail Cache")

        # Start Threads operations
        self.thread_thumbnails = Thread_Thumbnails()
        self.thread_thumbnails.SIGNAL_IMAGE['QPixmap'].connect(self.Thumbnail_Image)
        self.thread_thumbnails.SIGNAL_RESET.connect(self.Thumbnail_Reset)
        self.thread_thumbnails.Variables_Run(os.path.basename(self.directory_path), self.found_path, self.preview_max, limit_l, limit_r)
        self.thread_thumbnails.start()
    def Thumbnail_Image(self, SIGNAL_IMAGE):
        # Recieve Image
        self.found_qpixmap.append(SIGNAL_IMAGE)
        # Display Progress
        self.layout.progress_bar.setValue(self.counter)
        self.layout.index_number.setValue(self.counter + 1)
        self.layout.progress_bar.update()
        self.layout.index_number.update()
        self.counter += 1 # Increment Counter for next cycle
    def Thumbnail_Reset(self, SIGNAL_RESET):
        self.thread_thumbnails.quit()
        self.layout.progress_bar.setValue(1)
        self.Index_Range(1, self.preview_max)
        self.Widget_Enable(True)
        self.Index_Block(False)
        self.Preview_GoTo(self.preview_index)
        self.layout.search.setPlaceholderText(self.placeholder_text)

    def Namelist_Start(self, path):
        # Prepare Widgets for Thread
        self.imagine_preview.Set_Default()
        self.Index_Block(True)
        self.Widget_Enable(False)

        # Display
        self.placeholder_text = self.layout.search.placeholderText()
        self.layout.search.setPlaceholderText("Compressed Check")

        # Delete previous Thread if it exists
        try:
            self.thread_namelist.disconnect()
            self.thread_namelist.quit()
        except:
            pass

        # Create New Thread
        self.thread_namelist = Thread_NameList()
        self.thread_namelist.SIGNAL_PROGRESS_VALUE.connect(self.Progress_Value)
        self.thread_namelist.SIGNAL_PROGRESS_MAX.connect(self.Progress_Max)
        self.thread_namelist.SIGNAL_COMP_MAX.connect(self.Comp_Range)
        self.thread_namelist.SIGNAL_NAMELIST.connect(self.Namelist_Input)
        self.thread_namelist.Variables_Run(path)
        self.thread_namelist.start()
    def Namelist_Input(self, lista):
        # Thread
        self.thread_namelist.quit()
        # Widgets
        self.Widget_Enable(True)
        self.Index_Block(False)
        self.layout.search.setPlaceholderText(self.placeholder_text)
        # Parsing Variabls
        path = lista[0]
        name_list = lista[1]
        string = lista[2]
        self.comp_index = 0
        self.comp_max = len(name_list)

        # Update
        if len(name_list) > 0:
            # Log Viewer
            try:QtCore.qDebug(string)
            except:pass
            # Update
            self.Menu_CompPanel(True)
            self.imagine_preview.Set_Comp_Preview(path, name_list)
            self.imagine_preview.Set_Unpress()

    #endregion
    #region Signals ################################################################
    # Widgets
    def Context_Mode(self, SIGNAL):
        self.Menu_Index(SIGNAL)

    # Mouse Stylus
    def Drag_Drop(self, image_path):
        thumb_size = 200
        extension = os.path.splitext(image_path)[1][1:]
        if extension == "svg":
            # QImage
            qimage = QImage(image_path)
            try: qimage_scaled = qimage.scaled(thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except: qimage_scaled = qimage
            qpixmap = QPixmap().fromImage(qimage_scaled)
            # MimeData
            qimage = QImage(image_path)
            mimedata = QMimeData()
            url = QUrl().fromLocalFile(image_path)
            mimedata.setUrls([url])
            mimedata.setImageData(qimage)
            mimedata.setData(image_path, image_path.encode())
            # Clipboard
            clipboard = QApplication.clipboard().setImage(qimage)
            # Drag
            drag = QDrag(self)
            drag.setMimeData(mimedata)
            drag.setPixmap(qpixmap)
            drag.setHotSpot(QPoint(qimage_scaled.width() / 2 , qimage_scaled.height() / 2))
            drag.exec_(Qt.CopyAction)
        else:
            # QImage
            reader = QImageReader(image_path)
            if self.clip_state == True:
                reader.setClipRect(QRect(self.clip_px, self.clip_py, self.clip_dw, self.clip_dh))
            qimage = reader.read()
            try:
                qimage_scaled = qimage.scaled(thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except:
                qimage_scaled = qimage
            qpixmap = QPixmap().fromImage(qimage_scaled)
            # MimeData
            mimedata = QMimeData()
            url = QUrl().fromLocalFile(image_path)
            mimedata.setUrls([url])
            if (self.insert_size_bool == True and (self.canvas() is not None) and (self.canvas().view() is not None)):
                ad = Krita.instance().activeDocument()
                scale_width = ad.width() * self.image_scale
                scale_height = ad.height() * self.image_scale
            else:
                scale_width = qimage.width() * self.image_scale
                scale_height = qimage.height() * self.image_scale
            try:
                mimedata.setImageData(qimage.scaled(scale_width, scale_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except:
                mimedata.setImageData(qimage)
            # Clipboard
            clipboard = QApplication.clipboard().setImage(qimage)
            # Drag
            drag = QDrag(self)
            drag.setMimeData(mimedata)
            drag.setPixmap(qpixmap)
            drag.setHotSpot(QPoint(qimage_scaled.width() / 2 , qimage_scaled.height() / 2))
            drag.exec_(Qt.CopyAction)

    # File
    def File_Clip(self, SIGNAL_CLIP):
        self.clip_state = SIGNAL_CLIP[0]
        self.clip_px = SIGNAL_CLIP[1]
        self.clip_py = SIGNAL_CLIP[2]
        self.clip_dw = SIGNAL_CLIP[3]
        self.clip_dh = SIGNAL_CLIP[4]
    def File_Location(self, SIGNAL_LOCATION):
        kernel = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux
        if kernel == "winnt": # Windows
            FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
            subprocess.run([FILEBROWSER_PATH, '/select,', os.path.normpath(SIGNAL_LOCATION)])
        elif kernel == "linux": # Linux
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(SIGNAL_LOCATION)))
        elif okernels == "darwin": # MAC
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(SIGNAL_LOCATION)))
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(SIGNAL_LOCATION)))

    # Insert
    def Insert_Document(self, SIGNAL_NEW_DOCUMENT):
        # Create Document
        document = Krita.instance().openDocument(SIGNAL_NEW_DOCUMENT)
        Application.activeWindow().addView(document)
        # Show Message
        Krita.instance().activeWindow().activeView().showFloatingMessage(
            "IB : New Document",
            Krita.instance().icon('document-new'),
            5000,
            0
            )
    def Insert_Layer(self, SIGNAL_INSERT_LAYER):
        if ((self.canvas() is not None) and (self.canvas().view() is not None) and self.preview_max > 0):
            image_path = SIGNAL_INSERT_LAYER
            extension = os.path.splitext(image_path)[1][1:]
            if extension == "svg":
                # MimeData
                mimedata = QMimeData()
                url = QUrl().fromLocalFile(image_path)
                mimedata.setUrls([url])
                mimedata.setImageData(QPixmap(image_path))
                mimedata.setData(image_path, image_path.encode())
                # Clipboard
                clipboard = QApplication.clipboard().setMimeData(mimedata)
                # Place Image
                Krita.instance().action('edit_paste').trigger()
                Krita.instance().activeDocument().refreshProjection()
                Krita.instance().activeWindow().activeView().showFloatingMessage(
                    "IB : Vector Layer Insert",
                    Krita.instance().icon('vectorLayer'),
                    5000,
                    0
                    )
            else: # Default Case for all static Images. This excludes animated GIFs.
                # QImage
                reader = QImageReader(image_path)
                if self.clip_state == True:
                    reader.setClipRect(QRect(self.clip_px, self.clip_py, self.clip_dw, self.clip_dh))
                qimage = reader.read()
                if QPixmap().fromImage(qimage).isNull() == False:
                    if self.insert_size_bool == True:
                        ad = Krita.instance().activeDocument()
                        doc_width = ad.width()
                        doc_height = ad.height()
                        qimage = qimage.scaled(doc_width * self.image_scale, doc_height * self.image_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    else:
                        size = max(qimage.size().width(), qimage.size().height())
                        qimage = qimage.scaled(size * self.image_scale, size * self.image_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # MimeData
                mimedata = QMimeData()
                url = QUrl().fromLocalFile(image_path)
                mimedata.setUrls([url])
                mimedata.setImageData(qimage)
                # Clipboard
                clipboard = QApplication.clipboard().setImage(qimage)
                # Place Image
                Krita.instance().action('edit_paste').trigger()
                Krita.instance().activeDocument().refreshProjection()
                Krita.instance().activeWindow().activeView().showFloatingMessage(
                    "IB : Paint Layer Insert",
                    Krita.instance().icon('paintLayer'),
                    5000,
                    0
                    )
    def Insert_Reference(self, SIGNAL_INSERT_REFERENCE):
        if ((self.canvas() is not None) and (self.canvas().view() is not None) and self.preview_max > 0):
            reader = QImageReader(SIGNAL_INSERT_REFERENCE)
            if self.clip_state == True:
                reader.setClipRect(QRect(self.clip_px, self.clip_py, self.clip_dw, self.clip_dh))
            qimage = reader.read()
            if QPixmap().fromImage(qimage).isNull() == False:
                if self.insert_size_bool == True:
                    ad = Krita.instance().activeDocument()
                    doc_width = ad.width()
                    doc_height = ad.height()
                    qimage = qimage.scaled(doc_width * self.image_scale, doc_height * self.image_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    size = max(qimage.size().width(), qimage.size().height())
                    qimage = qimage.scaled(size * self.image_scale, size * self.image_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # MimeData
            mimedata = QMimeData()
            url = QUrl().fromLocalFile(SIGNAL_INSERT_REFERENCE)
            mimedata.setUrls([url])
            mimedata.setImageData(qimage)
            # Clipboard
            clipboard = QApplication.clipboard().setImage(qimage)
            # Place Image
            Krita.instance().action('paste_as_reference').trigger()
            Krita.instance().activeDocument().refreshProjection()
            Krita.instance().activeWindow().activeView().showFloatingMessage(
                "IB : Reference Insert",
                Krita.instance().icon('krita_tool_reference_images'),
                5000,
                0
                )

    # Extension
    def Shortcut_Browse(self, SIGNAL_BROWSE):
        if self.mode_index == 0:
            if self.menu_comp == True:
                self.Preview_Comp_Increment(SIGNAL_BROWSE)
            else:
                self.Preview_Index_Increment(SIGNAL_BROWSE)
        if self.mode_index == 1:
            self.Grid_Index_Increment(SIGNAL_BROWSE)
        if self.mode_index == 2:
            if SIGNAL_BROWSE == -1:
                self.Reference_Undo()
            if SIGNAL_BROWSE == 1:
                self.Reference_Redo()

    #endregion
    #region Index ##################################################################
    def Index_Block(self, boolean):
        self.layout.index_slider.blockSignals(boolean)
        self.layout.index_number.blockSignals(boolean)
    def Index_Range(self, minimum, maximum):
        # Slider
        self.layout.index_slider.setMinimum(minimum)
        self.layout.index_slider.setMaximum(maximum)
        # Number
        self.layout.index_number.setMinimum(minimum)
        self.layout.index_number.setMaximum(maximum)
        self.layout.index_number.setSuffix(":" + str(maximum))
    def Index_Enable(self, bool):
        if self.slideshow_play == False:
            self.layout.index_slider.setEnabled(bool)
            self.layout.index_number.setEnabled(bool)
    def Index_Values(self, value):
        self.Index_Block(True)
        self.layout.index_slider.setValue(value+1)
        self.layout.index_number.setValue(value+1)
        self.Index_Block(False)

    def Index_Slider(self, value):
        self.Index_Block(True)
        self.preview_index = int(value-1) # Humans start at 1 and script starts at 0
        self.layout.index_number.setValue(value)
        if self.images_found == True:
            self.Display_Update()
        self.Index_Block(False)
    def Index_Number(self, value):
        self.Index_Block(True)
        self.preview_index = int(value-1) # Humans start at 1 and script starts at 0
        self.layout.index_slider.setValue(int(value))
        if self.images_found == True:
            self.Display_Update()
        self.Index_Block(False)

    def Preview_Index_Increment(self, SIGNAL_UNIT):
        if self.images_found == True:
            if self.anim_playpause == False:
                self.Preview_PlayPause(True)
            self.preview_index += SIGNAL_UNIT
            self.preview_index = Limit_Range(self.preview_index, 0, self.preview_max-1)
            self.Index_Values(self.preview_index)
            self.Display_Update()
    def Preview_Comp_Increment(self, SIGNAL_UNIT):
        value = self.layout.comp_slider.value() + SIGNAL_UNIT
        self.layout.comp_slider.setValue(value)
    def Grid_Index_Increment(self, SIGNAL_UNIT):
        if self.anim_playpause == False:
            self.Preview_PlayPause(True)
        self.line_grid += Limit_Range(SIGNAL_UNIT, 0, self.preview_max-1)
        self.preview_index += (SIGNAL_UNIT * self.grid_horz)
        self.preview_index = Limit_Range(self.preview_index, 0, self.preview_max-1)
        self.Index_Values(self.preview_index)
        if self.images_found == True:
            self.Display_Update()

    #endregion
    #region Compression ############################################################
    def Comp_Block(self, boolean):
        self.layout.comp_slider.blockSignals(boolean)
        self.layout.comp_number.blockSignals(boolean)
    def Comp_Range(self, maximum):
        # Slider
        self.layout.comp_slider.setValue(1)
        self.layout.comp_slider.setMinimum(1)
        self.layout.comp_slider.setMaximum(maximum)
        # Number
        self.layout.comp_number.setValue(1)
        self.layout.comp_number.setMinimum(1)
        self.layout.comp_number.setMaximum(maximum)
        self.layout.comp_number.setSuffix(":" + str(maximum))
    def Comp_Values(self, value):
        self.Comp_Block(True)
        self.layout.comp_slider.setValue(value+1)
        self.layout.comp_number.setValue(value+1)
        self.Comp_Block(False)

    def Comp_Slider(self, value):
        self.Comp_Block(True)
        self.comp_index = int(value-1) # Humans start at 1 and script starts at 0
        self.layout.comp_number.setValue(value)
        self.imagine_preview.Comp_Frame(self.comp_index)
        self.Comp_Block(False)
    def Comp_Number(self, value):
        self.Comp_Block(True)
        self.comp_index = int(value-1) # Humans start at 1 and script starts at 0
        self.layout.comp_slider.setValue(value)
        self.imagine_preview.Comp_Frame(self.comp_index)
        self.Comp_Block(False)

    def Preview_Comp_Increment(self, SIGNAL_UNIT):
        if self.menu_comp == True:
            self.Comp_Block(True)
            self.comp_index += SIGNAL_UNIT
            self.comp_index = Limit_Range(self.comp_index, 0, self.comp_max-1)
            self.Comp_Values(self.comp_index)
            self.imagine_preview.Comp_Frame(self.comp_index)
            self.Comp_Block(False)

    def Comp_Thumbnail(self, path):
        thumbnail = self.null_qpixmap
        try:
            if zipfile.is_zipfile(path):
                archive = zipfile.ZipFile(path, "r")
                name_list = archive.namelist()
                for i in range(0, len(name_list)):
                    try:
                        archive_open = archive.open(name_list[i])
                        archive_read = archive_open.read()
                        image = QImage()
                        image.loadFromData(archive_read)
                        pixmap = QPixmap().fromImage(image)
                        if pixmap.isNull() == False:
                            thumbnail = pixmap
                            break
                    except:
                        pass
        except:
            pass
        return thumbnail

    #endregion
    #region Preview ################################################################
    def Preview_GoTo(self, SIGNAL_VALUE):
        if self.images_found == True:
            self.preview_index = Limit_Range(SIGNAL_VALUE, 0, self.preview_max-1)
            self.Index_Values(self.preview_index)
            self.Display_Update()

    def Preview_Random(self, SIGNAL_RANDOM):
        random_value = self.preview_index
        while random_value == self.preview_index:
            random_value = Random_Range(self.preview_max-1)
        self.Preview_GoTo(random_value)
    def Preview_Color(self, SIGNAL_COLOR):
        # QImage RGB values
        kac_1 = SIGNAL_COLOR["red"]
        kac_2 = SIGNAL_COLOR["green"]
        kac_3 = SIGNAL_COLOR["blue"]
        # Pigmento Apply
        if self.MODULE_pigmento_bool == True:
            color = self.pigment_o.Script_Input_FG("RGB", kac_1, kac_2, kac_3, 0)
            self.imagine_preview.Set_Color_Display(color["d_rgb_1"], color["d_rgb_2"], color["d_rgb_3"])
        else:
            if ((self.canvas() is not None) and (self.canvas().view() is not None)):
                # Document
                d_cm = Krita.instance().activeDocument().colorModel()
                d_cd = Krita.instance().activeDocument().colorDepth()
                d_cp = Krita.instance().activeDocument().colorProfile()
                d_ac = Krita.instance().activeWindow().activeView().canvas()
                # Managed Colors RGB only
                managed_color = ManagedColor(d_cm, d_cd, d_cp)
                comp = managed_color.components()
                if (d_cm == "A" or d_cm == "GRAYA"):
                    comp = [kac_1, 1]
                if d_cm == "RGBA":
                    if (d_cd == "U8" or d_cd == "U16"):
                        comp = [kac_3, kac_2, kac_1, 1]
                    if (d_cd == "F16" or d_cd == "F32"):
                        comp = [kac_1, kac_2, kac_3, 1]
                managed_color.setComponents(comp)
                # Color for Canvas
                display = managed_color.colorForCanvas(d_ac)
                kac_1 = display.redF()
                kac_2 = display.greenF()
                kac_3 = display.blueF()
                # Apply Color
                Krita.instance().activeWindow().activeView().setForeGroundColor(managed_color)
        # Display Color on Self
        self.imagine_preview.Set_Color_Display(kac_1, kac_2, kac_3)

    def Preview_SlideShow_Switch(self, SIGNAL_SLIDESHOW):
        self.slideshow_play = SIGNAL_SLIDESHOW
        if self.slideshow_play == True:
            # Icons
            self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-stop'))
            self.layout.slideshow.setToolTip("SlideShow Stop")
            # Enabled
            self.layout.mode.setEnabled(False)
            self.layout.folder.setEnabled(False)
            self.layout.thread.setEnabled(False)
            self.layout.search.setEnabled(False)
            self.layout.index_slider.setEnabled(False)
            self.layout.index_number.setEnabled(False)
            # Timer
            self.timer.start(self.slideshow_time)
        else:
            # Icons
            self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-start'))
            self.layout.slideshow.setToolTip("SlideShow Play")
            # Enabled
            self.layout.mode.setEnabled(True)
            self.layout.folder.setEnabled(True)
            self.layout.thread.setEnabled(True)
            self.layout.search.setEnabled(True)
            self.layout.index_slider.setEnabled(True)
            self.layout.index_number.setEnabled(True)
            # Timer
            self.timer.stop()
        self.dirty = 5
    def Preview_SlideShow_Play(self):
        if self.slideshow_sequence == "Linear":
            loop = self.preview_index + 1
            self.preview_index = Limit_Loop(loop, self.preview_max-1)
            self.Preview_GoTo(self.preview_index)
        if self.slideshow_sequence == "Random":
            # Clear for a full Cycle
            if len(self.slideshow_lottery) == self.preview_max:
                self.slideshow_lottery.clear()
            # Lottery Random
            number = random.randint(0, self.preview_max-1)
            while number in self.slideshow_lottery:
                number = random.randint(0, self.preview_max-1)
            self.slideshow_lottery.append(number)
            self.Preview_GoTo(number)

    def Preview_PlayPause(self, playpause):
        self.anim_playpause = playpause
        if self.anim_playpause == True:
            self.Preview_Play()
        else:
            self.Preview_Pause()
    def Preview_Play(self):
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_pause'))
        self.imagine_preview.Anim_Play()
    def Preview_Pause(self):
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_play'))
        self.imagine_preview.Anim_Pause()
    def Preview_Frame_Back(self):
        self.imagine_preview.Anim_Frame_Back()
    def Preview_Frame_Forward(self):
        self.imagine_preview.Anim_Frame_Forward()
    def Preview_Frame_Display(self, SIGNAL_FRAME):
        self.layout.anim_frame_display.setText(SIGNAL_FRAME)
    def Preview_Screenshot(self):
        self.imagine_preview.Anim_Screenshot()

    #endregion
    #region Grid ###################################################################
    def Grid_Name(self, SIGNAL_NAME):
        num = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_NAME[0], SIGNAL_NAME[1])
        if (self.images_found == True and num < self.preview_max):
            self.preview_index = Limit_Range(num, 0, self.preview_max-1)
            self.Index_Values(self.preview_index)
            name = os.path.basename(self.found_path[num])
        else:
            name = ""
        self.dialog.menu_file.setText(name)
    def Grid_Preview(self, SIGNAL_PREVIEW):
        self.preview_index = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_PREVIEW[0], SIGNAL_PREVIEW[1])
        self.Preview_GoTo(self.preview_index)
        self.Menu_Index(0)

    #endregion
    #region Reference ##############################################################
    def Reference_Insert(self, SIGNAL_REF):
        # Parsing
        path = SIGNAL_REF["path"]
        text = SIGNAL_REF["text"]
        origin_x = SIGNAL_REF["origin_x"]
        origin_y = SIGNAL_REF["origin_y"]

        #region Image
        point_size = 15
        if (text == None or text == ""):
            path = os.path.normpath(path)
            qpixmap = QPixmap(path)
            if self.ref_original == True:
                limit_w = Limit_Range(qpixmap.width(), 1, self.ref_limit)
                limit_h = Limit_Range(qpixmap.height(), 1, self.ref_limit)
                qpixmap_scaled = qpixmap.scaled(limit_w, limit_h, Qt.KeepAspectRatio, self.tn_smooth_scale)
            else:
                size = 100
                qpixmap_scaled = qpixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, self.tn_smooth_scale)
            width = qpixmap_scaled.width()
            height = qpixmap_scaled.height()
        else:
            qfont = QFont("Tahoma")
            qfont.setPointSizeF(point_size)

            font_metrics = QFontMetricsF(qfont)
            text_rect = font_metrics.boundingRect(text)
            width = text_rect.width()
            height = text_rect.height()

            qpixmap = QPixmap(width, height)
        point_ratio = height / point_size
        w2 = width * 0.5
        h2 = height * 0.5

        #endregion
        #region Variables
        # Sorting
        index = 0
        active = False
        select = False
        pack = False
        # Text
        color = "#595959"
        # Move
        relative_x = 0
        relative_y = 0
        # Rotation
        rotation_neutral = Trig_2D_Points_Lines_Angle(width,0, 0,0, width, height)
        rotation_offset = 0
        # Scale
        scale_size = Trig_2D_Points_Distance(0,0, width*0.5,height*0.5)
        scale_relative = 1
        # Draw
        draw_x = origin_x - w2
        draw_y = origin_y - h2
        draw_w = width
        draw_h = height
        draw_xw = origin_x + w2
        draw_yh = origin_y + h2
        if self.clip_state == True:
            pixmap_w = qpixmap.width()
            pixmap_h = qpixmap.height()
            cl = (self.clip_px) / pixmap_w
            cr = (self.clip_px + self.clip_dw) / pixmap_w
            ct = (self.clip_py) / pixmap_h
            cb = (self.clip_py + self.clip_dh) / pixmap_h
        else:
            cl = 0
            cr = 1
            ct = 0
            cb = 1
        # Bounding Box
        bl = origin_x - w2
        br = origin_x + w2
        bt = origin_y - h2
        bb = origin_y + h2
        # Dimensions
        perimeter = (2 * width) + (2 * height)
        area = width * height
        if (width != 0 and height != 0):
            ratio = width / height
        else:
            ratio = 0
        pack = False
        # Edits
        edit_grayscale = False
        edit_flip_x = False
        edit_flip_y = False

        #endregion
        #region Pin
        pin = {
            # Path to File (new entries to "Board_Loader" also)
            "path"       : path,
            # Sorting
            "index"      : index,
            "active"     : active,
            "select"     : select,
            "pack"       : pack,
            # Text
            "text"       : text,
            "color"      : color,
            "pis"        : point_size,
            "pir"        : point_ratio,
            # Move
            "ox"         : origin_x,
            "oy"         : origin_y,
            "rx"         : relative_x,
            "ry"         : relative_y,
            # Rotation
            "rn"         : rotation_neutral,
            "ro"         : rotation_offset,
            # Scale
            "ss"         : scale_size,
            "sr"         : scale_relative,
            # Draw
            "dx"         : draw_x,
            "dy"         : draw_y,
            "dw"         : draw_w,
            "dh"         : draw_h,
            "dxw"        : draw_xw,
            "dyh"        : draw_yh,
            # Clip
            "cl"         : cl, # 0-1 left-right
            "cr"         : cr, # 0-1 left-right
            "ct"         : ct, # 0-1 top-bot
            "cb"         : cb, # 0-1 top-bot
            # Bound Box
            "bl"         : bl,
            "br"         : br,
            "bt"         : bt,
            "bb"         : bb,
            # Dimensions
            "perimeter"  : perimeter,
            "area"       : area,
            "ratio"      : ratio,
            # Edits
            "egs"        : edit_grayscale,
            "efx"        : edit_flip_x,
            "efy"        : edit_flip_y,
            # Pixmap Load (This is never Loaded, Module Loads once recieved)
            "qpixmap"    : None,
            }

        self.list_pin_ref.append(pin)
        self.imagine_reference.Pin_Ref(pin)

        #endregion

    def Board_Loader(self, lista):
        # Progress Bar
        self.Progress_Value(0)
        self.Progress_Max(len(lista))

        self.list_pin_ref = []
        for i in range(0, len(lista)):
            # Progress Bar
            self.Progress_Value(i+1)

            # Variables
            pin = {}
            item_i = lista[i]

            # Path
            try:
                path = item_i["path"]
                check_path = os.path.exists(path)
            except:
                path = None
                check_path = None
            # Text
            try:
                check_text = item_i["text"]
            except:
                check_text = None

            # Construct Display
            if (check_path == True or check_text != None):
                # Variables
                ox = 100
                oy = 100
                if check_path == True:
                    qpixmap = QPixmap(path)
                    width = qpixmap.width()
                    height = qpixmap.height()
                else:
                    width = 1
                    height = 1

                # Path
                try:     pin["path"] = path
                except:  pin["path"] = None
                # Sorting
                try:     pin["index"] = item_i["index"]
                except:  pin["index"] = 0
                try:     pin["active"] = item_i["active"]
                except:  pin["active"] = False
                try:     pin["select"] = item_i["select"]
                except:  pin["select"] = False
                try:     pin["pack"] = item_i["pack"]
                except:  pin["pack"] = False
                # Text
                try:     pin["text"] = item_i["text"]
                except:  pin["text"] = None
                try:     pin["color"] = item_i["color"]
                except:  pin["color"] = "#595959"
                try:     pin["pis"] = item_i["pis"]
                except:  pin["pis"] = 15
                try:     pin["pir"] = item_i["pir"]
                except:  pin["pir"] = 24/15
                # Move
                try:     pin["ox"] = item_i["ox"]
                except:  pin["ox"] = ox
                try:     pin["oy"] = item_i["oy"]
                except:  pin["oy"] = oy
                try:     pin["rx"] = item_i["rx"]
                except:  pin["rx"] = 0
                try:     pin["ry"] = item_i["ry"]
                except:  pin["ry"] = 0
                # Rotation
                try:     pin["rn"] = item_i["rn"]
                except:  pin["rn"] = Trig_2D_Points_Lines_Angle(width,0, 0,0, width, height)
                try:     pin["ro"] = item_i["ro"]
                except:  pin["ro"] = 0
                # Scale
                try:     pin["ss"] = item_i["ss"]
                except:  pin["ss"] = Trig_2D_Points_Distance(0,0, width,height) * 0.5
                try:     pin["sr"] = item_i["sr"]
                except:  pin["sr"] = 1
                # Draw
                try:     pin["dx"] = item_i["dx"]
                except:  pin["dx"] = ox - (width * 0.5)
                try:     pin["dy"] = item_i["dy"]
                except:  pin["dy"] = oy - (height * 0.5)
                try:     pin["dw"] = item_i["dw"]
                except:  pin["dw"] = width
                try:     pin["dh"] = item_i["dh"]
                except:  pin["dh"] = height
                try:     pin["dxw"] = item_i["dxw"]
                except:  pin["dxw"] = ox + (width * 0.5)
                try:     pin["dyh"] = item_i["dyh"]
                except:  pin["dyh"] = oy + (height * 0.5)
                # Clip
                try:     pin["cl"] = item_i["cl"]
                except:  pin["cl"] = 0
                try:     pin["cr"] = item_i["cr"]
                except:  pin["cr"] = 1
                try:     pin["ct"] = item_i["ct"]
                except:  pin["ct"] = 0
                try:     pin["cb"] = item_i["cb"]
                except:  pin["cb"] = 1
                # Bounding Box
                try:     pin["bl"] = item_i["bl"]
                except:  pin["bl"] = ox - (width * 0.5)
                try:     pin["br"] = item_i["br"]
                except:  pin["br"] = oy - (height * 0.5)
                try:     pin["bt"] = item_i["bt"]
                except:  pin["bt"] = ox + (width * 0.5)
                try:     pin["bb"] = item_i["bb"]
                except:  pin["bb"] = oy + (height * 0.5)
                # Dimensions
                try:     pin["perimeter"] = item_i["perimeter"]
                except:  pin["perimeter"] = (2*width) + (2*height)
                try:     pin["area"] = item_i["area"]
                except:  pin["area"] = width * height
                try:     pin["ratio"] = item_i["ratio"]
                except:  pin["ratio"] = width / height
                # Edits
                try:     pin["egs"] = item_i["egs"]
                except:  pin["egs"] = False
                try:     pin["efx"] = item_i["efx"]
                except:  pin["efx"] = False
                try:     pin["efy"] = item_i["efy"]
                except:  pin["efy"] = False

                # Pixmap Load
                pin["qpixmap"] = None
                self.list_pin_ref.append(pin)

        # Progress Bar
        self.Progress_Value(0)
        self.Progress_Max(1)

        # Update Board
        if len(self.list_pin_ref) > 0:
            self.imagine_reference.Board_Load(self.list_pin_ref)
    def Board_Save(self, SIGNAL_SAVE):
        # Parsing
        if self.list_pin_ref != SIGNAL_SAVE:
            self.list_pin_ref = SIGNAL_SAVE

        # Watcher
        self.Watcher_Update()
        # Save
        Krita.instance().writeSetting("Imagine Board", "list_pin_ref", str(self.list_pin_ref) )
        self.Annotation_Save()

    def Reference_Cache(self, list_reference):
        # Clear Previous
        if self.undocache_index > 0:
            self.undocache_list = self.undocache_list[self.undocache_index:]
            self.undocache_index = 0
        # Update State List
        self.undocache_list.insert(0, list_reference)
        # Crop Excess from List
        if len(self.undocache_list) > self.undocache_size:
            self.undocache_list = self.undocache_list[:self.undocache_size]
    def Reference_Undo(self):
        limit = min(self.undocache_size, len(self.undocache_list))
        self.undocache_index = Limit_Range(self.undocache_index + 1, 0, limit)
        if (len(self.undocache_list) > 0 and self.undocache_index < len(self.undocache_list) and self.undocache_index < self.undocache_size):
            self.Board_Loader(self.undocache_list[self.undocache_index])
    def Reference_Redo(self):
        limit = min(self.undocache_size, len(self.undocache_list))
        self.undocache_index = Limit_Range(self.undocache_index - 1, 0, limit)
        if (len(self.undocache_list) > 0 and self.undocache_index < len(self.undocache_list) and self.undocache_index < self.undocache_size):
            self.Board_Loader(self.undocache_list[self.undocache_index])

    #endregion
    #region Information ############################################################
    def Information_Block_Signals(self, bool):
        # Signals
        self.dialog.info_title.blockSignals(bool)
        self.dialog.info_subject.blockSignals(bool)
        self.dialog.info_keyword.blockSignals(bool)
        self.dialog.info_license.blockSignals(bool)
        self.dialog.info_description.blockSignals(bool)
        self.dialog.info_abstract.blockSignals(bool)
    def Information_Read(self):
        # Block Signals
        self.Information_Block_Signals(True)
        # Variables
        file_name = ""
        self.info = {
            'title': "",
            'description': "",
            'subject': "",
            'abstract': "",
            'keyword': "",
            'initial-creator': "",
            'editing-cycles': "",
            'editing-time': "",
            'date': "",
            'creation-date': "",
            'language': "",
            'license': "",
            'full-name': "",
            'creator-first-name': "",
            'creator-last-name': "",
            'initial': "",
            'author-title': "",
            'position': "",
            'company': "",
            }
        t_editing_cycles = ""
        t_editing_time = ""
        d_date = ""
        d_creation_date = ""
        delta_creation = ""
        creator_fl_name = ""
        self.contact = []

        # Active Document is Open
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            try:
                # Active Document
                ki = Krita.instance()
                ad = ki.activeDocument()
                text = ad.documentInfo()
                ET = xml.etree.ElementTree
                root = ET.fromstring(text)

                for r in root:
                    for i in r:
                        # build xml
                        index = i.tag.split('}')[1]
                        entry = i.text
                        if (entry == "" or entry == None):
                            entry = ""
                        self.info[index] = entry
                        # build contacts
                        if index == "contact":
                            self.contact.append(entry)

                # Calculations
                file_name = str(ad.fileName())
                t_editing_cycles = self.time_to_string( self.cycles_to_time( self.info["editing-cycles"] ) )
                t_editing_time = self.time_to_string( self.cycles_to_time( self.info["editing-time"] ) )
                d_date = self.display_date( self.info["date"] )
                d_creation_date = self.display_date( self.info["creation-date"] )
                if d_creation_date != "":
                    delta_creation = self.time_delta(
                        int(d_creation_date[0:4]),
                        int(d_creation_date[5:7]),
                        int(d_creation_date[8:10]),
                        int(d_creation_date[11:13]),
                        int(d_creation_date[14:16]),
                        int(d_creation_date[17:19]),
                        int(d_date[0:4]),
                        int(d_date[5:7]),
                        int(d_date[8:10]),
                        int(d_date[11:13]),
                        int(d_date[14:16]),
                        int(d_date[17:19]),
                        )
                creator_fl_name = self.info["creator-first-name"] + " " + self.info["creator-last-name"]

                # Costs (Edit time avoids idle inflation cost)
                self.Money_Cost( self.cycle_to_hour( self.info["editing-time"] ) )
            except:
                self.Money_Rate(0)
        else:
            self.Money_Rate(0)

        # Place Values
        self.dialog.info_path.setText(file_name)

        self.dialog.info_title.setText(self.info["title"])
        self.dialog.info_subject.setText(self.info["subject"])
        self.dialog.info_keyword.setText(self.info["keyword"])
        self.dialog.info_license.setText(self.info["license"])
        self.dialog.info_abstract.setText(self.info["abstract"]) # Abstract is Description inside Krita
        self.dialog.info_description.setText(self.info["description"]) # Description is Abstract inside Krita
        self.dialog.info_language.setText(self.info["language"])

        self.dialog.info_edit_cycles.setText(str(self.info["editing-cycles"]) + str(t_editing_cycles))
        self.dialog.info_edit_time.setText(str(self.info["editing-time"]) + str(t_editing_time))
        self.dialog.info_date.setText(d_date)
        self.dialog.info_creation.setText(d_creation_date + delta_creation)

        self.dialog.info_creator.setText(self.info["initial-creator"])
        self.dialog.info_nick_name.setText(self.info["full-name"])
        self.dialog.info_full_name.setText(creator_fl_name)
        self.dialog.info_initials.setText(self.info["initial"])
        self.dialog.info_author_title.setText(self.info["author-title"])
        self.dialog.info_position.setText(self.info["position"])
        self.dialog.info_company.setText(self.info["company"])
        self.dialog.info_contact.clear()
        for i in range(0, len(self.contact)):
            self.dialog.info_contact.addItem(str(self.contact[i]))

        # Block Signals
        self.Information_Block_Signals(False)
    def Information_Save(self):
        # Active Document is Open
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            new_title = str(self.dialog.info_title.text())
            new_description = str(self.dialog.info_description.text())
            new_subject = str(self.dialog.info_subject.text())
            new_abstract = str(self.dialog.info_abstract.toPlainText())
            new_keyword = str(self.dialog.info_keyword.text())
            new_language = str(self.dialog.info_language.text())
            new_license = str(self.dialog.info_license.text())

            contacts = ""
            for i in range(0, len(self.contact)):
                contacts += "<contact>"+self.contact[i]+"</contact>\n"

            # Save string to Active Document
            info_string = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE document-info PUBLIC '-//KDE//DTD document-info 1.1//EN' 'http://www.calligra.org/DTD/document-info-1.1.dtd'>
                <document-info xmlns="http://www.calligra.org/DTD/document-info">
                 <about>
                  <title>""" + new_title + """</title>
                  <description>""" + new_description + """</description>
                  <subject>""" + new_subject + """</subject>
                  <abstract><![CDATA[""" + new_abstract + """]]></abstract>
                  <keyword>""" + new_keyword + """</keyword>
                  <initial-creator>""" + self.info["initial-creator"] + """</initial-creator>
                  <language>""" + new_language + """</language>
                  <license>""" + new_license + """</license>
                 </about>
                 <author>
                  <full-name>""" + self.info["full-name"] + """</full-name>
                  <creator-first-name>""" + self.info["creator-first-name"] + """</creator-first-name>
                  <creator-last-name>""" + self.info["creator-last-name"] + """</creator-last-name>
                  <initial>""" + self.info["initial"] + """</initial>
                  <author-title>""" + self.info["author-title"] + """</author-title>
                  <position>""" + self.info["position"] + """</position>
                  <company>""" + self.info["company"] + """</company>
                  """ + contacts + """
                 </author>
                </document-info>"""
            text = Krita.instance().activeDocument().setDocumentInfo(info_string)

            # Reconstruct Items
            self.dialog.info_contact.clear()
            for i in range(0, len(self.contact)):
                self.dialog.info_contact.addItem(str(self.contact[i]))
    def Information_Copy(self, item):
        contact = item.text()
        if contact != "":
            QApplication.clipboard().setText(contact)

    def cycles_to_time(self, cycles):
        # Variables
        year = 0
        month = 0
        day = 0
        hour = 0
        minute = 0
        second = 0
        # Checks
        if (cycles != "" and cycles != 0 and cycles != None):
            cycles = int(cycles)
            while cycles >= sec_ano:
                year += 1
                cycles -= sec_ano
            while cycles >= sec_mes:
                month += 1
                cycles -= sec_mes
            while cycles >= sec_dia:
                day += 1
                cycles -= sec_dia
            while cycles >= sec_hora:
                hour += 1
                cycles -= sec_hora
            while cycles >= sec_minuto:
                minute += 1
                cycles -= sec_minuto
            second = int(cycles)
        # Return
        time = [year, month, day, hour, minute, second]
        return time
    def time_to_string(self, time):
        # Variables
        ano = time[0]
        mes = time[1]
        dia = time[2]
        hor = time[3]
        min = time[4]
        seg = time[5]
        # string constants
        suffix = ""
        seconds = ""
        minutes = ""
        hours = ""
        days = ""
        months = ""
        years = ""
        # strings
        if (ano>0 or mes>0 or dia>0 or hor>0 or min>0 or seg>0):
            suffix = " >> "
        if ano > 0:
            years = str(ano).zfill(1) + "Y "
        if mes > 0:
            months = str(mes).zfill(2) + "M "
        if dia > 0:
            days = str(dia).zfill(2) + "D "
        if hor > 0:
            hours = str(hor).zfill(2) + "h "
        if min > 0:
            minutes = str(min).zfill(2) + "m "
        if seg > 0:
            seconds = str(seg).zfill(2) + "s"
        # string missing
        if (mes==0 and ano>0):
            months = "00M "
        if (dia==0 and (ano>0 or mes>0)):
            days = "00D "
        if (hor==0 and (ano>0 or mes>0 or dia>0)):
            hours = "00h "
        if (min==0 and (ano>0 or mes>0 or dia>0 or hor>0)):
            minutes = "00m "
        if (seg==0 and (ano>0 or mes>0 or dia>0 or hor>0 or seg>0)):
            seconds = "00s"
        # return
        string = suffix + years + months + days + hours + minutes + seconds
        return string
    def display_date(self, date):
        if (date != "" and date != None):
            ano = date[0:4]
            mes = date[5:7]
            dia = date[8:10]
            hor = date[11:13]
            min = date[14:16]
            seg = date[17:19]
            string = ano + "-" + mes + "-" + dia + " " + hor + ":" + min + ":" + seg
        else:
            string = ""
        return string
    def time_delta(self, year1, month1, day1, hour1, minute1, second1, year2, month2, day2, hour2, minute2, second2):
        date_start = datetime.datetime(year1, month1, day1, hour1, minute1, second1)
        date_now = datetime.datetime(year2, month2, day2, hour2, minute2, second2)
        delta = (date_now - date_start)
        string = self.time_to_string(self.cycles_to_time((delta.days * 86400) + delta.seconds))
        return string

    def cycle_to_hour(self, cycles):
        # Variables
        hour = 0
        # Checks
        if (cycles != "" and cycles != 0 and cycles != None):
            cycles = int(cycles)
            while cycles >= sec_hora:
                hour += 1
                cycles -= sec_hora
            resto = cycles / sec_hora
            work_hours = hour + resto
        else:
            work_hours = 0
        return work_hours
    def Money_Cost(self, work_hours):
        # Variables
        self.work_hours = work_hours
        rate = self.dialog.menu_money_rate.value()
        # Calculations
        total = rate * self.work_hours
        # Signals
        self.Money_Block_Signals(True)
        self.dialog.menu_money_total.setValue(total)
        self.Money_Block_Signals(False)
    def Money_Rate(self, rate):
        total = rate * self.work_hours
        # Signals
        self.Money_Block_Signals(True)
        self.dialog.menu_money_total.setValue(total)
        self.Money_Block_Signals(False)
    def Money_Total(self, total):
        if self.work_hours > 0:
            rate = total / self.work_hours
        else:
            rate = 0
        # Signals
        self.Money_Block_Signals(True)
        self.dialog.menu_money_rate.setValue(rate)
        self.Money_Block_Signals(False)
    def Money_Block_Signals(self, bool):
        self.dialog.menu_money_rate.blockSignals(bool)
        self.dialog.menu_money_total.blockSignals(bool)

    #endregion
    #region Save ###################################################################
    def Export_Filename(self, string):
        if string == "":
            self.export_filename = "file"
        else:
            self.export_filename = string
        # Save
        Krita.instance().writeSetting("Imagine Board", "export_filename", str( self.export_filename ))
    def Export_Extension(self, string):
        self.export_extension = string
        # Save
        Krita.instance().writeSetting("Imagine Board", "export_extension", str( self.export_extension ))

    def Scale_Width_Check(self):
        Krita.instance().writeSetting("Imagine Board", "scale_width_check", str( self.dialog.scale_width_check.isChecked() ))
    def Scale_Height_Check(self):
        Krita.instance().writeSetting("Imagine Board", "scale_height_check", str( self.dialog.scale_height_check.isChecked() ))
    def Scale_Percent_Check(self):
        Krita.instance().writeSetting("Imagine Board", "scale_percent_check", str( self.dialog.scale_percent_check.isChecked() ))
    def Scale_Width_Value(self):
        Krita.instance().writeSetting("Imagine Board", "scale_width_value", str( self.dialog.scale_width_value.value() ))
    def Scale_Height_Value(self):
        Krita.instance().writeSetting("Imagine Board", "scale_height_value", str( self.dialog.scale_height_value.value() ))
    def Scale_Percent_Value(self):
        Krita.instance().writeSetting("Imagine Board", "scale_percent_value", str( self.dialog.scale_percent_value.value() ))

    def Export_Clipboard(self):
        # Start
        ki = Krita.instance()
        ki.setBatchmode(True)

        # Export
        self.Export_Image("CLIPBOARD")

        # Finish
        ki.setBatchmode(False)
    def Export_Canvas(self):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            # Start
            ad = Krita.instance().activeDocument()
            ad.setBatchmode(True)
        
            # Export
            self.Export_Image("CANVAS")

            # Finish
            ad.waitForDone()
            ad.refreshProjection()
            ad.setBatchmode(False)
    def Export_Image(self, method):
        # Path
        i = 0
        while True:
            string = ( str(self.directory_path) + "\\" + str(self.export_filename) + "_{number}" + str(self.export_extension) ).format(number=str(i).zfill(4))
            path = os.path.normpath(string)
            exists = os.path.exists(path)
            if exists == False:
                break
            else:
                i += 1

         # Export
        if self.directory_path == "":
            QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Invalid Folder Path"))
        else:
            # Variables
            ad = Krita.instance().activeDocument()
            result = False

            # QImage
            qimage = QImage()
            if method == "CLIPBOARD":
                # Text
                # text = QApplication.clipboard().text()
                # qimage = QImage(os.path.normpath( text.replace("file:///", "") ))
                # Image
                qimage = QApplication.clipboard().image()
                # Dimensions
                ow = qimage.width()
                oh = qimage.height()
            elif method == "CANVAS":
                ow = ad.width()
                oh = ad.height()
                qimage = ad.thumbnail(ow, oh)
            else:
                qimage = QImage()

            # Save
            check = qimage.isNull()
            if qimage.isNull() == False:
                # Scale
                sw = self.dialog.scale_width_value.value()
                sh = self.dialog.scale_height_value.value()
                sp = self.dialog.scale_percent_value.value() / 100

                # Leading Value
                normal = Qt.KeepAspectRatio
                expand = Qt.KeepAspectRatioByExpanding
                if self.dialog.scale_width_check.isChecked() == True:
                    qimage = qimage.scaled(sw, 1, normal, Qt.SmoothTransformation)
                elif self.dialog.scale_height_check.isChecked() == True:
                    qimage = qimage.scaled(1, sh, normal, Qt.SmoothTransformation)
                elif self.dialog.scale_percent_check.isChecked() == True:
                    qimage = qimage.scaled(int(ow*sp), int(oh*sp), normal, Qt.SmoothTransformation)
                
                # Save
                result = qimage.save(path)
                if result == True:
                    try:QtCore.qDebug("IB | File: "+ str(path) + " | Saved")
                    except:pass

            # Update Display
            self.Filter_Keywords(False)

    #endregion
    #region Function (Key Enter) ###################################################
    def Function_ValidPath(self):
        text = self.dialog.menu_function_path.text()
        name = os.path.basename(text)
        path = self.Clean_Dot(os.path.normpath(text))
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.Function_Run([[name, path]])
    def Function_Run(self, SIGNAL_PATH):
        # Settings
        operation = self.dialog.menu_function_operation.currentText()
        strings = self.List_Selected()
        number = self.dialog.menu_function_number.value()
        paths = SIGNAL_PATH
        # Has valid Paths
        if len(paths) > 0:
            # Sort Files and Folders
            folders = []
            files = []
            for i in range(0, len(paths)):
                if os.path.isdir(paths[i][1]) == True:
                    folders.append(paths[i])
                if os.path.isfile(paths[i][1]) == True:
                    files.append(paths[i])

            # File Watcher
            self.Watcher_State(False)
            self.Function_Enabled(False)
            # Thread
            self.thread_function.Variables_Run(operation, strings, number, files, folders, self.directory_path)
            self.thread_function.start()

    def Function_PBAR_Value(self, SIGNAL_PBAR_VALUE):
        self.dialog.menu_function_progress.setValue(SIGNAL_PBAR_VALUE)
    def Function_PBAR_Max(self, SIGNAL_PBAR_MAX):
        self.dialog.menu_function_progress.setMaximum(SIGNAL_PBAR_MAX)
    def Function_String(self, SIGNAL_STRING):
        self.dialog.menu_file.setText(SIGNAL_STRING)
    def Function_Number(self, SIGNAL_NUMBER):
        self.dialog.menu_function_number.setValue(SIGNAL_NUMBER)
    def Function_Reset(self, SIGNAL_RESET):
        self.dialog.menu_function_progress.setValue(0)
        self.thread_function.quit()
        self.Watcher_State(True)
        self.Function_Enabled(True)
        self.Filter_Keywords(False)
    def Function_Item(self, SIGNAL_ITEM):
        # Variables
        list_count = self.dialog.menu_function_list.count()
        # Create a Set
        keys_s = set()
        for i in range(0, list_count):
            keys_s.add( self.dialog.menu_function_list.item(i).text() )
        keys_s.add( SIGNAL_ITEM )
        # Clear List
        self.dialog.menu_function_list.clear()
        # Repopulate List
        keys_l = list(keys_s)
        keys_l.sort()
        for i in range(0, len(keys_l)):
            self.dialog.menu_function_list.addItem(keys_l[i])
        # Save
        self.List_Save()
    def Function_NewPath(self, SIGNAL_NEWPATH):
        # Paths
        path_i = str(SIGNAL_NEWPATH[0])
        path_new = str(SIGNAL_NEWPATH[1])
        # Change References
        for i in range(0, len(self.list_pin_ref)):
            if self.list_pin_ref[i]["path"] == path_i:
                self.list_pin_ref[i]["path"] = path_new
                self.imagine_reference.Pin_Replace(i, path_new)

    def Function_Enabled(self, bool):
        self.dialog.menu_function_operation.setEnabled(bool)
        self.dialog.menu_function_add.setEnabled(bool)
        self.dialog.menu_function_clear.setEnabled(bool)
        self.dialog.menu_function_list.setEnabled(bool)
        self.dialog.menu_function_number.setEnabled(bool)
        self.dialog.menu_function_path.setEnabled(bool)
        self.dialog.menu_function_run.setEnabled(bool)

    #endregion
    #region Watcher ################################################################
    def Watcher_Display(self):
        try:
            self.preview_path = self.found_path[self.preview_index]
            self.Filter_Keywords(False)
            self.Search_Previous(self.preview_path)
        except:
            self.Filter_Keywords(True)
        self.imagine_reference.Board_Rebase()
    def Watcher_State(self, boolean):
        # Blocks Imagine Board from updating to changes to the Directory
        if boolean == True: # Start
            try:self.Watcher_Add()
            except:pass
        if boolean == False: # Stop
            try:self.Watcher_Remove()
            except:pass
    def Watcher_Update(self):
        self.Watcher_Remove()
        self.Watcher_Add()

    def Watcher_Remove(self):
        directories = self.file_system_watcher.directories()
        files = self.file_system_watcher.files()
        paths_clean = []
        for d in range(0, len(directories)):
            paths_clean.append(directories[d])
        for f in range(0, len(files)):
            paths_clean.append(files[f])
        if len(paths_clean) > 0:
            self.file_system_watcher.removePaths(paths_clean)
    def Watcher_Add(self):
        # Variables
        path_list = []

        # Add Directory Path
        dir_p = self.directory_path
        if dir_p != "":
            path_list.append(dir_p)
        # Add Recent Documents
        if self.list_active == "Recent Documents":
            for d in range(0, len(self.list_recentdocument)):
                path_d = os.path.normpath( self.list_recentdocument[d] )
                dir_d = os.path.dirname(path_d)
                if (dir_d != dir_p and path_d not in path_list):
                    path_list.append(path_d)
        # Add References
        for r in range(0, len(self.list_pin_ref)):
            path_r = self.list_pin_ref[r]["path"]
            text_r = self.list_pin_ref[r]["text"]
            if (path_r != None and text_r == None):
                dir_r = os.path.dirname(path_r)
                if (dir_r != dir_p and path_r not in path_list):
                    path_list.append(path_r)
        # Watch these Files
        if len(path_list) > 0:
            self.file_system_watcher.addPaths(path_list)

        # Construct List
        self.dialog.menu_watcher_list.clear()
        if dir_p != "":
            item = QListWidgetItem(dir_p)
            item.setIcon(Krita.instance().icon('document-open'))
            self.dialog.menu_watcher_list.addItem(item)
        # Add Recent Documents
        if self.list_active == "Recent Documents":
            for d in range(0, len(self.list_recentdocument)):
                path_d = os.path.normpath( self.list_recentdocument[d] )
                item = QListWidgetItem(path_d)
                if path_d in path_list:
                    qicon = Krita.instance().icon('document-new')
                else:
                    qicon = Krita.instance().icon('paintbrush')
                item.setIcon( qicon )
                self.dialog.menu_watcher_list.addItem(item)
        # Add References
        for r in range(0, len(self.list_pin_ref)):
            path_r = self.list_pin_ref[r]["path"]
            text_r = self.list_pin_ref[r]["text"]
            if (path_r != None and text_r == None): # Image
                item = QListWidgetItem( os.path.normpath(path_r) )
                if path_r in path_list:
                    qicon = Krita.instance().icon('document-new')
                else:
                    qicon = Krita.instance().icon('paintbrush')
            else: # Text
                item = QListWidgetItem(text_r)
                qicon = Krita.instance().icon('draw-text')
            item.setIcon( qicon )
            self.dialog.menu_watcher_list.addItem(item)

    def List_Reference(self):
        if self.list_active == "Reference Images":
            # Found Paths Set
            paths = []
            for i in range(0, len(self.found_path)):
                item = self.found_path[i]
                paths.append(item)
            compare_path = set(paths)

            # References Set
            refs = []
            for i in range(0, len(self.list_pin_ref)):
                item = self.list_pin_ref[i]["path"]
                if self.list_pin_ref[i]["text"] == None:
                    refs.append(item)
            compare_ref = set(refs)

            # Verify diferences to update Preview and Grid
            if compare_path != compare_ref:
                self.Filter_Keywords(False)

    #endregion
    #region Annotations ############################################################
    def AutoSave_KRA(self, boolean):
        self.annotation_kra = boolean
        # Save
        Krita.instance().writeSetting("Imagine Board", "annotation_kra", str(self.annotation_kra))
    def AutoSave_File(self, boolean):
        self.annotation_file = boolean
        # Save
        Krita.instance().writeSetting("Imagine Board", "annotation_file", str(self.annotation_file))

    def Annotation_KRA_Load(self):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            try:
                # Active Document
                doc = Krita.instance().activeDocument()

                # Annotations
                annotation = doc.annotation("Imagine Board")
                an_string = str(annotation)
                an_replace = an_string[:-3].replace("b\"", "")
                an_split = an_replace.split("\\n")
                self.Variables_Load(an_split)
            except:
                pass
    def Annotation_FILE_Load(self):
        file_dialog = QFileDialog(QWidget(self))
        file_dialog.setFileMode(QFileDialog.AnyFile)
        directory_path = file_dialog.getOpenFileName(self, "Select *.imagine_board.eo File", "", str("*.imagine_board.eo"))
        directory_path = os.path.normpath( directory_path[0] )
        if (directory_path != "" and directory_path != "."):
            # Read
            file = open(directory_path, "r")
            data = file.readlines()
            self.Variables_Load(data)
    def Variables_Load(self, lista):
        # lista = [str, str, str, ...]

        try:
            plugin = str(lista[0]).replace("\n", "", 1)
            if plugin  == "imagine_board":
                # Read
                for i in range(0, len(lista)):
                    lista_i = lista[i]
                    if lista_i.startswith("directory_path=") == True: # Preview and Grid
                        self.directory_path = os.path.normpath( str(lista_i).replace("directory_path=", "", 1).replace("\n", "", 1) )
                    if lista_i.startswith("list_pin_ref=") == True: # Reference
                        self.list_pin_ref = eval( str(lista_i).replace("list_pin_ref=", "", 1) )
                # Write
                self.Folder_Load(self.directory_path)
                self.Reference_Cache(self.list_pin_ref)
                self.Board_Loader(self.list_pin_ref)
        except:
            pass

    def Annotation_Save(self):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            try:
                # Document
                doc = Krita.instance().activeDocument()

                # Data to be Saved
                data = (
                    # Plugin
                    "imagine_board\n"+
                    # Preview and Grid
                    "directory_path="+str(self.directory_path)+"\n"+
                    # Reference
                    "list_pin_ref="+str(self.list_pin_ref)+"\n"+
                    # Other
                    ""
                    )

                # Save Method
                if doc != None:
                    if self.annotation_kra == True:
                        # Save to active Document
                        doc.setAnnotation('Imagine Board', "Document", QByteArray(data.encode()))
                    if self.annotation_file == True:
                        # Variables
                        file_path = os.path.normpath(doc.fileName())
                        base_name = os.path.basename(file_path)
                        extension = os.path.splitext(file_path)[1]
                        directory = file_path[:-len(base_name)]
                        name = base_name[:-len(extension)]
                        save_path = directory + name + ".imagine_board.eo"

                        # Save to TXT file
                        if (file_path != "" and file_path != "."):
                            try:
                                file = open(save_path, "w")
                                file.write(data)
                            except:
                                pass
            except:
                pass

    #endregion
    #region Window #################################################################
    def Window_Connect(self):
        # Window
        self.window = Krita.instance().activeWindow()
        if self.window != None:
            # Connects
            self.window.activeViewChanged.connect(self.View_Changed)
            self.window.themeChanged.connect(self.Theme_Changed)
            self.window.windowClosed.connect(self.Window_Closed)

    def View_Changed(self):
        # Disables Auto Save
        self.dialog.annotation_kra_save.setChecked(False)
        self.dialog.annotation_file_save.setChecked(False)
    def Theme_Changed(self):
        # Krita Theme
        theme_value = QApplication.palette().color(QPalette.Window).value()
        if theme_value > 128:
            self.color_1 = QColor("#191919")
            self.color_2 = QColor("#e5e5e5")
        else:
            self.color_1 = QColor("#e5e5e5")
            self.color_2 = QColor("#191919")
        # Update Pigmento
        self.imagine_preview.Set_Theme(self.color_1, self.color_2)
        self.imagine_grid.Set_Theme(self.color_1, self.color_2)
        self.imagine_reference.Set_Theme(self.color_1, self.color_2)
    def Window_Closed(self):
        pass

    #endregion
    #region Widget Events ##########################################################
    def showEvent(self, event):
        # Window
        self.Window_Connect()
        self.Theme_Changed()
        # # UI
        self.Menu_Index(self.mode_index)

        # Start Up display
        if self.widget_display == False:
            start_up = QtCore.QTimer(self)
            start_up.setSingleShot(True)
            start_up.timeout.connect(self.Settings_Load)
            start_up.start(2000)
    def resizeEvent(self, event):
        self.Update_Sizes_Middle()
    def enterEvent(self, event):
        # Pigmento Module Load
        if self.MODULE_pigmento_bool == False:
            self.Import_Pigment_O()

        # Widget
        self.is_inside = True
        self.Transparent_Shift()

        # Start Up display
        self.Settings_Load()

        # Update
        self.update()
    def leaveEvent(self, event):
        # Cursor Focus
        self.Clear_Focus()
        # Widget
        self.is_inside = False
        self.Transparent_Shift()
        # Save
        self.Annotation_Save()
        # Update
        self.update()
    def closeEvent(self, event):
        self.MODULE_pigmento_bool = False
        self.widget_display = False
        self.found_qpixmap.clear()
        # Save
        self.Annotation_Save()

    def paintEvent(self, event):
        # Bypass PyQt5 limitation to detect correct size of widget right after change in Size Policy
        if self.dirty > 0:
            if self.widget_float == True:
                self.Update_Sizes_Middle()
            else:
                self.Update_Size_Corner()
            self.dirty -= 1

    #endregion
    #region Change Canvas ##########################################################
    def canvasChanged(self, canvas):
        self.Menu_Tabs()

    #endregion
    #region Notes ##################################################################
    """
    # Label Message
    self.layout.label.setText("message")

    # Pop Up Message
    QMessageBox.information(QWidget(), i18n("Warnning"), i18n("message"))

    # Log Viewer Message
    QtCore.qDebug("value = " + str(value))
    QtCore.qDebug("message")
    QtCore.qWarning("message")
    QtCore.qCritical("message")

    Code
    found_qpixmap = qpixmap#.scaled(self.tn_size, self.tn_size, Qt.KeepAspectRatioByExpanding, self.tn_smooth_scale)
    """
    #endregion


class Thread_Thumbnails(QThread):
    SIGNAL_IMAGE = QtCore.pyqtSignal(QPixmap)
    SIGNAL_RESET = QtCore.pyqtSignal(int)

    #region Initialize #############################################################
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.null_qpixmap = QPixmap()
        self.folder = "None"
        self.path = []
        self.items = 0
        self.ll = 0
        self.lr = 0
    def Variables_Run(self, folder, path, items, ll, lr):
        self.folder = folder
        self.path = path
        self.items = items
        self.ll = ll
        self.lr = lr

    #endregion
    #region Cycle ##################################################################
    def run(self):
        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()
        # Load images for Cache
        for i in range(0, self.items):
            index = self.path[i]
            if (i >= self.ll and i <= self.lr):
                found_qpixmap = QPixmap(index)
            else:
                found_qpixmap = self.null_qpixmap
            self.SIGNAL_IMAGE.emit(found_qpixmap)
        self.SIGNAL_RESET.emit(0)
        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo(end)
        time = QTime(0,0).addMSecs(delta)
        try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Directory: "+ self.folder + " | Thumbnail Cache")
        except:pass

    #endregion


class Thread_NameList(QThread):
    SIGNAL_PROGRESS_VALUE = QtCore.pyqtSignal(int)
    SIGNAL_PROGRESS_MAX = QtCore.pyqtSignal(int)
    SIGNAL_COMP_MAX = QtCore.pyqtSignal(int)
    SIGNAL_NAMELIST = QtCore.pyqtSignal(list)

    #region Initialize #############################################################
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.path = ""
        # self.stop = False
    def Variables_Run(self, path):
        self.path = path

    #endregion
    #region Cycle ##################################################################
    def run(self):
        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # Variables
        image_name = []
        # Open Zip File
        try:
            if zipfile.is_zipfile(self.path):
                archive = zipfile.ZipFile(self.path, "r")
                name_list = archive.namelist()
                length = len(name_list)

                # Check for image Files
                num = 0
                self.SIGNAL_PROGRESS_MAX.emit(length)
                self.SIGNAL_COMP_MAX.emit(length)
                for i in range(0, length):
                    num += 1
                    self.SIGNAL_PROGRESS_VALUE.emit(num)
                    try:
                        archive_open = archive.open(name_list[i])
                        archive_read = archive_open.read()
                        qimage = QImage()
                        qimage.loadFromData(archive_read)
                        if qimage.isNull() == False:
                            image_name.append(name_list[i])
                    except:
                        pass
                self.SIGNAL_PROGRESS_VALUE.emit(length+1)
        except:
            pass

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo(end)
        time = QTime(0,0).addMSecs(delta)
        string = ("IB " + str(time.toString('hh:mm:ss.zzz')) + " | File: "+ str(os.path.basename(self.path)) + " | Compressed Check")
        # try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | File: "+ str(os.path.basename(self.path)) + " | Compressed Check")
        # except:pass

        # Update Display
        self.SIGNAL_PROGRESS_VALUE.emit(0)
        self.SIGNAL_PROGRESS_MAX.emit(1)
        self.SIGNAL_NAMELIST.emit([self.path, image_name, string])

    #endregion


class Thread_Function(QThread):
    SIGNAL_COUNTER = QtCore.pyqtSignal(int)
    SIGNAL_PBAR_VALUE = QtCore.pyqtSignal(int)
    SIGNAL_PBAR_MAX = QtCore.pyqtSignal(int)
    SIGNAL_STRING = QtCore.pyqtSignal(str)
    SIGNAL_NUMBER = QtCore.pyqtSignal(int)
    SIGNAL_RESET = QtCore.pyqtSignal(int)
    SIGNAL_ITEM = QtCore.pyqtSignal(str)
    SIGNAL_NEWPATH = QtCore.pyqtSignal(list)

    #region Initialize #############################################################
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        # Operating System
        self.OS = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux
        # Modules
        self.qfile = QFile()
        self.dir = QDir()
        self.Variables_Reset()

    def Docker(self, dialog):
        self.dialog = dialog
    def Variables_Reset(self):
        self.operation = ">>"
        self.strings = []
        self.number = 0
        self.folders = []
        self.files = []
        self.directory = ""
        self.reset = ""
    def Variables_Run(self, operation, strings, number, files, folders, directory):
        self.Variables_Reset()
        self.operation = operation
        self.strings = strings
        self.number = number
        self.folders = folders
        self.files = files
        self.directory = directory
    def verify_total(self, value):
        mat = value * value
        count = int((mat - value) / 2)
        return count

    #endregion
    #region Cycle ##################################################################
    def run(self):
        # Operation spacing
        try:QtCore.qDebug("IB")
        except:pass

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # Operation Selection
        null_operation = self.operation == ">>" or self.operation == ""
        if null_operation == False:
            # Totals
            total_dir = len(self.folders)
            total_fil = len(self.files)
            rename = ["key_add", "key_replace", "key_remove", "key_clean", "rename_order", "rename_age", "rename_random"]
            if (total_fil == 0 and total_dir == 1): # Directory
                # Variables
                self.dir.setPath(self.folders[0][1])
                self.dir.setSorting(QDir.LocaleAware)
                self.dir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
                self.dir.setNameFilters(file_normal)
                total = self.dir.count()
                files = self.dir.entryInfoList()
                name = []
                path = []
                for i in range(0, len(files)):
                    file_path = files[i].filePath()
                    name.append(os.path.basename(file_path))
                    path.append(file_path)
                # Modes
                if self.operation in rename:
                    self.File_Cycle(total, path, self.strings, self.number)
                elif self.operation == "key_populate":
                    self.File_Populate(total, path)
                elif self.operation == "save_original":
                    self.File_Save_Original(total, path, name, self.directory)
                elif self.operation == "save_order":
                    self.File_Save_Order(total, path, self.strings, self.directory)
                elif self.operation == "search_null":
                    self.File_Null(total, path)
                elif self.operation == "search_copy":
                    self.File_Copy(total, path)
            elif (total_fil > 0 and total_dir == 0): # Files
                # Variables
                name = []
                path = []
                for i in range(0, total_fil):
                    name.append(self.files[i][0])
                    path.append(self.files[i][1])

                # Modes
                if self.operation in rename:
                    self.File_Cycle(total_fil, path, self.strings, self.number)
                elif self.operation == "key_populate":
                    self.File_Populate(total_fil, path)
                elif self.operation == "save_original":
                    self.File_Save_Original(total_fil, path, name, self.directory)
                elif self.operation == "save_order":
                    self.File_Save_Order(total_fil, path, self.strings, self.directory)
                elif self.operation == "search_null":
                    self.File_Null(total_fil, path)
                elif self.operation == "search_copy":
                    self.File_Copy(total_fil, path)

        # Progress Bar
        self.SIGNAL_PBAR_VALUE.emit(0)
        self.SIGNAL_PBAR_MAX.emit(1)

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo(end)
        time = QTime(0,0).addMSecs(delta)
        try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Operation " + str(self.operation) )
        except:pass

        # End
        self.SIGNAL_RESET.emit(0)

    #endregion
    #region File Cycle #############################################################
    def File_Cycle(self, total, path, key, number):
        self.SIGNAL_PBAR_MAX.emit(total)
        # Pre Sorting
        if self.operation == "rename_age":
            path = self.Sort_Age(total, path)
        # Cycle
        for i in range(0, total):
            # Counter
            self.SIGNAL_STRING.emit(str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            # Old String
            path_i = os.path.normpath(path[i])
            # New String
            if self.operation == "key_add": # Add
                path_new = self.String_Add(path_i, key)
            if self.operation == "key_replace": # Replace
                path_new = self.String_Replace(path_i, key)
            if self.operation == "key_remove": # Remove
                path_new = self.String_Remove(path_i, key)
            if self.operation == "key_clean": # Clean
                path_new = self.String_Clean(path_i)
            if self.operation == "rename_order": # Rename
                path_new = self.String_ReName(path_i, key, number, i, "order")
            if self.operation == "rename_age": # Rename
                path_new = self.String_ReName(path_i, key, number, i, "age")
            if self.operation == "rename_random": # Rename
                path_new = self.String_ReName(path_i, key, number, i, "random")

            # Confirm Differences to Apply
            exists = os.path.exists( os.path.normpath( os.path.join( os.path.dirname(path_i), path_new) ) )
            if (path_i != path_new and exists == False):
                self.SIGNAL_NEWPATH.emit([path_i, path_new])
                try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " >> " + str(os.path.basename(path_new)))
                except:pass
                self.qfile.rename(path_i, path_new)
    def File_Populate(self, total, path):
        self.SIGNAL_PBAR_MAX.emit(total)
        keys = ""
        count = 0
        for i in range(0, total):
            path_i = path[i]
            self.SIGNAL_STRING.emit(str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            keys += self.String_Populate(path_i)
        words = list(set(keys.split()))
        for w in range(0, len(words)):
            if (w != "" and w != " "):
                self.SIGNAL_ITEM.emit( str(words[w]) )
    def File_Save_Original(self, total, path, name, directory):
        self.SIGNAL_PBAR_MAX.emit(total)
        for i in range(0, total):
            # Counter
            self.SIGNAL_STRING.emit(str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            # Save
            path_i = os.path.normpath(path[i])
            basename = name[i]
            path_new = os.path.normpath(os.path.join(directory, basename))
            check = os.path.exists(path_new)
            if check == False:
                qimage = QImage(path_i)
                qimage.save(path_new)
                try:QtCore.qDebug("IB save original | " + str(path_new))
                except:pass
    def File_Save_Order(self, total, path, name, directory):
        self.SIGNAL_PBAR_MAX.emit(total)
        for i in range(0, total):
            # Counter
            self.SIGNAL_STRING.emit(str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            # Save
            path_i = os.path.normpath(path[i])
            if len(name) == 0:
                new_name = "image"
            else:
                new_name = name[0]
            path_new = os.path.normpath( self.String_Save_Order(directory, new_name) )
            check = os.path.exists(path_new)
            if check == False:
                qimage = QImage(path_i)
                qimage.save(path_new)
                try:QtCore.qDebug("IB save order | " + str(path_new))
                except:pass
    def File_Null(self, total, path):
        self.SIGNAL_PBAR_MAX.emit(total)
        # Cycle
        counter = 0
        for i in range(0, total):
            # Counter
            self.SIGNAL_STRING.emit(str(counter) + " : " + str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            # Pixmap
            path_i = os.path.normpath(path[i])
            qpixmap = QPixmap(path_i)
            if qpixmap.isNull() == True:
                path_new = self.String_Null(path_i)
                counter += 1
                # Confirm Differences to Apply
                exists = os.path.exists( os.path.normpath( os.path.join( os.path.dirname(path_i), path_new)))
                if (path_i != path_new and exists == False):
                    self.SIGNAL_NEWPATH.emit([path_i, path_new])
                    try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " >> " + str(os.path.basename(path_new)))
                    except:pass
                    self.qfile.rename(path_i, path_new)
    def File_Copy(self, total, path):
        ver_total = self.verify_total(total)
        self.SIGNAL_PBAR_MAX.emit(ver_total)
        copy = 0
        count = 0
        replicas = []
        for i in range(0, total):
            path_i = os.path.normpath(path[i])
            qimage_i = QImageReader(path_i).read()
            for r in range(i+1, total):
                path_r = path[r]
                count += 1
                self.SIGNAL_STRING.emit(str(copy) + " : " + str(count+1) + " : " + str(ver_total+1))
                self.SIGNAL_PBAR_VALUE.emit(count+1)
                if path_r not in replicas:
                    qimage_r = QImageReader(path_r).read()
                    check = self.Pixel_Check(qimage_i, qimage_r)
                    if check == True:
                        copy += 1
                        replicas.append(path_r)
                        path_new = self.String_Copy(path_r)
                        if path_r != path_new:
                            self.SIGNAL_NEWPATH.emit([path_r, path_new])
                            try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " : " + str(os.path.basename(path_r)) + " >> " + str(os.path.basename(path_new)))
                            except:pass
                            self.qfile.rename(path_r, path_new)

    def Sort_Age(self, total, path):
        age_1 = []
        for i in range(0, total):
            age = int(time.time() - os.stat(path[i])[stat.ST_MTIME])
            age_1.append(age)
        age_2 = age_1.copy()
        age_2.sort()
        age_2.reverse()
        sort_age = []
        for i in range(0, total):
            for j in range(0, total):
                if (age_2[i] == age_1[j] and path[j] not in sort_age):
                    sort_age.append(path[j])
        path.clear()
        path = sort_age.copy()
        return sort_age
    def Pixel_Check(self, qimage_i, qimage_r):
        # Variabels
        check = False
        wi = qimage_i.width()
        hi = qimage_i.height()
        wr = qimage_r.width()
        hr = qimage_r.height()
        # Pixel check
        try:
            if (wi == wr and hi == hr):
                # Check pixels of images
                for x in range(0, wi):
                    for y in range(0, hi):
                        color_i = qimage_i.pixelColor(x, y)
                        color_r = qimage_r.pixelColor(x, y)
                        if color_i != color_r:
                            break
                # Check Verified as the same image
                check = True
        except:
            pass
        # Return
        return check

    #endregion
    #region String #################################################################
    """
    Key Enter convention : ' Basename [ key1 key2 ... ].extension '
    """
    def String_Add(self, path, key):
        if len(key) == 0:
            path_new = path
        else:
            # String Components
            directory, bn, extension, n, base = self.Path_Components(path)

            # construct keywords
            a = base.rfind(" [ ")
            b = base.rfind(" ]")
            if (a >= 0 and b >= 0 and a < b): # Keys Exist
                name = base[:a]
                c = base[a+3:b].split()
                d = list(set(c).union(set(key)))
            else: # No Keys Exist
                name = base
                d = key
            d.sort()
            keys = " [ "
            for i in range(0, len(d)):
                keys += d[i] + " "
            keys += "]"

            # Create new path name
            if self.OS == "winnt":
                base_new = name + keys + extension
            else:
                base_new = name + keys
            path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Replace(self, path, key):
        if len(key) == 0:
            path_new = path
        else:
            # String Components
            directory, bn, extension, n, base = self.Path_Components(path)

            # construct keywords
            a = base.rfind(" [ ")
            b = base.rfind(" ]")
            if (a >= 0 and b >= 0 and a < b): # Keys Exist
                name = base[:a]
            else: # No Keys Exist
                name = base
            d = key
            d.sort()
            keys = " [ "
            for i in range(0, len(d)):
                keys += d[i] + " "
            keys += "]"

            # Create new path name
            if self.OS == "winnt":
                base_new = name + keys + extension
            else:
                base_new = name + keys
            path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Remove(self, path, key):
        if len(key) == 0:
            path_new = path
        else:
            # String Components
            directory, bn, extension, n, base = self.Path_Components(path)

            # construct keywords
            a = base.rfind(" [ ")
            b = base.rfind(" ]")
            if (a >= 0 and b >= 0 and a < b): # Keys Exist
                name = base[:a]
                c = base[a+3:b].split()
                d = list(set(c).difference(set(key)))
            else: # No Keys Exist
                name = base
                d = key
            d.sort()

            # Keys left to display
            if len(d) >= 1:
                keys = " [ "
                for i in range(0, len(d)):
                    keys += d[i] + " "
                keys += "]"
            else:
                keys = ""

            # Create new path name
            if self.OS == "winnt":
                base_new = name + keys + extension
            else:
                base_new = name + keys
            path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Clean(self, path):
        # String Components
        directory, bn, extension, n, base = self.Path_Components(path)

        # construct keywords
        a = base.rfind(" [ ")
        b = base.rfind(" ]")
        if (a >= 0 and b >= 0 and a < b): # Keys Exist
            name = base[:a]
        else: # No Keys Exist
            name = base

        # Create new path name
        if self.OS == "winnt":
            base_new = name + extension
        else:
            base_new = name
        path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Populate(self, path):
        # String Components
        directory, bn, extension, n, base = self.Path_Components(path)

        # construct keywords
        a = base.rfind(" [ ")
        b = base.rfind(" ]")
        if (a >= 0 and b >= 0 and a < b): # Keys Exist
            keys = str(base[a+3:b]) + " "
        else: # No Keys Exist
            keys = " "

        # Return
        return keys
    def String_ReName(self, path, key, number, iter, mode):
        if len(key) == 0:
            path_new = path
        else:
            # String Components
            directory, bn, extension, n, base = self.Path_Components(path)

            # construct keywords
            a = base.rfind(" [ ")
            b = base.rfind(" ]")
            if (a >= 0 and b >= 0 and a < b): # Keys Exist
                name_old = base[:a-1]
                keywords = base[a:]
            else: # No Keys Exist
                name_old = base
                keywords = ""

            # Generate Names
            if (mode == "order" or mode == "age"):
                name_new = key[0] + " " + str(int(number) + iter).zfill(6)
            if mode == "random":
                code = ""
                for i in range(0, 20):
                    c = random.randint(1, 3)
                    if c == 1:
                        n = random.randint(48, 57)
                    if c == 2:
                        n = random.randint(65, 90)
                    if c == 3:
                        n = random.randint(97, 122)
                    code += chr(n)
                name_new = key[0] + " " + code

            # Create new path name
            if self.OS == "winnt":
                base_new = name_new + keywords + extension
            else:
                base_new = name_new + keywords
            path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Save_Order(self, directory, name):
        # Number formating
        val = int(self.dialog.menu_function_number.value())
        self.SIGNAL_NUMBER.emit(val+1)
        val = str(val).zfill(6)
        # Create new path name
        if self.OS == "winnt":
            base_new = name + " " + val + ".png"
        else:
            base_new = name + " " + val
        # Return
        path_new = os.path.normpath(os.path.join(directory, base_new))
        return path_new
    def String_Null(self, path):
        # String Components
        directory, bn, extension, n, base = self.Path_Components(path)

        # construct keywords
        a = base.rfind(" [ ")
        b = base.rfind(" ]")
        if (a >= 0 and b >= 0 and a < b): # Keys Exist
            name = base[:a]
        else: # No Keys Exist
            name = base

        # Create new path name
        text = "null"
        if self.OS == "winnt":
            base_new = name + " [ " + text + " ]" + extension
        else:
            base_new = name + " [ " + text + " ]"
        path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new
    def String_Copy(self, path):
        # String Components
        directory, bn, extension, n, base = self.Path_Components(path)

        # construct keywords
        a = base.rfind(" [ ")
        b = base.rfind(" ]")
        if (a >= 0 and b >= 0 and a < b): # Keys Exist
            name = base[:a]
        else: # No Keys Exist
            name = base

        # Create new path name
        text = "copy"
        if self.OS == "winnt":
            base_new = name + " [ " + text + " ]" + extension
        else:
            base_new = name + " [ " + text + " ]"
        path_new = os.path.join(directory, base_new)
        # Return
        path_new = os.path.normpath(path_new)
        return path_new

    def Path_Components(self, path):
        directory = os.path.dirname(path) # dir
        bn = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name
        return directory, bn, extension, n, base
    #endregion


"""
To Do:
- Reset Board View
- Scaling of Selections

Known Bug:
- Importing layer with alpha crops image size (reason unknown)
- Preview Mode on Windows, if it is openning a protected folder with OS_Folders and with first file a ZIP it will crash Krita instantly
"""