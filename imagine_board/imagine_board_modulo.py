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

# Python
import os
import copy
import math
import time
import urllib
import zipfile
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Imagine Board
from .imagine_board_calculations import *

#endregion
#region Global Variables

# Color Picker Display
colorpicker_size = 250
cps_a = colorpicker_size * 0.015
cps_b = colorpicker_size - ( cps_a * 2 )
cps_c = colorpicker_size * 0.040
cps_d = colorpicker_size - ( cps_c * 2 )
cps_e = colorpicker_size * 0.105
cps_f = colorpicker_size - ( cps_e * 2 )
cps_g = colorpicker_size * 0.120
cps_h = colorpicker_size - ( cps_g * 2 )

#endregion

#region Shared Function

# Painter
def Painter_Triangle( self, painter, w2, h2, side ):
    # Painter
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( QColor( self.color_1 ) ) )
    # Variables
    kw = 0.3 * side
    kh = 0.2 * side
    d = 0.5
    # Polygons
    poly_tri = QPolygon( [
        QPoint( int( w2 - kw ), int( h2 - kh ) ),
        QPoint( int( w2 + kw ), int( h2 - kh ) ),
        QPoint( int( w2 ),      int( h2 + kh ) ),
        ] )
    painter.drawPolygon( poly_tri )
def Painter_Locked( self, painter, w2, h2, side ):
    # Painter
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( QColor( self.color_1 ) ) )
    # Variables
    kw = 0.3 * side
    kh = 0.2 * side
    d = 0.5
    # Polygons
    bar = QPolygon( [
        QPoint( int( w2 - kw ), int( h2 - kh * d ) ),
        QPoint( int( w2 + kw ), int( h2 - kh * d ) ),
        QPoint( int( w2 + kw ), int( h2 + kh * d ) ),
        QPoint( int( w2 - kw ), int( h2 + kh * d ) ),
        ] )
    painter.drawPolygon( bar )

# Display
def Display_Icon( self, name ):
    # name = "warning"
    # Variables
    image_size = 500
    icon_size = 200
    icon_margin = int( ( image_size - icon_size ) * 0.5 )
    # QPixmap
    qpixmap = QPixmap( image_size, image_size )
    qpixmap.fill( Qt.transparent )
    qicon = Krita.instance().icon( name ).pixmap( QSize( icon_size, icon_size ) )    
    painter = QPainter( qpixmap )
    painter.drawPixmap( icon_margin, icon_margin, qicon )
    painter.end()
    return qpixmap

# Cursor
def Cursor_Icon( self ):
    if ( self.state_pickcolor == True and self.state_press == True ):
        QApplication.setOverrideCursor( Qt.CrossCursor )
    else:
        QApplication.restoreOverrideCursor()

# Drag
def Insert_Drag( self, path, clip ):
    if path != None:
        self.drag = True
        self.SIGNAL_DRAG.emit( path, clip )
# Drop
def Drop_Inside( self, event, local_only ):
    # Mimedata
    mimedata = event.mimeData()

    # Has Boolean
    has_text = mimedata.hasText()
    has_html = mimedata.hasHtml()
    has_urls = mimedata.hasUrls()
    has_image = mimedata.hasImage()
    # has_color = mimedata.hasColor()

    # Data
    data_text = mimedata.text()
    data_html = mimedata.html()
    data_urls = mimedata.urls()
    data_image = mimedata.imageData()
    # data_color = mimedata.colorData()

    # Construct Mime Data
    mime_data = []
    if ( has_text == True and has_html == True ):
        if local_only == False:
            mime_data.append( data_text )
    elif ( has_text == True and has_html == False ):
        for i in range( 0, len( data_urls ) ):
            qurl = data_urls[i].toLocalFile()
            exists = os.path.exists( qurl )
            if exists == True:
                mime_data.append( qurl )

    # Sort
    if len( mime_data ) > 0:
        mime_data.sort()

    # Return
    return mime_data

# Path
def Path_Copy( self, path ):
    copy = QApplication.clipboard()
    copy.clear()
    copy.setText( path )
# Color Picker
def ColorPicker_Event( self, ex, ey, qimage_grab, state_press ):
    if ( self.state_pickcolor == True and qimage_grab != None ):
        # Event
        ex = Limit_Range( ex, 0, self.ww - 1 )
        ey = Limit_Range( ey, 0, self.hh - 1 )
        # Picker Location
        pos = QPoint( ex, ey )
        point = self.mapToGlobal( pos )
        px = point.x() - ( colorpicker_size * 0.5 )
        py = point.y() - ( colorpicker_size * 0.5 )
        # Pixel RGB ( 0-1 )
        pixel = qimage_grab.pixelColor( ex , ey )
        red = pixel.redF()
        green = pixel.greenF()
        blue = pixel.blueF()

        # Apply Color
        if self.pigment_o != None:
            if state_press == True:
                self.pigment_o.API_Input_Kelvin( 6500 )
                cor = self.pigment_o.API_Input_Preview( "RGB", red, green, blue, 0 )
            if state_press == False:
                cor = self.pigment_o.API_Input_Apply( "RGB", red, green, blue, 0 )
            red   = cor[ "rgb_d1" ]
            green = cor[ "rgb_d2" ]
            blue  = cor[ "rgb_d3" ]
        else:
            active_document = Krita.instance().activeDocument()
            if active_document == None:
                d_cm = "RGBA"
                d_cd = "U8"
                d_cp = ""
            else:
                d_cm = active_document.colorModel()
                d_cd = active_document.colorDepth()
                d_cp = active_document.colorProfile()
            d_ac = Krita.instance().activeWindow().activeView().canvas()
            # Managed Colors RGB only
            managed_color = ManagedColor( d_cm, d_cd, d_cp )
            comp = managed_color.components()
            if ( d_cm == "A" or d_cm == "GRAYA" ):
                comp = [ red, 1 ]
            if d_cm == "RGBA":
                if ( d_cd == "U8" or d_cd == "U16" ):
                    comp = [ blue, green, red, 1 ]
                if ( d_cd == "F16" or d_cd == "F32" ):
                    comp = [ red, green, blue, 1 ]
            managed_color.setComponents( comp )
            # Color for Canvas
            if d_ac != None:
                display = managed_color.colorForCanvas( d_ac )
                red   = display.redF()
                green = display.greenF()
                blue  = display.blueF()
            # Apply Color
            if state_press == False:
                Krita.instance().activeWindow().activeView().setForeGroundColor( managed_color )

        # Display Color
        qcolor = QColor( int( red * 255 ), int( green * 255 ), int( blue * 255 ) )
        hex_code = qcolor.name()
        self.color_active = qcolor
        if state_press == False:
            # Previous
            self.color_previous = qcolor
            # Clipboard
            clip_board = QApplication.clipboard()
            clip_board.clear()
            clip_board.setText( f"{ hex_code }" )
def ColorPicker_Render( self, painter, ex, ey ):
    # Values
    ex = Limit_Range( ex, 0, self.ww )
    ey = Limit_Range( ey, 0, self.hh )
    ex = int( ex - ( colorpicker_size * 0.5 ) )
    ey = int( ey - ( colorpicker_size * 0.5 ) )

    # Mask Neutral
    mask_neutral = QPainterPath()
    mask_neutral.addEllipse( ex, ey, colorpicker_size, colorpicker_size )
    mask_neutral.addEllipse( ex + cps_g, ey + cps_g, cps_h, cps_h )
    painter.setClipPath( mask_neutral )
    # Color Neutral
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( QColor( 128, 128, 128 ) ) )
    painter.drawEllipse( ex, ey, colorpicker_size, colorpicker_size )

    # Mask Previous
    mask_previous = QPainterPath()
    mask_previous.addEllipse( ex + cps_a, ey + cps_a, cps_b, cps_b )
    mask_previous.addEllipse( ex + cps_e, ey + cps_e, cps_f, cps_f )
    painter.setClipPath( mask_previous )
    # Color Previous
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( self.color_previous ) )
    painter.drawEllipse( ex, ey, colorpicker_size, colorpicker_size )

    # Mask Active
    mask_previous = QPainterPath()
    mask_previous.addEllipse( ex + cps_c, ey + cps_c, cps_d, cps_d )
    mask_previous.addEllipse( ex + cps_e, ey + cps_e, cps_f, cps_f )
    painter.setClipPath( mask_previous )
    # Color Previous
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( self.color_active ) )
    painter.drawEllipse( ex, ey, colorpicker_size, colorpicker_size )

    # Reset Mask
    mask_reset = QPainterPath()
    mask_reset.addRect( 0, 0, self.ww, self.hh )
    painter.setClipPath( mask_reset )
# Insert
def Insert_Check( self ):
    doc = Krita.instance().documents()
    insert = len( doc ) > 0
    return insert

#endregion
#region Panels

