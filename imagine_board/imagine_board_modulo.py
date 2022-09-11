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

#\\ Imports ####################################################################
# Python
import math
import os
import zipfile
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from .imagine_board_calculations import *
#//
#\\ Global Variables ###########################################################
file_compress = [
    "zip",
    ]
#//


#\\ Panels #####################################################################
def krita_theme(self):
    theme = QApplication.palette().color(QPalette.Window).value()
    if theme > 128:
        self.color1 = QColor("#191919")
        self.color2 = QColor("#e5e5e5")
    else:
        self.color1 = QColor("#e5e5e5")
        self.color2 = QColor("#191919")
    self.color_hover = QColor(0,0,0,150)
    self.color_free = QColor(0,0,0,50)
    self.color_blue = QColor("#3daee9")
    self.color_inactive = QColor(40,4,4,150)
    self.color_ib = QColor(0, 0, 100, 20)
def event_drop(self, event):
    # Mimedata
    mimedata = event.mimeData()
    # Has Boolean
    has_text = mimedata.hasText()
    has_html = mimedata.hasHtml()
    has_urls = mimedata.hasUrls()
    # has_image = mimedata.hasImage()
    # has_color = mimedata.hasColor()
    # Data
    data_text = mimedata.text()
    data_html = mimedata.html()
    data_urls = mimedata.urls()
    # data_image = QPixmap().fromImage(mimedata.imageData())
    # data_color = QColor(mimedata.colorData())

    # Construct Mime Data
    mime_data = []
    len_urls = len(data_urls)
    if has_html == True:
        # Construct BaseName
        for i in range(-1, -len(data_text), -1):
            text_i = data_text.split("/")[i]
            if text_i != "":
                break
        if "." in text_i:
            text_i = text_i.split(".")[0]
        text_i = text_i + ".png" # overides default BMP format
        # Construct Path
        urls_i = os.path.normpath(data_urls[0].toLocalFile()) # Local File
        mime_data.append([text_i, urls_i])
    else:
        # Variables
        text_list = data_text.split("file:///")[1:]
        for i in range(0, len(text_list)):
            if text_list[i].endswith("\n"):
                text_list[i] = text_list[i][:-1]
        # Construct
        for i in range(0, len_urls):
            text_i = os.path.basename(text_list[i]) # Local Basename
            urls_i = os.path.normpath(data_urls[i].toLocalFile()) # Local File
            mime_data.append([text_i, urls_i])
        mime_data.sort()
    return mime_data
def insert_bool(self):
    doc = Krita.instance().documents()
    if len(doc) != 0:
        insert = True
    else:
        insert = False
    return insert

