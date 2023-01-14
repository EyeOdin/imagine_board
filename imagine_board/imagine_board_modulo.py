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
# Python
import math
import os
import zipfile
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Imagine Board
from .imagine_board_calculations import *
#endregion
#region Global Variables ###########################################################
file_compress = [
    "zip",
    ]
decimas = 10
#endregion


#region Function ###################################################################
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
    # # data_image = mimedata.imageData()
    # data_color = mimedata.colorData()

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
        # Construct
        for i in range(0, len_urls):
            path_i = data_urls[i].toLocalFile()
            text_i = os.path.basename( path_i ) # Local Basename
            urls_i = os.path.normpath( path_i ) # Local File
            mime_data.append([text_i, urls_i])
        mime_data.sort()
    # Return
    return mime_data
def insert_bool(self):
    doc = Krita.instance().documents()
    if len(doc) != 0:
        insert = True
    else:
        insert = False
    return insert

def Pixmap_Move_BB(self, lista, index, input_x, input_y):
    # Read
    ox = lista[index]["ox"]
    oy = lista[index]["oy"]
    dx = lista[index]["dx"]
    dy = lista[index]["dy"]
    dw = lista[index]["dw"]
    dh = lista[index]["dh"]
    dxw = lista[index]["dxw"]
    dyh = lista[index]["dyh"]
    bl = lista[index]["bl"]
    br = lista[index]["br"]
    bt = lista[index]["bt"]
    bb = lista[index]["bb"]
    bw = abs(br - bl)
    bh = abs(bb - bt)

    # Calculations
    n_ox = input_x + (ox - bl)
    n_oy = input_y + (oy - bt)
    n_dx = input_x + (dx - bl)
    n_dy = input_y + (dy - bt)
    n_dxw = input_x + (dxw - bl)
    n_dyh = input_y + (dyh - bt)
    n_bl = input_x
    n_br = input_x + bw
    n_bt = input_y
    n_bb = input_y + bh

    # Write
    lista[index]["ox"] = round(n_ox, decimas)
    lista[index]["oy"] = round(n_oy, decimas)
    lista[index]["dx"] = round(n_dx, decimas)
    lista[index]["dy"] = round(n_dy, decimas)
    lista[index]["dxw"] = round(n_dxw, decimas)
    lista[index]["dyh"] = round(n_dyh, decimas)

    lista[index]["bl"] = round(n_bl, decimas)
    lista[index]["br"] = round(n_br, decimas)
    lista[index]["bt"] = round(n_bt, decimas)
    lista[index]["bb"] = round(n_bb, decimas)

    return
def Pixmap_Box(self, lista):
    # Variables
    hor = []
    ver = []
    count = 0
    # Create Values
    for i in range(0, len(lista)):
        bl = lista[i]["bl"]
        br = lista[i]["br"]
        bt = lista[i]["bt"]
        bb = lista[i]["bb"]
        hor.append(bl)
        hor.append(br)
        ver.append(bt)
        ver.append(bb)
        count += 1
    if count >= 1:
        # Square Around
        min_x = min(hor)
        min_y = min(ver)
        max_x = max(hor)
        max_y = max(ver)
        delta_x = abs(max_x - min_x)
        delta_y = abs(max_y - min_y)
        perimeter = (2*delta_x) + (2*delta_y)
        area = delta_x * delta_y
        ratio = delta_x / delta_y
    # Return
    box = {
        "min_x" : min_x,
        "min_y" : min_y,
        "max_x" : max_x,
        "max_y" : max_y,
        "perimeter" : perimeter,
        "area" : area,
        "ratio" : ratio,
        }
    return box
def Clip_Construct(self, lista, index):
    # Read
    ox = lista[index]["ox"]
    oy = lista[index]["oy"]
    rn = lista[index]["rn"]
    ro = lista[index]["ro"]
    ss = lista[index]["ss"]
    cl = lista[index]["cl"]
    cr = lista[index]["cr"]
    ct = lista[index]["ct"]
    cb = lista[index]["cb"]

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
    der = max(tl_2x, tr_2x, br_2x, bl_2x)
    top = min(tl_2y, tr_2y, br_2y, bl_2y)
    bot = max(tl_2y, tr_2y, br_2y, bl_2y)

    # Calculations
    clip = [
        [tl_2x, tl_2y],
        [tr_2x, tr_2y],
        [br_2x, br_2y],
        [bl_2x, bl_2y],
        ]
    sides = [esq, der, top, bot]
    return clip, sides