class ImagineBoard_Preview( QWidget ):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_DROP = QtCore.pyqtSignal( list )
    # Preview
    SIGNAL_MODE = QtCore.pyqtSignal( int )
    SIGNAL_INCREMENT = QtCore.pyqtSignal( int )
    # Menu
    SIGNAL_FUNCTION = QtCore.pyqtSignal( list )
    SIGNAL_PIN_IMAGE = QtCore.pyqtSignal( [ dict, dict ] )
    SIGNAL_RANDOM = QtCore.pyqtSignal()
    SIGNAL_FULL_SCREEN = QtCore.pyqtSignal( bool )
    SIGNAL_LOCATION = QtCore.pyqtSignal( str )
    SIGNAL_ANALYSE = QtCore.pyqtSignal( [ QImage ] )
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal( [ str, dict ] )
    # UI
    SIGNAL_EXTRA_LABEL = QtCore.pyqtSignal( str )
    SIGNAL_EXTRA_PANEL = QtCore.pyqtSignal( bool )
    SIGNAL_EXTRA_VALUE = QtCore.pyqtSignal( int )
    SIGNAL_EXTRA_MAX = QtCore.pyqtSignal( int )


    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Preview, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 1
        self.hh = 1
        self.w2 = 0.5
        self.h2 = 0.5

        # Event
        self.ox = 0
        self.oy = 0
        self.ex = 0
        self.ey = 0

        # Display
        self.preview_path = None
        self.preview_qpixmap = None
        self.scale_method = Qt.FastTransformation

        # Compact
        self.file_search = []

        # State
        self.state_maximized = False
        self.state_press = False
        self.state_pickcolor = False
        self.state_clip = False
        self.state_animation = False
        self.state_compact = False
        self.state_information = False
        self.state_vector = False
        # Interaction
        self.operation = None
        # Camera
        self.pcmx = 0
        self.pcmy = 0
        self.pcz = 1
        self.cmx = 0 # Moxe X
        self.cmy = 0 # Move Y
        self.cz = 1 # Zoom
        self.display = False

        # Colors
        self.color_1 = QColor( "#ffffff" )
        self.color_2 = QColor( "#000000" )
        self.color_alpha = QColor( 0, 0, 0, 50 )
        self.color_clip = QColor( 0, 0, 0, 100 )

        # Function>>
        self.function_operation = ""

        # Edit
        self.edit_greyscale = False
        self.edit_invert_h = False
        self.edit_invert_v = False

        # Color Picker
        self.pigment_o = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # Bounding Box
        self.bl = 0
        self.bt = 0
        self.br = 0
        self.bb = 0
        self.bw = self.br - self.bl
        self.bh = self.bb - self.bt

        # Clip
        self.clip_node = None
        self.cl = 0.1  # 0-1
        self.ct = 0.1  # 0-1
        self.cr = 0.9  # 0-1
        self.cb = 0.9  # 0-1
        self.cw = self.cr - self.cl  # 0-1
        self.ch = self.cb - self.ct  # 0-1

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False

        # Animation
        self.anim_sequence = []
        self.anim_frame = 0
        self.anim_count = 0
        self.anim_rate = 33
        self.Anim_Timer()

        # Compact
        self.comp_path = []
        self.comp_sequence = []
        self.comp_index = 0
        self.comp_count = 0
    def sizeHint( self ):
        return QtCore.QSize( 5000,5000 )

    # Relay
    def Set_FileSearch( self, file_search ):
        self.file_search = file_search
    def Set_Pigment_O( self, plugin ):
        self.pigment_o = plugin
    def Set_Theme( self, color_1, color_2 ):
        self.color_1 = color_1
        self.color_2 = color_2
    def Set_Size( self, ww, hh, state_maximized ):
        self.ww = ww
        self.hh = hh
        self.w2 = ww * 0.5
        self.h2 = hh * 0.5
        self.state_maximized = state_maximized
        self.resize( ww, hh )
    def Set_Function( self, function_operation ):
        self.function_operation = function_operation
        self.update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()
    def Set_Display( self, boolean ):
        self.display = boolean
        self.update()

    # Display
    def Display_Reset( self, state ):
        # Variables
        if state == True:
            self.state_animation = False
            self.state_compact = False
        # Functions
        self.Camera_Reset()
        self.Clip_Reset()
        self.Edit_Reset()
        self.Anim_Pause()
    def Display_Default( self ):
        self.Display_Reset( True )
        self.preview_path = None
        self.preview_qpixmap = None
        self.update()
        self.Camera_Grab()
    def Display_Path( self, image_path ):
        qpixmap = QPixmap( image_path )
        if qpixmap.isNull() == False:
            if self.preview_path != image_path:
                self.Display_Reset( True )
                self.Check_Vector( image_path )
            self.preview_qpixmap = qpixmap
        else:
            self.preview_qpixmap = True
        self.preview_path = image_path
        self.update()
        self.Camera_Grab()
    def Display_QPixmap( self, qpixmap ):
        if qpixmap.isNull() == False:
            self.Display_Reset( True )
            self.preview_path = None
            self.preview_qpixmap = qpixmap
            self.update()
            self.Camera_Grab()
        else:
            self.Display_Default()
    def Display_Animation( self, image_path ):
        qmovie = QMovie( image_path )
        if qmovie.isValid() == True:
            # Variables
            if self.preview_path != image_path:
                self.Display_Reset( True )
            self.preview_path = image_path
            # Frames
            frames = qmovie.frameCount()
            speed = qmovie.speed() / 100
            if frames == 1:
                self.Display_Path( image_path )
            else:
                # Variables
                self.state_animation = True
                self.anim_frame = 0
                # Frames
                rate = []
                sequence = []
                for i in range( 0, frames ):
                    qmovie.jumpToFrame( i )
                    delay = qmovie.nextFrameDelay()
                    rate.append( delay )
                    qpixmap = qmovie.currentPixmap()
                    if qpixmap.isNull() == False:
                        sequence.append( qpixmap )
                mean = Stat_Mean( rate )
                # Variables
                self.anim_sequence = sequence
                self.anim_count = len( sequence ) - 1
                self.anim_rate = int( mean * speed )
                # Animation
                self.Anim_Play()
                # UI
                self.SIGNAL_EXTRA_PANEL.emit( True )
                self.SIGNAL_EXTRA_MAX.emit( frames - 1 )
                self.SIGNAL_EXTRA_VALUE.emit( 0 )
                # Garbage
                del qmovie
            self.update()
        else:
            self.Display_Path( image_path )
    def Display_Compact( self, zip_path ):
        # Variables
        self.comp_path = []
        self.comp_sequence = []
        self.comp_index = 0
        # Open Zip File
        self.Display_Reset( True )
        if zipfile.is_zipfile( zip_path ):
            # Variables
            self.state_compact = True
            self.preview_path = zip_path
            # Archive
            self.comp_archive = zipfile.ZipFile( zip_path, "r" )
            name_list = self.comp_archive.namelist()
            for name in name_list:
                try:
                    if name.split( "." )[1] in self.file_search:
                        self.comp_path.append( name )
                except:
                    pass
        # Display
        if len( self.comp_path ) > 0:
            # Variables
            self.preview_qpixmap = self.Comp_Read( self.comp_archive, self.comp_path[self.comp_index] )
            self.comp_count = len( self.comp_path ) - 1
            # UI
            self.SIGNAL_EXTRA_PANEL.emit( True )
            self.SIGNAL_EXTRA_MAX.emit( self.comp_count )
            self.SIGNAL_EXTRA_VALUE.emit( 0 )
            self.Extra_Label( True )
            # Update
            self.update()
            self.Camera_Grab()
        else:
            self.Display_Path( zip_path )
 
    # Draw
    def Draw_Render( self, qpixmap ):
        # QPixmap
        if self.display == False:
            draw = qpixmap.scaled( int( self.ww * self.cz ), int( self.hh * self.cz ), Qt.KeepAspectRatio, self.scale_method )
        else:
            ww = qpixmap.width()
            hh = qpixmap.height()
            draw = qpixmap.scaled( int( ww * self.cz ), int( hh * self.cz ), Qt.KeepAspectRatio, self.scale_method )
        self.bw = draw.width()
        self.bh = draw.height()
        # Variables
        self.bl = self.w2 - ( self.bw * 0.5 ) + ( self.cmx * self.cz )
        self.bt = self.h2 - ( self.bh * 0.5 ) + ( self.cmy * self.cz )
        self.br = self.bl + self.bw
        self.bb = self.bt + self.bh
        # Return
        return draw
    def Draw_Clip( self, qpixmap ):
        if self.state_clip == True:
            w = self.preview_qpixmap.width()
            h = self.preview_qpixmap.height()
            qpixmap = qpixmap.copy( int( w * self.cl ), int( h * self.ct ), int( w * self.cw ), int( h * self.ch ) )
        return qpixmap

    # Animation
    def Anim_Timer( self ):
        self.anim_timer = QtCore.QTimer( self )
        self.anim_timer.timeout.connect( lambda: self.Anim_Increment( +1 ) )
        self.anim_timer.stop()
    def Anim_Increment( self, increment ):
        if self.state_animation == True:
            self.anim_frame = Limit_Loop( int( self.anim_frame + increment ), self.anim_count )
            self.preview_qpixmap = self.anim_sequence[ self.anim_frame ]
            self.SIGNAL_EXTRA_VALUE.emit( self.anim_frame )
            self.update()
    def Anim_Play( self ):
        if self.state_animation == True:
            self.anim_timer.start( self.anim_rate )
            self.Extra_Label( False )
    def Anim_Pause( self ):
        self.anim_timer.stop()
        self.Extra_Label( True )
    def Anim_Back( self ):
        if ( self.state_animation == True and self.anim_timer.isActive() == False ):
            self.Anim_Increment( -1 )
            self.Extra_Label( True )
    def Anim_Forward( self ):
        if ( self.state_animation == True and self.anim_timer.isActive() == False ):
            self.Anim_Increment( +1 )
            self.Extra_Label( True )
    def Anim_Frame( self, frame ):
        if self.state_animation == True:
            self.anim_frame = Limit_Loop( int( frame ), self.anim_count )
            self.preview_qpixmap = self.anim_sequence[ self.anim_frame ]
            if self.anim_timer.isActive() == False:
                self.Extra_Label( True )
                self.update()
    # Animation Export
    def Anim_Export_Cycle( self ):
        if self.state_animation == True:
            for i in range( 0, len( self.anim_sequence ) ):
                self.Anim_Export_Index( i )
    def Anim_Export_Index( self, index ):
        if self.state_animation == True:
            # Construct New Path
            path = os.path.split( self.preview_path )
            directory = path[0]
            split = os.path.splitext( path[1] )
            name = split[0]
            extension = split[1]

            # Variables
            name_new = f"{ name }_{ str( index ).zfill( 4 ) }.png"
            save_path = os.path.join( directory, name_new )
            exists = os.path.exists( save_path )
            if exists == False:
                screenshot_qpixmap = self.anim_sequence[ index ]
                screenshot_qpixmap.save( save_path )
                # Logger
                try:QtCore.qDebug( f"Imagine Board | SCREENSHOT { index }:{ self.frame_count }" )
                except:pass
                # Garbage
                del screenshot_qpixmap

    # Compact
    def Comp_Read( self, archive, name ):
        if self.state_compact == True:
            try:
                extract = archive.open( name )
                data = extract.read()
                qpixmap = QPixmap()
                qpixmap.loadFromData( data )
            except:
                qpixmap = None
            return qpixmap
    def Comp_Increment( self, increment ):
        if self.state_compact == True:
            # Preparation
            self.Display_Reset( False )
            # Index
            comp_index = Limit_Range( self.comp_index + increment, 0, self.comp_count )
            if self.comp_index != comp_index:
                self.comp_index = comp_index
                self.preview_qpixmap = self.Comp_Read( self.comp_archive, self.comp_path[self.comp_index] )
    	    # Signals
            self.SIGNAL_EXTRA_VALUE.emit( self.comp_index )
            self.update()
            self.Camera_Grab()
    def Comp_Back( self ):
        if self.state_compact == True:
            self.Comp_Increment( -1 )
            self.Extra_Label( True )
    def Comp_Forward( self ):
        if self.state_compact == True:
            self.Comp_Increment( +1 )
            self.Extra_Label( True )
    def Comp_Index( self, index ):
        if self.state_compact == True:
            if self.comp_index != index:
                self.Display_Reset( False )
                self.comp_index = Limit_Range( index, 0, self.comp_count )
                self.preview_qpixmap = self.Comp_Read( self.comp_archive, self.comp_path[self.comp_index] )
                self.Extra_Label( True )
            self.update()
            self.Camera_Grab()
    # Compct Export
    def Comp_Export_Index( self, index ):
        if self.state_compact == True:
            # File Path
            file_directory = os.path.dirname( self.preview_path )
            file_basename = os.path.basename( self.preview_path )
            file_name = os.path.splitext( file_basename )[0]
            # Zip Path
            zip_namelist = self.comp_path[self.comp_index]
            zip_basename = os.path.basename( os.path.abspath( zip_namelist ))
            # Formating
            file_name    = file_name.replace( " ", "_" )
            zip_basename = zip_basename.replace( " ", "_" )
            join_name = f"{ file_name }_{ zip_basename }"
            save_location = os.path.join( file_directory, join_name )
            # Image Save
            qpixmap = self.Comp_Read( self.comp_archive, zip_namelist )
            exists = os.path.exists( save_location )
            if exists == False and qpixmap.isNull() == False:
                qpixmap.save( save_location )
            else:
                string = f"Imagine Board | ERROR zip file not saved"
                QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )

    # Extra UI
    def Extra_Label( self, mode ):
        string = ""
        if ( self.state_animation == True and mode == True ) == True:
            string = f"{ self.anim_frame }:{ self.anim_count }"
        if ( self.state_compact == True and mode == True and len( self.comp_path ) > 0 ) == True:
            string = f"{ self.comp_path[self.comp_index] }"
        self.SIGNAL_EXTRA_LABEL.emit( string )

    # Camera
    def Camera_Reset( self ):
        self.cmx = 0
        self.cmy = 0
        self.cz = 1
    def Camera_Previous( self ):
        self.pcmx = self.cmx
        self.pcmy = self.cmy
        self.pcz = self.cz
    def Camera_Move( self, ex, ey ):
        if self.cz != 0:
            self.cmx = self.pcmx + ( ( ex - self.ox ) / self.cz )
            self.cmy = self.pcmy + ( ( ey - self.oy ) / self.cz )
    def Camera_Scale( self, ex, ey ):
        factor = 200
        self.cz = Limit_Range( self.pcz - ( ( ey - self.oy ) / factor ), 0, 100 )
    def Camera_Grab( self ):
        try:self.qimage_grab = self.grab().toImage()
        except:pass

    # Pagination
    def Pagination_Reset( self, ex, ey ):
        self.ox = ex
        self.oy = ey
    def Pagination_Stylus( self, ex, ey ):
        factor = 20
        dx = ex - self.ox
        dy = ey - self.oy
        if dx >= factor:
            self.SIGNAL_INCREMENT.emit( +1 )
            self.Pagination_Reset( ex, ey )
        if dx <= -factor:
            self.SIGNAL_INCREMENT.emit( -1 )
            self.Pagination_Reset( ex, ey )
        if dy >= factor:
            self.SIGNAL_INCREMENT.emit( -1 )
            self.Pagination_Reset( ex, ey )
        if dy <= -factor:
            self.SIGNAL_INCREMENT.emit( +1 )
            self.Pagination_Reset( ex, ey )

    # Clip
    def Clip_Reset( self ):
        self.state_clip = False
        self.cl = 0.1
        self.ct = 0.1
        self.cr = 0.9
        self.cb = 0.9
        self.cw = self.cr - self.cl
        self.ch = self.cb - self.ct
    def Clip_Node( self, ex, ey ):
        # Nodes
        n1 = [ self.bl + self.bw * self.cl, self.bt + self.bh * self.ct ]
        n2 = [ self.bl + self.bw * self.cr, self.bt + self.bh * self.ct ]
        n3 = [ self.bl + self.bw * self.cl, self.bt + self.bh * self.cb ]
        n4 = [ self.bl + self.bw * self.cr, self.bt + self.bh * self.cb ]

        # Distance
        d1 = Trig_2D_Points_Distance( ex, ey, n1[0], n1[1] )
        d2 = Trig_2D_Points_Distance( ex, ey, n2[0], n2[1] )
        d3 = Trig_2D_Points_Distance( ex, ey, n3[0], n3[1] )
        d4 = Trig_2D_Points_Distance( ex, ey, n4[0], n4[1] )
        # Sort
        dist = [ [ d1, 1 ], [ d2, 2 ], [ d3, 3 ], [ d4, 4 ] ]
        dist.sort()
        factor = 20
        if dist[0][0] <= factor:
            self.clip_node = dist[0][1]
        else:
            self.clip_node = None
    def Clip_Edit( self, ex, ey, node ):
        if node != None:
            lx = ( Limit_Range( ex, self.bl, self.br ) - self.bl ) / self.bw
            ly = ( Limit_Range( ey, self.bt, self.bb ) - self.bt ) / self.bh
            if node == 1:
                if lx != self.cr:self.cl = lx
                if ly != self.cb:self.ct = ly
            if node == 2:
                if lx != self.cl:self.cr = lx
                if ly != self.cb:self.ct = ly
            if node == 3:
                if lx != self.cr:self.cl = lx
                if ly != self.ct:self.cb = ly
            if node == 4:
                if lx != self.cl:self.cr = lx
                if ly != self.ct:self.cb = ly
    def Clip_Flip( self ):
        if self.cr < self.cl:
            self.cl, self.cr = self.cr, self.cl
        if self.cb < self.ct:
            self.ct, self.cb = self.cb, self.ct
        self.cw = self.cr - self.cl
        self.ch = self.cb - self.ct

    # Information
    def Check_Vector( self, path ):
        self.state_vector = os.path.splitext( path )[1] in [ ".svg", ".svgz" ]
    def Information_Display( self ):
        # Variables
        path = self.preview_path
        # Logic
        if path == None:
            text = "None"
        else:
            # String
            text = ""

            # Paths
            try:
                info_path = os.path.split( path )
                info_dir = info_path[0]
                basename = os.path.splitext( info_path[1] )
                info_name = basename[0]
                info_type = basename[1].replace( ".", "" )
                text += f"Directory : { info_dir }\n"
                text += f"Name : { info_name } [ { info_type.upper() } ]\n"
            except:
                pass

            # Time
            try:
                mod_time = os.path.getmtime( path )
                local_time = time.localtime( mod_time )
                info_time = time.strftime( f"%Y-%m[%b]-%d[%a] %H:%M:%S", local_time )
                text += f"Time : { info_time }\n"
            except:
                pass

            # Size
            try:
                b = os.path.getsize( path )
                kb = b / 1000
                mb = kb / 1000
                if kb >= 1 and kb < 1000:
                    info_size = kb
                    info_scale = "Kb"
                elif mb >= 1 and mb < 1000:
                    info_size = mb
                    info_scale = "Mb"
                else:
                    info_size = b
                    info_scale = "b"
                text += f"Size : { round( info_size, 3 ) } { info_scale }\n"
            except:
                pass

            # Dimensions
            try:
                info_width = self.preview_qpixmap.width()
                info_height = self.preview_qpixmap.height()
                text += f"Dimension : { info_width } x { info_height } px"
            except:
                pass
        # Return
        return text

    # Edit
    def Edit_Reset( self ):
        self.edit_greyscale = False
        self.edit_invert_h = False
        self.edit_invert_v = False
    def Edit_Display( self, operation ):
        # Operations Boolean Toggle
        if operation == "egs":
            self.edit_greyscale = not self.edit_greyscale
        if operation == "efx":
            self.edit_invert_h = not self.edit_invert_h
        if operation == "efy":
            self.edit_invert_v = not self.edit_invert_v
        if operation == None:
            self.Edit_Reset()

        # Read
        if ( self.state_animation == False and self.state_compact == False ):
            qimage = QImage( self.preview_path )
        elif self.state_animation == True:
            qpixmap = self.anim_sequence[self.anim_frame]
            qimage = qpixmap.toImage()
        elif self.state_compact == True:
            qpixmap = self.Comp_Read( self.comp_archive, self.comp_path[self.comp_index] )
            qimage = qpixmap.toImage()

        # Edit Image
        if self.edit_greyscale == True:
            qimage = qimage.convertToFormat( 24 )
        if ( self.edit_invert_h == True or self.edit_invert_v == True ):
            qimage = qimage.mirrored( self.edit_invert_h, self.edit_invert_v )
        self.preview_qpixmap = QPixmap().fromImage( qimage )
        # Update
        self.update()

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        self.state_press = False
        state_null = self.preview_qpixmap == None
        state_insert = Insert_Check( self )
        state_animation = self.state_animation
        state_compact = self.state_compact
        state_vector = self.state_vector
        path_none = self.preview_path == None

        # Strings
        string_pickcolor = "Picker"
        if self.pigment_o == None:
            string_pickcolor += " [RGB]"
        string_clip = ""
        if self.state_clip == True:
            string_clip = " (Clip)"

        # Clip
        clip = { 
            "cstate" : self.state_clip,
            "cl": self.cl,
            "ct": self.ct,
            "cw": self.cw,
            "ch": self.ch,
            }

        # Cursor
        Cursor_Icon( self )

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )

        # General
        action_function = qmenu.addAction( "Function >> " + self.function_operation )
        action_pin = qmenu.addAction( "Pin Reference" + string_clip )
        action_random = qmenu.addAction( "Random Index" )
        action_clip = qmenu.addAction( "Clip Image" )
        action_full_screen = qmenu.addAction( "Full Screen" )
        qmenu.addSeparator()
        # File
        menu_file = qmenu.addMenu( "File" )
        action_file_location = menu_file.addAction( "File Location" )
        action_file_copy = menu_file.addAction( "Copy Path" )
        action_file_information = menu_file.addAction( "Information" )
        # Animation
        menu_anim = qmenu.addMenu( "Animation" )
        action_anim_export_one = menu_anim.addAction( "Export One Frame" )
        action_anim_export_all = menu_anim.addAction( "Export All Frames" )
        # Compact
        menu_comp = qmenu.addMenu( "Compressed" )
        action_comp_export_one = menu_comp.addAction( "Export One" )
        # Edit
        menu_edit = qmenu.addMenu( "Edit" )
        action_edit_greyscale = menu_edit.addAction( "View Greyscale" )
        action_edit_invert_h = menu_edit.addAction( "Flip Horizontal" )
        action_edit_invert_v = menu_edit.addAction( "Flip Vertical" )
        action_edit_reset = menu_edit.addAction( "Reset" )
        # Color
        menu_color = qmenu.addMenu( "Color" )
        action_pick_color = menu_color.addAction( string_pickcolor )
        action_analyse = menu_color.addAction( "Analyse" + string_clip )
        # Insert
        menu_insert = qmenu.addMenu( "Insert" )
        action_document = menu_insert.addAction( "Document" + string_clip )
        action_insert_layer = menu_insert.addAction( "Layer" + string_clip )
        action_insert_ref = menu_insert.addAction( "Reference" + string_clip )

        # Check Clip
        action_clip.setCheckable( True )
        action_clip.setChecked( self.state_clip )
        # Check Full Screen
        action_full_screen.setCheckable( True )
        action_full_screen.setChecked( self.state_maximized )
        # Check Information
        action_file_information.setCheckable( True )
        action_file_information.setChecked( self.state_information )
        # Check Edit
        action_edit_greyscale.setCheckable( True )
        action_edit_greyscale.setChecked( self.edit_greyscale )
        action_edit_invert_h.setCheckable( True )
        action_edit_invert_h.setChecked( self.edit_invert_h )
        action_edit_invert_v.setCheckable( True )
        action_edit_invert_v.setChecked( self.edit_invert_v )
        # Check Color
        action_pick_color.setCheckable( True )
        action_pick_color.setChecked( self.state_pickcolor )

        # Disable General
        if state_null == True:
            action_function.setEnabled( False )
            action_pin.setEnabled( False )
            action_random.setEnabled( False )
        # Disable Clip
        if state_null == True or state_vector == True or path_none == True:
            action_clip.setEnabled( False )
        # Disable File
        if state_null == True or path_none == True:
            menu_file.setEnabled( False )
        # Disable Animation
        if state_null == True or state_animation == False or path_none == True:
            menu_anim.setEnabled( False )
        # Disable Compact
        if state_null == True or state_compact == False or path_none == True:
            menu_comp.setEnabled( False )
        # Disable Edit
        if state_null == True or state_animation == True or path_none == True:
            menu_edit.setEnabled( False )
        # Disable Color
        if state_null == True:
            menu_color.setEnabled( False )
        if state_null == True or self.pigment_o == None:
            action_analyse.setEnabled( False )
        # Disable Insert
        if state_null == True or path_none == True or state_compact == True:
            menu_insert.setEnabled( False )
        if state_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_ref.setEnabled( False )

        #endregion
        #region Action

        # Mapping
        action = qmenu.exec_( self.mapToGlobal( event.pos() ) )

        # General
        if action == action_function:
            self.SIGNAL_FUNCTION.emit( [ self.preview_path ] )
        if action == action_pin:
            pin = {
                "bx" : self.w2,
                "by" : self.h2,
                "image_path" : self.preview_path,
                }
            self.SIGNAL_PIN_IMAGE.emit( pin, clip )
        if action == action_random:
            self.SIGNAL_RANDOM.emit()
        if action == action_clip:
            self.state_clip = not self.state_clip
        if action == action_full_screen:
            self.SIGNAL_FULL_SCREEN.emit( not self.state_maximized )

        # File
        if action == action_file_location:
            self.SIGNAL_LOCATION.emit( self.preview_path )
        if action == action_file_copy:
            Path_Copy( self, self.preview_path )
        if action == action_file_information:
            self.state_information = not self.state_information

        # Animation
        if action == action_anim_export_one:
            self.Anim_Export_Index( self.anim_frame )
        if action == action_anim_export_all:
            self.Anim_Export_Cycle()

        # Compressed
        if action == action_comp_export_one:
            self.Comp_Export_Index( self.comp_index )

        # Edit
        if action == action_edit_greyscale:
            self.Edit_Display( "egs" )
        if action == action_edit_invert_h:
            self.Edit_Display( "efx" )
        if action == action_edit_invert_v:
            self.Edit_Display( "efy" )
        if action == action_edit_reset:
            self.Edit_Display( None )

        # Color
        if action == action_pick_color:
            self.state_pickcolor = not self.state_pickcolor
        if action == action_analyse:
            qpixmap = self.Draw_Clip( self.preview_qpixmap )
            qimage = qpixmap.toImage()
            self.SIGNAL_ANALYSE.emit( qimage )

        # Insert
        if action == action_document:
            self.SIGNAL_NEW_DOCUMENT.emit( self.preview_path, clip )
        if action == action_insert_layer:
            self.SIGNAL_INSERT_LAYER.emit( self.preview_path, clip )
        if action == action_insert_ref:
            self.SIGNAL_INSERT_REFERENCE.emit( self.preview_path, clip )

        #endregion

    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ox = ex
        self.oy = ey
        self.ex = ex
        self.ey = ey

        # Cursor
        Cursor_Icon( self )

        # LMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton ):
            if self.state_pickcolor == True:
                self.operation = "color_picker"
                ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
            elif self.state_clip == True:
                self.operation = "clip"
                self.Clip_Node( ex, ey )
            else:
                self.operation = None
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "camera_move"
            self.Camera_Previous()
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "pagination"
            self.Camera_Reset()
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "drag_drop"

        # MMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton ):
            self.operation = "camera_move"
            self.Camera_Previous()

        # RMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = None
            self.Context_Menu( event )
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "camera_scale"
            self.Camera_Previous()
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "pagination"
            self.Camera_Reset()
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "drag_drop"

        # Update
        self.update()
    def mouseMoveEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ex = ex
        self.ey = ey

        # Neutral
        if ( self.operation == "color_picker" and self.anim_timer.isActive() == False ):
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
        if self.operation == "clip":
            self.Clip_Edit( ex, ey, self.clip_node )
        # Camera
        if self.operation == "camera_move":
            self.Camera_Move( ex, ey )
        if self.operation == "camera_scale":
            self.Camera_Scale( ex, ey )
        # Pagination
        if self.operation == "pagination":
            self.Pagination_Stylus( ex, ey )
        # Drag Drop
        if self.operation == "drag_drop":
            clip = { 
                "cstate" : self.state_clip,
                "cl": self.cl,
                "ct": self.ct,
                "cw": self.cw,
                "ch": self.ch,
                }
            Insert_Drag( self, self.preview_path, clip )

        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        self.SIGNAL_MODE.emit( 1 )
    def mouseReleaseEvent( self, event ):
        # Variables
        self.state_press = False
        # Function
        self.Clip_Flip()
        Cursor_Icon( self )
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, False )
        # Variables
        self.operation = None
        self.drop = False
        self.drag = False
        # Update
        self.update()
        self.Camera_Grab()
    # Wheel Event
    def wheelEvent( self, event ):
        delta_y = event.angleDelta().y()
        angle = 5
        if delta_y >= angle:
            self.SIGNAL_INCREMENT.emit( +1 )
        if delta_y <= -angle:
            self.SIGNAL_INCREMENT.emit( -1 )
    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        if event.mimeData().hasImage:
            if ( self.drop == True and self.drag == False ):
                event.setDropAction( Qt.CopyAction )
                mime_data = Drop_Inside( self, event, False )
                self.SIGNAL_DROP.emit( mime_data )
            event.accept()
        else:
            event.ignore()
        self.drop = False
        self.drag = False
        self.update()
    # Widget
    def enterEvent( self, event ):
        self.Camera_Grab()
    def leaveEvent( self, event ):
        pass
    # Painter
    def paintEvent( self, event ):
        # Variables
        ww = self.ww
        hh = self.hh
        w2 = self.w2
        h2 = self.h2
        if ww < hh:
            side = ww
        else:
            side = hh

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Background Hover
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( self.color_alpha ) )
        painter.drawRect( 0, 0, ww, hh )

        # Mask
        painter.setClipRect( QRect( int( 0 ), int( 0 ), int( ww ), int( hh ) ), Qt.ReplaceClip )

        # Render Image
        qpixmap = self.preview_qpixmap
        render = True
        if qpixmap in [ None, False, True ]:
            render = False
        if render == True:
            # Draw Pixmap
            draw = self.Draw_Render( qpixmap )
            painter.drawPixmap( int( self.bl ), int( self.bt ), draw )

            # Clip Area
            if self.state_clip == True:
                # Painter
                painter.setPen( QtCore.Qt.NoPen )
                painter.setBrush( QBrush( self.color_clip ) )
                # Path
                area = QPainterPath()
                area.moveTo( self.bl + 0,                 self.bt + 0 )
                area.lineTo( self.bl + self.bw,           self.bt + 0 )
                area.lineTo( self.bl + self.bw,           self.bt + self.bh )
                area.lineTo( self.bl + 0,                 self.bt + self.bh )
                area.moveTo( self.bl + self.bw * self.cl, self.bt + self.bh * self.ct )
                area.lineTo( self.bl + self.bw * self.cr, self.bt + self.bh * self.ct )
                area.lineTo( self.bl + self.bw * self.cr, self.bt + self.bh * self.cb )
                area.lineTo( self.bl + self.bw * self.cl, self.bt + self.bh * self.cb )
                painter.drawPath( area )
                # Points
                painter.setPen( QPen( self.color_2, 2, Qt.SolidLine ) )
                painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                tri = 15
                poly1 = QPolygon( [
                    QPoint( int( self.bl + self.bw * self.cl ),       int( self.bt + self.bh * self.ct ) ),
                    QPoint( int( self.bl + self.bw * self.cl + tri ), int( self.bt + self.bh * self.ct ) ),
                    QPoint( int( self.bl + self.bw * self.cl ),       int( self.bt + self.bh * self.ct + tri ) ),
                    ] )
                poly2 = QPolygon( [
                    QPoint( int( self.bl + self.bw * self.cr ),       int( self.bt + self.bh * self.ct ) ),
                    QPoint( int( self.bl + self.bw * self.cr ),       int( self.bt + self.bh * self.ct + tri ) ),
                    QPoint( int( self.bl + self.bw * self.cr - tri ), int( self.bt + self.bh * self.ct ) ),
                    ] )
                poly3 = QPolygon( [
                    QPoint( int( self.bl + self.bw * self.cr ),       int( self.bt + self.bh * self.cb ) ),
                    QPoint( int( self.bl + self.bw * self.cr - tri ), int( self.bt + self.bh * self.cb ) ),
                    QPoint( int( self.bl + self.bw * self.cr ),       int( self.bt + self.bh * self.cb - tri ) ),
                    ] )
                poly4 = QPolygon( [
                    QPoint( int( self.bl + self.bw * self.cl ),       int( self.bt + self.bh * self.cb ) ),
                    QPoint( int( self.bl + self.bw * self.cl ),       int( self.bt + self.bh * self.cb - tri ) ),
                    QPoint( int( self.bl + self.bw * self.cl + tri ), int( self.bt + self.bh * self.cb )  ),
                    ] )
                # Polygons
                painter.drawPolygon( poly1 )
                painter.drawPolygon( poly2 )
                painter.drawPolygon( poly3 )
                painter.drawPolygon( poly4 )
        elif ( render == False and self.drop == False ):
            # Dots ( no results )
            painter.setPen( QtCore.Qt.NoPen )
            if qpixmap == None:painter.setBrush( QBrush( self.color_2 ) )
            else:painter.setBrush( QBrush( self.color_1 ) )
            painter.drawEllipse( int( w2 - 0.2 * side ), int( h2 - 0.2 * side ), int( 0.4 * side ), int( 0.4 * side ) )

        # Information
        if self.state_information == True:
            # Variables
            s = 20
            r = 5
            cor = self.color_2
            cor.setAlpha( 200 )
            text = self.Information_Display()

            # Bounding Box
            box = QRect( int( s ), int( hh - s*6 ), int( ww - s*2 ), int( s*5 ) )
            # Highlight
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( cor ) )
            painter.drawRoundedRect( box, r, r )
            # String
            painter.setBrush( QtCore.Qt.NoBrush )
            painter.setPen( QPen( self.color_1, 1, Qt.SolidLine ) )
            qfont = QFont( "Consolas", 10 )
            painter.setFont( qfont )
            painter.drawText( box, Qt.AlignCenter, text )
            # Garbage
            del qfont

        # Display Color Picker
        if self.operation == "color_picker":
            ColorPicker_Render( self, painter, self.ex, self.ey )

        # Drag and Drop Triangle
        if ( self.drop == True and self.drag == False ):
            Painter_Triangle( self, painter, w2, h2, side )