class ImagineBoard_Preview(QWidget):
    # General
    SIGNAL_CLICK = QtCore.pyqtSignal(int)
    SIGNAL_WHEEL = QtCore.pyqtSignal(int)
    SIGNAL_STYLUS = QtCore.pyqtSignal(int)
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    SIGNAL_NEUTRAL = QtCore.pyqtSignal(str)
    # Preview
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    SIGNAL_FRAME = QtCore.pyqtSignal(str)
    SIGNAL_FUNCTION = QtCore.pyqtSignal(list)
    SIGNAL_PIN_PATH = QtCore.pyqtSignal(str)
    SIGNAL_RANDOM = QtCore.pyqtSignal(int)
    SIGNAL_LOCATION = QtCore.pyqtSignal(str)
    SIGNAL_COLOR = QtCore.pyqtSignal(dict)
    SIGNAL_CLIP = QtCore.pyqtSignal(list)
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal(str)
    SIGNAL_ANIM_PANEL = QtCore.pyqtSignal(bool)
    SIGNAL_COMP = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(ImagineBoard_Preview, self).__init__(parent)
        # Display
        self.number = 0
        self.active = True
        self.expand = False
        self.label = None
        self.press = False
        self.operation = ""
        self.is_null = True
        # Size
        self.widget_width = 0
        self.widget_height = 0
        self.wt2 = 0
        self.ht2 = 0
        # Image
        self.size = 0
        self.scaled_width = 1
        self.scaled_height = 1
        self.offset_x = 0
        self.offset_y = 0
        self.var_w = 1
        self.var_h = 1
        self.width_per = 0
        self.height_per = 0
        self.image_width = 1
        self.image_height = 1
        # Events
        self.origin_x = 0
        self.origin_y = 0
        self.stylus_x = 0
        self.stylus_y = 0
        self.zoom = 1
        self.focus_x = 0.5
        self.focus_y = 0.5
        # Clip
        self.clip_state = False
        self.clip_p1_per = [0.1, 0.1] # range : 0-1
        self.clip_p2_per = [0.9, 0.1] # range : 0-1
        self.clip_p3_per = [0.9, 0.9] # range : 0-1
        self.clip_p4_per = [0.1, 0.9] # range : 0-1
        self.clip_p1_img = [0, 0]
        self.clip_p2_img = [0, 0]
        self.clip_p3_img = [0, 0]
        self.clip_p4_img = [0, 0]
        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
        # Color Picker
        self.pigmento = False
        self.pick_color = False
        self.red = 0
        self.green = 0
        self.blue = 0
        self.range = 255
        # Edit
        self.edit_greyscale = False
        self.edit_invert_h = False
        self.edit_invert_v = False
        # Animation
        self.directory = ""
        self.is_animation = False
        self.frame_count = 0
        self.anim_rate = 33
        self.Set_Anim_Timer()
        # Compressed
        self.is_compressed = False
        self.archive = None
        self.name_list = []
        self.comp_index = 0

        # Startup
        self.Set_Default()
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Pigmento(self, bool):
        self.pigmento = bool
    def Set_Reset(self):
        self.Preview_Reset(True)
        self.Clip_Off()
    def Set_Anim_Timer(self):
        self.anim_timer = QtCore.QTimer(self)
        self.anim_timer.timeout.connect(self.Anim_Frame)
        self.anim_timer.stop()
    def Set_Expand(self, expand):
        self.expand = expand
        self.update()
    def Set_Size(self, widget_width, widget_height):
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.wt2 = widget_width * 0.5
        self.ht2 = widget_height * 0.5
    def Set_Directory(self, directory):
        self.directory = directory
    def Set_DropDot(self, boolean):
        self.drop = boolean
    def Set_Operation(self, operation):
        self.operation = operation
        self.update()
    def Set_Color_Display(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue
        self.update()

    # Input Display
    def Set_Default(self):
        self.is_null = True
        self.path = ""
        self.qpixmap = QPixmap()
        self.anim_sequence = [self.qpixmap]
        self.frame_value = 0
        self.update()
    def Set_Default_Preview(self, path):
        # Reset
        self.Set_Reset()
        self.is_null = False
        # Image
        self.path = path
        self.qpixmap = QPixmap()
        self.update()
    def Set_QPixmap_Preview(self, path):
        # Reset
        self.Set_Reset()
        self.is_null = False
        # Image
        self.path = path
        self.qpixmap = QPixmap(path)
        self.update()
    def Set_Anim_Preview(self, path, playpause):
        # Reset
        self.Set_Reset()
        self.is_null = False
        # Image Qmovie
        self.path = path
        qmovie = QMovie(path)
        if qmovie.isValid() == True:
            # Frames
            frames = qmovie.frameCount()
            speed = qmovie.speed() / 100
            anim_rate = []
            sequence = []
            for i in range(0, frames):
                qmovie.jumpToFrame(i)
                delay = qmovie.nextFrameDelay()
                anim_rate.append(delay)
                qpixmap = qmovie.currentPixmap()
                if qpixmap.isNull() == False:
                    sequence.append(qpixmap)
            mean = Stat_Mean(anim_rate)
            # Open Animation
            if frames == 1:
                boolean = False
            else:
                boolean = True
            self.is_animation = boolean
            self.SIGNAL_ANIM_PANEL.emit(boolean)
            # Set Values
            self.anim_sequence = sequence
            self.frame_count = frames - 1
            self.anim_rate = mean * speed
            # Play Animation
            qmovie.deleteLater()
            self.Anim_Play()
            self.update()
    def Set_Comp_Preview(self, path, name_list):
        # Reset
        self.Set_Reset()
        self.is_null = False
        # Variables
        self.path = path

        try:
            # Variables
            self.is_compressed = True
            self.name_list = name_list
            self.comp_index = 0

            # Zip File
            self.archive = zipfile.ZipFile(path, "r")
            self.qpixmap = self.Comp_QPixmap(self.archive, self.name_list, self.comp_index)
        except:
            pass
        self.update()

    # Animation
    def Anim_Frame(self):
        if self.is_animation == True:
            self.frame_value = Limit_Loop(self.frame_value + 1, self.frame_count)
            self.update()
    def Anim_Pause(self):
        if self.is_animation == True:
            self.anim_timer.stop()
            self.Anim_Logger(str(self.frame_value) + ":" + str(self.frame_count))
            self.update()
    def Anim_Play(self):
        if self.is_animation == True:
            self.anim_timer.start(self.anim_rate)
            self.Anim_Logger("")
            self.update()
    def Anim_Frame_Back(self):
        check = self.anim_timer.isActive()
        if (self.is_animation == True and check == False):
            self.frame_value = Limit_Loop(self.frame_value - 1, self.frame_count)
            self.Anim_Logger(str(self.frame_value) + ":" + str(self.frame_count))
            self.update()
    def Anim_Frame_Forward(self):
        check = self.anim_timer.isActive()
        if (self.is_animation == True and check == False):
            self.frame_value = Limit_Loop(self.frame_value + 1, self.frame_count)
            self.Anim_Logger(str(self.frame_value) + ":" + str(self.frame_count))
            self.update()
    def Anim_Logger(self, string):
        self.SIGNAL_FRAME.emit(string)
    def Anim_Screenshot(self):
        check = self.anim_timer.isActive()
        if (self.is_animation == True and check == False):
            self.Anim_Frame_Save(self.frame_value)
    def Anim_Export_Frames(self):
        for i in range(0, len(self.anim_sequence)):
            self.Anim_Frame_Save(i)
    def Anim_Frame_Save(self, frame):
        # Construct New Path
        directory = os.path.dirname(self.path) # dir
        bn = os.path.basename(self.path) # name.ext
        extension = os.path.splitext(self.path)[1] # .ext
        n = bn.find(extension)
        base = bn[:n] # name
        base_new = base + "_" + str(frame).zfill(4) + ".png"
        save_path = os.path.normpath( os.path.join(directory, base_new) )
        # Save File
        screenshot_qpixmap = self.anim_sequence[frame]
        screenshot_qpixmap.save(save_path)
        # Logger
        try:QtCore.qDebug("IB Screenshot | " + str(self.frame_value) + ":" + str(self.frame_count))
        except:pass

    # Compressed
    def Comp_Frame(self, comp_index):
        if self.archive != None:
            self.comp_index = Limit_Range(comp_index, 0, len(self.name_list))
            self.qpixmap = self.Comp_QPixmap(self.archive, self.name_list, self.comp_index)
            self.update()
    def Comp_QPixmap(self, archive, name_list, index):
        # GIF's inside a ZIP will become static images
        display = QPixmap()
        try:
            archive_open = archive.open(name_list[index])
            archive_read = archive_open.read()
            qimage = QImage()
            qimage.loadFromData(archive_read)
            qpixmap = QPixmap().fromImage(qimage)
            if qpixmap.isNull() == False:
                display = qpixmap
        except:
            pass
        return display

    # Preview Calculations
    def Preview_Reset(self, reset):
        # Camera
        self.zoom = 1
        self.focus_x = 0.5
        self.focus_y = 0.5
        # Animation
        if reset == True:
            self.is_animation = False
            self.frame_value = 0
            self.anim_timer.stop()
        check = self.anim_timer.isActive()
        if (self.is_animation == True and check == False):
            self.Anim_Logger(str(self.frame_value) + ":" + str(self.frame_count))
        # Compressed
        self.is_compressed = False
        # Edit
        self.edit_greyscale = False
        self.edit_invert_h = False
        self.edit_invert_v = False
        # Update
        self.update()
    def Preview_Position(self, event):
        self.focus_x = 1 - (event.x() / self.widget_width)
        self.focus_y = 1 - (event.y() / self.widget_height)
        self.update()
    def Preview_Zoom(self, event):
        delta = 2
        dist_x = (event.x() - self.origin_x) / delta
        dist_y = (event.y() - self.origin_y) / delta
        if abs(dist_x) >= abs(dist_y):
            dist = dist_x
        else:
            dist = dist_y
        if dist <= -1:
            self.zoom += 0.03
            self.origin_x = event.x()
            self.origin_y = event.y()
        if dist >= 1:
            self.zoom -= 0.03
            self.origin_x = event.x()
            self.origin_y = event.y()
        self.update()
    def Preview_Edit(self, operation):
        # Operations Boolean Toggle
        if operation == "egs":
            self.edit_greyscale = not self.edit_greyscale
        if operation == "efx":
            self.edit_invert_h = not self.edit_invert_h
        if operation == "efy":
            self.edit_invert_v = not self.edit_invert_v

        # Edit Image
        qimage = QImage(self.path)
        if self.edit_greyscale == True:
            qimage = qimage.convertToFormat(24)
        if (self.edit_invert_h == True or self.edit_invert_v == True):
            qimage = qimage.mirrored(self.edit_invert_h, self.edit_invert_v)
        self.qpixmap = QPixmap().fromImage(qimage)
        self.update()

    # Clip Calculations
    def Clip_Off(self):
        self.clip_state = False
        self.SIGNAL_CLIP.emit([False,0,0,self.image_width,self.image_height])
    def Clip_Switch(self):
        self.clip_state = not self.clip_state
    def Clip_Default(self):
        self.clip_p1_per = [0.1, 0.1]
        self.clip_p2_per = [0.9, 0.1]
        self.clip_p3_per = [0.9, 0.9]
        self.clip_p4_per = [0.1, 0.9]
    def Clip_Event(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            # Preview Fix
            self.Preview_Reset(False)
            # Point of event
            ex = event.x()
            ey = event.y()
            # Points in Widget Space
            self.clip_p1_img = [self.offset_x, self.offset_y]
            self.clip_p2_img = [self.offset_x + (self.scaled_width * self.zoom), self.offset_y]
            self.clip_p3_img = [self.offset_x + (self.scaled_width * self.zoom), self.offset_y + (self.scaled_height * self.zoom)]
            self.clip_p4_img = [self.offset_x, self.offset_y + (self.scaled_height * self.zoom)]
            relative = [ex - self.offset_x, ey - self.offset_y]
            width_img = self.clip_p2_img[0] - self.offset_x
            height_img = self.clip_p4_img[1] - self.offset_y
            per_x = Limit_Float(relative[0] / width_img)
            per_y = Limit_Float(relative[1] / height_img)
            # Distances
            dist1 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p1_per[0] * self.scaled_width),self.offset_y + (self.clip_p1_per[1] * self.scaled_height), ex,ey)
            dist2 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p2_per[0] * self.scaled_width),self.offset_y + (self.clip_p2_per[1] * self.scaled_height), ex,ey)
            dist3 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p3_per[0] * self.scaled_width),self.offset_y + (self.clip_p3_per[1] * self.scaled_height), ex,ey)
            dist4 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p4_per[0] * self.scaled_width),self.offset_y + (self.clip_p4_per[1] * self.scaled_height), ex,ey)
            # Shortest distance
            dist_min = min(dist1, dist2, dist3, dist4)
            if dist_min < 20:
                limit = 0.01
                if dist_min == dist1:
                    if per_x > (self.clip_p2_per[0] - limit):
                        per_x = self.clip_p2_per[0] - limit
                    if per_y > (self.clip_p4_per[1] - limit):
                        per_y = self.clip_p4_per[1] - limit
                    self.clip_p1_per = [per_x, per_y]
                    self.clip_p2_per[1] = per_y
                    self.clip_p4_per[0] = per_x
                if dist_min == dist2:
                    if per_x < (self.clip_p1_per[0] + limit):
                        per_x = self.clip_p1_per[0] + limit
                    if per_y > (self.clip_p3_per[1] - limit):
                        per_y = self.clip_p3_per[1] - limit
                    self.clip_p2_per = [per_x, per_y]
                    self.clip_p3_per[0] = per_x
                    self.clip_p1_per[1] = per_y
                if dist_min == dist3:
                    if per_x < (self.clip_p4_per[0] + limit):
                        per_x = self.clip_p4_per[0] + limit
                    if per_y < (self.clip_p2_per[1] + limit):
                        per_y = self.clip_p2_per[1] + limit
                    self.clip_p3_per = [per_x, per_y]
                    self.clip_p4_per[1] = per_y
                    self.clip_p2_per[0] = per_x
                if dist_min == dist4:
                    if per_x > (self.clip_p3_per[0] - limit):
                        per_x = self.clip_p3_per[0] - limit
                    if per_y < (self.clip_p1_per[1] + limit):
                        per_y = self.clip_p1_per[1] + limit
                    self.clip_p4_per = [per_x, per_y]
                    self.clip_p1_per[0] = per_x
                    self.clip_p3_per[1] = per_y
            # Width and Height
            self.width_per = self.clip_p2_per[0] - self.clip_p1_per[0]
            self.height_per = self.clip_p4_per[1] - self.clip_p1_per[1]
            # Lists
            if (self.edit_invert_h == False and self.edit_invert_v == False):
                point_x = self.clip_p1_per[0]
                point_y = self.clip_p1_per[1]
            if (self.edit_invert_h == True and self.edit_invert_v == False):
                point_x = self.clip_p2_per[0]
                point_y = self.clip_p2_per[1]
            if (self.edit_invert_h == False and self.edit_invert_v == True):
                point_x = self.clip_p3_per[0]
                point_y = self.clip_p3_per[1]
            if (self.edit_invert_h == True and self.edit_invert_v == True):
                point_x = self.clip_p4_per[0]
                point_y = self.clip_p4_per[1]
            list = [
                self.clip_state,
                point_x * self.image_width,
                point_y * self.image_height,
                self.width_per * self.image_width,
                self.height_per * self.image_height
                ]
            self.SIGNAL_CLIP.emit(list)
            # Finish
            self.update()

    # Rotation
    def Rotate_Image(self, amount):
        # Reset
        self.Clip_Off()
        # Transform
        rot = QTransform().rotate(amount, Qt.ZAxis)
        self.qpixmap = self.qpixmap.transformed(rot)

        # Save
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Information)
        message_box.setText("Save file ?")
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        message_box.buttonClicked.connect(self.Rotate_Save)
        message_box.exec_()

        # Update
        self.update()
    def Rotate_Save(self, SIGNAL):
        if SIGNAL.text() == "&OK":
            self.qpixmap.save(self.path)

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        self.stylus_x = event.x()
        self.stylus_y = event.y()

        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            if self.pick_color == True:
                self.Color_Apply(event)
            else:
                self.SIGNAL_NEUTRAL.emit(os.path.basename(self.path))

        # Camera
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            if event.buttons() == QtCore.Qt.LeftButton: # Pan
                self.Preview_Position(event)
            if event.buttons() == QtCore.Qt.RightButton: #Zoom
                self.Preview_Zoom(event)
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton):
            self.Preview_Position(event)
        # Pagination
        if (event.modifiers() == QtCore.Qt.ControlModifier and (event.buttons() == QtCore.Qt.LeftButton or event.buttons() == QtCore.Qt.RightButton)):
            self.Preview_Reset(False)
            self.Clip_Off()
            self.Pagination_Flip(event)
        if (event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier) and (event.buttons() == QtCore.Qt.LeftButton or event.buttons() == QtCore.Qt.RightButton)):
            pass
        # Drag and Drop
        if (event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
            pass

        # Context
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
            self.Context_Menu(event)

        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseMoveEvent(self, event):
        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            if self.pick_color == True:
                self.Color_Apply(event)
            else:
                self.SIGNAL_NEUTRAL.emit(os.path.basename(self.path))

        # Camera
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            if event.buttons() == QtCore.Qt.LeftButton: # Pan
                self.Preview_Position(event)
            if event.buttons() == QtCore.Qt.RightButton: # Zoom
                self.Preview_Zoom(event)
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton):
            self.Preview_Position(event)
        # Pagination
        if (event.modifiers() == QtCore.Qt.ControlModifier and (event.buttons() == QtCore.Qt.LeftButton or event.buttons() == QtCore.Qt.RightButton)):
            self.Pagination_Stylus(event)
        if (event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier) and (event.buttons() == QtCore.Qt.LeftButton or event.buttons() == QtCore.Qt.RightButton)):
            self.Pagination_Comp(event)
        # Drag and Drop
        if (event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.SIGNAL_DRAG.emit(self.path)

        # Context
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
            pass

        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseDoubleClickEvent(self, event):
        # Neutral
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_MODE.emit(1)
    def mouseReleaseEvent(self, event):
        self.SIGNAL_NEUTRAL.emit("")
        self.origin_x = 0
        self.origin_y = 0
        self.press = False
        self.drop = False
        self.update()

    def Pagination_Flip(self, event):
        top = 0.1 * self.widget_height
        bot = 0.9 * self.widget_height
        if self.origin_y <= top:
            self.press = True
            self.SIGNAL_CLICK.emit(1)
        elif self.origin_y >= bot:
            self.press = True
            self.SIGNAL_CLICK.emit(-1)
    def Pagination_Stylus(self, event):
        delta = 40
        dist_x = (event.x() - self.stylus_x) / delta
        dist_y = -((event.y() - self.stylus_y) / delta)
        if abs(dist_x) >= abs(dist_y):
            dist = dist_x
        else:
            dist = dist_y
        if dist <= -1:
            self.press = False
            self.SIGNAL_STYLUS.emit(-1)
            self.stylus_x = event.x()
            self.stylus_y = event.y()
        if dist >= 1:
            self.press = False
            self.SIGNAL_STYLUS.emit(1)
            self.stylus_x = event.x()
            self.stylus_y = event.y()
    def Pagination_Comp(self, event):
        delta = 40
        dist_x = (event.x() - self.stylus_x) / delta
        dist_y = -((event.y() - self.stylus_y) / delta)
        if abs(dist_x) >= abs(dist_y):
            dist = dist_x
        else:
            dist = dist_y
        if dist <= -1:
            self.press = False
            self.SIGNAL_COMP.emit(-1)
            self.stylus_x = event.x()
            self.stylus_y = event.y()
        if dist >= 1:
            self.press = False
            self.SIGNAL_COMP.emit(1)
            self.stylus_x = event.x()
            self.stylus_y = event.y()
    def Color_Apply(self, event):
        # Geometry
        tl = QPoint(0, 0)
        br = QPoint(self.width(), self.height() )
        pixmap = self.grab(QRect(tl, br))
        image = pixmap.toImage()
        ex = event.x()
        ey = event.y()
        color = image.pixelColor(ex , ey)
        # Apply Color Values
        red = color.red()
        green = color.green()
        blue = color.blue()
        dictionary = {"red":red/255, "green":green/255, "blue":blue/255}
        # Emit
        self.SIGNAL_COLOR.emit(dictionary)
        self.SIGNAL_NEUTRAL.emit( "R:" + str(int(red)) + " G:" + str(int(green)) + " B:" + str(int(blue)) )
        # Update
        self.update()
    def Context_Menu(self, event):
        # variables
        insert = insert_bool(self)
        is_animation = self.is_animation # Changes to self.is_animation do not affect menu on the if stack
        is_compressed = self.is_compressed
        # Menu
        cmenu = QMenu(self)
        # Actions
        if is_compressed == False:
            cmenu_function = cmenu.addAction("Function >>" + self.operation)
            cmenu_pin = cmenu.addAction("Pin Reference")
            cmenu.addSeparator()
        cmenu_random = cmenu.addAction("Random")
        cmenu_location = cmenu.addAction("Location")
        cmenu_copy = cmenu.addMenu("Copy")
        cmenu_copy_file = cmenu_copy.addAction("File Name")
        cmenu_copy_directory = cmenu_copy.addAction("Path Directory")
        cmenu_copy_path = cmenu_copy.addAction("Path Full")
        cmenu.addSeparator()
        # Color Picker
        if self.pigmento == True:
            cmenu_pick_color = cmenu.addAction("Pick Color")
        else:
            cmenu_pick_color = cmenu.addAction("Pick Color [OFF]")
        cmenu_pick_color.setCheckable(True)
        cmenu_pick_color.setChecked(self.pick_color)
        cmenu.addSeparator()
        if is_animation == True:
            cmenu_export_current_frame = cmenu.addAction("Export Current Frame")
            cmenu_export_all_frames = cmenu.addAction("Export All Frames")
        elif is_compressed == True:
            pass
        else:
            # Greyscale
            cmenu_edit_greyscale = cmenu.addAction("View Greyscale")
            cmenu_edit_greyscale.setCheckable(True)
            cmenu_edit_greyscale.setChecked(self.edit_greyscale)
            # Flips
            cmenu_edit_invert_h = cmenu.addAction("Flip Horizontal")
            cmenu_edit_invert_h.setCheckable(True)
            cmenu_edit_invert_h.setChecked(self.edit_invert_h)
            cmenu_edit_invert_v = cmenu.addAction("Flip Vertical")
            cmenu_edit_invert_v.setCheckable(True)
            cmenu_edit_invert_v.setChecked(self.edit_invert_v)
            # Clip
            cmenu_clip = cmenu.addAction("Clip Image")
            cmenu_clip.setCheckable(True)
            cmenu_clip.setChecked(self.clip_state)
            # Rotate
            cmenu_rotate = cmenu.addMenu("Rotate Image")
            cmenu_rot_left = cmenu_rotate.addAction("Rotate Left")
            cmenu_rot_right = cmenu_rotate.addAction("Rotate Right")
            cmenu_rot_flip = cmenu_rotate.addAction("Rotate Flip")
        cmenu.addSeparator()
        # Document
        cmenu_document = cmenu.addAction("New Document")
        # Inserts
        if insert == True:
            cmenu_insert_layer = cmenu.addAction("Insert Layer")
            cmenu_insert_ref = cmenu.addAction("Insert Reference")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))
        # Triggers
        if is_compressed == False:
            if action == cmenu_function:
                name = os.path.basename(self.path)
                path = os.path.normpath(self.path)
                name_path = [[name, path]]
                self.SIGNAL_FUNCTION.emit(name_path)
            if action == cmenu_pin:
                self.SIGNAL_PIN_PATH.emit(self.path)
        if action == cmenu_random:
            self.Preview_Reset(True)
            self.Clip_Off()
            self.SIGNAL_RANDOM.emit(0)
        if action == cmenu_location:
            self.SIGNAL_LOCATION.emit(self.path)
        if action == cmenu_copy_file:
            copy = QApplication.clipboard()
            copy.clear()
            copy.setText(os.path.basename(self.path))
        if action == cmenu_copy_directory:
            copy = QApplication.clipboard()
            copy.clear()
            copy.setText(os.path.normpath(os.path.dirname(self.path)))
        if action == cmenu_copy_path:
            copy = QApplication.clipboard()
            copy.clear()
            copy.setText(os.path.normpath(self.path))
        if action == cmenu_pick_color:
            self.pick_color = not self.pick_color
        if is_animation == True:
            if action == cmenu_export_current_frame:
                self.Anim_Frame_Save(self.frame_value)
            if action == cmenu_export_all_frames:
                self.Anim_Export_Frames()
        elif is_compressed == True:
            pass
        else:
            if action == cmenu_edit_greyscale:
                if self.clip_state == False:
                    self.Preview_Edit("egs")
            if action == cmenu_edit_invert_h:
                if self.clip_state == False:
                    self.Preview_Edit("efx")
            if action == cmenu_edit_invert_v:
                if self.clip_state == False:
                    self.Preview_Edit("efy")
            if action == cmenu_clip:
                self.Preview_Reset(False)
                self.Preview_Edit(None)
                self.Clip_Switch()
                if self.clip_state == True:
                    self.Clip_Default()
                    list = [
                        self.clip_state,
                        self.clip_p1_per[0] * self.image_width,
                        self.clip_p1_per[1] * self.image_height,
                        self.width_per * self.image_width,
                        self.height_per * self.image_height
                        ]
                    self.SIGNAL_CLIP.emit(list)
                else:
                    self.SIGNAL_CLIP.emit([False,0,0,self.image_width,self.image_height])
            if action == cmenu_rot_left:
                self.Rotate_Image(-90)
            if action == cmenu_rot_right:
                self.Rotate_Image(90)
            if action == cmenu_rot_flip:
                self.Rotate_Image(180)
        if action == cmenu_document:
            self.SIGNAL_NEW_DOCUMENT.emit(self.path)
        if insert == True:
            try:
                if action == cmenu_insert_layer:
                    self.SIGNAL_INSERT_LAYER.emit(self.path)
                if action == cmenu_insert_ref:
                    self.SIGNAL_INSERT_REFERENCE.emit(self.path)
            except:
                pass

    # Wheel Events
    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        angle = 5
        # Zoom
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            self.Wheel_Zoom(event, delta_y, angle)
        # Change Index
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Wheel_Index(event, delta_y, angle)
        # Change Compressed Index
        if (event.modifiers() == QtCore.Qt.ControlModifier or event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)):
            self.Wheel_Comp(event, delta_y, angle)
    def Wheel_Zoom(self, event, delta_y, angle):
        if delta_y >= angle:
            self.zoom += 0.1
        if delta_y <= -angle:
            self.zoom -= 0.1
        self.update()
    def Wheel_Index(self, event, delta_y, angle):
        if delta_y >= angle:
            self.SIGNAL_WHEEL.emit(+1)
        if delta_y <= -angle:
            self.SIGNAL_WHEEL.emit(-1)
    def Wheel_Comp(self, event, delta_y, angle):
        if delta_y >= angle:
            self.SIGNAL_COMP.emit(+1)
        if delta_y <= -angle:
            self.SIGNAL_COMP.emit(-1)

    # Drag and Drop Event
    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent(self, event):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = False
            event.setDropAction(Qt.CopyAction)
            mime_paths = []
            if (self.origin_x == 0 and self.origin_y == 0): # Denys from recieving from self.
                mime_data = event_drop(self, event)
                self.SIGNAL_FUNCTION.emit(mime_data)
            event.accept()
        else:
            event.ignore()
        self.update()

    # Painter
    def paintEvent(self, event):
        # Theme
        krita_theme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Display Pixmap
        if (self.is_null == True or (self.qpixmap.isNull() == True and self.is_animation == False and self.drop == False)):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color1)))
            if self.widget_width < self.widget_height:
                side = self.widget_width
            else:
                side = self.widget_height
            w2 = self.widget_width * 0.5
            h2 = self.widget_height * 0.5
            painter.drawEllipse(w2 - (0.2*side), h2 - (0.2*side), 0.4*side, 0.4*side)
        else:
            self.Image_Calculations()
            painter.save()
            painter.translate(self.offset_x, self.offset_y)
            painter.scale(self.size * self.zoom, self.size * self.zoom)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtCore.Qt.NoBrush)
            if self.is_animation == True:
                painter.drawPixmap(0,0,self.anim_sequence[self.frame_value])
            else:
                painter.drawPixmap(0,0,self.qpixmap)
            # Clip Area
            if self.clip_state == True:
                # Area to hide
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color_hover)))
                area = QPainterPath()
                area.moveTo(0,0)
                area.lineTo(self.image_width, 0)
                area.lineTo(self.image_width, self.image_height)
                area.lineTo(0, self.image_height)
                area.moveTo(self.clip_p1_per[0] * self.image_width, self.clip_p1_per[1] * self.image_height)
                area.lineTo(self.clip_p2_per[0] * self.image_width, self.clip_p2_per[1] * self.image_height)
                area.lineTo(self.clip_p3_per[0] * self.image_width, self.clip_p3_per[1] * self.image_height)
                area.lineTo(self.clip_p4_per[0] * self.image_width, self.clip_p4_per[1] * self.image_height)
                painter.drawPath(area)
                # Points
                painter.setPen(QPen(self.color2, 2, Qt.SolidLine))
                painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                tri = 15
                poly1 = QPolygon([
                    QPoint((self.image_width * self.clip_p1_per[0]), (self.image_height * self.clip_p1_per[1])),
                    QPoint((self.image_width * self.clip_p1_per[0]) + tri, (self.image_height * self.clip_p1_per[1])),
                    QPoint((self.image_width * self.clip_p1_per[0]), (self.image_height * self.clip_p1_per[1]) + tri),
                    ])
                poly2 = QPolygon([
                    QPoint((self.image_width * self.clip_p2_per[0]), (self.image_height * self.clip_p2_per[1])),
                    QPoint((self.image_width * self.clip_p2_per[0]), (self.image_height * self.clip_p2_per[1]) + tri),
                    QPoint((self.image_width * self.clip_p2_per[0]) - tri, (self.image_height * self.clip_p2_per[1])),
                    ])
                poly3 = QPolygon([
                    QPoint((self.image_width * self.clip_p3_per[0]), (self.image_height * self.clip_p3_per[1])),
                    QPoint((self.image_width * self.clip_p3_per[0]) - tri, (self.image_height * self.clip_p3_per[1])),
                    QPoint((self.image_width * self.clip_p3_per[0]), (self.image_height * self.clip_p3_per[1]) - tri),
                    ])
                poly4 = QPolygon([
                    QPoint((self.image_width * self.clip_p4_per[0]), (self.image_height * self.clip_p4_per[1])),
                    QPoint((self.image_width * self.clip_p4_per[0]), (self.image_height * self.clip_p4_per[1]) - tri),
                    QPoint((self.image_width * self.clip_p4_per[0]) + tri, (self.image_height * self.clip_p4_per[1])),
                    ])
                painter.drawPolygon(poly1)
                painter.drawPolygon(poly2)
                painter.drawPolygon(poly3)
                painter.drawPolygon(poly4)
            # Restor Space
            painter.restore()

        # Arrows
        if self.press == True:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color1)))
            if self.origin_y < (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint(self.widget_width*0.50, self.widget_height*0.05),
                    QPoint(self.widget_width*0.45, self.widget_height*0.10),
                    QPoint(self.widget_width*0.55, self.widget_height*0.10)
                    ])
            elif self.origin_y > (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint(self.widget_width*0.50, self.widget_height*0.95),
                    QPoint(self.widget_width*0.45, self.widget_height*0.90),
                    QPoint(self.widget_width*0.55, self.widget_height*0.90)
                    ])
            painter.drawPolygon(arrow)

        # Drag and Drop
        if self.drop == True:
            check = (self.origin_x == 0 and self.origin_y == 0)
            if check == True:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color1)))
                if self.widget_width < self.widget_height:
                    side = self.widget_width
                else:
                    side = self.widget_height
                w2 = self.widget_width * 0.5
                h2 = self.widget_height * 0.5
                poly_tri = QPolygon([
                    QPoint(w2 - (0.3*side), h2 - (0.2*side)),
                    QPoint(w2 + (0.3*side), h2 - (0.2*side)),
                    QPoint(w2, h2 + (0.2*side)),
                    ])
                painter.drawPolygon(poly_tri)

        # Color Picker
        if (self.pick_color == True and self.origin_x != 0 and self.origin_y != 0):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.red*self.range, self.green*self.range, self.blue*self.range)))
            painter.drawRect(0,0,50,50)
    def Image_Calculations(self):
        # Calculations for Image
        if self.is_animation == True:
            self.image_width = self.anim_sequence[0].width()
            self.image_height = self.anim_sequence[0].height()
        else:
            self.image_width = self.qpixmap.width()
            self.image_height = self.qpixmap.height()
        if (self.image_width != 0 or self.image_height != 0):
            self.var_w = self.widget_width / self.image_width
            self.var_h = self.widget_height / self.image_height
        else:
            self.var_w = 1
            self.var_h = 1
        self.size = 0
        if self.expand == True:
            if self.var_w <= self.var_h:
                self.size = self.var_h
            if self.var_w > self.var_h:
                self.size = self.var_w
        else:
            if self.var_w <= self.var_h:
                self.size = self.var_w
            if self.var_w > self.var_h:
                self.size = self.var_h
        self.scaled_width = self.image_width * self.size
        self.scaled_height = self.image_height * self.size
        self.offset_x = self.wt2 - (self.scaled_width * self.focus_x * self.zoom)
        self.offset_y = self.ht2 - (self.scaled_height * self.focus_y * self.zoom)
        # Calculation for Movie
        self.movie_width = self.scaled_width - 25
        self.movie_height = self.scaled_height - 25

