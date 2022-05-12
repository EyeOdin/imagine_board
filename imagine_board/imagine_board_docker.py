# Imagine Board is a Krita plugin to browse images and create image boards.
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


#\\ Imports ####################################################################
from krita import *
import copy
import math
import random
import os
import subprocess
import datetime
import xml
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from .imagine_board_modulo import (
    ImagineBoard_Preview,
    ImagineBoard_Grid,
    ImagineBoard_Reference,
    Dialog_UI,
    Dialog_CR,
)
from .imagine_board_extension import ImagineBoard_Extension
#//
#\\ Global Variables ###########################################################
DOCKER_NAME = "Imagine Board"
imagine_board_version = "2022_05_10"

file_normal = [
    "*.kra",
    "*.krz",
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
    "*.webp",
    "*.svg",
    ]
file_backup = [
    "*.kra~",
    "*.krz~",
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
    ]

#//


class ImagineBoard_Docker(DockWidget):
    """
    Imagine Board
    """

    #\\ Initialize #############################################################
    def __init__(self):
        super(ImagineBoard_Docker, self).__init__()

        # Construct
        self.Variables()
        self.User_Interface()
        self.Connections()
        self.Modules()
        self.Timer()
        self.Style()
        self.Extension()
        self.Settings()

    def Variables(self):
        # Variables
        self.widget_display = False
        self.dirty = 0
        self.menu_mode = 0
        self.menu_anim = False
        self.directory_path = ""
        self.file_extension = file_normal
        self.filter_sort = QDir.LocaleAware
        self.fit_canvas_bool = False
        self.image_scale = 1
        self.images_found = False
        self.recent_documents = False

        # Preview
        self.preview_index = 0
        self.preview_max = 0

        # Grid
        self.grid_horz = 3
        self.grid_vert = 3
        self.grid_table = (self.grid_horz * self.grid_vert) - 1
        self.grid_max = 0

        # Lines
        self.line_preview = 0
        self.line_grid = 0

        # Reference
        self.references = []
        self.ref_import = False
        self.ref_limit = 2000

        # Animation
        self.playpause = True # True=Play  False=Pause

        # Cache amount
        self.tn_size = 256
        self.tn_limit = 256
        self.cache_load = 0
        self.cache_clean = 0
        self.cache_thread = 1000

        # Slideshow
        self.slideshow_sequence = "Linear"
        self.slideshow_time = 1000
        self.slideshow_lottery = []

        # Clip
        self.clip_state = False
        self.clip_x = 0.1
        self.clip_y = 0.1
        self.clip_w = 0.8
        self.clip_h = 0.8
    def User_Interface(self):
        # Window
        self.setWindowTitle(DOCKER_NAME)

        # Operating System
        self.OS = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux

        # Path Name
        self.directory_plugin = str(os.path.dirname(os.path.realpath(__file__)))

        # Imagine Board Docker
        self.window = QWidget()
        self.layout = uic.loadUi(self.directory_plugin + "/imagine_board_docker.ui", self.window)
        self.setWidget(self.window)
        # Pigmento Dialog Settings
        self.dialog = Dialog_UI(self)
        self.dialog.accept()
        # Pigmento Dialog Copyright
        self.copyright = Dialog_CR(self)
        self.copyright.accept()

        # Path and Pixmaps
        self.null_qpixmap = QPixmap()
        self.default_path = str(os.path.normpath(self.directory_plugin + "/DEFAULT/ib_default.png"))
        self.default_qpixmap = QPixmap(self.default_path)
        self.found_path = [self.default_path] * self.grid_table
        self.found_qpixmap = [self.default_qpixmap] * self.grid_table

        # Animation Panel Boot
        self.AnimPanel_Shrink()
    def Connections(self):
        # Movie Connections
        self.layout.anim_playpause.clicked.connect(lambda: self.Preview_PlayPause(not self.playpause))
        self.layout.anim_frame_b.clicked.connect(self.Preview_Frame_Back)
        self.layout.anim_frame_f.clicked.connect(self.Preview_Frame_Forward)
        self.layout.anim_screenshot.clicked.connect(self.Preview_Screenshot)
        # Layout Connections
        self.layout.slider.valueChanged.connect(lambda: self.Value_Display("slider", self.layout.slider.value()))
        self.layout.mode.currentIndexChanged.connect(self.Menu_Mode)
        self.layout.folder.clicked.connect(self.Folder_Open)
        self.layout.slideshow.toggled.connect(self.Preview_SlideShow_Switch)
        self.layout.thread.clicked.connect(self.Thumbnail_Start)
        self.layout.filter.returnPressed.connect(lambda: self.Filter_Keywords(True))
        self.layout.number.valueChanged.connect(lambda: self.Value_Display("function_number", self.layout.number.value()))
        self.layout.docker.clicked.connect(self.Menu_DOCKER)

        # Dialog Directory
        self.dialog.menu_recent.toggled.connect(self.Info_Recent)
        self.dialog.menu_directory.currentTextChanged.connect(self.Menu_Directory)
        self.dialog.menu_sort.currentTextChanged.connect(self.Menu_Sort)
        self.dialog.menu_slideshow_sequence.currentTextChanged.connect(self.Menu_SlideShow_Sequence)
        self.dialog.menu_slideshow_time.timeChanged.connect(self.Menu_SlideShow_Time)
        self.dialog.menu_grid_horz.valueChanged.connect(self.Menu_Grid_U)
        self.dialog.menu_grid_vert.valueChanged.connect(self.Menu_Grid_V)
        self.dialog.menu_cache_load.valueChanged.connect(self.Menu_Cache_Load)
        self.dialog.menu_cache_clean.valueChanged.connect(self.Menu_Cache_Clean)
        self.dialog.menu_cache_thread.valueChanged.connect(self.Menu_Cache_Thread)
        self.dialog.menu_thumbnails.valueChanged.connect(self.Menu_Thumbnails)
        self.dialog.menu_ref_import.toggled.connect(self.Menu_Ref_Import)
        self.dialog.menu_ref_limit.valueChanged.connect(self.Menu_Ref_Limit)
        # Dialog Information
        self.dialog.info_title.textChanged.connect(self.Information_Save)
        self.dialog.info_subject.textChanged.connect(self.Information_Save)
        self.dialog.info_keyword.textChanged.connect(self.Information_Save)
        self.dialog.info_license.textChanged.connect(self.Information_Save)
        self.dialog.info_description.textChanged.connect(self.Information_Save)
        self.dialog.info_abstract.textChanged.connect(self.Information_Save)
        self.dialog.info_contact.itemClicked.connect(self.Information_Copy)
        # Dialog Connections
        self.dialog.menu_function_operation.currentTextChanged.connect(self.Menu_Function_Operation)
        self.dialog.menu_function_add.returnPressed.connect(self.Menu_Function_Add)
        self.dialog.menu_function_clear.clicked.connect(self.Menu_Function_Clear)
        self.dialog.menu_function_number.valueChanged.connect(self.Menu_Number)
        self.dialog.menu_function_path.textChanged.connect(self.Menu_Function_Path)
        self.dialog.menu_function_run.clicked.connect(self.Function_ValidPath)
        # Dialog
        self.dialog.tab_widget.tabBarClicked.connect(self.Information_Read)

        # Copyright
        self.dialog.zzz.clicked.connect(self.Menu_Copyright)
    def Modules(self):
        # Directory
        self.dir = QDir(self.directory_plugin)
        # File Watcher
        self.directory_watcher = QFileSystemWatcher(self)
        self.directory_watcher.directoryChanged.connect(lambda: self.Filter_Keywords(False))

        # Preview
        self.imagine_preview = ImagineBoard_Preview(self.layout.imagine_preview)
        self.imagine_preview.Set_Label(self.layout.imagine_preview)
        self.imagine_preview.SIGNAL_CLICK.connect(self.Preview_Increment)
        self.imagine_preview.SIGNAL_WHEEL.connect(self.Preview_Increment)
        self.imagine_preview.SIGNAL_STYLUS.connect(self.Preview_Increment)
        self.imagine_preview.SIGNAL_DRAG.connect(self.Drag_Drop)

        self.imagine_preview.SIGNAL_MODE.connect(self.Context_Mode)
        self.imagine_preview.SIGNAL_FUNCTION.connect(self.Function_Run)
        self.imagine_preview.SIGNAL_PIN.connect(self.Preview_Favorite)
        self.imagine_preview.SIGNAL_RANDOM.connect(self.Preview_Random)
        self.imagine_preview.SIGNAL_LOCATION.connect(self.File_Location)
        self.imagine_preview.SIGNAL_CLIP.connect(self.Preview_Clip)
        self.imagine_preview.SIGNAL_FIT.connect(self.Preview_Fit)
        self.imagine_preview.SIGNAL_NEW_DOCUMENT.connect(self.Insert_Document)
        self.imagine_preview.SIGNAL_INSERT_REFERENCE.connect(self.Insert_Reference)
        self.imagine_preview.SIGNAL_INSERT_LAYER.connect(self.Insert_Layer)
        self.imagine_preview.SIGNAL_COLOR.connect(self.Preview_Color)

        # Grid
        self.imagine_grid = ImagineBoard_Grid(self.layout.imagine_grid)
        self.imagine_grid.Set_Default(self.default_qpixmap)
        self.imagine_grid.SIGNAL_CLICK.connect(self.Grid_Increment)
        self.imagine_grid.SIGNAL_WHEEL.connect(self.Grid_Increment)
        self.imagine_grid.SIGNAL_STYLUS.connect(self.Grid_Increment)
        self.imagine_grid.SIGNAL_DRAG.connect(self.Hover_DragDrop)

        self.imagine_grid.SIGNAL_MODE.connect(self.Context_Mode)
        self.imagine_grid.SIGNAL_FUNCTION_GRID.connect(self.Function_Grid)
        self.imagine_grid.SIGNAL_FUNCTION_DROP.connect(self.Function_Run)
        self.imagine_grid.SIGNAL_PIN.connect(self.Grid_Favorite)
        self.imagine_grid.SIGNAL_NAME.connect(self.Grid_Name)
        self.imagine_grid.SIGNAL_PREVIEW.connect(self.Grid_Preview)

        # Reference
        self.imagine_reference = ImagineBoard_Reference(self.layout.imagine_reference)
        self.imagine_reference.SIGNAL_MODE.connect(self.Context_Mode)
        self.imagine_reference.SIGNAL_DRAG.connect(self.Drag_Drop)
        self.imagine_reference.SIGNAL_DROP.connect(self.Reference_Add)
        self.imagine_reference.SIGNAL_UPDATE.connect(self.Reference_Update)
        self.imagine_reference.SIGNAL_LOAD.connect(self.Reference_Load)

        # Thread Function
        self.thread_function = Thread_Function()
        self.thread_function.Docker(self.dialog)
        self.thread_function.SIGNAL_PBAR_VALUE.connect(self.Function_PBAR_Value)
        self.thread_function.SIGNAL_PBAR_MAX.connect(self.Function_PBAR_Max)
        self.thread_function.SIGNAL_STRING.connect(self.Function_String)
        self.thread_function.SIGNAL_NUMBER.connect(self.Function_Number)
        self.thread_function.SIGNAL_RESET.connect(self.Function_Reset)
        self.thread_function.SIGNAL_ITEM.connect(self.Function_Item)
        self.thread_function.SIGNAL_NEWPATH.connect(self.Function_NewPath)
    def Timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.Preview_SlideShow_Play)
    def Style(self):
        # Mode Size
        if self.OS == "winnt":
            self.layout.mode.setMaximumWidth(50)
        else:
            self.layout.mode.setMaximumWidth(46)

        # Icons
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_play'))
        self.layout.anim_frame_b.setIcon(Krita.instance().icon('prevframe'))
        self.layout.anim_frame_f.setIcon(Krita.instance().icon('nextframe'))
        self.layout.anim_screenshot.setIcon(Krita.instance().icon('document-print'))

        self.layout.mode.setItemIcon(0, Krita.instance().icon('folder-pictures')) # Preview
        self.layout.mode.setItemIcon(1, Krita.instance().icon('gridbrush')) # Grid
        self.layout.mode.setItemIcon(2, Krita.instance().icon('zoom-fit')) # Reference
        self.layout.folder.setIcon(Krita.instance().icon('folder'))
        self.layout.thread.setIcon(Krita.instance().icon('document-import'))
        self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-start'))
        self.layout.docker.setIcon(Krita.instance().icon('settings-button'))

        self.dialog.menu_function_clear.setIcon(Krita.instance().icon('edit-clear-16'))

        # ToolTips
        self.layout.mode.setToolTip("Mode")
        self.layout.folder.setToolTip("Open Directory")
        self.layout.thread.setToolTip("Thread Cache")

        self.layout.slideshow.setToolTip("SlideShow Play")
        self.layout.filter.setToolTip("Filter Contents")
        self.layout.number.setToolTip("Number Index")
        self.layout.docker.setToolTip("Settings")

        self.layout.anim_playpause.setToolTip("Play / Pause")
        self.layout.anim_frame_b.setToolTip("Frame Backward")
        self.layout.anim_frame_f.setToolTip("Frame Forward")
        self.layout.anim_screenshot.setToolTip("Frame Save")

        # StyleSheets
        self.layout.anim_panel.setStyleSheet("#anim_panel{background-color: rgba(0, 0, 0, 50);}")
        self.dialog.tab_display.setStyleSheet("#tab_display{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scroll_area_information.setStyleSheet("#scroll_area_information{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.tab_function.setStyleSheet("#tab_function{background-color: rgba(0, 0, 100, 20);}")
    def Extension(self):
        # Install Extension for Docker
        extension = ImagineBoard_Extension(parent = Krita.instance())
        Krita.instance().addExtension(extension)
        # Connect Extension Signals
        extension.SIGNAL_BROWSE.connect(self.Shortcut_Browse)
    def Settings(self):
        #\\ Docker #########################################################
        # Menu Mode
        menu_mode = Krita.instance().readSetting("Imagine Board", "menu_mode", "")
        if menu_mode == "":
            Krita.instance().writeSetting("Imagine Board", "menu_mode", str(0) )
        else:
            self.layout.mode.setCurrentIndex(int(menu_mode))
        # Directory Path
        directory_path = str( Krita.instance().readSetting("Imagine Board", "directory_path", "") )
        if directory_path == "":
            Krita.instance().writeSetting("Imagine Board", "directory_path", "")
        else:
            self.directory_path = directory_path
        # Filter
        filter = str(Krita.instance().readSetting("Imagine Board", "filter", ""))
        if filter == "":
            Krita.instance().writeSetting("Imagine Board", "filter", "")
        else:
            self.layout.filter.setText(filter)

        #//
        #\\ Dialog Display #################################################
        # Recent Documents
        recent_documents = Krita.instance().readSetting("Imagine Board", "recent_documents", "")
        if recent_documents == "":
            Krita.instance().writeSetting("Imagine Board", "recent_documents", "")
        else:
            self.dialog.menu_recent.setChecked(eval(recent_documents))
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
            tempo = QTime(0,0,0).addMSecs(float(ms))
            self.dialog.menu_slideshow_time.setTime(tempo)
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
        # Thumbnail Limit
        thumbnail_limit = Krita.instance().readSetting("Imagine Board", "thumbnail_limit", "")
        if thumbnail_limit == "":
            Krita.instance().writeSetting("Imagine Board", "thumbnail_limit", str(256) )
        else:
            self.dialog.menu_thumbnails.setValue(int(thumbnail_limit))
        # Reference Import
        ref_import = Krita.instance().readSetting("Imagine Board", "ref_import", "")
        if ref_import == "":
            Krita.instance().writeSetting("Imagine Board", "ref_import", "")
        else:
            self.dialog.menu_ref_import.setChecked(eval(ref_import))
        # Reference Limit
        ref_limit = Krita.instance().readSetting("Imagine Board", "ref_limit", "")
        if ref_limit == "":
            Krita.instance().writeSetting("Imagine Board", "ref_limit", str(2000) )
        else:
            self.dialog.menu_ref_limit.setValue(int(ref_limit))

        #//
        #\\ Dialog Function ################################################
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

        #//
        #\\ References #####################################################
        references = Krita.instance().readSetting("Imagine Board", "references", "")
        if references == "":
            Krita.instance().writeSetting("Imagine Board", "references", "")
        else:
            self.references = eval(references)
            self.imagine_reference.Board_Load(self.references)

        #//

    #//
    #\\ Menu ###################################################################
    def Menu_Mode(self, mode):
        # prepare cycle
        self.Display_Shrink()
        self.AnimPanel_Shrink()
        self.imagine_reference.Set_Active(False)
        # Preview
        if mode == 0:
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            # Height
            self.layout.imagine_preview.setMaximumHeight(16777215)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(0)
            self.layout.progress_bar.setMaximumHeight(5)
            self.layout.slider.setMaximumHeight(15)
            # Width
            self.layout.folder.setMinimumWidth(20)
            self.layout.folder.setMaximumWidth(20)
            self.layout.slideshow.setMinimumWidth(20)
            self.layout.slideshow.setMaximumWidth(20)
            self.layout.thread.setMinimumWidth(0)
            self.layout.thread.setMaximumWidth(0)
        # Grid
        if mode == 1:
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            # Height
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(16777215)
            self.layout.imagine_reference.setMaximumHeight(0)
            self.layout.progress_bar.setMaximumHeight(5)
            self.layout.slider.setMaximumHeight(15)
            # Width
            self.layout.folder.setMinimumWidth(20)
            self.layout.folder.setMaximumWidth(20)
            self.layout.slideshow.setMinimumWidth(0)
            self.layout.slideshow.setMaximumWidth(0)
            self.layout.thread.setMinimumWidth(20)
            self.layout.thread.setMaximumWidth(20)
        # Reference
        if mode == 2:
            # Module Containers
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            # Height
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(16777215)
            self.layout.progress_bar.setMaximumHeight(0)
            self.layout.slider.setMaximumHeight(0)
            # Width
            self.layout.folder.setMinimumWidth(0)
            self.layout.folder.setMaximumWidth(0)
            self.layout.slideshow.setMinimumWidth(0)
            self.layout.slideshow.setMaximumWidth(0)
            self.layout.thread.setMinimumWidth(0)
            self.layout.thread.setMaximumWidth(0)
        # update cycle
        if self.menu_mode != mode: # After a filter with null results this ensure other modes update
            self.menu_mode = mode
            self.Display_Clean()
            self.Display_Update()
        self.dirty = 5
        # Save
        Krita.instance().writeSetting("Imagine Board", "menu_mode", str( self.menu_mode ))
    def Display_Shrink(self):
        self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.imagine_preview.setMinimumHeight(0)
        self.layout.imagine_grid.setMinimumHeight(0)
        self.layout.imagine_reference.setMinimumHeight(0)
        self.layout.imagine_preview.setMaximumHeight(16777215)
        self.layout.imagine_grid.setMaximumHeight(16777215)
        self.layout.imagine_reference.setMaximumHeight(16777215)
    # Animation
    def Menu_AnimPanel(self, anim):
        # State
        if self.menu_mode == 0 and anim == True:
            value = 20
            margin = 1
        else:
            value = 0
            margin = 0
        # Widgets
        self.layout.anim_panel.setMinimumHeight(value)
        self.layout.anim_panel.setMaximumHeight(value)
        self.layout.anim_playpause.setMinimumHeight(value)
        self.layout.anim_playpause.setMaximumHeight(value)
        self.layout.anim_frame_b.setMinimumHeight(value)
        self.layout.anim_frame_b.setMaximumHeight(value)
        self.layout.anim_frame_f.setMinimumHeight(value)
        self.layout.anim_frame_f.setMaximumHeight(value)
        self.layout.anim_screenshot.setMinimumHeight(value)
        self.layout.anim_screenshot.setMaximumHeight(value)
        self.layout.anim_panel_layout.setContentsMargins(margin,margin,margin,margin)
        # update cycle
        if self.menu_anim != anim:
            self.menu_anim = anim
            self.dirty = 5
    def AnimPanel_Shrink(self):
        self.layout.anim_panel.setMinimumHeight(0)
        self.layout.anim_panel.setMaximumHeight(0)
        self.layout.anim_playpause.setMinimumHeight(0)
        self.layout.anim_playpause.setMaximumHeight(0)
        self.layout.anim_frame_b.setMinimumHeight(0)
        self.layout.anim_frame_b.setMaximumHeight(0)
        self.layout.anim_frame_f.setMinimumHeight(0)
        self.layout.anim_frame_f.setMaximumHeight(0)
        self.layout.anim_screenshot.setMinimumHeight(0)
        self.layout.anim_screenshot.setMaximumHeight(0)
        self.layout.anim_panel_layout.setContentsMargins(0,0,0,0)
    # Directory
    def Menu_Directory(self):
        # Directory
        directory = self.dialog.menu_directory.currentText()
        if directory == "Normal":
            self.file_extension = file_normal
        if directory == "BackUp~":
            self.file_extension = file_backup
        self.Filter_Keywords(True)
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
        self.Filter_Keywords(True)
        # Save
        Krita.instance().writeSetting("Imagine Board", "sort", str( SIGNAL_SORT ))
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
    def Menu_Grid_U(self):
        self.grid_horz = int(self.dialog.menu_grid_horz.value())
        Krita.instance().writeSetting("Imagine Board", "grid_u", str( self.grid_horz ))
        self.Menu_Grid_Size()
    def Menu_Grid_V(self):
        self.grid_vert = int(self.dialog.menu_grid_vert.value())
        Krita.instance().writeSetting("Imagine Board", "grid_v", str( self.grid_vert ))
        self.Menu_Grid_Size()
    def Menu_Grid_Size(self):
        self.grid_table = (self.grid_horz * self.grid_vert)
        self.imagine_grid.Set_Grid(self.grid_horz, self.grid_vert)
        self.Thumbnail_Size()
        self.Display_Update()
    def Menu_Cache_Load(self):
        self.cache_load = int(self.dialog.menu_cache_load.value())
        if self.cache_load >= self.cache_clean:
            self.dialog.menu_cache_clean.setValue(self.cache_load)
        Krita.instance().writeSetting("Imagine Board", "cache_load", str( self.cache_load ))
    def Menu_Cache_Clean(self):
        self.cache_clean = int(self.dialog.menu_cache_clean.value())
        if self.cache_clean <= self.cache_load:
            self.dialog.menu_cache_load.setValue(self.cache_clean)
        Krita.instance().writeSetting("Imagine Board", "cache_clean", str( self.cache_clean ))
    def Menu_Cache_Thread(self):
        self.cache_thread = int(self.dialog.menu_cache_thread.value())
        Krita.instance().writeSetting("Imagine Board", "cache_thread", str( self.cache_thread ))
    def Menu_Thumbnails(self):
        self.tn_limit = int(self.dialog.menu_thumbnails.value())
        self.Thumbnail_Size()
        Krita.instance().writeSetting("Imagine Board", "thumbnail_limit", str( self.tn_limit ))
    # Reference
    def Menu_Ref_Import(self):
        self.ref_import = self.dialog.menu_ref_import.isChecked()
        # Save
        Krita.instance().writeSetting("Imagine Board", "ref_import", str( self.ref_import ))
    def Menu_Ref_Limit(self):
        self.ref_limit = int(self.dialog.menu_ref_limit.value())
        # Save
        Krita.instance().writeSetting("Imagine Board", "ref_limit", str( self.ref_limit ))
    # Function
    def Menu_Function_Operation(self):
        operation = self.dialog.menu_function_operation.currentText()
        if operation == ">>":
            text = "Filter"
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
        if operation == "rename_random":
            text = "RENAME RANDOM (s)"
        if operation == "save_order":
            text = "SAVE ORDER (s, n)"
        if operation == "search_null":
            text = "SEARCH NULL"
        if operation == "search_copy":
            text = "SEARCH COPY"
        # crop excess from right
        width = self.layout.filter.width()
        letter = 8
        d = int(width / letter)
        text = text[:d]
        # Display Placeholder Text
        self.layout.filter.setPlaceholderText(text)
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
    def Menu_Function_Path(self):
        # Path
        path = self.Clean_Dot(os.path.normpath( self.dialog.menu_function_path.text() ))
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.dialog.menu_function_run.setEnabled(True)
        else:
            self.dialog.menu_function_run.setEnabled(False)
        # Save
        Krita.instance().writeSetting("Imagine Board", "function_path", str( self.dialog.menu_function_path.text() ))

    def Menu_DOCKER(self):
        self.dialog.show()
    def Menu_Copyright(self):
        self.copyright.show()

    #//
    #\\ Management #############################################################
    def Block_Signals(self, boolean):
        self.layout.slider.blockSignals(boolean)
        self.layout.number.blockSignals(boolean)
    def Clear_Focus(self):
        self.layout.filter.clearFocus()
        self.layout.number.clearFocus()
    def Update_Sizes(self):
        # Widgets
        self.imagine_preview.Set_Size(self.layout.imagine_preview.width(), self.layout.imagine_preview.height())
        self.imagine_grid.Set_Size(self.layout.imagine_grid.width(), self.layout.imagine_grid.height())
        self.imagine_reference.Set_Size(self.layout.imagine_reference.width(), self.layout.imagine_reference.height())

        # Thumbnails
        self.Thumbnail_Size()
    def Thumbnail_Size(self):
        w = self.layout.width()
        h = self.layout.height()
        u = self.grid_horz
        v = self.grid_vert
        rw = w / u
        rh = h / v
        if rw >= rh:
            self.tn_size = int(rw)
        else:
            self.tn_size = int(rh)
        comic = 2
        if (self.grid_table > comic and self.tn_size >= self.tn_limit):
            self.tn_size = self.tn_limit

    def Widget_Enable(self, boolean):
        # Panels
        self.layout.imagine_preview.setEnabled(boolean)
        self.layout.imagine_grid.setEnabled(boolean)
        self.layout.imagine_reference.setEnabled(boolean)
        # Animations
        self.layout.anim_frame_b.setEnabled(boolean)
        self.layout.anim_playpause.setEnabled(boolean)
        self.layout.anim_frame_f.setEnabled(boolean)
        self.layout.anim_screenshot.setEnabled(boolean)
        # Widgets
        self.layout.slider.setEnabled(boolean)
        self.layout.mode.setEnabled(boolean)
        self.layout.folder.setEnabled(boolean)
        self.layout.thread.setEnabled(boolean)
        self.layout.slideshow.setEnabled(boolean)
        self.layout.filter.setEnabled(boolean)
        self.layout.number.setEnabled(boolean)
        self.layout.docker.setEnabled(boolean)
    def Widget_Range(self, minimum, maximum):
        # Slider
        self.layout.slider.setMinimum(minimum)
        self.layout.slider.setMaximum(maximum)
        # Number
        self.layout.number.setMinimum(minimum)
        self.layout.number.setMaximum(maximum)
        self.layout.number.setSuffix(":" + str(maximum))
    def Widget_Values(self, value):
        self.Block_Signals(True)
        self.layout.slider.setValue(value+1)
        self.layout.number.setValue(value+1)
        self.Block_Signals(False)

    def Clean_Dot(self, text):
        if text == ".":
            text = ""
        return text

    #//
    #\\ File Options ###########################################################
    def Folder_Load(self, directory_path):
        # Variables
        try:load = int(Krita.instance().readSetting("Imagine Board", "preview_index", ""))
        except:pass
        self.imagine_preview.Set_Directory(directory_path)
        self.directory_watcher.addPath(directory_path)
        self.layout.folder.setToolTip("Dir : " + os.path.basename(directory_path))
        # Update Display
        self.Filter_Keywords(True)
        try:self.Preview_GoTo(load)
        except:pass
    def Folder_Open(self):
        file_dialog = QFileDialog(QWidget(self))
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        directory_path = file_dialog.getExistingDirectory(self, "Select Directory")
        directory_path = os.path.normpath( directory_path )
        if (directory_path != "" and directory_path != "." and self.directory_path != directory_path):
            self.directory_watcher.removePath(self.directory_path)
            self.directory_path = directory_path
            self.imagine_preview.Set_Directory(self.directory_path)
            self.directory_watcher.addPath(self.directory_path)
            self.layout.folder.setToolTip("Dir : " + os.path.basename(self.directory_path))
            Krita.instance().writeSetting("Imagine Board", "directory_path", str( self.directory_path ))
        self.imagine_preview.Set_Clip_Off()
        self.Filter_Keywords(True)

    def Filter_State(self, boolean):
        # Blocks Imagine Board from updating to changes to the Directory
        if boolean == True: # Start
            try:self.directory_watcher.addPath(self.directory_path)
            except:pass
        if boolean == False: # Stop
            try:self.directory_watcher.removePath(self.directory_path)
            except:pass
    def Filter_Keywords(self, reset):
        if self.widget_display == True:
            # Time Watcher
            start = QtCore.QDateTime.currentDateTimeUtc()

            # Reset to Page Zero
            if reset == True:
                self.preview_index = 0
                self.line_preview = 0
                self.line_grid = 0
                self.Widget_Values(0)

            search = ""
            if self.directory_path != "":
                if self.recent_documents == True:
                    # Recent Documents
                    recent_documents = krita.Krita.instance().recentDocuments()
                    files = []
                    for i in range(0, len(recent_documents)):
                        if recent_documents[i] != "":
                            files.append(recent_documents[i])
                    files.reverse()
                    count = len(files)
                else:
                    # Directory
                    self.dir.setPath(self.directory_path)
                    self.dir.setSorting(self.filter_sort)
                    self.dir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
                    self.dir.setNameFilters(self.file_extension)
                    files = self.dir.entryInfoList()
                    count = len(files)

                # Input parsing
                search = self.layout.filter.text()
                Krita.instance().writeSetting("Imagine Board", "filter", str( search ))
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
                        if self.recent_documents == True:
                            fn = os.path.basename(files[i])
                            fp = files[i]
                        else:
                            fn = files[i].fileName()
                            fp = files[i].filePath()
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
                    self.Widget_Range(1, self.preview_max)
                else:
                    self.images_found = False
                    self.Widget_Range(0, 0)

            # Update List and Display
            self.Display_Clean()
            self.Display_Update()

            # Time Watcher
            end = QtCore.QDateTime.currentDateTimeUtc()
            delta = start.msecsTo(end)
            time = QTime(0,0).addMSecs(delta)
            try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Directory: " + os.path.basename(self.directory_path) + " | Filter: " + search )
            except:pass
        else:
            self.Filter_Null()
    def Filter_Null(self):
        self.imagine_preview.Set_Default()
        self.dialog.menu_file.setText("")
        self.Widget_Range(0, 0)
        self.Widget_Values(0)

    def Display_Clean(self):
        if self.images_found == True:
            self.found_qpixmap = [self.null_qpixmap] * self.preview_max
        else:
            self.found_qpixmap = [self.default_qpixmap] * self.grid_table
    def Display_Update(self):
        # Images to Display
        self.Display_Sync()
        self.Display_Cache()
        self.Display_Preview()
        self.Display_Grid()
        self.Display_Reference()

        # Update
        if self.images_found == True:
            self.dialog.menu_file.setText( os.path.basename(self.found_path[self.preview_index]) )
        else:
            self.dialog.menu_file.setText("")
    def Display_Sync(self):
        if self.menu_mode == 0:
            self.line_preview = math.trunc((self.preview_index) / self.grid_horz)
            if self.line_preview <= self.line_grid:
                self.line_grid = self.line_preview
            if self.line_preview >= (self.line_grid + self.grid_vert):
                self.line_grid = self.line_preview - self.grid_vert + 1
        if self.menu_mode == 1:
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
            ll = self.Math_1D_Limit(grid_tl - load_left, 0, self.preview_max)
            lr = self.Math_1D_Limit(grid_br + load_right, 0, self.preview_max)
            cl = self.Math_1D_Limit(grid_tl - clean_left, 0, self.preview_max)
            cr = self.Math_1D_Limit(grid_br + clean_right, 0, self.preview_max)
            # Send Pixmaps to Modules
            try:
                for i in range(0, self.preview_max):
                    path = self.found_path[i]
                    # Populate Nearby
                    if (i >= ll and i <= lr):
                        if self.found_qpixmap[i].isNull() == True: # From List, Only load if the image is a null
                            qpixmap = QPixmap(path)#.scaled(self.tn_size, self.tn_size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
                            self.found_qpixmap[i] = qpixmap
                    # Clean Far Away
                    elif (i <= cl or i >= cr): # From List, Clean if image is too far away
                        self.found_qpixmap[i] = self.null_qpixmap
            except:
                pass
        else:
            self.found_qpixmap = [self.default_qpixmap] * self.grid_table

    def Display_Preview(self):
        if self.menu_mode == 0:
            if self.images_found == True:
                image_path = self.found_path[self.preview_index]
                if QPixmap(image_path).isNull() == False:
                    extension = os.path.splitext(image_path)[1] # .ext
                    if (extension == ".gif" or extension == ".webp"):
                        self.imagine_preview.Set_QMovie_Preview(image_path)
                        self.Menu_AnimPanel(True)
                    else:
                        self.imagine_preview.Set_QPixmap_Preview(image_path)
                        self.Menu_AnimPanel(False)
                else:
                    self.imagine_preview.Set_Default_Preview(image_path, self.default_qpixmap)
                    self.Menu_AnimPanel(False)
            else:
                self.imagine_preview.Set_QPixmap_Preview(self.default_path)
                self.Menu_AnimPanel(False)
        self.imagine_preview.update()
    def Display_Grid(self):
        if self.menu_mode == 1:
            # cunstruct pixmaps
            pixmaps = []
            n = 0
            if self.images_found == True:
                for v in range(0, self.grid_vert):
                    for h in range(0, self.grid_horz):
                        index = (self.line_grid * self.grid_horz) + n
                        try:
                            pixmaps.append([h, v, self.found_path[index], self.found_qpixmap[index]])
                        except:
                            pixmaps.append([h, v, "", self.null_qpixmap])
                        n += 1
            else:
                for v in range(0, self.grid_vert):
                    for h in range(0, self.grid_horz):
                        pixmaps.append([h, v, self.default_path, self.default_qpixmap])
            # send pixmaps
            self.imagine_grid.Set_QPixmaps(pixmaps)
        self.imagine_grid.update()
    def Display_Reference(self):
        if self.menu_mode == 2:
            pass
        self.imagine_reference.update()

    def Thumbnail_Start(self, SIGNAL_LOAD):
        # Prepare Widgets for Thread
        self.Block_Signals(True)
        self.Widget_Enable(False)
        self.layout.progress_bar.setMaximum(self.preview_max)
        # Variables
        self.found_qpixmap = []
        self.counter = 0
        self.layout.number.setMinimum(0)
        self.layout.number.setMaximum(16777215)

        # Range
        grid_tl = self.line_grid * self.grid_horz
        grid_br = grid_tl + self.grid_table
        limit_l = self.Math_1D_Limit(grid_tl - self.cache_thread, 0, self.preview_max)
        limit_r = self.Math_1D_Limit(grid_br + self.cache_thread, 0, self.preview_max)

        # Display
        self.placeholder_text = self.layout.filter.placeholderText()
        self.layout.filter.setPlaceholderText("Loading")

        # Start Threads operations
        self.thread_thumbnails = Thread_Thumbnails()
        self.thread_thumbnails.SIGNAL_IMAGE['QPixmap'].connect(self.Thumbnail_Image)
        self.thread_thumbnails.SIGNAL_RESET.connect(self.Thumbnail_Reset)
        self.thread_thumbnails.Variables_Run(os.path.basename(self.directory_path), self.found_path, self.preview_max, limit_l, limit_r)
        self.thread_thumbnails.start()
    def Thumbnail_Image(self, SIGNAL_IMAGE):
        # Recieve Image
        if SIGNAL_IMAGE.isNull() == False:
            qpixmap = SIGNAL_IMAGE.scaled(self.tn_size, self.tn_size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
        else:
            qpixmap = SIGNAL_IMAGE
        self.found_qpixmap.append(qpixmap)
        # Display Progress
        self.layout.progress_bar.setValue(self.counter)
        self.layout.number.setValue(self.counter + 1)
        self.layout.progress_bar.update()
        self.layout.number.update()
        self.counter += 1 # Increment Counter for next cycle
    def Thumbnail_Reset(self, SIGNAL_RESET):
        self.thread_thumbnails.quit()
        self.layout.progress_bar.setValue(1)
        self.Widget_Range(1, self.preview_max)
        self.Widget_Enable(True)
        self.Block_Signals(False)
        self.Preview_GoTo(self.preview_index)
        self.layout.filter.setPlaceholderText(self.placeholder_text)

    #//
    #\\ Signals ################################################################
    # Widgets
    def Value_Display(self, mode, value):
        self.Block_Signals(True)
        self.preview_index = int(value-1) # Humans start at 1 and script starts at 0
        if mode == "slider":
            self.layout.number.blockSignals(True)
            self.layout.number.setValue(value)
        if mode == "function_number":
            self.layout.slider.blockSignals(True)
            self.layout.slider.setValue(value)
        if self.images_found == True:
            self.Display_Update()
        self.Block_Signals(False)

    # Mouse Stylus
    def Hover_DragDrop(self, SIGNAL_DRAG):
        index = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_DRAG[0], SIGNAL_DRAG[1])
        path = self.found_path[index]
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.Drag_Drop(path)
    def Drag_Drop(self, image_path):
        thumb_size = 200
        if image_path[-3:] == "svg":
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
                reader.setClipRect(QRect(self.clip_x, self.clip_y, self.clip_w, self.clip_h))
            qimage = reader.read()
            try: qimage_scaled = qimage.scaled(thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except: qimage_scaled = qimage
            qpixmap = QPixmap().fromImage(qimage_scaled)
            # MimeData
            mimedata = QMimeData()
            url = QUrl().fromLocalFile(image_path)
            mimedata.setUrls([url])
            if (self.fit_canvas_bool == True and (self.canvas() is not None) and (self.canvas().view() is not None)):
                ad = Krita.instance().activeDocument()
                scale_width = ad.width() * self.image_scale
                scale_height = ad.height() * self.image_scale
            else:
                scale_width = qimage.width() * self.image_scale
                scale_height = qimage.height() * self.image_scale
            try: mimedata.setImageData(qimage.scaled(scale_width, scale_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except: mimedata.setImageData(qimage)
            # Clipboard
            clipboard = QApplication.clipboard().setImage(qimage)
            # Drag
            drag = QDrag(self)
            drag.setMimeData(mimedata)
            drag.setPixmap(qpixmap)
            drag.setHotSpot(QPoint(qimage_scaled.width() / 2 , qimage_scaled.height() / 2))
            drag.exec_(Qt.CopyAction)

    # Context Menu
    def Context_Mode(self, SIGNAL):
        self.layout.mode.setCurrentIndex(SIGNAL)
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
    def Insert_Document(self, SIGNAL_NEW_DOCUMENT):
        document = Krita.instance().openDocument(SIGNAL_NEW_DOCUMENT)
        Application.activeWindow().addView(document)
    def Insert_Reference(self, SIGNAL_INSERT_REFERENCE):
        if ((self.canvas() is not None) and (self.canvas().view() is not None) and self.preview_max > 0):
            reader = QImageReader(SIGNAL_INSERT_REFERENCE)
            if self.clip_state == True:
                reader.setClipRect(QRect(self.clip_x, self.clip_y, self.clip_w, self.clip_h))
            qimage = reader.read()
            if QPixmap().fromImage(qimage).isNull() == False:
                if self.fit_canvas_bool == True:
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
            # Place reference
            QApplication.clipboard().setImage(qimage)
            Krita.instance().action('paste_as_reference').trigger()
    def Insert_Layer(self, SIGNAL_INSERT_LAYER):
        if ((self.canvas() is not None) and (self.canvas().view() is not None) and self.preview_max > 0):
            image_path = SIGNAL_INSERT_LAYER
            if image_path[-3:] == "svg":
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
            else: # Default Case for all static Images. This excludes animated GIFs.
                # QImage
                reader = QImageReader(image_path)
                if self.clip_state == True:
                    reader.setClipRect(QRect(self.clip_x, self.clip_y, self.clip_w, self.clip_h))
                qimage = reader.read()
                if QPixmap().fromImage(qimage).isNull() == False:
                    if self.fit_canvas_bool == True:
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

    # Extension
    def Shortcut_Browse(self, SIGNAL_BROWSE):
        if self.menu_mode == 0:
            self.Preview_Increment(SIGNAL_BROWSE)
        if self.menu_mode == 1:
            self.Grid_Increment(SIGNAL_BROWSE)

    #//
    #\\ Preview ################################################################
    def Preview_GoTo(self, SIGNAL_VALUE):
        if self.images_found == True:
            self.preview_index = self.Math_1D_Limit(SIGNAL_VALUE, 0, self.preview_max-1)
            self.Widget_Values(self.preview_index)
            self.Display_Update()
    def Preview_Increment(self, SIGNAL_UNIT):
        if self.images_found == True:
            if self.playpause == False:
                self.Preview_PlayPause(True)
            self.preview_index += SIGNAL_UNIT
            self.preview_index = self.Math_1D_Limit(self.preview_index, 0, self.preview_max-1)
            self.Widget_Values(self.preview_index)
            self.Display_Update()

    def Preview_Favorite(self, SIGNAL_PIN):
        if SIGNAL_PIN not in self.references:
            self.Reference_Add(SIGNAL_PIN)
    def Preview_Clip(self, SIGNAL_CLIP):
        self.clip_state = SIGNAL_CLIP[0]
        self.clip_x = SIGNAL_CLIP[1]
        self.clip_y = SIGNAL_CLIP[2]
        self.clip_w = SIGNAL_CLIP[3]
        self.clip_h = SIGNAL_CLIP[4]
    def Preview_Random(self, SIGNAL_RANDOM):
        random_value = self.Math_1D_Random_Range(self.preview_max-1)
        self.Preview_GoTo(random_value)
    def Preview_Fit(self, SIGNAL_FIT):
        self.fit_canvas_bool = SIGNAL_FIT
    def Preview_Color(self, SIGNAL_COLOR):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            d_cm = Krita.instance().activeDocument().colorModel()
            d_cd = Krita.instance().activeDocument().colorDepth()
            d_cp = Krita.instance().activeDocument().colorProfile()
            kritaEraserAction = Krita.instance().action("erase_action")
            fg_color = ManagedColor(d_cm, d_cd, d_cp)
            kac1 = SIGNAL_COLOR[0]
            kac2 = SIGNAL_COLOR[1]
            kac3 = SIGNAL_COLOR[2]

            if (d_cm == "A" or d_cm == "GRAYA"):
                kac1 = self.aaa_1
                kbc1 = self.aaa_bg1
                fg_color.setComponents([kac1, 1.0])
            if (d_cm == "RGBA" or d_cm == None):
                fg_comp = fg_color.components()
                if (d_cd == "U8" or d_cd == "U16"):
                    fg_comp[0] = kac3
                    fg_comp[1] = kac2
                    fg_comp[2] = kac1
                    fg_comp[3] = 1
                if (d_cd == "F16" or d_cd == "F32"):
                    fg_comp[0] = kac1
                    fg_comp[1] = kac2
                    fg_comp[2] = kac3
                    fg_comp[3] = 1
                fg_color.setComponents(fg_comp)

            fg_display = fg_color.colorForCanvas(Krita.instance().activeWindow().activeView().canvas())
            self.disp_1 = fg_display.redF()
            self.disp_2 = fg_display.greenF()
            self.disp_3 = fg_display.blueF()

            Krita.instance().activeWindow().activeView().setForeGroundColor(fg_color)
            if kritaEraserAction.isChecked():
                kritaEraserAction.trigger()

    def Preview_SlideShow_Switch(self, SIGNAL_SLIDESHOW):
        if SIGNAL_SLIDESHOW == True:
            self.layout.thread.setEnabled(False)
            self.layout.progress_bar.setMaximumHeight(0)
            self.layout.slider.setMaximumHeight(0)
            self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-stop'))
            self.layout.slideshow.setToolTip("SlideShow Stop")
            self.layout.mode.setEnabled(False)
            self.layout.folder.setEnabled(False)
            self.layout.thread.setEnabled(False)
            self.layout.filter.setEnabled(False)
            self.layout.slider.setEnabled(False)
            self.layout.number.setEnabled(False)
            self.timer.start(self.slideshow_time)
        else:
            self.layout.thread.setEnabled(True)
            self.layout.progress_bar.setMaximumHeight(5)
            self.layout.slider.setMaximumHeight(15)
            self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-start'))
            self.layout.slideshow.setToolTip("SlideShow Play")
            self.layout.mode.setEnabled(True)
            self.layout.folder.setEnabled(True)
            self.layout.thread.setEnabled(True)
            self.layout.filter.setEnabled(True)
            self.layout.slider.setEnabled(True)
            self.layout.number.setEnabled(True)
            self.timer.stop()
        self.dirty = 5
    def Preview_SlideShow_Play(self):
        if self.slideshow_sequence == "Linear":
            loop = self.preview_index + 1
            self.preview_index = self.Math_1D_Loop(loop, self.preview_max-1)
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
        self.playpause = playpause
        if playpause == True:
            self.Preview_Play()
        elif playpause == False:
            self.Preview_Pause()
    def Preview_Play(self):
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_play'))
        self.imagine_preview.Movie_Play()
    def Preview_Pause(self):
        self.layout.anim_playpause.setIcon(Krita.instance().icon('animation_pause'))
        self.imagine_preview.Movie_Pause()
    def Preview_Frame_Back(self):
        self.imagine_preview.Movie_Frame_Back()
    def Preview_Frame_Forward(self):
        self.imagine_preview.Movie_Frame_Forward()
    def Preview_Screenshot(self):
        self.imagine_preview.Movie_Screenshot(self.directory_path)

    #//
    #\\ Grid ###################################################################
    def Grid_Increment(self, SIGNAL_UNIT):
        if self.playpause == False:
            self.Preview_PlayPause(True)
        self.line_grid += self.Math_1D_Limit(SIGNAL_UNIT, 0, self.preview_max-1)
        self.preview_index += (SIGNAL_UNIT * self.grid_horz)
        self.preview_index = self.Math_1D_Limit(self.preview_index, 0, self.preview_max-1)
        self.Widget_Values(self.preview_index)
        if self.images_found == True:
            self.Display_Update()

    def Grid_Favorite(self, SIGNAL_PIN):
        num = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_PIN[0], SIGNAL_PIN[1])
        if (self.images_found == True and num < self.preview_max):
            pin = self.found_path[num]
            if pin not in self.references:
                self.Reference_Add(pin)
    def Grid_Name(self, SIGNAL_NAME):
        num = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_NAME[0], SIGNAL_NAME[1])
        if (self.images_found == True and num < self.preview_max):
            self.preview_index = self.Math_1D_Limit(num, 0, self.preview_max-1)
            self.Widget_Values(self.preview_index)
            name = os.path.basename(self.found_path[num])
        else:
            name = ""
        self.dialog.menu_file.setText(name)
    def Grid_Preview(self, SIGNAL_PREVIEW):
        self.layout.mode.setCurrentIndex(0)
        self.preview_index = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_PREVIEW[0], SIGNAL_PREVIEW[1])
        self.Preview_GoTo(self.preview_index)

    #//
    #\\ Reference ##############################################################
    def Reference_Add(self, path):
        location_x = 10
        location_y = 10
        qpixmap = QPixmap(path)
        if self.ref_import == True:
            limit_w = self.Math_1D_Limit(qpixmap.width(), 1, self.ref_limit)
            limit_h = self.Math_1D_Limit(qpixmap.height(), 1, self.ref_limit)
            qpixmap = qpixmap.scaled(limit_w, limit_h, Qt.KeepAspectRatio, Qt.FastTransformation)
        else:
            size = 100
            qpixmap = qpixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
        width = qpixmap.width()
        height = qpixmap.height()
        angle = self.Math_2D_Points_Lines_Angle(width,0, 0,0, width, height)
        perimeter = (2 * width) + (2 * height)
        area = width * height
        ratio = width / height
        pin = [os.path.normpath(path), location_x, location_y, width, height, angle, perimeter, area, ratio]
        self.references.append(pin)
        self.imagine_reference.Pin_Add(pin)

    def Reference_Load(self, SIGNAL_LOAD):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            try:
                self.references = eval(Krita.instance().activeDocument().annotation("imagineboard_annotations"))
                self.imagine_reference.Board_Load(self.references)
            except:
                pass
    def Reference_Update(self, SIGNAL_UPDATE):
        # Signal
        self.kra_bind = SIGNAL_UPDATE[0]
        self.references = SIGNAL_UPDATE[1]
        data = str(self.references)
        # Kritarc
        Krita.instance().writeSetting("Imagine Board", "references", data )
        # Save Annotations
        if self.kra_bind == True:
            if ((self.canvas() is not None) and (self.canvas().view() is not None)):
                try:Krita.instance().activeDocument().setAnnotation('imagineboard_annotations', "imagineboard annotations", QByteArray(data.encode()) )
                except:pass

    #//
    #\\ Information ############################################################
    def Info_Recent(self):
        self.recent_documents = self.dialog.menu_recent.isChecked()
        self.Filter_Keywords(True)
        # Save
        Krita.instance().writeSetting("Imagine Board", "recent_documents", str( self.recent_documents ))

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
            t_editing_cycles = self.cycles_to_time( self.info.get("editing-cycles") )
            t_editing_time = self.cycles_to_time( self.info.get("editing-time") )
            d_date = self.display_date( self.info.get("date") )
            d_creation_date = self.display_date( self.info.get("creation-date") )
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
            creator_fl_name = self.info.get("creator-first-name") + " " + self.info.get("creator-last-name")

        # Place Values
        self.dialog.info_path.setText(file_name)

        self.dialog.info_title.setText(self.info.get("title"))
        self.dialog.info_subject.setText(self.info.get("subject"))
        self.dialog.info_keyword.setText(self.info.get("keyword"))
        self.dialog.info_license.setText(self.info.get("license"))
        self.dialog.info_abstract.setText(self.info.get("abstract")) # Abstract is Description inside Krita
        self.dialog.info_description.setText(self.info.get("description")) # Description is Abstract inside Krita

        self.dialog.info_creator.setText(self.info.get("initial-creator"))
        self.dialog.info_edit_cycles.setText(str(self.info.get("editing-cycles")) + str(t_editing_cycles))
        self.dialog.info_edit_time.setText(str(self.info.get("editing-time")) + str(t_editing_time))
        self.dialog.info_date.setText(d_date)
        self.dialog.info_creation.setText(d_creation_date + delta_creation)
        self.dialog.info_language.setText(self.info.get("language"))

        self.dialog.info_nick_name.setText(self.info.get("full-name"))
        self.dialog.info_full_name.setText(creator_fl_name)
        self.dialog.info_initials.setText(self.info.get("initial"))
        self.dialog.info_author_title.setText(self.info.get("author-title"))
        self.dialog.info_position.setText(self.info.get("position"))
        self.dialog.info_company.setText(self.info.get("company"))
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
                  <initial-creator>""" + self.info.get("initial-creator") + """</initial-creator>
                  <language>""" + self.info.get("language") + """</language>
                  <license>""" + new_license + """</license>
                 </about>
                 <author>
                  <full-name>""" + self.info.get("full-name") + """</full-name>
                  <creator-first-name>""" + self.info.get("creator-first-name") + """</creator-first-name>
                  <creator-last-name>""" + self.info.get("creator-last-name") + """</creator-last-name>
                  <initial>""" + self.info.get("initial") + """</initial>
                  <author-title>""" + self.info.get("author-title") + """</author-title>
                  <position>""" + self.info.get("position") + """</position>
                  <company>""" + self.info.get("company") + """</company>
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
        # time constants
        k_seg = 1
        k_min = 60
        k_hor = 60 * k_min
        k_dia = 24 * k_hor
        k_mes = 30.4167 * k_dia
        k_ano = 12 * k_mes
        seg = 0
        min = 0
        hor = 0
        dia = 0
        mes = 0
        ano = 0
        # string constants
        suffix = ""
        seconds = ""
        minutes = ""
        hours = ""
        days = ""
        months = ""
        years = ""
        # Checks
        if (cycles != "" and cycles != 0 and cycles != None):
            cycles = int(cycles)
            while cycles >= k_ano:
                ano += 1
                cycles -= k_ano
            while cycles >= k_mes:
                mes += 1
                cycles -= k_mes
            while cycles >= k_dia:
                dia += 1
                cycles -= k_dia
            while cycles >= k_hor:
                hor += 1
                cycles -= k_hor
            while cycles >= k_min:
                min += 1
                cycles -= k_min
            seg = int(cycles)
            # strings
            if (ano>0 or mes>0 or dia>0 or hor>0 or min>0 or seg>0):
                suffix = " >> "
            if ano > 0:
                years = str(ano).zfill(1) + "y "
            if mes > 0:
                months = str(mes).zfill(2) + "m "
            if dia > 0:
                days = str(dia).zfill(2) + "d "
            if hor > 0:
                hours = str(hor).zfill(2) + "h "
            if min > 0:
                minutes = str(min).zfill(2) + "m "
            if seg > 0:
                seconds = str(seg).zfill(2) + "s"
            # string missing
            if (mes==0 and ano>0):
                months = "00m "
            if (dia==0 and (ano>0 or mes>0)):
                days = "00d "
            if (hor==0 and (ano>0 or mes>0 or dia>0)):
                hours = "00h "
            if (min==0 and (ano>0 or mes>0 or dia>0 or hor>0)):
                minutes = "00m "
            if (seg==0 and (ano>0 or mes>0 or dia>0 or hor>0 or seg>0)):
                seconds = "00s"
        string = suffix + years + months + days + hours + minutes + seconds
        # return
        return string
    def display_date(self, date):
        if (date != "" and date != None):
            ano = date[0:4]
            mes = date[5:7]
            dia = date[8:10]
            hor = date[11:13]
            min = date[14:16]
            seg = date[17:19]
            string = ano+"-"+mes+"-"+dia+" "+ hor+":"+min+":"+seg
        else:
            string = ""
        return string
    def time_delta(self, year1, month1, day1, hour1, minute1, second1, year2, month2, day2, hour2, minute2, second2):
        date_start = datetime.datetime(year1, month1, day1, hour1, minute1, second1)
        date_now = datetime.datetime(year2, month2, day2, hour2, minute2, second2)
        delta = (date_now - date_start)
        string = self.cycles_to_time((delta.days * 86400) + delta.seconds)
        return string

    #//
    #\\ Function (Key Enter) ###################################################
    def Function_Grid(self, SIGNAL_FUNCTION_GRID):
        index = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_FUNCTION_GRID[0], SIGNAL_FUNCTION_GRID[1])
        path = self.found_path[index]
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.Function_Run([path])
    def Function_ValidPath(self):
        path = self.Clean_Dot(os.path.normpath( self.dialog.menu_function_path.text() ))
        exists = os.path.exists(path)
        if (len(path) > 0 and exists == True):
            self.Function_Run([path])
    def Function_Run(self, SIGNAL_FUNCTION):
        # Settings
        operation = self.dialog.menu_function_operation.currentText()
        strings = self.List_Selected()
        number = self.dialog.menu_function_number.value()
        paths = SIGNAL_FUNCTION
        # Has valid Paths
        if len(paths) > 0:
            # Sort Files and Folders
            files = []
            folders = []
            for i in range(0, len(paths)):
                if os.path.isfile(paths[i]) == True:
                    files.append( os.path.normpath(paths[i]) )
                if os.path.isdir(paths[i]) == True:
                    folders.append( os.path.normpath(paths[i]) )

            # File Watcher
            self.Filter_State(False)
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
        self.Filter_State(True)
        self.Function_Enabled(True)
        self.Filter_Keywords(False)
    def Function_Item(self, SIGNAL_ITEM):
        # Variables
        list_count = self.dialog.menu_function_list.count()
        # Create a Set
        keys = set()
        for i in range(0, list_count):
            keys.add( self.dialog.menu_function_list.item(i).text() )
        keys.add( SIGNAL_ITEM )
        # Clear List
        self.dialog.menu_function_list.clear()
        # Repopulate List
        keys = list(keys)
        for i in range(0, len(keys)):
            self.dialog.menu_function_list.addItem(keys[i])
        # Save
        self.List_Save()
    def Function_NewPath(self, SIGNAL_NEWPATH):
        # Paths
        path_i = str(SIGNAL_NEWPATH[0])
        path_new = str(SIGNAL_NEWPATH[1])
        # Change References
        for i in range(0, len(self.references)):
            if self.references[i][0] == path_i:
                self.references[i][0] = path_new
                self.imagine_reference.Pin_Replace(i, path_new)

    def Function_Enabled(self, bool):
        self.dialog.menu_function_operation.setEnabled(bool)
        self.dialog.menu_function_add.setEnabled(bool)
        self.dialog.menu_function_clear.setEnabled(bool)
        self.dialog.menu_function_list.setEnabled(bool)
        self.dialog.menu_function_number.setEnabled(bool)
        self.dialog.menu_function_path.setEnabled(bool)
        self.dialog.menu_function_run.setEnabled(bool)

    #//
    #\\ Math ###################################################################
    def grid_to_prev(self, gp, gh, sx, sy):
        prev = (gp * gh) + (sy * gh) + sx
        return prev

    def Math_1D_Lerp(self, percent, bot, top):
        delta = top - bot
        lerp = bot + ( delta * percent)
        return lerp
    def Math_1D_Limit(self, var, bot, top):
        if var <= bot:
            var = bot
        if var >= top:
            var = top
        return var
    def Math_1D_Loop(self, var, limit):
        if var < 0:
            var = limit
        if var > limit:
            var = 0
        return var
    def Math_1D_Random_Range(self, range):
        time = int(QtCore.QTime.currentTime().toString('hhmmssms'))
        random.seed(time)
        random_value = random.randint(0, range)
        while random_value == self.preview_index:
            random_value = random.randint(0, range)
        return random_value
    def Math_2D_Points_Lines_Angle(self, x1, y1, x2, y2, x3, y3):
        v1 = (x1-x2, y1-y2)
        v2 = (x3-x2, y3-y2)
        v1_theta = math.atan2(v1[1], v1[0])
        v2_theta = math.atan2(v2[1], v2[0])
        angle = (v2_theta - v1_theta) * (180.0 / math.pi)
        if angle < 0:
            angle += 360.0
        return angle

    #//
    #\\ Widget Events ##########################################################
    def showEvent(self, event):
        self.Display_Clean()
        self.Menu_Mode(self.menu_mode)
        self.widget_display = True
        self.Folder_Load(self.directory_path)
    def resizeEvent(self, event):
        self.Update_Sizes()
    def leaveEvent(self, event):
        self.Clear_Focus()
    def closeEvent(self, event):
        self.widget_display = False
        self.found_qpixmap.clear()

    def paintEvent(self, event):
        # Bypass PyQt5 limitation to detect correct size of widget right after change in Size Policy
        if self.dirty > 0:
            self.Update_Sizes()
            self.dirty -= 1

    #//
    #\\ Change Canvas ##########################################################
    def canvasChanged(self, canvas):
        pass

    #//
    #\\ Notes ##################################################################
    """
    # Label Message
    self.layout.label.setText("message")

    # Pop Up Message
    QMessageBox.information(QWidget(), i18n("Warnning"), i18n("message"))

    # Log Viewer Message
    QtCore.qDebug(str())
    QtCore.qDebug("message")
    QtCore.qWarning("message")
    QtCore.qCritical("message")

    Code
    found_qpixmap = qpixmap#.scaled(self.tn_size, self.tn_size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
    """
    #//

