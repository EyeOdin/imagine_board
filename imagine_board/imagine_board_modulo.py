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
        self.color1 = QColor('#191919')
        self.color2 = QColor('#e5e5e5')
    else:
        self.color1 = QColor('#e5e5e5')
        self.color2 = QColor('#191919')
    self.color_hover = QColor(0,0,0,150)
    self.color_free = QColor(0,0,0,50)
    self.color_blue = QColor('#3daee9')
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
            # img.save(fp=self.bytesio, format='GIF', append_images=imgs, save_all=True, duration=GIF_DELAY, loop=0)
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
    def Set_Clip_Off(self):
        self.Clip_Off()
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
        self.focus_x = event.x() / self.widget_width
        self.focus_y = event.y() / self.widget_height
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
            # Finish
            list = [
                self.clip_state,
                self.clip_p1_per[0] * self.image_width,
                self.clip_p1_per[1] * self.image_height,
                self.width_per * self.image_width,
                self.height_per * self.image_height
                ]
            self.SIGNAL_CLIP.emit(list)
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
            cmenu_pick_color = cmenu.addAction("Pick Color")
            cmenu_pick_color.setCheckable(True)
            cmenu_pick_color.setChecked(self.pick_color)
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
                string = [os.path.normpath( self.path.lower() )]
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
                    item = os.path.normpath( event.mimeData().urls()[i].toLocalFile().lower() )
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
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    SIGNAL_FUNCTION_GRID = QtCore.pyqtSignal(list) # Location
    SIGNAL_FUNCTION_DROP = QtCore.pyqtSignal(list) # Path
    SIGNAL_PIN = QtCore.pyqtSignal(list)
    SIGNAL_NAME = QtCore.pyqtSignal(list)
    SIGNAL_PREVIEW = QtCore.pyqtSignal(list)

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
                    item = os.path.normpath( event.mimeData().urls()[i].toLocalFile().lower() )
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
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    # Reference
    SIGNAL_UPDATE = QtCore.pyqtSignal(list)
    SIGNAL_LOAD = QtCore.pyqtSignal(int)

    # Init
    def __init__(self, parent):
        super(ImagineBoard_Reference, self).__init__(parent)
        # Widget
        self.widget_width = 1
        self.widget_height = 1

        # References
        self.maximum = 100000
        self.ref = []
        self.index = None
        self.select = False
        self.delta_x = 0
        self.delta_y = 0
        self.node = 0

        # Camera
        self.camera_tx = 0
        self.camera_ty = 0
        self.camera_sx = 1
        self.camera_sy = 1
        self.opt_square = [0,0,0,0]

        # Board
        self.kra_bind = False

        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Size(self, widget_width, widget_height):
        # Objects
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.update()
    def Set_Select(self, bool):
        self.select = bool

    def Pin_Add(self, pin):
        self.ref.append(pin)
        self.update()
    def Pin_Drop(self, path):
        location_x = 10
        location_y = 10
        path = str(path)
        size = 100
        qpixmap = QPixmap(path).scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
        width = qpixmap.width()
        height = qpixmap.height()
        angle = self.Math_2D_Points_Lines_Angle(width,0, 0,0, width, height)
        pin = [path, location_x, location_y, width, height, angle]
        self.Pin_Add(pin)
    def Pin_Clear(self, index):
        if index is not None:
            self.ref.pop(index)
            self.update()
    def Pin_Replace(self, index, path):
        if len(self.ref) > 0:
            self.ref[index][0] = path
            self.update()
    def Pin_NewPath(self):
        path = QFileDialog(QWidget(self))
        path.setFileMode(QFileDialog.ExistingFile)
        file_path = path.getOpenFileName(self, "Select File")[0]
        QtCore.qDebug(str(file_path))
        file_path = os.path.normpath( file_path )
        if (file_path != "" and file_path != "."):
            self.Pin_Clear(self.index)
            self.Pin_Drop(file_path)

    def Board_Load(self, references):
        self.ref = references
        self.update()
    def Board_Save(self):
        self.SIGNAL_UPDATE.emit([self.kra_bind, self.ref])
    def Board_Clear(self):
        self.ref.clear()
        self.update()

    # Operations
    def Index_Closest(self, event):
        # Detect Image Index
        index = None
        dist = self.maximum
        for i in range(0, len(self.ref)):
            mx = event.x()
            my = event.y()
            px = self.ref[i][1]
            py = self.ref[i][2]
            sx = self.ref[i][3]
            sy = self.ref[i][4]
            if (mx >= px and mx <= (px+sx) and my >= py and my <= (py+sy)): # Clicked inside the image
                point_x = px + (sx * 0.5)
                point_y = py + (sy * 0.5)
                dist_i = self.Math_2D_Points_Distance(point_x, point_y, self.origin_x, self.origin_y)
                if dist_i < dist:
                    index = i
                    dist = dist_i
                    self.delta_x = self.origin_x - point_x
                    self.delta_y = self.origin_y - point_y
        # Change index to last
        if index != None:
            pin = self.ref[index]
            self.ref.pop(index)
            self.ref.append(pin)
            self.index = len(self.ref)-1
        else:
            self.index = index
    def Index_Points(self, index):
        # Node Points
        n1_x = self.ref[index][1]
        n1_y = self.ref[index][2]
        n2_x = self.ref[index][1] + (self.ref[index][3] * 0.5)
        n2_y = self.ref[index][2]
        n3_x = self.ref[index][1] + self.ref[index][3]
        n3_y = self.ref[index][2]
        n4_x = self.ref[index][1]
        n4_y = self.ref[index][2] + (self.ref[index][4] * 0.5)
        n5_x = self.ref[index][1] + (self.ref[index][3] * 0.5)
        n5_y = self.ref[index][2] + (self.ref[index][4] * 0.5)
        n6_x = self.ref[index][1] + self.ref[index][3]
        n6_y = self.ref[index][2] + (self.ref[index][4] * 0.5)
        n7_x = self.ref[index][1]
        n7_y = self.ref[index][2] + self.ref[index][4]
        n8_x = self.ref[index][1] + (self.ref[index][3] * 0.5)
        n8_y = self.ref[index][2] + self.ref[index][4]
        n9_x = self.ref[index][1] + self.ref[index][3]
        n9_y = self.ref[index][2] + self.ref[index][4]
        node = [ [n1_x, n1_y], [n2_x, n2_y], [n3_x, n3_y], [n4_x, n4_y], [n5_x, n5_y], [n6_x, n6_y], [n7_x, n7_y], [n8_x, n8_y], [n9_x, n9_y] ]
        # Cross Points
        margin = 10
        c1_x = n1_x - margin
        c1_y = n1_y - margin
        c2_x = n2_x
        c2_y = n2_y - margin
        c3_x = n3_x + margin
        c3_y = n3_y + margin
        c4_x = n4_x - margin
        c4_y = n4_y
        c5_x = n5_x
        c5_y = n5_y
        c6_x = n6_x + margin
        c6_y = n6_y
        c7_x = n7_x - margin
        c7_y = n7_y + margin
        c8_x = n8_x
        c8_y = n8_y + margin
        c9_x = n9_x + margin
        c9_y = n9_y + margin
        cross = [ [c1_x, c1_y], [c2_x, c2_y], [c3_x, c3_y], [c4_x, c4_y], [c5_x, c5_y], [c6_x, c6_y], [c7_x, c7_y], [c8_x, c8_y], [c9_x, c9_y] ]
        # Return
        return node, cross
    def Index_Node(self, event):
        # Node Choice
        node, cross = self.Index_Points(self.index)
        dist = self.maximum
        check = []
        for i in range(0, len(node)):
            point_x = node[i][0]
            point_y = node[i][1]
            dist = self.Math_2D_Points_Distance(point_x, point_y, self.origin_x, self.origin_y)
            check.append(dist)
        value = min(check)
        if value <= 20:
            self.node = check.index(value) + 1
        else:
            self.node = 0

    def Pixmap_Operation(self, event, node):
        scale = [1,3,7,9]
        if node in scale:
            self.Pixmap_Scale(event, node)
        else:
            self.Pixmap_Move(event)
        self.update()
    def Pixmap_Move(self, event):
        px = self.ref[self.index][1]
        py = self.ref[self.index][2]
        sx = self.ref[self.index][3]
        sy = self.ref[self.index][4]
        self.ref[self.index][1] = event.x() - (sx * 0.5) - self.delta_x
        self.ref[self.index][2] = event.y() - (sy * 0.5) - self.delta_y

        # Check nearby Images
        for i in range(0, len(self.ref)):
            if i != self.index:
                pass
    def Pixmap_Scale(self, event, node):
        ex = event.x()
        ey = event.y()
        px = self.ref[self.index][1]
        py = self.ref[self.index][2]
        sx = self.ref[self.index][3]
        sy = self.ref[self.index][4]
        ang = self.ref[self.index][5]
        if node == 1:
            nx = px + sx # N9
            ny = py + sy # N9
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[self.index][1] = nx - tx
            self.ref[self.index][2] = ny - ty
            self.ref[self.index][3] = tx
            self.ref[self.index][4] = ty
        if node == 3:
            nx = px # N7
            ny = py + sy # N7
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[self.index][1] = nx
            self.ref[self.index][2] = ny - ty
            self.ref[self.index][3] = tx
            self.ref[self.index][4] = ty
        if node == 7:
            nx = px + sx # N3
            ny = py # N3
            hip = self.Math_2D_Points_Distance(nx, ny, ex, ey)
            tx = math.cos(math.radians(ang)) * hip
            ty = math.sin(math.radians(ang)) * hip
            self.ref[self.index][1] = nx - tx
            self.ref[self.index][2] = ny
            self.ref[self.index][3] = tx
            self.ref[self.index][4] = ty
        if node == 9:
            hip = self.Math_2D_Points_Distance(px, py, ex, ey)
            self.ref[self.index][3] = math.cos(math.radians(ang)) * hip
            self.ref[self.index][4] = math.sin(math.radians(ang)) * hip

    def Camera_Pan(self, event):
        dx = event.x() - self.origin_x
        dy = event.y() - self.origin_y
        for i in range(0, len(self.ref)):
            self.ref[i][1] = self.camera_pan[i][0] + dx
            self.ref[i][2] = self.camera_pan[i][1] + dy
        self.update()
    def Camera_Scale(self, event):
        dist = event.y() - self.origin_y
        for i in range(0, len(self.ref)):
            self.ref[i][1] = self.camera_scale[i][0] + (-self.origin_x + self.camera_scale[i][0]) * (-dist * 0.01)
            self.ref[i][2] = self.camera_scale[i][1] + (-self.origin_y + self.camera_scale[i][1]) * (-dist * 0.01)
            self.ref[i][3] = (self.camera_scale[i][4] + (-self.origin_x + self.camera_scale[i][4]) * (-dist * 0.01)) - self.ref[i][1]
            self.ref[i][4] = (self.camera_scale[i][5] + (-self.origin_y + self.camera_scale[i][5]) * (-dist * 0.01)) - self.ref[i][2]
        self.update()

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.Index_Closest(event)
            if self.index is not None:
                self.select = True
                self.Index_Node(event)
                self.Pixmap_Operation(event, self.node)
            else:
                self.select = False
                self.node = 0
                self.delta_x = 0
                self.delta_y = 0
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)): # Camera Pan
            self.camera_pan = []
            for i in range(0, len(self.ref)):
                self.camera_pan.append([self.ref[i][1], self.ref[i][2]])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Zoom
            self.camera_scale = []
            for i in range(0, len(self.ref)):
                self.camera_scale.append([
                self.ref[i][1], self.ref[i][2],
                self.ref[i][3], self.ref[i][4],
                self.ref[i][1] + self.ref[i][3], self.ref[i][2] + self.ref[i][4],
                ])
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Reset
            pass
    def mouseMoveEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            if self.index is not None:
                self.Pixmap_Operation(event, self.node)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)): # Camera Pan
            self.Camera_Pan(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Zoom
            self.Camera_Scale(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier)): # Camera Reset
            pass
    def mouseDoubleClickEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
    def mouseReleaseEvent(self, event):
        self.node = 0
        self.origin_x = 0
        self.origin_y = 0
        self.delta_x = 0
        self.delta_y = 0
        self.Board_Save()
        self.update()

    # Wheel Events
    def wheelEvent(self, event):
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Wheel_Index(event, delta)
            self.update()
    def Wheel_Index(self, event, delta):
        value = 0.1
        if delta.y() > 20:
            self.camera_sx += value
            self.camera_sy += value
        elif delta.y() < -20:
            self.camera_sx -= value
            self.camera_sy -= value
        if (self.camera_sx <= 0 or self.camera_sy <= 0):
            self.camera_sx = value
            self.camera_sy = value

    # Context Menu Event
    def contextMenuEvent(self, event):
        if event.modifiers() == QtCore.Qt.NoModifier:
            self.Index_Closest(event)
            cmenu = QMenu(self)
            if self.index == None:
                # Actions
                cmenu_board_clear = cmenu.addAction("Board Clear")
                cmenu_board_load = cmenu.addAction("Board KRA Load")
                cmenu_board_save = cmenu.addAction("Board KRA Save")
                cmenu_board_save.setCheckable(True)
                cmenu_board_save.setChecked(self.kra_bind)
                action = cmenu.exec_(self.mapToGlobal(event.pos()))
                # Triggers
                if action == cmenu_board_clear:
                    self.Board_Clear()
                if action == cmenu_board_load:
                    self.SIGNAL_LOAD.emit(0)
                if action == cmenu_board_save:
                    self.kra_bind = not self.kra_bind
            else:
                # Actions
                cmenu_pin_newpath = cmenu.addAction("Pin NewPath")
                cmenu_pin_clear = cmenu.addAction("Pin Clear")
                position = QPoint(self.ref[self.index][1] + 10, self.ref[self.index][2] + 10)
                action = cmenu.exec_(self.mapToGlobal(position))
                # Triggers
                if action == cmenu_pin_newpath:
                    self.Pin_NewPath()
                if action == cmenu_pin_clear:
                    self.Pin_Clear(self.index)
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
            # Files and Folders
            length = len(event.mimeData().urls())
            for i in range(0, length):
                self.Pin_Drop(os.path.normpath(event.mimeData().urls()[i].toLocalFile()))
            self.Board_Save()
            event.accept()
        else:
            event.ignore()
        self.update()

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        self.select = False
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
            tx = []
            ty = []
            bx = []
            by = []
            for i in range(0, len(self.ref)):
                tx.append(self.ref[i][1])
                ty.append(self.ref[i][2])
                bx.append(self.ref[i][1] + self.ref[i][3])
                by.append(self.ref[i][2] + self.ref[i][4])
            mtx = min(tx)
            mty = min(ty)
            mbx = -mtx + max(bx)
            mby = -mty + max(by)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color_ib)))
            painter.drawRect(mtx, mty, mbx, mby)
            self.opt_square = [mtx, mty, mbx, mby]

        # Images
        painter.setBrush(QtCore.Qt.NoBrush)
        for i in range(0, len(self.ref)):
            # Parse References
            path = self.ref[i][0]
            px = self.ref[i][1]
            py = self.ref[i][2]
            sx = self.ref[i][3]
            sy = self.ref[i][4]
            # QPixmap
            qpixmap = QPixmap(path)
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

        # Selection
        if (self.select == True and self.index is not None and len(self.ref) > 0):
            # Variables
            painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
            px = self.ref[self.index][1]
            py = self.ref[self.index][2]
            sx = self.ref[self.index][3]
            sy = self.ref[self.index][4]
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
            poly1 = QPolygon([QPoint(n1_x, n1_y), QPoint(n1_x + tri, n1_y), QPoint(n1_x, n1_y + tri),])
            painter.drawPolygon(poly1)
            # scale 3
            if self.node == 3:
                painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
            poly3 = QPolygon([QPoint(n3_x, n3_y), QPoint(n3_x, n3_y + tri), QPoint(n3_x - tri, n3_y),])
            painter.drawPolygon(poly3)
            # Scale 7
            if self.node == 7:
                painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
            poly7 = QPolygon([QPoint(n7_x, n7_y), QPoint(n7_x, n7_y - tri), QPoint(n7_x + tri, n7_y),])
            painter.drawPolygon(poly7)
            # Scale 9
            if self.node == 9:
                painter.setBrush(QBrush(self.color_blue, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.color1, Qt.SolidPattern))
            poly9 = QPolygon([QPoint(n9_x, n9_y), QPoint(n9_x - tri, n9_y), QPoint(n9_x, n9_y - tri),])
            painter.drawPolygon(poly9)

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


class Dialog_UI(QDialog):

    def __init__(self, parent):
        super(Dialog_UI, self).__init__(parent)
        # Load UI for Dialog
        self.dir_name = str(os.path.dirname(os.path.realpath(__file__)))
        uic.loadUi(self.dir_name + '/imagine_board_settings.ui', self)
class Dialog_CR(QDialog):

    def __init__(self, parent):
        super(Dialog_CR, self).__init__(parent)
        # Load UI for Dialog
        self.dir_name = str(os.path.dirname(os.path.realpath(__file__)))
        uic.loadUi(self.dir_name + '/imagine_board_copyright.ui', self)


"""
To Do:
- Gif starts playing when resizing. break play button.
- https://developers.pinterest.com/docs/api/v5/#tag/Introduction
"""
