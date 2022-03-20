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
        self.color1 = QColor('#2a2a2a')
        self.color2 = QColor('#d4d4d4')
    else:
        self.color1 = QColor('#d4d4d4')
        self.color2 = QColor('#2a2a2a')
    self.color_hover = QColor(0,0,0,150)
    self.color_free = QColor(0,0,0,50)
    self.color_blue = QColor('#3daee9')
    self.color_inactive = QColor(40,4,4,150)


class ImagineBoard_Preview(QWidget):
    # General
    SIGNAL_CLICK = QtCore.pyqtSignal(int)
    SIGNAL_WHEEL = QtCore.pyqtSignal(int)
    SIGNAL_STYLUS = QtCore.pyqtSignal(int)
    SIGNAL_DRAG = QtCore.pyqtSignal(str)
    # Preview
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    SIGNAL_FUNCTION = QtCore.pyqtSignal(list)
    SIGNAL_FAVORITE = QtCore.pyqtSignal(str)
    SIGNAL_RANDOM = QtCore.pyqtSignal(int)
    SIGNAL_LOCATION = QtCore.pyqtSignal(str)
    SIGNAL_CLIP = QtCore.pyqtSignal(list)
    SIGNAL_FIT = QtCore.pyqtSignal(bool)
    SIGNAL_DOCUMENT = QtCore.pyqtSignal(str)
    SIGNAL_REFERENCE = QtCore.pyqtSignal(str)
    SIGNAL_LAYER = QtCore.pyqtSignal(str)

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
    def Set_QPixmap_Preview(self, path):
        self.label.clear()
        self.movie = False
        self.path = path
        self.qpixmap = QPixmap(path)
        self.qmovie.stop()
        self.update()
    def Set_QMovie_Preview(self, path):
        self.path = path
        self.qpixmap = QPixmap(path)
        self.qmovie = QMovie(path)
        if self.qmovie.isValid() == True:
            # # Buffer Movie
            # self.bytesio = io.BytesIO()
            # img.save(fp=self.bytesio, format='GIF', append_images=imgs, save_all=True, duration=GIF_DELAY, loop=0)
            # qbytearray = QByteArray(self.bytesio.getvalue())
            # self.bytesio.close()
            # qbuffer = QBuffer(qbytearray)
            #
            #
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

    # Mouse Events
    def mousePressEvent(self, event):
        # Requires Active
        self.origin_x = event.x()
        self.origin_y = event.y()
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
            self.Mouse_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
        # RMB
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.Preview_Position(event)
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Preview_Zoom(event)
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.AltModifier):
            self.Preview_Reset()
            self.Clip_Off()
        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseMoveEvent(self, event):
        # LMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.press = True
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Stylus_Pagination(event)
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.AltModifier):
            self.SIGNAL_DRAG.emit(self.path)
        # RMB
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            self.Preview_Position(event)
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ControlModifier):
            self.Preview_Zoom(event)
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.AltModifier):
            self.Preview_Reset()
            self.Clip_Off()
        # States
        if self.clip_state == True:
            self.Clip_Event(event)
    def mouseDoubleClickEvent(self, event):
        # LMB and RMB
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_MODE.emit(1)
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
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
            cmenu_mode_grid = cmenu.addAction("Mode Grid")
            # cmenu_mode_reference = cmenu.addAction("Mode Reference")
            cmenu.addSeparator()
            cmenu_function = cmenu.addAction("Function >>")
            # cmenu_favorite = cmenu.addAction("Favorite")
            cmenu_random = cmenu.addAction("Random")
            cmenu_location = cmenu.addAction("Location")
            cmenu_copy = cmenu.addMenu("Copy")
            cmenu_file = cmenu_copy.addAction("File Name")
            cmenu_directory = cmenu_copy.addAction("Path Directory")
            cmenu_path = cmenu_copy.addAction("Path Full")
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
            if action == cmenu_mode_grid:
                self.SIGNAL_MODE.emit(1)
            # if action == cmenu_mode_reference:
            #     self.SIGNAL_MODE.emit(2)
            if action == cmenu_function:
                string = [os.path.normpath( self.path.lower() )]
                self.SIGNAL_FUNCTION.emit(string)
            # if action == cmenu_favorite:
            #     self.SIGNAL_FAVORITE.emit(self.path)
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
            if action == cmenu_clip:
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
                self.SIGNAL_DOCUMENT.emit(self.path)
            if action == cmenu_insert_ref:
                self.SIGNAL_REFERENCE.emit(self.path)
            if action == cmenu_insert_layer:
                self.SIGNAL_LAYER.emit(self.path)

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

            self.Movie_Log()
    def Movie_Play(self):
        if self.movie == True:
            self.qmovie.setPaused(False)

            self.Movie_Log()
    def Movie_Frame_Back(self):
        if self.movie == True:
            self.qmovie_frame -= 1
            self.qmovie.jumpToFrame(self.qmovie_frame)
            self.qmovie.setPaused(True)

            self.Movie_Log()
    def Movie_Frame_Forward(self):
        if self.movie == True:
            # self.qmovie_frame += 1
            # self.qmovie.stop()
            # self.qmovie.jumpToFrame(self.qmovie_frame)
            # self.qmovie.start()
            # self.qmovie.setPaused(True)

            self.qmovie.jumpToNextFrame()

            self.Movie_Log()
    def Movie_Screenshot(self, directory_path):
        if self.movie == True:
            # screenshot_pixmap = self.qmovie.currentPixmap()
            # basename = os.path.basename(self.path)
            # save_path = os.path.normpath(self.directory + "/" + basename)
            # QtCore.qDebug(str(save_path))
            # screenshot_pixmap.save()

            # self.Movie_Log()

            pass
    def Movie_Log(self):
        QtCore.qDebug("frame index = " + str(self.qmovie_frame))
        QtCore.qDebug("frame count = " + str(self.qmovie.frameCount()))
        QtCore.qDebug("speed = " + str(self.qmovie.speed()))
        QtCore.qDebug("state = " + str(self.qmovie.state()))
        QtCore.qDebug("-----------------------------------")

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