class ImagineBoard_Grid(QWidget):
    # General
    SIGNAL_CLICK = QtCore.pyqtSignal(int)
    SIGNAL_WHEEL = QtCore.pyqtSignal(int)
    SIGNAL_STYLUS = QtCore.pyqtSignal(int)
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    SIGNAL_NEUTRAL = QtCore.pyqtSignal(str)
    # Grid
    SIGNAL_PREVIEW = QtCore.pyqtSignal(list)
    SIGNAL_FUNCTION = QtCore.pyqtSignal(list)
    SIGNAL_PIN_PATH = QtCore.pyqtSignal(str)
    SIGNAL_NAME = QtCore.pyqtSignal(list)
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(ImagineBoard_Grid, self).__init__(parent)
        self.images_found = False
        self.widget_width = 1
        self.widget_height = 1
        self.origin_x = 0
        self.origin_y = 0
        self.stylus_x = 0
        self.stylus_y = 0
        self.default = QPixmap()
        self.grid_horz = 3
        self.grid_vert = 3
        self.line_grid = 0
        self.qpixmap_list = []
        self.press = False
        self.operation = ""
        # Thumbnail
        self.tn_fit_ratio = False
        self.Set_Fit_Ratio(self.tn_fit_ratio)
        self.tn_x = 256
        self.tn_y = 256
        self.tn_smooth_scale = Qt.FastTransformation
        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_QPixmaps(self, images_found, qpixmap_list):
        self.images_found = images_found
        self.qpixmap_list = qpixmap_list
    def Set_Size(self, widget_width, widget_height):
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.Grid_Thumbnails()
    def Set_Grid(self, grid_horz, grid_vert):
        self.grid_horz = grid_horz
        self.grid_vert = grid_vert
        self.Grid_Thumbnails()
    def Set_Fit_Ratio(self, tn_fit_ratio):
        if tn_fit_ratio == False:
            self.display_ratio = Qt.KeepAspectRatioByExpanding
        elif tn_fit_ratio == True:
            self.display_ratio = Qt.KeepAspectRatio
        self.tn_fit_ratio = tn_fit_ratio
        self.update()
    def Set_Operation(self, operation):
        self.operation = operation
        self.update()
    def Set_Scale(self, tn_smooth_scale):
        self.tn_smooth_scale = tn_smooth_scale
        self.update()

    # Calculations
    def Grid_Path(self, event):
        # Location
        loc = self.Grid_Location(event)
        # Name and Path
        for i in range(0, len(self.qpixmap_list)):
            if (loc[0] == self.qpixmap_list[i][0] and loc[1] == self.qpixmap_list[i][1]):
                path = os.path.normpath( self.qpixmap_list[i][2] )
                basename = os.path.basename(path)
                if os.path.exists(path) == True:
                    emit = [basename, path]
                    return emit
                    break
    def Grid_Location(self, event):
        ex = event.x()
        ey = event.y()
        check = ((ex >= 0 and ex <= self.widget_width) or (ey >= 0 and ey <= self.widget_height)) and (self.widget_width > 0 and self.widget_height > 0)
        if check == True:
            loc_x = Limit_Range( int((ex * self.grid_horz) / self.widget_width), 0 , self.grid_horz-1)
            loc_y = Limit_Range( int((ey * self.grid_vert) / self.widget_height), 0 , self.grid_vert-1)
        else:
            loc_x = 0
            loc_y = 0
        return [loc_x, loc_y]
    def Grid_Thumbnails(self):
        self.tn_x = self.widget_width / self.grid_horz
        self.tn_y = self.widget_height / self.grid_vert
        self.update()

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        self.stylus_x = event.x()
        self.stylus_y = event.y()

        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            location = self.Grid_Location(event)
            self.SIGNAL_NAME.emit(location)
            self.SIGNAL_NEUTRAL.emit(self.Grid_Path(event)[0])

        # Camera
        if (event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton):
            pass
        # Pagination
        if (event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.Pagination_Flip(event)
        # Drag and Drop
        if (event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
            pass

        # Context
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
            self.Context_Menu(event)
    def mouseMoveEvent(self, event):
        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            location = self.Grid_Location(event)
            self.SIGNAL_NAME.emit(location)
            self.SIGNAL_NEUTRAL.emit(self.Grid_Path(event)[0])

        # Camera
        if (event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton):
            pass
        # Pagination
        if (event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.Pagination_Stylus(event)
        # Drag and Drop
        if (event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
            path = self.Grid_Path(event)[1]
            self.SIGNAL_DRAG.emit(path)

        # Context
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
            pass
    def mouseDoubleClickEvent(self, event):
        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            location = self.Grid_Location(event)
            self.SIGNAL_PREVIEW.emit(location)
    def mouseReleaseEvent(self, event):
        self.SIGNAL_NEUTRAL.emit("")
        self.press = False
        self.origin_x = 0
        self.origin_y = 0
        self.update()

    def Pagination_Flip(self, event):
        top = 0.1 * self.widget_height
        bot = 0.9 * self.widget_height
        if self.origin_y <= top:
            self.press = True
            self.SIGNAL_CLICK.emit(1)
        elif self.origin_y >= bot:
            self.press = True
            self.SIGNAL_CLICK.emit(-1)
    def Pagination_Stylus(self, event):
        # Variables
        ey = event.y()
        if self.stylus_y > 0:
            ratio = int(self.stylus_y / self.tn_y)
            limit_below = int(self.tn_y * ratio)
            limit_upper = int(limit_below + self.tn_y)
        elif self.stylus_y < 0:
            ratio = int(self.stylus_y / self.tn_y)
            limit_upper = int(self.tn_y * ratio)
            limit_below = int(limit_upper - self.tn_y)
        # Update
        if ey < limit_below:
            self.press = False
            self.SIGNAL_STYLUS.emit(+1)
            self.stylus_y -= self.tn_y
        elif ey > limit_upper:
            self.press = False
            self.SIGNAL_STYLUS.emit(-1)
            self.stylus_y += self.tn_y
    def Context_Menu(self, event):
        name_path = self.Grid_Path(event)
        extension = self.Path_Extension(name_path[1])
        if extension in file_compress:
            compressed = True
        else:
            compressed = False
        insert = insert_bool(self)
        if (event.modifiers() == QtCore.Qt.NoModifier and name_path[0] != "."):
            cmenu = QMenu(self)
            # Actions
            if compressed == False:
                cmenu_function = cmenu.addAction("Function >>" + self.operation)
                cmenu_pin = cmenu.addAction("Pin Reference")
                cmenu.addSeparator()
            cmenu_document = cmenu.addAction("New Document")
            if insert == True:
                cmenu_insert_layer = cmenu.addAction("Insert Layer")
                cmenu_insert_ref = cmenu.addAction("Insert Reference")
            action = cmenu.exec_(self.mapToGlobal(event.pos()))
            # Triggers
            if compressed == False:
                if action == cmenu_function:
                    self.SIGNAL_FUNCTION.emit([name_path])
                if action == cmenu_pin:
                    self.SIGNAL_PIN_PATH.emit(name_path[1])
            if action == cmenu_document:
                self.SIGNAL_NEW_DOCUMENT.emit(name_path[1])
            if insert == True:
                if action == cmenu_insert_layer:
                    self.SIGNAL_INSERT_LAYER.emit(name_path[1])
                if action == cmenu_insert_ref:
                    self.SIGNAL_INSERT_REFERENCE.emit(name_path[1])
    def Path_Extension(self, path):
        extension = os.path.splitext(path)[1][1:]
        return extension

    # Wheel Events
    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        angle = 5
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Wheel_Index(event, delta_y, angle)
    def Wheel_Index(self, event, delta_y, angle):
        if delta_y > angle:
            self.SIGNAL_WHEEL.emit(+1)
        if delta_y < -angle:
            self.SIGNAL_WHEEL.emit(-1)

    # Drag and Drop Event
    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent(self, event):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = False
            event.setDropAction(Qt.CopyAction)
            if (self.origin_x == 0 and self.origin_y == 0): # Denys from recieving from self.
                mime_data = event_drop(self, event)
                self.SIGNAL_FUNCTION.emit(mime_data)
            event.accept()
        else:
            event.ignore()
        self.update()

    # Painter
    def paintEvent(self, event):
        # Theme
        krita_theme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Dots (no results)
        if (self.images_found == False and self.drop == False):
            for h in range(0, self.grid_horz+1):
                for v in range(0, self.grid_vert+1):
                    px = h * self.tn_x
                    py = v * self.tn_y
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QBrush(QColor(self.color1)))
                    if self.tn_x < self.tn_y:
                        side = self.tn_x
                    else:
                        side = self.tn_y
                    offset_x = (self.tn_x * 0.5) - (0.3 * side)
                    offset_y = (self.tn_y * 0.5) - (0.3 * side)
                    painter.drawEllipse(px + offset_x, py + offset_y, 0.6*side, 0.6*side)

        # Draw Pixmaps
        for i in range(0, len(self.qpixmap_list)):
            if self.qpixmap_list[i][2] != "":
                # Clip Mask
                px = self.qpixmap_list[i][0] * self.tn_x
                py = self.qpixmap_list[i][1] * self.tn_y
                thumbnail = QRectF(px,py, self.tn_x,self.tn_y)
                painter.setClipRect(thumbnail, Qt.ReplaceClip)

                # Render Pixmap
                qpixmap = self.qpixmap_list[i][3]
                if qpixmap.isNull() == False:
                    render = qpixmap.scaled(self.tn_x+1, self.tn_y+1, self.display_ratio, self.tn_smooth_scale)
                    render_width = render.width()
                    render_height = render.height()
                    offset_x = (self.tn_x - render_width) * 0.5
                    offset_y = (self.tn_y - render_height) * 0.5
                    painter.drawPixmap(px + offset_x, py + offset_y, render)
                else:
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QBrush(QColor(self.color1)))
                    if self.tn_x < self.tn_y:
                        side = self.tn_x
                    else:
                        side = self.tn_y
                    offset_x = (self.tn_x * 0.5) - (0.3 * side)
                    offset_y = (self.tn_y * 0.5) - (0.3 * side)
                    painter.drawEllipse(px + offset_x, py + offset_y, 0.6*side, 0.6*side)

        # Clean Mask
        painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)

        # Arrows
        if self.press == True:
            # Arrows
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color1)))
            if self.origin_y < (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint(self.widget_width*0.50, self.widget_height*0.05),
                    QPoint(self.widget_width*0.45, self.widget_height*0.10),
                    QPoint(self.widget_width*0.55, self.widget_height*0.10)
                    ])
            elif self.origin_y > (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint(self.widget_width*0.50, self.widget_height*0.95),
                    QPoint(self.widget_width*0.45, self.widget_height*0.90),
                    QPoint(self.widget_width*0.55, self.widget_height*0.90)
                    ])
            painter.drawPolygon(arrow)

        # Drag and Drop
        if self.drop == True:
            check = self.origin_x == 0 and self.origin_y == 0
            if check == True:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color1)))
                if self.widget_width < self.widget_height:
                    side = self.widget_width
                else:
                    side = self.widget_height
                w2 = self.widget_width * 0.5
                h2 = self.widget_height * 0.5
                poly_tri = QPolygon([
                    QPoint(w2 - (0.3*side), h2 - (0.2*side)),
                    QPoint(w2 + (0.3*side), h2 - (0.2*side)),
                    QPoint(w2, h2 + (0.2*side)),
                    ])
                painter.drawPolygon(poly_tri)