class ImagineBoard_Grid( QWidget ):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_DROP = QtCore.pyqtSignal( list )
    # Grid
    SIGNAL_MODE = QtCore.pyqtSignal( int )
    SIGNAL_INDEX = QtCore.pyqtSignal( int )
    # Menu
    SIGNAL_FUNCTION = QtCore.pyqtSignal( list )
    SIGNAL_PIN_IMAGE = QtCore.pyqtSignal( [ dict, dict ] )
    SIGNAL_FULL_SCREEN = QtCore.pyqtSignal( bool )
    SIGNAL_LOCATION = QtCore.pyqtSignal( str )
    SIGNAL_ANALYSE = QtCore.pyqtSignal( [ QImage ] )
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal( [ str, dict ] )


    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Grid, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 1
        self.hh = 1
        self.w2 = 0.5
        self.h2 = 0.5

        # Event
        self.ox = 0
        self.oy = 0
        self.ex = 0
        self.ey = 0

        # Display
        self.scale_method = Qt.FastTransformation

        # Compact
        self.file_search = []

        # Line
        self.line_index = 0
        self.line_path = [ None ]
        self.line_qpixmap = [ None ]
        # Grid
        self.grid_size = 200
        self.grid_fit = Qt.KeepAspectRatioByExpanding
        self.gix = 0
        self.giy = 0
        self.gmx = 3
        self.gmy = 3
        self.grid_path = [ [ None ] * self.gmx ] * self.gmy
        self.grid_qpixmap = [ [ None ] * self.gmx ] * self.gmy
        self.grid_start = 0
        self.grid_end = self.gmx * self.gmy
        self.glt = 0
        self.glb = 0
        # Thumbnails
        self.tw = 200
        self.th = 200
        # Clip
        self.clip_false = { "cstate" : False, "cl" : 0, "ct" : 0, "cr" : 1, "cb" : 1 }

        # State
        self.state_maximized = False
        self.state_press = False
        self.state_pickcolor = False

        # State
        self.state_maximized = False
        # Interaction
        self.operation = None

        # Colors
        self.color_1 = QColor( "#ffffff" )
        self.color_2 = QColor( "#000000" )
        self.color_alpha = QColor( 0, 0, 0, 50 )

        # Function>>
        self.function_operation = ""

        # Color Picker
        self.pigment_o = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False
    def sizeHint( self ):
        return QtCore.QSize( 5000,5000 )

    # Relay
    def Set_FileSearch( self, file_search ):
        self.file_search = file_search
    def Set_Pigment_O( self, plugin ):
        self.pigment_o = plugin
    def Set_Theme( self, color_1, color_2 ):
        self.color_1 = color_1
        self.color_2 = color_2
    def Set_Size( self, ww, hh, state_maximized ):
        self.ww = ww
        self.hh = hh
        self.w2 = ww * 0.5
        self.h2 = hh * 0.5
        self.state_maximized = state_maximized
        self.resize( ww, hh )
        self.Render_Matrix()
    def Set_Function( self, function_operation ):
        self.function_operation = function_operation
        self.update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()

    # Display
    def Display_Default( self ):
        self.grid_path = [ [ None ] * self.gmx ] * self.gmy
        self.grid_qpixmap = [ [ None ] * self.gmx ] * self.gmy
        self.update()
        self.Camera_Grab()
    def Display_Path( self, line_path, line_index ):
        if self.line_path != line_path:
            self.line_path = line_path
            self.line_qpixmap = [ None ] * len( line_path )
        self.line_index = line_index
        # Update
        self.Render_Matrix()
        self.update()
        self.Camera_Grab()

    # Grid
    def Grid_Size( self, value ):
        self.grid_size = value
        self.Render_Matrix()
        self.update()
        self.Camera_Grab()
    def Grid_Fit( self, boolean ):
        if boolean == False:
            self.grid_fit = Qt.KeepAspectRatioByExpanding
        elif boolean == True:
            self.grid_fit = Qt.KeepAspectRatio
        self.update()
        self.Camera_Grab()
    def Grid_Index( self, ex, ey ):
        # Grid Index
        self.gix = Limit_Range( int( ( ex / self.ww ) * self.gmx ), 0, self.gmx - 1 )
        self.giy = Limit_Range( int( ( ey / self.hh ) * self.gmy ), 0, self.gmy - 1 )
        # Line Index
        line_index = self.grid_start + gi_to_pi( self.gix, self.giy, self.gmx )
        line_limit = len( self.line_path ) - 1
        self.line_index = Limit_Range( line_index, 0, line_limit )
        # Signal
        self.SIGNAL_INDEX.emit( self.line_index )
    def Grid_Increment( self, increment ):
        # Variables
        limit = len( self.line_path ) - 1
        # Calculations
        gix, giy = pi_to_gi( self.line_index, self.gmx, self.gmy )
        if increment < 0:
            delta = self.gmx * increment
            self.line_index = Limit_Range( self.grid_start + gix + delta, 0, limit )
        if increment > 0:
            self.line_index = Limit_Range( self.grid_end + gix, 0, limit )
        # Signal
        self.SIGNAL_INDEX.emit( self.line_index )
        # Update
        self.Render_Matrix()
        self.update()
        self.Camera_Grab()

    # Render
    def Render_Matrix( self ):
        if len( self.line_path ) > 0:
            # Grid Matrix
            gmx = round( self.ww / self.grid_size )
            gmy = round( ( self.hh * 0.8 ) / self.grid_size )
            if gmx <= 0:gmx = 1
            if gmy <= 0:gmy = 1
            # Thumbnails
            self.tw = int( self.ww / gmx )
            self.th = int( self.hh / gmy )

            # Screen Size
            screen = self.gmx * self.gmy
            # Screen Variation
            if ( self.gmx != gmx or self.gmy != gmy ):
                self.gmx = gmx
                self.gmy = gmy
            # Screen Inercia
            if self.line_index < self.grid_start:
                self.grid_start = math.floor( self.line_index / self.gmx ) * self.gmx
            if self.line_index >= self.grid_end:
                self.grid_start = math.ceil( ( self.line_index - screen + 1 ) / self.gmx ) * self.gmx
            # Screen End
            self.grid_end = self.grid_start + screen

            # Clean
            margin = 100
            cs = self.grid_start - margin
            ce = self.grid_end + margin
            for i in range( 0, cs ):
                self.line_qpixmap[i] = None
            for i in range( ce, len( self.line_qpixmap ) ):
                self.line_qpixmap[i] = None

            # Construct
            default = QPixmap()
            archive = Display_Icon( self, "bundle_archive" )
            string = []
            render = []
            for i in range( self.grid_start, self.grid_end ):
                try:
                    path = self.line_path[i]
                    qpixmap = self.line_qpixmap[i]
                    if qpixmap in [ None, False, True ]:
                        qpixmap = QPixmap( path )
                        if qpixmap.isNull() == False:
                            self.line_qpixmap[i] = qpixmap
                        elif zipfile.is_zipfile( path ) == True:
                            archive = zipfile.ZipFile( path, "r" )
                            name_list = archive.namelist()
                            name_list.sort()
                            qpixmap = True
                            for name in name_list:
                                try:
                                    if name.split( "." )[1] in self.file_search:
                                        extract = archive.open( name )
                                        data = extract.read()
                                        qpixmap = QPixmap()
                                        qpixmap.loadFromData( data )
                                        if qpixmap.isNull() == False:
                                            self.line_qpixmap[i] = qpixmap
                                            break
                                except:
                                    qpixmap = True
                        else:
                            qpixmap = True
                except:
                    path = None
                    qpixmap = None
                string.append( path )
                render.append( qpixmap )

            # Lists
            self.grid_path = preview_to_grid( string, self.gmx, self.gmy )
            self.grid_qpixmap = preview_to_grid( render, self.gmx, self.gmy )

    # Pagination
    def Pagination_Reset( self, ey ):
        oz = ey % self.th
        self.glt = ey - oz
        self.glb = self.glt + self.th
    def Pagination_Stylus( self, ey ):
        # Event
        ey = Limit_Range( ey, 0, self.hh )
        # Variables
        margin = 2
        limit = len( self.line_path )
        update = False
        # Logic
        if ey > ( self.glb + margin ):
            self.grid_start = Limit_Range( self.grid_start - self.gmx, 0, limit )
            self.grid_end = Limit_Range( self.grid_end - self.gmx, 0, limit )
            self.Pagination_Reset( ey )
            update = True
        if ey < ( self.glt - margin ):
            self.grid_start = Limit_Range( self.grid_start + self.gmx, 0, limit )
            self.grid_end = Limit_Range( self.grid_end + self.gmx, 0, limit )
            self.Pagination_Reset( ey )
            update = True
        # Update
        if update == True:
            self.Render_Matrix()
            self.update()
            self.Camera_Grab()

    # Camera
    def Camera_Grab( self ):
        try:self.qimage_grab = self.grab().toImage()
        except:pass

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        # Variables
        self.state_press = False
        state_null = self.grid_qpixmap == None
        state_insert = Insert_Check( self )
        string_pickcolor = "Picker"
        if self.pigment_o == None:
            string_pickcolor += " [RGB]"

        # Indexes
        grid_path = self.grid_path[self.giy][self.gix]
        grid_qpixmap = self.grid_qpixmap[self.giy][self.gix]
        # Clip
        clip = { "cstate" : False, "cl": 0, "ct": 0, "cw": 1, "ch": 1 }
        # Cursor
        Cursor_Icon( self )

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )

        # General
        action_function = qmenu.addAction( "Function >> " + self.function_operation )
        action_pin = qmenu.addAction( "Pin Reference" )
        action_full_screen = qmenu.addAction( "Full Screen" )
        qmenu.addSeparator()
        # File
        menu_file = qmenu.addMenu( "File" )
        action_file_location = menu_file.addAction( "File Location" )
        action_file_copy = menu_file.addAction( "Copy Path" )
        # Color
        menu_color = qmenu.addMenu( "Color" )
        action_pick_color = menu_color.addAction( string_pickcolor )
        action_analyse = menu_color.addAction( "Analyse" )
        # Insert
        menu_insert = qmenu.addMenu( "Insert" )
        action_document = menu_insert.addAction( "Document" )
        action_insert_layer = menu_insert.addAction( "Layer" )
        action_insert_ref = menu_insert.addAction( "Reference" )

        # Check Full Screen
        action_full_screen.setCheckable( True )
        action_full_screen.setChecked( self.state_maximized )
        # Check Color
        action_pick_color.setCheckable( True )
        action_pick_color.setChecked( self.state_pickcolor )

        # Disable General
        if state_null == True:
            action_function.setEnabled( False )
            action_pin.setEnabled( False )
        # Disable File
        if state_null == True:
            menu_file.setEnabled( False )
        # Disable Color
        if state_null == True:
            menu_color.setEnabled( False )
        if state_null == True or self.pigment_o == None:
            action_analyse.setEnabled( False )
        # Disable Insert
        if state_null == True:
            menu_insert.setEnabled( False )
        if state_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_ref.setEnabled( False )

        #endregion
        #region Action

        # Mapping
        if grid_qpixmap != None:
            action = qmenu.exec_( self.mapToGlobal( event.pos() ) )

            # General
            if action == action_function:
                self.SIGNAL_FUNCTION.emit( [ grid_path ] )
            if action == action_pin:
                pin = { "bx" : self.w2, "by" : self.h2, "image_path" : grid_path }
                self.SIGNAL_PIN_IMAGE.emit( pin, self.clip_false )
            if action == action_full_screen:
                self.SIGNAL_FULL_SCREEN.emit( not self.state_maximized )

            # File
            if action == action_file_location:
                self.SIGNAL_LOCATION.emit( grid_path )
            if action == action_file_copy:
                Path_Copy( self, grid_path )

            # Color
            if action == action_pick_color:
                self.state_pickcolor = not self.state_pickcolor
            if action == action_analyse:
                qimage = grid_qpixmap.toImage()
                self.SIGNAL_ANALYSE.emit( qimage )

            # Insert
            if action == action_document:
                self.SIGNAL_NEW_DOCUMENT.emit( grid_path, clip )
            if action == action_insert_layer:
                self.SIGNAL_INSERT_LAYER.emit( grid_path, clip )
            if action == action_insert_ref:
                self.SIGNAL_INSERT_REFERENCE.emit( grid_path, clip )

        #endregion
    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ox = ex
        self.oy = ey
        self.ex = ex
        self.ey = ey

        # Functions
        Cursor_Icon( self )
        self.Grid_Index( ex, ey )

        # LMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton ):
            if self.state_pickcolor == True:
                self.operation = "color_picker"
                ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
            else:
                self.operation = "neutral_press"
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "camera_move"
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "pagination"
            self.Pagination_Reset( ey )
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "drag_drop"

        # MMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton ):
            self.operation = "camera_move"

        # RMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = None
            self.Context_Menu( event )
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "camera_scale"
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "pagination"
            self.Pagination_Reset( ey )
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "drag_drop"

        # Update
        self.update()
    def mouseMoveEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ex = ex
        self.ey = ey

        # Neutral
        if self.operation == "neutral_press":
            self.Grid_Index( ex, ey )
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
        # Camera
        if self.operation == "camera_move":
            pass
        if self.operation == "camera_scale":
            pass
        # Pagination
        if self.operation == "pagination":
            self.Pagination_Stylus( ey )
        # Drag Drop
        if self.operation == "drag_drop":
            path = self.grid_path[self.giy][self.gix]
            clip = { "cstate" : False, "cl": 0, "ct": 0, "cw": 1, "ch": 1 }
            Insert_Drag( self, path, clip )

        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        self.SIGNAL_MODE.emit( 0 )
    def mouseReleaseEvent( self, event ):
        # Variables
        self.state_press = False
        # Function
        Cursor_Icon( self )
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, False )
        # Variables
        self.operation = None
        # Update
        self.update()
        self.Camera_Grab()
    # Wheel Event
    def wheelEvent( self, event ):
        delta_y = event.angleDelta().y()
        angle = 5
        if delta_y >= angle:
            self.Grid_Increment( +1 )
        if delta_y <= -angle:
            self.Grid_Increment( -1 )
    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        if event.mimeData().hasImage:
            if ( self.drop == True and self.drag == False ):
                event.setDropAction( Qt.CopyAction )
                mime_data = Drop_Inside( self, event, False )
                self.SIGNAL_DROP.emit( mime_data )
            event.accept()
        else:
            event.ignore()
        self.drop = False
        self.drag = False
        self.update()
    # Widget
    def enterEvent( self, event ):
        self.Camera_Grab()
    def leaveEvent( self, event ):
        self.update()
    # Painter
    def paintEvent( self, event ):
        # Variables
        ww = self.ww
        hh = self.hh
        w2 = self.w2
        h2 = self.h2
        if ww < hh:
            side = ww
        else:
            side = hh
        if self.tw < self.th:
            thumb = self.tw
        else:
            thumb = self.th

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Background Hover
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( self.color_alpha ) )
        painter.drawRect( 0, 0, ww, hh )

        # Draw QPixmaps
        for y in range( 0, len( self.grid_qpixmap ) ):
            row = self.grid_qpixmap[y]
            for x in range( 0, len( row ) ):
                # Clip Mask
                px = self.tw * x
                py = self.th * y
                thumbnail = QRect( int( px ), int( py ), int( self.tw ), int( self.th ) )
                painter.setClipRect( thumbnail, Qt.ReplaceClip )

                # Render
                qpixmap = self.grid_qpixmap[y][x]
                broken = Display_Icon( self, "broken-preset" )
                render = True
                if qpixmap in [ None, False, True ]:
                    render = False
                if render == True:
                    try:draw = qpixmap.scaled( int( self.tw + 1 ), int( self.th + 1 ), self.grid_fit, self.scale_method )
                    except:draw = broken.scaled( int( self.tw + 1 ), int( self.th + 1 ), self.grid_fit, self.scale_method )
                    rw = draw.width()
                    rh = draw.height()
                    ox = ( self.tw - rw ) * 0.5
                    oy = ( self.th - rh ) * 0.5
                    painter.drawPixmap( int( px + ox ), int( py + oy ), draw )
                else:
                    painter.setPen( QtCore.Qt.NoPen )
                    if qpixmap == None or self.drop == True:
                        painter.setBrush( QBrush( self.color_2 ) )
                    else:
                        painter.setBrush( QBrush( self.color_1 ) )
                    ox = ( self.tw * 0.5 ) - ( 0.3 * thumb )
                    oy = ( self.th * 0.5 ) - ( 0.3 * thumb )
                    painter.drawEllipse( int( px + ox ), int( py + oy ), int( 0.6 * thumb ), int( 0.6 * thumb ) )

        # Clean Mask
        painter.setClipping( False )

        # Display Color Picker
        if self.operation == "color_picker":
            ColorPicker_Render( self, painter, self.ex, self.ey )

        # Drag and Drop Triangle
        if ( self.drop == True and self.drag == False ):
            Painter_Triangle( self, painter, w2, h2, side )

