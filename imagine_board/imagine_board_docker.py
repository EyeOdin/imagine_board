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
imagine_board_version = "2022_03_23"

file_normal = [
    "*.kra",
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
    "*.svg"
    ]
file_backup = [
    "*.kra~",
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
    "*.svg~"
    ]

#//


class ImagineBoard_Docker(DockWidget):
    """
    Imagine Board
    """

    #\\ Initialize the Docker Window ###########################################
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
        self.thumbnail = 256
        self.fit_canvas_bool = False
        self.image_scale = 1
        self.images_found = False

        # Preview
        self.preview_index = 0
        self.preview_max = 0

        # Grid
        self.grid_horz = 3
        self.grid_vert = 3
        self.grid_table = self.grid_horz * self.grid_vert
        self.grid_max = 0
        self.grid_delta = 0

        # Lines
        self.line_preview = 0
        self.line_grid = 0

        # Reference
        self.list_references = []

        # Animation
        self.playpause = True # True=Play  False=Pause

        # Cache amount
        self.cache_load = 3
        self.cache_thread = 2000
        self.cache_clean = 2 * self.cache_thread

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
        self.layout.thread.clicked.connect(self.Thumbnail_Start)
        self.layout.slideshow.toggled.connect(self.Preview_SlideShow_Switch)
        self.layout.filter.returnPressed.connect(lambda: self.Filter_Keywords(True))
        self.layout.number.valueChanged.connect(lambda: self.Value_Display("function_number", self.layout.number.value()))
        self.layout.docker.clicked.connect(self.Menu_DOCKER)

        # Dialog Connections
        self.dialog.menu_directory.currentTextChanged.connect(self.Menu_Directory)
        self.dialog.menu_sort.currentTextChanged.connect(self.Menu_Sort)
        # Dialog Connections
        self.dialog.menu_slideshow_sequence.currentTextChanged.connect(self.Menu_SlideShow_Sequence)
        self.dialog.menu_slideshow_time.timeChanged.connect(self.Menu_SlideShow_Time)
        self.dialog.menu_grid_horz.valueChanged.connect(self.Menu_Grid)
        self.dialog.menu_grid_vert.valueChanged.connect(self.Menu_Grid)
        # Dialog Connections
        self.dialog.menu_function_operation.currentTextChanged.connect(self.Menu_Function_Operation)
        self.dialog.menu_function_add.returnPressed.connect(self.Menu_Function_Add)
        self.dialog.menu_function_clear.clicked.connect(self.Menu_Function_Clear)
        self.dialog.menu_function_number.valueChanged.connect(self.Menu_Number)
        self.dialog.menu_function_path.textChanged.connect(self.Menu_Function_Path)
        self.dialog.menu_function_run.clicked.connect(self.Function_ValidPath)

        # Copyright
        self.dialog.zzz.clicked.connect(self.Menu_Copyright)
    def Modules(self):
        # Directory
        self.dir = QDir(self.directory_plugin)
        # File Watcher
        self.directory_watcher = QFileSystemWatcher(self)
        self.directory_watcher.directoryChanged.connect(lambda: self.Filter_Keywords(False))
        # Notifier
        self.notify = Krita.instance().notifier()

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

        # Thread Function
        self.thread_function = Thread_Function()
        self.thread_function.Docker(self.dialog)
        self.thread_function.SIGNAL_PBAR_VALUE.connect(self.Function_PBAR_Value)
        self.thread_function.SIGNAL_PBAR_MAX.connect(self.Function_PBAR_Max)
        self.thread_function.SIGNAL_STRING.connect(self.Function_String)
        self.thread_function.SIGNAL_NUMBER.connect(self.Function_Number)
        self.thread_function.SIGNAL_RESET.connect(self.Function_Reset)
        self.thread_function.SIGNAL_ITEM.connect(self.Function_Item)
    def Timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.Preview_SlideShow_Play)
    def Style(self):
        # Size
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
        self.layout.mode.setItemIcon(2, Krita.instance().icon('object-group-calligra')) # Reference
        self.layout.folder.setIcon(Krita.instance().icon('folder'))
        self.layout.thread.setIcon(Krita.instance().icon('document-import'))
        self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-start'))
        self.layout.docker.setIcon(Krita.instance().icon('settings-button'))

        self.dialog.menu_function_clear.setIcon(Krita.instance().icon('edit-clear-16'))

        # ToolTips
        self.layout.mode.setToolTip("Mode")
        self.layout.folder.setToolTip("Open Directory")
        self.layout.thread.setToolTip("Thumbnail Cache")

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
        self.dialog.group_a.setStyleSheet("#group_a{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.group_function.setStyleSheet("#group_function{background-color: rgba(0, 0, 20, 50);}")
    def Extension(self):
        # Install Extension for Docker
        extension = ImagineBoard_Extension(parent = Krita.instance())
        Krita.instance().addExtension(extension)
        # Connect Extension Signals
        extension.SIGNAL_BROWSE.connect(self.Shortcut_Browse)
    def Settings(self):
        try:
            # Docker
            self.layout.mode.setCurrentIndex( int(Krita.instance().readSetting("Imagine Board", "menu_mode", "")) )
            self.directory_path = str( Krita.instance().readSetting("Imagine Board", "directory_path", "") )
            self.layout.filter.setText( str(Krita.instance().readSetting("Imagine Board", "filter", "")) )

            # Dialog
            self.dialog.menu_directory.setCurrentText(          str(Krita.instance().readSetting("Imagine Board", "directory_file", "")) )
            self.dialog.menu_sort.setCurrentText(               str(Krita.instance().readSetting("Imagine Board", "sort", "")) )
            self.dialog.menu_slideshow_sequence.setCurrentText( str(Krita.instance().readSetting("Imagine Board", "slideshow_sequence", "")) )
            self.dialog.menu_grid_horz.setValue(                int(Krita.instance().readSetting("Imagine Board", "grid_u", "")) )
            self.dialog.menu_grid_vert.setValue(                int(Krita.instance().readSetting("Imagine Board", "grid_v", "")) )
            self.dialog.menu_function_operation.setCurrentText( str(Krita.instance().readSetting("Imagine Board", "function_operation", "")) )
            self.dialog.menu_function_number.setValue(          int(Krita.instance().readSetting("Imagine Board", "function_number", "")) )
            self.dialog.menu_function_path.setText(             str(Krita.instance().readSetting("Imagine Board", "function_path", "")) )
            # Time
            ms = float(Krita.instance().readSetting("Imagine Board", "slideshow_time", ""))
            tempo = QTime(0,0,0).addMSecs(ms)
            self.dialog.menu_slideshow_time.setTime(tempo)
            # Keywords
            keywords = str(Application.readSetting("Imagine Board", "function_string", "")).split(",")
            for k in keywords:
                if (k != "," and k != ""):
                    self.dialog.menu_function_list.addItem(k)
        except:
            try:QtCore.qWarning("IB load | error")
            except:pass

    #//
    #\\ Menu ###################################################################
    def Menu_Mode(self, mode):
        # prepare cycle
        self.Display_Shrink()
        self.AnimPanel_Shrink()
        # Preview
        if mode == 0:
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_preview.setMaximumHeight(16777215)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(0)
        # Grid
        if mode == 1:
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(16777215)
            self.layout.imagine_reference.setMaximumHeight(0)
        # Reference
        if mode == 2:
            self.layout.imagine_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_grid.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.layout.imagine_reference.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.layout.imagine_preview.setMaximumHeight(0)
            self.layout.imagine_grid.setMaximumHeight(0)
            self.layout.imagine_reference.setMaximumHeight(16777215)
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

    def Menu_Grid(self):
        # Grid
        self.grid_horz = int(self.dialog.menu_grid_horz.value())
        self.grid_vert = int(self.dialog.menu_grid_vert.value())
        self.grid_table = self.grid_horz * self.grid_vert
        self.imagine_grid.Set_Grid(self.grid_horz, self.grid_vert)
        # Display
        self.Thumbnail_Size()
        self.Display_Update()
        # Save
        Krita.instance().writeSetting("Imagine Board", "grid_u", str( self.grid_horz ))
        Krita.instance().writeSetting("Imagine Board", "grid_v", str( self.grid_vert ))
    def Menu_Display(self, display):
        self.imagine_grid.Set_Display(display)
        self.update()

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
        if operation == "key_echo":
            text = "KEY ECHO"
        if operation == "key_populate":
            text = "KEY POPULATE"
        if operation == "rename_order":
            text = "RENAME ORDER (s, n)"
        if operation == "rename_random":
            text = "RENAME RANDOM (s)"
        if operation == "save_order":
            text = "SAVE ORDER (s, n)"
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
            self.thumbnail = int(rw)
        else:
            self.thumbnail = int(rh)
        if (self.grid_table >= 10 and self.thumbnail >= 200):
            self.thumbnail = 200

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
    def Folder_Load(self, load):
        self.imagine_preview.Set_Directory(load)
        self.directory_watcher.addPath(load)
        self.layout.folder.setToolTip("Dir : " + os.path.basename(load))
        self.Filter_Keywords(True)
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
                        fn = files[i].fileName()  # File Path
                        fp = files[i].filePath()  # File Path
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
        # Display list in a build up fashion as you scroll through images
        if self.menu_mode == 0:
            load = self.cache_load
        elif self.menu_mode == 1:
            load = self.grid_table + (self.grid_horz * self.cache_load)
        else:
            load = 0

        # Images to Display
        self.Display_Sync()
        self.Display_Cache(load, load, self.cache_clean, self.cache_clean)
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
    def Display_Cache(self, load_left, load_right, clean_left, clean_right):
        if self.images_found == True:
            # Calculate ranges dynamically
            ll = self.Math_1D_Limit(self.preview_index - load_left, 0, self.preview_max)
            lr = self.Math_1D_Limit(self.preview_index + load_right, 0, self.preview_max)
            cl = self.Math_1D_Limit(self.preview_index - clean_left, 0, self.preview_max)
            cr = self.Math_1D_Limit(self.preview_index + clean_right, 0, self.preview_max)
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
                    self.imagine_preview.Set_QPixmap_Preview(self.default_path)
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

        # Dynamic Range
        left = self.line_grid * self.grid_horz
        right = (self.line_grid + self.grid_vert) * self.grid_horz
        max = self.dialog.menu_grid_horz.maximum() * self.dialog.menu_grid_vert.maximum()
        delta = int(self.Math_1D_Lerp(self.grid_table/max , self.cache_load, self.cache_thread))
        ll = self.Math_1D_Limit(left - delta, 0, self.preview_max)
        lr = self.Math_1D_Limit(right + delta, 0, self.preview_max)

        # Display
        self.placeholder_text = self.layout.filter.placeholderText()
        self.layout.filter.setPlaceholderText("Loading")

        # Start Threads operations
        self.thread_thumbnails = Thread_Thumbnails()
        self.thread_thumbnails.SIGNAL_IMAGE['QPixmap'].connect(self.Thumbnail_Image)
        self.thread_thumbnails.SIGNAL_RESET.connect(self.Thumbnail_Reset)
        self.thread_thumbnails.Variables(os.path.basename(self.directory_path), self.found_path, self.preview_max, ll, lr)
        self.thread_thumbnails.start()
    def Thumbnail_Image(self, SIGNAL_IMAGE):
        # Recieve Image
        if SIGNAL_IMAGE.isNull() == False:
            qpixmap = SIGNAL_IMAGE.scaled(self.thumbnail, self.thumbnail, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
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
        if SIGNAL_PIN not in self.list_references:
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

    def Preview_SlideShow_Switch(self, SIGNAL_SLIDESHOW):
        if SIGNAL_SLIDESHOW == True:
            self.layout.thread.setEnabled(False)
            self.layout.progress_bar.setMaximumHeight(0)
            self.layout.slider.setMaximumHeight(0)
            self.layout.slideshow.setIcon(Krita.instance().icon('media-playback-stop'))
            self.layout.slideshow.setToolTip("SlideShow Stop")
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
            if SIGNAL_PIN not in self.list_references:
                self.Reference_Add(self.found_path[num])
    def Grid_Name(self, SIGNAL_NAME):
        num = self.grid_to_prev(self.line_grid, self.grid_horz, SIGNAL_NAME[0], SIGNAL_NAME[1])
        if (self.images_found == True and num < self.preview_max):
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
        self.list_references.append(str(path))
        self.imagine_reference.Add_Pin(path)
        QtCore.qDebug(str(self.list_references))

    def Reference_Render(self):
        pass
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

        if len(paths) > 0:
            # Sort Files and Folders
            files = []
            folders = []
            for i in range(0, len(paths)):
                if os.path.isfile(paths[i]) == True:
                    files.append(paths[i])
                if os.path.isdir(paths[i]) == True:
                    folders.append(paths[i])

            # File Watcher
            self.Filter_State(False)
            self.Function_Enabled(False)
            # Thread
            self.thread_function.Variables(operation, strings, number, files, folders, self.directory_path)
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
    found_qpixmap = qpixmap#.scaled(self.thumbnail, self.thumbnail, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
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
    def Variables(self, folder, path, items, ll, lr):
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
    def Variables(self, operation, strings, number, files, folders, directory):
        self.Variables_Reset()
        self.operation = operation
        self.strings = strings
        self.number = number
        self.files = files
        self.folders = folders
        self.directory = directory

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
                elif self.operation == "key_echo":
                    self.File_Echo(total, path)
                elif self.operation == "key_populate":
                    self.File_Populate(total, path)
                elif self.operation == "save_order":
                    self.File_Save(total, path, self.strings, self.number, self.directory)
            elif total_fil > 0: # Files
                # Construct
                if self.operation in rename:
                    self.File_Cycle(total_fil, self.files, self.strings, self.number)
                elif self.operation == "key_echo":
                    self.File_Echo(total_fil, self.files)
                elif self.operation == "key_populate":
                    self.File_Populate(total_fil, self.files)
                elif self.operation == "save_order":
                    self.File_Save(total_fil, self.files, self.strings, self.number, self.directory)

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
            path_i = path[i]
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
                try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " >> " + str(os.path.basename(path_new)))
                except:pass
                self.qfile.rename(path_i, path_new)
    def File_Echo(self, total, path):
        ver_total = self.verify_total(total)
        self.SIGNAL_PBAR_MAX.emit(ver_total)
        echo = 0
        count = 0
        replicas = []
        for i in range(0, total):
            path_i = path[i]
            qimage = QImage(path_i)
            for r in range(i+1, total):
                path_r = path[r]
                count += 1
                self.SIGNAL_STRING.emit(str(echo) + " : " + str(count+1) + " : " + str(ver_total+1))
                self.SIGNAL_PBAR_VALUE.emit(count+1)
                if path_r not in replicas:
                    if qimage == QImage(path_r):
                        echo += 1
                        replicas.append(path_r)
                        path_new = self.String_Echo(path_r)
                        if path_r != path_new:
                            try:QtCore.qDebug("IB rename | " + str(os.path.basename(path_i)) + " : " + str(os.path.basename(path_r)) + " >> " + str(os.path.basename(path_new)))
                            except:pass
                            self.qfile.rename(path_r, path_new)
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
            path_i = path[i]
            path_new = os.path.normpath( self.String_Save(directory, name[0]) )
            check = os.path.exists(path_new)
            if check == False:
                qimage = QImage(path_i)
                qimage.save(path_new)
                try:QtCore.qDebug("IB save | " + str(path_new))
                except:pass

    def verify_total(self, value):
        mat = value * value
        count = int((mat - value) / 2)
        return count

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
        return path_new
    def String_Echo(self, path):
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
        text = "echo"
        if self.OS == "winnt":
            base_new = name + " [ " + text + " ]" + extension
        else:
            base_new = name + " [ " + text + " ]"
        path_new = os.path.join(directory, base_new)
        # Return
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

    #//
