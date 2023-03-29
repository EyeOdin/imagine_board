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
import sqlite3
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Imagine Board
from .imagine_board_calculations import *

#endregion
#region Global Variables ###########################################################
decimas = 10

#endregion


class ImagineBoard_Database(QWidget):


    # Init
    def __init__(self, parent):
        super(ImagineBoard_Database, self).__init__(parent)
        self.Variables()
    def Variables(self):
        # Widget
        self.widget_width = 1
        self.widget_height = 1
        self.w2 = 0.5
        self.h2 = 0.5
        self.side = min(self.widget_width, self.widget_height)
        self.layout = None

        # Colors
        self.color_1 = QColor("#ffffff")
        self.color_2 = QColor("#000000")
        self.color_shade = QColor(0,0,0,30)
        self.color_alpha = QColor(0,0,0,50)
        self.color_blue = QColor("#3daee9")

        # Events
        self.origin_x = 0
        self.origin_y = 0

        # Pins
        self.packing = False

        # Color Picker
        self.pigmento = False
        self.pick_color = False
        self.red = 0
        self.green = 0
        self.blue = 0
        self.range = 255

        # Database
        self.database_path = None
        self.connection = None
        self.cursor = None
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    # Relay
    def Set_Pigmento(self, bool):
        self.pigmento = bool
    def Set_Size_Corner(self, widget_width, widget_height):
        if self.packing == False:
            # Variables
            self.widget_width = widget_width
            self.widget_height = widget_height
            self.w2 = widget_width * 0.5
            self.h2 = widget_height * 0.5
            self.update()
    def Set_Size_Middle(self, widget_width, widget_height):
        if self.packing == False:
            # Reformat View
            if (self.widget_width != widget_width or self.widget_height != widget_height):
                delta_x = (widget_width - self.widget_width) * 0.5
                delta_y = (widget_height - self.widget_height) * 0.5
                # for i in range(0, len(self.pin_ref)):
                #     Pixmap_Mover(self, self.pin_ref, i, self.pin_ref[i]["bl"] + delta_x, self.pin_ref[i]["bt"] + delta_y)

            # Variables
            self.widget_width = widget_width
            self.widget_height = widget_height
            self.w2 = widget_width * 0.5
            self.h2 = widget_height * 0.5
            self.update()
        else:
            self.Set_Size_Corner(widget_width, widget_height)
    def Set_Color_Display(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue
        self.update()
    def Set_Theme(self, color_1, color_2):
        self.color_1 = color_1
        self.color_2 = color_2
        self.update()
    def Set_Layout(self, layout):
        self.layout = layout
        self.update()

    # Database
    def Database_Run(self, directory):
        self.database_path = os.path.normpath( directory + "\\DATABASE\\imagine_board_database.db" )
        self.Database_Connect( self.database_path )
        self.Database_Table()
        self.update()
    def Database_Connect(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()
    def Database_Table(self):
        try:
            self.cursor.execute("""CREATE TABLE ref_pin(
                p_path TEXT,
                p_index INTEGER,
                p_active NULL,
                p_select NULL,
                p_pack NULL,
                p_text TEXT,
                p_color REAL,
                p_pis REAL,
                p_pir REAL,
                p_ox REAL,
                p_oy REAL,
                p_rx REAL,
                p_ry REAL,
                p_rn REAL,
                p_ro REAL,
                p_ss REAL,
                p_sr REAL,
                p_dx REAL,
                p_dy REAL,
                p_dw REAL,
                p_dh REAL,
                p_dxw REAL,
                p_dyh REAL,
                p_cl REAL,
                p_ct REAL,
                p_cr REAL,
                p_cb REAL,
                p_bl REAL,
                p_bt REAL,
                p_br REAL,
                p_bb REAL,
                p_bw REAL,
                p_bh REAL,
                p_perimeter REAL,
                p_area REAL,
                p_ratio REAL,
                p_egs NULL,
                p_efx NULL,
                p_efy NULL,
                p_qpixmap BLOB,
                p_render BLOB
                )
                """)
            self.connection.commit()
        except sqlite3.OperationalError:
            pass
    def Database_Disconnect(self):
        self.connection.close()

    def Database_Pin_New(self, pin):
        try:
            command = """INSERT INTO ref_pin VALUES(
                :_path,
                :_index,
                :_active,
                :_select,
                :_pack,
                :_text,
                :_color,
                :_pis,
                :_pir,
                :_ox,
                :_oy,
                :_rx,
                :_ry,
                :_rn,
                :_ro,
                :_ss,
                :_sr,
                :_dx,
                :_dy,
                :_dw,
                :_dh,
                :_dxw,
                :_dyh,
                :_cl,
                :_ct,
                :_cr,
                :_cb,
                :_bl,
                :_bt,
                :_br,
                :_bb,
                :_bw,
                :_bh,
                :_perimeter,
                :_area,
                :_ratio,
                :_egs,
                :_efx,
                :_efy,
                :_qpixmap,
                :_render
                )"""
            self.cursor.execute(command, pin)
            self.connection.commit()
        except sqlite3.OperationalError:
            pass
    def Database_Pin_Edit(self):
        pass
    def Database_Pin_Rebase(self):
        pass
    def Database_Pin_Delete(self):
        pass
    def Database_Board_Load(self):
        pass
    def Database_Board_Save(self):
        pass
    def Database_Board_Undo(self):
        pass
    def Database_Board_Rebase(self):
        pass
    def Database_Board_Delete(self):
        pass

    # Events
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        pass
    def closeEvent(self, event):
        pass

    # Painter
    def paintEvent(self, event):
        # Painter
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background Hover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color_alpha)))
        painter.drawRect(0,0,self.widget_width,self.widget_height)

        """
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
            render = self.pin_ref[i]["render"]

        self.cursor.fetchall()


            check_1 = ((bl >= 0 or br <= self.widget_width) or (bt >= 0 or bb <= self.widget_width))
            check_2 = ((bl < 0 and br > self.widget_width) or (bt < 0 or bb > self.widget_width))
            if (check_1 == True or check_2 == True):
                # # Clip Mask
                # clip, sides = self.Clip_Construct(self.pin_ref, i)
                # square = QPainterPath()
                # square.moveTo(clip[0][0], clip[0][1])
                # square.lineTo(clip[1][0], clip[1][1])
                # square.lineTo(clip[2][0], clip[2][1])
                # square.lineTo(clip[3][0], clip[3][1])
                # painter.setClipPath(square)

                # Draw Images & Background Color
                if pack == False: # Hides images to be packed
                    if (text == None or len(text) == 0): # Draw Image
                        # Missing Image
                        if qpixmap == None:
                            qpixmap = QPixmap(path)
                            if qpixmap.isNull() == False:
                                self.pin_ref[i]["render"] = render = qpixmap.scaled( int(dw), int(dh), Qt.IgnoreAspectRatio, Qt.FastTransformation)
                         # Render Image
                        if render != None:
                            painter.setPen(QtCore.Qt.NoPen)
                            painter.setBrush(QtCore.Qt.NoBrush)
                            painter.drawPixmap( int(dx), int(dy), render )
                        else: # No Image to Render
                            # Highlight
                            painter.setPen(QtCore.Qt.NoPen)
                            painter.setBrush(QBrush(QColor(self.color_1)))
                            painter.drawRect( QRectF(bl, bt, br-bl, bb-bt) )
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

                # Mask Reset
                painter.setClipRect(QRectF(0,0, self.widget_width,self.widget_height), Qt.ReplaceClip)
        """