#endregion
#region Panels #####################################################################
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
    SIGNAL_PIN_PATH = QtCore.pyqtSignal(dict)
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
        self.color_1 = QColor("#ffffff")
        self.color_2 = QColor("#000000")
        self.color_alpha = QColor(0,0,0,50)
        self.origin_ref = 100
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
        self.clip_index = None
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
    def Set_Theme(self, color_1, color_2):
        self.color_1 = color_1
        self.color_2 = color_2

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
            if frames == 1:
                self.Set_QPixmap_Preview(path)
            else:
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
        else:
            self.Set_QPixmap_Preview(path)
    def Set_Comp_Preview(self, path, name_list):
        # On Windows, if path is inside a protected folder this will crash Krita instantly when using OS_Folders path
        try:
            # Reset
            self.Set_Reset()
            self.is_null = False
            # Variables
            self.path = path

            # Variables
            self.is_compressed = True
            self.name_list = name_list
            self.comp_index = 0

            # Zip File
            self.archive = zipfile.ZipFile(path, "r")
            self.qpixmap = self.Comp_QPixmap(self.archive, self.name_list, self.comp_index)

            self.update()
        except:
            self.Set_Default()
    def Set_Unpress(self):
        self.press = False
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
        if (self.archive != None and len(self.name_list) > 0):
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
    def Clip_Click(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            # Preview Fix
            self.Preview_Reset(False)
            # Point of event
            ex = event.x()
            ey = event.y()
            # Mouse to Points Distances
            dist1 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p1_per[0] * self.scaled_width),self.offset_y + (self.clip_p1_per[1] * self.scaled_height), ex,ey)
            dist2 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p2_per[0] * self.scaled_width),self.offset_y + (self.clip_p2_per[1] * self.scaled_height), ex,ey)
            dist3 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p3_per[0] * self.scaled_width),self.offset_y + (self.clip_p3_per[1] * self.scaled_height), ex,ey)
            dist4 = Trig_2D_Points_Distance(self.offset_x + (self.clip_p4_per[0] * self.scaled_width),self.offset_y + (self.clip_p4_per[1] * self.scaled_height), ex,ey)
            dist = [dist1, dist2, dist3, dist4]
            dist_min = min(dist)
            if dist_min < 20:
                self.clip_index = dist.index(dist_min)
            # Lists
            point_x = self.clip_p1_per[0]
            point_y = self.clip_p1_per[1]
            self.width_per = self.clip_p2_per[0] - self.clip_p1_per[0]
            self.height_per = self.clip_p4_per[1] - self.clip_p1_per[1]
            list = [
                self.clip_state,
                point_x * self.image_width,
                point_y * self.image_height,
                self.width_per * self.image_width,
                self.height_per * self.image_height
                ]
            self.SIGNAL_CLIP.emit(list)
            self.update()
    def Clip_Move(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
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
            # Interaction
            limit = 0.01
            if self.clip_index == 0:
                if per_x > (self.clip_p2_per[0] - limit):
                    per_x = self.clip_p2_per[0] - limit
                if per_y > (self.clip_p4_per[1] - limit):
                    per_y = self.clip_p4_per[1] - limit
                self.clip_p1_per = [per_x, per_y]
                self.clip_p2_per[1] = per_y
                self.clip_p4_per[0] = per_x
            if self.clip_index == 1:
                if per_x < (self.clip_p1_per[0] + limit):
                    per_x = self.clip_p1_per[0] + limit
                if per_y > (self.clip_p3_per[1] - limit):
                    per_y = self.clip_p3_per[1] - limit
                self.clip_p2_per = [per_x, per_y]
                self.clip_p3_per[0] = per_x
                self.clip_p1_per[1] = per_y
            if self.clip_index == 2:
                if per_x < (self.clip_p4_per[0] + limit):
                    per_x = self.clip_p4_per[0] + limit
                if per_y < (self.clip_p2_per[1] + limit):
                    per_y = self.clip_p2_per[1] + limit
                self.clip_p3_per = [per_x, per_y]
                self.clip_p4_per[1] = per_y
                self.clip_p2_per[0] = per_x
            if self.clip_index == 3:
                if per_x > (self.clip_p3_per[0] - limit):
                    per_x = self.clip_p3_per[0] - limit
                if per_y < (self.clip_p1_per[1] + limit):
                    per_y = self.clip_p1_per[1] + limit
                self.clip_p4_per = [per_x, per_y]
                self.clip_p1_per[0] = per_x
                self.clip_p3_per[1] = per_y
            # Lists
            point_x = self.clip_p1_per[0]
            point_y = self.clip_p1_per[1]
            self.width_per = self.clip_p2_per[0] - self.clip_p1_per[0]
            self.height_per = self.clip_p4_per[1] - self.clip_p1_per[1]
            list = [
                self.clip_state,
                point_x * self.image_width,
                point_y * self.image_height,
                self.width_per * self.image_width,
                self.height_per * self.image_height
                ]
            self.SIGNAL_CLIP.emit(list)
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
            self.Clip_Click(event)
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
            self.Clip_Move(event)
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
        self.clip_index = None
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
        br = QPoint(self.widget_width, self.widget_height )
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
        cmenu_location = cmenu.addAction("File Location")
        cmenu.addSeparator()
        cmenu_random = cmenu.addAction("Random Index")
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
            cmenu_anim_current_frame = cmenu.addAction("Export Current Frame")
            cmenu_anim_all_frames = cmenu.addAction("Export All Frames")
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
        if is_compressed == False:
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
                pin = {"path" : self.path, "text" : None, "origin_x": self.origin_ref, "origin_y": self.origin_ref}
                self.SIGNAL_PIN_PATH.emit(pin)
        if action == cmenu_location:
            self.SIGNAL_LOCATION.emit(self.path)
        if action == cmenu_random:
            self.Preview_Reset(True)
            self.Clip_Off()
            self.SIGNAL_RANDOM.emit(0)
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
            if action == cmenu_anim_current_frame:
                self.Anim_Frame_Save(self.frame_value)
            if action == cmenu_anim_all_frames:
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
        if is_compressed == False:
            if action == cmenu_document:
                self.SIGNAL_NEW_DOCUMENT.emit(self.path)
            if insert == True:
                if action == cmenu_insert_layer:
                    self.SIGNAL_INSERT_LAYER.emit(self.path)
                if action == cmenu_insert_ref:
                    self.SIGNAL_INSERT_REFERENCE.emit(self.path)

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
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(self.color_alpha))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Display Pixmap
        if (self.is_null == True or (self.qpixmap.isNull() == True and self.is_animation == False and self.drop == False)):
            self.Image_Default(painter)
        else:
            self.Image_Calculations()
            painter.save()
            painter.translate(self.offset_x, self.offset_y)
            painter.scale(self.size * self.zoom, self.size * self.zoom)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtCore.Qt.NoBrush)
            if self.is_animation == True:
                qpixmap = self.anim_sequence[self.frame_value]
                painter.drawPixmap(0,0,qpixmap)
            else:
                qpixmap = self.qpixmap
                painter.drawPixmap(0,0,qpixmap)
            # Clip Area
            if self.clip_state == True:
                # Area to hide
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(self.color_alpha))
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
                painter.setPen(QPen(self.color_2, 2, Qt.SolidLine))
                painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                tri = 15
                poly1 = QPolygon([
                    QPoint( int(self.image_width * self.clip_p1_per[0]),       int(self.image_height * self.clip_p1_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p1_per[0] + tri), int(self.image_height * self.clip_p1_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p1_per[0]),       int(self.image_height * self.clip_p1_per[1] + tri) ),
                    ])
                poly2 = QPolygon([
                    QPoint( int(self.image_width * self.clip_p2_per[0]),       int(self.image_height * self.clip_p2_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p2_per[0]),       int(self.image_height * self.clip_p2_per[1] + tri) ),
                    QPoint( int(self.image_width * self.clip_p2_per[0] - tri), int(self.image_height * self.clip_p2_per[1]) ),
                    ])
                poly3 = QPolygon([
                    QPoint( int(self.image_width * self.clip_p3_per[0]),       int(self.image_height * self.clip_p3_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p3_per[0] - tri), int(self.image_height * self.clip_p3_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p3_per[0]),       int(self.image_height * self.clip_p3_per[1] - tri) ),
                    ])
                poly4 = QPolygon([
                    QPoint( int(self.image_width * self.clip_p4_per[0]),       int(self.image_height * self.clip_p4_per[1]) ),
                    QPoint( int(self.image_width * self.clip_p4_per[0]),       int(self.image_height * self.clip_p4_per[1] - tri) ),
                    QPoint( int(self.image_width * self.clip_p4_per[0] + tri), int(self.image_height * self.clip_p4_per[1]) ),
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
            painter.setBrush(QBrush(QColor(self.color_1)))
            if self.origin_y < (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint( int(self.widget_width*0.50), int(self.widget_height*0.05) ),
                    QPoint( int(self.widget_width*0.45), int(self.widget_height*0.10) ),
                    QPoint( int(self.widget_width*0.55), int(self.widget_height*0.10) )
                    ])
            elif self.origin_y > (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint( int(self.widget_width*0.50), int(self.widget_height*0.95) ),
                    QPoint( int(self.widget_width*0.45), int(self.widget_height*0.90) ),
                    QPoint( int(self.widget_width*0.55), int(self.widget_height*0.90) )
                    ])
            painter.drawPolygon(arrow)

        # Drag and Drop
        if self.drop == True:
            check = (self.origin_x == 0 and self.origin_y == 0)
            if check == True:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color_1)))
                if self.widget_width < self.widget_height:
                    side = self.widget_width
                else:
                    side = self.widget_height
                w2 = self.widget_width * 0.5
                h2 = self.widget_height * 0.5
                poly_tri = QPolygon([
                    QPoint( int(w2 - 0.3*side), int(h2 - 0.2*side)),
                    QPoint( int(w2 + 0.3*side), int(h2 - 0.2*side)),
                    QPoint( int(w2),            int(h2 + 0.2*side) ),
                    ])
                painter.drawPolygon(poly_tri)

        # Color Picker
        if (self.pick_color == True and self.origin_x != 0 and self.origin_y != 0):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor( int(self.red*self.range), int(self.green*self.range), int(self.blue*self.range) )))
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
    def Image_Default(self, painter):
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_1)))
        if self.widget_width < self.widget_height:
            side = self.widget_width
        else:
            side = self.widget_height
        w2 = self.widget_width * 0.5
        h2 = self.widget_height * 0.5
        painter.drawEllipse( QRectF( w2 - (0.2*side), h2 - (0.2*side), 0.4*side, 0.4*side ) )

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
    SIGNAL_LOCATION = QtCore.pyqtSignal(str)
    SIGNAL_PIN_PATH = QtCore.pyqtSignal(dict)
    SIGNAL_NAME = QtCore.pyqtSignal(list)
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(ImagineBoard_Grid, self).__init__(parent)
        # Variables
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
        self.location = None
        self.origin_ref = 100
        # Colors
        self.color_1 = QColor("#ffffff")
        self.color_2 = QColor("#000000")
        self.color_alpha = QColor(0,0,0,50)
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
    def Set_Theme(self, color_1, color_2):
        self.color_1 = color_1
        self.color_2 = color_2

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
            # Functions
            self.location = self.Grid_Location(event)
            grid_path = self.Grid_Path(event)
            # Signals
            self.SIGNAL_NAME.emit(self.location)
            self.SIGNAL_NEUTRAL.emit(grid_path[0])

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

        # Update
        self.update()
    def mouseMoveEvent(self, event):
        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.location = self.Grid_Location(event)
            grid_path = self.Grid_Path(event)
            self.SIGNAL_NAME.emit(self.location)
            self.SIGNAL_NEUTRAL.emit(grid_path[0])

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

        # Update
        self.update()
    def mouseDoubleClickEvent(self, event):
        # Neutral
        if (event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton):
            self.location = self.Grid_Location(event)
            self.SIGNAL_PREVIEW.emit(self.location)

        # Update
        self.update()
    def mouseReleaseEvent(self, event):
        self.SIGNAL_NEUTRAL.emit("")
        self.press = False
        self.origin_x = 0
        self.origin_y = 0
        self.location = None
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
            cmenu_location = cmenu.addAction("File Location")
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
                    pin = {"path" : name_path[1], "text" : None, "origin_x": self.origin_ref, "origin_y": self.origin_ref}
                    self.SIGNAL_PIN_PATH.emit(pin)
            if action == cmenu_location:
                self.SIGNAL_LOCATION.emit(name_path[1])
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
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_alpha)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Dots (no results)
        if (self.images_found == False and self.drop == False):
            for h in range(0, self.grid_horz+1):
                for v in range(0, self.grid_vert+1):
                    px = h * self.tn_x
                    py = v * self.tn_y
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QBrush(QColor(self.color_1)))
                    if self.tn_x < self.tn_y:
                        side = self.tn_x
                    else:
                        side = self.tn_y
                    offset_x = (self.tn_x * 0.5) - (0.3 * side)
                    offset_y = (self.tn_y * 0.5) - (0.3 * side)
                    painter.drawEllipse( QRectF ( px + offset_x, py + offset_y, 0.6*side, 0.6*side ) )

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
                    # Alpha Background
                    if self.location == [ self.qpixmap_list[i][0], self.qpixmap_list[i][1] ]:
                        painter.setPen(QtCore.Qt.NoPen)
                        painter.setBrush(QBrush(QColor(self.color_1)))
                        painter.drawRect(0,0,self.widget_width,self.widget_height)
                    # Pixmap
                    render = qpixmap.scaled( int(self.tn_x+1), int(self.tn_y+1), self.display_ratio, self.tn_smooth_scale )
                    render_width = render.width()
                    render_height = render.height()
                    offset_x = (self.tn_x - render_width) * 0.5
                    offset_y = (self.tn_y - render_height) * 0.5
                    painter.drawPixmap( QPointF(px + offset_x, py + offset_y), render)
                else:
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QBrush(QColor(self.color_1)))
                    if self.tn_x < self.tn_y:
                        side = self.tn_x
                    else:
                        side = self.tn_y
                    offset_x = (self.tn_x * 0.5) - (0.3 * side)
                    offset_y = (self.tn_y * 0.5) - (0.3 * side)
                    painter.drawEllipse( QRectF( px + offset_x, py + offset_y, 0.6*side, 0.6*side ) )

        # Clean Mask
        painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)

        # Arrows
        if self.press == True:
            # Arrows
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color_1)))
            if self.origin_y < (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint( int(self.widget_width*0.50), int(self.widget_height*0.05) ),
                    QPoint( int(self.widget_width*0.45), int(self.widget_height*0.10) ),
                    QPoint( int(self.widget_width*0.55), int(self.widget_height*0.10) )
                    ])
            elif self.origin_y > (self.widget_height * 0.5):
                arrow = QPolygon([
                    QPoint( int(self.widget_width*0.50), int(self.widget_height*0.95) ),
                    QPoint( int(self.widget_width*0.45), int(self.widget_height*0.90) ),
                    QPoint( int(self.widget_width*0.55), int(self.widget_height*0.90) )
                    ])
            painter.drawPolygon(arrow)

        # Drag and Drop
        if self.drop == True:
            check = self.origin_x == 0 and self.origin_y == 0
            if check == True:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color_1)))
                if self.widget_width < self.widget_height:
                    side = self.widget_width
                else:
                    side = self.widget_height
                w2 = self.widget_width * 0.5
                h2 = self.widget_height * 0.5
                poly_tri = QPolygon([
                    QPoint( int(w2 - 0.3*side), int(h2 - 0.2*side)),
                    QPoint( int(w2 + 0.3*side), int(h2 - 0.2*side)),
                    QPoint( int(w2),            int(h2 + 0.2*side)),
                    ])
                painter.drawPolygon(poly_tri)