class ImagineBoard_Reference( QWidget ):
    # General
    SIGNAL_DRAG = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_DROP = QtCore.pyqtSignal( list )
    # Reference
    SIGNAL_PIN_IMAGE = QtCore.pyqtSignal( [ dict, dict ] )
    SIGNAL_PIN_LABEL = QtCore.pyqtSignal( dict )
    SIGNAL_PIN_SAVE = QtCore.pyqtSignal( [ QPixmap ] )
    SIGNAL_BOARD_SAVE = QtCore.pyqtSignal( list )
    SIGNAL_CAMERA = QtCore.pyqtSignal( [ list, float, int ] )
    # Menu
    SIGNAL_LOCKED = QtCore.pyqtSignal( bool )
    SIGNAL_REFRESH = QtCore.pyqtSignal()
    SIGNAL_FULL_SCREEN = QtCore.pyqtSignal( bool )
    SIGNAL_LOCATION = QtCore.pyqtSignal( str )
    SIGNAL_ANALYSE = QtCore.pyqtSignal( [ QImage ] )
    SIGNAL_NEW_DOCUMENT = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_LAYER = QtCore.pyqtSignal( [ str, dict ] )
    SIGNAL_INSERT_REFERENCE = QtCore.pyqtSignal( [ str, dict ] )
    # UI
    SIGNAL_PB_VALUE = QtCore.pyqtSignal( int )
    SIGNAL_PB_MAX = QtCore.pyqtSignal( int )
    SIGNAL_PACK_STOP = QtCore.pyqtSignal( bool )
    SIGNAL_LABEL_PANEL = QtCore.pyqtSignal( bool )
    SIGNAL_LABEL_INFO = QtCore.pyqtSignal( dict )


    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Reference, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 1
        self.hh = 1
        self.w2 = 0.5
        self.h2 = 0.5

        # Event
        self.ox = 0
        self.oy = 0
        self.ex = 0
        self.ey = 0

        # State
        self.state_inside = False
        self.state_locked = False
        self.state_maximized = False
        self.state_press = False
        self.state_select = False
        self.state_pack = False
        self.state_pickcolor = False
        self.state_label = False
        # Interaction
        self.operation = None

        # Camera
        self.cn = [
            0.000, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009,
            0.010, 0.011, 0.012, 0.013, 0.014, 0.015, 0.016, 0.017, 0.018, 0.019,
            0.020, 0.021, 0.022, 0.023, 0.024, 0.025, 0.026, 0.027, 0.028, 0.029,
            0.030, 0.031, 0.032, 0.033, 0.034, 0.035, 0.036, 0.037, 0.038, 0.039,
            0.040, 0.041, 0.042, 0.043, 0.044, 0.045, 0.046, 0.047, 0.048, 0.049,
            0.050, 0.051, 0.052, 0.053, 0.054, 0.055, 0.056, 0.057, 0.058, 0.059,
            0.060, 0.061, 0.062, 0.063, 0.064, 0.065, 0.066, 0.067, 0.068, 0.069,
            0.070, 0.071, 0.072, 0.073, 0.074, 0.075, 0.076, 0.077, 0.078, 0.079,
            0.080, 0.081, 0.082, 0.083, 0.084, 0.085, 0.086, 0.087, 0.088, 0.089,
            0.090, 0.091, 0.092, 0.093, 0.094, 0.095, 0.096, 0.097, 0.098, 0.099,

            0.10, 0.10429, 0.10869, 0.11316, 0.11771, 0.12231, 0.12697, 0.13169, 0.13645, 0.14126, 0.14611, 0.1501, 0.15596, 0.16093, 0.16598, 0.17105, 0.17616, 0.18132, 0.18651, 0.19176, 0.19704, 
            0.20237, 0.20773, 0.21314, 0.2186, 0.22409, 0.22964, 0.23521, 0.24086, 0.24652, 0.25226, 0.25801, 0.26384, 0.26969, 0.27561, 0.28156, 0.28759, 0.29364, 0.29976, 
            0.30592, 0.31214, 0.31842, 0.32475, 0.33114, 0.33757, 0.34409, 0.35064, 0.35729, 0.36395, 0.37074, 0.37753, 0.38446, 0.3914, 0.39846, 
            0.40556, 0.41276, 0.42003, 0.42738, 0.43482, 0.44233, 0.44996, 0.45764, 0.46547, 0.4733, 0.48138, 0.48945, 0.49772, 
            0.50601, 0.51454, 0.52307, 0.53186, 0.54066, 0.54974, 0.55885, 0.56825, 0.5777, 0.58743, 0.59728, 
            0.60739, 0.61769, 0.6282, 0.63904, 0.65, 0.66145, 0.67309, 0.6851, 0.69755,
            0.7103, 0.72363, 0.7375, 0.75188, 0.76691, 0.78293, 0.79985, 
            0.8179, 0.83738, 0.85876, 0.88275, 
            0.91046, 0.94563, 

            1.0000, 1.0681, 1.1362, 1.2043, 1.2724, 1.3441, 1.4158, 1.5119, 1.6081, 1.7042, 1.8004, 1.9181,
            2.0359, 2.1708, 2.3058, 2.4514, 2.5970, 2.7812, 2.9654, 
            3.1517, 3.3381, 3.5795, 3.8209, 
            4.0623, 4.3038, 4.6025, 4.9012,
            5.2029, 5.5047, 5.8573,
            6.2099, 6.5693, 6.9288, 
            7.3262, 7.7237, 
            8.1328, 8.5419, 8.9714,
            9.4011, 9.84855,
            10.296, 10.7470,
            11.198, 11.6725,
            12.147, 12.6215,
            13.096, 13.5770,
            14.058, 14.5490,
            15.040, 15.5305,
            16.021, 16.5150,
            17.009, 17.5075,
            18.006, 18.5045,
            19.003, 19.5015,

            20.0, 20.5,
            21.0, 21.5,
            22.0, 22.5,
            23.0, 23.5,
            24.0, 24.5,
            25.0, 25.5,
            26.0, 26.5,
            27.0, 27.5,
            28.0, 28.5,
            29.0, 29.5,
            30.0, 30.5,
            31.0, 31.5,
            32.0, 32.5,
            33.0, 33.5,
            34.0, 34.5,
            35.0, 35.5,
            36.0, 36.5,
            37.0, 37.5,
            38.0, 38.5,
            39.0, 39.5,
            40.0, 40.5,
            41.0, 41.5,
            42.0, 42.5,
            43.0, 43.5,
            44.0, 44.5,
            45.0, 45.5,
            46.0, 46.5,
            47.0, 47.5,
            48.0, 48.5,
            49.0, 49.5,

            50.0,
            51.0,
            52.0,
            53.0,
            54.0,
            55.0,
            56.0,
            57.0,
            58.0,
            59.0,
            60.0,
            61.0,
            62.0,
            63.0,
            64.0,
            65.0,
            66.0,
            67.0,
            68.0,
            69.0,
            70.0,
            71.0,
            72.0,
            73.0,
            74.0,
            75.0,
            76.0,
            77.0,
            78.0,
            79.0,
            80.0,
            81.0,
            82.0,
            83.0,
            84.0,
            85.0,
            86.0,
            87.0,
            88.0,
            89.0,
            90.0,
            91.0,
            92.0,
            93.0,
            94.0,
            95.0,
            96.0,
            97.0,
            98.0,
            99.0,
            100.0,
            ]
        self.ci = self.cn.index( 1 )
        self.cz = self.cn[self.ci] # Camera Zoom

        # Display
        self.scale_method = Qt.FastTransformation

        # Files
        self.file_extension = []
        self.file_path = ""

        # Pin
        self.pin_list = []
        self.pin_previous = []
        self.pin_index = None
        self.pin_path = None
        self.pin_basename = None
        self.pin_node = None
        self.pin_count = 0
        self.pin_preview = None

        # Limit
        self.limit_x = []
        self.limit_y = []

        # Selection
        self.select_box = False
        self.select_count = 0

        # Pack
        self.packing_process = False

        # Board (surface)
        self.board_l = 0
        self.board_r = 0
        self.board_t = 0
        self.board_b = 0
        self.board_w = 0
        self.board_h = 0

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False

        # Colors
        self.color_1 = QColor( "#ffffff" )
        self.color_2 = QColor( "#000000" )
        self.color_shade = QColor( 0, 0, 0, 30 )
        self.color_alpha = QColor( 0, 0, 0, 50 )
        self.color_backdrop = QColor( 0, 0, 0, 100 )
        self.color_blue = QColor( "#3daee9" )

        # Color Picker
        self.pigment_o = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # Function>>
        self.function_operation = ""

        # Clip
        self.clip_false = { "cstate" : False, "cl" : 0, "ct" : 0, "cr" : 1, "cb" : 1 }

        # Debug Packer Points
        # self.p = []
    def sizeHint( self ):
        return QtCore.QSize( 5000,5000 )

    # Relay
    def Set_File_Extension( self, file_extension ):
        self.file_extension = file_extension
    def Set_Pigment_O( self, boolean ):
        self.pigment_o = boolean
    def Set_Theme( self, color_1, color_2 ):
        self.color_1 = color_1
        self.color_2 = color_2
    def Set_Size( self, ww, hh, state_maximized ):
        if self.state_pack == False:
            # Count
            self.pin_count = len( self.pin_list )
            # Transform Correction
            dx = ( ww - self.ww ) * 0.5
            dy = ( hh - self.hh ) * 0.5
            for i in range( 0, self.pin_count ):
                self.Move_Transform( self.pin_list, i, dx, dy )
            # Widget
            self.ww = ww
            self.hh = hh
            self.w2 = ww * 0.5
            self.h2 = hh * 0.5
            # Maximized State
            self.state_maximized = state_maximized
            # Board
            self.Board_Limit( "DRAW" )
            # Update
            self.resize( ww, hh )
    def Set_Camera( self, position, zoom ):
        # Position
        self.Pin_Previous()
        board_l, board_r, board_t, board_b, board_w, board_h = self.Board_Limit( "PIN" )
        cx = self.w2
        cy = self.h2
        px = board_l + board_w * position[0]
        py = board_t + board_h * position[1]
        dx = cx - px
        dy = cy - py
        for i in range( 0, self.pin_count ):
            self.Move_Transform( self.pin_previous, i, dx, dy )

        # Zoom
        index = 0
        for i in range( 0, len( self.cn ) ):
            if ( zoom >= self.cn[i] ) and ( zoom < self.cn[i+1] ):
                index = i
                break
        self.ci = index
        self.cz = self.cn[index]

        # Update
        self.Board_Update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()
    def Set_Stop_Cycle( self ):
        try:self.worker_packer.STOP()
        except:pass
    def Set_File_Path( self, path ):
        if path not in [ "", ".", None]:
            name = ( os.path.basename( path ) ).split( "." )[0]
            file_path = f" [ { name } ]"
        else:
            file_path = ""
        self.file_path = file_path
        self.update()
    def Set_Function( self, function_operation ):
        self.function_operation = function_operation
        self.update()
    def Set_Locked( self, state_locked ):
        self.state_locked = state_locked
        self.update()

    # Points
    def Point_Deltas( self, ex, ey ):
        try:
            dx = ( ex - self.ox ) / self.cz
            dy = ( ey - self.oy ) / self.cz
        except:
            dx = 0
            dy = 0
        return dx, dy
    def Point_Location( self, ex, ey ):
        try:
            px = self.w2 + ( ex - self.w2 ) / self.cz
            py = self.h2 + ( ey - self.h2 ) / self.cz
        except:
            px = self.w2
            py = self.h2
        return px, py

    # Pin
    def Pin_Insert( self, pin ):
        # Pin
        self.pin_list.append( pin )
        self.pin_count = len( self.pin_list )
        # Update
        self.update()
    def Pin_URL( self, bx, by ):
        url, ok = QInputDialog.getText( self, "Insert Pin", "URL", QLineEdit.Normal, "" )
        if ok and url != "":
            pin = { "bx" : bx, "by" : by, "image_path" : url }
            self.SIGNAL_PIN_IMAGE.emit( pin, self.clip_false )
    def Pin_Update( self ):
        for i in range( 0, self.pin_count ):
            self.pin_list[i]["index"] = i
    def Pin_Index( self, ex, ey ):
        # Variables
        index = None
        self.pin_index = None
        self.pin_path = None
        self.pin_basename = None
        self.pin_node = None
        self.pin_count = len( self.pin_list )

        # Index
        for i in range( self.pin_count - 1, -1, -1 ):
            dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( i )
            check = ( ex >= dl ) and ( ex <= dr ) and ( ey >= dt ) and ( ey <= db )
            if check == True:
                index = i
                break

        # Variables
        if index != None:
            # Pin List
            save = self.pin_list[ index ]
            self.pin_list.pop( index )
            self.pin_list.append( save )

            # Pin Previous
            save = self.pin_previous[ index ]
            self.pin_previous.pop( index )
            self.pin_previous.append( save )

            # Variables
            pin_index = self.pin_count - 1
            self.pin_index = pin_index
            self.pin_node = self.Pin_Node( self.pin_index )
            if self.pin_list[pin_index]["tipo"] == "image":
                self.pin_path = self.pin_list[pin_index]["path"]
                try:self.pin_basename = str( os.path.basename( self.pin_path ) ) # local
                except:self.pin_basename = None # web
            else:
                self.pin_path = None
                self.pin_basename = None
    def Pin_Active( self, index ):
        for i in range( 0, self.pin_count ):
            self.pin_list[i]["active"] = False
        if index != None:
            self.pin_list[index]["active"] = True
    def Pin_Node( self, index ):
        # None = Board, 0 = No Node, 1-9 = Node
        if index == None:
            pin_node = None
        else:
            # Variables
            sca = 50
            rot = 75

            # Read
            img = self.pin_list[index]["tipo"] == "image"

            # Read
            dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( index )

            # List
            nodes = []
            nodes.append( [ Trig_2D_Points_Distance( dl, dt, self.ox, self.oy ), 1 ] ) # top left
            nodes.append( [ Trig_2D_Points_Distance( dr, dt, self.ox, self.oy ), 3 ] ) # top right
            nodes.append( [ Trig_2D_Points_Distance( dl, db, self.ox, self.oy ), 7 ] ) # bot left
            nodes.append( [ Trig_2D_Points_Distance( dr, db, self.ox, self.oy ), 9 ] ) # bot right
            if ( dw >= sca or dh >= sca ):
                nodes.append( [ Trig_2D_Points_Distance( dx, dt, self.ox, self.oy ), 2 ] ) # top
                nodes.append( [ Trig_2D_Points_Distance( dl, dy, self.ox, self.oy ), 4 ] ) # mid left
                nodes.append( [ Trig_2D_Points_Distance( dr, dy, self.ox, self.oy ), 6 ] ) # mid right
                nodes.append( [ Trig_2D_Points_Distance( dx, db, self.ox, self.oy ), 8 ] ) # bot
            if ( img ==  True and ( dw >= rot or dh >= rot ) ):
                nodes.append( [ Trig_2D_Points_Distance( dx, dy, self.ox, self.oy ) * 2, 5 ] ) # mid
            nodes.sort()

            # Index
            pin_node = 0
            if nodes[0][0] <= 20:
                pin_node = nodes[0][1]

        # Return
        return pin_node
    def Pin_Limits( self ):
        # Variables
        set_limit_x = list()
        set_limit_y = list()
        active_select = False
        if self.pin_index != None:
            active_select = self.pin_list[self.pin_index]["select"]
        # Collect values
        for i in range( 0, self.pin_count ):
            pin_select = self.pin_list[i]["select"]
            check_active = self.pin_index != i and active_select == False
            check_select = self.pin_index != i and active_select == True and pin_select == False
            if ( check_active == True or check_select == True ):
                set_limit_x.append( self.pin_list[i]["bl"] )
                set_limit_x.append( self.pin_list[i]["br"] )
                set_limit_y.append( self.pin_list[i]["bt"] )
                set_limit_y.append( self.pin_list[i]["bb"] )
        # Update Limits
        self.limit_x = list( set( set_limit_x ) )
        self.limit_y = list( set( set_limit_y ) )
    def Pin_Previous( self ):
        if self.pin_count > 0:
            pin_previous = []
            for i in range( 0, self.pin_count ):
                dicta = {
                    # Transform
                    "trz" : self.pin_list[i]["trz"],
                    "tsk" : self.pin_list[i]["tsk"],
                    "tsw" : self.pin_list[i]["tsw"],
                    "tsh" : self.pin_list[i]["tsh"],
                    # Bounding Box
                    "bx" : self.pin_list[i]["bx"],
                    "by" : self.pin_list[i]["by"],
                    "bl" : self.pin_list[i]["bl"],
                    "br" : self.pin_list[i]["br"],
                    "bt" : self.pin_list[i]["bt"],
                    "bb" : self.pin_list[i]["bb"],
                    "bw" : self.pin_list[i]["bw"],
                    "bh" : self.pin_list[i]["bh"],
                    }
                pin_previous.append( dicta )
            self.pin_previous = pin_previous
    def Pin_Preview( self, index ):
        # Logic
        if ( index == None or self.pin_preview != None ):
            self.pin_preview = None
        else:
            # Read
            trz = self.pin_list[index]["trz"]
            egs = self.pin_list[index]["egs"]
            efx = self.pin_list[index]["efx"]
            efy = self.pin_list[index]["efy"]
            qpixmap = self.pin_list[index]["qpixmap"]
            # Pixmap
            if qpixmap != None:
                draw = self.Edit_QPixmap( qpixmap, egs, efx, efy )
                draw = self.Rotate_QPixmap( draw, trz )
                self.pin_preview = draw
            else:
                self.pin_preview = None
        # Update
        self.update()
    def Pin_Draw_Box( self, index ):
        if index != None:
            # Read
            bx = self.pin_list[index]["bx"]
            by = self.pin_list[index]["by"]
            bl = self.pin_list[index]["bl"]
            br = self.pin_list[index]["br"]
            bt = self.pin_list[index]["bt"]
            bb = self.pin_list[index]["bb"]
            bw = self.pin_list[index]["bw"]
            bh = self.pin_list[index]["bh"]
            # Transform
            dx = self.w2 + ( bx - self.w2 ) * self.cz
            dy = self.h2 + ( by - self.h2 ) * self.cz
            dl = self.w2 + ( bl - self.w2 ) * self.cz
            dr = self.w2 + ( br - self.w2 ) * self.cz
            dt = self.h2 + ( bt - self.h2 ) * self.cz
            db = self.h2 + ( bb - self.h2 ) * self.cz
            dw = dr - dl
            dh = db - dt
            # Return
            return dx, dy, dl, dr, dt, db, dw, dh
    def Pin_Draw_QPixmap( self, lista, index ):
        # Variables
        tipo = lista[index]["tipo"]
        render = lista[index]["render"]
        if ( index != None and tipo == "image" and render == True ):
            # Read
            trz = lista[index]["trz"]
            tsw = lista[index]["tsw"]
            tsh = lista[index]["tsh"]
            egs = lista[index]["egs"]
            efx = lista[index]["efx"]
            efy = lista[index]["efy"]
            qpixmap = lista[index]["qpixmap"]
            # Pixmap
            if qpixmap != None:
                draw = self.Edit_QPixmap( qpixmap, egs, efx, efy )
                draw = self.Scale_QPixmap( draw, tsw, tsh )
                draw = self.Rotate_QPixmap( draw, trz )
                lista[index]["draw"] = draw
                del draw
            else:
                lista[index]["qpixmap"] = None
                lista[index]["draw"] = None
            # Garbage
            del qpixmap

    # QPixmap
    def Edit_QPixmap( self, source, egs, efx, efy ):
        source = source.toImage()
        if egs == True:
            source = source.convertToFormat( QImage.Format_Grayscale8 )
        if ( efx == True or efy == True ):
            source = source.mirrored( efx, efy )
        draw = QPixmap().fromImage( source )
        return draw
    def Scale_QPixmap( self, source, width, height ):
        w = width * self.cz
        h = height * self.cz
        if( self.state_inside == False and self.scale_method == True ):
            draw = source.scaled( int( w ), int( h ), Qt.IgnoreAspectRatio, Qt.SmoothTransformation )
        else:
            draw = source.scaled( int( w ), int( h ), Qt.IgnoreAspectRatio, Qt.FastTransformation )
        draw = draw.copy( int( w ), int( h ), int( w ), int( h ) ) # Cut the error
        return draw
    def Rotate_QPixmap( self, source, angle ):
        if angle == 0:
            draw = source
        else:
            rotation = QTransform().rotate( angle, Qt.ZAxis )
            draw = source.transformed( rotation )
        return draw

    # Label ( Text )
    def Label_Insert( self, event ):
        pos = event.pos()
        bx, by = self.Point_Location( pos.x(), pos.y() )
        pin = {
            "bx" : bx,
            "by" : by,
            "cstate" : None,
            }
        self.SIGNAL_PIN_LABEL.emit( pin )
    def Label_List( self ):
        lista = []
        for i in range( 0, self.pin_count ):
            if self.pin_list[i]["select"] == True:
                lista.append( i )
        return lista
    def Label_Panel( self, index ):
        info = {
            "text"   : self.pin_list[index]["text"],
            "font"   : self.pin_list[index]["font"],
            "letter" : self.pin_list[index]["letter"],
            "pen"    : self.pin_list[index]["pen"],
            "bg"     : self.pin_list[index]["bg"],
            }
        self.SIGNAL_LABEL_INFO.emit( info )
    # Get Label
    def Get_Label_Infomation( self ):
        lista = self.Label_List()
        if len( lista ) > 0:
            index = lista[-1]
            info = {
                "text"   : self.pin_list[index]["text"],
                "font"   : self.pin_list[index]["font"],
                "letter" : self.pin_list[index]["letter"],
                "pen"    : self.pin_list[index]["pen"],
                "bg"     : self.pin_list[index]["bg"],
                }
        else:
            info = None
        return info
    # Set Label
    def Set_Label_Text( self, text ):
        lista = self.Label_List()
        for i in lista:
            self.pin_list[i]["text"] = text
        self.update()
    def Set_Label_Font( self, font ):
        lista = self.Label_List()
        for i in lista:
            self.pin_list[i]["font"] = font
        self.update()
    def Set_Label_Letter( self, letter ):
        lista = self.Label_List()
        for i in lista:
            self.pin_list[i]["letter"] = letter
        self.update()
    def Set_Label_Pen( self, pen ):
        lista = self.Label_List()
        for i in lista:
            self.pin_list[i]["pen"] = pen
        self.update()
    def Set_Label_Bg( self, bg ):
        lista = self.Label_List()
        for i in lista:
            self.pin_list[i]["bg"] = bg
        self.update()

    # Pin Transforms
    def Pin_Transform( self, ex, ey, node ):
        # Check
        move = node == 0
        scale = node in [ 1, 2, 3, 4, 6, 7, 8, 9 ]
        rotate = node == 5
        # Transformation
        if move == True:
            dx, dy = self.Point_Deltas( ex, ey )
            self.Move_Pin( dx, dy, True )
        if scale == True:
            if self.pin_list[self.pin_index]["tipo"] == "image":
                px, py = self.Point_Location( ex, ey )
                self.Scale_Pin( px, py, node )
            if self.pin_list[self.pin_index]["tipo"] == "label":
                dx, dy = self.Point_Deltas( ex, ey )
                self.Scale_Label( self.pin_previous, self.pin_index, node, dx, dy )
        if rotate == True:
            if self.pin_list[self.pin_index]["tipo"] == "image":
                dx = ( ex - self.ox )
                self.Rotate_Pin( dx )

    # Move
    def Move_Pin( self, dx, dy, boolean ):
        # Variabels
        sx = 0
        sy = 0
        snap_dist = 10 / self.cz

        # Preview Move
        n_bx = self.pin_previous[self.pin_index]["bx"] + dx
        n_by = self.pin_previous[self.pin_index]["by"] + dy
        n_bl = self.pin_previous[self.pin_index]["bl"] + dx
        n_br = self.pin_previous[self.pin_index]["br"] + dx
        n_bt = self.pin_previous[self.pin_index]["bt"] + dy
        n_bb = self.pin_previous[self.pin_index]["bb"] + dy

        # Snap
        if boolean == True:
            for j in range( 0, len( self.limit_x ) ):
                xj = self.limit_x[j]
                ll = xj - snap_dist
                lr = xj + snap_dist
                dl = abs( xj - n_bl )
                dr = abs( xj - n_br )
                cl = ( n_bl >= ll and n_bl <= lr )
                cr = ( n_br >= ll and n_br <= lr )
                if cl == True and dl < dr:
                    sx = xj - n_bl
                    break
                elif cr == True and dr < dl:
                    sx = xj - n_br
                    break
            for j in range( 0, len( self.limit_y ) ):
                yj = self.limit_y[j]
                lt = yj - snap_dist
                lb = yj + snap_dist
                dt = abs( yj - n_bt )
                db = abs( yj - n_bb )
                ct = ( n_bt >= lt and n_bt <= lb )
                cb = ( n_bb >= lt and n_bb <= lb )
                if ct == True and dt < db:
                    sy = yj - n_bt
                    break
                elif cb == True and db < dt:
                    sy = yj - n_bb
                    break

        # Move Pin Index
        self.Move_Transform( self.pin_previous, self.pin_index, dx + sx, dy + sy )

        # Snap and Selection
        if ( self.pin_list[self.pin_index]["select"] == True and self.select_count > 0 ):
            for i in range( 0, self.pin_count ):
                if self.pin_list[i]["select"] == True:
                    self.Move_Transform( self.pin_previous, i, dx + sx, dy + sy )
    def Move_Transform( self, previous, index, dx, dy ):
        self.pin_list[index]["bx"] = previous[index]["bx"] + dx
        self.pin_list[index]["by"] = previous[index]["by"] + dy
        self.pin_list[index]["bl"] = previous[index]["bl"] + dx
        self.pin_list[index]["br"] = previous[index]["br"] + dx
        self.pin_list[index]["bt"] = previous[index]["bt"] + dy
        self.pin_list[index]["bb"] = previous[index]["bb"] + dy
    def Move_Point( self, lista, index, px, py ):
        # Read
        bw = lista[index]["bw"]
        bh = lista[index]["bh"]
        # Write
        lista[index]["bx"] = px + bw * 0.5
        lista[index]["by"] = py + bh * 0.5
        lista[index]["bl"] = px
        lista[index]["br"] = px + bw
        lista[index]["bt"] = py
        lista[index]["bb"] = py + bh

    # Scale
    def Scale_Pin( self, px, py, node ):
        # Variables
        snap_dist = 20 / self.cz

        # Read
        tipo = self.pin_list[self.pin_index]["tipo"]
        bx = self.pin_previous[self.pin_index]["bx"]
        by = self.pin_previous[self.pin_index]["by"]
        bl = self.pin_previous[self.pin_index]["bl"]
        br = self.pin_previous[self.pin_index]["br"]
        bt = self.pin_previous[self.pin_index]["bt"]
        bb = self.pin_previous[self.pin_index]["bb"]

        # Point Neutral
        if node == 1:
            nx = br
            ny = bb
            ax = bl
            ay = bt
        if node == 2:
            nx = bx
            ny = bb
            ax = bx
            ay = bt
        if node == 3:
            nx = bl
            ny = bb
            ax = br
            ay = bt
        if node == 4:
            nx = br
            ny = by
            ax = bl
            ay = by
        if node == 6:
            nx = bl
            ny = by
            ax = br
            ay = by
        if node == 7:
            nx = br
            ny = bt
            ax = bl
            ay = bb
        if node == 8:
            nx = bx
            ny = bt
            ax = bx
            ay = bb
        if node == 9:
            nx = bl
            ny = bt
            ax = br
            ay = bb

        # Line intersection
        dist = []
        for x in range( 0, len( self.limit_x ) ):
            try:
                lx = self.limit_x[x]
                ix, iy = Trig_2D_Points_Lines_Intersection( nx, ny, ax, ay, lx, 0, lx, 1 )
                di = Trig_2D_Points_Distance( px, py, ix, iy )
                dist.append( [ di, ix, iy ] )
            except:
                pass
        for y in range( 0, len( self.limit_y ) ):
            try:
                ly = self.limit_y[y]
                ix, iy = Trig_2D_Points_Lines_Intersection( nx, ny, ax, ay, 0, ly, 1, ly )
                di = Trig_2D_Points_Distance( px, py, ix, iy )
                dist.append( [ di, ix, iy ] )
            except:
                pass
        # Factor
        if len( dist ) > 0:
            dist.sort()
            di = dist[0][0]
            ix = dist[0][1]
            iy = dist[0][2]
            if di <= snap_dist:
                px = ix
                py = iy

        # Delta Scale
        sx = px - nx
        sy = py - ny

        # Scale
        self.Scale_Transform( self.pin_previous, self.pin_index, self.pin_node, nx, ny, sx, sy )
        self.Pin_Draw_QPixmap( self.pin_list, self.pin_index )

        # Snap and Selection
        if self.select_count > 0:
            for i in range( 0, self.pin_count ):
                if self.pin_list[i]["select"] == True:
                    # Read
                    n_bx = self.pin_previous[i]["bx"]
                    n_by = self.pin_previous[i]["by"]
                    n_bl = self.pin_previous[i]["bl"]
                    n_br = self.pin_previous[i]["br"]
                    n_bt = self.pin_previous[i]["bt"]
                    n_bb = self.pin_previous[i]["bb"]

                    # Points
                    if node == 1:
                        n_nx = n_br
                        n_ny = n_bb
                        n_ax = n_bl
                        n_ay = n_bt
                    if node == 2:
                        n_nx = n_bx
                        n_ny = n_bb
                        n_ax = n_bx
                        n_ay = n_bt
                    if node == 3:
                        n_nx = n_bl
                        n_ny = n_bb
                        n_ax = n_br
                        n_ay = n_bt
                    if node == 4:
                        n_nx = n_br
                        n_ny = n_by
                        n_ax = n_bl
                        n_ay = n_by
                    if node == 6:
                        n_nx = n_bl
                        n_ny = n_by
                        n_ax = n_br
                        n_ay = n_by
                    if node == 7:
                        n_nx = n_br
                        n_ny = n_bt
                        n_ax = n_bl
                        n_ay = n_bb
                    if node == 8:
                        n_nx = n_bx
                        n_ny = n_bt
                        n_ax = n_bx
                        n_ay = n_bb
                    if node == 9:
                        n_nx = n_bl
                        n_ny = n_bt
                        n_ax = n_br
                        n_ay = n_bb

                    # Scale
                    self.Scale_Transform( self.pin_previous, i, node, n_nx, n_ny, sx, sy )
                    self.Pin_Draw_QPixmap( self.pin_list, i )
    def Scale_Transform( self, previous, index, node, nx, ny, sx, sy ):
        # nx, ny = neutral point
        # sx, sy = scaling point

        # Read
        trz = previous[index]["trz"]
        tsk = previous[index]["tsk"]
        tsw = previous[index]["tsw"]
        tsh = previous[index]["tsh"]
        bx = previous[index]["bx"]
        by = previous[index]["by"]
        bl = previous[index]["bl"]
        br = previous[index]["br"]
        bt = previous[index]["bt"]
        bb = previous[index]["bb"]
        bw = previous[index]["bw"]
        bh = previous[index]["bh"]

        # Factor
        if node in ( 1, 3, 7, 9 ):
            d_delta = Trig_2D_Points_Distance( 0, 0, sx, sy )
            d_box = Trig_2D_Points_Distance( 0, 0, bw, bh )
        if node in ( 2, 8 ):
            d_delta = Trig_2D_Points_Distance( 0, 0, 0, sy )
            d_box = Trig_2D_Points_Distance( 0, 0, 0, bh )
        if node in ( 4, 6 ):
            d_delta = Trig_2D_Points_Distance( 0, 0, sx, 0 )
            d_box = Trig_2D_Points_Distance( 0, 0, bw, 0 )
        factor = d_delta / d_box
        # Dimension with Factor
        fw = bw * factor
        fh = bh * factor

        # Write
        if ( fw != 0 and fh != 0 ):
            self.pin_list[index]["tsk"] = tsk * factor
            self.pin_list[index]["tsw"] = tsw * factor
            self.pin_list[index]["tsh"] = tsh * factor
            if node == 1:
                self.pin_list[index]["bx"] = nx - fw * 0.5
                self.pin_list[index]["by"] = ny - fh * 0.5
                self.pin_list[index]["bl"] = nx - fw
                self.pin_list[index]["br"] = nx
                self.pin_list[index]["bt"] = ny - fh
                self.pin_list[index]["bb"] = ny
            if node == 2:
                self.pin_list[index]["bx"] = nx
                self.pin_list[index]["by"] = ny - fh * 0.5
                self.pin_list[index]["bl"] = nx - fw * 0.5
                self.pin_list[index]["br"] = nx + fw * 0.5
                self.pin_list[index]["bt"] = ny - fh
                self.pin_list[index]["bb"] = ny
            if node == 3:
                self.pin_list[index]["bx"] = nx + fw * 0.5
                self.pin_list[index]["by"] = ny - fh * 0.5
                self.pin_list[index]["bl"] = nx
                self.pin_list[index]["br"] = nx + fw
                self.pin_list[index]["bt"] = ny - fh
                self.pin_list[index]["bb"] = ny
            if node == 4:
                self.pin_list[index]["bx"] = nx - fw * 0.5
                self.pin_list[index]["by"] = ny
                self.pin_list[index]["bl"] = nx - fw
                self.pin_list[index]["br"] = nx
                self.pin_list[index]["bt"] = ny - fh * 0.5
                self.pin_list[index]["bb"] = ny + fh * 0.5
            if node == 6:
                self.pin_list[index]["bx"] = nx + fw * 0.5
                self.pin_list[index]["by"] = ny
                self.pin_list[index]["bl"] = nx
                self.pin_list[index]["br"] = nx + fw
                self.pin_list[index]["bt"] = ny - fh * 0.5
                self.pin_list[index]["bb"] = ny + fh * 0.5
            if node == 7:
                self.pin_list[index]["bx"] = nx - fw * 0.5
                self.pin_list[index]["by"] = ny + fh * 0.5
                self.pin_list[index]["bl"] = nx - fw
                self.pin_list[index]["br"] = nx
                self.pin_list[index]["bt"] = ny
                self.pin_list[index]["bb"] = ny + fh
            if node == 8:
                self.pin_list[index]["bx"] = nx
                self.pin_list[index]["by"] = ny + fh * 0.5
                self.pin_list[index]["bl"] = nx - fw * 0.5
                self.pin_list[index]["br"] = nx + fw * 0.5
                self.pin_list[index]["bt"] = ny
                self.pin_list[index]["bb"] = ny + fh
            if node == 9:
                self.pin_list[index]["bx"] = nx + fw * 0.5
                self.pin_list[index]["by"] = ny + fh * 0.5
                self.pin_list[index]["bl"] = nx
                self.pin_list[index]["br"] = nx + fw
                self.pin_list[index]["bt"] = ny
                self.pin_list[index]["bb"] = ny + fh
            self.pin_list[index]["bw"] = fw
            self.pin_list[index]["bh"] = fh
            self.pin_list[index]["area"] = fw * fh
            self.pin_list[index]["perimeter"] = 2 * fw + 2 * fh
            self.pin_list[index]["ratio"] = fw / fh
    def Scale_Factor( self, previous, index, nx, ny, factor ):
        # Read
        trz = previous[index]["trz"]
        tsk = previous[index]["tsk"]
        tsw = previous[index]["tsw"]
        tsh = previous[index]["tsh"]
        bx = previous[index]["bx"]
        by = previous[index]["by"]
        bl = previous[index]["bl"]
        br = previous[index]["br"]
        bt = previous[index]["bt"]
        bb = previous[index]["bb"]
        bw = previous[index]["bw"]
        bh = previous[index]["bh"]

        # Calculation
        n_tsk = tsk * factor
        n_tsw = tsw * factor
        n_tsh = tsh * factor
        n_bx = nx + ( bx - nx ) * factor
        n_by = ny + ( by - ny ) * factor
        n_bl = nx + ( bl - nx ) * factor
        n_br = nx + ( br - nx ) * factor
        n_bt = ny + ( bt - ny ) * factor
        n_bb = ny + ( bb - ny ) * factor
        n_bw = n_br - n_bl
        n_bh = n_bb - n_bt

        # Write
        self.pin_list[index]["tsk"] = n_tsk
        self.pin_list[index]["tsw"] = n_tsw
        self.pin_list[index]["tsh"] = n_tsh
        self.pin_list[index]["bx"] = n_bx
        self.pin_list[index]["by"] = n_by
        self.pin_list[index]["bl"] = n_bl
        self.pin_list[index]["br"] = n_br
        self.pin_list[index]["bt"] = n_bt
        self.pin_list[index]["bb"] = n_bb
        self.pin_list[index]["bw"] = n_bw
        self.pin_list[index]["bh"] = n_bh
        self.pin_list[index]["area"] = n_bw * n_bh
        self.pin_list[index]["perimeter"] = 2 * n_bw + 2 * n_bh
        self.pin_list[index]["ratio"] = n_bw / n_bh
    def Scale_Label( self, previous, index, node, dx, dy ):
        # dx, dy =  delta amount

        # Variabels
        snap_dist = 10 / self.cz

        # Read
        bx = previous[index]["bx"]
        by = previous[index]["by"]
        bl = previous[index]["bl"]
        br = previous[index]["br"]
        bt = previous[index]["bt"]
        bb = previous[index]["bb"]
        # Nodes
        if node == 1:
            n_bl = bl + dx
            n_br = br
            n_bt = bt + dy
            n_bb = bb
        if node == 2:
            n_bl = bl
            n_br = br
            n_bt = bt + dy
            n_bb = bb
        if node == 3:
            n_bl = bl
            n_br = br + dx
            n_bt = bt + dy
            n_bb = bb
        if node == 4:
            n_bl = bl + dx
            n_br = br
            n_bt = bt
            n_bb = bb
        if node == 6:
            n_bl = bl
            n_br = br + dx
            n_bt = bt
            n_bb = bb
        if node == 7:
            n_bl = bl + dx
            n_br = br
            n_bt = bt
            n_bb = bb + dy
        if node == 8:
            n_bl = bl
            n_br = br
            n_bt = bt
            n_bb = bb + dy
        if node == 9:
            n_bl = bl
            n_br = br + dx
            n_bt = bt
            n_bb = bb + dy

        # Snap
        sx = 0
        sy = 0
        for j in range( 0, len( self.limit_x ) ):
            xj = self.limit_x[j]
            ll = xj - snap_dist
            lr = xj + snap_dist
            dl = abs( xj - n_bl )
            dr = abs( xj - n_br )
            if node in ( 1, 4, 7 ): # Left
                cl = ( n_bl >= ll and n_bl <= lr )
                if cl == True:
                    sx = xj - n_bl
                    break
            if node in ( 3, 6, 9 ): # Right
                cr = ( n_br >= ll and n_br <= lr )
                if cr == True:
                    sx = xj - n_br
                    break
        for j in range( 0, len( self.limit_y ) ):
            yj = self.limit_y[j]
            lt = yj - snap_dist
            lb = yj + snap_dist
            dt = abs( yj - n_bt )
            db = abs( yj - n_bb )
            if node in ( 1, 2, 3 ): # Top
                ct = ( n_bt >= lt and n_bt <= lb )
                if ct == True:
                    sy = yj - n_bt
                    break
            if node in ( 7, 8, 9 ): # Bottom
                cb = ( n_bb >= lt and n_bb <= lb )
                if cb == True:
                    sy = yj - n_bb
                    break

        # Nodes
        if node == 1:
            n_bl += sx
            n_bt += sy
        if node == 2:
            n_bt += sy
        if node == 3:
            n_br += sx
            n_bt += sy
        if node == 4:
            n_bl += sx
        if node == 6:
            n_br += sx
        if node == 7:
            n_bl += sx
            n_bb += sy
        if node == 8:
            n_bb += sy
        if node == 9:
            n_br += sx
            n_bb += sy
        # Dimensions
        w = n_br - n_bl
        h = n_bb - n_bt
        # Write
        if w > 0:
            self.pin_list[index]["bx"] = n_bl + w * 0.5
            self.pin_list[index]["bl"] = n_bl
            self.pin_list[index]["br"] = n_br
        if h > 0:
            self.pin_list[index]["by"] = n_bt + h * 0.5
            self.pin_list[index]["bt"] = n_bt
            self.pin_list[index]["bb"] = n_bb
        if w < 0:
            w = abs( w )
            self.pin_list[index]["bx"] = n_br + w * 0.5
            self.pin_list[index]["bl"] = n_br
            self.pin_list[index]["br"] = n_bl
        if h < 0:
            h = abs( h )
            self.pin_list[index]["by"] = n_bb + h * 0.5
            self.pin_list[index]["bt"] = n_bb
            self.pin_list[index]["bb"] = n_bt
        if ( w > 0 and h > 0 ):
            self.pin_list[index]["bw"] = w
            self.pin_list[index]["bh"] = h
            self.pin_list[index]["area"] = w * h
            self.pin_list[index]["perimeter"] = 2 * w + 2 * h
            self.pin_list[index]["ratio"] = w / h

    # Rotate
    def Rotate_Pin( self, dx ):
        # Angle
        angle = Limit_Angle( dx / 2, 2.5 )
        # Rotate Pin Index
        self.Rotate_Transform( self.pin_previous, self.pin_index, angle )
        self.Pin_Draw_QPixmap( self.pin_list, self.pin_index )

        # Selection
        if self.select_count > 0:
            for i in range( 0, self.pin_count ):
                if self.pin_list[i]["select"] == True:
                    self.Rotate_Transform( self.pin_previous, i, angle )
                    self.Pin_Draw_QPixmap( self.pin_list, i )
    def Rotate_Transform( self, previous, index, angle ):
        # Read
        bx = previous[index]["bx"]
        by = previous[index]["by"]
        trz = previous[index]["trz"]
        tsk = previous[index]["tsk"]
        tsw = previous[index]["tsw"]
        tsh = previous[index]["tsh"]

        # Variables
        n_trz = Limit_Looper( trz + angle, 360 )
        # Dimensions
        w2 = tsw * 0.5
        h2 = tsh * 0.5
        raio = tsk * 0.5
        # Points

        cn = [ bx - w2, by ]
        c1 = [ bx - w2, by - h2 ]
        c3 = [ bx + w2, by - h2 ]
        c7 = [ bx - w2, by + h2 ]
        c9 = [ bx + w2, by + h2 ]
        # Angles for Corners
        a_c1 = Trig_2D_Points_Lines_Angle( cn[0], cn[1], bx, by, c1[0], c1[1] )
        a_c3 = Trig_2D_Points_Lines_Angle( cn[0], cn[1], bx, by, c3[0], c3[1] )
        a_c7 = Trig_2D_Points_Lines_Angle( cn[0], cn[1], bx, by, c7[0], c7[1] )
        a_c9 = Trig_2D_Points_Lines_Angle( cn[0], cn[1], bx, by, c9[0], c9[1] )
        # Circle Points
        c1_x, c1_y = Trig_2D_Points_Rotate( bx, by, raio, Limit_Looper( a_c1 + n_trz, 360 ) )
        c3_x, c3_y = Trig_2D_Points_Rotate( bx, by, raio, Limit_Looper( a_c3 + n_trz, 360 ) )
        c7_x, c7_y = Trig_2D_Points_Rotate( bx, by, raio, Limit_Looper( a_c7 + n_trz, 360 ) )
        c9_x, c9_y = Trig_2D_Points_Rotate( bx, by, raio, Limit_Looper( a_c9 + n_trz, 360 ) )
        # New Bounding Box
        n_bl = bx + ( min( c1_x, c3_x, c7_x, c9_x ) - bx )
        n_br = bx + ( max( c1_x, c3_x, c7_x, c9_x ) - bx )
        n_bt = by + ( min( c1_y, c3_y, c7_y, c9_y ) - by )
        n_bb = by + ( max( c1_y, c3_y, c7_y, c9_y ) - by )
        n_bw = ( n_br - n_bl )
        n_bh = ( n_bb - n_bt )

        # Write
        self.pin_list[index]["trz"] = n_trz
        self.pin_list[index]["bl"] = n_bl
        self.pin_list[index]["br"] = n_br
        self.pin_list[index]["bt"] = n_bt
        self.pin_list[index]["bb"] = n_bb
        self.pin_list[index]["bw"] = n_bw
        self.pin_list[index]["bh"] = n_bh
        self.pin_list[index]["area"] = n_bw * n_bh
        self.pin_list[index]["perimeter"] = 2 * n_bw + 2 * n_bh
        self.pin_list[index]["ratio"] = n_bw / n_bh

    # Edit
    def Edit_Pin( self, egs, efx, efy ):
        for i in range( 0, self.pin_count ):
            valid = self.pin_list[i]["active"] == True or self.pin_list[i]["select"] == True
            if valid == True:
                # Write
                self.pin_list[i]["egs"] = egs
                self.pin_list[i]["efx"] = efx
                self.pin_list[i]["efy"] = efy
                # QPixmaps
                self.Pin_Draw_QPixmap( self.pin_list, i )

    # Selection
    def Selection_Click( self, index ):
        if index != None:
            select = self.pin_list[index]["select"]
            if select == True:
                self.pin_list[index]["select"] = False
            else:
                self.pin_list[index]["select"] = True
        self.Selection_Verify()
    def Selection_Box( self, ex, ey, operation ):
        # Variables
        self.select_box = True
        self.select_count = 0

        # Selection
        dist = Trig_2D_Points_Distance( self.ox, self.oy, ex, ey )
        if dist > 10:
            sl = min( ex, self.ox )
            sr = max( ex, self.ox )
            st = min( ey, self.oy )
            sb = max( ey, self.oy )
            for i in range( 0, self.pin_count ):
                dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( i )
                check = ( dl >= sl ) and ( dr <= sr ) and ( dt >= st ) and ( db <= sb )
                if check == True:
                    if operation in ( "add", "replace" ):
                        self.pin_list[i]["select"] = True
                    if operation == "minus":
                        self.pin_list[i]["select"] = False
                    self.select_count += 1
                if ( check == False and operation == "replace" ):
                    self.pin_list[i]["select"] = False
    def Selection_Verify( self ):
        # Variables
        self.state_select = False
        self.select_count = 0

        # Cycle
        for i in range( 0, self.pin_count ):
            if self.pin_list[i]["select"] == True:
                self.state_select = True
                self.select_count += 1

        # Label
        lista = self.Label_List()
        if len( lista ) > 0:
            index = lista[-1]
            self.Label_Panel( index )
    def Selection_Raise( self ):
        holder = list()
        # Collect Pin
        for pin in self.pin_list:
            if pin["select"] == True:
                holder.append( pin )
                self.pin_list.remove( pin )
        # Update
        self.pin_list.extend( holder )
        self.Pin_Update()
        del holder
    def Selection_All( self ):
        # Variables
        count = self.pin_count
        self.state_select = True
        self.select_count = count
        # Pin
        for i in range( 0, count ):
            self.pin_list[i]["select"] = True
            self.pin_list[i]["active"] = False
    def Selection_Clear( self ):
        # Variables
        self.state_select = False
        self.select_box = False
        self.select_count = 0
        # Pin
        for i in range( 0, self.pin_count ):
            self.pin_list[i]["select"] = False
            self.pin_list[i]["active"] = False

    # Boards
    def Board_Insert( self, lista ):
        # Insert Pins
        self.pin_list.clear()
        self.pin_count = len( lista )
        for i in range( 0, self.pin_count ):
            pin = lista[i]
            self.pin_list.append( pin )
        # Update
        self.Board_Update()
    def Board_Fit( self ):
        # Variables
        self.pin_count = len( self.pin_list )
        if self.pin_count > 0:
            # Variables
            nx, ny = self.Point_Location( 0, 0 )
            mx, my = self.Point_Location( self.ww, self.hh )
            nmx = mx - nx
            nmy = my - ny
            # Board
            board_l, board_r, board_t, board_b, board_w, board_h = self.Board_Limit( "PIN" )
            # Move to Neutral
            for i in range( 0, self.pin_count ):
                px = nx + self.pin_list[i]["bl"] - board_l
                py = ny + self.pin_list[i]["bt"] - board_t
                self.Move_Point( self.pin_list, i, px, py )

            # Board
            board_l, board_r, board_t, board_b, board_w, board_h = self.Board_Limit( "PIN" )
            # Move to Center
            for i in range( 0, self.pin_count ):
                px = self.w2 + ( self.pin_list[i]["bl"] - ( board_l + board_w * 0.5 ) )
                py = self.h2 + ( self.pin_list[i]["bt"] - ( board_t + board_h * 0.5 ) )
                self.Move_Point( self.pin_list, i, px, py )

            self.Camera_Zoom_Fit()

        # Update
        self.Pin_Previous()
        self.Board_Limit( "DRAW" )
        self.update()
    def Board_Clear( self ):
        self.pin_list.clear()
        self.Board_Update()
    def Board_Update( self ):
        # Pin
        self.pin_count = len( self.pin_list )
        self.Pin_Previous()
        # Camera
        self.Camera_Emit()
        # Board
        self.Board_Limit( "DRAW" )
        self.Board_Render()
        self.Board_Save()
        # Update
        self.update()
        self.Camera_Grab()
    def Board_Limit( self, mode ):
        # Variables
        self.pin_count = len( self.pin_list )
        board_horz = []
        board_vert = []
        # Cycle
        for i in range( 0, self.pin_count ):
            # Read
            if mode == "PIN":
                bl = self.pin_list[i]["bl"]
                br = self.pin_list[i]["br"]
                bt = self.pin_list[i]["bt"]
                bb = self.pin_list[i]["bb"]
            if mode == "DRAW":
                bx, by, bl, br, bt, bb, bw, bh = self.Pin_Draw_Box( i )
            # Board Limit
            board_horz.extend( [ bl, br ] )
            board_vert.extend( [ bt, bb ] )
        if ( self.pin_count > 0 ):
            board_l = min( board_horz )
            board_r = max( board_horz )
            board_t = min( board_vert )
            board_b = max( board_vert )
            board_w = board_r - board_l
            board_h = board_b - board_t
        else:
            board_l = 0
            board_r = 0
            board_t = 0
            board_b = 0
            board_w = 0
            board_h = 0
        # Return
        if mode == "PIN":
            return board_l, board_r, board_t, board_b, board_w, board_h
        if mode == "DRAW":
            self.board_l = board_l
            self.board_r = board_r
            self.board_t = board_t
            self.board_b = board_b
            self.board_w = board_w
            self.board_h = board_h
    def Board_Render( self ):
        for i in range( 0, self.pin_count ):
            # Read
            render = self.pin_list[i]["render"]
            # Calculations
            dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( i )
            draw = not ( ( dl > self.ww ) or ( dr < 0 ) or ( dt > self.hh ) or ( db < 0 ) )
            # Write
            self.pin_list[i]["render"] = draw
            # Update Draw Information
            if ( render == False and draw == True ):
                self.Pin_Draw_QPixmap( self.pin_list, i )
    def Board_Focus( self ):
        for i in range( 0, self.pin_count ):
            if self.pin_list[i]["render"] != None:
                self.Pin_Draw_QPixmap( self.pin_list, i )
    def Board_Save( self ):
        self.SIGNAL_BOARD_SAVE.emit( self.pin_list )
    def Board_Locked( self, boolean ):
        self.state_locked = boolean
        self.SIGNAL_LOCKED.emit( self.state_locked )

    # Reset
    def Reset_Rotation( self, lista ):
        self.Pin_Previous()
        for item in lista:
            index = item["index"]
            angle = -self.pin_list[index]["trz"]
            self.Rotate_Transform( self.pin_previous, index, angle )
            self.Pin_Draw_QPixmap( self.pin_list, index )
    def Reset_Scale( self, lista ):
        # Variables
        side = 200
        # Scaling
        self.Pin_Previous()
        for pin in lista:
            # Read
            index = pin["index"]
            nx = pin["bl"]
            ny = pin["bt"]
            width = pin["bw"]
            height = pin["bh"]
            # Calculations
            if width >= height:
                factor = side / height
            else:
                factor = side / width
            # Scale
            self.Scale_Factor( self.pin_previous, index, nx, ny, factor )
            self.Pin_Draw_QPixmap( self.pin_list, index )

    # Relative
    def Relative_Rebase( self, lista ):
        # Variables
        count = self.pin_count
        suggestion = ""
        for item in lista:
            path = item["path"]
            if path != None:
                suggestion = os.path.dirname( path )
                break
        previous_path = lista[0]["path"]

        # Select Directory
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        directory = file_dialog.getExistingDirectory( self, f"Select Directory - previous_path = { previous_path }", suggestion )
        if directory not in [ "", "." ]:
            qdir = QDir( directory )
            qdir.setSorting( QDir.LocaleAware )
            qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            qdir.setNameFilters( self.file_extension )
            files = qdir.entryInfoList()
        else:
            files = []

        # Search Cycles
        path_old = []
        for i in range( 0, self.pin_count ):
            item = self.pin_list[i]
            path = item["path"]
            qpixmap = QPixmap( path )
            if qpixmap.isNull() == False:
                item["qpixmap"] = qpixmap
                item["draw"] = self.Pin_Draw_QPixmap( self.pin_list, i )
            else:
                item["qpixmap"] = None
                item["draw"] = None
            path_old.append( path )
        for item in lista:
            tipo = item["tipo"]
            bx = item["bx"]
            by = item["by"]
            cstate = item["cstate"]
            cl = item["cl"]
            ct = item["ct"]
            cw = item["cw"]
            ch = item["ch"]
            path = item["path"]
            web = item["web"]
            qpixmap = item["qpixmap"]
            if path != None:
                basename = os.path.basename( path )
            elif web != None:
                basename = os.path.split( urllib.parse.urlparse( web ).path )[1]
            else:
                basename = None
            if ( tipo == "image" and qpixmap == None ):
                for f in files:
                    fn = f.fileName() # basename
                    fp = os.path.abspath( f.filePath() ) # path
                    if basename == fn and fp not in path_old:
                        pin = { "bx" : bx + 20, "by" : by + 20, "image_path" : fp }
                        clip = { "cstate":cstate, "cl":cl, "ct":ct, "cw":cw, "ch":ch }
                        self.SIGNAL_PIN_IMAGE.emit( pin, clip )
                        break
            # Selection
            if len( self.pin_list ) > count:
                self.Selection_Clear()
                for i in range( count, len( self.pin_list ) ):
                    self.pin_list[i]["select"] = True
                self.Selection_Verify()
        # Update
        self.Board_Update()
        self.Board_Focus()
    def Relative_Delete( self, lista ):
        for i in range( 0, len( lista ) ):
            self.pin_list.remove( lista[i] )
        self.pin_count = len( self.pin_list )
        if self.pin_count == 0:
            self.Camera_Reset()
        self.Camera_Emit()
        self.Board_Update()

    # Camera
    def Camera_Reset( self ):
        self.ci = self.cn.index( 1 )
        self.cz = self.cn[self.ci] # Camera Zoom
    def Camera_Move( self, ex, ey ):
        dx, dy = self.Point_Deltas( ex, ey )
        for i in range( 0, self.pin_count ):
            self.Move_Transform( self.pin_previous, i, dx, dy )
    def Camera_Scale( self, ex, ey ):
        dy = -( ( ey - self.oy ) / 10 )
        if abs( dy ) >= 1:
            self.oy = ey
            self.Camera_Zoom_Step( dy )
    def Camera_Zoom_Step( self, step ):
        self.ci = Limit_Range( self.ci + int( step ), 0, len( self.cn ) - 1 )
        self.cz = self.cn[self.ci]
        self.Camera_Emit()
    def Camera_Zoom_Fit( self ):
        # Board
        bl, br, bt, bb, bw, bh = self.Board_Limit( "PIN" )
        # Widget
        pl = 0
        pt = 0
        pr = self.ww
        pb = self.hh
        w2 = pr * 0.5
        h2 = pb * 0.5

        # Ratio
        cl = ( pl - w2 ) / ( bl - w2 )
        cr = ( pr - w2 ) / ( br - w2 )
        ct = ( pt - h2 ) / ( bt - h2 )
        cb = ( pb - h2 ) / ( bb - h2 )
        # Zoom
        zoom = []
        if cl > 0:zoom.append( cl )
        if cr > 0:zoom.append( cr )
        if ct > 0:zoom.append( ct )
        if cb > 0:zoom.append( cb )
        zoom = min( zoom )

        # Index
        index = self.cn.index( 1 )
        for i in range( 0, len( self.cn ) ):
            if ( zoom >= self.cn[i] and zoom < self.cn[i+1] ):
                index = i
                break
        # Apply
        self.ci = index
        self.cz = self.cn[self.ci]
        self.Camera_Emit()
    def Camera_Signal( self ):
        if ( self.board_w != 0 or self.board_h != 0 ):
            px = ( self.w2 - self.board_l ) / self.board_w
            py = ( self.h2 - self.board_t ) / self.board_h
        else:
            px = 0
            py = 0
        self.SIGNAL_CAMERA.emit( [ px, py ], self.cz, self.pin_count )
    def Camera_Emit( self ):
        self.Camera_Signal()
        for i in range( 0, self.pin_count ):
            self.Pin_Draw_QPixmap( self.pin_list, i )
    def Camera_Grab( self ):
        try:self.qimage_grab = self.grab().toImage()
        except:pass

    # Packer
    def Packer_Process( self, method ):
        if self.select_count > 0:
            # Variables
            self.state_pack = True
            # Widget
            self.setEnabled( False )
            self.SIGNAL_PACK_STOP.emit( True )
            # Pin
            self.Selection_Raise()
            # Packer
            thread = True
            if thread == False:self.Packer_Single_Start( method )
            if thread == True:self.Packer_Thread_Start( method )
    def Packer_Single_Start( self, method ):
        self.worker_packer = Worker_Packer()
        self.worker_packer.run( self, "SINGLE", method )
    def Packer_Thread_Start( self, method ):
        # Thread
        self.thread_packer = QThread()
        # Worker
        self.worker_packer = Worker_Packer()
        self.worker_packer.moveToThread( self.thread_packer )
        # Thread
        self.thread_packer.started.connect( lambda : self.worker_packer.run( self, "THREAD", method ) )
        self.thread_packer.start()
    def Packer_Thread_Quit( self ):
        self.thread_packer.quit()
        self.Packer_Stop()
    def Packer_Stop( self ):
        # Variables
        self.state_pack = False
        self.Pin_Previous()
        # Widget
        self.setEnabled( True )
        self.SIGNAL_PACK_STOP.emit( False )
        # Update
        self.update()

    # UI
    def ProgressBar_Value( self, value ):
        self.SIGNAL_PB_VALUE.emit( value )
    def ProgressBar_Maximum( self, maximum ):
        self.SIGNAL_PB_MAX.emit( maximum )

    # Cursor
    def Cursor_Shape( self, operation, pin_node ):
        if ( operation == "color_picker" ):
            QApplication.setOverrideCursor( Qt.CrossCursor )
        elif ( operation == "pin_move" or operation == "pin_transform" ):
            if pin_node == 0:
                QApplication.setOverrideCursor( Qt.SizeAllCursor )
            elif pin_node == 5:
                QApplication.setOverrideCursor( Qt.SizeHorCursor )
            elif pin_node in ( 1, 9 ):
                QApplication.setOverrideCursor( Qt.SizeFDiagCursor )
            elif pin_node in ( 3, 7 ):
                QApplication.setOverrideCursor( Qt.SizeBDiagCursor )
            elif pin_node in ( 2, 8 ):
                QApplication.setOverrideCursor( Qt.SizeVerCursor )
            elif pin_node in ( 4, 6 ):
                QApplication.setOverrideCursor( Qt.SizeHorCursor )
        elif ( operation == "camera_move" ):
            QApplication.setOverrideCursor( Qt.SizeAllCursor )
        elif ( operation == "camera_scale" ):
            QApplication.setOverrideCursor( Qt.SizeVerCursor )
        elif ( operation == "select_add" or operation == "select_minus" or operation == "select_replace" ):
            QApplication.restoreOverrideCursor()
        elif ( operation == "drag" ):
            QApplication.setOverrideCursor( Qt.ClosedHandCursor )
        elif ( operation == "drop" ):
            QApplication.setOverrideCursor( Qt.OpenHandCursor )
        else:
            QApplication.restoreOverrideCursor()

    # Keyboard Event
    def keyPressEvent( self, event ):
        # Spacebar
        if event.key() == Qt.Key.Key_Space:
            pass

        # Escape
        if event.key() == Qt.Key.Key_Escape:
            self.Selection_Clear()
            self.update()

        # Delete
        if event.key() == Qt.Key.Key_Delete:
            selection = []
            for i in range( 0, self.pin_count ):
                if self.pin_list[i]["select"] == True:
                    selection.append( self.pin_list[i] )
            self.Relative_Delete( selection )
            self.update()

        # Pack
        if event.key() == Qt.Key.Key_P:
            self.Packer_Process( "GRID" )
    def keyReleaseEvent( self, event ):
        # Space
        if event.key() == Qt.Key.Key_Space:
            auto = event.isAutoRepeat()
            if auto == False:
                pass

        # Escape
        if event.key() == Qt.Key.Key_Escape:
            pass

        # Delete
        if event.key() == Qt.Key.Key_Delete:
            pass

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        # variables
        self.state_press = False
        self.operation = None
        state_insert = Insert_Check( self )

        # Cursor
        QApplication.restoreOverrideCursor()

        # Path
        if self.pin_index == None:
            pin_tipo = None
            pin_egs = False
            pin_efx = False
            pin_efy = False
            pin_erz = 0
            pin_path = None
            pin_web = None
            pin_qpixmap = None
        else:
            pin = self.pin_list[self.pin_index]
            pin_tipo = pin["tipo"]
            pin_erz = pin["trz"]
            pin_egs = pin["egs"]
            pin_efx = pin["efx"]
            pin_efy = pin["efy"]
            pin_path = pin["path"]
            pin_web = pin["web"]
            pin_qpixmap = pin["qpixmap"]

        # Color
        string_pickcolor = "Color Picker"
        if self.pigment_o == None:
            string_pickcolor += " [RGB]"

        # Relative
        relative = []
        for i in range( 0, self.pin_count ):
            if ( self.pin_list[i]["active"] == True or self.pin_list[i]["select"] == True ):
                relative.append( self.pin_list[i] )

        # Clip
        clip = { 
            "cstate" : False,
            "cl": 0,
            "ct": 0,
            "cw": 1,
            "ch": 1,
            }

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )

        # General
        action_locked = qmenu.addAction( "Locked" )
        action_refresh = qmenu.addAction( "Refresh" )
        action_board_fit = qmenu.addAction( "Board Fit" )
        action_insert_pin = qmenu.addAction( "Insert Pin" )
        action_full_screen = qmenu.addAction( "Full Screen" )
        qmenu.addSeparator()
        # Label
        menu_label = qmenu.addMenu( "Label" )
        action_label_create = menu_label.addAction( "Create" )
        action_label_edit = menu_label.addAction( "Edit" )
        # Pin
        menu_pin = qmenu.addMenu( "Pin" )
        action_pin_location = menu_pin.addAction( "File Location" )
        action_pin_copy     = menu_pin.addAction( "Copy Path" )
        action_pin_save     = menu_pin.addAction( "Save To" )
        # Packer
        menu_pack = qmenu.addMenu( f"Pack [ { self.select_count } ]" )
        action_pack_grid      = menu_pack.addAction( "Linear Grid" )
        action_pack_row       = menu_pack.addAction( "Linear Row" )
        action_pack_column    = menu_pack.addAction( "Linear Column" )
        action_pack_pile      = menu_pack.addAction( "Linear Pile" )
        action_pack_area      = menu_pack.addAction( "Optimal Area" )
        action_pack_perimeter = menu_pack.addAction( "Optimal Perimeter" )
        action_pack_ratio     = menu_pack.addAction( "Optimal Ratio" )
        action_pack_class     = menu_pack.addAction( "Optimal Class" )
        # Reset
        menu_reset = qmenu.addMenu( "Reset" )
        action_reset_rotation  = menu_reset.addAction( "Rotation" )
        action_reset_scale     = menu_reset.addAction( "Scale" )
        # Edit
        menu_edit = qmenu.addMenu( "Edit" )
        action_edit_grey   = menu_edit.addAction( "View Greyscale" )
        action_edit_flip_h = menu_edit.addAction( "Flip Horizontal" )
        action_edit_flip_v = menu_edit.addAction( "Flip Vertical" )
        action_edit_reset  = menu_edit.addAction( "Reset" )
        # Color
        menu_color = qmenu.addMenu( "Color" )
        action_color_picker  = menu_color.addAction( string_pickcolor )
        action_color_analyse = menu_color.addAction( "Analyse" )
        # Insert
        menu_insert = qmenu.addMenu( "Insert ")
        action_insert_document  = menu_insert.addAction( "Document" )
        action_insert_layer     = menu_insert.addAction( "Layer" )
        action_insert_reference = menu_insert.addAction( "Reference" )
        qmenu.addSeparator()
        # Context
        action_rebase = qmenu.addAction( "Rebase" )
        action_delete = qmenu.addAction( "Delete" )

        # Check Full Screen
        action_locked.setCheckable( True )
        action_locked.setChecked( self.state_locked )
        action_full_screen.setCheckable( True )
        action_full_screen.setChecked( self.state_maximized )
        # Check Label
        action_label_edit.setCheckable( True )
        action_label_edit.setChecked( self.state_label )
        # Check Edit
        action_edit_grey.setCheckable( True )
        action_edit_grey.setChecked( pin_egs )
        action_edit_flip_h.setCheckable( True )
        action_edit_flip_h.setChecked( pin_efx )
        action_edit_flip_v.setCheckable( True )
        action_edit_flip_v.setChecked( pin_efy )
        # Check Color Picker
        action_color_picker.setCheckable( True )
        action_color_picker.setChecked( self.state_pickcolor )

        # General
        if self.state_locked == True:
            action_insert_pin.setEnabled( False )
        # Label
        if self.state_locked == True:
            menu_label.setEnabled( False )
        # Disable Pin
        if pin_tipo != "image":
            menu_pin.setEnabled( False )
        # Disable Packer
        if ( self.select_count == 0 or self.state_locked == True ):
            menu_pack.setEnabled( False )
        # Disable Reset
        if ( self.pin_index == None or self.state_locked == True ):
            menu_reset.setEnabled( False )
        # Disable Edit
        if ( self.pin_index == None or self.state_locked == True ):
            menu_edit.setEnabled( False )
        # Disable Color
        if ( self.pin_index == None or self.pigment_o == None ):
            action_color_analyse.setEnabled( False )
        # Disable Insert
        if self.pin_index == None:
            action_insert_document.setEnabled( False )
        if self.pin_index == None or state_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_reference.setEnabled( False )
        # Disable Relative
        if ( self.pin_index == None or self.state_locked == True ):
            action_rebase.setEnabled( False )
            action_delete.setEnabled( False )

        #endregion
        #region Actions

        # Mapping
        action = qmenu.exec_( self.mapToGlobal( event.pos() ) )

        # General
        if action == action_locked:
            self.Board_Locked( not self.state_locked )
        if action == action_board_fit:
            self.Board_Fit()
        if action == action_insert_pin:
            bx = event.pos().x()
            by = event.pos().y()
            self.Pin_URL( bx, by )
        if action == action_refresh:
            self.SIGNAL_REFRESH.emit()
        if action == action_full_screen:
            self.SIGNAL_FULL_SCREEN.emit( not self.state_maximized )

        # Label
        if action == action_label_create:
            self.Label_Insert( event )
        if action == action_label_edit:
            self.state_label = not self.state_label
            self.SIGNAL_LABEL_PANEL.emit( self.state_label )

        # Pin
        if action == action_pin_location:
            self.SIGNAL_LOCATION.emit( pin_path )
        if action == action_pin_copy:
            Path_Copy( self, pin_path )
        if action == action_pin_save:
            self.SIGNAL_PIN_SAVE.emit( pin_qpixmap )

        # Pack Linear
        if action == action_pack_grid:
            self.Packer_Process( "GRID" )
        if action == action_pack_row:
            self.Packer_Process( "ROW" )
        if action == action_pack_column:
            self.Packer_Process( "COLUMN" )
        if action == action_pack_pile:
            self.Packer_Process( "PILE" )
        # Pack Optimal
        if action == action_pack_area:
            self.Packer_Process( "AREA" )
        if action == action_pack_perimeter:
            self.Packer_Process( "PERIMETER" )
        if action == action_pack_ratio:
            self.Packer_Process( "RATIO" )
        if action == action_pack_class:
            self.Packer_Process( "CLASS" )

        # Reset
        if action == action_reset_rotation:
            self.Reset_Rotation( relative )
        if action == action_reset_scale:
            self.Reset_Scale( relative )

        # Edit
        if action == action_edit_grey:
            pin_egs = not pin_egs
            self.Edit_Pin( pin_egs, pin_efx, pin_efy )
        if action == action_edit_flip_h:
            pin_efx = not pin_efx
            self.Edit_Pin( pin_egs, pin_efx, pin_efy )
        if action == action_edit_flip_v:
            pin_efy = not pin_efy
            self.Edit_Pin( pin_egs, pin_efx, pin_efy )
        if action == action_edit_reset:
            self.Edit_Pin( False, False, False )

        # Color
        if action == action_color_picker:
            self.state_pickcolor = not self.state_pickcolor
        if action == action_color_analyse:
            qimage = pin_qpixmap.toImage()
            self.SIGNAL_ANALYSE.emit( qimage )

        # Insert
        if action == action_insert_document:
            self.SIGNAL_NEW_DOCUMENT.emit( pin_path, clip )
        if action == action_insert_layer:
            self.SIGNAL_INSERT_LAYER.emit( pin_path, clip )
        if action == action_insert_reference:
            self.SIGNAL_INSERT_REFERENCE.emit( pin_path, clip )

        # Relative
        if action == action_rebase:
            self.Relative_Rebase( relative )
        if action == action_delete:
            self.Relative_Delete( relative )

        #endregion

    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ox = ex
        self.oy = ey
        self.ex = ex
        self.ey = ey

        # Pin
        self.Pin_Update()
        self.Pin_Index( ex, ey )
        self.Pin_Active( self.pin_index )
        self.Pin_Limits()

        # LMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton ):
            if self.state_pickcolor == True:
                self.operation = "color_picker"
                ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
            if self.state_pickcolor == False:
                if self.pin_index == None:
                    self.operation = "select_replace"
                else:
                    self.operation = "pin_move"
                    self.pin_node = 0
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "camera_move"
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "select_add"
            self.Selection_Click( self.pin_index )
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "drag_drop"
        if ( event.modifiers() == ( QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier ) and event.buttons() == QtCore.Qt.LeftButton ):
            self.operation = "pin_transform"
        if ( event.modifiers() == ( QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier ) and event.buttons() == QtCore.Qt.LeftButton ):
            self.Pin_Preview( self.pin_index )

        # MMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.MiddleButton ):
            self.operation = "camera_move"

        # RMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = None
            self.Context_Menu( event )
        if ( event.modifiers() == QtCore.Qt.ShiftModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "camera_scale"
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "select_minus"
            self.Selection_Click( self.pin_index )
        if ( event.modifiers() == QtCore.Qt.AltModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.operation = "drag_drop"

        # Update
        self.Cursor_Shape( self.operation, self.pin_node )
        self.update()
    def mouseMoveEvent( self, event ):
        # Variable
        self.state_press = True

        # Event
        ex = event.x()
        ey = event.y()
        self.ex = ex
        self.ey = ey

        # Operations
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )

        if self.state_locked == False:
            if self.operation == "pin_move":
                dx, dy = self.Point_Deltas( ex, ey )
                if event.modifiers() == QtCore.Qt.NoModifier:
                    self.Move_Pin( dx, dy, False )
                else:
                    self.Move_Pin( dx, dy, True )
            if self.operation == "pin_transform":
                self.Pin_Transform( ex, ey, self.pin_node )

        if self.operation == "camera_move":
            self.Camera_Move( ex, ey ) 
        if self.operation == "camera_scale":
            self.Camera_Scale( ex, ey )

        if self.operation == "select_add":
            self.Selection_Box( ex, ey, "add" )
        if self.operation == "select_minus":
            self.Selection_Box( ex, ey, "minus" )
        if self.operation == "select_replace":
            self.Selection_Box( ex, ey, "replace" )

        if self.operation == "drag_drop":
            clip = { 
                "cstate" : False,
                "cl": 0,
                "ct": 0,
                "cw": 1,
                "ch": 1,
                }
            Insert_Drag( self, self.pin_path, clip )

        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Event
        ex = event.x()
        ey = event.y()

        # LMB
        if ( event.modifiers() == QtCore.Qt.NoModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.Pin_Index( ex, ey )
            self.Pin_Preview( self.pin_index )
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.LeftButton ):
            self.Selection_All()
        # RMB
        if ( event.modifiers() == QtCore.Qt.ControlModifier and event.buttons() == QtCore.Qt.RightButton ):
            self.Selection_Clear()
    def mouseReleaseEvent( self, event ):
        # Variables
        self.state_press = False
        self.drop = False
        self.drag = False
        # Color Picker
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, False )
        # Release
        self.Release_Event()
    def Release_Event( self ):
        # Variables General
        self.operation = None
        self.select_box = False
        # Variables Pin
        self.Pin_Update()
        self.Pin_Previous()
        self.pin_index = None
        self.pin_path = None
        self.pin_basename = None
        self.pin_node = None
        self.pin_count = len( self.pin_list )
        # Variables Limit
        self.limit_x = []
        self.limit_y = []

        # Update
        self.Cursor_Shape( None, None )
        self.Selection_Verify()
        self.Board_Limit( "DRAW" )
        self.Camera_Signal()
        self.update()
        self.Camera_Grab()
    # Wheel Event
    def wheelEvent( self, event ):
        # Variables
        self.state_press = True
        # Camera Zoom
        delta_y = event.angleDelta().y()
        angle = 5
        if delta_y >= angle:
            self.Camera_Zoom_Step( +1 )
        else:
            self.Camera_Zoom_Step( -1 )
        # Update
        self.update()
    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        if event.mimeData().hasImage:
            if ( self.drop == True and self.drag == False and self.state_locked == False ):
                # Policy
                event.setDropAction( Qt.CopyAction )
                # Position
                pos = event.pos()
                bx, by = self.Point_Location( pos.x(), pos.y() )
                # Data
                mime_data = Drop_Inside( self, event, False )
                # Insert Pin
                count = len( mime_data )
                # Board
                self.state_press = True
                # Progress Bar
                self.ProgressBar_Value( 0 )
                self.ProgressBar_Maximum( count )
                # Pin References
                self.drop = False
                for i in range( 0, count ):
                    # Progress Bar
                    self.ProgressBar_Value( i + 1 )
                    QApplication.processEvents()
                    # Pin
                    image_path = mime_data[i]
                    pin = { "bx" : bx, "by" : by, "image_path" : image_path }
                    self.SIGNAL_PIN_IMAGE.emit( pin, self.clip_false )
                # Progress Bar
                self.ProgressBar_Value( 0 )
                self.ProgressBar_Maximum( 1 )
                # Board
                self.state_press = False
                self.Board_Update()
            event.accept()
        else:
            event.ignore()
        self.drop = False
        self.drag = False
        self.Release_Event()
        self.update()
    # Widget Events
    def showEvent( self, event ):
        pass
    def enterEvent( self, event ):
        # Variables
        self.state_inside = True
        self.Release_Event()
        # Keyboard
        self.grabKeyboard()
        # Color Picker
        self.Camera_Grab()
    def leaveEvent( self, event ):
        # Variables
        self.state_inside = False
        self.Release_Event()
        # Keyboard
        self.releaseKeyboard()
        # Camera
        self.Board_Focus()
        # Update
        self.Board_Update()
    def closeEvent( self, event ):
        # Database
        self.Database_Close()
        # Qthread
        if self.thread_packer.isRunning():
            self.thread_packer.quit()
        # Garbage
        del self.thread_packer
        del self.worker_packer
    # Painter Event
    def paintEvent( self, event ):
        # Variables
        ww = self.ww
        hh = self.hh
        w2 = self.w2
        h2 = self.h2
        if ww < hh:
            side = ww
        else:
            side = hh
        self.pin_count = len( self.pin_list )

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Background Hover
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( self.color_alpha ) )
        painter.drawRect( 0, 0, ww, hh )

        # Mask
        painter.setClipRect( QRect( int( 0 ), int( 0 ), int( ww ), int( hh ) ), Qt.ReplaceClip )

        """
        # Board Scalling
        painter.setPen( QPen( self.color_1, 1, Qt.SolidLine ) )
        painter.setBrush( QtCore.Qt.NoBrush )
        dl = w2 - w2 * self.cz
        dt = h2 - h2 * self.cz
        dw = ww * self.cz
        dh = hh * self.cz
        dr = dl + dw
        db = dt + dh
        painter.drawRect( int(dl), int(dt), int(dw), int(dh) )
        """

        # Board
        if self.state_press == False:
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( self.color_shade ) )
            painter.drawRect( int( self.board_l ), int( self.board_t ), int( self.board_w ), int( self.board_h ) )
        # Lost Pins
        if ( self.state_press == False and self.pin_count > 0 ):
            valid = ( self.board_l >= ww ) or ( self.board_r <= 0 ) or ( self.board_t >= hh ) or ( self.board_b <= 0 )
            if valid == True:
                # Variables
                bw2 = self.board_l + self.board_w * 0.5
                bh2 = self.board_t + self.board_h * 0.5
                dot = 5
                # Line
                painter.setPen( QPen( self.color_1, 2, Qt.SolidLine ) )
                painter.setBrush( QtCore.Qt.NoBrush )
                painter.drawLine( int( w2 ), int( h2 ), int( bw2 ), int( bh2 ) )
                # Dot
                painter.setPen( QtCore.Qt.NoPen )
                painter.setBrush( QBrush( self.color_1 ) )
                painter.drawEllipse( int( w2 - dot ), int( h2 - dot ), int( dot * 2 ), int( dot * 2 ) )

        # No References Square
        if ( self.pin_count == 0 and self.drop == False ):
            painter.setPen( QtCore.Qt.NoPen )
            if self.file_path == "":
                painter.setBrush( QBrush( self.color_2 ) )
            else:
                painter.setBrush( QBrush( self.color_1 ) )
            poly_quad = QPolygon( [
                QPoint( int( w2 - ( 0.2 * side ) ), int( h2 - ( 0.2 * side ) ) ),
                QPoint( int( w2 + ( 0.2 * side ) ), int( h2 - ( 0.2 * side ) ) ),
                QPoint( int( w2 + ( 0.2 * side ) ), int( h2 + ( 0.2 * side ) ) ),
                QPoint( int( w2 - ( 0.2 * side ) ), int( h2 + ( 0.2 * side ) ) ),
                ] )
            painter.drawPolygon( poly_quad )

        # Render State
        self.Board_Render()

        # Images and Text
        painter.setBrush( QtCore.Qt.NoBrush )
        for i in range( 0, self.pin_count ):
            render = self.pin_list[i]["render"]
            if render == True:
                # Read
                tipo = self.pin_list[i]["tipo"]
                dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( i )

                # Render
                if tipo == "image":
                    # Read
                    pack = self.pin_list[i]["pack"]
                    draw = self.pin_list[i]["draw"]

                    # Image
                    if ( pack == True or draw == None ):
                        painter.setPen( QPen( self.color_1, 1, Qt.SolidLine ) )
                        painter.setBrush( QBrush( self.color_2 ) )
                        painter.drawRect( int( dl ), int( dt ), int( dw ), int( dh ) )
                    else:
                        painter.setPen( QtCore.Qt.NoPen )
                        painter.setBrush( QtCore.Qt.NoBrush )
                        painter.drawPixmap( int( dl ), int( dt ), draw )
                    del draw
                if tipo == "label":
                    # Read
                    text = self.pin_list[i]["text"]
                    font = self.pin_list[i]["font"]
                    letter = self.pin_list[i]["letter"]
                    pen = self.pin_list[i]["pen"]
                    bg = self.pin_list[i]["bg"]

                    letter_size = int( letter * self.cz )
                    if letter_size > 0:
                        # Bounding Box
                        box = QRect( int( dl ), int( dt ), int( dw ), int( dh ) )
                        # Highlight
                        painter.setPen( QtCore.Qt.NoPen )
                        painter.setBrush( QBrush( QColor( bg ) ) )
                        painter.drawRect( box )
                        # String
                        painter.setBrush( QtCore.Qt.NoBrush )
                        painter.setPen( QPen( QColor( pen ), 1, Qt.SolidLine ) )
                        qfont = QFont( font )
                        qfont.setPointSizeF( letter_size )
                        painter.setFont( qfont )
                        painter.drawText( box, Qt.AlignCenter, text )
                        # Garbage
                        del qfont

        # Decorators
        if self.state_pickcolor == False:
            # Dots Over
            if ( self.select_box == True or self.state_select == True ):
                # Variables
                sel_hor = []
                sel_ver = []
                # Painter
                painter.setPen( QtCore.Qt.NoPen )
                painter.setBrush( QBrush( self.color_1, Qt.Dense6Pattern ) )
                # Items
                for i in range( 0, self.pin_count ):
                    render = self.pin_list[i]["render"]
                    if render == True:
                        select_i = self.pin_list[i]["select"] == True
                        pack_i = self.pin_list[i]["pack"] == True
                        if ( select_i == True and pack_i == False ):
                            dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( i )
                            painter.drawRect( int( dl ), int( dt ), int( dw ), int( dh ) )
                            sel_hor.extend( [ dl, dr ] )
                            sel_ver.extend( [ dt, db ] )
                # Selection Square
                painter.setPen( QPen( self.color_1, 1, Qt.SolidLine ) )
                painter.setBrush( QtCore.Qt.NoBrush )
                if ( len( sel_hor ) > 0 and len( sel_ver ) > 0 ):
                    min_x = min( sel_hor )
                    min_y = min( sel_ver )
                    max_x = max( sel_hor )
                    max_y = max( sel_ver )
                    painter.drawRect( int( min_x ), int( min_y ), int( max_x - min_x ), int( max_y - min_y ) )
            # Active Nodes
            if ( self.state_press == True and self.pin_index != None and self.state_pack == False ):
                # Read
                dx, dy, dl, dr, dt, db, dw, dh = self.Pin_Draw_Box( self.pin_index )
                trz = self.pin_list[self.pin_index]["trz"]

                # Variables
                dw2 = dw * 0.5
                dh2 = dh * 0.5
                line = 200

                # Bounding Box
                painter.setPen( QPen( self.color_2, 1, Qt.SolidLine ) )
                painter.setBrush( QtCore.Qt.NoBrush )
                painter.drawRect( int( dl ), int( dt ), int( dw ), int( dh ) )

                # Triangle
                min_tri = 20
                if ( ww > min_tri and hh > min_tri ):
                    # Variables
                    tri = 10
                    # Scale 1
                    if self.pin_node == 1:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_t1 = QPolygon( [
                        QPoint( int( dl ),       int( dt ) ),
                        QPoint( int( dl + tri ), int( dt ) ),
                        QPoint( int( dl ),       int( dt + tri ) ),
                        ] )
                    painter.drawPolygon( poly_t1 )
                    # scale 3
                    if self.pin_node == 3:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_t3 = QPolygon( [
                        QPoint( int( dr ),       int( dt ) ),
                        QPoint( int( dr ),       int( dt + tri ) ),
                        QPoint( int( dr - tri ), int( dt ) ),
                        ] )
                    painter.drawPolygon( poly_t3 )
                    # Scale 7
                    if self.pin_node == 7:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_t7 = QPolygon( [
                        QPoint( int( dl ),       int( db ) ),
                        QPoint( int( dl ),       int( db - tri ) ),
                        QPoint( int( dl + tri ), int( db ) ),
                        ] )
                    painter.drawPolygon( poly_t7 )
                    # Scale 9
                    if self.pin_node == 9:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_t9 = QPolygon( [
                        QPoint( int( dr ),       int( db ) ),
                        QPoint( int( dr - tri ), int( db ) ),
                        QPoint( int( dr ),       int( db - tri ) ),
                        ] )
                    painter.drawPolygon( poly_t9 )

                # Squares
                min_sq = 50
                if ( ww > min_sq and hh > min_sq ):
                    # Variables
                    sq = 5
                    # Clip 2
                    if self.pin_node == 2:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_s2 = QPolygon( [
                        QPoint( int( dl + dw2 - sq ), int( dt ) ),
                        QPoint( int( dl + dw2 - sq ), int( dt + sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( dt + sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( dt ) ),
                        ] )
                    painter.drawPolygon( poly_s2 )
                    # Clip 4
                    if self.pin_node == 4:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_s4 = QPolygon( [
                        QPoint( int( dl ),      int( dt + dh2 - sq ) ),
                        QPoint( int( dl + sq ), int( dt + dh2 - sq ) ),
                        QPoint( int( dl + sq ), int( dt + dh2 + sq ) ),
                        QPoint( int( dl ),      int( dt + dh2 + sq ) ),
                        ] )
                    painter.drawPolygon( poly_s4 )
                    # Clip 6
                    if self.pin_node == 6:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_s6 = QPolygon( [
                        QPoint( int( dr ),      int( dt + dh2 - sq ) ),
                        QPoint( int( dr - sq ), int( dt + dh2 - sq ) ),
                        QPoint( int( dr - sq ), int( dt + dh2 + sq ) ),
                        QPoint( int( dr ),      int( dt + dh2 + sq ) ),
                        ] )
                    painter.drawPolygon( poly_s6 )
                    # Clip 8
                    if self.pin_node == 8:
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                    poly_s8 = QPolygon( [
                        QPoint( int( dl + dw2 - sq ), int( db ) ),
                        QPoint( int( dl + dw2 - sq ), int( db - sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( db - sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( db ) ),
                        ] )
                    painter.drawPolygon( poly_s8 )

                # Circle
                min_cir = 30
                if ( ww > min_cir and hh > min_cir ):
                    cir = 4
                    # Clip 5
                    if self.pin_node == 5:
                        # Lines
                        cir_x, cir_y = Trig_2D_Points_Rotate( dl + dw2 , dt + dh2, line, Limit_Looper( trz + 90, 360 ) )
                        neu_x, neu_y = Trig_2D_Points_Rotate( dl + dw2 , dt + dh2, line, Limit_Looper( 90, 360 ) )
                        painter.setPen( QPen( self.color_2, 4, Qt.SolidLine ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( cir_x ), int( cir_y ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( neu_x ), int( neu_y ) )
                        painter.setPen( QPen( self.color_1, 2, Qt.SolidLine ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( cir_x ), int( cir_y ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( neu_x ), int( neu_y ) )
                        # Circle
                        painter.setPen( QPen( self.color_2, 1, Qt.SolidLine ) )
                        painter.setBrush( QBrush( self.color_blue, Qt.SolidPattern ) )
                        painter.drawEllipse( int( dl + dw2 - cir ), int( dt + dh2 - cir ), int( 2 * cir ), int( 2 * cir ) )
                    else:
                        painter.setBrush( QBrush( self.color_1, Qt.SolidPattern ) )
                        painter.drawEllipse( int( dl + dw2 - cir ), int( dt + dh2 - cir ), int( 2 * cir ), int( 2 * cir ) )

        # Cursor Selection Square
        if ( self.state_press == True and self.select_box == True and self.state_pack == False ):
            painter.setPen( QPen( self.color_1, 2, Qt.SolidLine ) )
            painter.setBrush( QBrush( self.color_1, Qt.Dense7Pattern ) )
            sx = min( self.ox, self.ex )
            sy = min( self.oy, self.ey )
            sw = abs( self.ex - self.ox )
            sh = abs( self.ey - self.oy )
            painter.drawRect( int( sx ), int( sy ), int( sw ), int( sh ) )

        # Pixmap Preview
        if self.pin_preview != None:
            # Back Drop
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( self.color_backdrop ) )
            painter.drawRect( 0, 0, ww, hh )
            # Pin Preview
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QtCore.Qt.NoBrush )
            preview = self.pin_preview.scaled( int( ww ), int( hh ), Qt.KeepAspectRatio, Qt.FastTransformation )
            px = w2 - preview.width() * 0.5
            py = h2 - preview.height() * 0.5
            painter.drawPixmap( int( px ), int( py ), preview )

        # Display Color Picker
        if self.operation == "color_picker":
            ColorPicker_Render( self, painter, self.ex, self.ey )

        # Drag and Drop Triangle
        if ( self.drop == True and self.drag == False ):
            if self.state_locked == False:
                Painter_Triangle( self, painter, w2, h2, side )
            elif self.state_locked == True:
                Painter_Locked( self, painter, w2, h2, side )

        """
        # Packing Points
        v = 255
        dot = 20 * self.cz
        painter.setPen( QPen( self.color_2, 2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin ) )
        for item in self.p:
            px = w2 + ( item[0] - w2 ) * self.cz
            py = h2 + ( item[1] - h2 ) * self.cz
            valid = item[2]
            if valid == True:
                painter.setBrush( QBrush( QColor( 0, v, 0 ) ) )
            elif valid == False:
                painter.setBrush( QBrush( QColor( v, 0, 0 ) ) )
            elif valid == None:
                painter.setBrush( QBrush( self.color_1 ) )
            painter.drawEllipse( int( px - dot ), int( py - dot ), int( dot * 2 ), int( dot * 2 ) )

            # # Point location Text
            # painter.setBrush( QtCore.Qt.NoBrush )
            # painter.setPen( QPen( QColor( self.color_1 ), 1, Qt.SolidLine ) )
            # qfont = QFont( self.label_font, int( 8 * self.cz ) )
            # painter.setFont( qfont )
            # box = QRect( int( px ), int( py ), int( 100*self.cz ), int( 20*self.cz ) )
            # text = f"( {item[0]} , {item[1]} )"
            # painter.drawText( box, Qt.AlignCenter, text )
            # # Garbage
            # del qfont
        """

#endregion
#region Threads

class Worker_Packer( QObject ):

    # Run Packer
    def run( self, source, mode, method ):
        # Variables
        self.stop = False
        pin_list = source.pin_list
        count = len( pin_list )

        # Thread Settings
        if mode == "THREAD":
            source.thread_packer.setPriority( QThread.HighestPriority )

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # List Packs
        perfect_area = 0
        pack_sort = [] # Yes Packing
        pack_other = [] # No Packing
        for i in range( 0, count ):
            # Index
            pin_list[i]["index"] = i

            # Entry
            entry = {
                "index"    : pin_list[i]["index"],
                "bx"        : pin_list[i]["bx"],
                "by"        : pin_list[i]["by"],
                "bl"        : pin_list[i]["bl"],
                "br"        : pin_list[i]["br"],
                "bt"        : pin_list[i]["bt"],
                "bb"        : pin_list[i]["bb"],
                "bw"        : pin_list[i]["bw"],
                "bh"        : pin_list[i]["bh"],
                "perimeter" : pin_list[i]["perimeter"],
                "area"      : pin_list[i]["area"],
                "ratio"     : pin_list[i]["ratio"],
                }

            # Selection
            select = pin_list[i]["select"]
            if select == True:
                # List
                pack_sort.append( entry )
                # Area
                area = pin_list[i]["area"]
                perfect_area += area
                # Write
                pin_list[i]["pack"] = True
                pin_list[i]["draw"] = None
            else:
                # List
                pack_other.append( entry )
                # Write
                pin_list[i]["pack"] = False
        
        # Reorder Pin List
        list_order = list()
        reorder = list()
        reorder.extend( pack_other )
        reorder.extend( pack_sort )
        for i in range( 0, len( reorder ) ):
            list_order.append( pin_list[ reorder[i]["index"] ] )
        source.pin_list = list_order
        del list_order, reorder

        # Progress Bar
        source.ProgressBar_Maximum( count - 1 )
        source.ProgressBar_Value( 0 )

        # Packing
        if method in ( "GRID", "ROW", "COLUMN", "PILE" ):
            pack_area = self.Pack_Linear( source, mode, method, pack_sort, pack_other, pin_list )
        if method in ( "AREA", "PERIMETER", "RATIO", "CLASS" ):
            pack_area = self.Pack_Optimal( source, mode, method, pack_sort, pack_other, pin_list )

        # Progress Bar
        source.ProgressBar_Maximum( 1 )
        source.ProgressBar_Value( 0 )

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo( end )
        time = QTime( 0,0 ).addMSecs( delta )

        # Efficiency
        efficiency = round( ( perfect_area / pack_area ) * 100, 3 )
        # Print
        try:QtCore.qDebug( f"Imagine Board | PACK { time.toString( 'hh:mm:ss.zzz' ) } | COUNT { count } | METHOD { method } | EFFICIENCY { efficiency } %" )
        except:pass

        # Stop Worker
        if mode == "SINGLE":source.Packer_Stop()
        if mode == "THREAD":source.Packer_Thread_Quit()
    def STOP( self ):
        self.stop = True

    # Cycles
    def Pack_Linear( self, source, mode, method, pack_sort, pack_other, pin_list ):
        # Sorting List
        if method in ( "GRID", "ROW" ):
            pack_sort = sorted( pack_sort, reverse=True, key=lambda entry:entry["bh"] )
        if method == "COLUMN":
            pack_sort = sorted( pack_sort, reverse=True, key=lambda entry:entry["bw"] )
        if method == "PILE":
            pack_sort = sorted( pack_sort, reverse=False, key=lambda entry:entry["area"] )

        # Starting Points
        start_x = min( self.List_Key( pack_sort, "bl" ) )
        start_y = min( self.List_Key( pack_sort, "bt" ) )
        if method == "GRID":
            total_area = 0
            for i in range( 0, len( pack_sort ) ):
                total_area += pack_sort[i]["area"]
            side = math.sqrt( total_area )
            end_x = start_x + side
        if method == "PILE":
            lx = max( self.List_Key( pack_sort, "bw" ) )
            ly = max( self.List_Key( pack_sort, "bh" ) )

        # Apply to Reference List
        for s in range( 0, len( pack_sort ) ):
            # Progress Bar
            if s % 5 == 0:
                source.ProgressBar_Value( s + 1 )
                QApplication.processEvents()
            # Stop Cycle
            if self.stop == True:
                message = "Continue Packing ?"
                loop = QMessageBox.question( QWidget(), "Imagine Board", message, QMessageBox.Yes, QMessageBox.Abort )
                if loop == QMessageBox.Abort:
                    break
                self.stop = False

            # Index
            pin_index = pack_sort[s]["index"]

            # Calculation
            if s == 0:
                if method in ( "GRID", "ROW", "COLUMN" ):
                    px = start_x
                    py = start_y
                if method == "GRID":
                    above = start_y + pack_sort[s]["bh"]
                if method == "PILE":
                    px = start_x - pack_sort[s]["bw"] * 0.5 + lx * 0.5
                    py = start_y - pack_sort[s]["bh"] * 0.5 + ly * 0.5
            else:
                if method == "GRID":
                    if pack_sort[s-1]["br"] >= end_x:
                        px = start_x
                        py = above
                        above += pack_sort[s]["bh"]
                    else:
                        px = pack_sort[s-1]["br"]
                        py = pack_sort[s-1]["bt"]
                if method == "ROW":
                    px = pack_sort[s-1]["br"]
                    py = pack_sort[s-1]["bt"]
                if method == "COLUMN":
                    px = pack_sort[s-1]["bl"]
                    py = pack_sort[s-1]["bb"]
                if method == "PILE":
                    px = start_x - pack_sort[s]["bw"] * 0.5 + lx * 0.5
                    py = start_y - pack_sort[s]["bh"] * 0.5 + ly * 0.5

            # Move to Point
            source.Move_Point( pack_sort, s, px, py )
            source.Move_Point( pin_list, pin_index, px, py )

        # Draw
        for s in range( 0 , len( pack_sort ) ):
            pin_index = pack_sort[s]["index"]
            pin_list[pin_index]["pack"] = False
            source.Pin_Draw_QPixmap( pin_list, pin_index )

        # Finish
        pack_area = self.Report_Area( pack_sort )
        return pack_area
    def Pack_Optimal( self, source, mode, method, pack_sort, pack_other, pin_list ):
        # Variables
        ru = 5

        # Sorting List
        if method == "AREA":
            pack_sort = sorted( pack_sort, reverse=True, key = lambda entry:entry["area"] )
        if method == "PERIMETER":
            pack_sort = sorted( pack_sort, reverse=True, key = lambda entry:entry["perimeter"] )
        if method == "RATIO":
            pack_sort = sorted( pack_sort, reverse=False, key = lambda entry:entry["ratio"] )
        if method == "CLASS":
            # Variables
            ratio_0 = []
            ratio_1 = []
            ratio_2 = []
            # Sorting
            for i in range( 0, len( pack_sort ) ):
                ratio = pack_sort[i]["ratio"]
                if ratio < 1:
                    ratio_0.append( pack_sort[i] )
                if ratio == 1:
                    ratio_1.append( pack_sort[i] )
                if ratio > 1:
                    ratio_2.append( pack_sort[i] )
            pack_sort = []
            ratio_0 = sorted( ratio_0, reverse=True, key = lambda entry:entry["area"] )
            ratio_1 = sorted( ratio_1, reverse=True, key = lambda entry:entry["area"] )
            ratio_2 = sorted( ratio_2, reverse=True, key = lambda entry:entry["area"] )
            if len( ratio_0 ) >= len( ratio_2 ):
                pack_sort.extend( ratio_0 )
                pack_sort.extend( ratio_1 )
                pack_sort.extend( ratio_2 )
            else:
                pack_sort.extend( ratio_2 )
                pack_sort.extend( ratio_1 )
                pack_sort.extend( ratio_0 )

        # Variables
        start_x = min( self.List_Key( pack_sort, "bl" ) )
        start_y = min( self.List_Key( pack_sort, "bt" ) )

        # Reset Location
        for s in range( 0, len( pack_sort ) ):
            ox = start_x - pack_sort[s]["bw"]
            oy = start_y - pack_sort[s]["bh"]
            source.Move_Point( pack_sort, s, ox, oy )
            source.Move_Point( pin_list, pack_sort[s]["index"], ox, oy )
        QApplication.processEvents()

        # Variables
        points_x = list()
        points_y = list()
        grid_points = list()
        count = len( pack_sort )
        arranged = list()
        extended = list()
        extended.extend( pack_other )

        # Apply to Sort List
        for s in range( 0, count ):
            # Progress Bar
            if s % 5 == 0:
                source.ProgressBar_Value( s + 1 )
                QApplication.processEvents()
            # Stop Cycle
            if self.stop == True:
                message = "Continue Packing ?"
                loop = QMessageBox.question( QWidget(), "Imagine Board", message, QMessageBox.Yes, QMessageBox.Abort )
                if loop == QMessageBox.Abort:
                    break
                self.stop = False

            # Item
            item = pack_sort[s]
            bw = item["bw"]
            bh = item["bh"]
            pin_index = item["index"]

            # Points XY update
            if s == 0:
                # Extended
                extended = list()
                extended.extend( pack_other )
                len_ext = len( extended )

                # Grid Points
                grid_points = list()

                # Point
                px = start_x
                py = start_y
            else:
                # Lists
                psi = pack_sort[s-1]
                arranged.append( psi )
                extended.append( psi )
                len_ext = len( extended )

                # Variables
                len_grid = len( grid_points )
                end_x = max( self.List_Key( arranged, "br" ) )
                end_y = max( self.List_Key( arranged, "bb" ) )
                delta_x = end_x - start_x
                delta_y = end_y - start_y
                if delta_x >= delta_y:
                    side = delta_x
                else:
                    side = delta_y
                margin = 0.1 # enforces square when equal to zero
                square_x = start_x + side + bw * margin
                square_y = start_y + side + bh * margin

                # Control
                control = list()
                for g in range( 0, len_grid ):
                    # Grid Point with Item
                    gl = grid_points[g][0]
                    gr = gl + bw
                    gt = grid_points[g][1]
                    gb = gt + bh

                    valid = None
                    # State Delete
                    for e in range( 0, len_ext ):
                        # E Point
                        el = extended[e]["bl"]
                        er = extended[e]["br"]
                        et = extended[e]["bt"]
                        eb = extended[e]["bb"]

                        # Overlaps
                        overlap = (( round(gl,ru) >= round(el,ru) and round(gl,ru) < round(er,ru) ) and ( round(gt,ru) >= round(et,ru) and round(gt,ru) < round(eb,ru) ))
                        # Logic
                        if overlap == True:
                            valid = False
                            break
                    # State Consider Valid or None
                    if valid != False:
                        for e in range( 0, len_ext ):
                            # E Point
                            el = extended[e]["bl"]
                            er = extended[e]["br"]
                            et = extended[e]["bt"]
                            eb = extended[e]["bb"]

                            # Test Fit
                            fit = ( round(gl,ru) < round(er,ru) and round(gr,ru) > round(el,ru) ) and ( round(gt,ru) < round(eb,ru) and round(gb,ru) > round(et,ru) )
                            # Square Shape
                            if delta_x >= delta_y:square = gr >= square_x
                            else:square = gb >= square_y
                            # Contact is Valid
                            cl = ( round(gl,ru) == round(er,ru) ) and ( round(gt,ru) <= round(eb,ru) and round(gb,ru) >= round(et,ru) )
                            ct = ( round(gt,ru) == round(eb,ru) ) and ( round(gl,ru) <= round(er,ru) and round(gr,ru) >= round(el,ru) )
                            contact = cl == True or ct == True

                            # Logic
                            if fit == True or square == True:
                                valid = None
                                break
                            if contact == True:
                                valid = True

                    # Write
                    grid_points[g][2] = valid
                    if valid == True:
                        # Variables
                        box_x = ( start_x, end_x, gl, gr )
                        box_y = ( start_y, end_y, gt, gb )
                        min_x = min( box_x )
                        max_x = max( box_x )
                        min_y = min( box_y )
                        max_y = max( box_y )
                        width = abs( max_x - min_x )
                        height = abs( max_y - min_y )

                        # Calculations
                        if delta_x >= delta_y:
                            ca = gt - start_y
                            cb = gl - start_x
                            side = height
                        else:
                            ca = gl - start_x
                            cb = gt - start_y
                            side = width
                        index = g

                        # Control
                        control.append( {
                            "CA"     : ca,
                            "CB"     : cb,
                            "SIDE"   : side,
                            "INDEX"  : index,
                            } )

                # Control Sort
                k1 = "CA"
                k2 = "CB"
                sort = list()
                if len( control ) > 0:
                    # Control Selection
                    control = sorted( control, key=lambda entry:entry[k1] )
                    c0 = control[0][k1]
                    for item in control:
                        check = c0 #+ ( item["SIDE"] * 0.2 )
                        if item[k1] <= check:
                            sort.append( item )
                        else:
                            break
                    # Sort Control
                    sort = sorted( sort, key=lambda entry:entry[k2] )

                    # Variables
                    index = sort[0]["INDEX"]
                    grid_points[index][2] = False
                    # Point
                    px = grid_points[index][0]
                    py = grid_points[index][1]
                else:
                    self.stop = True
                    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( "Imagine Board | ERROR packer cycle" ) )

                # Garbage
                del control, sort

            # Grid Points with Item
            gl = px
            gr = px + bw
            gt = py
            gb = py + bh

            # Item Valid Points
            grid_points.append( [ gr, gt, None ] )
            grid_points.append( [ gl, gb, None ] )
            grid_points.append( [ gr, gb, None ] )
            if s != 0:
                points_x = [ start_x ]
                points_y = [ start_y ]
                points_x.extend( self.List_Key( extended, "br" ) )
                points_y.extend( self.List_Key( extended, "bb" ) )
                grid_points = self.Extra_Points( gl, gr, gt, gb, arranged, grid_points, start_x, start_y, source )
                del points_x, points_y

            # Deleted Invalid Grid Points
            remove = list()
            previous = list()
            for gp in grid_points:
                point = [ gp[0], gp[1] ]
                valid = gp[2]
                if ( valid == False or point in previous ):
                    remove.append( gp )
                else:
                    previous.append( point )
            for ri in remove:
                grid_points.remove( ri )
            del remove, previous

            # Move
            source.Move_Point( pack_sort, s, px, py )
            source.Move_Point( pin_list, pin_index, px, py )

            # Debug Points
            # source.p = grid_points.copy()
            # source.update()
            # QApplication.processEvents()
            # QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( str(s) ) )

        # Draw
        for s in range( 0 , count ):
            # Variables
            item = pack_sort[s]
            index = item["index"]
            px = item["bl"]
            py = item["bt"]
            # Render
            pin_list[index]["pack"] = False
            source.Pin_Draw_QPixmap( pin_list, index )

        # Finish
        area = self.Report_Area( pack_sort )
        return area

        # Garbage
        del pack_sort, pack_other, extended, grid_points

    # Support
    def List_Key( self, lista, key ):
        check = list()
        for i in lista:
            value = i[key]
            if value not in check:
                check.append( value )
        return check
    def Report_Area( self, lista ):
        # Lists
        min_x = min( self.List_Key( lista, "bl" ) )
        max_x = max( self.List_Key( lista, "br" ) )
        min_y = min( self.List_Key( lista, "bt" ) )
        max_y = max( self.List_Key( lista, "bb" ) )
        # Calculations
        w = abs( max_x - min_x )
        h = abs( max_y - min_y )
        area = w * h
        # Return
        return area
    def Extra_Points( self, gl, gr, gt, gb, arranged, grid_points, start_x, start_y, source ):
        # Variables
        pl = list(); pr = list(); pt = list(); pb = list()
        sw = list(); sh = list()
        i1 = list(); i2 = list(); i3 = list(); i4 = list()
        # Read
        lbl = self.List_Key( arranged, "bl" )
        lbr = self.List_Key( arranged, "br" )
        lbt = self.List_Key( arranged, "bt" )
        lbb = self.List_Key( arranged, "bb" )

        # Cycle
        for a in range( 0, len( arranged ) ):
            # E Point
            al = arranged[a]["bl"]
            ar = arranged[a]["br"]
            at = arranged[a]["bt"]
            ab = arranged[a]["bb"]

            # Projecting Points to Minor
            if ab <= gt:
                dist_y = gt - ab
                if gl >= al and gl <= ar:
                    pl.append( [ dist_y, gl, ab ] )
                if gr >= al and gr <= ar:
                    pr.append( [ dist_y, gr, ab ] )
            if ar <= gl:
                dist_x = gl - ar
                if gt >= at and gt <= ab:
                    pt.append( [ dist_x, ar, gt ] )
                if gb >= at and gb <= ab:
                    pb.append( [ dist_x, ar, gb ] )

            # Points to Self
            if at >= gb:
                dist_y = gb - at
                if ( al >= gl and al <= gr ):
                    px = Limit_Range( al, gl, gr )
                    py = gb
                    boolean = self.Connection_Valid( arranged, a, px, gb, px, at )
                    if boolean == True:
                        sh.append( [ dist_y, px, py ] )
                if ( ar >= gl and ar <= gr ):
                    px = Limit_Range( ar, gl, gr )
                    py = gb
                    boolean = self.Connection_Valid( arranged, a, px, gb, px, at )
                    if boolean == True:
                        sh.append( [ dist_y, px, py ] )
            if al >= gr:
                dist_x = gr - al
                if ( at >= gt and at <= gb ):
                    px = gr
                    py = Limit_Range( at, gt, gb )
                    boolean = self.Connection_Valid( arranged, a, gr, py, al, py )
                    if boolean == True:
                        sw.append( [ dist_x, px, py ] )
                if ( ab >= gt and ab <= gb ):
                    px = gr
                    py = Limit_Range( ab, gt, gb )
                    boolean = self.Connection_Valid( arranged, a, gr, py, al, py )
                    if boolean == True:
                        sw.append( [ dist_x, px, py ] )

            # Intersection Points
            if ar <= gl and ab <= gt: # top left
                dist = Trig_2D_Points_Distance( gl, gt, ar, ab )
                p = [ dist, [ gl, ab ], [ ar, gt ] ]
                i1.append( p )
            if al >= gr and ab <= gt: # top right
                dist = Trig_2D_Points_Distance( gr, gt, al, ab )
                p = [ dist, [ gr, ab ], [ al, gt ] ]
                i2.append( p )
            if ar <= gl and at >= gb: # bot left
                dist = Trig_2D_Points_Distance( gl, gb, ar, at )
                p = [ dist, [ gl, at ], [ ar, gb ] ]
                i3.append( p )
            if al >= gr and at >= gb: # bot right
                dist = Trig_2D_Points_Distance( gr, gb, al, at )
                p = [ dist, [ gr, at ], [ al, gb ] ]
                i4.append( p )

        # Sort Start
        grid_points.append( [ start_x, gb, None ] )
        grid_points.append( [ gr, start_y, None ] )
        # Sort Projected
        for lista in [ pl, pr, pt, pb ]:
            if len( lista ) > 0:
                lista.sort()
                item = lista[0]
                array = [ item[1], item[2], None ]
                grid_points.append( array )
        # Sort Self
        for lista in [ sw, sh ]:
            if len( lista ) > 0:
                lista.sort()
                for item in lista:
                    array = [ item[1], item[2], None ]
                    grid_points.append( array )
        # Sort Intersections
        for lista in [ i1, i2, i3, i4 ]:
            if len( lista ) > 0:
                lista.sort()
                item = lista[0]
                if item != 0:
                    a1 = [ item[1][0], item[1][1], None ]
                    a2 = [ item[2][0], item[2][1], None ]
                    grid_points.append( a1 )
                    grid_points.append( a2 )
        # Return
        return grid_points
    def Connection_Valid( self, lista, a, p1x, p1y, p2x, p2y ):
        # Variables
        boolean = True
        for i in range( 0, len( lista ) ):
            if i != a:
                # Read
                il = lista[i]["bl"]
                ir = lista[i]["br"]
                it = lista[i]["bt"]
                ib = lista[i]["bb"]
                # Checks
                check = ( ir > p1x and il < p2x ) and ( ib > p1y and it < p2y )
                if check == True:
                    boolean = False
                    break
        # Return
        return boolean

#endregion
#region Color Picker

class Picker_Block( QWidget ):
    SIGNAL_COLOR = QtCore.pyqtSignal( [ QColor ] )

    # Init
    def __init__( self, parent ):
        super( Picker_Block, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        self.ww = 20
        self.hh = 20
        self.qcolor = QColor( 0, 0, 0 )
    def sizeHint( self ):
        return QtCore.QSize( 50, 50 )

    # Relay
    def Set_Size( self, ww, hh ):
        self.ww = ww
        self.hh =  hh
        self.update()
    def Set_Color( self, qcolor ):
        self.qcolor = qcolor
        self.update()

    # Mouse Events
    def mousePressEvent( self, event ):
        self.SIGNAL_COLOR.emit( self.qcolor )

    # Painter
    def paintEvent( self, event ):
        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Background Hover
        r = 5
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( self.qcolor ) )
        painter.drawRoundedRect( int( 0 ), int( 0 ), int( self.ww ), int( self.hh ), r, r )

class Picker_Color_HUE( QWidget ):
    SIGNAL_COLOR = QtCore.pyqtSignal( [ QColor ] )

    # Init
    def __init__( self, parent ):
        super( Picker_Color_HUE, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 200
        self.hh = 50

        # Event
        self.ex = 0

        # Colors
        self.hsv_1 = 0 # 0-1
        self.hsv_2 = 0 # 0-1
        self.hsv_3 = 0 # 0-1
    def sizeHint( self ):
        return QtCore.QSize( 200, 50 )

    # Relay
    def Set_Color( self, qcolor ):
        # Parse
        self.hsv_1 = qcolor.hsvHueF()
        self.hsv_2 = qcolor.hsvSaturationF()
        self.hsv_3 = qcolor.valueF()
        # Cursor
        self.ex = self.hsv_1 * self.ww
        # Update
        self.update()

    # Mouse Events
    def mousePressEvent( self, event ):
        # Event
        ex = event.x()
        self.Press_Color( ex )
        # Update
        self.update()
    def mouseMoveEvent( self, event ):
        # Event
        ex = event.x()
        self.Press_Color( ex )
        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Event
        ex = event.x()
        self.Press_Color( ex )
        # Update
        self.update()
    def mouseReleaseEvent( self, event ):
        pass
    def Press_Color( self, ex ):
        # Event
        self.ex = Limit_Looper( ex, self.ww )
        # Saturation and Value
        self.hsv_1 = self.ex / self.ww
        # Emition
        qcolor = QColor().fromHsvF( self.hsv_1, self.hsv_2, self.hsv_3 )
        self.SIGNAL_COLOR.emit( qcolor )

    # Painter
    def paintEvent( self, event ):
        # Variables
        ex = int( self.ex )
        ww = int( self.ww )
        hh = int( self.hh )
        qrect = QRect( -1, -1, ww+2, hh+2 )

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Gradient Rainbow
        cor = QLinearGradient( 0, 0, ww+1, 0 )
        cor.setColorAt( 0/6, Qt.red ) # Red
        cor.setColorAt( 1/6, Qt.yellow ) # Yellow
        cor.setColorAt( 2/6, Qt.green ) # Green
        cor.setColorAt( 3/6, Qt.cyan ) # Cyan
        cor.setColorAt( 4/6, Qt.blue ) # Blue
        cor.setColorAt( 5/6, Qt.magenta ) # Magenta
        cor.setColorAt( 6/6, Qt.red ) # Color
        painter.setBrush( QBrush( cor ) )
        painter.drawRect( qrect )

        # Cursor
        cb = 3
        cbx = ex - cb
        cbw = 2 * cb
        cw = 1
        cwx = ex - cw
        cww = 2 * cw
        # Black Square
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( Qt.black ) )
        painter.drawRect( cbx, 0, cbw, hh )
        # White Square
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( Qt.white ) )
        painter.drawRect( cwx, 0, cww, hh )

        # Finish QPainter
        painter.end()

class Picker_Color_HSV( QWidget ):
    SIGNAL_COLOR = QtCore.pyqtSignal( [ QColor ] )

    # Init
    def __init__( self, parent ):
        super( Picker_Color_HSV, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 200
        self.hh = 200

        # Event
        self.ex = 0
        self.ey = 0

        # Colors
        self.hue = QColor( 255, 0, 0 )
        self.hsv_1 = 0 # 0-1
        self.hsv_2 = 0 # 0-1
        self.hsv_3 = 0 # 0-1
    def sizeHint( self ):
        return QtCore.QSize( 200, 200 )

    # Relay
    def Set_Color( self, qcolor ):
        # Parse
        hsv_1 = qcolor.hsvHueF()
        self.hsv_2 = qcolor.hsvSaturationF()
        self.hsv_3 = qcolor.valueF()
        # Hue
        hue = QColor().fromHsvF( hsv_1, 1, 1 )
        if self.hsv_2 != 0:
            self.hsv_1 = hsv_1
            self.hue = hue
        # Cursor
        self.ex = self.hsv_2 * self.ww
        self.ey = ( 1 - self.hsv_3 ) * self.hh
        # Update
        self.update()

    # Mouse Events
    def mousePressEvent( self, event ):
        # Event
        ex = event.x()
        ey = event.y()
        self.Press_Color( ex, ey )
        # Update
        self.update()
    def mouseMoveEvent( self, event ):
        # Event
        ex = event.x()
        ey = event.y()
        self.Press_Color( ex, ey )
        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Event
        ex = event.x()
        ey = event.y()
        self.Press_Color( ex, ey )
        # Update
        self.update()
    def mouseReleaseEvent( self, event ):
        pass
    def Press_Color( self, ex, ey ):
        # Event
        self.ex = Limit_Range( ex, 0, self.ww )
        self.ey = Limit_Range( ey, 0, self.hh )
        # Saturation and Value
        self.hsv_2 = self.ex / self.ww
        self.hsv_3 = ( self.hh - self.ey ) / self.hh
        # Emition
        qcolor = QColor().fromHsvF( self.hsv_1, self.hsv_2, self.hsv_3 )
        self.SIGNAL_COLOR.emit( qcolor )

    # Painter
    def paintEvent( self, event ):
        # Variables
        ex = self.ex
        ey = self.ey
        ww = self.ww
        hh = self.hh
        qrect = QRect( -1, -1, ww+2, hh+2 )

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Gradient Color
        cor = QLinearGradient( 0, 0, ww+1, 0 )
        cor.setColorAt( 0.000, Qt.white ) # White
        cor.setColorAt( 1.000, self.hue ) # Color
        painter.setBrush( QBrush( cor ) )
        painter.drawRect( qrect )
        # Gradient BW
        painter.setCompositionMode( QPainter.CompositionMode_Multiply )
        bw = QLinearGradient( 0, 0, 0, hh+1 )
        bw.setColorAt( 0.000, Qt.white ) # White Invisiable
        bw.setColorAt( 1.000, Qt.black ) # Black
        painter.setBrush( QBrush( bw ) )
        painter.drawRect( qrect )

        # Compositor Reset
        painter.setCompositionMode( QPainter.CompositionMode_SourceOver )

        # Cursor
        size = 10
        w = 2
        circle = QRectF(
            int( ex - size ),
            int( ey - size ),
            int( size * 2 ),
            int( size * 2 ),
            )
        # Mask
        mask = QPainterPath()
        mask.addEllipse( circle )
        mask.addEllipse( 
            int( ex - size + w * 2 ),
            int( ey - size + w * 2 ),
            int( size * 2 - w * 4 ),
            int( size * 2 - w * 4 ),
            )
        painter.setClipPath( mask )
        # Black Circle
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( Qt.black ) )
        painter.drawEllipse( circle )
        # White Circle
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( Qt.white ) )
        painter.drawEllipse( 
            int( ex - size + w ),
            int( ey - size + w ),
            int( size * 2 - w * 2 ),
            int( size * 2 - w * 2 ),
            )

        # Finish QPainter
        painter.end()

#endregion
#region Function

class Function_Process( QWidget ):
    SIGNAL_DROP = QtCore.pyqtSignal( list )

    # Init
    def __init__( self, parent ):
        super( Function_Process, self ).__init__( parent )
        self.Variables()
    def Variables( self ):
        # Widget
        self.ww = 500
        self.hh = 500
        self.w2 = int( self.ww * 0.5 )
        self.h2 = int( self.hh * 0.5 )
        self.side = 500
        # Colors
        self.color_1 = QColor( "#ffffff" )
        self.color_2 = QColor( "#000000" )
        # Drop Event
        self.setAcceptDrops( True )
        self.drop = False
    def sizeHint( self ):
        return QtCore.QSize( 500, 500 )

    # Relay
    def Set_Theme( self, color_1, color_2 ):
        self.color_1 = color_1
        self.color_2 = color_2
    def Set_Size( self, ww, hh ):
        self.ww = ww
        self.hh = hh
        self.w2 = ww * 0.5
        self.h2 = hh * 0.5
        if ww < hh:
            self.side = ww
        else:
            self.side = hh
        self.resize( ww, hh )

    def dragEnterEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        if event.mimeData().hasImage:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        if event.mimeData().hasImage:
            if self.drop == True:
                event.setDropAction( Qt.CopyAction )
                mime_data = Drop_Inside( self, event, True )
                self.SIGNAL_DROP.emit( mime_data )
            event.accept()
        else:
            event.ignore()
        self.drop = False
        self.update()

    # Painter
    def paintEvent( self, event ):
        # Variables
        text = "FUNCTION>>\nDROP IMAGES\nINSIDE BOX\nTO OPERATE"
        font = "Consolas"
        letter_size = 10

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Bounding Box
        box = QRect( int( 0 ), int( 0 ), int( self.ww ), int( self.hh ) )

        # Background Hover
        painter.setBrush( QtCore.Qt.NoBrush )
        painter.setPen( QPen( self.color_1, 1, Qt.DashLine ) )
        painter.drawRect( box )

        # String
        painter.setBrush( QtCore.Qt.NoBrush )
        painter.setPen( QPen( self.color_1, 1, Qt.SolidLine ) )
        qfont = QFont( font )
        qfont.setPointSizeF( letter_size )
        painter.setFont( qfont )
        painter.drawText( box, Qt.AlignCenter, text )

        # Triangle
        if self.drop == True:
            Painter_Triangle( self, painter, self.w2, self.h2, self.side )

        # Finish QPainter
        painter.end()

#endregion