class ImagineBoard_Reference(QWidget):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    SIGNAL_DROP = QtCore.pyqtSignal(str)
    # Reference
    SIGNAL_UNDO = QtCore.pyqtSignal(list)
    SIGNAL_SAVE = QtCore.pyqtSignal(list)
    SIGNAL_LOAD = QtCore.pyqtSignal(int)
    SIGNAL_CLIP = QtCore.pyqtSignal(list)

    # Init
    def __init__(self, parent):
        super(ImagineBoard_Reference, self).__init__(parent)
        self.Variables()
    def Variables(self):
        # Widget
        self.drop = False
        self.context_menu = "BOARD"

        # Board
        self.kra_bind = False
        self.pin_zoom = {
            "bool" : False,
            "qpixmap" : "",
            }

        # Events
        self.origin_x = 0
        self.origin_y = 0
        # self.mmb_press = False # blockes pressing and rotating at the same time
        self.press = None

        # References
        self.ref = []
        self.index = None
        self.node = None
        self.limit_x = []
        self.limit_y = []

        # Selection
        self.selection_count = 0
        self.sel_l = 0
        self.sel_r = 0
        self.sel_t = 0
        self.sel_b = 0

        # Camera
        self.camera_scale = []
        self.camera_relative = 0

        # Undo
        self.modified = False

        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Size(self, widget_width, widget_height):
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.update()

    # Index
    def Index_Closest(self, event):
        # Event
        ex = event.x()
        ey = event.y()
        # Detect Image Index
        index = None
        if (self.ref != [] and self.ref != None):
            self.ref.reverse()
            for i in range(0, len(self.ref)):
                ox = self.ref[i]["ox"]
                oy = self.ref[i]["oy"]
                bl = self.ref[i]["bl"]
                br = self.ref[i]["br"]
                bt = self.ref[i]["bt"]
                bb = self.ref[i]["bb"]
                if (ex >= bl and ex <= br and ey >= bt and ey <= bb): # Clicked inside the image
                    index = i
                    self.ref[i]["rx"] = self.origin_x - ox
                    self.ref[i]["ry"] = self.origin_y - oy
                    break
            self.ref.reverse()

        # Change index to last
        if index != None:
            index = (len(self.ref)-1) - index
            pin = self.ref[index]
            self.ref.pop(index)
            self.ref.append(pin)
            self.index = len(self.ref)-1
        else:
            self.index = index

        # Calculate Node
        if self.index != None:
            self.node = self.Index_Node(event)
        else:
            self.node = 0

        # Relative Deltas
        self.Index_Deltas_Move(index)
    def Index_Deltas_Move(self, index):
        for i in range(0, len(self.ref)):
            if i != index:
                self.ref[i]["rx"] = self.origin_x - self.ref[i]["ox"]
                self.ref[i]["ry"] = self.origin_y - self.ref[i]["oy"]
    def Index_Deltas_Scale(self):
        self.camera_scale = []
        for i in range(0, len(self.ref)):
            self.camera_scale.append(self.ref[i])
    def Index_Delta_Clean(self):
        for i in range(0, len(self.ref)):
            self.ref[i]["rx"] = 0
            self.ref[i]["ry"] = 0
    def Index_Node(self, event):
        # Node Choice
        nodes = self.Index_Points(self.index)
        check = []
        for i in range(0, len(nodes)):
            point_x = nodes[i][0]
            point_y = nodes[i][1]
            dist = Trig_2D_Points_Distance(point_x, point_y, self.origin_x, self.origin_y)
            if i == 4:
                dist = dist * 2 # node 5 range debuff in half
            check.append(dist)
        value = min(check)
        if value <= 20:
            nodo = check.index(value) + 1
        else:
            nodo = 0
        return nodo
    def Index_Points(self, index):
        # Read
        bl = self.ref[index]["bl"]
        br = self.ref[index]["br"]
        bt = self.ref[index]["bt"]
        bb = self.ref[index]["bb"]
        ww = abs(br - bl)
        hh = abs(bb - bt)
        w2 = ww * 0.5
        h2 = hh * 0.5
        # Node Points
        n1_x = bl
        n1_y = bt
        n2_x = bl + w2
        n2_y = bt
        n3_x = bl + ww
        n3_y = bt
        n4_x = bl
        n4_y = bt + h2
        n5_x = bl + w2
        n5_y = bt + h2
        n6_x = br
        n6_y = bt + h2
        n7_x = bl
        n7_y = bb
        n8_x = bl + w2
        n8_y = bb
        n9_x = br
        n9_y = bb
        # List
        nodes = [ [n1_x, n1_y], [n2_x, n2_y], [n3_x, n3_y], [n4_x, n4_y], [n5_x, n5_y], [n6_x, n6_y], [n7_x, n7_y], [n8_x, n8_y], [n9_x, n9_y] ]
        # Return
        return nodes
    def Index_Limits(self, event):
        if self.index != None:
            # X Axis
            self.limit_x = []
            for i in range(0, len(self.ref)):
                if (i != self.index and self.ref[i]["select"] == False):
                    bl = self.ref[i]["bl"]
                    br = self.ref[i]["br"]
                    check_l = (bl >= 0 and bl <= self.widget_width)
                    check_r = (br >= 0 and br <= self.widget_width)
                    if (bl not in self.limit_x and check_l == True):
                        self.limit_x.append(bl)
                    if (br not in self.limit_x and check_r == True):
                        self.limit_x.append(br)
            # Y Axis
            self.limit_y = []
            for i in range(0, len(self.ref)):
                if (i != self.index and self.ref[i]["select"] == False):
                    bt = self.ref[i]["bt"]
                    bb = self.ref[i]["bb"]
                    check_t = (bt >= 0 and bt <= self.widget_height)
                    check_b = (bb >= 0 and bb <= self.widget_height)
                    if (bt not in self.limit_y and check_t == True):
                        self.limit_y.append(bt)
                    if (bb not in self.limit_y and check_b == True):
                        self.limit_y.append(bb)

    # Active
    def Active_Select(self, index):
        self.Active_Clear()
        self.ref[index]["active"] = True
        self.update()
    def Active_Clear(self):
        for i in range(0, len(self.ref)):
            self.ref[i]["active"] = False
        self.update()

    # Selection
    def Selection_Shift(self, index):
        self.ref[index]["select"] = not self.ref[index]["select"]
        self.Selection_Count()
        self.update()
    def Selection_Clear(self):
        for i in range(0, len(self.ref)):
            self.ref[i]["select"] = False
        self.Selection_Count()
        self.update()
    def Selection_Replace(self, index):
        self.Selection_Clear()
        self.ref[index]["select"] = True
        self.Selection_Count()
        self.update()
    def Selection_Square(self, event):
        # Event
        ex = event.x()
        ey = event.y()
        # Calculations
        sel_w = ex - self.origin_x
        sel_h = ey - self.origin_y
        self.sel_l = min(ex, self.origin_x)
        self.sel_r = max(ex, self.origin_x)
        self.sel_t = min(ey, self.origin_y)
        self.sel_b = max(ey, self.origin_y)
        # Selection
        for i in range(0, len(self.ref)):
            bl = self.ref[i]["bl"]
            br = self.ref[i]["br"]
            bt = self.ref[i]["bt"]
            bb = self.ref[i]["bb"]
            check = (bl >= self.sel_l and br <= self.sel_r and bt >= self.sel_t and bb <= self.sel_b)
            self.ref[i]["active"] = False
            if check == True:
                self.ref[i]["select"] = True
            else:
                self.ref[i]["select"] = False
        self.Selection_Count()
        self.update()
    def Selection_Count(self):
        self.selection_count = 0
        for i in range(0, len(self.ref)):
            if self.ref[i]["select"] == True:
                self.selection_count += 1
    def Selection_Delete(self):
        count = 0
        for i in range(0, len(self.ref)):
            if self.ref[i]["select"] == True:
                count += 1
        for i in range(0, count):
            for i in range(0, len(self.ref)):
                if self.ref[i]["select"] == True:
                    self.ref.pop(i)
                    break
        self.index = None
        self.update()

    # Pins on the Board
    def Pin_Add(self, pin):
        pin["qpixmap"] = QPixmap(pin["path"])
        self.ref.append(pin)
        self.Pixmap_Edit(len(self.ref)-1)
        self.Board_Save()
        self.modified = True
        self.update()
    def Pin_Drop(self, path):
        self.SIGNAL_DROP.emit(path)
        self.update()
    def Pin_Drag(self, index):
        # Calculations
        path = self.ref[index]["path"]
        pixmap = QPixmap(path)
        width = pixmap.width()
        height = pixmap.height()
        cl = self.ref[index]["cl"]
        cr = self.ref[index]["cr"]
        ct = self.ref[index]["ct"]
        cb = self.ref[index]["cb"]
        cw = cr - cl
        ch = cb - ct
        if (cl != 0 or cr != 1 or ct != 0 or cb != 1):
            clip_state = True
        else:
            clip_state = False
        # Emit
        self.SIGNAL_CLIP.emit([clip_state, cl * width, ct * height, cw * width, ch * height])
        self.SIGNAL_DRAG.emit(path)
    def Pin_Replace(self, index, path):
        if len(self.ref) > 0:
            self.ref[index]["path"] = path
            self.update()
    def Pin_NewPath(self, index):
        path = QFileDialog(QWidget(self))
        path.setFileMode(QFileDialog.ExistingFile)
        file_path = path.getOpenFileName(self, "Select File", os.path.dirname(self.ref[index]["path"]) )[0]
        file_path = os.path.normpath( file_path )
        if (file_path != "" and file_path != "."):
            self.Pin_Delete(self.index)
            self.Pin_Drop(file_path)
    def Pin_Delete(self, index):
        self.Selection_Clear()
        if index != None:
            self.ref.pop(index)
        self.index = None
        self.update()

    # Board Management
    def Board_Rebase(self):
        for i in range(0, len(self.ref)):
            self.Pixmap_Edit(i)
        self.update()
    def Board_Load(self, references):
        self.ref = []
        for i in range(0, len(references)):
            self.Pin_Add(references[i])
        self.update()
    def Board_Save(self):
        reference = []
        for i in range(0, len(self.ref)):
            pin = self.ref[i].copy()
            pin["qpixmap"] = None
            reference.append(pin)
        self.SIGNAL_SAVE.emit([self.kra_bind, reference])
    def Board_Delete(self):
        self.ref = []
        self.Selection_Clear()
        self.update()

    # Image Packing
    def Pack_Straight(self, orientation):
        if orientation == "line":
            pass
            # self.Search_Something(self.ref, "dy")
        if orientation == "column":
            pass
    def Pack_Optimized(self):
        pass

    def Search_Something(self, dic, search, check):
        # Variables
        index = 0
        minmax = 0
        # Check valid dicctionary
        length = len(dic)
        if length > 0:
            # Search dicctionary
            for i in range(0, length):
                select = dic["select"]
                value = dic[search]
                if check == "MAX":
                    if (select == True and (minmax == 0 or minmax < value)):
                        index = i
                        minmax = value
                if check == "MIN":
                    if (select == True and (minmax == 0 or minmax > value)):
                        index = i
                        minmax = value
            return index, minmax

    # Mouse Events
    def mousePressEvent(self, event):
        # Mouse
        self.origin_x = event.x()
        self.origin_y = event.y()
        self.Index_Closest(event)
        self.Index_Limits(event)

        if self.press == None:
            # Neutral
            if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
                self.press = "n0"
                if self.index != None:
                    self.Active_Select(self.index)

            # Camera
            if (event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton):
                self.press = "c1"
                self.Index_Deltas_Move(None)
            if (event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.RightButton):
                self.press = "c2"
                self.camera_relative = self.origin_y
                self.Index_Deltas_Scale()
            if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton):
                self.press = "c3"
                self.Index_Deltas_Move(None)
            # Select
            if (event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton):
                self.press = "s1"
                if self.index != None:
                    self.Selection_Shift(self.index)
                else:
                    self.Selection_Clear()
            # Drag and Drop
            if (event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
                self.press = "d1"

            # Pixmap Operations
            if (event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier) and event.buttons() == QtCore.Qt.LeftButton):
                self.press = "p1"
                if self.index != None:
                    self.Active_Select(self.index)
                    self.Index_Deltas_Move(self.index)
                    self.Transform_Operation(event, self.index, self.node)
                else:
                    self.Selection_Clear()

            # Context
            if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
                self.press = "c1"
                self.Context_Menu(event)
    def mouseMoveEvent(self, event):
        # Mouse
        ex = event.x()
        ey = event.y()
        dist = Trig_2D_Points_Distance(self.origin_x, self.origin_y, event.x(), event.y())
        limit = 10

        # Neutral
        if (self.press == "n0" and event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            if dist >= limit:
                self.Selection_Square(event)

        # Camera
        if (self.press == "c1" and event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.Camera_Pan(event)
        if (self.press == "c2" and event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.RightButton):
            value = 0.02
            check = ey - self.camera_relative
            if check > 1:
                self.Camera_Scale(event, self.origin_x, self.origin_y, -value)
            if check < -1:
                self.Camera_Scale(event, self.origin_x, self.origin_y, value)
        if (self.press == "c3" and event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton):
            self.mmb_press = True
            self.Camera_Pan(event)
        # Select
        if (self.press == "s1" and event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton):
            if dist >= limit:
                self.Selection_Square(event)
        # Drag and Drop
        if (self.press == "d1" and event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton):
            if (self.index != None and dist >= limit):
                self.Pin_Drag(self.index)

        # Pixmap Operations
        if (self.press == "p1" and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier) and event.buttons() == QtCore.Qt.LeftButton):
            if self.index != None:
                self.Transform_Operation(event, self.index, self.node)

        # Context
        if (self.press == "c1" and event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton):
            pass
    def mouseDoubleClickEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        # Events
        self.origin_x = 0
        self.origin_y = 0
        self.camera_relative = 0
        # self.mmb_press = False
        self.press = None
        # Square Selection
        self.sel_l = 0
        self.sel_r = 0
        self.sel_t = 0
        self.sel_b = 0
        # Active
        self.Active_Clear()
        # Relative Deltas
        self.Index_Delta_Clean()
        # Undo
        if self.modified == True:
            self.SIGNAL_UNDO.emit(self.ref)
            self.modified = False
        self.update()

    # Context Menu Event
    def Context_Menu(self, event):
        self.Index_Closest(event)
        cmenu = QMenu(self)
        position = self.mapToGlobal(event.pos())
        if self.pin_zoom["bool"] == True:
            self.Menu_Pin_Zoom(event, cmenu, position)
        elif self.index == None:
            self.Menu_Board(event, cmenu, position)
        elif self.ref[self.index]["select"] == True:
            self.Menu_Selection(event, cmenu, position)
        else:
            self.Menu_Pin(event, cmenu, position)
        # Undo
        if self.modified == True:
            self.SIGNAL_UNDO.emit(self.ref)
            self.modified = False
    def Menu_Pin(self, event, cmenu, position):
        # Actions
        cmenu.addSection("PIN")
        cmenu_zoom_open = cmenu.addAction("Zoom")
        cmenu.addSection(" ")
        cmenu_edit_greyscale = cmenu.addAction("Greyscale")
        cmenu_edit_greyscale.setCheckable(True)
        cmenu_edit_greyscale.setChecked(self.ref[self.index]["egs"])
        cmenu_edit_invert_h = cmenu.addAction("Flip Horizontal")
        cmenu_edit_invert_h.setCheckable(True)
        cmenu_edit_invert_h.setChecked(self.ref[self.index]["efx"])
        cmenu_edit_invert_v = cmenu.addAction("Flip Vertical")
        cmenu_edit_invert_v.setCheckable(True)
        cmenu_edit_invert_v.setChecked(self.ref[self.index]["efy"])
        cmenu.addSection(" ")
        cmenu_pin_newpath = cmenu.addAction("New Path")
        cmenu_pin_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_zoom_open:
            self.Pixmap_Zoom(True, self.ref[self.index]["qpixmap"])
        if action == cmenu_edit_greyscale:
            self.ref[self.index]["egs"] = not self.ref[self.index]["egs"]
            self.Pixmap_Edit(self.index)
            self.modified = True
        if action == cmenu_edit_invert_h:
            # Operation
            self.ref[self.index]["efx"] = not self.ref[self.index]["efx"]
            # Clip Invert
            a = 1 - self.ref[self.index]["cr"]
            b = 1 - self.ref[self.index]["cl"]
            self.ref[self.index]["cl"] = a
            self.ref[self.index]["cr"] = b
            # Bounding Box
            clip, sides = self.Clip_Construct(self.index)
            self.ref[self.index]["bl"] = sides[0]
            self.ref[self.index]["br"] = sides[1]
            self.ref[self.index]["bt"] = sides[2]
            self.ref[self.index]["bb"] = sides[3]
            # Pixmap Edit
            self.Pixmap_Edit(self.index)
            self.modified = True
        if action == cmenu_edit_invert_v:
            # Operation
            self.ref[self.index]["efy"] = not self.ref[self.index]["efy"]
            # Clip Invert
            a = 1 - self.ref[self.index]["cb"]
            b = 1 - self.ref[self.index]["ct"]
            self.ref[self.index]["ct"] = a
            self.ref[self.index]["cb"] = b
            # Bounding Box
            clip, sides = self.Clip_Construct(self.index)
            self.ref[self.index]["bl"] = sides[0]
            self.ref[self.index]["br"] = sides[1]
            self.ref[self.index]["bt"] = sides[2]
            self.ref[self.index]["bb"] = sides[3]
            # Pixmap Edit
            self.Pixmap_Edit(self.index)
            self.modified = True
        if action == cmenu_pin_newpath:
            self.Pin_NewPath(self.index)
            self.modified = True
        if action == cmenu_pin_delete:
            self.Pin_Delete(self.index)
            self.modified = True
    def Menu_Selection(self, event, cmenu, position):
        # Actions
        cmenu.addSection("SELECTION")
        cmenu_pack_line = cmenu.addAction("Pack Line")
        cmenu_pack_column = cmenu.addAction("Pack Column")
        cmenu_pack_optimized = cmenu.addAction("Pack Optimized")
        cmenu.addSection(" ")
        cmenu_selection_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_pack_line:
            self.Pack_Straight("line")
            self.modified = True
        if action == cmenu_pack_column:
            self.Pack_Straight("column")
            self.modified = True
        if action == cmenu_pack_optimized:
            self.Pack_Optimized()
            self.modified = True
        if action == cmenu_selection_delete:
            self.Selection_Delete()
            self.modified = True
    def Menu_Board(self, event, cmenu, position):
        # Actions
        cmenu.addSection("BOARD")
        cmenu_board_rebase = cmenu.addAction("Rebase")
        cmenu.addSection(" ")
        cmenu_kra_load = cmenu.addAction("KRA Load")
        cmenu_kra_save = cmenu.addAction("KRA Save")
        cmenu_kra_save.setCheckable(True)
        cmenu_kra_save.setChecked(self.kra_bind)
        cmenu.addSection(" ")
        cmenu_board_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_board_rebase:
            self.Board_Rebase()
        if action == cmenu_kra_load:
            self.SIGNAL_LOAD.emit(0)
            self.modified = True
        if action == cmenu_kra_save:
            self.kra_bind = not self.kra_bind
        if action == cmenu_board_delete:
            self.Board_Delete()
            self.modified = True
    def Menu_Pin_Zoom(self, event, cmenu, position):
        # Actions
        cmenu.addSection("ZOOM")
        cmenu_zoom_close = cmenu.addAction("Close")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_zoom_close:
            self.Pixmap_Zoom(False, "")

    # Wheel Events
    def wheelEvent(self, event):
        if self.press == None:
            self.Index_Deltas_Scale()
            ex = event.x()
            ey = event.y()
            delta = event.angleDelta()
            if event.modifiers() == QtCore.Qt.NoModifier:
                value = 0.1
                delta_y = delta.y()
                if delta_y > 20:
                    self.press = "c4"
                    self.Camera_Scale(event, ex, ey, value)
                    self.press = None
                if delta_y < -20:
                    self.press = "c4"
                    self.Camera_Scale(event, ex, ey, -value)
                    self.press = None
                self.update()

    # Image Operations
    def Transform_Operation(self, event, index, node):
        scale = [1,3,7,9]
        rotation = [5]
        clip = [2,4,6,8]
        if node in scale:
            self.Pixmap_Scale(event, index, node)
        elif node in rotation:
            self.Pixmap_Rotation(event, index)
        elif node in clip:
            self.Pixmap_Clip(event, index, node)
        else:
            self.Pixmap_Move(event, index)
        # Undo entry
        self.modified = True
    def Pixmap_Move(self, event, index):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Index Move
        path = self.ref[index]["path"]
        ox = self.ref[index]["ox"]
        oy = self.ref[index]["oy"]
        rx = self.ref[index]["rx"]
        ry = self.ref[index]["ry"]
        dw = self.ref[index]["dw"]
        dh = self.ref[index]["dh"]
        dw2 = dw * 0.5
        dh2 = dh * 0.5
        sx = 0
        sy = 0

        # Move Single
        n_ox = self.ref[index]["ox"] = ex - rx
        n_oy = self.ref[index]["oy"] = ey - ry
        n_dx = self.ref[index]["dx"] = n_ox - dw2
        n_dy = self.ref[index]["dy"] = n_oy - dh2
        n_dxw = self.ref[index]["dxw"] = n_ox + dw2
        n_dyh = self.ref[index]["dyh"] = n_oy + dh2

        # Bounding Box
        clip, sides = self.Clip_Construct(index)
        bl = self.ref[index]["bl"] = sides[0]
        br = self.ref[index]["br"] = sides[1]
        bt = self.ref[index]["bt"] = sides[2]
        bb = self.ref[index]["bb"] = sides[3]

        # Calculations
        bbl = bl - n_dx
        bbr = n_dxw - br
        bbt = bt - n_dy
        bbb = n_dyh - bb
        bbw = abs(br - bl)
        bbh = abs(bb - bt)

        # Attach to Edges
        snap = 5
        if len(self.limit_x) > 0:
            for i in range(0, len(self.limit_x)):
                lim_xi = self.limit_x[i]
                ll = lim_xi - snap
                lr = lim_xi + snap
                if (bl >= ll and bl <= lr):
                    self.ref[index]["ox"] = lim_xi + dw2 - bbl
                    self.ref[index]["dx"] = lim_xi - bbl
                    self.ref[index]["dxw"] = lim_xi + dw - bbr
                    self.ref[index]["bl"] = lim_xi
                    self.ref[index]["br"] = lim_xi + bbw
                    sx = self.ref[index]["ox"] - n_ox
                    break
                elif (br >= ll and br <= lr):
                    self.ref[index]["ox"] = lim_xi - dw2 + bbr
                    self.ref[index]["dx"] = lim_xi - dw + bbr
                    self.ref[index]["dxw"] = lim_xi + bbr
                    self.ref[index]["bl"] = lim_xi - bbw
                    self.ref[index]["br"] = lim_xi
                    sx = self.ref[index]["ox"] - n_ox
                    break
        if len(self.limit_y) > 0:
            for i in range(0, len(self.limit_y)):
                lim_yi = self.limit_y[i]
                lt = lim_yi - snap
                lb = lim_yi + snap
                if (bt >= lt and bt <= lb):
                    self.ref[index]["oy"] = lim_yi + dh2 - bbt
                    self.ref[index]["dy"] = lim_yi - bbt
                    self.ref[index]["dyh"] = lim_yi + dh - bbt
                    self.ref[index]["bt"] = lim_yi
                    self.ref[index]["bb"] = lim_yi + bbh
                    sy = self.ref[index]["oy"] - n_oy
                    break
                elif (bb >= lt and bb <= lb):
                    self.ref[index]["oy"] = lim_yi - dh2 + bbb
                    self.ref[index]["dy"] = lim_yi - dh + bbb
                    self.ref[index]["dyh"] = lim_yi + bbb
                    self.ref[index]["bt"] = lim_yi - bbh
                    self.ref[index]["bb"] = lim_yi
                    sy = self.ref[index]["oy"] - n_oy
                    break

        # Selection Move
        for i in range(0, len(self.ref)):
            if (i != index and self.ref[i]["select"] == True):
                # Read
                ox = self.ref[i]["ox"]
                oy = self.ref[i]["oy"]
                rx = self.ref[i]["rx"]
                ry = self.ref[i]["ry"]
                dw = self.ref[i]["dw"]
                dh = self.ref[i]["dh"]
                dw2 = dw * 0.5
                dh2 = dh * 0.5
                n_ox = ex - rx + sx
                n_oy = ey - ry + sy
                # Write
                self.ref[i]["ox"] = n_ox
                self.ref[i]["oy"] = n_oy
                self.ref[i]["dx"] = n_ox - dw2
                self.ref[i]["dy"] = n_oy - dh2
                self.ref[i]["dxw"] = n_ox + dw2
                self.ref[i]["dyh"] = n_oy + dh2
                clip, sides = self.Clip_Construct(i)
                self.ref[i]["bl"] = sides[0]
                self.ref[i]["br"] = sides[1]
                self.ref[i]["bt"] = sides[2]
                self.ref[i]["bb"] = sides[3]

        # Update
        self.update()
    def Pixmap_Rotation(self, event, index):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Read
        ox = self.ref[index]["ox"]
        oy = self.ref[index]["oy"]
        rn = self.ref[index]["rn"]
        ro = self.ref[index]["ro"]
        ss = self.ref[index]["ss"]
        dx = self.ref[index]["dx"]
        dy = self.ref[index]["dy"]
        dw = self.ref[index]["dw"]
        dh = self.ref[index]["dh"]
        dxw = self.ref[index]["dxw"]
        dyh = self.ref[index]["dyh"]
        cl = self.ref[index]["cl"]
        cr = self.ref[index]["cr"]
        ct = self.ref[index]["ct"]
        cb = self.ref[index]["cb"]

        # Angle
        dist_event = Trig_2D_Points_Distance(ex, ey, ox, oy)
        if (cl == 0 and cr == 1 and ct == 0 and cb == 1):
            angle_event = Trig_2D_Points_Lines_Angle(ox, oy-100, ox, oy, ex, ey)
        else:
            angle_event = Trig_2D_Points_Lines_Angle(self.origin_x, self.origin_y, ox, oy, ex, ey)
        offset = 5
        angle_event = Limit_Looper(angle_event+offset, 360)

        # Snapping
        snap = ss * 0.5
        if dist_event >= snap:
            angle = (int(angle_event / 5) * 5)
        else:
            angle = ro

        # Controller Points
        c1_x, c1_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(angle + rn + 180, 360) )
        c2_x, c2_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(angle - rn      , 360) )
        c3_x, c3_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(angle - rn - 180, 360) )
        c4_x, c4_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(angle + rn      , 360) )

        # Calculations
        esq = min(c1_x, c2_x, c3_x, c4_x)
        dir = max(c1_x, c2_x, c3_x, c4_x)
        top = min(c1_y, c2_y, c3_y, c4_y)
        bot = max(c1_y, c2_y, c3_y, c4_y)
        width = abs(dir - esq)
        height = abs(bot - top)

        # Scale Relative
        dist_draw = Trig_2D_Points_Distance(esq, top, ox, oy)
        dist_cir = Trig_2D_Points_Distance(c1_x, c1_y, ox, oy)
        sr = dist_cir / dist_draw

        # Write
        self.ref[index]["ro"] = angle
        self.ref[index]["sr"] = sr
        self.ref[index]["dx"] = esq
        self.ref[index]["dy"] = top
        self.ref[index]["dw"] = width
        self.ref[index]["dh"] = height
        self.ref[index]["dxw"] = dir
        self.ref[index]["dyh"] = bot

        # Bounding Box
        clip, sides = self.Clip_Construct(index)
        bl = self.ref[index]["bl"] = sides[0]
        br = self.ref[index]["br"] = sides[1]
        bt = self.ref[index]["bt"] = sides[2]
        bb = self.ref[index]["bb"] = sides[3]

        # Edit Cycle
        self.Pixmap_Edit(index)

        # Update
        self.update()
    def Pixmap_Scale(self, event, index, node):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Read
        ox = self.ref[index]["ox"]
        oy = self.ref[index]["oy"]
        rn = self.ref[index]["rn"]
        ro = self.ref[index]["ro"]
        sr = self.ref[index]["sr"]
        dx = self.ref[index]["dx"]
        dy = self.ref[index]["dy"]
        dw = self.ref[index]["dw"]
        dh = self.ref[index]["dh"]
        dxw = self.ref[index]["dxw"]
        dyh = self.ref[index]["dyh"]
        bl = self.ref[index]["bl"]
        br = self.ref[index]["br"]
        bt = self.ref[index]["bt"]
        bb = self.ref[index]["bb"]

        # Calculations
        bw = abs(br - bl)
        bh = abs(bb - bt)
        r_angle = rn + ro
        b_ratio = bw / bh
        snap_lim = 5 # distance pixmap to limit to snap
        snap_mouse = 20 # distance mouse to pixmap to trigger snapping mode

        # Snapping Preparation Cycle
        if (node == 1 or node == 9):
            s19_1x = 0
            s19_1y = 0
            s19_2x = 0
            s19_2y = 0
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                for x in range(0, len(self.limit_x)):
                    ll = self.limit_x[x] - snap_lim
                    lr = self.limit_x[x] + snap_lim
                    if (ex >= ll and ex <= lr):
                        s19_1x, s19_1y = Trig_2D_Points_Lines_Intersection(
                            self.limit_x[x], ey,
                            self.limit_x[x], (ey + 10),
                            dx, dy,
                            dw, dh)
                        break
                for y in range(0, len(self.limit_y)):
                    lt = self.limit_y[y] - snap_lim
                    lb = self.limit_y[y] + snap_lim
                    if (ey >= lt and ey <= lb):
                        s19_2x, s19_2y = Trig_2D_Points_Lines_Intersection(
                            ex, self.limit_y[y],
                            (ex + 10), self.limit_y[y],
                            dx, dy,
                            dw, dh)
                        break
                lim_x = s19_1x
                lim_y = s19_2y
        if (node == 3 or node == 7):
            s37_1x = 0
            s37_1y = 0
            s37_2x = 0
            s37_2y = 0
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                for x in range(0, len(self.limit_x)):
                    ll = self.limit_x[x] - snap_lim
                    lr = self.limit_x[x] + snap_lim
                    if (ex >= ll and ex <= lr):
                        s37_1x, s37_1y = Trig_2D_Points_Lines_Intersection(
                            self.limit_x[x], ey,
                            self.limit_x[x], (ey + 10),
                            dw, dy,
                            dx, dh)
                        break
                for y in range(0, len(self.limit_y)):
                    lt = self.limit_y[y] - snap_lim
                    lb = self.limit_y[y] + snap_lim
                    if (ey >= lt and ey <= lb):
                        s37_2x, s37_2y = Trig_2D_Points_Lines_Intersection(
                            ex, self.limit_y[y],
                            (ex + 10), self.limit_y[y],
                            dw, dy,
                            dx, dh)
                        break
                lim_x = s37_1x
                lim_y = s37_2y

        # Pivot Point (relative)
        if node == 1:
            pivot_x = br
            pivot_y = bb
        if node == 3:
            pivot_x = bl
            pivot_y = bb
        if node == 7:
            pivot_x = br
            pivot_y = bt
        if node == 9:
            pivot_x = bl
            pivot_y = bt
        pl = dx - pivot_x
        pr = dxw - pivot_x
        pt = dy - pivot_y
        pb = dyh - pivot_y

        # Scale
        hip = Trig_2D_Points_Distance(pivot_x, pivot_y, ex, ey)
        b_angle = Trig_2D_Points_Lines_Angle(br,bt, bl,bt, br,bb)
        n_bbox_h = math.cos(math.radians(b_angle)) * hip
        n_bbox_v = math.sin(math.radians(b_angle)) * hip

        # Bounding Box
        if node == 1:
            # Bounding Box
            n_bl = pivot_x - n_bbox_h
            n_br = pivot_x
            n_bt = pivot_y - n_bbox_v
            n_bb = pivot_y
            # to Point
            to_a = n_bl
            to_b = n_bt
        if node == 3:
            # Bounding Box
            n_bl = pivot_x
            n_br = pivot_x + n_bbox_h
            n_bt = pivot_y - n_bbox_v
            n_bb = pivot_y
            # to Point
            to_a = n_br
            to_b = n_bt
        if node == 7:
            # Bounding Box
            n_bl = pivot_x - n_bbox_h
            n_br = pivot_x
            n_bt = pivot_y
            n_bb = pivot_y + n_bbox_v
            # to Point
            to_a = n_bl
            to_b = n_bb
        if node == 9:
            # Bounding Box
            n_bl = pivot_x
            n_br = pivot_x + n_bbox_h
            n_bt = pivot_y
            n_bb = pivot_y + n_bbox_v
            # to Point
            to_a = n_br
            to_b = n_bb

        # Distance Snapping
        if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
            snap_e = Trig_2D_Points_Distance(ex, ey, to_a, to_b)
            snap_x = Trig_2D_Points_Distance(ex, ey, lim_x, ey)
            snap_y = Trig_2D_Points_Distance(ex, ey, ex, lim_y)
            if (snap_e <= snap_mouse and (snap_x <= snap_lim or snap_y <= snap_lim)):
                # Distance
                if snap_x <= snap_y:
                    n_bbox_h = Trig_2D_Points_Distance(pivot_x, 0, lim_x, 0)
                    n_bbox_v = n_bbox_h / b_ratio
                else:
                    n_bbox_v = Trig_2D_Points_Distance(0, pivot_y, 0, lim_y)
                    n_bbox_h = n_bbox_v * b_ratio
                # Snap Dimensions
                if node == 1:
                    n_bl = pivot_x - n_bbox_h
                    n_bt = pivot_y - n_bbox_v
                if node == 3:
                    n_br = pivot_x + n_bbox_h
                    n_bt = pivot_y - n_bbox_v
                if node == 7:
                    n_bl = pivot_x - n_bbox_h
                    n_bb = pivot_y + n_bbox_v
                if node == 9:
                    n_br = pivot_x + n_bbox_h
                    n_bb = pivot_y + n_bbox_v

        # Factor
        factor_x = n_bbox_h / bw
        factor_y = n_bbox_v / bh

        # Calculations
        n_dx = pivot_x + (pl * factor_x)
        n_dy = pivot_y + (pt * factor_y)
        n_dxw = pivot_x + (pr * factor_x)
        n_dyh = pivot_y + (pb * factor_y)
        n_dw = abs(n_dxw - n_dx)
        n_dh = abs(n_dyh - n_dy)
        n_ox = n_dx + (n_dw * 0.5)
        n_oy = n_dy + (n_dh * 0.5)
        n_ss = Trig_2D_Points_Distance(n_dx, n_dy, n_ox, n_oy) * sr

        # Write
        self.ref[index]["ox"] = n_ox
        self.ref[index]["oy"] = n_oy
        self.ref[index]["dx"] = n_dx
        self.ref[index]["ss"] = n_ss
        self.ref[index]["dy"] = n_dy
        self.ref[index]["dw"] = n_dw
        self.ref[index]["dh"] = n_dh
        self.ref[index]["dxw"] = n_dxw
        self.ref[index]["dyh"] = n_dyh
        self.ref[index]["bl"] = n_bl
        self.ref[index]["br"] = n_br
        self.ref[index]["bt"] = n_bt
        self.ref[index]["bb"] = n_bb

        # Update
        self.update()
    def Pixmap_Clip(self, event, index, node):
        # Event
        ex = event.x()
        ey = event.y()

        # Read
        dx = self.ref[index]["dx"]
        dy = self.ref[index]["dy"]
        dw = self.ref[index]["dw"]
        dh = self.ref[index]["dh"]
        dxw = self.ref[index]["dxw"]
        dyh = self.ref[index]["dyh"]
        cl = self.ref[index]["cl"]
        cr = self.ref[index]["cr"]
        ct = self.ref[index]["ct"]
        cb = self.ref[index]["cb"]

        # Nodes
        safe = 0.03
        if node == 2:
            cut = Limit_Range((ey - dy) / dh, 0, cb-safe)
            self.ref[index]["ct"] = cut
        if node == 4:
            cut = Limit_Range((ex - dx) / dw, 0, cr-safe)
            self.ref[index]["cl"] = cut
        if node == 6:
            cut = Limit_Range((ex - dx) / dw, cl+safe, 1)
            self.ref[index]["cr"] = cut
        if node == 8:
            cut = Limit_Range((ey - dy) / dh, ct+safe, 1)
            self.ref[index]["cb"] = cut

        # Bounding Box
        clip, sides = self.Clip_Construct(index)
        self.ref[index]["bl"] = sides[0]
        self.ref[index]["br"] = sides[1]
        self.ref[index]["bt"] = sides[2]
        self.ref[index]["bb"] = sides[3]

        # Sorting Items
        c_w = Trig_2D_Points_Distance(clip[0][0], clip[0][1], clip[1][0], clip[1][1])
        c_h = Trig_2D_Points_Distance(clip[0][0], clip[0][1], clip[3][0], clip[3][1])
        self.ref[index]["perimeter"] = (2 * c_w) + (2 * c_h)
        self.ref[index]["area"] = c_w * c_h

        # Update
        self.update()
    def Pixmap_Edit(self, index):
        # Read Operations
        path = self.ref[index]["path"]
        egs = self.ref[index]["egs"]
        efx = self.ref[index]["efx"]
        efy = self.ref[index]["efy"]
        cl = self.ref[index]["cl"]
        cr = self.ref[index]["cr"]
        ct = self.ref[index]["ct"]
        cb = self.ref[index]["cb"]

        # Post Edit Guide Update
        if efx == False:
            g_esq = cl
        else:
            g_esq = 1 - cr
        if efy == False:
            g_top = ct
        else:
            g_top = 1 - cb
        g_wid = abs(cr - cl)
        g_hei = abs(cb - ct)

        # Update Pixmap to crop
        qimage_edit = QImage(path)

        # Operation Greyscale
        if egs == True:
            qimage_edit = qimage_edit.convertToFormat(24)
        # Operation Mirror
        if (efx == True or efy == True):
            qimage_edit = qimage_edit.mirrored(efx, efy)
        # Rotation
        qimage_edit = qimage_edit.transformed(
            QTransform().rotate(self.ref[index]["ro"],  Qt.ZAxis),
            Qt.SmoothTransformation
            )

        # Apply Pixmap to rendering list
        qpixmap = QPixmap().fromImage(qimage_edit)
        self.ref[index]["qpixmap"] = qpixmap
        self.update()
    def Pixmap_Zoom(self, bool, qpixmap):
        self.pin_zoom["bool"] = bool
        self.pin_zoom["qpixmap"] = qpixmap
        self.update()

    # Camera Operations
    def Camera_Pan(self, event):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Move all
        for i in range(0, len(self.ref)):
            # Read
            dw = self.ref[i]["dw"]
            dh = self.ref[i]["dh"]
            rx = self.ref[i]["rx"]
            ry = self.ref[i]["ry"]
            # Calculations
            n_ox = ex - rx
            n_oy = ey - ry
            # Write
            self.ref[i]["ox"] = n_ox
            self.ref[i]["oy"] = n_oy
            self.ref[i]["dx"] = n_ox - (dw * 0.5)
            self.ref[i]["dy"] = n_oy - (dh * 0.5)
            self.ref[i]["dxw"] = n_ox + (dw * 0.5)
            self.ref[i]["dyh"] = n_oy + (dh * 0.5)
            # Bounding Box
            pints, sides = self.Clip_Construct(i)
            self.ref[i]["bl"] = sides[0]
            self.ref[i]["br"] = sides[1]
            self.ref[i]["bt"] = sides[2]
            self.ref[i]["bb"] = sides[3]
        self.update()
    def Camera_Scale(self, event, pivot_x, pivot_y, value):
        # Event Mouse
        self.camera_relative = event.y()

        # Scale all
        for i in range(0, len(self.ref)):
            # Read
            ox = self.ref[i]["ox"]
            oy = self.ref[i]["oy"]
            rn = self.ref[i]["rn"]
            ro = self.ref[i]["ro"]
            sr = self.ref[i]["sr"]
            dx = self.ref[i]["dx"]
            dy = self.ref[i]["dy"]
            dw = self.ref[i]["dw"]
            dh = self.ref[i]["dh"]
            dxw = self.ref[i]["dxw"]
            dyh = self.ref[i]["dyh"]
            bl = self.ref[i]["bl"]
            br = self.ref[i]["br"]
            bt = self.ref[i]["bt"]
            bb = self.ref[i]["bb"]

            # Calculations
            n_ox = self.camera_scale[i]["ox"] + (-pivot_x + self.camera_scale[i]["ox"]) * value
            n_oy = self.camera_scale[i]["oy"] + (-pivot_y + self.camera_scale[i]["oy"]) * value
            n_dx = self.camera_scale[i]["dx"] + (-pivot_x + self.camera_scale[i]["dx"]) * value
            n_dy = self.camera_scale[i]["dy"] + (-pivot_y + self.camera_scale[i]["dy"]) * value
            n_dxw = self.camera_scale[i]["dxw"] + (-pivot_x + self.camera_scale[i]["dxw"]) * value
            n_dyh = self.camera_scale[i]["dyh"] + (-pivot_y + self.camera_scale[i]["dyh"]) * value
            n_dw = abs(n_dxw - n_dx)
            n_dh = abs(n_dyh - n_dy)
            n_bl = self.camera_scale[i]["bl"] + (-pivot_x + self.camera_scale[i]["bl"]) * value
            n_br = self.camera_scale[i]["br"] + (-pivot_x + self.camera_scale[i]["br"]) * value
            n_bt = self.camera_scale[i]["bt"] + (-pivot_y + self.camera_scale[i]["bt"]) * value
            n_bb = self.camera_scale[i]["bb"] + (-pivot_y + self.camera_scale[i]["bb"]) * value
            n_ss = Trig_2D_Points_Distance(n_dx, n_dy, n_ox, n_oy) * sr

            # Write
            self.ref[i]["ox"] = n_ox
            self.ref[i]["oy"] = n_oy
            self.ref[i]["dx"] = n_dx
            self.ref[i]["ss"] = n_ss
            self.ref[i]["dy"] = n_dy
            self.ref[i]["dw"] = n_dw
            self.ref[i]["dh"] = n_dh
            self.ref[i]["dxw"] = n_dxw
            self.ref[i]["dyh"] = n_dyh
            self.ref[i]["bl"] = n_bl
            self.ref[i]["br"] = n_br
            self.ref[i]["bt"] = n_bt
            self.ref[i]["bb"] = n_bb

        # Update
        self.update()

    # Clip
    def Clip_Construct(self, index):
        # Read
        ox = self.ref[index]["ox"]
        oy = self.ref[index]["oy"]
        rn = self.ref[index]["rn"]
        ro = self.ref[index]["ro"]
        ss = self.ref[index]["ss"]
        cl = self.ref[index]["cl"]
        cr = self.ref[index]["cr"]
        ct = self.ref[index]["ct"]
        cb = self.ref[index]["cb"]

        # Clip Mask
        tl_0x, tl_0y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(+ rn + ro      , 360) ) # top + left
        tr_0x, tr_0y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(- rn + ro + 180, 360) ) # top + right
        br_0x, br_0y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(+ rn + ro - 180, 360) ) # bot + right
        bl_0x, bl_0y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(- rn + ro      , 360) ) # bot + left

        tl_1x, tl_1y = Lerp_2D(cl, tl_0x, tl_0y, tr_0x, tr_0y)
        tr_1x, tr_1y = Lerp_2D(cr, tl_0x, tl_0y, tr_0x, tr_0y)
        br_1x, br_1y = Lerp_2D(cr, bl_0x, bl_0y, br_0x, br_0y)
        bl_1x, bl_1y = Lerp_2D(cl, bl_0x, bl_0y, br_0x, br_0y)

        tl_2x, tl_2y = Lerp_2D(ct, tl_1x, tl_1y, bl_1x, bl_1y)
        tr_2x, tr_2y = Lerp_2D(ct, tr_1x, tr_1y, br_1x, br_1y)
        br_2x, br_2y = Lerp_2D(cb, tr_1x, tr_1y, br_1x, br_1y)
        bl_2x, bl_2y = Lerp_2D(cb, tl_1x, tl_1y, bl_1x, bl_1y)

        esq = min(tl_2x, tr_2x, br_2x, bl_2x)
        dir = max(tl_2x, tr_2x, br_2x, bl_2x)
        top = min(tl_2y, tr_2y, br_2y, bl_2y)
        bot = max(tl_2y, tr_2y, br_2y, bl_2y)

        # Calculations
        clip = [
            [tl_2x, tl_2y],
            [tr_2x, tr_2y],
            [br_2x, br_2y],
            [bl_2x, bl_2y],
            ]
        sides = [esq, dir, top, bot]
        return clip, sides

    # Drag and Drop Event
    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent(self, event):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent(self, event):
        if event.mimeData().hasImage:
            self.drop = False
            event.setDropAction(Qt.CopyAction)
            mime_paths = []
            if (self.origin_x == 0 and self.origin_y == 0): # Denys from recieving from self.
                mime_data = event_drop(self, event)
                for i in range(0, len(mime_data)):
                    self.Pin_Drop(mime_data[i][1])
            event.accept()
        else:
            event.ignore()
        self.Board_Save()
        self.update()

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        self.Active_Clear()
        self.Board_Save()
        self.update()

    # Painter
    def paintEvent(self, event):
        # Theme
        krita_theme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # No References
        if (len(self.ref) == 0 and self.drop == False):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color1)))
            if self.widget_width < self.widget_height:
                side = self.widget_width
            else:
                side = self.widget_height
            w2 = self.widget_width * 0.5
            h2 = self.widget_height * 0.5
            poly_quad = QPolygon([
                QPoint(w2 - (0.2*side), h2 - (0.2*side)),
                QPoint(w2 + (0.2*side), h2 - (0.2*side)),
                QPoint(w2 + (0.2*side), h2 + (0.2*side)),
                QPoint(w2 - (0.2*side), h2 + (0.2*side)),
                ])
            painter.drawPolygon(poly_quad)

        # Images
        painter.setBrush(QtCore.Qt.NoBrush)
        for i in range(0, len(self.ref)):
            # Read
            path = self.ref[i]["path"]
            qpixmap = self.ref[i]["qpixmap"]
            ox = self.ref[i]["ox"]
            oy = self.ref[i]["oy"]
            ro = self.ref[i]["ro"]
            ss = self.ref[i]["ss"]
            dx = self.ref[i]["dx"]
            dy = self.ref[i]["dy"]
            dw = self.ref[i]["dw"]
            dh = self.ref[i]["dh"]
            dxw = self.ref[i]["dxw"]
            dyh = self.ref[i]["dyh"]
            cl = self.ref[i]["cl"]
            cr = self.ref[i]["cr"]
            ct = self.ref[i]["ct"]
            cb = self.ref[i]["cb"]
            bl = self.ref[i]["bl"]
            br = self.ref[i]["br"]
            bt = self.ref[i]["bt"]
            bb = self.ref[i]["bb"]

            # Clip Mask
            clip, sides = self.Clip_Construct(i)
            square = QPainterPath()
            square.moveTo(clip[0][0], clip[0][1])
            square.lineTo(clip[1][0], clip[1][1])
            square.lineTo(clip[2][0], clip[2][1])
            square.lineTo(clip[3][0], clip[3][1])
            painter.setClipPath(square)

            # Draw Image
            if qpixmap == None:
                qpixmap = QPixmap(path)
            if qpixmap.isNull() == False:
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawPixmap(dx, dy, qpixmap.scaled(dw, dh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)
            else:
                painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
                painter.drawLine(dx,  dy,  dxw, dy)
                painter.drawLine(dxw, dy,  dxw, dyh)
                painter.drawLine(dxw, dyh, dx,  dyh)
                painter.drawLine(dx,  dyh, dx,  dy)
                painter.drawLine(dx,  dy,  dxw, dyh)
                painter.drawLine(dx,  dyh, dxw, dy)

        # Selection
        painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
        painter.setBrush(QtCore.Qt.NoBrush)
        len_ref = len(self.ref)
        hor = []
        ver = []
        count = 0
        for i in range(0, len_ref):
            if (self.ref[i]["active"] == True or self.ref[i]["select"] == True):
                hor.append(self.ref[i]["bl"])
                hor.append(self.ref[i]["br"])
                ver.append(self.ref[i]["bt"])
                ver.append(self.ref[i]["bb"])
                count += 1
        if count >= 1:
            # Square Around
            min_x = min(hor)
            min_y = min(ver)
            max_x = max(hor)
            max_y = max(ver)
            painter.drawRect(min_x, min_y, max_x-min_x, max_y-min_y)
            # Dots Over
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(self.color1, Qt.Dense7Pattern))
            for i in range(0, len_ref):
                if self.ref[i]["select"] == True:
                    bl = self.ref[i]["bl"]
                    br = self.ref[i]["br"]
                    bt = self.ref[i]["bt"]
                    bb = self.ref[i]["bb"]
                    bw = abs(br - bl)
                    bh = abs(bb - bt)
                    painter.drawRect(bl, bt, bw, bh)

        # Active Nodes
        if (self.index != None and self.ref[self.index]["active"] == True):
            # Variables
            ox = self.ref[self.index]["ox"]
            oy = self.ref[self.index]["oy"]
            ro = self.ref[self.index]["ro"]
            ss = self.ref[self.index]["ss"]
            dx = self.ref[self.index]["dx"]
            dy = self.ref[self.index]["dy"]
            dw = self.ref[self.index]["dw"]
            dh = self.ref[self.index]["dh"]
            dxw = self.ref[self.index]["dxw"]
            dyh = self.ref[self.index]["dyh"]
            cl = self.ref[self.index]["cl"]
            cr = self.ref[self.index]["cr"]
            ct = self.ref[self.index]["ct"]
            cb = self.ref[self.index]["cb"]
            bl = self.ref[self.index]["bl"]
            br = self.ref[self.index]["br"]
            bt = self.ref[self.index]["bt"]
            bb = self.ref[self.index]["bb"]
            ww = abs(br - bl)
            hh = abs(bb - bt)
            w2 = ww * 0.5
            h2 = hh * 0.5

            # Bounding Box
            painter.setPen(QPen(self.color2, 1, Qt.SolidLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(bl, bt, ww, hh)

            # Triangle
            minimal_triangle = 20
            if (ww > minimal_triangle and hh > minimal_triangle):
                tri = 10
                # Scale 1
                if self.node == 1:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt1 = QPolygon([QPoint(bl, bt), QPoint(bl + tri, bt), QPoint(bl, bt + tri),])
                painter.drawPolygon(polyt1)
                # scale 3
                if self.node == 3:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt3 = QPolygon([QPoint(br, bt), QPoint(br, bt + tri), QPoint(br - tri, bt),])
                painter.drawPolygon(polyt3)
                # Scale 7
                if self.node == 7:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt7 = QPolygon([QPoint(bl, bb), QPoint(bl, bb - tri), QPoint(bl + tri, bb),])
                painter.drawPolygon(polyt7)
                # Scale 9
                if self.node == 9:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt9 = QPolygon([QPoint(br, bb), QPoint(br - tri, bb), QPoint(br, bb - tri),])
                painter.drawPolygon(polyt9)

            # Squares
            minimal_square = 50
            if (ww > minimal_square and hh > minimal_square):
                sq = 5
                # Clip 2
                if self.node == 2:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl+w2-sq, bt), QPoint(bl+w2-sq, bt+sq), QPoint(bl+w2+sq, bt+sq), QPoint(bl+w2+sq, bt),])
                painter.drawPolygon(polys2)
                # Clip 4
                if self.node == 4:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl, bt+h2-sq), QPoint(bl+sq, bt+h2-sq), QPoint(bl+sq, bt+h2+sq), QPoint(bl, bt+h2+sq),])
                painter.drawPolygon(polys2)
                # Clip 6
                if self.node == 6:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(br, bt+h2-sq), QPoint(br-sq, bt+h2-sq), QPoint(br-sq, bt+h2+sq), QPoint(br, bt+h2+sq),])
                painter.drawPolygon(polys2)
                # Clip 8
                if self.node == 8:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl+w2-sq, bb), QPoint(bl+w2-sq, bb-sq), QPoint(bl+w2+sq, bb-sq), QPoint(bl+w2+sq, bb),])
                painter.drawPolygon(polys2)

            # Circle
            minimal_cicle = 30
            if (ww > minimal_cicle and hh > minimal_cicle):
                cir = 4
                # Clip 5
                if self.node == 5:
                    painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                    cir_x, cir_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(ro+90, 360) )
                    neu_x, neu_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(90, 360) )
                    painter.drawLine(ox, oy, cir_x, cir_y)
                    painter.drawLine(ox, oy, neu_x, neu_y)
                    painter.drawEllipse(ox-cir, oy-cir, 2*cir, 2*cir)
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                    painter.drawEllipse(bl+w2-cir, bt+h2-cir, 2*cir, 2*cir)

        # Image Zoom
        if self.pin_zoom["bool"] == True:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.NoPen)
            qpixmap = self.pin_zoom["qpixmap"]
            if qpixmap.isNull() == False:
                ww = self.widget_width
                wh = self.widget_height
                qpixmap_scaled = qpixmap.scaled(ww, wh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pw = qpixmap_scaled.width()
                ph = qpixmap_scaled.height()
                painter.drawPixmap((ww/2)-(pw/2), (wh/2)-(ph/2), qpixmap_scaled)

        # Selection Square
        check = (self.sel_l == 0 and self.sel_r == 0 and self.sel_t == 0 and self.sel_b == 0)
        if check == False:
            painter.setPen(QPen(self.color1, 2, Qt.SolidLine))
            painter.setBrush(QBrush(self.color1, Qt.Dense7Pattern))
            min_x = min(self.origin_x, self.sel_l, self.sel_r)
            max_x = max(self.origin_x, self.sel_l, self.sel_r)
            min_y = min(self.origin_y, self.sel_t, self.sel_b)
            max_y = max(self.origin_y, self.sel_t, self.sel_b)
            ww = max_x - min_x
            hh = max_y - min_y
            painter.drawRect(min_x, min_y, ww, hh)

        # Drag and Drop
        if self.drop == True:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color1)))
            if self.widget_width < self.widget_height:
                side = self.widget_width
            else:
                side = self.widget_height
            w2 = self.widget_width * 0.5
            h2 = self.widget_height * 0.5
            poly_tri = QPolygon([
                QPoint(w2 - (0.3*side), h2 - (0.2*side)),
                QPoint(w2 + (0.3*side), h2 - (0.2*side)),
                QPoint(w2, h2 + (0.2*side)),
                ])
            painter.drawPolygon(poly_tri)

