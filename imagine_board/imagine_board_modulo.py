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


import math
import os
from krita import *
from PyQt5 import QtWidgets, QtCore, uic


def kritaTheme(self):
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


class ImagineBoard_Preview(QWidget):
    # General
    SIGNAL_CLICK = QtCore.pyqtSignal(int)
    SIGNAL_WHEEL = QtCore.pyqtSignal(int)
    SIGNAL_STYLUS = QtCore.pyqtSignal(int)
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    # Preview
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    SIGNAL_FUNCTION = QtCore.pyqtSignal(list)
    SIGNAL_PIN = QtCore.pyqtSignal(str)
    SIGNAL_RANDOM = QtCore.pyqtSignal(int)
    SIGNAL_LOCATION = QtCore.pyqtSignal(str)
    SIGNAL_CLIP = QtCore.pyqtSignal(list)
    SIGNAL_CROP = QtCore.pyqtSignal(list)
    SIGNAL_FIT = QtCore.pyqtSignal(bool)
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal(str)
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal(str)
    SIGNAL_COLOR = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        super(ImagineBoard_Preview, self).__init__(parent)
        # Display
        self.number = 0
        self.active = True
        self.expand = False
        self.movie = False
        self.label = None
        self.press = False
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
        # Movie
        self.qmovie_frame = 0
        self.movie_width = 0
        self.movie_height = 0
        # Events
        self.origin_x = 0
        self.origin_y = 0
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
        # Fit
        self.fit_state = False
        # Startup
        self.Set_Default()
        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
        # Animation
        self.directory = ""
        # Color
        self.pick_color = False
        self.red = 0
        self.green = 0
        self.blue = 0
        # Edit
        self.edit_greyscale = False
        self.edit_invert_h = False
        self.edit_invert_v = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Label(self, label):
        self.label = label
    def Set_Default(self):
        self.path = ""
        self.qpixmap = QPixmap()
        self.qmovie = QMovie()
        self.update()
    def Set_Default_Preview(self, path, qpixmap):
        self.Preview_Reset()
        self.Clip_Off()
        self.label.clear()
        self.movie = False
        self.path = path
        self.qpixmap = qpixmap
        self.qmovie.stop()
        self.update()
    def Set_QPixmap_Preview(self, path):
        self.Preview_Reset()
        self.Clip_Off()
        self.label.clear()
        self.movie = False
        self.path = path
        self.qpixmap = QPixmap(path)
        self.qmovie.stop()
        self.update()
    def Set_QMovie_Preview(self, path):
        self.Preview_Reset()
        self.Clip_Off()
        self.path = path
        self.qpixmap = QPixmap(path)
        self.qmovie = QMovie(path)
        self.clip_state == False
        if self.qmovie.isValid() == True:
            # # Buffer Movie
            # self.bytesio = io.BytesIO()
            # img.save(fp=self.bytesio, format="GIF", append_images=imgs, save_all=True, duration=GIF_DELAY, loop=0)
            # qbytearray = QByteArray(self.bytesio.getvalue())
            # self.bytesio.close()
            # qbuffer = QBuffer(qbytearray)

            # self.qmovie.setDevice(qbuffer)
            self.qmovie.setCacheMode(QMovie.CacheAll)
            # Variables
            self.movie = True
            self.label.setMovie(self.qmovie)
            self.update()

            # QtCore.qDebug( str( self.qmovie.scaledSize().rwidth() ) )
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

    # Trignometry
    def Math_1D_Limit(self, var):
        if var <= 0:
            var = 0
        if var >= 1:
            var = 1
        return var
    def Math_2D_Points_Distance(self, x1, y1, x2, y2):
        dd = math.sqrt( math.pow((x1-x2),2) + math.pow((y1-y2),2) )
        return dd

    # Movie
    def Movie_Pause(self):
        if self.movie == True:
            self.qmovie.setPaused(True)
            self.qmovie_frame = self.qmovie.currentFrameNumber()
            # self.qmovie.stop()

            self.Movie_Log()
    def Movie_Play(self):
        if self.movie == True:
            self.qmovie.setPaused(False)
            # self.qmovie.start()

            self.Movie_Log()
    def Movie_Frame_Back(self):
        if self.movie == True:
            self.qmovie.stop()
            self.qmovie_frame = self.movie_loop(self.qmovie_frame - 1, self.qmovie.frameCount())
            jump = self.qmovie.jumpToFrame(self.qmovie_frame)
            if jump == True:
                self.qmovie.setPaused(True)
                # self.qmovie.stop()

            self.Movie_Log()
    def Movie_Frame_Forward(self):
        if self.movie == True:
            self.qmovie.stop()
            self.qmovie_frame = self.movie_loop(self.qmovie_frame + 1, self.qmovie.frameCount())
            jump = self.qmovie.jumpToFrame(self.qmovie_frame)
            if jump == True:
                self.qmovie.setPaused(True)
                # self.qmovie.stop()

            self.Movie_Log()
    def Movie_Screenshot(self, directory_path):
        if self.movie == True:
            directory = os.path.dirname(self.path) # dir
            bn = os.path.basename(self.path) # name.ext
            extension = os.path.splitext(self.path)[1] # .ext
            n = bn.find(extension)
            base = bn[:n] # name
            save_path = os.path.normpath(directory + "/" + base + "_" + str(self.qmovie_frame).zfill(4) + ".png")

            screenshot_qpixmap = self.qmovie.currentPixmap()
            screenshot_qpixmap.save(save_path)

            self.Movie_Log()

    def Movie_Log(self):
        QtCore.qDebug("frame index = " + str(self.qmovie_frame))
        QtCore.qDebug("frame count = " + str(self.qmovie.frameCount()))
        QtCore.qDebug("speed = " + str(self.qmovie.speed()))
        QtCore.qDebug("state = " + str(self.qmovie.state()))
        QtCore.qDebug("-----------------------------------")
    def movie_loop(self, value, max):
        if value <= 0:
            value = max + value
        if value >= max:
            value = max - value
        return value

    # Preview Calculations
    def Preview_Reset(self):
        self.zoom = 1
        self.focus_x = 0.5
        self.focus_y = 0.5
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
    def Preview_Edit(self, pixmap):
        # Load
        qimage = QImage(self.path)
        # Grayscale
        if self.edit_greyscale == True:
            value = 24
        else:
            value = 6
        qimage1 = qimage.convertToFormat(value)
        # Invert Horizontal and Vertical
        image23 = qimage1.mirrored(self.edit_invert_h, self.edit_invert_v)

        # Apply Pixmap to rendering list
        self.qpixmap = QPixmap.fromImage(image23)
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
            self.Preview_Reset()
            # Point of event
            event_x = event.x()
            event_y = event.y()
            # Points in Widget Space
            self.clip_p1_img = [self.offset_x, self.offset_y]
            self.clip_p2_img = [self.clip_p1_img[0] + (self.scaled_width * self.zoom), self.clip_p1_img[1]]
            self.clip_p3_img = [self.clip_p1_img[0] + (self.scaled_width * self.zoom), self.clip_p1_img[1] + (self.scaled_height * self.zoom)]
            self.clip_p4_img = [self.clip_p1_img[0], self.clip_p1_img[1] + (self.scaled_height * self.zoom)]
            relative = [event_x - self.clip_p1_img[0], event_y - self.clip_p1_img[1]]
            width_img = self.clip_p2_img[0] - self.clip_p1_img[0]
            height_img = self.clip_p4_img[1] - self.clip_p1_img[1]
            per_x = self.Math_1D_Limit(relative[0] / width_img)
            per_y = self.Math_1D_Limit(relative[1] / height_img)
            # Distances
            dist1 = self.Math_2D_Points_Distance(self.clip_p1_img[0] + (self.clip_p1_per[0] * self.scaled_width),self.clip_p1_img[1] + (self.clip_p1_per[1] * self.scaled_height), event_x,event_y)
            dist2 = self.Math_2D_Points_Distance(self.clip_p1_img[0] + (self.clip_p2_per[0] * self.scaled_width),self.clip_p1_img[1] + (self.clip_p2_per[1] * self.scaled_height), event_x,event_y)
            dist3 = self.Math_2D_Points_Distance(self.clip_p1_img[0] + (self.clip_p3_per[0] * self.scaled_width),self.clip_p1_img[1] + (self.clip_p3_per[1] * self.scaled_height), event_x,event_y)
            dist4 = self.Math_2D_Points_Distance(self.clip_p1_img[0] + (self.clip_p4_per[0] * self.scaled_width),self.clip_p1_img[1] + (self.clip_p4_per[1] * self.scaled_height), event_x,event_y)
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
            list = [
                self.clip_state,
                self.clip_p1_per[0] * self.image_width,
                self.clip_p1_per[1] * self.image_height,
                self.width_per * self.image_width,
                self.height_per * self.image_height
                ]
            self.SIGNAL_CLIP.emit(list)
            # Support Crop
            crop = [
                self.clip_p1_per[0],
                self.clip_p1_per[1],
                self.width_per,
                self.height_per
                ]
            self.SIGNAL_CROP.emit(crop)
            # Finish
            self.update()

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Color_Apply(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
            self.Preview_Reset()
            self.Clip_Off()
            self.Mouse_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Preview_Reset()
            self.Clip_Off()
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)):
            self.Preview_Position(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            self.Preview_Zoom(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            self.Preview_Reset()
            self.Clip_Off()
        # MMB
        if (event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Preview_Position(event)
        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseMoveEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Color_Apply(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            self.SIGNAL_DRAG.emit(self.path)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)):
            self.Preview_Position(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            self.Preview_Zoom(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            self.Preview_Reset()
            self.Clip_Off()
        # MMB
        if (event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Preview_Position(event)
        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseDoubleClickEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_MODE.emit(1)
    def mouseReleaseEvent(self, event):
        self.origin_x = 0
        self.origin_y = 0
        self.press = False
        self.drop = False
        self.update()
    def Mouse_Pagination(self, event):
        self.Preview_Reset()
        self.Clip_Off()
        margin = 0.5
        if event.y() > (self.widget_height * margin):
            self.SIGNAL_CLICK.emit(-1)
        else:
            self.SIGNAL_CLICK.emit(1)
    def Stylus_Pagination(self, event):
        self.Preview_Reset()
        self.Clip_Off()
        delta = 40
        dist_x = (event.x() - self.origin_x) / delta
        dist_y = -((event.y() - self.origin_y) / delta)
        if abs(dist_x) >= abs(dist_y):
            dist = dist_x
        else:
            dist = dist_y
        if dist <= -1:
            self.SIGNAL_STYLUS.emit(-1)
            self.origin_x = event.x()
            self.origin_y = event.y()
        if dist >= 1:
            self.SIGNAL_STYLUS.emit(1)
            self.origin_x = event.x()
            self.origin_y = event.y()
    def Color_Apply(self, event):
        if self.pick_color == True:
            # Geometry
            tl = QPoint(0, 0)
            br = QPoint(self.width(), self.height() )
            pixmap = self.grab(QRect(tl, br))
            image = pixmap.toImage()
            color = image.pixelColor( event.x(), event.y() )
            # Apply Color Values
            self.red = color.red()/255
            self.green = color.green()/255
            self.blue = color.blue()/255
            self.SIGNAL_COLOR.emit([self.red, self.green, self.blue])
            self.update()

    # Wheel Events
    def wheelEvent(self, event):
        delta = event.angleDelta()
        # Zoom
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self.Wheel_Zoom(event, delta)
        # Change Index
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Wheel_Index(event, delta)
    def Wheel_Zoom(self, event, delta):
        if delta.y() > 20:
            self.zoom += 0.1
        elif delta.y() < -20:
            self.zoom -= 0.1
        self.update()
    def Wheel_Index(self, event, delta):
        if delta.y() > 20:
            self.Preview_Reset()
            self.Clip_Off()
            self.SIGNAL_WHEEL.emit(+1)
        elif delta.y() < -20:
            self.Preview_Reset()
            self.Clip_Off()
            self.SIGNAL_WHEEL.emit(-1)

    # Context Menu Event
    def contextMenuEvent(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            cmenu = QMenu(self)
            # Actions
            cmenu_function = cmenu.addAction("Function >>")
            cmenu_pin = cmenu.addAction("Pin Reference")
            cmenu.addSeparator()
            cmenu_random = cmenu.addAction("Random")
            cmenu_location = cmenu.addAction("Location")
            cmenu_copy = cmenu.addMenu("Copy")
            cmenu_file = cmenu_copy.addAction("File Name")
            cmenu_directory = cmenu_copy.addAction("Path Directory")
            cmenu_path = cmenu_copy.addAction("Path Full")
            cmenu.addSeparator()
            cmenu_pick_color = cmenu.addAction("Pick Color")
            cmenu_pick_color.setCheckable(True)
            cmenu_pick_color.setChecked(self.pick_color)
            cmenu_edit_greyscale = cmenu.addAction("View Grayscale")
            cmenu_edit_greyscale.setCheckable(True)
            cmenu_edit_greyscale.setChecked(self.edit_greyscale)
            cmenu_edit_invert_h = cmenu.addAction("Flip Horizontal")
            cmenu_edit_invert_h.setCheckable(True)
            cmenu_edit_invert_h.setChecked(self.edit_invert_h)
            cmenu_edit_invert_v = cmenu.addAction("Flip Vertical")
            cmenu_edit_invert_v.setCheckable(True)
            cmenu_edit_invert_v.setChecked(self.edit_invert_v)
            cmenu.addSeparator()
            cmenu_clip = cmenu.addAction("Clip Image")
            cmenu_clip.setCheckable(True)
            cmenu_clip.setChecked(self.clip_state)
            cmenu_fit = cmenu.addAction("Fit Insert")
            cmenu_fit.setCheckable(True)
            cmenu_fit.setChecked(self.fit_state)
            cmenu.addSeparator()
            cmenu_document = cmenu.addAction("New Document")
            cmenu_insert_ref = cmenu.addAction("Insert Reference")
            cmenu_insert_layer = cmenu.addAction("Insert Layer")
            action = cmenu.exec_(self.mapToGlobal(event.pos()))
            # Triggers
            if action == cmenu_function:
                string = [os.path.normpath( self.path )]
                self.SIGNAL_FUNCTION.emit(string)
            if action == cmenu_pin:
                self.SIGNAL_PIN.emit(self.path)
            if action == cmenu_random:
                self.Preview_Reset()
                self.Clip_Off()
                self.SIGNAL_RANDOM.emit(0)
            if action == cmenu_location:
                self.SIGNAL_LOCATION.emit(self.path)
            if action == cmenu_file:
                copy = QApplication.clipboard()
                copy.clear()
                copy.setText(os.path.basename(self.path))
            if action == cmenu_directory:
                copy = QApplication.clipboard()
                copy.clear()
                copy.setText(os.path.normpath(os.path.dirname(self.path)))
            if action == cmenu_path:
                copy = QApplication.clipboard()
                copy.clear()
                copy.setText(os.path.normpath(self.path))
            if action == cmenu_pick_color:
                self.pick_color = not self.pick_color
            if action == cmenu_edit_greyscale:
                self.edit_greyscale = not self.edit_greyscale
                self.Preview_Edit(self.qpixmap)
            if action == cmenu_edit_invert_h:
                self.edit_invert_h = not self.edit_invert_h
                self.Preview_Edit(self.qpixmap)
            if action == cmenu_edit_invert_v:
                self.edit_invert_v = not self.edit_invert_v
                self.Preview_Edit(self.qpixmap)
            if action == cmenu_clip:
                if self.movie == False:
                    self.Preview_Reset()
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
            if action == cmenu_fit:
                self.fit_state = not self.fit_state
                self.SIGNAL_FIT.emit(self.fit_state)
            if action == cmenu_document:
                self.SIGNAL_NEW_DOCUMENT.emit(self.path)
            if action == cmenu_insert_ref:
                self.SIGNAL_INSERT_REFERENCE.emit(self.path)
            if action == cmenu_insert_layer:
                self.SIGNAL_INSERT_LAYER.emit(self.path)

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
                # Files and Folders
                length = len(event.mimeData().urls())
                for i in range(0, length):
                    item = os.path.normpath( event.mimeData().urls()[i].toLocalFile() )
                    mime_paths.append(item)
                mime_paths.sort()
                self.SIGNAL_FUNCTION.emit(mime_paths)
            event.accept()
        else:
            event.ignore()
        self.update()

    # Widget Event
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        pass

    # Painter
    def paintEvent(self, event):
        # Theme
        kritaTheme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Calculations For Image
        self.Image_Calculations()

        # Save State for Painter display
        if self.movie == True:
            self.qmovie.setScaledSize(QSize(self.movie_width, self.movie_height))
            self.qmovie.start()
        else:
            painter.save()
            painter.translate(self.offset_x, self.offset_y)
            painter.scale(self.size * self.zoom, self.size * self.zoom)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtCore.Qt.NoBrush)
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

        # Restore Space to normal space
        if self.movie == False:
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
            check = self.origin_x == 0 and self.origin_y == 0
            if check == True:
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QBrush(QColor(self.color1)))
                if self.widget_width < self.widget_height:
                    side = self.widget_width
                else:
                    side = self.widget_height
                dim = 0.4
                dim_half = dim * 0.5
                painter.drawEllipse(
                    (self.widget_width*0.5) - (side * dim_half),
                    (self.widget_height*0.5) - (side * dim_half),
                    side * dim,
                    side * dim
                    )

        # Colors
        if (self.pick_color == True and self.origin_x != 0 and self.origin_y != 0):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.red*255, self.green*255, self.blue*255)))
            painter.drawRect(0,0,50,50)
    def Image_Calculations(self):
        # Calculations for Image
        self.image_width = self.qpixmap.width()
        self.image_height = self.qpixmap.height()
        try:
            self.var_w = self.widget_width / self.image_width
            self.var_h = self.widget_height / self.image_height
        except:
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
    SIGNAL_DRAG = QtCore.pyqtSignal(list)
    # Grid
    SIGNAL_PREVIEW = QtCore.pyqtSignal(list)
    SIGNAL_FUNCTION_GRID = QtCore.pyqtSignal(list) # Location
    SIGNAL_FUNCTION_DROP = QtCore.pyqtSignal(list) # Path
    SIGNAL_PIN = QtCore.pyqtSignal(list)
    SIGNAL_NAME = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        super(ImagineBoard_Grid, self).__init__(parent)
        self.widget_width = 1
        self.widget_height = 1
        self.origin_x = 0
        self.origin_y = 0
        self.default = QPixmap()
        self.grid_horz = 3
        self.grid_vert = 3
        self.tn_x = 256
        self.tn_y = 256
        self.qpixmap_list = []
        self.display_bool = False
        self.Set_Display(self.display_bool)
        self.press = False
        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Default(self, default_qpixmap):
        self.default_qpixmap = default_qpixmap
    def Set_QPixmaps(self, qpixmap_list):
        self.qpixmap_list = qpixmap_list
    def Set_Size(self, widget_width, widget_height):
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.tn_x = self.widget_width / self.grid_horz
        self.tn_y = self.widget_height / self.grid_vert
    def Set_Grid(self, grid_horz, grid_vert):
        self.grid_horz = grid_horz
        self.grid_vert = grid_vert
        self.tn_x = self.widget_width / grid_horz
        self.tn_y = self.widget_height / grid_vert
    def Set_Display(self, display):
        self.display_bool = display
        if display == False:
            self.display_ratio = Qt.KeepAspectRatioByExpanding
        elif display == True:
            self.display_ratio = Qt.KeepAspectRatio
        self.update()

    # Calculations
    def Hover_Square(self, event):
        try:
            a = int((event.x() * self.grid_horz) / self.widget_width)
            b = int((event.y() * self.grid_vert) / self.widget_height)
            a = self.Value_Limit(a, 0 , self.grid_horz-1)
            b = self.Value_Limit(b, 0 , self.grid_vert-1)
            hover_square = [a,b]
        except:
            hover_square = [0,0]
        return hover_square
    def Value_Limit(self, value, minimum, maximum):
        if value <= minimum:
            value = minimum
        if value >= maximum:
            value = maximum
        return value

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_NAME.emit(self.Hover_Square(event))
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
            self.Mouse_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            pass
    def mouseMoveEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_NAME.emit(self.Hover_Square(event))
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            self.SIGNAL_DRAG.emit(self.Hover_Square(event))
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)):
            pass
    def mouseDoubleClickEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_PREVIEW.emit(self.Hover_Square(event))
    def mouseReleaseEvent(self, event):
        self.press = False
        self.origin_x = 0
        self.origin_y = 0
        self.update()
    def Mouse_Pagination(self, event):
        margin = 0.5
        if event.y() > (self.widget_height * margin):
            self.SIGNAL_CLICK.emit(-1)
        else:
            self.SIGNAL_CLICK.emit(1)
    def Stylus_Pagination(self, event):
        # Variables
        event_y = event.y()
        if self.origin_y > 0:
            ratio = int(self.origin_y / self.tn_y)
            limit_below = int(self.tn_y * ratio)
            limit_upper = int(limit_below + self.tn_y)
        elif self.origin_y < 0:
            ratio = int(self.origin_y / self.tn_y)
            limit_upper = int(self.tn_y * ratio)
            limit_below = int(limit_upper - self.tn_y)
        # Update
        if event_y < limit_below:
            self.SIGNAL_STYLUS.emit(+1)
            self.origin_y -= self.tn_y
        elif event_y > limit_upper:
            self.SIGNAL_STYLUS.emit(-1)
            self.origin_y += self.tn_y

    # Wheel Events
    def wheelEvent(self, event):
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Wheel_Index(event, delta)
    def Wheel_Index(self, event, delta):
        if delta.y() > 20:
            self.SIGNAL_WHEEL.emit(+1)
        elif delta.y() < -20:
            self.SIGNAL_WHEEL.emit(-1)

    # Context Menu
    def contextMenuEvent(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            cmenu = QMenu(self)
            # Actions
            cmenu_function = cmenu.addAction("Function >>")
            cmenu_pin = cmenu.addAction("Pin Reference")
            cmenu.addSeparator()
            cmenu_ratio = cmenu.addAction("Fit Ratio")
            cmenu_ratio.setCheckable(True)
            cmenu_ratio.setChecked(self.display_bool)
            action = cmenu.exec_(self.mapToGlobal(event.pos()))
            # Triggers
            if action == cmenu_function:
                self.SIGNAL_FUNCTION_GRID.emit(self.Hover_Square(event))
            if action == cmenu_pin:
                self.SIGNAL_PIN.emit(self.Hover_Square(event))
            if action == cmenu_ratio:
                self.Set_Display(not self.display_bool)

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
                # Files and Folders
                length = len(event.mimeData().urls())
                for i in range(0, length):
                    item = os.path.normpath( event.mimeData().urls()[i].toLocalFile() )
                    mime_paths.append(item)
                mime_paths.sort()
                self.SIGNAL_FUNCTION_DROP.emit(mime_paths)
            event.accept()
        else:
            event.ignore()
        self.update()

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        pass

    # Painter
    def paintEvent(self, event):
        # Theme
        kritaTheme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Draw Pixmaps
        for i in range(0, len(self.qpixmap_list)):
            if self.qpixmap_list[i][2] != "":
                # # Clip Mask
                px = self.qpixmap_list[i][0] * self.tn_x
                py = self.qpixmap_list[i][1] * self.tn_y
                thumbnail = QRectF(px,py, self.tn_x,self.tn_y)
                painter.setClipRect(thumbnail, Qt.ReplaceClip)

                # Render Pixmap
                qpixmap = self.qpixmap_list[i][3]
                if qpixmap.isNull() == False:
                    render = qpixmap.scaled(self.tn_x+1, self.tn_y+1, self.display_ratio, Qt.FastTransformation)
                else:
                    render = self.default_qpixmap.scaled(self.tn_x+1, self.tn_y+1, self.display_ratio, Qt.FastTransformation)
                render_width = render.width()
                render_height = render.height()
                offset_x = (self.tn_x - render_width) * 0.5
                offset_y = (self.tn_y - render_height) * 0.5
                painter.drawPixmap(px + offset_x, py + offset_y, render)
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
                dim = 0.4
                dim_half = dim * 0.5
                painter.drawEllipse(
                    (self.widget_width*0.5) - (side * dim_half),
                    (self.widget_height*0.5) - (side * dim_half),
                    side * dim,
                    side * dim
                    )


class ImagineBoard_Reference(QWidget):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    SIGNAL_DROP = QtCore.pyqtSignal(str)
    # Reference
    SIGNAL_SAVE = QtCore.pyqtSignal(list)
    SIGNAL_LOAD = QtCore.pyqtSignal(int)

    # Init
    def __init__(self, parent):
        super(ImagineBoard_Reference, self).__init__(parent)
        # Widget
        self.widget_width = 1
        self.widget_height = 1
        self.origin_x = 0
        self.origin_y = 0
        self.event_x = 0
        self.event_y = 0

        # References
        self.ref = []
        self.selection = []
        self.index = None
        self.active = False
        self.delta_x = 0
        self.delta_y = 0
        self.node = 0
        self.limit_x = []
        self.limit_y = []

        # Camera
        self.camera_tx = 0
        self.camera_ty = 0
        self.camera_dx = 1
        self.camera_dy = 1
        self.opt_square = [0,0,0,0]
        self.camera_wheel = None

        # Selection
        self.select_state = False
        self.select_ox = 0
        self.select_oy = 0
        self.select_ex = 0
        self.select_ey = 0

        # Board
        self.pin_zoom = [False, ""]
        self.kra_bind = False

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
    def Set_Active(self, bool):
        self.active = bool
        self.update()

    def Pin_Add(self, pin):
        pin["qpixmap"] = QPixmap(pin["path"])
        self.ref.append(pin)
        self.Pin_Edit(None, len(self.ref)-1)
        self.update()
    def Pin_Drop(self, path):
        self.SIGNAL_DROP.emit(path)
    def Pin_Replace(self, index, path):
        if len(self.ref) > 0:
            self.ref[index]["path"] = path
            self.update()
    def Pin_NewPath(self, index):
        path = QFileDialog(QWidget(self))
        path.setFileMode(QFileDialog.ExistingFile)
        file_path = path.getOpenFileName(self, "Select File", os.path.dirname(self.ref[index]["path"]) )[0]
        QtCore.qDebug(str(file_path))
        file_path = os.path.normpath( file_path )
        if (file_path != "" and file_path != "."):
            self.Pin_Clean(self.index)
            self.Pin_Drop(file_path)
    def Pin_Zoom(self, bool, qimage):
        self.pin_zoom = [bool, qimage]
        self.update()
    def Pin_Clean(self, index):
        if index is not None:
            self.ref.pop(index)
        self.selection.clear()
        self.update()
    def Pin_Edit(self, operation, index):
        # Load
        qimage = QImage(self.ref[index]["path"])
        # Edit Operations
        e1 = self.ref[index]["egs"]
        e2 = self.ref[index]["efx"]
        e3 = self.ref[index]["efy"]
        if operation == "egs":
            e1 = not e1
            self.ref[index]["egs"] = e1
        if operation == "efx":
            e2 = not e2
            self.ref[index]["efx"] = e2
        if operation == "efy":
            e3 = not e3
            self.ref[index]["efy"] = e3
        # Grayscale
        if e1 == True:
            value = 24
        else:
            value = 6
        qimage1 = qimage.convertToFormat(value)
        # Invert Horizontal and Vertical
        image23 = qimage1.mirrored(e2, e3)

        # Apply Pixmap to rendering list
        qpixmap = QPixmap.fromImage(image23)
        self.ref[index]["qpixmap"] = qpixmap
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
    def Board_Clean(self):
        self.ref.clear()
        self.update()

    # Operations
    def Selection_Origin(self, event):
        self.select_ox = event.x()
        self.select_oy = event.y()
        self.update()
    def Selection_Replace(self, index):
        self.selection = [index]
        self.update()
    def Selection_Add(self, index):
        if index not in self.selection:
            self.selection.append(index)
        else:
            pop_index = self.selection.index(index)
            self.selection.pop(pop_index)
        self.update()
    def Selection_Clear(self):
        self.selection.clear()
        self.update()
    def Selection_Square(self, event):
        # Painter
        self.select_ex = event.x() - self.select_ox
        self.select_ey = event.y() - self.select_oy
        # Square
        if self.event_x > self.select_ox:
            square_top_left_x = self.select_ox
            square_bot_right_x = self.event_x
        else:
            square_top_left_x = self.event_x
            square_bot_right_x = self.select_ox
        if self.event_y > self.select_oy:
            square_top_left_y = self.select_oy
            square_bot_right_y = self.event_y
        else:
            square_top_left_y = self.event_y
            square_bot_right_y = self.select_oy
        # Selection
        self.selection.clear()
        for i in range(0, len(self.ref)):
            if (
            self.ref[i]["px"] >= square_top_left_x and
            self.ref[i]["py"] >= square_top_left_y and
            (self.ref[i]["px"] + self.ref[i]["dw"]) <= square_bot_right_x and
            (self.ref[i]["py"] + self.ref[i]["dh"]) <= square_bot_right_y):
                self.selection.append(self.ref[i]["path"])
        self.update()
    def Selection_Clean(self, selection):
        indexes = []
        if len(selection) > 0:
            for r in range(0, len(self.ref)):
                for s in range(0, len(selection)):
                    if self.ref[r]["path"] == selection[s]:
                        indexes.append(r)
        for i in range(0, len(indexes)):
            self.ref.pop(indexes[i] - i)
        self.selection = []
        self.update()

    def Pack_Straight(self, orientation):
        # Create Sort List
        sort = []
        if orientation == "line":
            sort = self.Selection_Sort(self.selection, "dh")
        if orientation == "column":
            sort = self.Selection_Sort(self.selection, "dw")
        mpx, mpy, mdx, mdy = self.Pixmap_Area(sort)
        # Move Images
        sort[0]["px"] = mpx
        sort[0]["py"] = mpy
        for s in range(1, len(sort)):
            i = s - 1
            if orientation == "line":
                sort[s]["px"] = sort[i]["px"] + sort[i]["dw"]
                sort[s]["py"] = mpy
            if orientation == "column":
                sort[s]["px"] = mpx
                sort[s]["py"] = sort[i]["py"] + sort[i]["dh"]
        # Copy values back to References List
        for r in range(0, len(self.ref)):
            for a in range(0, len(sort)):
                if self.ref[r]["path"] == sort[a]["path"]:
                    self.ref[r] = sort[a]
        # Update the Display
        self.update()
    def Pack_Optimized(self):
        pass

    def Selection_Sort(self, lista, index):
        initial = []
        for r in range(0, len(self.ref)):
            if self.ref[r]["path"] in lista:
                initial.append(self.ref[r])
        topic = []
        for t in range(0, len(initial)):
            topic.append(initial[t][index])
        topic.sort()
        topic.reverse()
        sorted = []
        for t in range(0, len(topic)):
            for i in range(0, len(initial)):
                if topic[t] == initial[i][index]:
                    duplicates = False
                    for s in range(0, len(sorted)):
                        if initial[i]["path"] == sorted[s]["path"]:
                            duplicates = True
                    if duplicates == False:
                        sorted.append(initial[i])
        return sorted
    def Selection_Area(self, lista):
        if len(lista) > 0:
            px = []
            py = []
            dx = []
            dy = []
            for r in range(0, len(self.ref)):
                for l in range(0, len(lista)):
                    if self.ref[r]["path"] == lista[l]:
                        a = self.ref[r]["px"]
                        b = self.ref[r]["py"]
                        c = self.ref[r]["dw"]
                        d = self.ref[r]["dh"]
                        px.append(a)
                        py.append(b)
                        dx.append(a + c)
                        dy.append(b + d)
            spx = min(px)
            spy = min(py)
            sdx = -spx + max(dx)
            sdy = -spy + max(dy)
            return spx, spy, sdx, sdy

    def Index_Closest(self, event):
        # Detect Image Index
        index = None
        if (self.ref != [] and self.ref != None):
            self.ref.reverse()
            for i in range(0, len(self.ref)):
                ex = event.x()
                ey = event.y()
                px = self.ref[i]["px"]
                py = self.ref[i]["py"]
                sx = self.ref[i]["dw"]
                sy = self.ref[i]["dh"]
                if (ex >= px and ex <= (px+sx) and ey >= py and ey <= (py+sy)): # Clicked inside the image
                    index = i
                    self.delta_x = self.origin_x - px
                    self.delta_y = self.origin_y - py
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
        if self.index is not None:
            self.active = True
            self.node = self.Index_Node(event)
        else:
            self.active = False
            self.node = 0
            self.delta_x = 0
            self.delta_y = 0

        # Deltas
        event_x = event.x()
        event_y = event.y()
        self.deltas = []
        for i in range(0, len(self.ref)):
            delta_x = self.origin_x - self.ref[i]["px"]
            delta_y = self.origin_y - self.ref[i]["py"]
            self.deltas.append([delta_x, delta_y])
    def Index_Limits(self, event, index):
        if index != None:
            # X Axis
            self.limit_x = []
            for i in range(0, len(self.ref)):
                if i != index:
                    a = self.ref[i]["px"]
                    b = a + self.ref[i]["dw"]
                    if a not in self.limit_x:
                        self.limit_x.append(a)
                    if b not in self.limit_x:
                        self.limit_x.append(b)

            # Y Axis
            self.limit_y = []
            for i in range(0, len(self.ref)):
                if i != index:
                    a = self.ref[i]["py"]
                    b = a + self.ref[i]["dh"]
                    if a not in self.limit_y:
                        self.limit_y.append(a)
                    if b not in self.limit_y:
                        self.limit_y.append(b)
    def Index_Points(self, index):
        # Node Points
        n1_x = self.ref[index]["px"]
        n1_y = self.ref[index]["py"]
        n2_x = self.ref[index]["px"] + (self.ref[index]["dw"] * 0.5)
        n2_y = self.ref[index]["py"]
        n3_x = self.ref[index]["px"] + self.ref[index]["dw"]
        n3_y = self.ref[index]["py"]
        n4_x = self.ref[index]["px"]
        n4_y = self.ref[index]["py"] + (self.ref[index]["dh"] * 0.5)
        n5_x = self.ref[index]["px"] + (self.ref[index]["dw"] * 0.5)
        n5_y = self.ref[index]["py"] + (self.ref[index]["dh"] * 0.5)
        n6_x = self.ref[index]["px"] + self.ref[index]["dw"]
        n6_y = self.ref[index]["py"] + (self.ref[index]["dh"] * 0.5)
        n7_x = self.ref[index]["px"]
        n7_y = self.ref[index]["py"] + self.ref[index]["dh"]
        n8_x = self.ref[index]["px"] + (self.ref[index]["dw"] * 0.5)
        n8_y = self.ref[index]["py"] + self.ref[index]["dh"]
        n9_x = self.ref[index]["px"] + self.ref[index]["dw"]
        n9_y = self.ref[index]["py"] + self.ref[index]["dh"]
        node = [ [n1_x, n1_y], [n2_x, n2_y], [n3_x, n3_y], [n4_x, n4_y], [n5_x, n5_y], [n6_x, n6_y], [n7_x, n7_y], [n8_x, n8_y], [n9_x, n9_y] ]
        # Return
        return node
    def Index_Node(self, event):
        # Node Choice
        nodes = self.Index_Points(self.index)
        check = []
        for i in range(0, len(nodes)):
            point_x = nodes[i][0]
            point_y = nodes[i][1]
            dist = self.Math_2D_Points_Distance(point_x, point_y, self.origin_x, self.origin_y)
            check.append(dist)
        value = min(check)
        if value <= 20:
            nodo = check.index(value) + 1
        else:
            nodo = 0
        return nodo

    def Pixmap_Operation(self, event, index, node, selection):
        scale = [1,3,7,9]
        clip = [2,4,6,8]
        if node in scale:
            self.Pixmap_Scale(event, index, node)
        elif node in clip:
            # self.Pixmap_Clip(event)
            self.Pixmap_Move(event, index, selection)
        else:
            self.Pixmap_Move(event, index, selection)
    def Pixmap_Move(self, event, index, selection):
        # Event Mouse
        event_x = event.x()
        event_y = event.y()
        # Index Move
        px = self.ref[index]["px"]
        py = self.ref[index]["py"]
        dx = self.ref[index]["dw"]
        dy = self.ref[index]["dh"]
        mx = event_x - self.delta_x
        my = event_y - self.delta_y

        # Simple Move
        self.ref[index]["px"] = mx
        self.ref[index]["py"] = my
        # Nodes
        nl = mx
        nt = my
        nr = mx + dx
        nb = my + dy
        sx = 0
        sy = 0
        # Attach to Edges
        spl = 5
        if index != None:
            if len(self.limit_x) > 0:
                for i in range(0, len(self.limit_x)):
                    ll = self.limit_x[i] - spl
                    lr = self.limit_x[i] + spl
                    if (nl >= ll and nl <= lr):
                        self.ref[index]["px"] = self.limit_x[i]
                        sx = self.ref[index]["px"] - mx
                        break
                    elif (nr >= ll and nr <= lr):
                        self.ref[index]["px"] = self.limit_x[i] - self.ref[index]["dw"]
                        sx = self.ref[index]["px"] - mx
                        break
            if len(self.limit_y) > 0:
                for i in range(0, len(self.limit_y)):
                    lt = self.limit_y[i] - spl
                    lb = self.limit_y[i] + spl
                    if (nt >= lt and nt <= lb):
                        self.ref[index]["py"] = self.limit_y[i]
                        sy = self.ref[index]["py"] - my
                        break
                    elif (nb >= lt and nb <= lb):
                        self.ref[index]["py"] = self.limit_y[i] - self.ref[index]["dh"]
                        sy = self.ref[index]["py"] - my
                        break

        # Selection Move
        sel_len = len(selection)
        if sel_len > 1:
            for i in range(0, len(self.ref)):
                if (self.ref[i]["path"] in selection and self.ref[i]["path"] != self.ref[index]["path"]):
                    self.ref[i]["px"] = event_x - self.deltas[i][0] + sx
                    self.ref[i]["py"] = event_y - self.deltas[i][1] + sy
        # Update
        self.update()
    def Pixmap_Scale(self, event, index, node):
        # Variables
        ex = event.x()
        ey = event.y()
        px = self.ref[index]["px"]
        py = self.ref[index]["py"]
        dx = self.ref[index]["dw"]
        dy = self.ref[index]["dh"]
        ang = self.ref[index]["ang"]
        spl = 5 # distance pixmap to limit to snap
        spt = 20 # distance mouse to pixmap to trigger snapping mode

        # Snapping Preparation Cycle
        if (node == 1 or node == 9):
            s19_1x = 0
            s19_1y = 0
            s19_2x = 0
            s19_2y = 0
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                for x in range(0, len(self.limit_x)):
                    ll = self.limit_x[x] - spl
                    lr = self.limit_x[x] + spl
                    if (ex >= ll and ex <= lr):
                        s19_1x, s19_1y = self.Math_2D_Points_Lines_Intersection(
                            self.limit_x[x], ey,
                            self.limit_x[x], (ey + 10),
                            px, py,
                            (px + dx), (py + dy))
                        break
                for y in range(0, len(self.limit_y)):
                    lt = self.limit_y[y] - spl
                    lb = self.limit_y[y] + spl
                    if (ey >= lt and ey <= lb):
                        s19_2x, s19_2y = self.Math_2D_Points_Lines_Intersection(
                            ex, self.limit_y[y],
                            (ex + 10), self.limit_y[y],
                            px, py,
                            (px + dx), (py + dy))
                        break
        if (node == 3 or node == 7):
            s37_1x = 0
            s37_1y = 0
            s37_2x = 0
            s37_2y = 0
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                for x in range(0, len(self.limit_x)):
                    ll = self.limit_x[x] - spl
                    lr = self.limit_x[x] + spl
                    if (ex >= ll and ex <= lr):
                        s37_1x, s37_1y = self.Math_2D_Points_Lines_Intersection(
                            self.limit_x[x], ey,
                            self.limit_x[x], (ey + 10),
                            (px + dx), py,
                            px, (py + dy))
                        break
                for y in range(0, len(self.limit_y)):
                    lt = self.limit_y[y] - spl
                    lb = self.limit_y[y] + spl
                    if (ey >= lt and ey <= lb):
                        s37_2x, s37_2y = self.Math_2D_Points_Lines_Intersection(
                            ex, self.limit_y[y],
                            (ex + 10), self.limit_y[y],
                            (px + dx), py,
                            px, (py + dy))
                        break

        # Nodes
        if node == 1:
            # Scale
            nx = px + dx
            ny = py + dy
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[index]["px"] = nx - tx
            self.ref[index]["py"] = ny - ty
            self.ref[index]["dw"] = tx
            self.ref[index]["dh"] = ty
            # Snapping
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                dist_e = self.Math_2D_Points_Distance(ex, ey, px, py)
                dist_1 = self.Math_2D_Points_Distance(ex, ey, s19_1x, ey)
                dist_2 = self.Math_2D_Points_Distance(ex, ey, ex, s19_2y)
                if (dist_e <= spt and (dist_1 <= spl or dist_2 <= spl)):
                    if dist_1 <= dist_2:
                        hip = self.Math_2D_Points_Distance(nx, ny, s19_1x, s19_1y)
                    else:
                        hip = self.Math_2D_Points_Distance(nx, ny, s19_2x, s19_2y)
                    tx = math.cos(math.radians(ang)) * hip
                    ty = math.sin(math.radians(ang)) * hip
                    self.ref[index]["px"] = nx - tx
                    self.ref[index]["py"] = ny - ty
                    self.ref[index]["dw"] = tx
                    self.ref[index]["dh"] = ty
        if node == 3:
            # Scale
            nx = px
            ny = py + dy
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[index]["px"] = nx
            self.ref[index]["py"] = ny - ty
            self.ref[index]["dw"] = tx
            self.ref[index]["dh"] = ty
            # Snapping
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                dist_e = self.Math_2D_Points_Distance(ex, ey, (px + dx), py)
                dist_1 = self.Math_2D_Points_Distance(ex, ey, s37_1x, ey)
                dist_2 = self.Math_2D_Points_Distance(ex, ey, ex, s37_2y)
                if (dist_e <= spt and (dist_1 <= spl or dist_2 <= spl)):
                    if dist_1 <= dist_2:
                        hip = self.Math_2D_Points_Distance(nx, ny, s37_1x, s37_1y)
                    else:
                        hip = self.Math_2D_Points_Distance(nx, ny, s37_2x, s37_2y)
                    tx = math.cos(math.radians(ang)) * hip
                    ty = math.sin(math.radians(ang)) * hip
                    self.ref[index]["px"] = nx
                    self.ref[index]["py"] = ny - ty
                    self.ref[index]["dw"] = tx
                    self.ref[index]["dh"] = ty
        if node == 7:
            # Scale
            nx = px + dx
            ny = py
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[index]["px"] = nx - tx
            self.ref[index]["py"] = ny
            self.ref[index]["dw"] = tx
            self.ref[index]["dh"] = ty
            # Snapping
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                dist_e = self.Math_2D_Points_Distance(ex, ey, px, (py + dy))
                dist_1 = self.Math_2D_Points_Distance(ex, ey, s37_1x, ey)
                dist_2 = self.Math_2D_Points_Distance(ex, ey, ex, s37_2y)
                if (dist_e <= spt and (dist_1 <= spl or dist_2 <= spl)):
                    if dist_1 <= dist_2:
                        hip = self.Math_2D_Points_Distance(nx, ny, s37_1x, s37_1y)
                    else:
                        hip = self.Math_2D_Points_Distance(nx, ny, s37_2x, s37_2y)
                    tx = math.cos(math.radians(ang)) * hip
                    ty = math.sin(math.radians(ang)) * hip
                    self.ref[index]["px"] = nx - tx
                    self.ref[index]["py"] = ny
                    self.ref[index]["dw"] = tx
                    self.ref[index]["dh"] = ty
        if node == 9:
            # Scale
            hip = self.Math_2D_Points_Distance(px, py, ex, ey)
            self.ref[index]["dw"] = math.cos(math.radians(ang)) * hip
            self.ref[index]["dh"] = math.sin(math.radians(ang)) * hip
            # Snapping
            if (len(self.limit_x) > 0 and len(self.limit_y) > 0):
                dist_e = self.Math_2D_Points_Distance(ex, ey, (px + dx), (py + dy))
                dist_1 = self.Math_2D_Points_Distance(ex, ey, s19_1x, ey)
                dist_2 = self.Math_2D_Points_Distance(ex, ey, ex, s19_2y)
                if (dist_e <= spt and (dist_1 <= spl or dist_2 <= spl)):
                    if dist_1 <= dist_2:
                        hip = self.Math_2D_Points_Distance(px, py, s19_1x, s19_1y)
                    else:
                        hip = self.Math_2D_Points_Distance(px, py, s19_2x, s19_2y)
                    self.ref[index]["dw"] = math.cos(math.radians(ang)) * hip
                    self.ref[index]["dh"] = math.sin(math.radians(ang)) * hip

        # Update Perimeter and Area as they are dependant
        self.ref[index]["per"] = (2 * self.ref[index]["dw"]) + (2 * self.ref[index]["dh"])
        self.ref[index]["are"] = self.ref[index]["dw"] * self.ref[index]["dh"]
        self.update()
    def Pixmap_Clip(self, event):
        pass
    def Pixmap_Area(self, lista):
        if len(lista) > 0:
            px = []
            py = []
            dx = []
            dy = []
            for i in range(0, len(lista)):
                a = lista[i]["px"]
                b = lista[i]["py"]
                c = lista[i]["dw"]
                d = lista[i]["dh"]
                px.append(a)
                py.append(b)
                dx.append(a + c)
                dy.append(b + d)
            mpx = min(px)
            mpy = min(py)
            mdx = -mpx + max(dx)
            mdy = -mpy + max(dy)
            return mpx, mpy, mdx, mdy

    def Camera_Pan(self, event):
        dx = event.x() - self.origin_x
        dy = event.y() - self.origin_y
        for i in range(0, len(self.ref)):
            self.ref[i]["px"] = self.camera_pan[i][0] + dx
            self.ref[i]["py"] = self.camera_pan[i][1] + dy
        self.update()
    def Camera_Scale(self, event):
        dist = event.y() - self.origin_y
        value = 0.01
        for i in range(0, len(self.ref)):
            self.ref[i]["px"] = self.camera_scale[i][0] + (-self.origin_x + self.camera_scale[i][0]) * (-dist * value)
            self.ref[i]["py"] = self.camera_scale[i][1] + (-self.origin_y + self.camera_scale[i][1]) * (-dist * value)
            self.ref[i]["dw"] = (self.camera_scale[i][4] + (-self.origin_x + self.camera_scale[i][4]) * (-dist * value)) - self.ref[i]["px"]
            self.ref[i]["dh"] = (self.camera_scale[i][5] + (-self.origin_y + self.camera_scale[i][5]) * (-dist * value)) - self.ref[i]["py"]
            self.ref[i]["per"] = (2 * self.ref[i]["dw"]) + (2 * self.ref[i]["dh"])
            self.ref[i]["are"] = self.ref[i]["dw"] * self.ref[i]["dh"]
        self.update()

    # Mouse Events
    def mousePressEvent(self, event):
        # Mouse
        self.origin_x = event.x()
        self.origin_y = event.y()
        self.Index_Closest(event)
        if self.index is not None:
            self.Index_Limits(event, self.index)
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier): # Select
            self.Selection_Origin(event)
            if self.index is not None:
                self.Selection_Replace(self.ref[self.index]["path"])
            else:
                self.Selection_Clear()
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier): # Select Add
            self.Selection_Origin(event)
            if self.index is not None:
                self.Selection_Add(self.ref[self.index]["path"])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier): # Pixmap Operation
            if self.index is not None:
                self.Pixmap_Operation(event, self.index, self.node, self.selection)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier)): # Pin Zoom
            # Close Pin Zoom
            if self.pin_zoom[0] == True:
                self.Pin_Zoom(False, "")
            # Open Pin Zoom
            else:
                self.Index_Closest(event)
                if self.index is not None:
                    self.Pin_Zoom(True, self.ref[self.index]["qpixmap"])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)): # Camera Pan
            self.camera_pan = []
            for i in range(0, len(self.ref)):
                self.camera_pan.append([self.ref[i]["px"], self.ref[i]["py"]])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Zoom
            self.camera_scale = []
            for i in range(0, len(self.ref)):
                self.camera_scale.append([
                    self.ref[i]["px"], self.ref[i]["py"],
                    self.ref[i]["dw"], self.ref[i]["dh"],
                    self.ref[i]["px"] + self.ref[i]["dw"], self.ref[i]["py"] + self.ref[i]["dh"],
                    ])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Reset
            pass
        # MMB
        if (event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier): # Camera Pan
            if self.camera_wheel == None:
                self.camera_wheel = "press"
                self.camera_pan = []
                for i in range(0, len(self.ref)):
                    self.camera_pan.append([self.ref[i]["px"], self.ref[i]["py"]])
    def mouseMoveEvent(self, event):
        # Mouse
        self.event_x = event.x()
        self.event_y = event.y()
        dist = self.Math_2D_Points_Distance(self.origin_x, self.origin_y, self.event_x, self.event_y)
        limit = 10
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier): # Select Square
            if dist >= limit:
                self.select_state = True
                self.Selection_Square(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier): # Select Square
            if dist >= limit:
                self.select_state = True
                self.Selection_Square(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier): # Pixmap Operation
            if self.index is not None:
                self.Pixmap_Operation(event, self.index, self.node, self.selection)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier): # Drag and Drop
            if self.index is not None:
                self.SIGNAL_DRAG.emit(self.ref[self.index]["path"])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier)):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)): # Camera Pan
            self.Camera_Pan(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Zoom
            self.Camera_Scale(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Reset
            pass
        # MMB
        if (event.buttons() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier): # Camera Pan
            if self.camera_wheel == "press":
                self.Camera_Pan(event)
    def mouseDoubleClickEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        self.index = None
        self.node = 0
        self.origin_x = 0
        self.origin_y = 0
        self.event_x = 0
        self.event_y = 0
        self.delta_x = 0
        self.delta_y = 0
        self.select_state = False
        self.select_ox = 0
        self.select_oy = 0
        self.select_ex = 0
        self.select_ey = 0
        self.limit_x = []
        self.limit_y = []
        self.camera_wheel = None
        self.Board_Save()
        self.update()

    # Wheel Events
    def wheelEvent(self, event):
        if self.camera_wheel == None:
            self.camera_wheel = "wheel"
            delta = event.angleDelta()
            if event.modifiers() == QtCore.Qt.NoModifier:
                self.camera_scale = []
                for i in range(0, len(self.ref)):
                    self.camera_scale.append([
                        self.ref[i]["px"], self.ref[i]["py"],
                        self.ref[i]["dw"], self.ref[i]["dh"],
                        self.ref[i]["px"] + self.ref[i]["dw"], self.ref[i]["py"] + self.ref[i]["dh"],
                        ])
                value = 0.1
                if delta.y() > 20:
                    self.Wheel_Scale(event, value)
                elif delta.y() < -20:
                    self.Wheel_Scale(event, -value)
                self.update()
            self.camera_wheel = None
    def Wheel_Scale(self, event, value):
        ex = event.x()
        ey = event.y()
        for i in range(0, len(self.ref)):
            self.ref[i]["px"] = self.camera_scale[i][0]  + (-ex + self.camera_scale[i][0]) * (value)
            self.ref[i]["py"] = self.camera_scale[i][1]  + (-ey + self.camera_scale[i][1]) * (value)
            self.ref[i]["dw"] = (self.camera_scale[i][4] + (-ex + self.camera_scale[i][4]) * (value)) - self.ref[i]["px"]
            self.ref[i]["dh"] = (self.camera_scale[i][5] + (-ey + self.camera_scale[i][5]) * (value)) - self.ref[i]["py"]
            self.ref[i]["per"] = (2 * self.ref[i]["dw"]) + (2 * self.ref[i]["dh"])
            self.ref[i]["are"] = self.ref[i]["dw"] * self.ref[i]["dh"]

    # Context Menu Event
    def contextMenuEvent(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Index_Closest(event)
            cmenu = QMenu(self)
            if self.pin_zoom[0] == True:
                # Actions
                cmenu_zoom_close = cmenu.addAction("Zoom Close")
                action = cmenu.exec_(self.mapToGlobal(event.pos()))
                # Triggers
                if action == cmenu_zoom_close:
                    self.Pin_Zoom(False, "")
            else:
                if self.index == None:
                    # Actions
                    cmenu_board_load = cmenu.addAction("Board KRA Load")
                    cmenu_board_save = cmenu.addAction("Board KRA Save")
                    cmenu_board_save.setCheckable(True)
                    cmenu_board_save.setChecked(self.kra_bind)
                    cmenu.addSeparator()
                    cmenu_board_clean = cmenu.addAction("Board Clean")
                    action = cmenu.exec_(self.mapToGlobal(event.pos()))
                    # Triggers
                    if action == cmenu_board_load:
                        self.SIGNAL_LOAD.emit(0)
                    if action == cmenu_board_save:
                        self.kra_bind = not self.kra_bind
                    if action == cmenu_board_clean:
                        self.Board_Clean()
                else:
                    sel_len = len(self.selection)
                    if sel_len > 1:
                        # Actions
                        cmenu_pack_line = cmenu.addAction("Pack Line")
                        cmenu_pack_column = cmenu.addAction("Pack Column")
                        # cmenu_pack_optimized = cmenu.addAction("Pack Optimized")
                        cmenu.addSeparator()
                        cmenu_selection_clean = cmenu.addAction("Selection Clean")
                        action = cmenu.exec_(self.mapToGlobal(event.pos()))
                        # Triggers
                        if action == cmenu_pack_line:
                            self.Pack_Straight("line")
                        if action == cmenu_pack_column:
                            self.Pack_Straight("column")
                        # if action == cmenu_pack_optimized:
                        #     self.Pack_Optimized()
                        if action == cmenu_selection_clean:
                            self.Selection_Clean(self.selection)
                    else:
                        # Actions
                        cmenu_zoom_open = cmenu.addAction("Zoom Open")
                        cmenu.addSeparator()
                        cmenu_edit_greyscale = cmenu.addAction("Edit Grayscale")
                        cmenu_edit_greyscale.setCheckable(True)
                        cmenu_edit_greyscale.setChecked(self.ref[self.index]["egs"])
                        cmenu_edit_invert_h = cmenu.addAction("Edit Flip Horizontal")
                        cmenu_edit_invert_h.setCheckable(True)
                        cmenu_edit_invert_h.setChecked(self.ref[self.index]["efx"])
                        cmenu_edit_invert_v = cmenu.addAction("Edit Flip Vertical")
                        cmenu_edit_invert_v.setCheckable(True)
                        cmenu_edit_invert_v.setChecked(self.ref[self.index]["efy"])
                        cmenu.addSeparator()
                        cmenu_pin_newpath = cmenu.addAction("Pin NewPath")
                        cmenu_pin_clean = cmenu.addAction("Pin Clean")
                        position = QPoint(self.ref[self.index]["px"] + 10, self.ref[self.index]["py"] + 10)
                        action = cmenu.exec_(self.mapToGlobal(position))
                        # Triggers
                        if action == cmenu_zoom_open:
                            self.Pin_Zoom(True, self.ref[self.index]["qpixmap"])
                        if action == cmenu_edit_greyscale:
                            self.Pin_Edit("egs", self.index)
                        if action == cmenu_edit_invert_h:
                            self.Pin_Edit("efx", self.index)
                        if action == cmenu_edit_invert_v:
                            self.Pin_Edit("efy", self.index)
                        if action == cmenu_pin_newpath:
                            self.Pin_NewPath(self.index)
                        if action == cmenu_pin_clean:
                            self.Pin_Clean(self.index)
        self.Board_Save()

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
                # Files and Folders
                length = len(event.mimeData().urls())
                for i in range(0, length):
                    self.Pin_Drop(os.path.normpath(event.mimeData().urls()[i].toLocalFile()))
            event.accept()
        else:
            event.ignore()
        self.Board_Save()
        self.update()

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        self.active = False
        self.Board_Save()
        self.update()

    # Painter
    def paintEvent(self, event):
        # Theme
        kritaTheme(self)
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Optimized Square
        if len(self.ref) > 0:
            mpx, mpy, mdx, mdy = self.Pixmap_Area(self.ref)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color_ib)))
            painter.drawRect(mpx, mpy, mdx, mdy)
            self.opt_square = [mpx, mpy, mdx, mdy]

        # Images
        painter.setBrush(QtCore.Qt.NoBrush)
        for i in range(0, len(self.ref)):
            # Parse References
            path = self.ref[i]["path"]
            px = self.ref[i]["px"]
            py = self.ref[i]["py"]
            sx = self.ref[i]["dw"]
            sy = self.ref[i]["dh"]
            # Draw Images
            if self.ref[i]["qpixmap"] != None:
                qpixmap = self.ref[i]["qpixmap"]
            else:
                qpixmap = QPixmap(path)
                if qpixmap.isNull() == False:
                    self.ref[i]["qpixmap"] = qpixmap
            if qpixmap.isNull() == False:
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawPixmap(px, py, qpixmap.scaled(sx, sy, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
                painter.drawLine(px,    py,    px+sx, py)
                painter.drawLine(px+sx, py,    px+sx, py+sy)
                painter.drawLine(px+sx, py+sy, px,    py+sy)
                painter.drawLine(px,    py+sy, px,    py)
                painter.drawLine(px,    py,    px+sx, py+sy)
                painter.drawLine(px,    py+sy, px+sx, py)

        # Selection Multi-Pin
        sel_len = len(self.selection)
        # Dots over images
        if sel_len == 1:
            painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
            painter.setBrush(QtCore.Qt.NoBrush)
        if sel_len > 1:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(self.color1, Qt.Dense7Pattern))
        for i in range(0, len(self.ref)):
            if self.ref[i]["path"] in self.selection:
                painter.drawRect(self.ref[i]["px"], self.ref[i]["py"], self.ref[i]["dw"], self.ref[i]["dh"])
        # Square around the selection
        if sel_len >= 2:
            painter.setPen(QPen(self.color1, 2, Qt.SolidLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            spx, spy, sdx, sdy = self.Selection_Area(self.selection)
            painter.drawRect(spx, spy, sdx, sdy)

        # Active
        if (self.active == True and self.index is not None and len(self.ref) > 0):
            # Squares
            minimal_triangle = 20
            if (self.ref[self.index]["dw"] > minimal_triangle and self.ref[self.index]["dh"] > minimal_triangle):
                # Variables
                painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                px = self.ref[self.index]["px"]
                py = self.ref[self.index]["py"]
                sx = self.ref[self.index]["dw"]
                sy = self.ref[self.index]["dh"]
                # Lines
                painter.setPen(QPen(self.color1, 1, Qt.SolidLine))
                n1_x = px
                n1_y = py
                n3_x = px+sx
                n3_y = py
                n7_x = px
                n7_y = py+sy
                n9_x = px+sx
                n9_y = py+sy
                painter.drawLine(n1_x, n1_y, n3_x, n3_y)
                painter.drawLine(n3_x, n3_y, n9_x, n9_y)
                painter.drawLine(n9_x, n9_y, n7_x, n7_y)
                painter.drawLine(n7_x, n7_y, n1_x, n1_y)

                # Triangles
                painter.setPen(QPen(self.color2, 1, Qt.SolidLine))
                tri = 10
                # Scale 1
                if self.node == 1:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt1 = QPolygon([QPoint(n1_x, n1_y), QPoint(n1_x + tri, n1_y), QPoint(n1_x, n1_y + tri),])
                painter.drawPolygon(polyt1)
                # scale 3
                if self.node == 3:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt3 = QPolygon([QPoint(n3_x, n3_y), QPoint(n3_x, n3_y + tri), QPoint(n3_x - tri, n3_y),])
                painter.drawPolygon(polyt3)
                # Scale 7
                if self.node == 7:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt7 = QPolygon([QPoint(n7_x, n7_y), QPoint(n7_x, n7_y - tri), QPoint(n7_x + tri, n7_y),])
                painter.drawPolygon(polyt7)
                # Scale 9
                if self.node == 9:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polyt9 = QPolygon([QPoint(n9_x, n9_y), QPoint(n9_x - tri, n9_y), QPoint(n9_x, n9_y - tri),])
                painter.drawPolygon(polyt9)

            # Squares
            minimal_square = 50
            if (self.ref[self.index]["dw"] > minimal_square and self.ref[self.index]["dh"] > minimal_square):
                # Variables
                n2_x =  px + (sx * 0.5)
                n2_y =  py
                n4_x =  px
                n4_y =  py + (sy * 0.5)
                n6_x =  px + sx
                n6_y =  py + (sy * 0.5)
                n8_x =  px + (sx * 0.5)
                n8_y =  py + sy
                # Polygons
                painter.setPen(QPen(self.color2, 1, Qt.SolidLine))
                sq = 5
                # Clip 2
                if self.node == 2:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(n2_x-sq, n2_y), QPoint(n2_x-sq, n2_y+sq), QPoint(n2_x+sq, n2_y+sq), QPoint(n2_x+sq, n2_y),])
                painter.drawPolygon(polys2)
                # Clip 4
                if self.node == 4:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(n4_x, n4_y-sq), QPoint(n4_x+sq, n4_y-sq), QPoint(n4_x+sq, n4_y+sq), QPoint(n4_x, n4_y+sq),])
                painter.drawPolygon(polys2)
                # Clip 6
                if self.node == 6:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(n6_x, n6_y-sq), QPoint(n6_x-sq, n6_y-sq), QPoint(n6_x-sq, n6_y+sq), QPoint(n6_x, n6_y+sq),])
                painter.drawPolygon(polys2)
                # Clip 8
                if self.node == 8:
                    painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
                else:
                    painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
                polys2 = QPolygon([QPoint(n8_x-sq, n8_y), QPoint(n8_x-sq, n8_y-sq), QPoint(n8_x+sq, n8_y-sq), QPoint(n8_x+sq, n8_y),])
                painter.drawPolygon(polys2)

        # Image Zoom
        if self.pin_zoom[0] == True:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.NoPen)
            qpixmap = QPixmap(self.pin_zoom[1])
            if qpixmap.isNull() == False:
                ww = self.widget_width
                wh = self.widget_height
                qpixmap_scaled = qpixmap.scaled(ww, wh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pw = qpixmap_scaled.width()
                ph = qpixmap_scaled.height()
                painter.drawPixmap((ww/2)-(pw/2), (wh/2)-(ph/2), qpixmap_scaled)

        # Selection Square
        if (self.select_state == True and self.select_ox != 0 and self.select_oy != 0):
            painter.setPen(QPen(self.color1, 2, Qt.SolidLine))
            painter.setBrush(QBrush(self.color1, Qt.Dense7Pattern))
            painter.drawRect(self.select_ox, self.select_oy, self.select_ex, self.select_ey)

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

    # Math
    def Math_2D_Points_Distance(self, x1, y1, x2, y2):
        dd = math.sqrt( math.pow((x1-x2),2) + math.pow((y1-y2),2) )
        return dd
    def Math_2D_Points_Lines_Angle(self, x1, y1, x2, y2, x3, y3):
        v1 = (x1-x2, y1-y2)
        v2 = (x3-x2, y3-y2)
        v1_theta = math.atan2(v1[1], v1[0])
        v2_theta = math.atan2(v2[1], v2[0])
        angle = (v2_theta - v1_theta) * (180.0 / math.pi)
        if angle < 0:
            angle += 360.0
        return angle
    def Math_2D_Points_Lines_Intersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        try:
            xx = ((x2*y1-x1*y2)*(x4-x3)-(x4*y3-x3*y4)*(x2-x1)) / ((x2-x1)*(y4-y3)-(x4-x3)*(y2-y1))
            yy = ((x2*y1-x1*y2)*(y4-y3)-(x4*y3-x3*y4)*(y2-y1)) / ((x2-x1)*(y4-y3)-(x4-x3)*(y2-y1))
        except:
            xx = 0
            yy = 0
        return xx, yy


class Dialog_UI(QDialog):

    def __init__(self, parent):
        super(Dialog_UI, self).__init__(parent)
        # Load UI for Dialog
        self.dir_name = str(os.path.dirname(os.path.realpath(__file__)))
        uic.loadUi(self.dir_name + "/imagine_board_settings.ui", self)
class Dialog_CR(QDialog):

    def __init__(self, parent):
        super(Dialog_CR, self).__init__(parent)
        # Load UI for Dialog
        self.dir_name = str(os.path.dirname(os.path.realpath(__file__)))
        uic.loadUi(self.dir_name + "/imagine_board_copyright.ui", self)


"""
To Do:
- Gif starts playing when resizing. break play button.
- https://developers.pinterest.com/docs/api/v5/#tag/Introduction
- Optimized Packing
- GIF animation frame forward and back with pause
- renames
"""