class ImagineBoard_Reference(QWidget):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    SIGNAL_DROP = QtCore.pyqtSignal(dict)
    # Reference
    SIGNAL_SAVE = QtCore.pyqtSignal(list)
    SIGNAL_UNDO = QtCore.pyqtSignal(list)
    SIGNAL_CLIP = QtCore.pyqtSignal(list)
    SIGNAL_TEXT = QtCore.pyqtSignal(dict)

    # Init
    def __init__(self, parent):
        super(ImagineBoard_Reference, self).__init__(parent)
        self.Variables()
    def Variables(self):
        # Widget
        self.widget_width = 1
        self.widget_height = 1
        self.w2 = 0.5
        self.h2 = 0.5

        # Colors
        self.color_1 = QColor("#ffffff")
        self.color_2 = QColor("#000000")
        self.color_shade = QColor(0,0,0,30)
        self.color_alpha = QColor(0,0,0,50)
        self.color_blue = QColor("#3daee9")
        self.color_highlight = QColor("#000032")

        # Events
        self.origin_x = 0
        self.origin_y = 0
        self.press = None
        self.drop = False

        # Pins
        self.origin_ref = 100
        self.pin_ref = []
        self.pin_index = None
        self.pin_node = None

        # Font
        self.font_type = "Tahoma"
        self.qfont = QFont(self.font_type, 15)
        self.text_default = "Text String"

        # Board
        self.limit_x = []
        self.limit_y = []
        self.pin_zoom = {"bool" : False, "qpixmap" : "",}

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
    def Set_Size_Corner(self, widget_width, widget_height):
        # Variables
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.w2 = widget_width * 0.5
        self.h2 = widget_height * 0.5
        self.update()
    def Set_Size_Middle(self, widget_width, widget_height):
        # # Reformat View
        w2 = widget_width * 0.5
        h2 = widget_height * 0.5

        if (self.widget_width != widget_width or self.widget_height != widget_height):
            delta_x = (widget_width - self.widget_width) * 0.5
            delta_y = (widget_height - self.widget_height) * 0.5
            for i in range(0, len(self.pin_ref)):
                Pixmap_Move_BB(self, self.pin_ref, i, self.pin_ref[i]["bl"] + delta_x, self.pin_ref[i]["bt"] + delta_y)

        # Variables
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.w2 = widget_width * 0.5
        self.h2 = widget_height * 0.5
        self.update()
    def Set_Theme(self, color_1, color_2):
        self.color_1 = color_1
        self.color_2 = color_2

    # Index
    def Index_Position(self, lista):
        for i in range(0, len(lista)):
            lista[i]["index"] = i
    def Index_Closest(self, event):
        # Event
        ex = event.x()
        ey = event.y()

        # Pin Images
        index_i = None
        if (self.pin_ref != [] and self.pin_ref != None):
            # Update Indexes
            self.Index_Position(self.pin_ref)

            # Make a Selection
            index_i = None
            # for i in range(0, len(self.pin_ref)):
            for i in range(len(self.pin_ref) - 1, -1, -1):
                ox = self.pin_ref[i]["ox"]
                oy = self.pin_ref[i]["oy"]
                bl = self.pin_ref[i]["bl"]
                br = self.pin_ref[i]["br"]
                bt = self.pin_ref[i]["bt"]
                bb = self.pin_ref[i]["bb"]
                if ((ex >= bl and ex <= br) and (ey >= bt and ey <= bb)): # Clicked inside
                    index_i = i
                    self.pin_ref[i]["rx"] = round(self.origin_x - ox, decimas)
                    self.pin_ref[i]["ry"] = round(self.origin_y - oy, decimas)
                    break
            # List
            if index_i != None:
                # List
                item = self.pin_ref.pop(i)
                self.pin_ref.append(item)
                self.Index_Position(self.pin_ref)
                # Variables
                self.pin_index = len(self.pin_ref) - 1
                self.pin_node = self.Index_Node(event, index_i)
            else:
                self.pin_index = None
                self.pin_node = 0

        # Relative Deltas
        self.Index_Deltas_Move(index_i)
    def Index_Deltas_Move(self, index):
        for i in range(0, len(self.pin_ref)):
            if i != index:
                self.pin_ref[i]["rx"] = round(self.origin_x - self.pin_ref[i]["ox"], decimas)
                self.pin_ref[i]["ry"] = round(self.origin_y - self.pin_ref[i]["oy"], decimas)
    def Index_Deltas_Scale(self):
        self.camera_scale = []
        for i in range(0, len(self.pin_ref)):
            self.camera_scale.append(self.pin_ref[i])
    def Index_Delta_Clean(self):
        for i in range(0, len(self.pin_ref)):
            self.pin_ref[i]["rx"] = 0
            self.pin_ref[i]["ry"] = 0
    def Index_Node(self, event, index):
        # Node Choice
        nodes = self.Index_Points(index)
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
        bl = self.pin_ref[index]["bl"]
        br = self.pin_ref[index]["br"]
        bt = self.pin_ref[index]["bt"]
        bb = self.pin_ref[index]["bb"]
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
        if self.pin_index != None:
            # X Axis
            self.limit_x = []
            for i in range(0, len(self.pin_ref)):
                if (i != self.pin_index and self.pin_ref[i]["select"] == False):
                    bl = self.pin_ref[i]["bl"]
                    br = self.pin_ref[i]["br"]
                    check_l = (bl >= 0 and bl <= self.widget_width)
                    check_r = (br >= 0 and br <= self.widget_width)
                    if (bl not in self.limit_x and check_l == True):
                        self.limit_x.append(bl)
                    if (br not in self.limit_x and check_r == True):
                        self.limit_x.append(br)
            # Y Axis
            self.limit_y = []
            for i in range(0, len(self.pin_ref)):
                if (i != self.pin_index and self.pin_ref[i]["select"] == False):
                    bt = self.pin_ref[i]["bt"]
                    bb = self.pin_ref[i]["bb"]
                    check_t = (bt >= 0 and bt <= self.widget_height)
                    check_b = (bb >= 0 and bb <= self.widget_height)
                    if (bt not in self.limit_y and check_t == True):
                        self.limit_y.append(bt)
                    if (bb not in self.limit_y and check_b == True):
                        self.limit_y.append(bb)

    # Active
    def Active_Select(self, index):
        self.Active_Clear()
        self.pin_ref[index]["active"] = True
        self.update()
    def Active_Clear(self):
        for i in range(0, len(self.pin_ref)):
            self.pin_ref[i]["active"] = False
        self.update()

    # Selection
    def Selection_Shift(self, index):
        self.pin_ref[index]["select"] = not self.pin_ref[index]["select"]
        self.Selection_Count()
        self.update()
    def Selection_Clear(self):
        for i in range(0, len(self.pin_ref)):
            self.pin_ref[i]["select"] = False
        self.Selection_Count()
        self.update()
    def Selection_Replace(self, index):
        self.Selection_Clear()
        self.pin_ref[index]["select"] = True
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
        for i in range(0, len(self.pin_ref)):
            bl = self.pin_ref[i]["bl"]
            br = self.pin_ref[i]["br"]
            bt = self.pin_ref[i]["bt"]
            bb = self.pin_ref[i]["bb"]
            check = (bl >= self.sel_l and br <= self.sel_r and bt >= self.sel_t and bb <= self.sel_b)
            self.pin_ref[i]["active"] = False
            if check == True:
                self.pin_ref[i]["select"] = True
            else:
                self.pin_ref[i]["select"] = False
        self.Selection_Count()
        self.update()
    def Selection_Count(self):
        self.selection_count = 0
        for i in range(0, len(self.pin_ref)):
            if self.pin_ref[i]["select"] == True:
                self.selection_count += 1
    def Selection_Delete(self):
        count = 0
        for i in range(0, len(self.pin_ref)):
            if self.pin_ref[i]["select"] == True:
                count += 1
        for i in range(0, count):
            for i in range(0, len(self.pin_ref)):
                if self.pin_ref[i]["select"] == True:
                    self.pin_ref.pop(i)
                    break
        self.pin_index = None
        self.update()
    def Selection_All(self):
        for i in range(0, len(self.pin_ref)):
            self.pin_ref[i]["select"] = True

    # Pins on the Board
    def Pin_Ref(self, pin):
        if pin["text"] == None: # Image
            pin["qpixmap"] = QPixmap(pin["path"])
            self.pin_ref.append(pin)
            index = len(self.pin_ref)-1
            self.Pixmap_Edit(index)
        else: # Text
            pis = pin["pis"]
            self.qfont.setPointSizeF(pis)
            self.pin_ref.append(pin)

        # Board
        self.Board_Save()
        self.modified = True
        self.update()
    def Pin_Drop(self, pin):
        self.SIGNAL_DROP.emit(pin)
        self.update()
    def Pin_Drag(self, index):
        # Calculations
        path = self.pin_ref[index]["path"]
        pixmap = QPixmap(path)
        width = pixmap.width()
        height = pixmap.height()
        cl = self.pin_ref[index]["cl"]
        cr = self.pin_ref[index]["cr"]
        ct = self.pin_ref[index]["ct"]
        cb = self.pin_ref[index]["cb"]
        cw = cr - cl
        ch = cb - ct
        if (cl != 0 or cr != 1 or ct != 0 or cb != 1):
            clip_state = True
        else:
            clip_state = False
        # Emit
        self.SIGNAL_CLIP.emit([clip_state, cl*width, ct*height, cw*width, ch*height])
        self.SIGNAL_DRAG.emit(path)
    def Pin_Replace(self, index, path):
        if len(self.pin_ref) > 0:
            self.pin_ref[index]["path"] = path
            self.update()
    def Pin_NewPath(self, index):
        path = QFileDialog(QWidget(self))
        path.setFileMode(QFileDialog.ExistingFile)
        file_path = path.getOpenFileName(self, "Select File", os.path.dirname(self.pin_ref[index]["path"]) )[0]
        file_path = os.path.normpath( file_path )
        if (file_path != "" and file_path != "."):
            # Variables
            ox = self.pin_ref[index]["ox"]
            oy = self.pin_ref[index]["oy"]
            # Delete Previous
            self.Pin_Delete(self.pin_index)
            # New Pin
            pin = {"path" : file_path, "text" : None, "origin_x" : ox, "origin_y" : oy}
            self.Pin_Drop(pin)
    def Pin_Delete(self, index):
        self.Selection_Clear()
        if index != None:
            self.pin_ref.pop(index)
        self.pin_index = None
        self.Release_Event()
        self.update()

    # Board Management
    def Board_Reset(self):
        QtCore.qDebug("--------------")
        # Bounding Box of All
        box = Pixmap_Box(self, self.pin_ref)
        min_x = box["min_x"]
        min_y = box["min_y"]
        max_x = box["max_x"]
        max_y = box["max_y"]
        bw = abs(max_x - min_x)
        bh = abs(max_y - min_y)
        QtCore.qDebug("bw = " + str(bw))
        QtCore.qDebug("bh = " + str(bh))

        if bw >= bh:
            size = bw
        else:
            size = bh
        unit_bw = bw / size
        unit_bh = bh / size
        QtCore.qDebug("unit_bw = " + str(unit_bw))
        QtCore.qDebug("unit_bh = " + str(unit_bh))

        # Widget Size
        if self.widget_width >= self.widget_height:
            size = self.widget_width
        else:
            size = self.widget_height
        unit_ww = self.widget_width / size
        unit_wh = self.widget_height / size
        QtCore.qDebug("unit_ww = " + str(unit_ww))
        QtCore.qDebug("unit_wh = " + str(unit_wh))

        # compress unit board
        if unit_ww < unit_wh:
            comp_bw = unit_bw * unit_ww
            comp_bh = unit_bh * unit_ww
        else:
            comp_bw = unit_bw * unit_wh
            comp_bh = unit_bh * unit_wh
        QtCore.qDebug("comp_bw = " + str(comp_bw))
        QtCore.qDebug("comp_bh = " + str(comp_bh))

        # Expand
        unit_min_x = (unit_ww * 0.5) - (comp_bw * 0.5)
        unit_max_x = (unit_ww * 0.5) + (comp_bw * 0.5)
        unit_min_y = (unit_wh * 0.5) - (comp_bh * 0.5)
        unit_max_y = (unit_wh * 0.5) + (comp_bh * 0.5)
        w_min_x = unit_min_x * self.widget_width
        w_max_x = unit_max_x * self.widget_width
        w_min_y = unit_min_y * self.widget_height
        w_max_y = unit_max_y * self.widget_height
        QtCore.qDebug("w_min_x = " + str(w_min_x))
        QtCore.qDebug("w_max_x = " + str(w_max_x))
        QtCore.qDebug("w_min_y = " + str(w_min_y))
        QtCore.qDebug("w_max_y = " + str(w_max_y))

        # Calculations
        original_size = Trig_2D_Points_Distance(min_x, min_y, max_x, max_y)
        QtCore.qDebug("original_size = " + str(original_size))

        widget_size = Trig_2D_Points_Distance(w_min_x, w_min_y, w_max_x, w_max_y)
        QtCore.qDebug("widget_size = " + str(widget_size))

        factor = widget_size / original_size
        QtCore.qDebug("factor = " + str(factor))

    def Board_Rebase(self):
        for i in range(0, len(self.pin_ref)):
            self.Pixmap_Edit(i)
        self.Board_Save()
        self.update()
    def Board_Load(self, references):
        self.pin_ref = []
        for i in range(0, len(references)):
            self.Pin_Ref(references[i])
        self.update()
    def Board_Save(self):
        reference = []
        for i in range(0, len(self.pin_ref)):
            pin = self.pin_ref[i].copy()
            pin["qpixmap"] = None
            reference.append(pin)
        self.SIGNAL_SAVE.emit(reference)
    def Board_Delete(self):
        # Clean variables
        self.pin_ref = []
        # State
        self.Selection_Clear()
        self.Release_Event()
        self.Board_Save()
        self.update()

    # Image Packing
    def Pack_Optimal_Start(self, method, mode):
        # Widget
        self.setEnabled(False)
        # Start Threads operations
        self.thread_packer = Thread_Packer()
        self.thread_packer.SIGNAL_REFERENCE.connect(self.Pack_Optimal_Ref)
        self.thread_packer.SIGNAL_RESET.connect(self.Pack_Optimal_Reset)
        self.thread_packer.Variables_Run(method, self.pin_ref, mode)
        self.thread_packer.start()
    def Pack_Optimal_Ref(self, pin):
        # Thread
        self.pin_ref[ pin["index"] ] = pin
        # Update
        self.modified = True
        self.update()
    def Pack_Optimal_Reset(self):
        # Thread
        self.thread_packer.quit()
        # Widget
        self.setEnabled(True)
        # Update
        if self.modified == True:
            self.SIGNAL_UNDO.emit(self.pin_ref)
            self.modified = False
        self.update()

    # Mouse Events
    def mousePressEvent(self, event):
        # Mouse Origin
        self.origin_x = event.x()
        self.origin_y = event.y()
        self.Index_Closest(event)
        self.Index_Limits(event)

        if self.press == None:
            # Neutral
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
                self.press = "neutral"
                if self.pin_index != None:
                    # Move
                    self.Active_Select(self.pin_index)
                    self.Index_Deltas_Move(self.pin_index)
                    self.Pixmap_Transform_MS(event, self.pin_index, self.pin_node)
                else:
                    self.Selection_Clear()

            # Camera
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
                self.press = "camera_1"
                self.Index_Deltas_Move(None)
            if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
                self.press = "camera_2"
                self.camera_relative = self.origin_y
                self.Index_Deltas_Scale()
            if (event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier):
                self.press = "camera_3"
                self.Index_Deltas_Move(None)
            # Select
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
                self.press = "select"
                if self.pin_index != None:
                    self.Selection_Shift(self.pin_index)
                else:
                    self.Selection_Clear()
            # Drag and Drop
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
                self.press = "dragdrop"

            # RC Operations
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier)):
                self.press = "clip"
                if self.pin_index != None:
                    self.Active_Select(self.pin_index)
                    self.Index_Deltas_Move(self.pin_index)
                    self.Pixmap_Transform_RC(event, self.pin_index, self.pin_node)
                else:
                    self.Selection_Clear()

            # Zoom
            if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
                boolean = self.pin_zoom["bool"]
                if (self.pin_index != None and boolean == False):
                    text = self.pin_ref[self.pin_index]["text"]
                    if (text == None or text == ""):
                        self.Pixmap_Zoom(True, self.pin_ref[self.pin_index]["qpixmap"])
                    else:
                        self.Pixmap_Zoom(False, "")
                else:
                    self.Pixmap_Zoom(False, "")

            # Context
            if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
                self.Context_Menu(event)
    def mouseMoveEvent(self, event):
        # Mouse
        ex = event.x()
        ey = event.y()
        dist = Trig_2D_Points_Distance(self.origin_x, self.origin_y, ex, ey)
        limit = 10

        # Neutral
        if (self.press == "neutral" and event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            if self.pin_index != None:
                self.Pixmap_Transform_MS(event, self.pin_index, self.pin_node)
            else:
                self.Selection_Square(event)

        # Camera
        if (self.press == "camera_1" and event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.Camera_Pan(event)
        if (self.press == "camera_2" and event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            value = 0.05
            check = ey - self.camera_relative
            if check > 1:
                self.Camera_Scale(event, self.origin_x, self.origin_y, -value)
            if check < -1:
                self.Camera_Scale(event, self.origin_x, self.origin_y, value)
        if (self.press == "camera_3" and event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Camera_Pan(event)
        # Select
        if (self.press == "select" and event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            if dist >= limit:
                self.Selection_Square(event)
        # Drag and Drop
        if (self.press == "dragdrop" and event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            if (self.pin_index != None and dist >= limit):
                self.Pin_Drag(self.pin_index)

        # RC Operations
        if (self.press == "clip" and event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier)):
            if self.pin_index != None:
                self.Pixmap_Transform_RC(event, self.pin_index, self.pin_node)
            else:
                self.Selection_Square(event)

        # Zoom
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            pass

        # Context
        if (self.press == "context" and event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
    def mouseDoubleClickEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        self.Release_Event()
    def Release_Event(self):
        # Events
        self.origin_x = 0
        self.origin_y = 0
        self.camera_relative = 0
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
            self.SIGNAL_UNDO.emit(self.pin_ref)
            self.modified = False
        self.update()

    # Context Menu Event
    def Context_Menu(self, event):
        self.Index_Closest(event)
        cmenu = QMenu(self)
        position = self.mapToGlobal(event.pos())
        if self.pin_zoom["bool"] == True:
            self.Menu_Pin_Zoom(event, cmenu, position)
        elif self.pin_index == None:
            self.Menu_Board(event, cmenu, position)
        elif self.pin_ref[self.pin_index]["select"] == True:
            self.Menu_Selection(event, cmenu, position)
        else:
            self.Menu_Pin(event, cmenu, position)
        # Undo
        if self.modified == True:
            self.SIGNAL_UNDO.emit(self.pin_ref)
            self.modified = False
    def Menu_Pin(self, event, cmenu, position):
        text = self.pin_ref[self.pin_index]["text"]
        # Actions
        cmenu.addSection("PIN")
        if text == None:
            cmenu_zoom_open = cmenu.addAction("Zoom Pin")
            cmenu.addSection(" ")
            cmenu_edit_greyscale = cmenu.addAction("Greyscale")
            cmenu_edit_greyscale.setCheckable(True)
            cmenu_edit_greyscale.setChecked(self.pin_ref[self.pin_index]["egs"])
            cmenu_edit_invert_h = cmenu.addAction("Flip Horizontal")
            cmenu_edit_invert_h.setCheckable(True)
            cmenu_edit_invert_h.setChecked(self.pin_ref[self.pin_index]["efx"])
            cmenu_edit_invert_v = cmenu.addAction("Flip Vertical")
            cmenu_edit_invert_v.setCheckable(True)
            cmenu_edit_invert_v.setChecked(self.pin_ref[self.pin_index]["efy"])
            cmenu.addSection(" ")
            cmenu_pin_newpath = cmenu.addAction("New Path")
        else:
            cmenu_text = cmenu.addAction("Text Edit")
            cmenu_color = cmenu.addAction("Label Color")
            cmenu.addSection(" ")
        cmenu_pin_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if text == None:
            if action == cmenu_zoom_open:
                self.Pixmap_Zoom(True, self.pin_ref[self.pin_index]["qpixmap"])
            if action == cmenu_edit_greyscale:
                self.pin_ref[self.pin_index]["egs"] = not self.pin_ref[self.pin_index]["egs"]
                self.Pixmap_Edit(self.pin_index)
                self.modified = True
            if action == cmenu_edit_invert_h:
                # Operation
                self.pin_ref[self.pin_index]["efx"] = not self.pin_ref[self.pin_index]["efx"]
                # Clip Invert
                a = 1 - self.pin_ref[self.pin_index]["cr"]
                b = 1 - self.pin_ref[self.pin_index]["cl"]
                self.pin_ref[self.pin_index]["cl"] = a
                self.pin_ref[self.pin_index]["cr"] = b
                # Bounding Box
                clip, sides = Clip_Construct(self, self.pin_ref, self.pin_index)
                self.pin_ref[self.pin_index]["bl"] = round(sides[0], decimas)
                self.pin_ref[self.pin_index]["br"] = round(sides[1], decimas)
                self.pin_ref[self.pin_index]["bt"] = round(sides[2], decimas)
                self.pin_ref[self.pin_index]["bb"] = round(sides[3], decimas)
                # Pixmap Edit
                self.Pixmap_Edit(self.pin_index)
                self.modified = True
            if action == cmenu_edit_invert_v:
                # Operation
                self.pin_ref[self.pin_index]["efy"] = not self.pin_ref[self.pin_index]["efy"]
                # Clip Invert
                a = 1 - self.pin_ref[self.pin_index]["cb"]
                b = 1 - self.pin_ref[self.pin_index]["ct"]
                self.pin_ref[self.pin_index]["ct"] = a
                self.pin_ref[self.pin_index]["cb"] = b
                # Bounding Box
                clip, sides = Clip_Construct(self, self.pin_ref, self.pin_index)
                self.pin_ref[self.pin_index]["bl"] = round(sides[0], decimas)
                self.pin_ref[self.pin_index]["br"] = round(sides[1], decimas)
                self.pin_ref[self.pin_index]["bt"] = round(sides[2], decimas)
                self.pin_ref[self.pin_index]["bb"] = round(sides[3], decimas)
                # Pixmap Edit
                self.Pixmap_Edit(self.pin_index)
                self.modified = True
            if action == cmenu_pin_newpath:
                self.Pin_NewPath(self.pin_index)
                self.modified = True
        else:
            if action == cmenu_text:
                self.Text_Edit()
            if action == cmenu_color:
                self.Text_Label()
        if action == cmenu_pin_delete:
            self.Pin_Delete(self.pin_index)
            self.modified = True
    def Menu_Selection(self, event, cmenu, position):
        # Actions
        cmenu.addSection("SELECTION")
        cmenu_pack = cmenu.addMenu("Pack")
        cmenu_pack_area = cmenu_pack.addAction("Area")
        cmenu_pack_perimeter = cmenu_pack.addAction("Perimeter")
        cmenu_pack_ratio = cmenu_pack.addAction("Ratio")
        cmenu_pack_class = cmenu_pack.addAction("Class")
        cmenu_pack_line = cmenu_pack.addAction("Line")
        cmenu_pack_column = cmenu_pack.addAction("Column")
        cmenu_color = cmenu.addAction("Label Color")
        cmenu.addSection(" ")
        cmenu_selection_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_pack_area:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("OPTIMAL", "AREA")
            self.modified = True
        if action == cmenu_pack_perimeter:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("OPTIMAL", "PERIMETER")
            self.modified = True
        if action == cmenu_pack_ratio:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("OPTIMAL", "RATIO")
            self.modified = True
        if action == cmenu_pack_class:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("OPTIMAL", "CLASS")
            self.modified = True
        if action == cmenu_pack_line:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("LINEAR", "LINE")
            self.modified = True
        if action == cmenu_pack_column:
            self.Index_Position(self.pin_ref)
            self.Pack_Optimal_Start("LINEAR", "COLUMN")
            self.modified = True
        if action == cmenu_color:
            self.Text_Label()
        if action == cmenu_selection_delete:
            self.Selection_Delete()
            self.modified = True
    def Menu_Board(self, event, cmenu, position):
        # Actions
        cmenu.addSection("BOARD")
        cmenu_board_text = cmenu.addAction("Insert Text")
        cmenu_board_select = cmenu.addAction("Select All")
        # cmenu_board_reset = cmenu.addAction("Reset")
        cmenu_board_rebase = cmenu.addAction("Rebase")
        cmenu_board_delete = cmenu.addAction("Delete")
        action = cmenu.exec_(position)
        # Triggers
        if action == cmenu_board_text:
            pin = {"path" : None, "text" : self.text_default, "origin_x" : event.x(), "origin_y" : event.y() }
            self.SIGNAL_TEXT.emit(pin)
            self.modified = True
        if action == cmenu_board_select:
            self.Selection_All()
            self.modified = True
        # if action == cmenu_board_reset:
        #     self.Board_Reset()
        #     self.modified = True
        if action == cmenu_board_rebase:
            self.Board_Rebase()
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
    def Pixmap_Transform_MS(self, event, index, node):
        scale = [1,3,7,9]
        if node in scale:
            self.Pixmap_Scale_Event(event, index, node)
        else:
            self.Pixmap_Move_Event(event, index)
        # Undo entry
        self.modified = True
    def Pixmap_Transform_RC(self, event, index, node):
        rotation = [5]
        clip = [2,4,6,8]
        if node in rotation:
            self.Pixmap_Rotation_Event(event, index)
        elif node in clip:
            self.Pixmap_Clip_Event(event, index, node)
        # Undo entry
        self.modified = True
    def Pixmap_Move_Event(self, event, index):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Read
        path = self.pin_ref[index]["path"]
        ox = self.pin_ref[index]["ox"]
        oy = self.pin_ref[index]["oy"]
        rx = self.pin_ref[index]["rx"]
        ry = self.pin_ref[index]["ry"]
        dw = self.pin_ref[index]["dw"]
        dh = self.pin_ref[index]["dh"]
        bl = self.pin_ref[index]["bl"]
        br = self.pin_ref[index]["br"]
        bt = self.pin_ref[index]["bt"]
        bb = self.pin_ref[index]["bb"]

        # Calculations
        dw2 = dw * 0.5
        dh2 = dh * 0.5
        sx = 0
        sy = 0
        n_ox = ex - rx
        n_oy = ey - ry
        n_dx = n_ox - dw2
        n_dy = n_oy - dh2
        n_dxw = n_ox + dw2
        n_dyh = n_oy + dh2

        n_bl = n_ox + (bl - ox)
        n_br = n_ox + (br - ox)
        n_bt = n_oy + (bt - oy)
        n_bb = n_oy + (bb - oy)

        # Move Single
        n_ox = self.pin_ref[index]["ox"] = round(n_ox, decimas)
        n_oy = self.pin_ref[index]["oy"] = round(n_oy, decimas)
        n_dx = self.pin_ref[index]["dx"] = round(n_dx, decimas)
        n_dy = self.pin_ref[index]["dy"] = round(n_dy, decimas)
        n_dxw = self.pin_ref[index]["dxw"] = round(n_dxw, decimas)
        n_dyh = self.pin_ref[index]["dyh"] = round(n_dyh, decimas)
        bl = self.pin_ref[index]["bl"] = round(n_bl, decimas)
        br = self.pin_ref[index]["br"] = round(n_br, decimas)
        bt = self.pin_ref[index]["bt"] = round(n_bt, decimas)
        bb = self.pin_ref[index]["bb"] = round(n_bb, decimas)

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
                    self.pin_ref[index]["ox"] = round(lim_xi + dw2 - bbl, decimas)
                    self.pin_ref[index]["dx"] = round(lim_xi - bbl, decimas)
                    self.pin_ref[index]["dxw"] = round(lim_xi + dw - bbr, decimas)
                    self.pin_ref[index]["bl"] = round(lim_xi, decimas)
                    self.pin_ref[index]["br"] = round(lim_xi + bbw, decimas)
                    sx = round(self.pin_ref[index]["ox"] - n_ox, decimas)
                    break
                elif (br >= ll and br <= lr):
                    self.pin_ref[index]["ox"] = round(lim_xi - dw2 + bbr, decimas)
                    self.pin_ref[index]["dx"] = round(lim_xi - dw + bbr, decimas)
                    self.pin_ref[index]["dxw"] = round(lim_xi + bbr, decimas)
                    self.pin_ref[index]["bl"] = round(lim_xi - bbw, decimas)
                    self.pin_ref[index]["br"] = round(lim_xi, decimas)
                    sx = round(self.pin_ref[index]["ox"] - n_ox, decimas)
                    break
        if len(self.limit_y) > 0:
            for i in range(0, len(self.limit_y)):
                lim_yi = self.limit_y[i]
                lt = lim_yi - snap
                lb = lim_yi + snap
                if (bt >= lt and bt <= lb):
                    self.pin_ref[index]["oy"] = round(lim_yi + dh2 - bbt, decimas)
                    self.pin_ref[index]["dy"] = round(lim_yi - bbt, decimas)
                    self.pin_ref[index]["dyh"] = round(lim_yi + dh - bbt, decimas)
                    self.pin_ref[index]["bt"] = round(lim_yi, decimas)
                    self.pin_ref[index]["bb"] = round(lim_yi + bbh, decimas)
                    sy = round(self.pin_ref[index]["oy"] - n_oy, decimas)
                    break
                elif (bb >= lt and bb <= lb):
                    self.pin_ref[index]["oy"] = round(lim_yi - dh2 + bbb, decimas)
                    self.pin_ref[index]["dy"] = round(lim_yi - dh + bbb, decimas)
                    self.pin_ref[index]["dyh"] = round(lim_yi + bbb, decimas)
                    self.pin_ref[index]["bt"] = round(lim_yi - bbh, decimas)
                    self.pin_ref[index]["bb"] = round(lim_yi, decimas)
                    sy = round(self.pin_ref[index]["oy"] - n_oy, decimas)
                    break

        # Selection Move
        for i in range(0, len(self.pin_ref)):
            if (i != index and self.pin_ref[i]["select"] == True):
                # Read
                ox = self.pin_ref[i]["ox"]
                oy = self.pin_ref[i]["oy"]
                rx = self.pin_ref[i]["rx"]
                ry = self.pin_ref[i]["ry"]
                dw = self.pin_ref[i]["dw"]
                dh = self.pin_ref[i]["dh"]
                bl = self.pin_ref[i]["bl"]
                br = self.pin_ref[i]["br"]
                bt = self.pin_ref[i]["bt"]
                bb = self.pin_ref[i]["bb"]

                # Calculations
                dw2 = dw * 0.5
                dh2 = dh * 0.5
                n_ox = ex - rx + sx
                n_oy = ey - ry + sy
                n_bl = n_ox + (bl - ox)
                n_br = n_ox + (br - ox)
                n_bt = n_oy + (bt - oy)
                n_bb = n_oy + (bb - oy)

                # Write
                self.pin_ref[i]["ox"] = round(n_ox, decimas)
                self.pin_ref[i]["oy"] = round(n_oy, decimas)
                self.pin_ref[i]["dx"] = round(n_ox - dw2, decimas)
                self.pin_ref[i]["dy"] = round(n_oy - dh2, decimas)
                self.pin_ref[i]["dxw"] = round(n_ox + dw2, decimas)
                self.pin_ref[i]["dyh"] = round(n_oy + dh2, decimas)
                self.pin_ref[i]["bl"] = round(n_bl, decimas)
                self.pin_ref[i]["br"] = round(n_br, decimas)
                self.pin_ref[i]["bt"] = round(n_bt, decimas)
                self.pin_ref[i]["bb"] = round(n_bb, decimas)

        # Update
        self.update()
    def Pixmap_Rotation_Event(self, event, index):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Read
        ox = self.pin_ref[index]["ox"]
        oy = self.pin_ref[index]["oy"]
        rn = self.pin_ref[index]["rn"]
        ro = self.pin_ref[index]["ro"]
        ss = self.pin_ref[index]["ss"]
        dx = self.pin_ref[index]["dx"]
        dy = self.pin_ref[index]["dy"]
        dw = self.pin_ref[index]["dw"]
        dh = self.pin_ref[index]["dh"]
        dxw = self.pin_ref[index]["dxw"]
        dyh = self.pin_ref[index]["dyh"]
        cl = self.pin_ref[index]["cl"]
        cr = self.pin_ref[index]["cr"]
        ct = self.pin_ref[index]["ct"]
        cb = self.pin_ref[index]["cb"]

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
        der = max(c1_x, c2_x, c3_x, c4_x)
        top = min(c1_y, c2_y, c3_y, c4_y)
        bot = max(c1_y, c2_y, c3_y, c4_y)
        width = abs(der - esq)
        height = abs(bot - top)

        # Scale Relative
        dist_draw = Trig_2D_Points_Distance(esq, top, ox, oy)
        dist_cir = Trig_2D_Points_Distance(c1_x, c1_y, ox, oy)
        sr = dist_cir / dist_draw

        # Write
        self.pin_ref[index]["ro"] = round(angle, decimas)
        self.pin_ref[index]["sr"] = round(sr, decimas)
        self.pin_ref[index]["dx"] = round(esq, decimas)
        self.pin_ref[index]["dy"] = round(top, decimas)
        self.pin_ref[index]["dw"] = round(width, decimas)
        self.pin_ref[index]["dh"] = round(height, decimas)
        self.pin_ref[index]["dxw"] = round(der, decimas)
        self.pin_ref[index]["dyh"] = round(bot, decimas)

        # Bounding Box
        clip, sides = Clip_Construct(self, self.pin_ref, index)
        bl = self.pin_ref[index]["bl"] = round(sides[0], decimas)
        br = self.pin_ref[index]["br"] = round(sides[1], decimas)
        bt = self.pin_ref[index]["bt"] = round(sides[2], decimas)
        bb = self.pin_ref[index]["bb"] = round(sides[3], decimas)

        # Edit Cycle
        self.Pixmap_Edit(index)

        # Update
        if self.pin_zoom["bool"] == True:
            self.pin_zoom["qpixmap"] = self.pin_ref[self.pin_index]["qpixmap"]
        self.update()
    def Pixmap_Scale_Event(self, event, index, node):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Read
        pis = self.pin_ref[index]["pis"]
        pir = self.pin_ref[index]["pir"]
        ox = self.pin_ref[index]["ox"]
        oy = self.pin_ref[index]["oy"]
        rn = self.pin_ref[index]["rn"]
        ro = self.pin_ref[index]["ro"]
        sr = self.pin_ref[index]["sr"]
        dx = self.pin_ref[index]["dx"]
        dy = self.pin_ref[index]["dy"]
        dw = self.pin_ref[index]["dw"]
        dh = self.pin_ref[index]["dh"]
        dxw = self.pin_ref[index]["dxw"]
        dyh = self.pin_ref[index]["dyh"]
        bl = self.pin_ref[index]["bl"]
        br = self.pin_ref[index]["br"]
        bt = self.pin_ref[index]["bt"]
        bb = self.pin_ref[index]["bb"]

        # Calculations
        bw = abs(br - bl)
        bh = abs(bb - bt)
        r_angle = rn + ro
        if bh == 0:
            return
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

        # Pivot Point (opposite of active node)
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
        if (n_dw == 0 or n_dh == 0):
            return
        n_ox = n_dx + (n_dw * 0.5)
        n_oy = n_dy + (n_dh * 0.5)
        n_ss = Trig_2D_Points_Distance(n_dx, n_dy, n_ox, n_oy) * sr
        n_perimeter = 2*n_dw + 2*n_dh
        n_area = n_dw * n_dh
        n_ratio = n_dw / n_dh
        n_pis = n_dh / (24/15) # 24/15 is the original constant

        # Write
        self.pin_ref[index]["ox"] = round(n_ox, decimas)
        self.pin_ref[index]["oy"] = round(n_oy, decimas)
        self.pin_ref[index]["ss"] = round(n_ss, decimas)
        self.pin_ref[index]["dx"] = round(n_dx, decimas)
        self.pin_ref[index]["dy"] = round(n_dy, decimas)
        self.pin_ref[index]["dw"] = round(n_dw, decimas)
        self.pin_ref[index]["dh"] = round(n_dh, decimas)
        self.pin_ref[index]["dxw"] = round(n_dxw, decimas)
        self.pin_ref[index]["dyh"] = round(n_dyh, decimas)
        self.pin_ref[index]["bl"] = round(n_bl, decimas)
        self.pin_ref[index]["br"] = round(n_br, decimas)
        self.pin_ref[index]["bt"] = round(n_bt, decimas)
        self.pin_ref[index]["bb"] = round(n_bb, decimas)

        self.pin_ref[index]["perimeter"] = round(n_perimeter, decimas)
        self.pin_ref[index]["area"] = round(n_area, decimas)
        self.pin_ref[index]["ratio"] = round(n_ratio, decimas)

        self.pin_ref[index]["pis"] = n_pis

        # Update
        self.update()
    def Pixmap_Clip_Event(self, event, index, node):
        # Event
        ex = event.x()
        ey = event.y()

        # Read
        dx = self.pin_ref[index]["dx"]
        dy = self.pin_ref[index]["dy"]
        dw = self.pin_ref[index]["dw"]
        dh = self.pin_ref[index]["dh"]
        dxw = self.pin_ref[index]["dxw"]
        dyh = self.pin_ref[index]["dyh"]
        cl = self.pin_ref[index]["cl"]
        cr = self.pin_ref[index]["cr"]
        ct = self.pin_ref[index]["ct"]
        cb = self.pin_ref[index]["cb"]

        # Nodes
        safe = 0.03
        if node == 2:
            cut = Limit_Range((ey - dy) / dh, 0, cb-safe)
            self.pin_ref[index]["ct"] = round(cut, decimas)
        if node == 4:
            cut = Limit_Range((ex - dx) / dw, 0, cr-safe)
            self.pin_ref[index]["cl"] = round(cut, decimas)
        if node == 6:
            cut = Limit_Range((ex - dx) / dw, cl+safe, 1)
            self.pin_ref[index]["cr"] = round(cut, decimas)
        if node == 8:
            cut = Limit_Range((ey - dy) / dh, ct+safe, 1)
            self.pin_ref[index]["cb"] = round(cut, decimas)

        # Bounding Box
        clip, sides = Clip_Construct(self, self.pin_ref, index)
        n_bl = sides[0]
        n_br = sides[1]
        n_bt = sides[2]
        n_bb = sides[3]
        bw = abs(n_br - n_bl)
        bh = abs(n_bb - n_bt)
        if (bw == 0 or bh == 0):
            return
        n_perimeter = 2*bw + 2*bh
        n_area = bw * bh
        n_ratio = bw / bh

        # Write
        self.pin_ref[index]["bl"] = round(n_bl, decimas)
        self.pin_ref[index]["br"] = round(n_br, decimas)
        self.pin_ref[index]["bt"] = round(n_bt, decimas)
        self.pin_ref[index]["bb"] = round(n_bb, decimas)
        self.pin_ref[index]["perimeter"] = round(n_perimeter, decimas)
        self.pin_ref[index]["area"] = round(n_area, decimas)
        self.pin_ref[index]["ratio"] = round(n_ratio, decimas)

        # Update
        self.update()

    # Isolated Pixmap Operations
    def Pixmap_Edit(self, index):
        # Read Operations
        path = self.pin_ref[index]["path"]
        egs = self.pin_ref[index]["egs"]
        efx = self.pin_ref[index]["efx"]
        efy = self.pin_ref[index]["efy"]
        cl = self.pin_ref[index]["cl"]
        cr = self.pin_ref[index]["cr"]
        ct = self.pin_ref[index]["ct"]
        cb = self.pin_ref[index]["cb"]

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
            QTransform().rotate(self.pin_ref[index]["ro"],  Qt.ZAxis),
            Qt.SmoothTransformation
            )

        # Apply Pixmap to rendering list
        qpixmap = QPixmap().fromImage(qimage_edit)
        self.pin_ref[index]["qpixmap"] = qpixmap
        self.update()
    def Pixmap_Zoom(self, bool, qpixmap):
        self.pin_zoom["bool"] = bool
        self.pin_zoom["qpixmap"] = qpixmap
        self.update()

    # Text Operations
    def Text_Edit(self):
        if self.pin_index != None:
            text = self.pin_ref[self.pin_index]["text"]
            string, ok = QInputDialog.getText(self, "Imagine Board", "Input Text", QLineEdit.Normal, text )
            if ok and string is not None and not "":
                # Read
                color = self.pin_ref[self.pin_index]["color"]
                ox = self.pin_ref[self.pin_index]["ox"]
                oy = self.pin_ref[self.pin_index]["oy"]

                # Eliminate Entry
                self.pin_ref.pop(self.pin_index)
                # New Pin
                pin = {"path" : None, "text" : string, "origin_x" : ox, "origin_y" : oy }
                self.SIGNAL_TEXT.emit(pin)
                self.pin_ref[self.pin_index]["color"] = color

                # Update
                self.modified = True
                self.update()
    def Text_Label(self):
        if self.pin_index != None:
            previous = self.pin_ref[self.pin_index]["color"]
            color, ok = QInputDialog.getText(self, "Imagine Board", "Input Color", QLineEdit.Normal, previous )
            check = len(color) == 7 and color.startswith("#")
            if ok and color is not None and not "" and check == True:
                # Cycle Change
                self.pin_ref[self.pin_index]["color"] = color
                for i in range(0, len(self.pin_ref)):
                    if (self.pin_ref[i]["select"] == True or self.pin_ref[i]["active"] == True):
                        self.pin_ref[i]["color"] = color

                # Update
                self.modified = True
                self.update()

    # Camera Operations
    def Camera_Pan(self, event):
        # Event Mouse
        ex = event.x()
        ey = event.y()

        # Move all
        for i in range(0, len(self.pin_ref)):
            # Read
            dw = self.pin_ref[i]["dw"]
            dh = self.pin_ref[i]["dh"]
            rx = self.pin_ref[i]["rx"]
            ry = self.pin_ref[i]["ry"]
            # Calculations
            n_ox = ex - rx
            n_oy = ey - ry
            # Write
            self.pin_ref[i]["ox"] = round(n_ox, decimas)
            self.pin_ref[i]["oy"] = round(n_oy, decimas)
            self.pin_ref[i]["dx"] = round(n_ox - (dw * 0.5), decimas)
            self.pin_ref[i]["dy"] = round(n_oy - (dh * 0.5), decimas)
            self.pin_ref[i]["dxw"] = round(n_ox + (dw * 0.5), decimas)
            self.pin_ref[i]["dyh"] = round(n_oy + (dh * 0.5), decimas)
            # Bounding Box
            clip, sides = Clip_Construct(self, self.pin_ref, i)
            self.pin_ref[i]["bl"] = round(sides[0], decimas)
            self.pin_ref[i]["br"] = round(sides[1], decimas)
            self.pin_ref[i]["bt"] = round(sides[2], decimas)
            self.pin_ref[i]["bb"] = round(sides[3], decimas)

        # Update
        self.update()
    def Camera_Scale(self, event, pivot_x, pivot_y, value):
        # Event Mouse
        self.camera_relative = event.y()

        # Scale all
        for i in range(0, len(self.pin_ref)):
            # Read
            pis = self.pin_ref[i]["pis"]
            pir = self.pin_ref[i]["pir"]
            ox = self.pin_ref[i]["ox"]
            oy = self.pin_ref[i]["oy"]
            rn = self.pin_ref[i]["rn"]
            ro = self.pin_ref[i]["ro"]
            sr = self.pin_ref[i]["sr"]
            dx = self.pin_ref[i]["dx"]
            dy = self.pin_ref[i]["dy"]
            dw = self.pin_ref[i]["dw"]
            dh = self.pin_ref[i]["dh"]
            dxw = self.pin_ref[i]["dxw"]
            dyh = self.pin_ref[i]["dyh"]
            bl = self.pin_ref[i]["bl"]
            br = self.pin_ref[i]["br"]
            bt = self.pin_ref[i]["bt"]
            bb = self.pin_ref[i]["bb"]

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
            n_perimeter = 2*n_dw + 2*n_dh
            n_area = n_dw * n_dh
            n_ratio = n_dw / n_dh
            n_pis = n_dh / pir

            # Write
            self.pin_ref[i]["pis"] = n_pis
            self.pin_ref[i]["ox"] = round(n_ox, decimas)
            self.pin_ref[i]["oy"] = round(n_oy, decimas)
            self.pin_ref[i]["ss"] = round(n_ss, decimas)
            self.pin_ref[i]["dx"] = round(n_dx, decimas)
            self.pin_ref[i]["dy"] = round(n_dy, decimas)
            self.pin_ref[i]["dw"] = round(n_dw, decimas)
            self.pin_ref[i]["dh"] = round(n_dh, decimas)
            self.pin_ref[i]["dxw"] = round(n_dxw, decimas)
            self.pin_ref[i]["dyh"] = round(n_dyh, decimas)
            self.pin_ref[i]["bl"] = round(n_bl, decimas)
            self.pin_ref[i]["br"] = round(n_br, decimas)
            self.pin_ref[i]["bt"] = round(n_bt, decimas)
            self.pin_ref[i]["bb"] = round(n_bb, decimas)
            self.pin_ref[i]["perimeter"] = round(n_perimeter, decimas)
            self.pin_ref[i]["area"] = round(n_area, decimas)
            self.pin_ref[i]["ratio"] = round(n_ratio, decimas)

        # Update
        self.update()
    def Camera_Reset(self):
        pass

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
        # MimeData
        if event.mimeData().hasImage:
            self.drop = False
            event.setDropAction(Qt.CopyAction)
            mime_paths = []
            if (self.origin_x == 0 and self.origin_y == 0): # Denys from recieving from self.
                mime_data = event_drop(self, event)
                for i in range(0, len(mime_data)):
                    pin = {"path" : mime_data[i][1], "text" : None, "origin_x" : self.origin_ref, "origin_y" : self.origin_ref }
                    self.Pin_Drop(pin)
            event.accept()
        else:
            event.ignore()
        self.Board_Save()
        self.update()

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        # Board
        self.Active_Clear()
        self.Board_Save()
        # Undo
        if self.modified == True:
            self.SIGNAL_UNDO.emit(self.pin_ref)
            self.modified = False
        self.update()

    # Painter
    def paintEvent(self, event):
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_alpha)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Clip Mask
        widget = QRectF(0,0, self.widget_width,self.widget_height)
        painter.setClipRect(widget, Qt.ReplaceClip)

        # Board
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_shade)))
        optimized = []
        for i in range(0, len(self.pin_ref)):
            if self.pin_ref[i]["pack"] == False:
                bl = self.pin_ref[i]["bl"]
                br = self.pin_ref[i]["br"]
                bt = self.pin_ref[i]["bt"]
                bb = self.pin_ref[i]["bb"]
                bw = abs(br - bl)
                bh = abs(bb - bt)
                painter.drawRect( QRectF(bl, bt, bw, bh) )
                optimized.append(self.pin_ref[i])
        if len(optimized) > 0:
            # Optimized Square
            box = Pixmap_Box(self, optimized)
            min_x = box["min_x"]
            min_y = box["min_y"]
            max_x = box["max_x"]
            max_y = box["max_y"]
            opt_width = abs(max_x-min_x)
            opt_height = abs(max_y-min_y)
            painter.drawRect(min_x, min_y, opt_width, opt_height)
            # Lost Line
            if (min_x > self.widget_width or max_x < 0 or min_y > self.widget_height or max_y < 0):
                painter.setPen(QPen(self.color_1, 2, Qt.SolidLine))
                painter.setBrush(QtCore.Qt.NoBrush)
                opt_w2 = min_x + (opt_width * 0.5)
                opt_h2 = min_y + (opt_height * 0.5)
                painter.drawLine( QPointF(self.w2, self.h2), QPointF(opt_w2, opt_h2) )
                painter.drawEllipse( QRectF( self.w2-2, self.h2-2, 4, 4 ) )

        # No References
        if (len(self.pin_ref) == 0 and self.drop == False):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color_1)))
            if self.widget_width < self.widget_height:
                side = self.widget_width
            else:
                side = self.widget_height
            w2 = self.widget_width * 0.5
            h2 = self.widget_height * 0.5
            poly_quad = QPolygon([
                QPoint( int(w2 - (0.2*side)), int(h2 - (0.2*side)) ),
                QPoint( int(w2 + (0.2*side)), int(h2 - (0.2*side)) ),
                QPoint( int(w2 + (0.2*side)), int(h2 + (0.2*side)) ),
                QPoint( int(w2 - (0.2*side)), int(h2 + (0.2*side)) ),
                ])
            painter.drawPolygon(poly_quad)

        # Images and Text
        painter.setBrush(QtCore.Qt.NoBrush)
        for i in range(0, len(self.pin_ref)):
            # Read
            path = self.pin_ref[i]["path"]
            pack = self.pin_ref[i]["pack"]
            text = self.pin_ref[i]["text"]
            color = self.pin_ref[i]["color"]
            pis = self.pin_ref[i]["pis"]
            pir = self.pin_ref[i]["pir"]
            ox = self.pin_ref[i]["ox"]
            oy = self.pin_ref[i]["oy"]
            ro = self.pin_ref[i]["ro"]
            ss = self.pin_ref[i]["ss"]
            dx = self.pin_ref[i]["dx"]
            dy = self.pin_ref[i]["dy"]
            dw = self.pin_ref[i]["dw"]
            dh = self.pin_ref[i]["dh"]
            dxw = self.pin_ref[i]["dxw"]
            dyh = self.pin_ref[i]["dyh"]
            cl = self.pin_ref[i]["cl"]
            cr = self.pin_ref[i]["cr"]
            ct = self.pin_ref[i]["ct"]
            cb = self.pin_ref[i]["cb"]
            bl = self.pin_ref[i]["bl"]
            br = self.pin_ref[i]["br"]
            bt = self.pin_ref[i]["bt"]
            bb = self.pin_ref[i]["bb"]
            qpixmap = self.pin_ref[i]["qpixmap"]

            # Clip Mask
            clip, sides = Clip_Construct(self, self.pin_ref, i)
            square = QPainterPath()
            square.moveTo(clip[0][0], clip[0][1])
            square.lineTo(clip[1][0], clip[1][1])
            square.lineTo(clip[2][0], clip[2][1])
            square.lineTo(clip[3][0], clip[3][1])
            painter.setClipPath(square)

            # Draw Images & Background Color
            if pack == False:
                if (text == None or len(text) == 0):
                    if qpixmap == None: # Try to correct Image
                        qpixmap = QPixmap(path)
                        if qpixmap.isNull() == False:
                            self.pin_ref[i]["qpixmap"] = qpixmap
                    if qpixmap.isNull() == False: # Render Image
                        # Pixmap
                        painter.setPen(QtCore.Qt.NoPen)
                        painter.drawPixmap( QPointF(dx, dy), qpixmap.scaled( int(dw), int(dh), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                        # Masks
                        painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)
                    else: # No Image to Render
                        # Highlight
                        painter.setPen(QtCore.Qt.NoPen)
                        painter.setBrush(QBrush(QColor(self.color_2)))
                        painter.drawRect( QRectF(bl, bt, br-bl, bb-bt) )
                        # Masks
                        painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)
                else: # Draw Text
                    # Bounding Box
                    box = QRectF(bl, bt, br-bl, bb-bt)
                    # Highlight
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QBrush(QColor(color)))

                    painter.drawRect( box )
                    # String
                    painter.setBrush(QtCore.Qt.NoBrush)
                    painter.setPen(QPen(self.color_1, 1, Qt.SolidLine))
                    self.qfont.setPointSizeF(pis)
                    painter.setFont(self.qfont)
                    painter.drawText(box, Qt.AlignCenter, text)
                    # Masks
                    painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)

        # Dots Over
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(self.color_1, Qt.Dense7Pattern))
        selection = []
        for i in range(0, len(self.pin_ref)):
            if (self.pin_ref[i]["pack"] == False and self.pin_ref[i]["select"] == True):
                bl = self.pin_ref[i]["bl"]
                br = self.pin_ref[i]["br"]
                bt = self.pin_ref[i]["bt"]
                bb = self.pin_ref[i]["bb"]
                bw = abs(br - bl)
                bh = abs(bb - bt)
                painter.drawRect( QRectF(bl, bt, bw, bh) )
                selection.append(self.pin_ref[i])
        # Selection Square
        painter.setPen(QPen(self.color_1, 1, Qt.SolidLine))
        painter.setBrush(QtCore.Qt.NoBrush)
        if len(selection) > 0:
            box = Pixmap_Box(self, selection)
            min_x = box["min_x"]
            min_y = box["min_y"]
            max_x = box["max_x"]
            max_y = box["max_y"]
            painter.drawRect( QRectF(min_x, min_y, max_x-min_x, max_y-min_y) )

        # Active Nodes
        index = None
        for i in range(0, len(self.pin_ref)):
            if self.pin_ref[i]["active"] == True:
                index = i
                break
        if (self.pin_index != None and index != None):
            # Variables
            ox = self.pin_ref[index]["ox"]
            oy = self.pin_ref[index]["oy"]
            ro = self.pin_ref[index]["ro"]
            ss = self.pin_ref[index]["ss"]
            dx = self.pin_ref[index]["dx"]
            dy = self.pin_ref[index]["dy"]
            dw = self.pin_ref[index]["dw"]
            dh = self.pin_ref[index]["dh"]
            dxw = self.pin_ref[index]["dxw"]
            dyh = self.pin_ref[index]["dyh"]
            cl = self.pin_ref[index]["cl"]
            cr = self.pin_ref[index]["cr"]
            ct = self.pin_ref[index]["ct"]
            cb = self.pin_ref[index]["cb"]
            bl = int( round(self.pin_ref[index]["bl"], 0 ) )
            br = int( round(self.pin_ref[index]["br"], 0 ) )
            bt = int( round(self.pin_ref[index]["bt"], 0 ) )
            bb = int( round(self.pin_ref[index]["bb"], 0 ) )
            ww = abs(br - bl)
            hh = abs(bb - bt)
            w2 = ww * 0.5
            h2 = hh * 0.5

            # Bounding Box
            painter.setPen(QPen(self.color_2, 1, Qt.SolidLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect( QRectF(bl, bt, ww, hh) )

            # Triangle
            minimal_triangle = 20
            if (ww > minimal_triangle and hh > minimal_triangle):
                tri = 10
                # Scale 1
                if self.pin_node == 1:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polyt1 = QPolygon([ QPoint(bl, bt), QPoint(bl + tri, bt), QPoint(bl, bt + tri) ])
                painter.drawPolygon(polyt1)
                # scale 3
                if self.pin_node == 3:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polyt3 = QPolygon([ QPoint(br, bt), QPoint(br, bt + tri), QPoint(br - tri, bt) ])
                painter.drawPolygon(polyt3)
                # Scale 7
                if self.pin_node == 7:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polyt7 = QPolygon([ QPoint(bl, bb), QPoint(bl, bb - tri), QPoint(bl + tri, bb) ])
                painter.drawPolygon(polyt7)
                # Scale 9
                if self.pin_node == 9:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polyt9 = QPolygon([ QPoint(br, bb), QPoint(br - tri, bb), QPoint(br, bb - tri) ])
                painter.drawPolygon(polyt9)

            # Squares
            minimal_square = 50
            if (ww > minimal_square and hh > minimal_square):
                sq = 5
                # Clip 2
                if self.pin_node == 2:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl+w2-sq, bt), QPoint(bl+w2-sq, bt+sq), QPoint(bl+w2+sq, bt+sq), QPoint(bl+w2+sq, bt),])
                painter.drawPolygon(polys2)
                # Clip 4
                if self.pin_node == 4:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl, bt+h2-sq), QPoint(bl+sq, bt+h2-sq), QPoint(bl+sq, bt+h2+sq), QPoint(bl, bt+h2+sq),])
                painter.drawPolygon(polys2)
                # Clip 6
                if self.pin_node == 6:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(br, bt+h2-sq), QPoint(br-sq, bt+h2-sq), QPoint(br-sq, bt+h2+sq), QPoint(br, bt+h2+sq),])
                painter.drawPolygon(polys2)
                # Clip 8
                if self.pin_node == 8:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(bl+w2-sq, bb), QPoint(bl+w2-sq, bb-sq), QPoint(bl+w2+sq, bb-sq), QPoint(bl+w2+sq, bb),])
                painter.drawPolygon(polys2)

            # Circle
            minimal_cicle = 30
            if (ww > minimal_cicle and hh > minimal_cicle):
                cir = 4
                # Clip 5
                if self.pin_node == 5:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                    # Lines
                    painter.setPen(QPen(self.color_1, 1, Qt.SolidLine))
                    cir_x, cir_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(ro+90, 360) )
                    neu_x, neu_y = Trig_2D_Points_Rotate(ox, oy, ss, Limit_Looper(90, 360) )
                    painter.drawLine(ox, oy, cir_x, cir_y)
                    painter.drawLine(ox, oy, neu_x, neu_y)
                    # Circle
                    painter.setPen(QPen(self.color_2, 1, Qt.SolidLine))
                    painter.drawEllipse( QRectF( ox-cir, oy-cir, 2*cir, 2*cir ) )
                else:
                    painter.setBrush(QBrush(self.color_1, Qt.SolidPattern))
                    painter.drawEllipse( QRectF( bl+w2-cir, bt+h2-cir, 2*cir, 2*cir ) )

        # Image Zoom
        if self.pin_zoom["bool"] == True:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.NoPen)
            qpixmap = self.pin_zoom["qpixmap"]
            if qpixmap.isNull() == False:
                ww = self.widget_width
                wh = self.widget_height
                qpixmap_scaled = qpixmap.scaled( int(ww), int(wh), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pw = qpixmap_scaled.width()
                ph = qpixmap_scaled.height()
                painter.drawPixmap( QPointF((ww*0.5)-(pw*0.5), (wh*0.5)-(ph*0.5)), qpixmap_scaled)

        # Cursor Selection Square
        check = (self.sel_l == 0 and self.sel_r == 0 and self.sel_t == 0 and self.sel_b == 0)
        if check == False:
            painter.setPen(QPen(self.color_1, 2, Qt.SolidLine))
            painter.setBrush(QBrush(self.color_1, Qt.Dense7Pattern))
            min_x = min(self.origin_x, self.sel_l, self.sel_r)
            max_x = max(self.origin_x, self.sel_l, self.sel_r)
            min_y = min(self.origin_y, self.sel_t, self.sel_b)
            max_y = max(self.origin_y, self.sel_t, self.sel_b)
            ww = max_x - min_x
            hh = max_y - min_y
            painter.drawRect( QRectF(min_x, min_y, ww, hh) )

        # Drag and Drop
        if self.drop == True:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color_1)))
            if self.widget_width < self.widget_height:
                side = self.widget_width
            else:
                side = self.widget_height
            w2 = self.widget_width * 0.5
            h2 = self.widget_height * 0.5
            poly_tri = QPolygon([
                QPoint( int(w2 - 0.3*side), int(h2 - 0.2*side) ),
                QPoint( int(w2 + 0.3*side), int(h2 - 0.2*side) ),
                QPoint( int(w2),            int(h2 + 0.2*side) ),
                ])
            painter.drawPolygon(poly_tri)