#//
#\\ Settings ###################################################################
class Menu_Mode(QWidget):
    SIGNAL_MODE = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(Menu_Mode, self).__init__(parent)
        # Menu Mode
        self.menu_index = 0
        self.widget_height = 25
        # QIcons
        self.icon_prev = Krita.instance().icon('folder-pictures')
        self.icon_grid = Krita.instance().icon('gridbrush')
        self.icon_refe = Krita.instance().icon('zoom-fit')
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    def Set_Mode(self, menu_index):
        self.menu_index = menu_index

    def mousePressEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            # Menu
            cmenu = QMenu(self)
            # Actions
            cmenu_preview   = cmenu.addAction("Preview")
            cmenu_grid      = cmenu.addAction("Grid")
            cmenu_reference = cmenu.addAction("Reference")
            # Icons
            cmenu_preview.setIcon(self.icon_prev)
            cmenu_grid.setIcon(self.icon_grid)
            cmenu_reference.setIcon(self.icon_refe)

            # Execute
            position = self.mapToGlobal( QPoint( self.x(), self.y()+self.widget_height ) )
            action = cmenu.exec_(position)
            # Triggers
            if action == cmenu_preview:
                self.Emit_Signal(0)
            elif action == cmenu_grid:
                self.Emit_Signal(1)
            elif action == cmenu_reference:
                self.Emit_Signal(2)

    def wheelEvent(self, event):
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            delta_y = delta.y()
            value = 0
            if delta_y > 20:
                value = -1
            if delta_y < -20:
                value = 1
            if (value == -1 or value == 1):
                self.Emit_Signal( Limit_Range(self.menu_index + value, 0, 2) )

    def Emit_Signal(self, value):
        self.menu_index = value
        self.SIGNAL_MODE.emit(value)