class ImagineBoard_Grid(QWidget):
    # General
    SIGNAL_CLICK = QtCore.pyqtSignal(int)
    SIGNAL_WHEEL = QtCore.pyqtSignal(int)
    SIGNAL_STYLUS = QtCore.pyqtSignal(int)
    # Grid
    SIGNAL_MODE = QtCore.pyqtSignal(int)
    SIGNAL_FUNCTION_GRID = QtCore.pyqtSignal(list) # Location
    SIGNAL_FUNCTION_DROP = QtCore.pyqtSignal(list) # Path
    SIGNAL_NAME = QtCore.pyqtSignal(list)
    SIGNAL_PREVIEW = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        super(ImagineBoard_Grid, self).__init__(parent)
        self.origin_x = 0
        self.origin_y = 0
        self.default = QPixmap()
        self.grid_horz = 3
        self.grid_vert = 3
        self.tn_x = 200
        self.tn_y = 200
        self.pixmap_list = []
        self.display_bool = False
        self.Set_Display(self.display_bool)
        self.press = False
        # Drag and Drop
        self.setAcceptDrops(True)
        self.drop = False
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_QPixmaps(self, pixmap_list):
        self.pixmap_list = pixmap_list
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
            hover_square = [
                int((event.x() * self.grid_horz) / self.widget_width),
                int((event.y() * self.grid_vert) / self.widget_height),
                ]
        except:
            hover_square = [0,0]
        return hover_square

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
        # RMB
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ControlModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.AltModifier):
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
            pass
        # RMB
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ShiftModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.ControlModifier):
            pass
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.AltModifier):
            pass
    def mouseDoubleClickEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            self.SIGNAL_PREVIEW.emit(self.Hover_Square(event))
        if (event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.NoModifier):
            pass
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
            cmenu_mode_preview = cmenu.addAction("Mode Preview")
            # cmenu_mode_reference = cmenu.addAction("Mode Reference")
            cmenu.addSeparator()
            cmenu_function = cmenu.addAction("Function >>")
            cmenu_ratio = cmenu.addAction("Fit Ratio")
            cmenu_ratio.setCheckable(True)
            cmenu_ratio.setChecked(self.display_bool)
            action = cmenu.exec_(self.mapToGlobal(event.pos()))
            # Triggers
            if action == cmenu_mode_preview:
                self.SIGNAL_PREVIEW.emit(self.Hover_Square(event))
            # if action == cmenu_mode_reference:
            #     self.SIGNAL_MODE.emit(2)
            if action == cmenu_function:
                self.SIGNAL_FUNCTION_GRID.emit(self.Hover_Square(event))
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
        for i in range(0, len(self.pixmap_list)):
            if self.pixmap_list[i][2] != "":
                # Clip Mask
                px = self.pixmap_list[i][0] * self.tn_x
                py = self.pixmap_list[i][1] * self.tn_y
                thumbnail = QRectF(px,py, self.tn_x,self.tn_y)
                painter.setClipRect(thumbnail, Qt.ReplaceClip)

                # Render Pixmap
                pixmap = self.pixmap_list[i][3]
                render = pixmap.scaled(self.tn_x+1, self.tn_y+1, self.display_ratio, Qt.FastTransformation)
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

    def __init__(self, parent):
        super(ImagineBoard_Reference, self).__init__(parent)
        self.path = ""
        self.qpixmap = QPixmap()
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    def Set_QPixmap_1(self, path):
        self.path = path
        self.qpixmap = QPixmap(path)
        self.update()
    def Set_Size(self, widget_width, widget_height):
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.wt2 = widget_width * 0.5
        self.ht2 = widget_height * 0.5

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

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_free)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        # Example
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPixmap(0,0,self.qpixmap)


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
- Send files into the Board
- Connect board to file (Link Hard Copy)
- Gif starts playing when resizing. break play button.
"""