class Thread_Thumbnails(QThread):
    SIGNAL_IMAGE = QtCore.pyqtSignal(QPixmap)
    SIGNAL_RESET = QtCore.pyqtSignal(int)

    #\\ Initialize #############################################################
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

    #//
    #\\ Cycle ##################################################################
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
        try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Directory: "+ self.folder + " | Thread Cache")
        except:pass

    #//

class Thread_Function(QThread):
    SIGNAL_COUNTER = QtCore.pyqtSignal(int)
    SIGNAL_PBAR_VALUE = QtCore.pyqtSignal(int)
    SIGNAL_PBAR_MAX = QtCore.pyqtSignal(int)
    SIGNAL_STRING = QtCore.pyqtSignal(str)
    SIGNAL_NUMBER = QtCore.pyqtSignal(int)
    SIGNAL_RESET = QtCore.pyqtSignal(int)
    SIGNAL_ITEM = QtCore.pyqtSignal(str)
    SIGNAL_NEWPATH = QtCore.pyqtSignal(list)

    #\\ Initialize #############################################################
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
        self.files = []
        self.folders = []
        self.directory = ""
        self.reset = ""
    def Variables_Run(self, operation, strings, number, files, folders, directory):
        self.Variables_Reset()
        self.operation = operation
        self.strings = strings
        self.number = number
        self.files = files
        self.folders = folders
        self.directory = directory
    def verify_total(self, value):
        mat = value * value
        count = int((mat - value) / 2)
        return count

    #//
    #\\ Cycle ##################################################################
    def run(self):
        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # Operation Selection
        if self.operation != ">>":
            # Totals
            total_fil = len(self.files)
            total_dir = len(self.folders)
            rename = ["key_add", "key_replace", "key_remove", "key_clean", "rename_order", "rename_random"]
            if (total_fil == 0 and total_dir == 1): # Directory
                # Directory Construct
                self.dir.setPath(self.folders[0])
                self.dir.setSorting(QDir.LocaleAware)
                self.dir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
                self.dir.setNameFilters(file_normal)
                total = self.dir.count()
                files = self.dir.entryInfoList()
                path = []
                for i in range(0, len(files)):
                    path.append(files[i].filePath())
                # Modes
                if self.operation in rename:
                    self.File_Cycle(total, path, self.strings, self.number)
                elif self.operation == "key_populate":
                    self.File_Populate(total, path)
                elif self.operation == "save_order":
                    self.File_Save(total, path, self.strings, self.number, self.directory)
                elif self.operation == "search_null":
                    self.File_Null(total, path)
                elif self.operation == "search_copy":
                    self.File_Copy(total, path)
            elif total_fil > 0: # Files
                # Construct
                if self.operation in rename:
                    self.File_Cycle(total_fil, self.files, self.strings, self.number)
                elif self.operation == "key_populate":
                    self.File_Populate(total_fil, self.files)
                elif self.operation == "save_order":
                    self.File_Save(total_fil, self.files, self.strings, self.number, self.directory)
                elif self.operation == "search_null":
                    self.File_Null(total_fil, self.files)
                elif self.operation == "search_copy":
                    self.File_Copy(total_fil, self.files)

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo(end)
        time = QTime(0,0).addMSecs(delta)
        try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Operation " + str(self.operation) )
        except:pass

        # End
        self.SIGNAL_RESET.emit(0)

    #//
    #\\ File Cycle #############################################################
    def File_Cycle(self, total, path, key, number):
        self.SIGNAL_PBAR_MAX.emit(total)
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
            if self.operation == "rename_random": # Rename
                path_new = self.String_ReName(path_i, key, number, i, "random")
            # Confirm Differences to Apply
            exists = os.path.exists( os.path.normpath( os.path.join( os.path.dirname(path_i), path_new)))
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
    def File_Save(self, total, path, name, number, directory):
        self.SIGNAL_PBAR_MAX.emit(total)
        for i in range(0, total):
            # Counter
            self.SIGNAL_STRING.emit(str(i+1) + " : " + str(total))
            self.SIGNAL_PBAR_VALUE.emit(i+1)
            # Save
            path_i = os.path.normpath(path[i])
            path_new = os.path.normpath( self.String_Save(directory, name[0]) )
            check = os.path.exists(path_new)
            if check == False:
                qimage = QImage(path_i)
                qimage.save(path_new)
                try:QtCore.qDebug("IB save | " + str(path_new))
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
            qimage = QImage(path_i)
            for r in range(i+1, total):
                path_r = path[r]
                count += 1
                self.SIGNAL_STRING.emit(str(copy) + " : " + str(count+1) + " : " + str(ver_total+1))
                self.SIGNAL_PBAR_VALUE.emit(count+1)
                if path_r not in replicas:
                    if qimage == QImage(path_r):
                        copy += 1
                        replicas.append(path_r)
                        path_new = self.String_Copy(path_r)
                        if path_r != path_new:
                            self.SIGNAL_NEWPATH.emit([path_r, path_new])
                            try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " : " + str(os.path.basename(path_r)) + " >> " + str(os.path.basename(path_new)))
                            except:pass
                            self.qfile.rename(path_r, path_new)

    #//
    #\\ String #################################################################
    """
    Key Enter convention : ' Basename [ key1 key2 ... ].extension '
    """
    def String_Add(self, path, key):
        if len(key) == 0:
            path_new = path
        else:
            # Cut into sections
            directory = os.path.dirname(path) # dir
            bn = os.path.basename(path) # name.ext
            extension = os.path.splitext(path)[1] # .ext
            n = bn.find(extension)
            base = bn[:n] # name

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
            # Cut into sections
            directory = os.path.dirname(path) # dir
            bn = os.path.basename(path) # name.ext
            extension = os.path.splitext(path)[1] # .ext
            n = bn.find(extension)
            base = bn[:n] # name

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
            # Cut into sections
            directory = os.path.dirname(path) # dir
            bn = os.path.basename(path) # name.ext
            extension = os.path.splitext(path)[1] # .ext
            n = bn.find(extension)
            base = bn[:n] # name

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
        # Cut into sections
        directory = os.path.dirname(path) # dir
        bn = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name

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
        # Cut into sections
        directory = os.path.dirname(path) # dir
        bn = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name

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
            # Cut into sections
            directory = os.path.dirname(path) # dir
            bn = os.path.basename(path) # name.ext
            extension = os.path.splitext(path)[1] # .ext
            n = bn.find(extension)
            base = bn[:n] # name

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
            if mode == "order":
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
    def String_Save(self, directory, name):
        # Name formating
        if len(name) == 0:
            name = "image"
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
        # Cut into sections
        directory = os.path.dirname(path) # dir
        bn = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name

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
        # Cut into sections
        directory = os.path.dirname(path) # dir
        bn = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name

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

    #//