class OS_Folders(QWidget):
    SIGNAL_PATH = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(OS_Folders, self).__init__(parent)
        self.directory = ""
        self.folders = []
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    def Set_Directory(self, directory):
        # Directory
        self.directory = directory
        # Folders with in Directory
        dirfiles = os.listdir(directory)
        fullpaths = map(lambda name: os.path.join(directory, name), dirfiles)
        self.folders = []
        for file in fullpaths:
            if os.path.isdir(file):
                self.folders.append(file)
        if len(self.folders) > 0:
            self.folders.sort()

    def contextMenuEvent(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            # Menu
            cmenu = QMenu(self)
            position = self.mapToGlobal(event.pos())
            # Paths
            current = self.directory
            # Width
            len_current = 8 * len(current)
            cmenu.setMinimumWidth(len_current)
            # Actions
            parent = "... " + str(os.path.basename(os.path.dirname(self.directory)))
            cmenu.addSection(current)
            cmenu_parent = cmenu.addAction(parent)
            cmenu.addSection(" ")
            actions = {}
            for i in range(0, len(self.folders)):
                string = "\ " + str(os.path.basename(self.folders[i]))
                actions[i] = cmenu.addAction( string )
            # Execute
            action = cmenu.exec_(position)
            # Triggers
            path = None
            if action == cmenu_parent:
                path = os.path.dirname(self.directory)
            for i in range(0, len(self.folders)):
                if action == actions[i]:
                    path = str(self.folders[i])
                    break
            # Emit
            if path != None:
                self.SIGNAL_PATH.emit(path)

class Dialog_UI(QDialog):
    def __init__(self, parent):
        super(Dialog_UI, self).__init__(parent)
        self.dir_name = str(os.path.dirname(os.path.realpath(__file__)))
        uic.loadUi(self.dir_name + "/imagine_board_settings.ui", self)

#//