#endregion
#region Threads ####################################################################
class Thread_Packer(QThread):
    SIGNAL_REFERENCE = QtCore.pyqtSignal(dict)
    SIGNAL_RESET = QtCore.pyqtSignal(int)

    #region Initialize #############################################################
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
    def Variables_Run(self, method, pin_ref, mode):
        self.method = method
        self.pin_ref = pin_ref
        self.mode = mode

    #endregion
    #region Cycle ##################################################################
    def run(self):
        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # Load images for Cache
        if self.method == "LINEAR":
            self.Pack_Linear(self.pin_ref, self.mode)
        if self.method == "OPTIMAL":
            self.Pack_Optimal(self.pin_ref, self.mode)
        self.SIGNAL_RESET.emit(0)

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo(end)
        time = QTime(0,0).addMSecs(delta)

        # Report
        report = 0
        selection = []
        for i in range(0, len(self.pin_ref)):
            if self.pin_ref[i]["select"] == True:
                selection.append( self.pin_ref[i] )
        if len(selection) > 0:
            img_area = self.Pixmap_Area(selection)
            box = Pixmap_Box(self, selection)
            report = round( (img_area / box["area"]) * 100, 3)
        # Print
        try:QtCore.qDebug("IB " + str(time.toString('hh:mm:ss.zzz')) + " | Packer " + str(self.mode) + " = " + str(report) + "%")
        except:pass

    def Pack_Linear(self, pin_ref, mode):
        # Sort Pins by Area
        sort_pack = []
        for i in range(0, len(pin_ref)):
            if pin_ref[i]["select"] == True:
                pin_ref[i]["pack"] = True
                sort_pack.append(pin_ref[i])
        # Sorting List
        if mode == "LINE":
            sort_pack.sort(reverse=True, key=self.Sort_Height_BB)
        if mode == "COLUMN":
            sort_pack.sort(reverse=True, key=self.Sort_Width_BB)

        # Starting Points
        box = Pixmap_Box(self, sort_pack)
        start_x = box["min_x"]
        start_y = box["min_y"]

        # Apply to Ref List
        for s in range(0, len(sort_pack)):
            # Index
            index = sort_pack[s]["index"]
            pin_ref[index]["pack"] = False

            # Move
            if s == 0:
                Pixmap_Move_BB(self, pin_ref, index, start_x, start_y )
            else:
                if mode == "LINE":
                    Pixmap_Move_BB(self, pin_ref, index, sort_pack[s-1]["br"], start_y )
                if mode == "COLUMN":
                    Pixmap_Move_BB(self, pin_ref, index, start_x, sort_pack[s-1]["bb"] )
            self.SIGNAL_REFERENCE.emit( pin_ref[index] )
    def Pack_Optimal(self, pin_ref, mode):
        # List for Packing
        sort_pack = []
        for i in range(0, len(pin_ref)):
            if pin_ref[i]["select"] == True:
                pin_ref[i]["pack"] = True
                sort_pack.append(pin_ref[i])
        # Sorting List
        if mode == "AREA":
            sort_pack.sort(reverse=True, key=self.Sort_Area_BB)
        if mode == "PERIMETER":
            sort_pack.sort(reverse=True, key=self.Sort_Perimeter_BB)
        if mode == "RATIO":
            sort_pack.sort(reverse=False, key=self.Sort_Ratio_BB)
        if mode == "CLASS":
            ratio_0 = []
            ratio_1 = []
            ratio_2 = []

            for i in range(0, len(sort_pack)):
                ratio = sort_pack[i]["ratio"]
                if ratio < 1:
                    ratio_0.append(sort_pack[i])
                if ratio == 1:
                    ratio_1.append(sort_pack[i])
                if ratio > 1:
                    ratio_2.append(sort_pack[i])

            sort_pack = []
            ratio_0.sort(reverse=True, key=self.Sort_Area_BB)
            ratio_1.sort(reverse=True, key=self.Sort_Area_BB)
            ratio_2.sort(reverse=True, key=self.Sort_Area_BB)

            if len(ratio_0) >= len(ratio_2):
                sort_pack.extend(ratio_0)
                sort_pack.extend(ratio_1)
                sort_pack.extend(ratio_2)
            else:
                sort_pack.extend(ratio_2)
                sort_pack.extend(ratio_1)
                sort_pack.extend(ratio_0)

        # Perfect Area Square
        sum_areas = 0
        for i in range(0, len(pin_ref)):
            if pin_ref[i]["select"] == True:
                sum_areas = sum_areas + pin_ref[i]["area"]
        side = math.ceil( math.sqrt( sum_areas ) ) # to limit the height of the panel

        # Variables
        box = Pixmap_Box(self, sort_pack)
        start_x = box["min_x"]
        start_y = box["min_y"]
        max_x = start_x + side
        max_y = start_y + side

        # Apply to Sort List
        organized = []
        for s in range(0, len(sort_pack)):
            # Variables
            index = sort_pack[s]["index"]
            pin_ref[index]["pack"] = False

            # Pack
            if s == 0:
                # Other Images go offset
                for i in range(1, len(sort_pack)):
                    Pixmap_Move_BB(self, pin_ref, index, 0, 0)

                # Move Starting image
                Pixmap_Move_BB(self, pin_ref, index, start_x, start_y )
                organized.append(sort_pack[s])
                points_x, points_y, points_v = self.Valid_Points(organized)
            else:
                # Variables
                num = len(points_v)
                control = []
                descrim_1 = []
                descrim_2 = []

                # Test all Points
                for p in range(0, num):
                    bl = sort_pack[s]["bl"]
                    br = sort_pack[s]["br"]
                    bt = sort_pack[s]["bt"]
                    bb = sort_pack[s]["bb"]
                    bw = abs(br - bl)
                    bh = abs(bb - bt)
                    
                    # Float
                    px  = points_v[p]["px"]
                    py  = points_v[p]["py"]
                    pxw = points_v[p]["px"] + bw
                    pyh = points_v[p]["py"] + bh
                    # Pixel Integer
                    ipx  = int(px)
                    ipy  = int(py)
                    ipxw = int(px + bw )
                    ipyh = int(py + bh )
                    box = Pixmap_Box(self, organized)

                    # Verify Point with Pixmap if it intersects with previous Pixmaps
                    ignore = False
                    for v in range(0, s):
                        # Variables
                        const = 0.2
                        # Read
                        sortpack_v = sort_pack[v]
                        ivbl  = int(sortpack_v["bl"])
                        ivbr  = int(sortpack_v["br"])
                        ivbt = int(sortpack_v["bt"])
                        ivbb = int(sortpack_v["bb"])
                        # Checks
                        overlap = ((ipxw<=ivbl or ipx>=ivbr) or (ipyh<=ivbt or ipy>=ivbb)) # verify overlap
                        if box["max_x"] >= box["max_y"]:
                            limits = ipxw > (box["max_x"] + (bw * const))
                        else:
                            limits = ipyh > (box["max_y"] + (bh * const))
                        if (overlap == False or limits == True):
                            ignore = True
                            break

                    # Control
                    if ignore == False:
                        box_x = (box["min_x"], box["max_x"], px, pxw)
                        box_y = (box["min_y"], box["max_y"], py, pyh)
                        min_x = min(box_x)
                        min_y = min(box_y)
                        max_x = max(box_x)
                        max_y = max(box_y)

                        dist = Trig_2D_Points_Distance(px, py, max_x, max_y)
                        area = (max_x - min_x) * (max_y - min_y)
                        ctrl = (max_x - px) + (max_y - py)
                        control.append({"area" : area, "dist" : dist, "ctrl" : ctrl, "index" : p })

                # Discriminate
                if len(control) > 0:
                    control.sort(reverse=False, key=self.Sort_Area_Value)
                    control_0 = control[0]["area"]

                    for i in range(0, len(control)):
                        if control[i]["area"] <= control_0:
                            descrim_1.append(control[i])
                        else:
                            descrim_2.append(control[i])
                    # Dont Change Area
                    descrim_1.sort(reverse=True, key=self.Sort_Dist_Value)
                    descrim_2.sort(reverse=False, key=self.Sort_Ctrl_Value)
                    descrim_1.extend(descrim_2)
                    pi = descrim_1[0]["index"]

                    # Move Pixmap
                    Pixmap_Move_BB(self, pin_ref, index, points_v[pi]["px"], points_v[pi]["py"])
                    organized.append(sort_pack[s])
                    points_x, points_y, points_v = self.Valid_Points(organized)

            # Emit Signal
            self.SIGNAL_REFERENCE.emit( pin_ref[index] )

    def Pixmap_Area(self, lista):
        img_area = 0
        for i in range(0, len(lista)):
            img_area += lista[i]["area"]
        return img_area
    def Valid_Points(self, lista):
        # Construct Intersections
        points_x = []
        points_y = []
        for i in range(0, len(lista)):
            # Read
            bl = lista[i]["bl"]
            br = lista[i]["br"]
            bt = lista[i]["bt"]
            bb = lista[i]["bb"]
            # Set
            if bl not in points_x:
                points_x.append(bl)
            if br not in points_x:
                points_x.append(br)
            if bt not in points_y:
                points_y.append(bt)
            if bb not in points_y:
                points_y.append(bb)

        # Start and End Points
        start_x = min(points_x)
        start_y = min(points_y)
        end_x = max(points_x)
        end_y = max(points_y)

        # Construct All Points with Area Sorting
        grid = []
        for y in range(0, len(points_y)):
            for x in range(0, len(points_x)):
                px = points_x[x]
                py = points_y[y]
                dist = Trig_2D_Points_Distance(start_x, start_y, px, py)
                grid.append( {"dist":dist, "px":px, "py":py} )

        # Points to Eliminate
        eliminate = []
        # Checks 1 & 2
        for p in range(0, len(grid)):
            # Points
            entry = grid[p]
            px = int(entry["px"])
            py = int(entry["py"])
            point = (entry["px"], entry["py"])
            # Cycle
            for l in range(0, len(lista)):
                # Intervals
                bl = int(lista[l]["bl"])
                br = int(lista[l]["br"])
                bt = int(lista[l]["bt"])
                bb = int(lista[l]["bb"])
                # Pixel Check
                check_1 = (px == bl and py == bt)
                if (check_1 == True and point not in eliminate):
                    eliminate.append( entry )
                check_2 = (px >= bl and px <= br-1) and (py >= bt and py <= bb-1) # point is inside the draw pixmap
                if (check_2 == True and point not in eliminate):
                    eliminate.append( entry )
        # Checks 3
        for p in range(0, len(grid)):
            # Points
            entry = grid[p]
            px = int(entry["px"])
            py = int(entry["py"])
            # Cycle
            floating = True
            for l in range(0, len(lista)):
                # Intervals
                bl = int(lista[l]["bl"])
                br = int(lista[l]["br"])
                bt = int(lista[l]["bt"])
                bb = int(lista[l]["bb"])
                # Check 3
                check_3 = (px >= bl and px <= br) and (py >= bt and py <= bb) # point is inside a shape
                if check_3 == True:
                    floating = False
            if (floating == True and entry not in eliminate):
                eliminate.append( entry )

        # Valid List
        points_valid = []
        for i in range(0, len(grid)):
            pi = grid[i]
            if pi not in eliminate:
                points_valid.append(pi)
        # Add Extra Points for Start XY axis
        for x in range(0, len(points_valid)):
            if points_valid[x]["px"] == start_x:
                m_y = points_valid[x]
                break
        for y in range(0, len(points_valid)):
            if points_valid[y]["py"] == start_y:
                m_x = points_valid[y]
                break
        for x in range(0, len(points_x)):
            if points_x[x] > m_x["px"]:
                px = points_x[x]
                py = start_y
                dist = Trig_2D_Points_Distance(start_x, start_y, px, py)
                item = {"dist":dist, "px":px, "py":py}
                if item not in points_valid:
                    points_valid.append( item )
        for y in range(0, len(points_y)):
            if points_y[y] > m_y["py"]:
                px = start_x
                py = points_y[y]
                dist = Trig_2D_Points_Distance(start_x, start_y, px, py)
                item = {"dist":dist, "px":px, "py":py}
                if item not in points_valid:
                    points_valid.append( item )
        # Sort
        points_valid.sort(reverse=False, key=self.Sort_Dist_Value)

        # Returns
        return points_x, points_y, points_valid

    #endregion
    #region Sort ###################################################################
    def Sort_Area_Value(self, sort):
        return sort["area"]
    def Sort_Dist_Value(self, sort):
        return sort["dist"]
    def Sort_PX_Value(self, sort):
        return sort["px"]
    def Sort_PY_Value(self, sort):
        return sort["py"]
    def Sort_Ctrl_Value(self, sort):
        return sort["ctrl"]

    def Sort_Width_BB(self, sort):
        bl = sort["bl"]
        br = sort["br"]
        width = abs(br - bl)
        return width
    def Sort_Height_BB(self, sort):
        bt = sort["bt"]
        bb = sort["bb"]
        height = abs(bb - bt)
        return height
    def Sort_Perimeter_BB(self, sort):
        bl = sort["bl"]
        br = sort["br"]
        bt = sort["bt"]
        bb = sort["bb"]
        width = abs(br - bl)
        height = abs(bb - bt)
        perimeter = (2 * width) + (2 * height)
        return perimeter
    def Sort_Area_BB(self, sort):
        bl = sort["bl"]
        br = sort["br"]
        bt = sort["bt"]
        bb = sort["bb"]
        width = abs(br - bl)
        height = abs(bb - bt)
        area = width * height
        return area
    def Sort_Ratio_BB(self, sort):
        bl = sort["bl"]
        br = sort["br"]
        bt = sort["bt"]
        bb = sort["bb"]
        width = abs(br - bl)
        height = abs(bb - bt)
        ratio = width / height
        return ratio

    #endregion

#endregion
#region Settings ###################################################################
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
    SIGNAL_PATH = QtCore.pyqtSignal(list)

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
            parent = "..." + str(os.path.basename(os.path.dirname(self.directory)))
            cmenu.addSection(current)
            cmenu_parent = cmenu.addAction(parent)
            cmenu.addSection(" ")
            actions = {}
            for i in range(0, len(self.folders)):
                string = "\\" + str(os.path.basename(self.folders[i]))
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
                self.SIGNAL_PATH.emit( [path, True] )

#endregion

