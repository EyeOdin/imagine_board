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
import re
import os
import copy
import math
import time
import zipfile
import subprocess
import webbrowser
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Plugin Modules
from .imagine_board_constants import *
from .imagine_board_calculations import *

#endregion


#region Shared Function

# Icons
def Style_Icon( self ):
    scale = 100
    ki = Krita.instance()
    self.qicon_img  = ki.icon( "document-new" ) # Static
    self.qicon_anim = ki.icon( "layer-animated" ) # Animated
    self.qicon_comp = ki.icon( "bundle_archive" ) # Compressed
    self.qicon_dir  = ki.icon( "document-open" ) # Directory
    self.qicon_web  = ki.icon( "download" ) # Internet
    self.qicon_comp = Style_Crop( self.qicon_comp, 16, 0, 0, 16, 16, scale )
    self.qicon_dir  = Style_Crop( self.qicon_dir, 22, 3, 3, 16, 16, scale )
def Style_Crop( qicon, os, px, py, pw, ph, s ):
    # Icons are 16x16 originally even those with margin
    pix = qicon.pixmap( int( os * s ), int( os * s ), QIcon.Normal, QIcon.On )
    pix = pix.copy( int( px * s ), int( py * s ), int( pw * s ), int( ph * s ) )
    qicon = QIcon( pix )
    return qicon

# Item
def Item_QImageReader( reader, width, height, state_fit ):
    # Variables
    qpixmap = None
    # Image Fit
    grid_fit = Information_Fit( state_fit )
    # QImageReader Transform
    reader.setAutoTransform( True )
    qsize = reader.size()
    qsize_valid = qsize.isValid()
    if qsize_valid == True: # no scale method, only smooth
        scale = QSize( width, height )
        qsize.scale( scale, grid_fit )
        reader.setScaledSize( qsize )
        qpixmap = QPixmap().fromImageReader( reader )
    return qpixmap
def Item_QImage( qimage, width, height, grid_fit, scale_method ):
    qimage = qimage.scaled( int( width ), int( height ), grid_fit, scale_method  )
    return qimage
def Item_QPixmap( qpixmap, width, height, grid_fit, scale_method ):
    qpixmap = qpixmap.scaled( int( width ), int( height ), grid_fit, scale_method  )
    return qpixmap
def Item_Size( width, height, depth ):
    size_bytes = ( width * height * depth ) / 8
    size_mb = size_bytes / 1024 / 1024
    return size_mb
def Item_Rotate( rotate, width, height ):
    if rotate == True:  rot_width, rot_height = height, width
    else:               rot_width, rot_height = width, height
    return rot_width, rot_height
def Item_Icon( qicon, width, height ):
    mini = min( width, height )
    margin = int( mini * 0.1 )
    side = int( mini - margin )
    ico_qpixmap = qicon.pixmap( side, side, QIcon.Normal, QIcon.On )
    ico_size = Item_Size( ico_qpixmap.width(), ico_qpixmap.height(), ico_qpixmap.depth() )
    return ico_qpixmap, ico_size

# Fit
def Fit_Image( reader, width, height, state_fit ):
    size = 0
    rotate = Information_Orientation( reader )
    width, height = Item_Rotate( rotate, width, height )
    qpixmap = Item_QImageReader( reader, width, height, state_fit )
    if qpixmap != None:
        size = Item_Size( width, height, qpixmap.depth() )
    return qpixmap, size
def Fit_QPixmap( qpixmap, width, height, state_fit, grid_method ):
    grid_fit = Information_Fit( state_fit )
    qpixmap = Item_QPixmap( qpixmap, width, height, grid_fit, grid_method )
    size = Item_Size( qpixmap.width(), qpixmap.height(), qpixmap.depth() )
    return qpixmap, size
def Fit_Compressed( url, width, height, state_fit ):
    # Variables
    side = min( width, height )
    pk = 0.8
    pw = int( side * pk )
    ph = int( side * pk )
    # Defaults
    qpixmap = QPixmap( int( pw ), int( ph ) )
    qpixmap.fill( Qt.transparent )
    size = 0
    # Archive
    archive = zipfile.ZipFile( url, "r" )
    if url.endswith( file_krita ) == True: # KRA KRZ ORA Bundle
        if url.endswith( "bundle" ):    find = preview_png
        else:                           find = merged_png
        buffer = Compressed_Buffer( archive, find )
        reader = QImageReader( buffer )
        if reader.canRead():
            qpixmap, size = Fit_Image( reader, width, height, state_fit )
    else: # ZIP file ( icon )
        comp_path = list()
        name_list = archive.namelist()
        for name in name_list:
            basename = os.path.basename( name )
            extension = basename.split( "." )[-1]
            if extension in file_search:
                comp_path.append( name )
        count = len( comp_path )
        if count > 0:
            comp_order = Compressed_Sort( comp_path )
            for name in comp_order:
                buffer = Compressed_Buffer( archive, name )
                reader = QImageReader( buffer )
                if reader.canRead():
                    qpixmap, size = Stretch_Icon( reader, pw, ph )
                    break
    # Return
    return qpixmap, size
def Fit_Directory( url, width, height ):
    # Variables
    side = min( width, height )
    pw = int( side * 0.8 )
    ph = int( side * 0.58 )
    # Defaults
    qpixmap = QPixmap( int( pw ), int( ph ) )
    qpixmap.fill( Qt.transparent )
    size = 0
    # Directory
    qdir = QDir()
    qdir.setPath( url )
    qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
    qdir.setNameFilters( file_normal )
    # Files
    it = QDirIterator( qdir, QDirIterator.NoIteratorFlags )
    while it.hasNext():
        reader = QImageReader( it.next() )
        if reader.canRead():
            qpixmap, size = Stretch_Icon( reader, pw, ph )
            break
    del qdir, it
    return qpixmap, size
# Stretch
def Stretch_Icon( reader, width, height ):
    reader.setAutoTransform( True )
    qpixmap = QPixmap().fromImageReader( reader )
    qpixmap = qpixmap.scaled( int( width ), int( height ), Qt.IgnoreAspectRatio, Qt.FastTransformation  )
    size = Item_Size( qpixmap.width(), qpixmap.height(), qpixmap.depth() )
    return qpixmap, size

# Painter
def Painter_Triangle( painter, w2, h2, side, qcolor ):
    # Painter
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( qcolor ) )
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
def Painter_Locked( painter, w2, h2, side, qcolor ):
    # Painter
    painter.setPen( QtCore.Qt.NoPen )
    painter.setBrush( QBrush( qcolor) )
    # Variables
    kw = 0.3 * side
    kh = 0.2 * side
    d = 0.2
    # Polygons
    bar1 = QPolygon( [
        QPoint( int( w2 - kw ),     int( h2 - kh ) ),
        QPoint( int( w2 - kw * d ), int( h2 - kh ) ),
        QPoint( int( w2 - kw * d ), int( h2 + kh ) ),
        QPoint( int( w2 - kw ),     int( h2 + kh ) ),
        ] )
    bar2 = QPolygon( [
        QPoint( int( w2 + kw ),     int( h2 - kh ) ),
        QPoint( int( w2 + kw * d ), int( h2 - kh ) ),
        QPoint( int( w2 + kw * d ), int( h2 + kh ) ),
        QPoint( int( w2 + kw ),     int( h2 + kh ) ),
        ] )
    bar = bar1.united( bar2 )
    painter.drawPolygon( bar )
# Cursor Icon
def Icon_Display( name ):
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
def Icon_Cursor( state_pickcolor, state_press ):
    if ( state_pickcolor == True and state_press == True ):
        QApplication.setOverrideCursor( Qt.CrossCursor )
    else:
        QApplication.restoreOverrideCursor()
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
        red   = pixel.redF()
        green = pixel.greenF()
        blue  = pixel.blueF()

        # Apply Color
        if self.pigmento_picker != None:
            if state_press == True:
                cor = self.pigmento_picker.API_Input_Preview( "SRGB", red, green, blue, 0 )
            if state_press == False:
                cor = self.pigmento_picker.API_Input_Apply( "SRGB", red, green, blue, 0 )
            red     = cor[ "srgb_1" ]
            green   = cor[ "srgb_2" ]
            blue    = cor[ "srgb_3" ]
            display = cor[ "display" ]
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
            try:
                clip_board = QApplication.clipboard()
                clip_board.clear()
                clip_board.setText( str( hex_code ) )
            except:
                pass
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

# File
def File_Open_Location( url ):
    # Variables
    kernel = str( QSysInfo.kernelType() ) # winnt=WINDOWS, linux=LINUX, darwin=MAC
    check_file = os.path.isfile( url )
    check_dir = os.path.isdir( url )
    check_web = Check_Html( url )
    # Logic
    if check_file == True and kernel == "winnt": # Windows
        url = os.path.normpath( url )
        file_browser_url = os.path.join( os.getenv( 'WINDIR' ), 'explorer.exe' )
        subprocess.run( [ file_browser_url, '/select,', url ] )
        Message_Log( "FILE LOCATION", f"{ url }" )
    elif check_file == True and kernel in [ linux, darwin ]:
        url = os.path.normpath( url )
        dirname = os.path.dirname( url )
        QDesktopServices.openUrl( QUrl.fromLocalFile( dirname ) )
        Message_Log( "FILE LOCATION", f"{ dirname }" )
    elif check_dir:
        QDesktopServices.openUrl( QUrl.fromLocalFile( url ) )
        Message_Log( "DIRECTORY", f"{ url }" )
    elif check_web:
        webbrowser.open_new( url )
        Message_Log( "WEB", f"{ url }" )
    else:
        Message_Log( "ERROR", "not able to access location" )
def File_Copy_Path( url ):
    url = os.path.normpath( url )
    clipboard = QApplication.clipboard()
    clipboard.clear()
    clipboard.setText( url )
    Message_Log( "COPY PATH", f"{ url }" )
def File_Copy_Image( url ):
    url = os.path.normpath( url )
    qpixmap = QPixmap( url )
    mimedata = Create_Mime_Data( [ url ], qpixmap )
    clipboard = QApplication.clipboard()
    clipboard.clear()
    clipboard.setMimeData( mimedata )
    Message_Log( "COPY IMAGE", f"{ url }" )

# Checks
def Check_Insert():
    doc = Krita.instance().documents()
    check_insert = len( doc ) > 0
    return check_insert
def Check_Vector( url ):
    try:    check_vector = os.path.basename( url ).endswith( ( ".svg", ".svgz" ) )
    except: check_vector = False
    return check_vector

# Insert
def Insert_Document( self, image_url, clip ):
    check_exists = os.path.exists( image_url )
    check_file = os.path.exists( image_url )
    if check_exists == True and check_file == True:
        try:
            # Create Document
            ki = Krita.instance()
            document = ki.openDocument( image_url )
            Application.activeWindow().addView( document )
            width = document.width()
            height = document.height()
            # Crop
            if clip["cstate"] == True:
                ad = Krita.instance().activeDocument()
                ad.crop( int( width * clip["cl"] ), int( height * clip["ct"] ), int( width * clip["cw"] ), int( height * clip["ch"] ) )
                ad.waitForDone()
                ad.refreshProjection()
                ki.action('reset_display').trigger()
            # Show Message
            Message_Float( "INSERT", "New Document", "document-new" )
        except Exception as e:
            Message_Error( e )
    else:
        Message_Error()
def Insert_Layer( self, image_url, clip ):
    check_exists = os.path.exists( image_url )
    check_file = os.path.exists( image_url )
    check_insert = Check_Insert()
    if check_exists == True and check_file == True and check_insert == True:
        check_vector = Check_Vector( image_url )
        if check_vector == True:
            Embed_Layer_Vector( self, image_url )
        else:
            Embed_Layer_Pixel( self, image_url, clip )
    else:
        Message_Error()
def Insert_Reference( self, image_url, clip ):
    check_exists = os.path.exists( image_url )
    check_file = os.path.exists( image_url )
    check_insert = Check_Insert()
    if check_exists == True and check_file == True and check_insert == True:
        Embed_Reference_Pixel( self, image_url, clip )
    else:
        Message_Error()
def Insert_Drag( self, image_url, clip, grid ):
    check_file = os.path.isfile( image_url )
    check_dir = os.path.isdir( image_url )
    if check_file == True and check_dir == False:
        # List Construct
        lista = [ image_url ] # first element on the list
        if grid == True:
            selection_list = self.Selection_List()
            count = len( selection_list )
            for url in selection_list:
                if url not in lista:
                    lista.append( url )
        # Process
        if len( lista ) > 0:
            # Variable
            self.drag = True
            # Pixmap
            if os.path.isfile( lista[0] ):
                qpixmap = Create_Image_Clip( self, lista[0], clip )
            elif Check_Html( lista[0] ):
                qpixmap = Download_QPixmap( lista[0] )
            # Mimedata
            for item in lista:
                if os.path.isfile( image_url ):
                    check_vector = Check_Vector( image_url )
                    if check_vector == True:
                        svg_shape = ""
                        file_item = open( image_url, "r", encoding=encode )
                        for line in file_item:
                            svg_shape += line
                        if svg_shape != "":
                            mimedata = Create_Mime_Data( svg_shape, qpixmap )
                    else:
                        mimedata = Create_Mime_Data( lista, qpixmap )
                elif Check_Html( image_url ):
                    mimedata = Create_Mime_Data( lista, qpixmap )
            # Drag
            Create_Thumbnail( self, qpixmap, mimedata )
def Insert_Drop( self, event ):
    # Mimedata
    mimedata = event.mimeData()
    format_id = mimedata.hasFormat( drag_id )

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
    mime_data = list()
    if ( has_text == True and has_html == True ):
        regex = r' src="(.*?)\" ' # Finds the "src" hyperlink in html
        match = re.findall( regex, data_html )
        for html in match:
            mime_data.append( html )
        if data_text in mime_data or len( mime_data ) == 0:
            mime_data = [ data_text ]
    elif ( has_text == True and has_html == False ):
        for url in data_urls:
            url = url.toLocalFile()
            mime_data.append( url )
    # Sort
    if len( mime_data ) > 0:
        mime_data.sort()
    # Return
    return mime_data, format_id
# Embed
def Embed_Layer_Vector( self, image_url ):
    try:
        # Variables
        basename = os.path.basename( image_url )
        # Read SVG
        svg_shape = ""
        file_item = open( image_url, "r", encoding="UTF-8" )
        for line in file_item:
            svg_shape += line
        # Create Layer
        ad = Krita.instance().activeDocument()
        rn = ad.rootNode()
        vl = ad.createVectorLayer( basename )
        rn.addChildNode( vl, None )
        # Input Shape to Layer
        vl.addShapesFromSvg( svg_shape )
        # Message
        Message_Float( "INSERT", "Layer Vector", "vectorLayer" )
    except Exception as e:
        Message_Error( e )
def Embed_Layer_Pixel( self, image_url, clip ):
    try:
        # Qimage
        qpixmap = Create_Image_Clip( self, image_url, clip )
        qimage = qpixmap.toImage()
        ptr = qimage.constBits()
        ptr.setsize( qimage.byteCount() )
        # Create Layer
        basename = os.path.basename( image_url )
        ad = Krita.instance().activeDocument()
        rn = ad.rootNode()
        pl = ad.createNode( basename, "paintLayer" )
        pl.setPixelData( bytes( ptr.asarray() ), 0, 0, qimage.width(), qimage.height() )
        rn.addChildNode( pl, None )
        ad.refreshProjection()
        # Message
        Message_Float( "INSERT", "Layer Pixel", "paintLayer" )
    except Exception as e:
        Message_Error( e )
def Embed_Reference_Pixel( self, image_url, clip ):
    try:
        # Image
        qpixmap = Create_Image_Clip( self, image_url, clip )
        mimedata = Create_Mime_Data( image_url, qpixmap )
        clipboard = QApplication.clipboard().setMimeData( mimedata )
        # Place Image
        ki = Krita.instance()
        ki.action( 'paste_as_reference' ).trigger()
        ad = ki.activeDocument()
        ad.waitForDone()
        ad.refreshProjection()
        # Message
        Message_Float( "INSERT", "Reference", "krita_tool_reference_images" )
    except Exception as e:
        Message_Error( e )
# Create
def Create_Image_Clip( self, image_url, clip ):
    # Default
    qpixmap = QPixmap( 1, 1 )
    qpixmap.fill( Qt.transparent )
    # Reader
    reader = QImageReader( image_url )
    reader.setAutoTransform( True )
    if reader.canRead() == True:
        # Crop
        if clip["cstate"] == True:
            qsize = reader.size()
            width = qsize.width()
            height = qsize.height()
            cl = clip["cl"]
            ct = clip["ct"]
            cw = clip["cw"]
            ch = clip["ch"]
            qrect = QRect( int( width * cl ), int( height * ct ), int( width * cw ), int( height * ch ) )
            reader.setClipRect( qrect )
        qpixmap = QPixmap().fromImageReader( reader )
        # Scale
        ad = Krita.instance().activeDocument()
        if self.insert_original_size == False and ad != None:
            qpixmap = qpixmap.scaled( ad.width(), ad.height(), Qt.KeepAspectRatio, self.scale_method )
    return qpixmap
def Create_Mime_Data( lista, qpixmap ):
    mime_list = list()
    mimedata = QMimeData()
    if Check_Html( lista[0] ):
        mime_data.append( lista[0] )
        mimedata.setHtml( lista[0] )
    else:
        for url in lista:
            if os.path.isfile( url ):
                qurl = QUrl().fromLocalFile( url )
                mime_list.append( qurl )
        mimedata.setUrls( mime_list )
    mime_string = str( mime_list )
    mimedata.setText( mime_string )
    mimedata.setData( drag_id, mime_string.encode( encode ) )
    mimedata.setImageData( qpixmap )
    return mimedata
def Create_Thumbnail( self, qpixmap, mimedata ):
    # Display
    size = 200
    if qpixmap.isNull() == False:
        qpixmap = qpixmap.scaled( size, size, Qt.KeepAspectRatio, Qt.FastTransformation )
    # Variables
    ww = int( qpixmap.width() * 0.5 )
    hh = int( qpixmap.height() * 0.5 )
    # Drag
    drag = QDrag( self )
    drag.setHotSpot( QPoint( ww, hh ) )
    drag.setMimeData( mimedata )
    drag.setPixmap( qpixmap )
    drag.exec_( Qt.CopyAction )

# Information
def Information_Format( value ):
    image_format = None
    if   value == 0:  image_format = "Invalid"
    elif value == 1:  image_format = "Mono"
    elif value == 2:  image_format = "MonoLSB"
    elif value == 3:  image_format = "Indexed8"
    elif value == 4:  image_format = "RGB32"
    elif value == 5:  image_format = "ARGB32"
    elif value == 6:  image_format = "ARGB32_Premultiplied"
    elif value == 7:  image_format = "RGB16"
    elif value == 8:  image_format = "ARGB8565_Premultiplied"
    elif value == 9:  image_format = "RGB666"
    elif value == 10: image_format = "ARGB6666_Premultiplied"
    elif value == 11: image_format = "RGB555"
    elif value == 12: image_format = "ARGB8555_Premultiplied"
    elif value == 13: image_format = "RGB888"
    elif value == 14: image_format = "RGB444"
    elif value == 15: image_format = "ARGB4444_Premultiplied"
    elif value == 16: image_format = "RGBX8888"
    elif value == 17: image_format = "RGBA8888"
    elif value == 18: image_format = "RGBA8888_Premultiplied"
    elif value == 19: image_format = "BGR30"
    elif value == 20: image_format = "A2BGR30_Premultiplied"
    elif value == 21: image_format = "RGB30"
    elif value == 22: image_format = "A2RGB30_Premultiplied"
    elif value == 23: image_format = "Alpha8"
    elif value == 24: image_format = "Grayscale8"
    elif value == 28: image_format = "Grayscale16"
    elif value == 25: image_format = "RGBX64"
    elif value == 26: image_format = "RGBA64"
    elif value == 27: image_format = "RGBA64_Premultiplied"
    elif value == 29: image_format = "BGR888"
    elif value == 30: image_format = "RGBX16FPx4"
    elif value == 31: image_format = "RGBA16FPx4"
    elif value == 32: image_format = "RGBA16FPx4_Premultiplied"
    elif value == 33: image_format = "RGBX32FPx4"
    elif value == 34: image_format = "RGBA32FPx4"
    elif value == 35: image_format = "RGBA32FPx4_Premultiplied"
    elif value == 36: image_format = "CMYK8888"
    return image_format
def Information_Fit( boolean ):
    if   boolean == True:    fit = Qt.KeepAspectRatio
    elif boolean == False:   fit = Qt.KeepAspectRatioByExpanding
    return fit
def Information_Orientation( reader ):
    """
    QImageIOHandler.TransformationNone
    QImageIOHandler.TransformationMirror
    QImageIOHandler.TransformationFlip
    QImageIOHandler.TransformationRotate180
    QImageIOHandler.TransformationRotate90
    QImageIOHandler.TransformationMirrorAndRotate90
    QImageIOHandler.TransformationFlipAndRotate90
    QImageIOHandler.TransformationRotate270
    """
    rotate = False
    rt = reader.transformation()
    if rt == QImageIOHandler.TransformationRotate90:            rotate = True
    if rt == QImageIOHandler.TransformationFlipAndRotate90:     rotate = True
    if rt == QImageIOHandler.TransformationRotate270:           rotate = True
    return rotate

# Pigment.O
def Color_Analyse( pigmento_picker, qimage ):
    if ( pigmento_picker != None and qimage.isNull() == False ):
        report = pigmento_picker.API_Image_Analyse( qimage )
        Message_Log( "ANALYSE", f"{ report }" )
    else:
        Message_Log( "ERROR", "Pigment.O Picker not accessible" )
def Color_LUT_to_Image( pigmento_sampler, list_url ):
    if pigmento_sampler != None:
        report = pigmento_sampler.API_LUT_to_Image( list_url )
        Message_Log( "LUT to IMAGE", f"{ report }" )
    else:
        Message_Log( "ERROR", "Pigment.O Sampler not accessible" )

#endregion
#region Panels

class ImagineBoard_Preview( QtWidgets.QWidget ):
    # General
    PREVIEW_PARENT = QtCore.pyqtSignal()
    PREVIEW_LOAD = QtCore.pyqtSignal( str, str, int )
    PREVIEW_MODE = QtCore.pyqtSignal( int, bool )
    PREVIEW_DROP = QtCore.pyqtSignal( list )
    PREVIEW_INCREMENT = QtCore.pyqtSignal( int )
    # Menu
    PREVIEW_PIN_INSERT = QtCore.pyqtSignal( str, float, float, str, str, dict )
    PREVIEW_RANDOM = QtCore.pyqtSignal()
    PREVIEW_FULL_SCREEN = QtCore.pyqtSignal( bool )
    # UI
    PREVIEW_PC_VALUE = QtCore.pyqtSignal( int )
    PREVIEW_PC_MAX = QtCore.pyqtSignal( int )
    PREVIEW_PB_VALUE = QtCore.pyqtSignal( int )
    PREVIEW_PB_MAX = QtCore.pyqtSignal( int )

    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Preview, self ).__init__( parent )
        self.Variables()
    def sizeHint( self ):
        return QtCore.QSize( 500,500 )

    # Variables
    def Variables( self ):
        # Widget
        self.ww = 1
        self.hh = 1
        self.w2 = 0.5
        self.h2 = 0.5
        self.state_maximized = False
        # Event
        self.ox = 0
        self.oy = 0
        self.ex = 0
        self.ey = 0
        # Interaction
        self.operation = None

        # State General
        self.state_maximized = False
        self.state_press = False
        self.state_pickcolor = False
        # State Preview
        self.state_original = False
        # State Overlay
        self.state_clip = False
        self.state_gridline = False
        self.state_underlayer = False
        self.state_information = False

        # Preview
        self.preview_url = None
        self.preview_qpixmap = None
        self.preview_state = None # None "FILE" "ANIM" "COMP" "DIR" "WEB"
        # Read
        self.preview_color_name = QColor( "#bfbfbf" )
        self.preview_format = None
        self.preview_image_format = None
        self.preview_text = None
        self.preview_dpr = None
        # Animation
        self.anim_sequence = list() # list of qpixmaps
        self.anim_frame = 0
        self.anim_count = 0
        self.anim_rate = 33
        self.anim_play = False # self.anim_timer.isActive()
        self.Anim_Timer()
        # Compact
        self.comp_archive = None
        self.comp_path = list() # list of paths inside the zip file
        self.comp_index = 0
        self.comp_count = 0

        # Grid Lines
        self.gridline_x = 3
        self.gridline_y = 3
        # Information
        self.info_edge = 160

        # Colors
        self.c_lite = QColor( "#ffffff" )
        self.c_dark = QColor( "#000000" )
        self.c_chrome = QColor( "#3daee9" )
        self.c_text = QColor( "#ffffff" )
        self.transparent = QColor( 0, 0, 0, 0 )
        self.underlayer_color = QColor( "#7f7f7f" )
        # Color Picker
        self.pigmento_picker = None
        self.pigmento_sampler = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # Edit
        self.edit_greyscale = False
        self.edit_invert_x = False
        self.edit_invert_y = False

        # Clip
        self.clip_node = None
        self.clip_l = 0.1  # 0-1
        self.clip_t = 0.1  # 0-1
        self.clip_r = 0.9  # 0-1
        self.clip_b = 0.9  # 0-1
        self.clip_w = self.clip_r - self.clip_l
        self.clip_h = self.clip_b - self.clip_t
        self.clip_image = { 
            "cstate" : self.state_clip,
            "cl": self.clip_l,
            "ct": self.clip_t,
            "cw": self.clip_w,
            "ch": self.clip_h,
            }
        # Draw
        self.draw_px = 0
        self.draw_py = 0
        self.draw_width = 1
        self.draw_height = 1

        # System
        self.insert_original_size = False
        self.scale_method = Qt.SmoothTransformation

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False

    # Relay
    def Set_Pigment_O( self, pigmento_picker, pigmento_sampler ):
        self.pigmento_picker = pigmento_picker
        self.pigmento_sampler = pigmento_sampler
    def Set_Theme( self, c_lite, c_dark, c_chrome, c_text ):
        self.c_lite = QColor( c_lite )
        self.c_dark = QColor( c_dark )
        self.c_chrome = QColor( c_chrome )
        self.c_text = QColor( c_text )
        Style_Icon( self )
        self.update()
    def Set_Size( self, ww, hh, state_maximized ):
        # Variables
        self.ww = ww
        self.hh = hh
        self.w2 = ww * 0.5
        self.h2 = hh * 0.5
        self.state_maximized = state_maximized
        self.resize( ww, hh )
        # Icons
        self.qpixmap_dir, self.dir_size = Item_Icon( self.qicon_dir, self.ww, self.hh )
        if self.preview_state == "DIR":
            self.preview_qpixmap, size = Fit_Directory( self.preview_url, self.ww, self.hh )
        # Update
        self.update()
    def Set_ColorPicker( self, boolean ):
        self.state_pickcolor = boolean 
        self.update()
    def Set_Insert_Original_Size( self, boolean ):
        self.insert_original_size = boolean
        self.update()
    def Set_Gridline_Division( self, gridline_x, gridline_y ):
        self.gridline_x = gridline_x
        self.gridline_y = gridline_y
        self.update()
    def Set_Gridline_State( self, boolean ):
        self.state_gridline = boolean
        self.update()
    def Set_Underlayer_Color( self, underlayer_color ):
        self.underlayer_color = QColor( underlayer_color )
        self.update()
    def Set_Underlayer_State( self, boolean ):
        self.state_underlayer = boolean
        self.update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()

    # Display
    def Preview_Reset( self ):
        # Variables
        self.state_clip = False
        # Functions
        self.Edit_Reset()
        self.Camera_Reset()
        self.Anim_Pause()
    def Preview_Path( self, preview_url, preview_state, update ):
        if self.preview_url != preview_url and preview_state != None or update == True:
            # Reset
            self.Preview_Reset()
            self.PREVIEW_PC_VALUE.emit( 0 )
            # Variables
            self.preview_url = preview_url
            self.preview_state = preview_state

            # Reader
            reader = QImageReader( preview_url )
            # Infomation
            self.preview_format = reader.format()
            self.preview_image_format = Information_Format( reader.imageFormat() )
            qcolor = reader.backgroundColor()
            self.preview_color_name = qcolor.name( QColor.HexArgb )
            # Meta Data
            preview_text = list()
            text_keys = reader.textKeys()
            if metadata_key in text_keys:
                index = text_keys.index( metadata_key )
                text_keys.pop( index )
                text_keys.insert( 0, metadata_key )
            for key in text_keys:
                text = reader.text( key )
                preview_text.append( ( key, text ) )
            self.preview_text = preview_text

            # Variables
            qpixmap = None
            # QPixmap
            if preview_state in [ "FILE", "IMG" ]:
                reader.setAutoTransform( True )
                qpixmap = QPixmap().fromImageReader( reader )
                if qpixmap.isNull() == True:
                    qpixmap = None
                self.PREVIEW_PC_MAX.emit( 1 )
            elif preview_state == "ANIM":
                # Read
                anim_sequence = list()
                anim_rate = list()
                frames = reader.imageCount()
                for i in range( 0, frames ):
                    reader.jumpToImage( i )
                    qpixmap = QPixmap().fromImageReader( reader )
                    if qpixmap.isNull() == False:
                        anim_sequence.append( qpixmap )
                        anim_rate.append( reader.nextImageDelay() )
                anim_mean = Stat_Mean( anim_rate )
                # Animation Variables
                if len( anim_sequence ) > 0:
                    qpixmap = anim_sequence[0]
                    if qpixmap.isNull() == True:
                        qpixmap = None
                    self.anim_sequence = anim_sequence
                    self.anim_frame = 0
                    self.anim_count = frames - 1
                    self.anim_rate = anim_mean
                self.PREVIEW_PC_MAX.emit( self.anim_count )
            elif preview_state == "COMP":
                # Open Archive
                comp_path = list()
                self.comp_archive = zipfile.ZipFile( preview_url, "r" )
                name_list = self.comp_archive.namelist()
                for name in name_list:
                    basename = os.path.basename( name )
                    extension = basename.split( "." )[-1]
                    if extension in file_search:
                        comp_path.append( name )
                # Com Variables
                if len( comp_path ) > 0:
                    # Krita Cover Image
                    comp_path = Compressed_Sort( comp_path )
                    check_kra = self.preview_url.endswith( file_krita )
                    check_merge = merged_png in comp_path
                    check_preview = preview_png in comp_path
                    if check_kra and check_preview == True:
                        index = comp_path.index( preview_png )
                        comp_path.insert( 0, comp_path.pop( index ) )
                    if check_kra and check_merge == True:
                        index = comp_path.index( merged_png )
                        comp_path.insert( 0, comp_path.pop( index ) )
                    # Archive
                    qpixmap = Compressed_QPixmap( self.comp_archive, comp_path[0] )
                    self.comp_path = comp_path
                    self.comp_index = 0
                    self.comp_count = len( comp_path ) - 1
                self.PREVIEW_PC_MAX.emit( self.comp_count )
            elif preview_state == "PDF":
                self.Preview_Default()
            elif preview_state == "DIR":
                qpixmap, size = Fit_Directory( preview_url, self.ww, self.hh )
                self.PREVIEW_PC_MAX.emit( 1 )
            elif preview_state == "WEB":
                qpixmap = Download_QPixmap( preview_url )
                self.PREVIEW_PC_MAX.emit( 1 )
            # Variables
            self.preview_qpixmap = qpixmap

            # Activate
            if preview_state == "ANIM" and self.anim_count > 0:
                self.Anim_Play()
            if preview_state == "COMP" and self.comp_count > 0:
                self.Comp_Index( 0 )
        # Update
        self.update()
        self.Camera_Grab()
    def Preview_QPixmap( self, url, qpixmap ):
        if qpixmap.isNull() == False:
            # Reset
            self.Preview_Reset()
            # Variables
            self.preview_state = "WEB"
            self.preview_url = url
            self.preview_qpixmap = qpixmap
        # Update
        self.update()
        self.Camera_Grab()
    def Preview_QImage( self, url, qimage ):
        if qimage.isNull() == False:
            # Reset
            self.Preview_Reset()
            # Variables
            self.preview_state = "WEB"
            self.preview_url = url
            self.preview_qpixmap = QPixmap().fromImage( qimage )
        # Update
        self.update()
        self.Camera_Grab()
    def Preview_Default( self ):
        # Reset
        self.Preview_Reset()
        # Variables
        self.preview_state = None
        self.preview_url = None
        self.preview_qpixmap = None
        self.anim_sequence = None
        self.comp_archive = None
        self.comp_path = None
        # Signals
        self.PREVIEW_PC_VALUE.emit( 0 )
        self.PREVIEW_PC_MAX.emit( 1 )
        # Update
        self.update()
        self.Camera_Grab()

    # Animation
    def Anim_Timer( self ):
        self.anim_timer = QtCore.QTimer( self )
        self.anim_timer.timeout.connect( lambda: self.Anim_Increment( +1 ) )
        self.anim_timer.stop()
    def Anim_Increment( self, increment ):
        if self.preview_state == "ANIM":
            self.anim_frame = Limit_Loop( int( self.anim_frame + increment ), self.anim_count )
            self.preview_qpixmap = self.anim_sequence[ self.anim_frame ]
            self.PREVIEW_PC_VALUE.emit( self.anim_frame )
            self.update()
    def Anim_Play( self ):
        if self.preview_state == "ANIM":
            self.anim_play = True
            self.anim_timer.start( int( self.anim_rate ) )
    def Anim_Pause( self ):
        try:
            self.anim_play = False
            self.anim_timer.stop()
        except:
            pass
    def Anim_Back( self ):
        if ( self.preview_state == "ANIM" and self.anim_play == False ):
            self.Anim_Increment( -1 )
    def Anim_Forward( self ):
        if ( self.preview_state == "ANIM" and self.anim_play == False ):
            self.Anim_Increment( +1 )
    def Anim_Frame( self, frame ):
        if self.preview_state == "ANIM":
            self.anim_frame = Limit_Loop( int( frame ), self.anim_count )
            self.preview_qpixmap = self.anim_sequence[ self.anim_frame ]
            self.PREVIEW_PC_VALUE.emit( self.anim_frame )
            self.update()

    # Compressed
    def Comp_Back( self ):
        if self.preview_state == "COMP":
            self.Comp_Index( self.comp_index - 1 )
    def Comp_Forward( self ):
        if self.preview_state == "COMP":
            self.Comp_Index( self.comp_index + 1 )
    def Comp_Index( self, comp_index ):
        if self.preview_state == "COMP":
            self.comp_index = Limit_Range( comp_index, 0, self.comp_count )
            self.preview_qpixmap = Compressed_QPixmap( self.comp_archive, self.comp_path[ self.comp_index ] )
            self.PREVIEW_PC_VALUE.emit( comp_index ) # values is out of range, it is fixed outside
            self.update()

    # Camera
    def Camera_Reset( self ):
        self.pcam_x = 0
        self.pcam_y = 0
        self.pcam_z = 1
        self.pcam_r = 0
        self.cam_x = 0 # Moxe X
        self.cam_y = 0 # Move Y
        self.cam_z = 1 # Zoom
        self.cam_r = 0 # Rotate
        self.cam_m = 15
    def Camera_Previous( self ):
        self.pcam_x = self.cam_x
        self.pcam_y = self.cam_y
        self.pcam_r = self.cam_r
        self.pcam_z = self.cam_z
    def Camera_Move( self, ex, ey ):
        if self.cam_z != 0:
            self.cam_x = self.pcam_x + ( ( ex - self.ox ) / self.cam_z )
            self.cam_y = self.pcam_y + ( ( ey - self.oy ) / self.cam_z )
    def Camera_Swap( self, ex, ey ):
        dx = ex - self.ox
        dy = ey - self.oy
        if abs( dx ) > self.cam_m and abs( dx ) > abs( dy ):
            self.ox = ex
            self.oy = ey
            self.operation = "camera_rotation"
        if abs( dy ) > self.cam_m and abs( dy ) > abs( dx ):
            self.ox = ex
            self.oy = ey
            self.operation = "camera_scale"
    def Camera_Rotation( self, ex, ey ):
        factor = 5
        rotate = self.pcam_r - ( ( ex - self.ox ) / factor )
        self.cam_r = int( Limit_Looper( rotate, 360 ) )
    def Camera_Scale( self, ex, ey ):
        factor = 200
        scale = self.pcam_z - ( ( ey - self.oy ) / factor )
        self.cam_z = Limit_Range( scale, 0, 100 )
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
            self.PREVIEW_INCREMENT.emit( +1 )
            self.Pagination_Reset( ex, ey )
        if dx <= -factor:
            self.PREVIEW_INCREMENT.emit( -1 )
            self.Pagination_Reset( ex, ey )
        if dy >= factor:
            self.PREVIEW_INCREMENT.emit( -1 )
            self.Pagination_Reset( ex, ey )
        if dy <= -factor:
            self.PREVIEW_INCREMENT.emit( +1 )
            self.Pagination_Reset( ex, ey )

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        # State Update
        self.state_press = False
        Icon_Cursor( self.state_pickcolor, self.state_press )

        # Variables
        check_insert = Check_Insert()
        check_vector = Check_Vector( self.preview_url )
        ppp = self.preview_url == None or self.preview_qpixmap == None
        # Clip
        if self.state_clip == True:
            string_clip = " [CLIP]"
            qpixmap = self.Clip_Crop( self.preview_qpixmap )
        else:
            string_clip = ""
            qpixmap = self.preview_qpixmap
        clip = { 
            "cstate" : self.state_clip,
            "cl": self.clip_l,
            "ct": self.clip_t,
            "cw": self.clip_r - self.clip_l,
            "ch": self.clip_b - self.clip_t,
            }

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )
        # General
        action_pin_reference = qmenu.addAction( "Pin Reference" + string_clip )
        action_clip_image = qmenu.addAction( "Clip Image" )
        qmenu.addSeparator()
        # Preview
        menu_preview = qmenu.addMenu( "Preview" )
        action_preview_original = menu_preview.addAction( "Original Size" )
        action_preview_random = menu_preview.addAction( "Random Index" )
        # File Single
        menu_file = qmenu.addMenu( "File" )
        action_file_location = menu_file.addAction( "Open Location" )
        action_file_copy = menu_file.addAction( "Copy Path" )
        action_file_data = menu_file.addAction( "Copy Image" )
        # File Animation
        menu_anim = qmenu.addMenu( "Animation" )
        action_anim_export_one = menu_anim.addAction( "Export One" )
        action_anim_export_all = menu_anim.addAction( "Export All" )
        # File Compact
        menu_comp = qmenu.addMenu( "Compressed" )
        action_comp_export_one = menu_comp.addAction( "Export One" )
        action_comp_export_all = menu_comp.addAction( "Export All" )
        # Color
        menu_color = qmenu.addMenu( "Color" )
        action_color_analyse = menu_color.addAction( "Color Analyse" + string_clip )
        action_color_lut = menu_color.addAction( "LUT to Image" )
        
        # Edit
        menu_edit = qmenu.addMenu( "Edit" )
        action_edit_greyscale = menu_edit.addAction( "View Greyscale" )
        action_edit_invert_x = menu_edit.addAction( "Flip Horizontal" )
        action_edit_invert_y = menu_edit.addAction( "Flip Vertical" )
        action_edit_reset = menu_edit.addAction( "Edit Reset" )
        # Insert
        menu_insert = qmenu.addMenu( "Insert" )
        action_insert_document = menu_insert.addAction( "Document" + string_clip )
        action_insert_layer = menu_insert.addAction( "Layer" + string_clip )
        action_insert_reference = menu_insert.addAction( "Reference" + string_clip )
        # Screen
        qmenu.addSeparator()
        action_full_screen = qmenu.addAction( "Full Screen" )

        #endregion
        #region State

        # Check Preview
        action_preview_original.setCheckable( True );       action_preview_original.setChecked( self.state_original )
        action_clip_image.setCheckable( True );             action_clip_image.setChecked( self.state_clip )
        # Check Edit
        action_edit_greyscale.setCheckable( True );         action_edit_greyscale.setChecked( self.edit_greyscale )
        action_edit_invert_x.setCheckable( True );          action_edit_invert_x.setChecked( self.edit_invert_x )
        action_edit_invert_y.setCheckable( True );          action_edit_invert_y.setChecked( self.edit_invert_y )
        # Check Full Screen
        action_full_screen.setCheckable( True );            action_full_screen.setChecked( self.state_maximized )

        # Disable Menu
        if ppp == True:
            menu_preview.setEnabled( False )
            menu_file.setEnabled( False )
            menu_edit.setEnabled( False )
            menu_insert.setEnabled( False )
        if ppp == True or self.preview_state != "ANIM":
            menu_anim.setEnabled( False )
        if ppp == True or self.preview_state != "COMP":
            menu_comp.setEnabled( False )
        # Disable Actions
        if self.preview_qpixmap == None:
            action_pin_reference.setEnabled( False )
        if check_vector == True:
            action_clip_image.setEnabled( False )
        if self.pigmento_picker == None: 
            action_color_analyse.setEnabled( False )
        if self.pigmento_sampler == None: 
            action_color_lut.setEnabled( False )
        if check_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_reference.setEnabled( False )

        #endregion
        #region Action

        # Mapping
        action = qmenu.exec_( self.mapToGlobal( event.pos() ) )
        # General
        if action == action_pin_reference:
            self.PREVIEW_PIN_INSERT.emit( "image", self.w2, self.h2, None, self.preview_url, clip )
        if action == action_clip_image:
            self.state_clip = not self.state_clip
            if self.state_clip == True:
                self.Camera_Reset()
        # Preview
        if action == action_preview_original:
            self.state_original = not self.state_original
        if action == action_preview_random:
            self.PREVIEW_RANDOM.emit()
        # File
        if action == action_file_location:
            File_Open_Location( self.preview_url )
        if action == action_file_copy:
            File_Copy_Path( self.preview_url )
        if action == action_file_data:
            File_Copy_Image( self.preview_url )
        # Animation
        if action == action_anim_export_one:
            self.Anim_Export_One()
        if action == action_anim_export_all:
            self.Anim_Export_All()
        # Compressed
        if action == action_comp_export_one:
            self.Comp_Export_One()
        if action == action_comp_export_all:
            self.Comp_Export_All()
        # Color
        if action == action_color_analyse:
            qimage = qpixmap.toImage()
            Color_Analyse( self.pigmento_picker, qimage )
        if action == action_color_lut:
            Color_LUT_to_Image( self.pigmento_sampler, [ self.preview_url ] )
        # Edit
        if action == action_edit_greyscale:
            self.Edit_Display( "egs" )
        if action == action_edit_invert_x:
            self.Edit_Display( "efx" )
        if action == action_edit_invert_y:
            self.Edit_Display( "efy" )
        if action == action_edit_reset:
            self.Edit_Display( None )
        # Insert
        if action == action_insert_document:
            Insert_Document( self, self.preview_url, clip )
        if action == action_insert_layer:
            Insert_Layer( self, self.preview_url, clip )
        if action == action_insert_reference:
            Insert_Reference( self, self.preview_url, clip )
        # Screen
        if action == action_full_screen:
            self.PREVIEW_FULL_SCREEN.emit( not self.state_maximized )

        #endregion
    # Clip
    def Clip_Reset( self ):
        self.state_clip = False
        self.clip_node = None
        self.clip_l = 0.1  # 0-1
        self.clip_t = 0.1  # 0-1
        self.clip_r = 0.9  # 0-1
        self.clip_b = 0.9  # 0-1
    def Clip_Node( self, ex, ey ):
        # Camera
        self.Camera_Reset()
        # Points Single
        pl = self.draw_px + self.draw_width * self.clip_l
        pr = self.draw_px + self.draw_width * self.clip_r
        pt = self.draw_py + self.draw_height * self.clip_t
        pb = self.draw_py + self.draw_height * self.clip_b
        # Point Pair
        n1 = [ int( pl ), int( pt ) ]
        n2 = [ int( pr ), int( pt ) ]
        n3 = [ int( pr ), int( pb ) ]
        n4 = [ int( pl ), int( pb ) ]
        # Distance
        d1 = Trig_2D_Points_Distance( ex, ey, n1[0], n1[1] )
        d2 = Trig_2D_Points_Distance( ex, ey, n2[0], n2[1] )
        d3 = Trig_2D_Points_Distance( ex, ey, n3[0], n3[1] )
        d4 = Trig_2D_Points_Distance( ex, ey, n4[0], n4[1] )
        # Sort
        dist = [ [ d1, 1 ], [ d2, 2 ], [ d3, 3 ], [ d4, 4 ] ]
        dist.sort()
        factor = 20
        self.clip_node = None
        if dist[0][0] <= factor:
            self.clip_node = dist[0][1]
    def Clip_Edit( self, ex, ey, node ):
        if node != None:
            # Limit Value
            lx = ( Limit_Range( ex, self.draw_px, self.draw_px + self.draw_width ) - self.draw_px ) / self.draw_width
            ly = ( Limit_Range( ey, self.draw_py, self.draw_py + self.draw_height ) - self.draw_py ) / self.draw_height
            # Nodes
            if node == 1:
                if lx != self.clip_r:   self.clip_l = lx
                if ly != self.clip_b:   self.clip_t = ly
            if node == 2:
                if lx != self.clip_l:   self.clip_r = lx
                if ly != self.clip_b:   self.clip_t = ly
            if node == 3:
                if lx != self.clip_l:   self.clip_r = lx
                if ly != self.clip_t:   self.clip_b = ly
            if node == 4:
                if lx != self.clip_r:   self.clip_l = lx
                if ly != self.clip_t:   self.clip_b = ly
    def Clip_Flip( self ):
        if self.clip_r < self.clip_l:
            self.clip_l, self.clip_r = self.clip_r, self.clip_l
        if self.clip_b < self.clip_t:
            self.clip_t, self.clip_b = self.clip_b, self.clip_t
    def Clip_Crop( self, qpixmap ):
        if self.state_clip == True:
            # Dimensions
            width = self.preview_qpixmap.width()
            height = self.preview_qpixmap.height()
            # Clip Flipping
            clip_l = self.clip_l
            clip_r = self.clip_r
            clip_t = self.clip_t
            clip_b = self.clip_b
            # Variables
            delta_w = abs( clip_r - clip_l )
            delta_h = abs( clip_b - clip_t )
            # Crop
            qpixmap = qpixmap.copy( int( width * clip_l ), int( height * clip_t ), int( width * delta_w ), int( height * delta_h ) )
        return qpixmap
    def Clip_Image( self ):
        self.clip_w = self.clip_r - self.clip_l
        self.clip_h = self.clip_b - self.clip_t
        self.clip_image = { 
            "cstate" : self.state_clip,
            "cl": self.clip_l,
            "ct": self.clip_t,
            "cw": self.clip_w,
            "ch": self.clip_h,
            }
    # Overlay
    def Overlay_Information( self ):
        # Variables
        text = ""
        url = self.preview_url
        # Checks
        if url != None:
            # Checks
            check_dir = os.path.isdir( url )
            check_file = os.path.isfile( url )
            dirname = os.path.dirname( url )
            basename = os.path.basename( url )
            # Paths
            try:
                if check_dir:
                    text += f"Directory : { dirname }"
                    text += f"\nName : { basename }"
                if check_file:
                    split = basename.split(".")
                    info_name = split[0]
                    info_ext = split[1].upper()
                    text += f"Directory : { dirname }"
                    text += f"\nName : { info_name } [ { info_ext } ]"
            except:pass
            # Time
            try:
                mod_time = os.path.getmtime( url )
                local_time = time.localtime( mod_time )
                info_time = time.strftime( f"%Y-%m[%b]-%d[%a] %H:%M:%S", local_time )
                text += f"\nTime : { info_time }"
            except:pass
            # Size
            try:
                if check_file:
                    b = os.path.getsize( url )
                    kb = b / 1000
                    mb = kb / 1000
                    if 1 <= kb < 1000:
                        info_size = kb
                        info_scale = "Kb"
                    elif 1 <= mb < 1000:
                        info_size = mb
                        info_scale = "Mb"
                    else:
                        info_size = b
                        info_scale = "b"
                    text += f"\nSize : { round( info_size, 3 ) } { info_scale }"
            except:pass
            # Type
            try:
                if check_file:
                    pf = self.preview_format
                    pif = self.preview_image_format
                    pn = self.preview_color_name
                    text += f"\nType : { pf } { pif } { pn }"
            except:pass
            # Dimensions
            try:
                if check_file:
                    info_width = self.preview_qpixmap.width()
                    info_height = self.preview_qpixmap.height()
                    info_dpr = self.preview_qpixmap.devicePixelRatio()
                    text += f"\nDimension : { info_width } x { info_height } px  { info_dpr } dpr"
            except:pass
            # Preview Control
            try:
                if self.preview_state == "ANIM" and self.anim_count > 0:
                    text += f"\nAnimation : { self.anim_frame }:{ self.anim_count }"
                if self.preview_state == "COMP" and self.comp_count > 0:
                    text += f"\nCompressed : { self.comp_index }:{ self.comp_count } : { self.comp_path[self.comp_index] }"
            except:pass
            # Meta Data
            try:
                text += "\n"
                for md in self.preview_text:
                    text += f"\n{ md[0] } : { md[1] }"
            except:pass
        else:
            pass
        # Return
        return text
    def Overlay_Slide( self, ex, ey ):
        lim = self.hh - self.info_edge
        mid = int( self.hh - self.info_edge * 0.5 )
        if lim <= self.oy <= self.hh:
            if ey < lim:        self.state_information = True
            elif ey > self.hh:  self.state_information = False

    # Animation
    def Anim_Export_One( self ):
        if self.preview_state == "ANIM":
            save_folder = self.Export_Directory()
            if save_folder not in invalid:
                self.Export_Image( save_folder, self.anim_sequence, self.anim_frame )
    def Anim_Export_All( self ):
        if self.preview_state == "ANIM":
            save_folder = self.Export_Directory()
            if save_folder not in invalid:
                # Variables
                count = len( self.anim_sequence )
                # Progress Bar
                self.PREVIEW_PB_VALUE.emit( 0 )
                self.PREVIEW_PB_MAX.emit( count )
                # Cycle
                for i in range( 0, count ):
                    self.PREVIEW_PB_VALUE.emit( i + 1 )
                    self.Export_Image( save_folder, self.anim_sequence, i )
                # Progress Bar
                self.PREVIEW_PB_VALUE.emit( 0 )
                self.PREVIEW_PB_MAX.emit( 1 )
    # Compressed
    def Comp_Export_One( self ):
        if self.preview_state == "COMP":
            save_folder = self.Export_Directory()
            if save_folder not in invalid:
                self.Export_Archive( save_folder, self.comp_archive, self.comp_path[self.comp_index] )
    def Comp_Export_All( self ):
        if self.preview_state == "COMP":
            save_folder = self.Export_Directory()
            if save_folder not in invalid:
                # Variables
                count = len( self.comp_path )
                # Progress Bar
                self.PREVIEW_PB_VALUE.emit( 0 )
                self.PREVIEW_PB_MAX.emit( count )
                # Cycle
                for i in range( 0, count ):
                    self.PREVIEW_PB_VALUE.emit( i + 1 )
                    self.Export_Archive( save_folder, self.comp_archive, self.comp_path[i] )
                # Progress Bar
                self.PREVIEW_PB_VALUE.emit( 0 )
                self.PREVIEW_PB_MAX.emit( 1 )
    # Export
    def Export_Directory( self ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        save_folder = file_dialog.getExistingDirectory( self, "Select Directory", self.preview_url )
        return save_folder
    def Export_Image( self, directory, lista, index ):
        # Variables
        basename = os.path.basename( self.preview_url )
        name = basename.split( "." )[0]
        name_new = f"{ name }_{ str( index ).zfill( 4 ) }.png"
        save_path = os.path.normpath( os.path.join( directory, name_new ) )
        exists = os.path.exists( save_path )
        if exists == False:
            qpixmap = lista[ index ]
            if qpixmap.isNull() == False:
                qpixmap.save( save_path )
                Message_Log( "EXPORT", save_path )
            del qpixmap
    def Export_Archive( self, directory, archive, name ):
        # Image
        qpixmap = Compressed_QPixmap( archive, name )
        # Archive
        archive_name = os.path.basename( self.preview_url )
        archive_name = archive_name.split( "." )[0]
        archive_name = archive_name.replace( " ", "_" )
        # File
        file_name = os.path.basename( name )
        file_name = file_name.split( "." )[0]
        file_name = file_name.replace( " ", "_" )
        # Path
        name_new = f"{ archive_name }_{ file_name }.png"
        save_path = os.path.normpath( os.path.join( directory, name_new ) )
        # Save
        check_exists = os.path.exists( save_path ) == False
        check_null = qpixmap.isNull() == False
        check_none = qpixmap != None
        if check_exists and check_null and check_none:
            qpixmap.save( save_path )
            Message_Log( "EXPORT", save_path )
        del qpixmap
    # Edit
    def Edit_Reset( self ):
        self.edit_greyscale = False
        self.edit_invert_x = False
        self.edit_invert_y = False
    def Edit_Display( self, operation ):
        # Operations Boolean Toggle
        if operation == "egs":
            self.edit_greyscale = not self.edit_greyscale
        if operation == "efx":
            self.edit_invert_x = not self.edit_invert_x
        if operation == "efy":
            self.edit_invert_y = not self.edit_invert_y
        if operation == None:
            self.Edit_Reset()

        # Read
        if self.preview_state not in [ "ANIM", "COMP" ]:
            reader = QImageReader( self.preview_url )
            reader.setAutoTransform( True )
            qimage = reader.read()
        elif self.preview_state == "ANIM":
            qpixmap = self.anim_sequence[self.anim_frame]
            qimage = qpixmap.toImage()
        elif self.preview_state == "COMP":
            qpixmap = Compressed_QPixmap( self.comp_archive, self.comp_path[self.comp_index] )
            qimage = qpixmap.toImage()

        # Edit Image
        if self.edit_greyscale == True:
            qimage = qimage.convertToFormat( 24 )
        if ( self.edit_invert_x == True or self.edit_invert_y == True ):
            qimage = qimage.mirrored( self.edit_invert_x, self.edit_invert_y )
        self.preview_qpixmap = QPixmap().fromImage( qimage )
        # Update
        self.update()

    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True
        # Event
        em = event.modifiers()
        eb = event.buttons()
        ex = event.x()
        ey = event.y()
        self.ox = ex
        self.oy = ey
        self.ex = ex
        self.ey = ey
        # Cursor
        Icon_Cursor( self.state_pickcolor, self.state_press )
        # LMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton:
            if ( self.state_pickcolor == True and self.anim_play == False ):
                self.operation = "color_picker"
                ColorPicker_Event( self, ex, ey, self.qimage_grab, True )
            elif self.state_clip == True:
                self.operation = "clip"
                self.Clip_Node( ex, ey )
            else:
                self.operation = "information"
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "camera_move"
            self.Camera_Previous()
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "pagination"
            self.Camera_Reset()
        if em == QtCore.Qt.AltModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "drag_drop"
            self.Clip_Image()
        # MMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.MiddleButton:
            self.operation = "camera_move"
            self.Camera_Previous()
        # RMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.RightButton:
            self.operation = None
            self.Context_Menu( event )
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.RightButton:
            self.operation = "camera_swap"
            self.Camera_Previous()
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
        if self.operation == "information":
            self.Overlay_Slide( ex, ey )
        if ( self.operation == "color_picker" and self.anim_play == False ):
            ColorPicker_Event( self, ex, ey, self.qimage_grab, True )
        if self.operation == "clip":
            self.Clip_Edit( ex, ey, self.clip_node )
        # Camera
        if self.operation == "camera_move":
            self.Camera_Move( ex, ey )
        if self.operation == "camera_swap":
            self.Camera_Swap( ex, ey )
        if self.operation == "camera_scale":
            self.Camera_Scale( ex, ey )
        if self.operation == "camera_rotation":
            self.Camera_Rotation( ex, ey )
        # Pagination
        if self.operation == "pagination":
            self.Pagination_Stylus( ex, ey )
        # Drag Drop
        if self.operation == "drag_drop":
            Insert_Drag( self, self.preview_url, self.clip_image, False )
        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Variables
        url = self.preview_url
        # Event
        em = event.modifiers()
        eb = event.buttons()
        # LMB
        if ( em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton ):
            self.PREVIEW_MODE.emit( 1, False )
        if ( em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.LeftButton ):
            if os.path.isdir( url ):
                self.PREVIEW_LOAD.emit( url, None, 0 )
        # RMB
        if ( em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.RightButton ):
            self.PREVIEW_PARENT.emit()
    def mouseReleaseEvent( self, event ):
        # Variables
        self.state_press = False
        # Cursor
        self.Clip_Flip()
        Icon_Cursor( self.state_pickcolor, self.state_press )
        if ( self.operation == "color_picker" and self.anim_play == False ):
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
        if delta_y >= angle:    self.PREVIEW_INCREMENT.emit( -1 )
        if delta_y <= -angle:   self.PREVIEW_INCREMENT.emit( +1 )
    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.state_press = False
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.state_press = False
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.state_press = False
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            if ( self.drop == True and self.drag == False ):
                event.setDropAction( Qt.CopyAction )
                self.PREVIEW_DROP.emit( mime_data )
            event.accept()
        else:
            event.ignore()
        self.state_press = False
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
        side = min( ww, hh )

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Mask
        painter.setClipRect( QRect( int( 0 ), int( 0 ), int( ww ), int( hh ) ), Qt.ReplaceClip )

        # Path
        url = self.preview_url
        qpixmap = self.preview_qpixmap
        # Render Image
        if url != None and qpixmap != None:
            if self.preview_state in [ "FILE", "IMG", "ANIM", "COMP", "WEB" ]:
                px, py, draw = self.Draw_Render( painter, qpixmap, None )
                painter.drawPixmap( int( px ), int( py ), draw )
            elif self.preview_state == "DIR":
                px, py, draw = self.Draw_Render( painter, self.qpixmap_dir, qpixmap )
                painter.drawPixmap( int( px ), int( py ), draw )
                self.Draw_Text( painter, draw, px, py, ww, hh, os.path.basename( url ) )
            else:
                pass
        elif url != None and qpixmap == None:
            self.Draw_Circle( painter, self.c_lite, w2, h2, side )
        else:
            self.Draw_Circle( painter, self.c_dark, w2, h2, side )

        # Information
        if self.state_information == True:
            # Variables
            cor = QColor( self.c_dark.name() )
            cor.setAlpha( 200 )
            text = self.Overlay_Information()

            # Bounding Box
            rr = 8
            ss = 20
            m = 10
            m2 = 2 * m
            m4 = 4 * m
            pw = ww - ss * 2
            ph = self.info_edge
            px = ss
            py = hh - ph
            box_sqr = QRect( int( px ), int( py ), int( pw ), int( ph+rr ) )
            box_txt = QRect( int( px+m2 ), int( py+m ), int( pw-m4 ), int( ph ) )
            # Highlight
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( cor ) )
            painter.drawRoundedRect( box_sqr, rr, rr )
            # String
            painter.setBrush( QtCore.Qt.NoBrush )
            painter.setPen( QPen( self.c_text, 1, Qt.SolidLine ) )
            qfont = QFont( "Consolas", 10 )
            painter.setFont( qfont )
            painter.drawText( box_txt, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text )
            # Garbage
            del qfont

        # Display Color Picker
        if ( self.operation == "color_picker" and self.anim_play == False ):
            ColorPicker_Render( self, painter, self.ex, self.ey )

        # Drag and Drop Triangle
        if ( self.drop == True and self.drag == False ):
            Painter_Triangle( painter, w2, h2, side, self.c_chrome )
    def Draw_Render( self, painter, draw, dir_thumb ):
        # Variables
        px = 0
        py = 0
        dw = draw.width()
        dh = draw.height()
        rew = 1 # rotation error width
        reh = 1 # rotation error height

        # Display Size
        if self.state_original == True:
            width = dw
            height = dh
        else:
            width = self.ww
            height = self.hh

        # Layers Merge
        if self.state_underlayer == True or self.state_clip == True or self.state_gridline == True or dir_thumb != None:
            # Background
            merge = QPixmap( dw, dh )
            if self.state_underlayer == True: merge.fill( self.underlayer_color )
            else:                           merge.fill( self.transparent )
            # Merge Layers
            qpainter = QPainter( merge )
            qpainter.setRenderHint( QPainter.Antialiasing, True )

            # Directory Thumbnail
            if dir_thumb != None:
                pixw = dir_thumb.width()
                pixh = dir_thumb.height()
                ox = ( dw - pixw ) * 0.5
                oy = ( dh - pixh ) * 0.5
                iy = dh * 0.125
                qpainter.drawPixmap( int( ox ), int( oy + iy ), dir_thumb )
                box = QRect( int( px + ox ), int( py + oy ), int( pixw ), int( pixh*0.2 ) )
            # Image
            qpainter.drawPixmap( px, py, draw )

            # GridLines
            if self.state_gridline == True:
                line_width = 4
                qpainter.setPen( QPen( self.c_chrome, line_width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin ) )
                qpainter.setBrush( QtCore.Qt.NoBrush )
                for i in range( 0, self.gridline_x + 1 ):
                    ix = i / self.gridline_x
                    qpainter.drawLine( int( dw * ix ), int( 0 ), int( dw * ix ), int( dh ) )
                for i in range( 0, self.gridline_y + 1 ):
                    iy = i / self.gridline_y
                    qpainter.drawLine( int( 0 ), int( dh * iy ), int( dw ), int( dh * iy ) )

            # Clip
            if self.state_clip == True:
                # Painter
                qpainter.setPen( QtCore.Qt.NoPen )
                qpainter.setBrush( QBrush( color_alpha ) )

                # Variables
                pl = dw * self.clip_l
                pr = dw * self.clip_r
                pt = dh * self.clip_t
                pb = dh * self.clip_b
                tri = 15

                # Surface
                area = QPainterPath()
                area.moveTo( int( 0 ),  int( 0 ) )
                area.lineTo( int( dw ), int( 0 ) )
                area.lineTo( int( dw ), int( dh ) )
                area.lineTo( int( 0 ),  int( dh ) )
                area.moveTo( int( pl ), int( pt ) )
                area.lineTo( int( pr ), int( pt ) )
                area.lineTo( int( pr ), int( pb ) )
                area.lineTo( int( pl ), int( pb ) )
                qpainter.drawPath( area )

                # Triangles
                qpainter.setPen( QPen( color_black, 2, Qt.SolidLine ) )
                qpainter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                poly1 = QPolygon( [
                    QPoint( int( pl ), int( pt ) ),
                    QPoint( int( pl + tri ), int( pt ) ),
                    QPoint( int( pl ), int( pt + tri ) ),
                    ] )
                poly2 = QPolygon( [
                    QPoint( int( pr ), int( pt ) ),
                    QPoint( int( pr - tri ), int( pt ) ),
                    QPoint( int( pr ), int( pt + tri ) ),
                    ] )
                poly3 = QPolygon( [
                    QPoint( int( pr ), int( pb ) ),
                    QPoint( int( pr - tri ), int( pb ) ),
                    QPoint( int( pr ), int( pb - tri ) ),
                    ] )
                poly4 = QPolygon( [
                    QPoint( int( pl ), int( pb ) ),
                    QPoint( int( pl + tri ), int( pb ) ),
                    QPoint( int( pl ), int( pb - tri ) ),
                    ] )
                # Polygons
                qpainter.drawPolygon( poly1 )
                qpainter.drawPolygon( poly2 )
                qpainter.drawPolygon( poly3 )
                qpainter.drawPolygon( poly4 )

            # Painter
            qpainter.end()
        else:
            merge = draw

        # Fail Safe
        if dw != 0 and dh != 0:
            # Rotate
            if self.cam_r != 0:
                merge, wr, hr, rew, reh = self.Draw_Rotate( merge, dw, dh )
            # Scale
            merge = merge.scaled( int( width * rew * self.cam_z ), int( height * reh * self.cam_z ), Qt.KeepAspectRatio, self.scale_method )
            draw_width = merge.width()
            draw_height = merge.height()

            # Points
            px = self.w2 - ( draw_width * 0.5 )  + ( self.cam_x * self.cam_z )
            py = self.h2 - ( draw_height * 0.5 ) + ( self.cam_y * self.cam_z )

            # Clip Variables
            if self.cam_x == 0 and self.cam_y == 0 and self.cam_z == 1:
                self.draw_px = px
                self.draw_py = py
                self.draw_width = draw_width
                self.draw_height = draw_height

            # Return
            return px, py, merge
    def Draw_Rotate( self, image, dw, dh ):
        draw = image
        if self.cam_r != 0:
            rotation = QTransform().rotate( self.cam_r, Qt.ZAxis )
            draw = image.transformed( rotation )
        wr = draw.width()
        hr = draw.height()
        rew = wr / dw
        reh = hr / dh
        return draw, wr, hr, rew, reh
    def Draw_Circle( self, painter, color, px, py, side ):
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( color ) )
        ox = 0.2 * side
        oy = 0.2 * side
        size = 0.4 * side
        painter.drawEllipse( int( px - ox ), int( py - oy ), int( size ), int( size ) )
    def Draw_Text( self, painter, qpixmap, px, py, pw, ph, basename ):
        if self.cam_r == 0:
            # Bounding Box
            pixw = qpixmap.width()
            pixh = qpixmap.height()
            ox = ( pw - pixw ) * 0.5
            oy = ( ph - pixh ) * 0.5
            iy = self.qpixmap_dir.height() * 0.125 * self.cam_z
            box = QRect( int( px ), int( py + iy ), int( pixw ), int( pixh * 0.2 ) )
            """
            # Highlight
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( self.c_chrome ) )
            painter.drawRect( box )
            """
            # String
            painter.setBrush( QtCore.Qt.NoBrush )
            painter.setPen( QPen( self.c_dark, 1, Qt.SolidLine ) )
            qfont = QFont( "Consolas" )
            qfont.setPointSize( 10 )
            painter.setFont( qfont )
            painter.drawText( box, QtCore.Qt.AlignCenter|QtCore.Qt.TextWordWrap, basename )
            # Garbage
            del qfont

class ImagineBoard_Grid( QtWidgets.QWidget ):
    # General
    GRID_PARENT = QtCore.pyqtSignal()
    GRID_LOAD = QtCore.pyqtSignal( str, str, int )
    GRID_MODE = QtCore.pyqtSignal( int, bool )
    GRID_DROP = QtCore.pyqtSignal( list )
    GRID_INDEX = QtCore.pyqtSignal( int )
    # Menu
    GRID_PIN_INSERT = QtCore.pyqtSignal( str, float, float, str, str, dict )
    GRID_CYCLE = QtCore.pyqtSignal( str )
    GRID_FULL_SCREEN = QtCore.pyqtSignal( bool )
    # Ui
    GRID_PB_VALUE = QtCore.pyqtSignal( int )
    GRID_PB_MAX = QtCore.pyqtSignal( int )

    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Grid, self ).__init__( parent )
        self.Variables()
    def sizeHint( self ):
        return QtCore.QSize( 500,500 )

    # Variables
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
        self.state_maximized = False
        self.state_press = False
        self.state_pickcolor = False
        self.state_fit = False # Controller of grid_fit
        # Interaction
        self.operation = None

        # Grid
        self.grid_thumb = 200 # Grid Size
        self.grid_precache = 200 # Mb
        self.grid_clean = 0
        self.grid_geometry = list()
        self.grid_method = Qt.SmoothTransformation
        self.grid_state = None # None "FILE" "ANIM" "COMP" "DIR" "WEB"
        # Grid Unit
        self.gix = 0
        self.giy = 0
        self.gux = 1 # Grid Units in X
        self.guy = 1 # Grid Units in Y
        self.guc = self.gux * self.guy # Grid Unit Count
        self.gtw = 1 # Thumbnail Width
        self.gth = 1 # Thumbnail Height
        self.glt = 1 # Grid Limit Top
        self.glb = 1 # Grid Limit Bottom
        # Line
        self.list_url = list()
        self.list_qpixmap = list()
        self.list_size = list()
        self.list_select = list() # Index matches path and qpixmap
        self.list_index = -1
        self.list_count = 0
        self.list_start = 0
        self.list_end = 0
        self.list_geo_index = 0
        self.list_geo_end = self.list_start + self.guc
        # Grid Settings
        self.pagination_index = None
        self.extra_control = False

        # Colors
        self.c_lite = QColor( "#ffffff" )
        self.c_dark = QColor( "#000000" )
        self.c_chrome = QColor( "#3daee9" )
        self.c_select = QColor( "#2980b9" )
        # Color Picker
        self.pigmento_picker = None
        self.pigmento_sampler = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # System
        self.insert_original_size = False
        self.scale_method = Qt.SmoothTransformation

        # Icons
        self.qpixmap_comp, self.comp_size = None, 0
        self.qpixmap_dir,  self.dir_size  = None, 0

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False

        # QTimer
        self.grid_qtimer = QtCore.QTimer()

    # Relay Neutral
    def Set_Pigment_O( self, pigmento_picker, pigmento_sampler ):
        self.pigmento_picker = pigmento_picker
        self.pigmento_sampler = pigmento_sampler
    def Set_Theme( self, c_lite, c_dark, c_chrome, c_select ):
        self.c_lite = QColor( c_lite )
        self.c_dark = QColor( c_dark )
        self.c_chrome = QColor( c_chrome )
        self.c_select = QColor( c_select )
        Style_Icon( self )
        self.Grid_Image( True )
        self.update()
    def Set_ColorPicker( self, boolean ):
        self.state_pickcolor = boolean 
        self.update()
    def Set_Press( self, boolean ):
        self.state_press = boolean
        self.update()
    def Set_Precache( self, grid_precache ):
        self.grid_precache = grid_precache
        self.update()
    def Set_Clean( self, grid_clean ):
        self.grid_clean = grid_clean
        self.update()
    def Set_Insert_Original_Size( self, boolean ):
        self.insert_original_size = boolean
        self.update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()

    # Grid Relay
    def Set_Size( self, ww, hh, state_maximized, grid_thumb, extra_control ):
        # Variable
        self.state_maximized = state_maximized
        # Checks
        cw = self.ww != ww
        ch = self.hh != hh
        ct = self.grid_thumb != grid_thumb
        ce = self.extra_control != extra_control
        check = cw == True or ch == True or ct == True or ce == True
        if check:
            # Variable
            self.ww = ww
            self.hh = hh
            self.grid_thumb = grid_thumb
            self.extra_control = extra_control

            # Calculate
            self.w2 = ww * 0.5
            self.h2 = hh * 0.5
            # Widget
            self.resize( ww, hh )

            # Grid
            self.List_Excess( self.list_start, self.list_end )
            self.Grid_Geometry( self.ww, self.hh, self.grid_thumb )
            self.Grid_Image( ct or ce )
    # Grid Display
    def Grid_Line( self, list_index, list_url, update ):
        # Checks
        ci = self.list_index != list_index
        cp = self.list_url != list_url
        if ci == True or cp == True or update == True:
            # Variables
            self.list_index = list_index
            self.list_url = list_url
            # Grid
            if cp == True:
                self.List_Clear()
            self.List_Index( self.list_index )
            self.Grid_Image( update )
    def Grid_Fit( self, state_fit ):
        if self.state_fit != state_fit:
            self.state_fit = state_fit
            self.Grid_Image( True )
    def Grid_Default( self ):
        # Variables
        self.list_url = list()
        self.list_qpixmap = list()
        self.list_size = list()
        self.list_index = -1
        self.list_start = 0
        self.list_end = 0
        self.list_geo_end = 0
        # Update
        self.update()
        self.Camera_Grab()
    # Grid Operators
    def Grid_Geometry( self, ww, hh, grid_thumb ):
        # Variables
        grid_geometry = list()
        try:
            # Variables
            px = [0]
            py = [0]
            pw = list()
            ph = list()
            # Grid Units
            gtx = grid_thumb * 0.95
            gty = grid_thumb
            lx = Limit_Range( ww / gtx, 0, ww )
            ly = Limit_Range( hh / gty, 0, hh )
            ux = Limit_Mini( int( lx ), 1 )
            uy = Limit_Mini( int( ly ), 1 )
            # Variables
            self.gux = ux
            self.guy = uy
            self.guc = ux * uy
            # Factor
            dx = ww - ( gtx * ux )
            dy = hh - ( gty * uy )
            fx = dx / ux
            fy = dy / uy
            # Points
            for i in range( 1, ux + 1 ):px.append( int( gtx * i + fx * i ) )
            for i in range( 1, uy + 1 ):py.append( int( gty * i + fy * i ) )
            for i in range( 1, len( px ) ):pw.append( px[i] - px[i-1] )
            for i in range( 1, len( py ) ):ph.append( py[i] - py[i-1] )
            # Variables
            self.gtw = int( max( pw ) )
            self.gth = int( max( ph ) )
            # Geometry Construct
            grid_geometry = [ [ None for _ in range( ux ) ] for _ in range( uy ) ]
            for y in range( 0, uy ):
                for x in range( 0, ux ):
                    try:grid_geometry[y][x] = ( px[x], py[y], pw[x], ph[y] )
                    except:pass

            # Display Range
            self.list_geo_end = self.list_start + self.guc
            self.List_Index( self.list_index )

            # Progress Bar
            self.GRID_PB_VALUE.emit( 0 )
            self.GRID_PB_MAX.emit( self.guc )
        except:
            self.gux = 1
            self.guy = 1
            self.guc = 1
            self.gtw = 1
            self.gth = 1
        # Return
        self.grid_geometry = grid_geometry
    def Grid_Image( self, update ):
        # Icons
        if update == True:
            self.qpixmap_comp, self.comp_size = Item_Icon( self.qicon_comp, self.gtw, self.gth )
            self.qpixmap_dir,  self.dir_size  = Item_Icon( self.qicon_dir, self.gtw, self.gth )
        # Construct
        if self.list_count > 0:
            self.List_Load( self.list_start, self.list_end, self.list_index, self.list_url, update )
        # Update
        try:
            self.update()
            self.Camera_Grab()
        except:pass
    def Grid_Index( self, ex, ey ):
        # Cursor
        ex = Limit_Range( ex, 0, self.ww )
        ey = Limit_Range( ey, 0, self.hh )
        # Geometry
        gix = None
        giy = None
        for x in range( 0, self.gux ):
            item = self.grid_geometry[0][x]
            px = item[0]
            pw = item[2]
            cx = px <= ex <= px+pw
            if cx == True:
                gix = x
                break
        for y in range( 0, self.guy ):
            item = self.grid_geometry[y][0]
            py = item[1]
            ph = item[3]
            cy = py <= ey <= py+ph
            if cy == True:
                giy = y
                break
        if gix != None and giy != None:
            # Variables
            self.gix = gix
            self.giy = giy
            # Calculations
            self.list_geo_index = self.list_start + gix + giy * self.gux
            self.list_index = Limit_Range( self.list_geo_index, 0, len( self.list_url )-1 )
            # Signal
            self.GRID_INDEX.emit( self.list_index )
    def Grid_Increment( self, increment ):
        # Variables
        len_path = self.list_count - 1
        # Calculations
        if increment < 0:
            count = int( ( self.list_index - self.list_start ) / self.gux ) * self.gux
            list_index = Limit_Range( self.list_index - count - self.gux, 0, len_path )
        if increment > 0:
            count = int( ( self.list_geo_end - self.list_index - 1 ) / self.gux ) * self.gux
            list_index = Limit_Range( self.list_index + count + self.gux, 0, len_path )
        # Signal
        self.GRID_INDEX.emit( list_index )
    def Grid_Unload( self ):
        lim_start = Limit_Range( self.list_start - self.grid_clean, 0, self.list_count )
        lim_end = Limit_Range( self.list_end + self.grid_clean, 0, self.list_count )
        self.List_Unload( 0, lim_start )
        self.List_Unload( lim_end, self.list_count )
    # List
    def List_Clear( self, select=True ):
        self.list_count = len( self.list_url )
        self.list_qpixmap = [ None ] * self.list_count
        self.list_size = [ 0 ] * self.list_count
        if select == True:
            self.list_select = [ False ] * self.list_count
    def List_Index( self, list_index ):
        # Variables
        li = int( list_index / self.gux )
        gi = int( li * self.gux )
        if list_index <= self.list_start:
            self.list_start = gi
            self.list_geo_end = self.list_start + self.guc
        if list_index >= self.list_geo_end:
            self.list_geo_end = gi + self.gux
            self.list_start = self.list_geo_end - self.guc
        self.list_end = min( self.list_geo_end, self.list_count )
    def List_Load( self, start, end, list_index, list_url, update ):
        # Variables
        amplitude = end - start
        check = amplitude > 100
        # Cycle
        for index in range( start, end ):
            try:
                # Progress Bar
                if check == True:
                    self.GRID_PB_VALUE.emit( index + 1 )
                # Read
                if self.list_qpixmap[index] == None or update == True: # Load files not loaded
                    # Variables
                    grid_url = list_url[index]

                    # Item ( to Trouble shoot )
                    # qpixmap, size = self.Item_Load( grid_url )
                    # self.list_qpixmap[index] = qpixmap
                    # self.list_size[index] = size

                    # Worker
                    self.Worker_Single( index, grid_url )
            except Exception as e:
                # QtCore.qDebug( f"error_{ index } = { e }" )
                pass
        # Progress Bar
        self.GRID_PB_VALUE.emit( 0 )
        self.GRID_PB_MAX.emit( self.guc )
    def List_Precache( self ):
        if self.list_url != None:
            # Time Watcher
            start = QtCore.QDateTime.currentDateTimeUtc()

            # Progress Bar
            self.GRID_PB_VALUE.emit( 0 )
            self.GRID_PB_MAX.emit( 0 )

            # Unload
            self.Grid_Unload()

            # Variables
            total_size = 0
            lim_start = self.list_start
            lim_end = self.list_end
            # Display
            for i in range( self.list_start, self.list_end ):
                qpixmap, size = self.Item_Load( self.list_url[i] )
                total_size += size
                self.list_qpixmap[i] = qpixmap
                self.list_size[i] = size
            # Out of Display
            for i in range( 0, self.list_count ):
                QApplication.processEvents()
                if total_size <= self.grid_precache:
                    if lim_start > 0:
                        lim_start = Limit_Range( self.list_start - i - 1, 0, self.list_count )
                        qpixmap, size = self.Item_Load( self.list_url[lim_start] )
                        total_size += size
                        self.list_qpixmap[lim_start] = qpixmap
                        self.list_size[lim_start] = size
                    if lim_end < self.list_count - 1:
                        lim_end = Limit_Range( self.list_end + i, 0, self.list_count )
                        qpixmap, size = self.Item_Load( self.list_url[lim_end] )
                        total_size += size
                        self.list_qpixmap[lim_end] = qpixmap
                        self.list_size[lim_end] = size
                else:
                    break

    	    # Progress Bar
            self.GRID_PB_VALUE.emit( 0 )
            self.GRID_PB_MAX.emit( self.guc )

            # Variables
            amount = lim_end - lim_start

            # Time Watcher
            end = QtCore.QDateTime.currentDateTimeUtc()
            delta = start.msecsTo( end )
            time = QTime( 0,0 ).addMSecs( delta )
            # Print
            string = f"{ DOCKER_NAME } | PRECACHE { time.toString( 'hh:mm:ss.zzz' ) } | AMOUNT { amount } images | RAM { round( total_size, 3 ) } Mb"
            try:QtCore.qDebug( string )
            except:pass
    def List_Size( self, start, end ):
        ram = 0
        for i in range( start, end ):
            try:ram += self.list_size[i]
            except:pass
        return ram
    def List_Unload( self, start, end ):
        for i in range( start, end ):
            try:
                self.list_qpixmap[i] = None
                self.list_size[i] = 0
            except:
                break
    def List_Excess( self, start, end ):
        for i in range( 0, start ):
            try:
                self.list_qpixmap[i] = None
                self.list_size[i] = 0
            except:
                break
        for i in range( end, self.list_count ):
            try:
                self.list_qpixmap[i] = None
                self.list_size[i] = 0
            except:
                break

    # Item
    def Item_Load( self, grid_url ):
        # Variables
        qpixmap = None
        size = 0
        # File
        if os.path.isfile( grid_url ) == True:
            # Reader
            reader = QImageReader( grid_url )
            check_read = reader.canRead()
            check_anim = reader.supportsAnimation()
            check_comp = zipfile.is_zipfile( grid_url )
            if check_read == True and check_comp == False:
                # Static
                if check_anim == False:
                    qpixmap, size = Fit_Image( reader, self.gtw, self.gth, self.state_fit )
                # Animation
                elif check_anim == True:
                    qpixmap, size = Fit_Image( reader, self.gtw, self.gth, self.state_fit )
            # Compressed
            elif check_comp == True:
                qpixmap, size = Fit_Compressed( grid_url, self.gtw, self.gth, self.state_fit )
        # Directory
        elif os.path.isdir( grid_url ) == True:
            qpixmap, size = Fit_Directory( grid_url, self.gtw, self.gth )
        # HTML
        elif Check_Html( grid_url ) == True:
            qpixmap = Download_QPixmap( grid_url )
            if qpixmap != None:
                qpixmap, size = Fit_QPixmap( qpixmap, self.gtw, self.gth, self.state_fit, self.grid_method )
        # Return
        return qpixmap, size
    # Worker
    def Worker_Single( self, index, grid_url ):
        worker = Worker_Reader()
        worker.GRID_READER.connect( self.Worker_Index )
        worker.run( self, index, grid_url, self.gtw, self.gth, self.state_fit, self.grid_method )
    def Worker_Index( self, index, qpixmap, size ):
        self.list_qpixmap[ index ] = qpixmap[0]
        self.list_size[ index ] = size

    # Camera
    def Camera_Reset( self, ex, ey ):
        oz = ey % self.gth
        self.glt = ey - oz
        self.glb = self.glt + self.gth
        self.pagination_index = self.list_index
    def Camera_Stylus( self, ex, ey ):
        # Variables
        ey = Limit_Range( ey, 0, self.hh )
        margin = 2
        # Logic
        if ey > ( self.glb + margin ):
            self.Camera_Reset( ex, ey )
            self.Grid_Increment( -1 )
        if ey < ( self.glt - margin ):
            self.Camera_Reset( ex, ey )
            self.Grid_Increment( 1 )
        # Signal
        if self.pagination_index != None:
            self.GRID_INDEX.emit( self.pagination_index )
            self.pagination_index = None
    def Camera_Grab( self ):
        try:self.qimage_grab = self.grab().toImage()
        except:pass

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        # Variables
        self.state_press = False
        state_null = self.list_qpixmap == list()
        check_insert = Check_Insert()

        # Indexes
        try:
            url = self.list_url[ self.list_index ]
            qpixmap = self.list_qpixmap[ self.list_index ]
            select_url = self.Selection_List()
        except:
            url = None
            qpixmap = None
            select_url = None
        # Cursor
        Icon_Cursor( self.state_pickcolor, self.state_press )

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )

        # General
        action_pin_reference = qmenu.addAction( "Pin Reference" )
        qmenu.addSeparator()
        # Grid
        menu_grid = qmenu.addMenu( "Grid" )
        action_grid_fit = menu_grid.addAction( "Display Fit" )
        action_grid_precache = menu_grid.addAction( "Precache List" )
        # Search ( Rename )
        menu_search = qmenu.addMenu( "Search" )
        action_search_null = menu_search.addAction( "[NULL]" )
        action_search_copy = menu_search.addAction( "[ORIGINAL] [COPY]" )
        action_search_clean = menu_search.addAction( "Clean [TAGS]" )
        # Modify ( Change )
        menu_modify = qmenu.addMenu( "Modify" )
        action_modify_fix = menu_modify.addAction( "Fix (to SRGB)" )
        action_modify_premult = menu_modify.addAction( "Pre-Multiply" )
        # File
        menu_file = qmenu.addMenu( "File" )
        action_file_location = menu_file.addAction( "Open Location" )
        action_file_path = menu_file.addAction( "Copy Path" )
        action_file_data = menu_file.addAction( "Copy Image" )
        # Color
        menu_color = qmenu.addMenu( "Color" )
        action_color_analyse = menu_color.addAction( "Color Analyse" )
        action_color_lut = menu_color.addAction( "LUT to Image" )
        # Insert
        menu_insert = qmenu.addMenu( "Insert" )
        action_insert_document = menu_insert.addAction( "Document" )
        action_insert_layer = menu_insert.addAction( "Layer" )
        action_insert_reference = menu_insert.addAction( "Reference" )
        # Screen
        qmenu.addSeparator()
        action_full_screen = qmenu.addAction( "Full Screen" )

        # endregion
        #region State

        # Check Full Screen
        action_grid_fit.setCheckable( True )
        action_grid_fit.setChecked( self.state_fit )
        action_full_screen.setCheckable( True )
        action_full_screen.setChecked( self.state_maximized )

        # Disables
        if state_null == True:
            action_pin_reference.setEnabled( False )
            menu_grid.setEnabled( False )
            menu_search.setEnabled( False )
            menu_modify.setEnabled( False )
            menu_file.setEnabled( False )
            menu_insert.setEnabled( False )
        if self.pigmento_picker == None:
            action_color_analyse.setEnabled( False )
        if self.pigmento_sampler == None: 
            action_color_lut.setEnabled( False )
        if check_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_reference.setEnabled( False )

        #endregion
        #region Action

        # Mapping
        len_path = len( self.list_url )
        if self.list_geo_index < len_path:
            action = qmenu.exec_( self.mapToGlobal( event.pos() ) )
            # General
            if action == action_pin_reference:
                self.GRID_PIN_INSERT.emit( "image", self.w2, self.h2, None, url, clip_false )
            # Grid
            if action == action_grid_fit:
                self.Grid_Fit( not self.state_fit )
            if action == action_grid_precache:
                self.List_Precache()
            # Search
            if action == action_search_null:
                self.GRID_CYCLE.emit( "NULL" )
            if action == action_search_copy:
                self.GRID_CYCLE.emit( "COPY" )
            if action == action_search_clean:
                self.GRID_CYCLE.emit( "CLEAN" )
            # Modify
            if action == action_modify_fix:
                self.GRID_CYCLE.emit( "FIX" )
            if action == action_modify_premult:
                self.GRID_CYCLE.emit( "PRE_MULTIPLY" )
            # File
            if action == action_file_location:
                File_Open_Location( url )
            if action == action_file_path:
                File_Copy_Path( url )
            if action == action_file_data:
                File_Copy_Image( url )
            # Colro
            if action == action_color_analyse:
                qimage = qpixmap.toImage()
                Color_Analyse( self.pigmento_picker, qimage )
            if action == action_color_lut:
                list_url = [ url ]
                list_url.extend( select_url )
                Color_LUT_to_Image( self.pigmento_sampler, list_url )
            # Insert
            if action == action_insert_document:
                Insert_Document( self, url, clip_false )
            if action == action_insert_layer:
                Insert_Layer( self, url, clip_false )
            if action == action_insert_reference:
                Insert_Reference( self, url, clip_false )
            # Screen
            if action == action_full_screen:
                self.GRID_FULL_SCREEN.emit( not self.state_maximized )

        #endregion

    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True
        # Event
        em = event.modifiers()
        eb = event.buttons()
        ex = event.x()
        ey = event.y()
        self.ox = ex
        self.oy = ey
        self.ex = ex
        self.ey = ey
        # Cursor
        Icon_Cursor( self.state_pickcolor, self.state_press )
        self.Grid_Index( ex, ey )
        # LMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton:
            if self.state_pickcolor == True:
                self.operation = "color_picker"
                ColorPicker_Event( self, ex, ey, self.qimage_grab, True )
            else:
                self.operation = "neutral_press"
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "camera_move"
            self.Camera_Reset( ex, ey )
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "select_plus"
            self.Selection_Plus( ex, ey )
        if em == QtCore.Qt.AltModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "drag_drop"
        # MMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.MiddleButton:
            self.operation = "camera_move"
            self.Camera_Reset( ex, ey )
        # RMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.RightButton:
            self.operation = None
            self.Context_Menu( event )
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.RightButton:
            self.operation = "camera_move"
            self.Camera_Reset( ex, ey )
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.RightButton:
            self.operation = "select_minus"
            self.Selection_Minus( ex, ey )
        if em == QtCore.Qt.AltModifier and eb == QtCore.Qt.RightButton:
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
            ColorPicker_Event( self, ex, ey, self.qimage_grab, True )
        # Camera
        if self.operation == "camera_move":
            self.Camera_Stylus( ex, ey )
        # Select
        if self.operation == "select_plus":
            self.Selection_Plus( ex, ey )
        if self.operation == "select_minus":
            self.Selection_Minus( ex, ey )
        # Drag Drop
        if self.operation == "drag_drop":
            url = self.list_url[ self.list_index ]
            Insert_Drag( self, url, clip_false, True )
        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Variables
        try:    url = self.list_url[ self.list_index ]
        except: url = None
        # Event
        em = event.modifiers()
        eb = event.buttons()
        # LMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton:
            self.GRID_MODE.emit( 0, False )
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.LeftButton:
            if os.path.isdir( url ):
                self.GRID_LOAD.emit( url, None, 0 )
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.LeftButton:
            self.Selection_All()
        # RMB
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.RightButton:
            self.GRID_PARENT.emit()
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.RightButton:
            self.Selection_Clear()
    def mouseReleaseEvent( self, event ):
        # Variables
        self.state_press = False
        self.selection = None
        # Cursor
        Icon_Cursor( self.state_pickcolor, self.state_press )
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, False )
        # Variables
        self.operation = None
        # Update
        self.update()
        self.Camera_Grab()
    # Selection
    def Selection_Plus( self, ex, ey ):
        self.Grid_Index( ex, ey )
        grid_url = self.list_url[ self.list_index ]
        self.list_select[ self.list_index ] = True
    def Selection_Minus( self, ex, ey ):
        self.Grid_Index( ex, ey )
        self.list_select[ self.list_index ] = False
    def Selection_All( self ):
        for i in range( 0, len( self.list_select ) ):
            self.list_select[i] = True
    def Selection_Clear( self ):
        for i in range( 0, len( self.list_select ) ):
            self.list_select[i] = False
    def Selection_List( self ):
        selection_list = list()
        for i in range( 0, len( self.list_url ) ):
            if self.list_select[i] == True:
                selection_list.append( self.list_url[i] )
        return selection_list

    # Wheel Event
    def wheelEvent( self, event ):
        delta_y = event.angleDelta().y()
        angle = 5
        if delta_y >= angle:    self.Grid_Increment( -1 )
        if delta_y <= -angle:   self.Grid_Increment( +1 )

    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.state_press = False
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.state_press = False
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragLeaveEvent( self, event ):
        self.state_press = False
        self.drop = False
        event.accept()
        self.update()
    def dropEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            if ( self.drop == True and self.drag == False ):
                event.setDropAction( Qt.CopyAction )
                self.GRID_DROP.emit( mime_data )
            event.accept()
        else:
            event.ignore()
        self.state_press = False
        self.drop = False
        self.drag = False
        self.update()

    # Timer
    def Grid_Timer_Event( self ):
        self.Grid_Timer_Stop()
        self.Grid_Timer_Start( lambda: self.Grid_Image( True ) )
    def Grid_Timer_Start( self, function ):
        self.grid_qtimer = QtCore.QTimer()
        self.grid_qtimer.setSingleShot( True )
        self.grid_qtimer.setInterval( 1000 )
        self.grid_qtimer.timeout.connect( function )
        self.grid_qtimer.start()
    def Grid_Timer_Stop( self ):
        try:self.grid_qtimer.stop()
        except:pass

    # Widget
    def showEvent( self, event ):
        self.Grid_Image( True )
    def resizeEvent( self, event ):
        self.Grid_Timer_Event()
    def enterEvent( self, event ):
        self.Camera_Grab()
    def leaveEvent( self, event ):
        self.Grid_Unload()
        self.update()
    def closeEvent( self, event ):
        self.Grid_Timer_Stop()

    # Painter
    def paintEvent( self, event ):
        # Variables
        ww = self.ww
        hh = self.hh
        w2 = self.w2
        h2 = self.h2
        side = min( ww, hh )
        thumb = min( self.gtw, self.gth )
        state_null = self.list_qpixmap == list()

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Draw QPixmaps
        length = len( self.list_qpixmap )
        for y in range( 0, self.guy ):
            for x in range( 0, self.gux ):
                # Index
                geo_index = x + y * self.gux

                # Geometry
                try:
                    geo = self.grid_geometry[y][x]
                    px = geo[0]
                    py = geo[1]
                    pw = geo[2]
                    ph = geo[3]
                except:
                    px = 0
                    py = 0
                    pw = 1
                    ph = 1

                # Clip Mask
                thumbnail = QRect( int( px ), int( py ), int( pw+1 ), int( ph+1 ) ) # +1 clears float error
                painter.setClipRect( thumbnail, Qt.ReplaceClip )

                # Variables
                index = self.list_start + geo_index
                check_marker = self.state_press == True and index == self.list_index and self.operation != "color_picker"

                # Render
                try:
                    url = self.list_url[index]
                    qpixmap = self.list_qpixmap[index]
                    select = self.list_select[index]
                    check_file = os.path.isfile( url )
                    check_comp = zipfile.is_zipfile( url )
                    check_kra = url.endswith( file_krita )
                    check_dir = os.path.isdir( url )
                    check_web = Check_Html( url )
                    render = True
                except:
                    render = False
                if render == True:
                    # Pixmap
                    if qpixmap != None:
                        if check_dir and self.qpixmap_dir != None: # Directory
                            self.Draw_Icon_Dir( painter, qpixmap, px, py, pw, ph ) # Image Inside
                            self.Draw_QPixmap( painter, self.qpixmap_dir, px, py, pw, ph ) # Folder Icon
                            self.Draw_Text( painter, self.qpixmap_dir, px, py, pw, ph, os.path.basename( url ) )
                        elif check_comp and self.qpixmap_comp != None and check_kra == False: # Compressed ( ZIP )
                            self.Draw_QPixmap( painter, qpixmap, px, py, pw, ph ) # Image Inside
                            self.Draw_QPixmap( painter, self.qpixmap_comp, px, py, pw, ph ) # Comp Icon
                        else: # Static + Animation + Compressed ( KRA ) + Internet
                            self.Draw_QPixmap( painter, qpixmap, px, py, pw, ph )
                    # Select
                    if select == True:
                        if check_file == True and check_comp == False:
                            color = self.c_select
                        else:
                            color = self.c_lite
                        self.Draw_Select( painter, color, px, py, pw, ph )
                    # Circles
                    if check_marker == True:
                        self.Draw_Circle( painter, self.c_chrome, px, py, thumb ) # Index Circle ( white )
                    elif check_marker == False and check_file == True and qpixmap == None:
                        self.Draw_Circle( painter, self.c_lite, px, py, thumb ) # Unreadable Image
                else:
                    self.Draw_Circle( painter, self.c_dark, px, py, thumb ) # Empty Space ( black )

        # Clean Mask
        painter.setClipping( False )

        # Display Color Picker
        if self.operation == "color_picker":
            ColorPicker_Render( self, painter, self.ex, self.ey )

        # Drag and Drop Triangle
        if ( self.drop == True and self.drag == False ):
            Painter_Triangle( painter, w2, h2, side, self.c_chrome )
    def Draw_QPixmap( self, painter, qpixmap, px, py, pw, ph ):
        ox = ( pw - qpixmap.width() ) * 0.5
        oy = ( ph - qpixmap.height() ) * 0.5
        painter.drawPixmap( int( px + ox ), int( py + oy ), qpixmap )
    def Draw_Icon_Dir( self, painter, qpixmap, px, py, pw, ph ):
        ox = ( pw - qpixmap.width() ) * 0.5
        oy = ( ph - qpixmap.height() ) * 0.5
        iy = self.qpixmap_dir.height() * 0.125
        painter.drawPixmap( int( px + ox ), int( py + oy + iy ), qpixmap )
    def Draw_Text( self, painter, qpixmap, px, py, pw, ph, basename ):
        # Bounding Box
        pixw = qpixmap.width()
        pixh = qpixmap.height()
        ox = ( pw - pixw ) * 0.5
        oy = ( ph - pixh ) * 0.5
        iy = self.qpixmap_dir.height() * 0.125
        box = QRect( int( px + ox ), int( py + oy + iy ), int( pixw ), int( pixh*0.2 ) )
        """
        # Highlight Under Text
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( self.c_chrome ) )
        painter.drawRect( box )
        """
        # String
        painter.setBrush( QtCore.Qt.NoBrush )
        painter.setPen( QPen( self.c_dark, 1, Qt.SolidLine ) )
        qfont = QFont( "Consolas" )
        qfont.setPointSize( 10 )
        painter.setFont( qfont )
        painter.drawText( box, QtCore.Qt.AlignCenter|QtCore.Qt.TextWordWrap, basename )
        # Garbage
        del qfont
    def Draw_Circle( self, painter, color, px, py, thumb ):
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( color ) )
        side = 0.6
        ox = ( self.gtw * 0.5 ) - ( side * thumb * 0.5 )
        oy = ( self.gth * 0.5 ) - ( side * thumb * 0.5 )
        painter.drawEllipse( int( px + ox ), int( py + oy ), int( side * thumb ), int( side * thumb ) )
    def Draw_Select( self, painter, color, px, py, pw, ph ):
        painter.setPen( QtCore.Qt.NoPen )
        painter.setBrush( QBrush( color, Qt.Dense3Pattern ) )
        m = 4
        painter.drawRect( int( px ), int( py ), int( pw + m ), int( ph + m ) )

class ImagineBoard_Reference( QtWidgets.QWidget ):
    # General
    REFERENCE_DROP = QtCore.pyqtSignal( list )
    # Menu
    REFERENCE_PIN_INSERT = QtCore.pyqtSignal( str, float, float, str, str, dict )
    REFERENCE_FULL_SCREEN = QtCore.pyqtSignal( bool )
    # UI
    REFERENCE_PB_VALUE = QtCore.pyqtSignal( int )
    REFERENCE_PB_MAX = QtCore.pyqtSignal( int )
    REFERENCE_LABEL = QtCore.pyqtSignal( str, str, int, str, str )
    REFERENCE_CAMERA = QtCore.pyqtSignal( list, float, int, int )
    REFERENCE_PACKER = QtCore.pyqtSignal( bool )

    # Init
    def __init__( self, parent ):
        super( ImagineBoard_Reference, self ).__init__( parent )
        self.Variables()
    def sizeHint( self ):
        return QtCore.QSize( 500,500 )

    # Variables
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

        # State Internal
        self.state_inside = False
        self.state_maximized = False
        self.state_press = False
        self.state_select = False
        self.state_pack = False
        # State Layout
        self.state_lock = False
        self.state_pickcolor = False
        # State Dialog
        self.state_rebase = False
        # Interaction
        self.operation = None
        self.dirty = False

        # Camera
        self.cam_p = [ 1, 1 ]
        self.cam_n = [
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
        self.cam_i = self.cam_n.index( 1 )
        self.cam_z = self.cam_n[self.cam_i] # Camera Zoom

        # Link
        self.link_eo_url = str()

        # Pin
        self.pin_list = list()
        self.pin_previous = list()
        self.pin_index = None
        self.pin_url = None
        self.pin_basename = None
        self.pin_node = None
        self.pin_count = 0
        self.pin_preview = None

        # Limit
        self.limit_x = list()
        self.limit_y = list()

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

        # Colors
        self.c_lite = QColor( "#ffffff" )
        self.c_dark = QColor( "#000000" )
        self.c_chrome = QColor( "#3daee9" )
        self.c_select = QColor( "#2980b9" )

        # Color Picker
        self.pigmento_picker = None
        self.pigmento_sampler = None
        self.qimage_grab = None
        self.color_active = QColor( 0, 0, 0 )
        self.color_previous = QColor( 0, 0, 0 )

        # Clip
        self.clip_pin = { "cstate" : False, "cl" : 0, "ct" : 0, "cr" : 1, "cb" : 1 }
        clip_false = { "cstate" : False, "cl" : 0, "ct" : 0, "cr" : 1, "cb" : 1 }

        # System
        self.insert_original_size = False
        self.scale_method = Qt.SmoothTransformation

        # Drag and Drop
        self.setAcceptDrops( True )
        self.drop = False
        self.drag = False

        # Kritarc
        self.Kritarc_Read()

        # Debug Packer Points
        # self.p = list()
    def Kritarc_Read( self ):
        # EO
        self.link_eo_state = True
        self.link_eo_archive = False
        self.link_eo_access = None # TextIOWrapper
        self.link_eo_url = str() # EO file url
        # KRA
        self.link_kra_state = False
        self.link_kra_archive = False
        self.link_kra_access = None # Active Document Krita Object
        self.link_kra_name = None # FileName
        # Read
        self.link_eo_url = Kritarc_Read( DOCKER_NAME, "link_eo_url", self.link_eo_url, str )
        self.link_eo_state = Kritarc_Read( DOCKER_NAME, "link_eo_state", self.link_eo_state, eval )
        self.link_kra_state = Kritarc_Read( DOCKER_NAME, "link_kra_state", self.link_kra_state, eval )

    # Relay System
    def Set_Pigment_O( self, pigmento_picker, pigmento_sampler ):
        self.pigmento_picker = pigmento_picker
        self.pigmento_sampler = pigmento_sampler
    def Set_Theme( self, c_lite, c_dark, c_chrome, c_select ):
        self.c_lite = QColor( c_lite )
        self.c_dark = QColor( c_dark )
        self.c_chrome = QColor( c_chrome )
        self.c_select = QColor( c_select )
        Style_Icon( self )
        self.update()
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
    # Relay Layout
    def Set_Lock( self, boolean ):
        self.state_lock = boolean
        self.update()
    def Set_ColorPicker( self, boolean ):
        self.state_pickcolor = boolean 
        self.update()
    # Relay Dialog
    def Set_Insert_Original_Size( self, boolean ):
        self.insert_original_size = boolean
        self.update()
    def Set_Rebase( self, boolean ):
        self.state_rebase = boolean
        self.update()
    def Set_Scale_Method( self, scale_method ):
        self.scale_method = scale_method
        self.update()
    # Relay Board
    def Set_Link_Document( self, link_kra_access ):
        self.link_kra_access = link_kra_access
        self.link_kra_name = str()
        if link_kra_access != None:
            file_name = self.link_kra_access.fileName()
            self.link_kra_name = os.path.basename( file_name )
        self.update()
    # Relay Label
    def Set_Label_Text( self, text ):
        if self.state_lock == False:
            lista = self.Label_List()
            for i in lista:
                self.pin_list[i]["text"] = text
            self.update()
    def Set_Label_Font( self, font ):
        if self.state_lock == False:
            lista = self.Label_List()
            for i in lista:
                self.pin_list[i]["font"] = font
            self.update()
    def Set_Label_Letter( self, letter ):
        if self.state_lock == False:
            lista = self.Label_List()
            for i in lista:
                self.pin_list[i]["letter"] = letter
            self.update()
    def Set_Label_Pen( self, pen ):
        if self.state_lock == False:
            lista = self.Label_List()
            for i in lista:
                self.pin_list[i]["pen"] = pen
            self.update()
    def Set_Label_Bg( self, bg ):
        if self.state_lock == False:
            lista = self.Label_List()
            for i in lista:
                self.pin_list[i]["bg"] = bg
            self.update()

    # Request Board
    def Get_Pin( self ):
        return self.pin_list
    def Get_Count( self ):
        return self.pin_count
    def Get_EO_State( self ):
        return self.link_eo_state
    def Get_KRA_State( self ):
        return self.link_kra_state
    def Get_File_Name( self ):
        file_name = str()
        if   self.link_eo_state  == True:   file_name = os.path.basename( self.link_eo_url )
        elif self.link_kra_state == True:   file_name = self.link_kra_name
        return file_name
    # Request Label
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

    # Boards
    def Board_Load( self, lista ):
        # Insert Pins
        self.pin_list = list()
        self.pin_count = len( lista )
        for i in range( 0, self.pin_count ):
            pin = lista[i]
            self.pin_list.append( pin )
        # Update
        self.Board_Update()
    def Board_Refresh( self ):
        if   self.link_eo_state  == True:   self.EO_Load()
        elif self.link_kra_state == True:   self.KRA_Read()
    def Board_Save( self ):
        if   self.link_eo_state  == True:   self.EO_Save()
        elif self.link_kra_state == True:   self.KRA_Write( False )
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
            # Camera
            self.Camera_Zoom_Fit()
        # Update
        self.Pin_Previous()
        self.Board_Limit( "DRAW" )
        self.update()
    def Board_Limit( self, mode ):
        # Variables
        self.pin_count = len( self.pin_list )
        board_horz = list()
        board_vert = list()
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
    def Board_Empty( self ):
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
        if self.dirty == True:
            self.dirty = False
            self.Board_Save()
        # Update
        self.update()
        self.Camera_Grab()

    # Camera
    def Camera_Load( self, position, zoom ):
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
        for i in range( 0, len( self.cam_n ) ):
            if ( zoom >= self.cam_n[i] ) and ( zoom < self.cam_n[i+1] ):
                index = i
                break
        self.cam_i = index
        self.cam_z = self.cam_n[index]
        # Update
        self.Board_Update()
    def Camera_Reset( self ):
        self.cam_i = self.cam_n.index( 1 )
        self.cam_z = self.cam_n[self.cam_i] # Camera Zoom
    def Camera_Position( self ):
        px = 1
        py = 1
        if ( self.board_w != 0 or self.board_h != 0 ):
            px = ( self.w2 - self.board_l ) / self.board_w
            py = ( self.h2 - self.board_t ) / self.board_h
        self.cam_p = [ px, py ]
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
        self.cam_i = Limit_Range( self.cam_i + int( step ), 0, len( self.cam_n ) - 1 )
        self.cam_z = self.cam_n[self.cam_i]
        self.Camera_Emit()
        self.update()
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
        zoom = list()
        if cl > 0:zoom.append( cl )
        if cr > 0:zoom.append( cr )
        if ct > 0:zoom.append( ct )
        if cb > 0:zoom.append( cb )
        zoom = min( zoom )

        # Index
        index = self.cam_n.index( 1 )
        for i in range( 0, len( self.cam_n ) ):
            if ( zoom >= self.cam_n[i] and zoom < self.cam_n[i+1] ):
                index = i
                break
        # Apply
        self.cam_i = index
        self.cam_z = self.cam_n[self.cam_i]
        self.Camera_Emit()
    def Camera_Signal( self ):
        self.Camera_Position()
        self.REFERENCE_CAMERA.emit( self.cam_p, self.cam_z, self.select_count, self.pin_count )
    def Camera_Emit( self ):
        self.Camera_Signal()
        for i in range( 0, self.pin_count ):
            self.Pin_Draw_QPixmap( self.pin_list, i )
    def Camera_Grab( self ):
        try:self.qimage_grab = self.grab().toImage()
        except:pass

    # Pin
    def Pin_Insert( self, pin ):
        # Pin
        self.pin_list.append( pin )
        self.pin_count = self.pin_count + 1
        # Update
        self.update()
    def Pin_URL( self, bx, by ):
        url, ok = QInputDialog.getText( self, "Link Image", "URL", QLineEdit.Normal, "" )
        if ok and url != "":
            self.REFERENCE_PIN_INSERT.emit( "image", bx, by, None, url, clip_false )
    def Pin_Update( self ):
        for i in range( 0, self.pin_count ):
            self.pin_list[i]["index"] = i
    def Pin_Index( self, ex, ey ):
        # Variables
        index = None
        self.pin_index = None
        self.pin_url = None
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
                self.pin_url = self.pin_list[pin_index]["url"]
                try:self.pin_basename = str( os.path.basename( self.pin_url ) ) # local
                except:self.pin_basename = None # web
            else:
                self.pin_url = None
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
            nodes = list()
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
            pin_previous = list()
            for i in range( 0, self.pin_count ):
                previous = {
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
                pin_previous.append( previous )
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
            dx = self.w2 + ( bx - self.w2 ) * self.cam_z
            dy = self.h2 + ( by - self.h2 ) * self.cam_z
            dl = self.w2 + ( bl - self.w2 ) * self.cam_z
            dr = self.w2 + ( br - self.w2 ) * self.cam_z
            dt = self.h2 + ( bt - self.h2 ) * self.cam_z
            db = self.h2 + ( bb - self.h2 ) * self.cam_z
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
            if qpixmap == None:
                lista[index]["qpixmap"] = None
                lista[index]["draw"] = None
            else:
                draw = self.Edit_QPixmap( qpixmap, egs, efx, efy )
                draw = self.Scale_QPixmap( draw, tsw, tsh )
                draw = self.Rotate_QPixmap( draw, trz )
                lista[index]["draw"] = draw
                del draw
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
        w = width * self.cam_z
        h = height * self.cam_z
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
        snap_dist = 10 / self.cam_z

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
    # Points
    def Point_Deltas( self, ex, ey ):
        try:
            dx = ( ex - self.ox ) / self.cam_z
            dy = ( ey - self.oy ) / self.cam_z
        except:
            dx = 0
            dy = 0
        return dx, dy
    def Point_Location( self, ex, ey ):
        try:
            px = self.w2 + ( ex - self.w2 ) / self.cam_z
            py = self.h2 + ( ey - self.h2 ) / self.cam_z
        except:
            px = self.w2
            py = self.h2
        return px, py
    # Scale
    def Scale_Pin( self, px, py, node ):
        # Variables
        snap_dist = 20 / self.cam_z

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
        dist = list()
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
    def Scale_Reset( self, previous, index ):
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

        # Variables
        side = 200
        # Calculations
        if bw >= bh:
            factor = side / bh
            n_bw = int( bw * factor )
            n_bh = side
        else:
            factor = side / bw
            n_bw = side
            n_bh = int( bh * factor )
        dw = bw * 0.5
        dh = bh * 0.5

        # Calculation
        n_tsk = tsk * factor
        n_tsw = tsw * factor
        n_tsh = tsh * factor
        n_bl = bx - dw
        n_br = n_bl + n_bw
        n_bt = by - dh
        n_bb = n_bt + n_bh

        # Write
        self.pin_list[index]["tsk"] = n_tsk
        self.pin_list[index]["tsw"] = n_tsw
        self.pin_list[index]["tsh"] = n_tsh
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
        snap_dist = 10 / self.cam_z

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

    # Clip
    def Clip_Pin( self ):
        if self.pin_index == None:
            pin_cstate = False
            pin_cl = 0
            pin_ct = 0
            pin_cw = 1
            pin_ch = 1
        else:
            pin = self.pin_list[self.pin_index]
            pin_cstate = pin["cstate"]
            pin_cl = pin["cl"]
            pin_ct = pin["ct"]
            pin_cw = pin["cw"]
            pin_ch = pin["ch"]
        self.clip_pin = { "cstate" : pin_cstate, "cl": pin_cl, "ct": pin_ct, "cw": pin_cw, "ch": pin_ch }

    # Label ( Text )
    def Label_Insert( self, event ):
        pos = event.pos()
        bx, by = self.Point_Location( pos.x(), pos.y() )
        self.REFERENCE_PIN_INSERT.emit( "label", bx, by, "Text", None, clip_false )
    def Label_List( self ):
        lista = list()
        for i in range( 0, self.pin_count ):
            if self.pin_list[i]["select"] == True:
                lista.append( i )
        return lista
    def Label_Panel( self, index ):
        info_text = self.pin_list[index]["text"]
        info_font = self.pin_list[index]["font"]
        info_letter = self.pin_list[index]["letter"]
        info_pen = self.pin_list[index]["pen"]
        info_bg = self.pin_list[index]["bg"]
        self.REFERENCE_LABEL.emit( info_text, info_font, info_letter, info_pen, info_bg )
        
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
    # UI
    def ProgressBar_Value( self, value ):
        self.REFERENCE_PB_VALUE.emit( value )
    def ProgressBar_Maximum( self, maximum ):
        self.REFERENCE_PB_MAX.emit( maximum )

    # Garbage
    def Garbage_Clean( self ):
        try:del self.packer_qthread
        except:pass
        try:del self.packer_worker
        except:pass

    # Context Menu
    def Context_Menu( self, event ):
        #region Variables

        # Cursor
        QApplication.restoreOverrideCursor()
        # Variables
        self.state_press = False
        self.operation = None
        check_insert = Check_Insert()
        # Path
        if self.pin_index == None:
            pin_tipo = None
            pin_cstate = False
            pin_cl = 0
            pin_ct = 0
            pin_cw = 1
            pin_ch = 1
            pin_egs = False
            pin_efx = False
            pin_efy = False
            pin_url = None
            pin_qpixmap = None
        else:
            pin = self.pin_list[self.pin_index]
            pin_tipo = pin["tipo"]
            pin_cstate = pin["cstate"]
            pin_cl = pin["cl"]
            pin_ct = pin["ct"]
            pin_cw = pin["cw"]
            pin_ch = pin["ch"]
            pin_egs = pin["egs"]
            pin_efx = pin["efx"]
            pin_efy = pin["efy"]
            pin_url = pin["url"]
            pin_qpixmap = pin["qpixmap"]
        # Relative
        list_relative = list()
        list_url = list()
        for i in range( 0, self.pin_count ):
            item = self.pin_list[i]
            if ( item["active"] == True or item["select"] == True ):
                list_relative.append( item )
                list_url.append( item["url"] )
        # Clip
        clip = { "cstate" : pin_cstate, "cl": pin_cl, "ct": pin_ct, "cw": pin_cw, "ch": pin_ch }

        # State
        link_eo_state = self.link_eo_state
        link_kra_state = self.link_kra_state
        # Archive
        link_eo_archive = str()
        link_kra_archive = str()
        if self.link_eo_archive == True:
            link_eo_archive = "[ARCHIVE]"
        if self.link_kra_archive == True:
            link_kra_archive = "[ARCHIVE]"

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )
        # General
        action_fit              = qmenu.addAction( "Fit" )
        # Reference
        menu_ref = qmenu.addMenu( "Reference" )
        action_ref_refresh      = menu_ref.addAction( "Refresh" )
        action_ref_label        = menu_ref.addAction( "Label" )
        action_ref_link         = menu_ref.addAction( "Link" )
        # Board
        menu_board = qmenu.addMenu( "Board" )
        action_link_eo          = menu_board.addAction( f"[EO] { os.path.basename( self.link_eo_url ) } { link_eo_archive }")
        action_link_kra         = menu_board.addAction( f"[KRA] { self.link_kra_name } { link_kra_archive }")
        menu_board.addSection( " " )
        if link_eo_state == True:
            action_eo_new           = menu_board.addAction( "New" )
            action_eo_open          = menu_board.addAction( "Open" )
            action_eo_save          = menu_board.addAction( "Save" )
            action_eo_copy          = menu_board.addAction( "Save As" )
            action_eo_archive       = menu_board.addAction( "Archive" )
        elif link_kra_state == True:
            action_kra_read         = menu_board.addAction( "Read" )
            action_kra_write        = menu_board.addAction( "Write" )
            action_kra_archive      = menu_board.addAction( "Archive" )
            action_kra_unarchive    = menu_board.addAction( "Un-Archive" )
        # Pin
        menu_pin = qmenu.addMenu( "Pin" )
        # Packer
        menu_pack = menu_pin.addMenu( f"Pack [ { self.select_count } ]" )
        action_pack_grid        = menu_pack.addAction( "Linear Grid" )
        action_pack_row         = menu_pack.addAction( "Linear Row" )
        action_pack_column      = menu_pack.addAction( "Linear Column" )
        action_pack_pile        = menu_pack.addAction( "Linear Pile" )
        menu_pack.addSeparator()
        action_pack_area        = menu_pack.addAction( "Optimal Area" )
        action_pack_perimeter   = menu_pack.addAction( "Optimal Perimeter" )
        action_pack_ratio       = menu_pack.addAction( "Optimal Ratio" )
        action_pack_class       = menu_pack.addAction( "Optimal Class" )
        # Reset
        menu_reset = menu_pin.addMenu( "Reset" )
        action_reset_rotation   = menu_reset.addAction( "Rotation" )
        action_reset_scale      = menu_reset.addAction( "Scale" )
        # File
        menu_file = menu_pin.addMenu( "File" )
        action_file_location    = menu_file.addAction( "Open Location" )
        action_file_copy        = menu_file.addAction( "Copy Path" )
        action_file_data        = menu_file.addAction( "Copy Image" )
        # Color
        menu_color = menu_pin.addMenu( "Color" )
        action_color_analyse    = menu_color.addAction( "Color Analyse" )
        action_color_lut        = menu_color.addAction( "LUT to Image" )
        
        # Edit
        menu_edit = menu_pin.addMenu( "Edit" )
        action_edit_grey        = menu_edit.addAction( "View Greyscale" )
        action_edit_flip_h      = menu_edit.addAction( "Flip Horizontal" )
        action_edit_flip_v      = menu_edit.addAction( "Flip Vertical" )
        action_edit_reset       = menu_edit.addAction( "Edit Reset" )
        # Insert
        menu_insert = menu_pin.addMenu( "Insert ")
        action_insert_document  = menu_insert.addAction( "Document" )
        action_insert_layer     = menu_insert.addAction( "Layer" )
        action_insert_reference = menu_insert.addAction( "Reference" )
        # Danger
        menu_pin.addSeparator()
        action_pin_download     = menu_pin.addAction( "Download" )
        action_pin_rebase       = menu_pin.addAction( "Rebase" )
        action_pin_delete       = menu_pin.addAction( "Delete" )
        # Screen
        qmenu.addSeparator()
        action_full_screen      = qmenu.addAction( "Full Screen" )

        # endregion
        #region State

        # Check Board
        action_link_eo.setCheckable( True );        action_link_eo.setChecked( link_eo_state )
        action_link_kra.setCheckable( True );       action_link_kra.setChecked( link_kra_state )
        # Check Edit
        action_edit_grey.setCheckable( True );      action_edit_grey.setChecked( pin_egs )
        action_edit_flip_h.setCheckable( True );    action_edit_flip_h.setChecked( pin_efx )
        action_edit_flip_v.setCheckable( True );    action_edit_flip_v.setChecked( pin_efy )
        # Screen
        action_full_screen.setCheckable( True );    action_full_screen.setChecked( self.state_maximized )

        # Disables
        if self.pin_index == None:
            menu_pin.setEnabled( False )
            menu_reset.setEnabled( False )
            menu_file.setEnabled( False )
            menu_edit.setEnabled( False )
            menu_insert.setEnabled( False )
            action_insert_document.setEnabled( False )
        if self.select_count < 2:
            menu_pack.setEnabled( False )
        if pin_tipo == "label":
            menu_reset.setEnabled( False )
            menu_file.setEnabled( False )
            menu_edit.setEnabled( False )
            menu_insert.setEnabled( False )
            action_pin_download.setEnabled( False )
            action_pin_rebase.setEnabled( False )
        if self.pigmento_picker == None:
            action_color_analyse.setEnabled( False )
        if self.pigmento_sampler == None: 
            action_color_lut.setEnabled( False )
        if check_insert == False:
            action_insert_layer.setEnabled( False )
            action_insert_reference.setEnabled( False )
        if self.state_lock == True:
            action_ref_label.setEnabled( False )
            action_ref_link.setEnabled( False )
            menu_pack.setEnabled( False )
            menu_reset.setEnabled( False )
            menu_edit.setEnabled( False )
            action_pin_download.setEnabled( False )
            action_pin_rebase.setEnabled( False )
            action_pin_delete.setEnabled( False )

        #endregion
        #region Actions

        # Mapping
        action = qmenu.exec_( self.mapToGlobal( event.pos() ) )
        # General
        if action == action_fit:
            self.Board_Fit()
        # Reference
        if action == action_ref_refresh:
            self.Board_Refresh()
        if action == action_ref_label:
            self.Label_Insert( event )
        if action == action_ref_link:
            pos = event.pos()
            self.Pin_URL( pos.x(), pos.y() )
        # Link
        if action == action_link_eo:
            self.Link_EO()
        if action == action_link_kra:
            self.Link_KRA()
        # Board
        if link_eo_state == True:
            if action == action_eo_new:
                self.EO_New()
            if action == action_eo_open:
                self.EO_Open()
            if action == action_eo_save:
                self.EO_Save()
            if action == action_eo_copy:
                self.EO_Copy()
            if action == action_eo_archive:
                self.EO_Archive()
        elif link_kra_state == True:
            if action == action_kra_read:
                self.KRA_Read()
            if action == action_kra_write:
                self.KRA_Write( True )
            if action == action_kra_archive:
                self.KRA_Archive()
            if action == action_kra_unarchive:
                self.KRA_UnArchive()
        # Pack Linear ( loops )
        if action == action_pack_grid:
            self.Packer_Process( "GRID" )
        if action == action_pack_row:
            self.Packer_Process( "ROW" )
        if action == action_pack_column:
            self.Packer_Process( "COLUMN" )
        if action == action_pack_pile:
            self.Packer_Process( "PILE" )
        # Pack Optimal ( loops )
        if action == action_pack_area:
            self.Packer_Process( "AREA" )
        if action == action_pack_perimeter:
            self.Packer_Process( "PERIMETER" )
        if action == action_pack_ratio:
            self.Packer_Process( "RATIO" )
        if action == action_pack_class:
            self.Packer_Process( "CLASS" )
        # Reset ( loops )
        if action == action_reset_rotation:
            self.Reset_Rotation( list_relative )
        if action == action_reset_scale:
            self.Reset_Scale( list_relative )
        # File
        if action == action_file_location:
            File_Open_Location( pin_url )
        if action == action_file_copy:
            File_Copy_Path( pin_url )
        if action == action_file_data:
            File_Copy_Image( pin_url )
        # Color
        if action == action_color_analyse:
            qimage = pin_qpixmap.toImage()
            Color_Analyse( self.pigmento_picker, qimage )
        if action == action_color_lut:
            Color_LUT_to_Image( self.pigmento_sampler, list_url )
        # Edit ( loops )
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
        # Insert
        if action == action_insert_document:
            Insert_Document( self, pin_url, clip )
        if action == action_insert_layer:
            Insert_Layer( self, pin_url, clip )
        if action == action_insert_reference:
            Insert_Reference( self, pin_url, clip )
        # Danger
        if action == action_pin_download:
            self.Relative_Download( list_relative )
        if action == action_pin_rebase:
            self.Relative_Rebase( list_relative )
        if action == action_pin_delete:
            self.Relative_Delete( list_relative )
        # Screen
        if action == action_full_screen:
            self.REFERENCE_FULL_SCREEN.emit( not self.state_maximized )

        #endregion

    # Link
    def Link_EO( self ):
        # Save
        self.KRA_Write( False )
        # Link
        self.link_eo_state = True
        self.link_kra_state = False
        self.Link_State()
        # Switch
        self.EO_Load()
    def Link_KRA( self ):
        # Save
        self.EO_Save()
        # Link
        self.link_eo_state = False
        self.link_kra_state = True
        self.Link_State()
        # Switch
        self.KRA_Read()
    def Link_State( self ):
        Kritarc_Write( DOCKER_NAME, "link_eo_state", self.link_eo_state )
        Kritarc_Write( DOCKER_NAME, "link_kra_state", self.link_kra_state )
    # EO Functions
    def EO_Load( self ):
        if self.link_eo_url != None and os.path.isfile( self.link_eo_url ) == True:
            self.File_Read( self.link_eo_url )
        else:
            self.Board_Empty()
    def EO_New( self ):
        link_eo_url = self.Dialog_Save( "New File Location" )
        if link_eo_url != None:
            exists = os.path.exists( link_eo_url )
            if exists == True:
                Message_Warnning( "ERROR", "new board requires a new url")
            elif exists == False:
                self.link_eo_url = link_eo_url
                self.link_eo_archive = False
                self.Board_Empty()
                self.File_Write( link_eo_url )
    def EO_Open( self ):
        link_eo_url = self.Dialog_Load( "Open File Location" )
        if link_eo_url != None:
            self.link_eo_url = link_eo_url
            self.File_Read( self.link_eo_url )
            Kritarc_Write( DOCKER_NAME, "link_eo_url", self.link_eo_url )
    def EO_Save( self ):
        if ( self.link_eo_url != None ) and ( os.path.isfile( self.link_eo_url ) == True ) and ( self.link_eo_archive == False ):
            self.File_Write( self.link_eo_url )
    def EO_Copy( self ):
        link_eo_url = self.Dialog_Save( "Copy File Location" )
        if link_eo_url != None and self.link_eo_url != link_eo_url:
            self.link_eo_url = link_eo_url
            self.link_eo_archive = False
            self.File_Write( link_eo_url )
    def EO_Archive( self ):
        archive_url = self.Dialog_Save( "Archive File Location" )
        if archive_url != None:
            if self.link_eo_url == archive_url:
                self.link_eo_archive = True
            self.File_Archive( archive_url )
    # KRA Functions
    def KRA_Read( self ):
        if self.link_kra_access != None:
            self.link_kra_archive = False
            file_name = self.link_kra_access.fileName()
            annotation = self.link_kra_access.annotation( DOCKER_NAME )
            decode = bytes( annotation ).decode( encode )
            if len( decode ) > 0:
                board = decode.split( "\n" )
                self.Data_Read( board )
            else:
                self.link_kra_access.removeAnnotation( DOCKER_NAME )
                self.Board_Empty()
        else:
            self.Board_Empty()
    def KRA_Write( self, save ):
        if ( self.link_kra_access != None ) and ( self.link_kra_archive == False ):
            self.link_kra_archive = False
            data = self.Data_Write()
            self.link_kra_access.setAnnotation( DOCKER_NAME, "Document", QByteArray( data.encode() ) )
            if save == True:
                self.link_kra_access.save()
    def KRA_Archive( self ):
        if self.link_kra_access != None:
            self.link_kra_archive = True
            data = self.Data_Archive()
            self.link_kra_access.setAnnotation( DOCKER_NAME, "Document", QByteArray( data.encode() ) )
            self.link_kra_access.save()
    def KRA_UnArchive( self ):
        if self.link_kra_access != None:
            self.link_kra_archive = False
            data = self.Data_Write()
            self.link_kra_access.setAnnotation( DOCKER_NAME, "Document", QByteArray( data.encode() ) )
            self.Board_Render()
    # Dialog
    def Dialog_Load( self, title ):
        # Variables
        directory = str()
        if self.link_eo_state == True:
            directory = self.link_eo_url
        # File Dialog
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        file_url = file_dialog.getOpenFileName( self, title, directory, "File( *.eo )" )[0]
        file_url = os.path.normpath( file_url )
        if file_url in invalid:
            file_url = None
        return file_url
    def Dialog_Save( self, title ):
        # Variabels
        directory = str()
        if self.link_eo_state == True:
            directory = self.link_eo_url
        elif self.link_kra_state == True:
            if ( self.link_kra_access != None ):
                name = self.link_kra_name.split( "." )[0]
                directory = os.path.join( dirname, f"{ name }.eo")
        # File Dialog
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        file_url = file_dialog.getSaveFileName( self, title, directory, "File( *.eo )" )[0]
        file_url = os.path.normpath( file_url )
        if file_url in invalid:
            file_url = None
        return file_url
    # File
    def File_Read( self, url ):
        with open( url, "r", encoding=encode ) as self.link_eo_access:
            board = self.link_eo_access.readlines()
            self.Data_Read( board )
    def File_Write( self, url ):
        data = self.Data_Write()
        self.File_Access( url, data )
    def File_Archive( self, url ):
        data = self.Data_Archive()
        self.File_Access( url, data )
    def File_Access( self, url, data ):
        if self.link_eo_access == None or self.link_eo_access.closed == True:
            with open( url, "w", encoding=encode ) as self.link_eo_access:
                    self.link_eo_access.write( data )
    # Data
    def Data_Read( self, board ):
        # Variables
        count = len( board )
        if self.link_eo_state == True:   self.link_eo_archive = False
        if self.link_kra_state == True:  self.link_kra_archive = False
        # Progress Bar
        self.ProgressBar_Value( 0 )
        self.ProgressBar_Maximum( count )
        # Construct Board
        pin_list = list()
        camera_zoom = 1
        camera_position = [ 1, 1 ]
        if len( board ) > 0 and board[0].startswith( DOCKER_NAME ) == True:
            for i in range( 1, count ):
                # Progress Bar
                self.ProgressBar_Value( i+1 )
                QApplication.processEvents()
                # Cycle
                try:
                    # Formating
                    line = board[i].replace( "\n", "" )
                    # Evaluation
                    if line.endswith( "reference_archive" ) == True or line.endswith( "data" ) == True:
                        if self.link_eo_state == True:   self.link_eo_archive = True
                        if self.link_kra_state == True:  self.link_kra_archive = True
                    elif line.startswith( "ref_camera_position=" ) == True or line.startswith( "camera_position=" ) == True:
                        line = line.replace( "ref_", "" )
                        line = line.replace( "camera_position=", "" )
                        camera_position = eval( line )
                    elif line.startswith( "ref_camera_zoom=" ) == True or line.startswith( "camera_zoom=" ) == True:
                        line = line.replace( "ref_", "" )
                        line = line.replace( "camera_zoom=", "" )
                        camera_zoom = float( line )
                    elif line.startswith( "{" ) and line.endswith( "}" ): # Dictionary
                        # Variables
                        qpixmap = None
                        # Read
                        line = eval( line )
                        cstate = line["cstate"]
                        cl = line["cl"]
                        ct = line["ct"]
                        cw = line["cw"]
                        ch = line["ch"]
                        # URL
                        try: # Current Version
                            url = line["url"]
                        except: # Previous Version
                            path = line["path"]
                            web = line["web"]
                            if    path != None: url = os.path.normpath( path )
                            elif  web  != None: url = web
                            line["url"] = url
                            line.pop( "path" )
                            line.pop( "web" )
                        # ZArchive
                        try: # Current Version
                            zarchive = line["zarchive"]
                        except: # Previous Version
                            zarchive = line["zdata"]
                            line["zarchive"] = zarchive
                            line.pop( "zdata" )
                        # Load
                        if os.path.isfile( url ): # Local
                            reader = QImageReader( url )
                            pix = QPixmap().fromImageReader( reader )
                            if pix.isNull() == False:
                                qpixmap = pix
                        elif Check_Html( url ): # internet
                            pix = Download_QPixmap( url )
                            if pix.isNull() == False:
                                qpixmap = pix
                        elif zarchive != None: # Import
                            # Buffer
                            byte_array = QByteArray( zarchive )
                            buffer = QBuffer()
                            buffer.setData( byte_array )
                            buffer.open( QIODevice.OpenModeFlag.ReadOnly )
                            reader = QImageReader( buffer )
                            if reader.canRead() == True:
                                qpixmap = QPixmap().fromImageReader( reader )
                        # Copy
                        check_qpixmap = qpixmap != None
                        if check_qpixmap:
                            if cstate == True:
                                w = qpixmap.width()
                                h = qpixmap.height()
                                qpixmap = qpixmap.copy( int( w * cl ), int( h * ct ), int( w * cw ), int( h * ch ) )
                            line["qpixmap"] = qpixmap
                        # Construct
                        pin_list.append( line )
                        if check_qpixmap:
                            del qpixmap
                except:
                    pass
        # Preview & Grid
        if self.pin_list != pin_list:
            self.pin_list = pin_list
        # Reference
        self.Board_Load( pin_list )
        self.Camera_Load( camera_position, camera_zoom )
        # Progress Bar
        self.ProgressBar_Value( 0 )
        self.ProgressBar_Maximum( 1 )
    def Data_Write( self ):
        # Variables
        data = ""
        count = len( self.pin_list )
        # Construct Board
        if len( self.pin_list ) > 0:
            # Header
            data = DOCKER_NAME
            # Type of save
            data += f"\nreference_connect"
            # Camera
            data += f"\ncamera_position={ self.cam_p }"
            data += f"\ncamera_zoom={ self.cam_z }"
            # Cycle
            for i in range( 0, count ):
                # Item
                item = self.pin_list[i]
                line = item.copy()
                line["qpixmap"] = None
                line["draw"] = None
                line["zarchive"] = None
                data += f"\n{ line }"
        # Return
        return data
    def Data_Archive( self ):
        # Variables
        data = ""
        count = len( self.pin_list )
        # Progress Bar
        self.ProgressBar_Value( 0 )
        self.ProgressBar_Maximum( count )
        # Construct Board
        if len( self.pin_list ) > 0:
            # Header
            data = DOCKER_NAME
            # Type of save
            data += f"\nreference_archive"
            # Camera
            data += f"\ncamera_position={ self.cam_p }"
            data += f"\ncamera_zoom={ self.cam_z }"
            # Cycle
            for i in range( 0, count ):
                # Progress Bar
                self.ProgressBar_Value( i+1 )
                QApplication.processEvents()
                # Read
                item = self.pin_list[i]
                line = item.copy()
                url = line["url"]
                # ZData
                if os.path.isfile( url ): # Local
                    line["zarchive"] = self.Bytes_Python( url )
                elif Check_Html( url ): # Internet
                    line["zarchive"] = Download_Data( url )
                else:
                    line["zarchive"] = None
                # Clean
                line["qpixmap"] = None
                line["draw"] = None
                # String
                data += f"\n{ line }"
        # Progress Bar
        self.ProgressBar_Value( 0 )
        self.ProgressBar_Maximum( 1 )
        # Return
        return data
    # Bytes
    def Bytes_QPixmap( self, qpixmap ):
        extension = "PNG" # "PNG" "JPG"
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer( ba )
        buffer.open( QtCore.QIODevice.WriteOnly )
        ok = qpixmap.save( buffer, extension )
        assert ok
        pixmap_bytes = ba.data()
        return pixmap_bytes
    def Bytes_Python( self, url ):
        with open( url, "rb" ) as f:
            data = f.read()
        return data

    # Packer
    def Packer_Interrupt( self ):
        try:self.packer_worker.Stop()
        except:pass
    def Packer_Process( self, mode ):
        if self.select_count > 0:
            # Variables
            self.state_pack = True
            # Widget
            self.setEnabled( False )
            self.REFERENCE_PACKER.emit( True )
            # Pin
            self.Selection_Raise()
            # Packer
            thread = True
            if thread == False: self.Packer_Single( thread, mode )
            if thread == True:  self.Packer_Thread( thread, mode )
    def Packer_Connect( self ):
        self.state_cycle = True
        self.packer_worker = Worker_Packer()
        self.packer_worker.PACKER_CYCLE.connect( self.Packer_Cycle )
        self.packer_worker.PACKER_PB_VALUE.connect( self.ProgressBar_Value )
        self.packer_worker.PACKER_PB_MAX.connect( self.ProgressBar_Maximum )
        self.packer_worker.PACKER_FINISH.connect( self.Packer_Finish )
    def Packer_Single( self, thread, mode ):
        self.Packer_Connect()
        self.packer_worker.run( self, thread, mode )
    def Packer_Thread( self, thread, mode ):
        # Thread
        self.packer_qthread = QtCore.QThread()
        # Worker
        self.Packer_Connect()
        self.packer_worker.moveToThread( self.packer_qthread )
        # Thread
        self.packer_qthread.started.connect( lambda : self.packer_worker.run( self, thread, mode ) )
        self.packer_qthread.start()
    def Packer_Cycle( self, boolean ):
        self.REFERENCE_PACKER.emit( boolean )
    def Packer_Finish( self, thread ):
        # Thread
        if thread == True:
            self.packer_qthread.quit()
        # Variables
        self.state_pack = False
        self.Pin_Previous()
        # Widget
        self.REFERENCE_PACKER.emit( False )
        self.setEnabled( True )
        # Update
        self.update()

    # Reset
    def Reset_Rotation( self, lista ):
        self.Pin_Previous()
        for item in lista:
            index = item["index"]
            angle = -self.pin_list[index]["trz"]
            self.Rotate_Transform( self.pin_previous, index, angle )
            self.Pin_Draw_QPixmap( self.pin_list, index )
    def Reset_Scale( self, lista ):
        self.Pin_Previous()
        for pin in lista:
            index = pin["index"]
            self.Scale_Reset( self.pin_previous, index )
            self.Pin_Draw_QPixmap( self.pin_list, index )
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
    # Relative
    def Relative_Download( self, lista ):
        # Select Location
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        directory = file_dialog.getExistingDirectory( self, f"Download to Directory" )
        # Save Files
        if directory not in invalid:
            # Variables
            count = len( lista )
            # Progress Bar
            self.REFERENCE_PB_VALUE.emit( 0 )
            self.REFERENCE_PB_MAX.emit( count )
            # Cycle
            for i in range( 0, count ):
                try:
                    # Progress
                    if i % 5 == 0:
                        self.REFERENCE_PB_VALUE.emit( i + 1 )
                        QApplication.processEvents()
                    # Read
                    url = lista[i]["url"]
                    # Variables
                    qpixmap = None
                    basename = os.path.basename( url )
                    saveto = os.path.normpath( os.path.join( directory, basename ) )
                    if os.path.exists( saveto ) == False:
                        # Checks
                        check_file = os.path.isfile( url )
                        check_web = Check_Html( url )
                        # QPixmap
                        if check_file:
                            reader = QImageReader( url )
                            if reader.canRead() == True:
                                reader.setAutoTransform( True )
                                pix = QPixmap().fromImageReader( reader )
                                qpixmap = pix
                        elif check_web:
                            qpixmap = Download_QPixmap( url )
                        if qpixmap != None:
                            boolean = qpixmap.save( saveto )
                            if boolean == True: string = f"{ DOCKER_NAME } | DOWNLOAD { saveto }"
                            else:               string = f"{ DOCKER_NAME } | ERROR { url }"
                            try:QtCore.qDebug( string )
                            except:pass
                except:
                    pass
            # Progress Bar
            self.REFERENCE_PB_VALUE.emit( 0 )
            self.REFERENCE_PB_MAX.emit( 1 )
    def Relative_Rebase( self, lista ):
        # Variables
        count = self.pin_count
        previous_url = str()
        suggestion = str()
        previous_url = lista[0]["url"]
        # Directory
        list_url = list()
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        directory = file_dialog.getExistingDirectory( self, f"Select Directory - previous_url = { previous_url }", os.path.dirname( previous_url ) )
        if directory not in invalid:
            qdir = QDir( directory )
            qdir.setSorting( QDir.Name )
            qdir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            qdir.setNameFilters( file_normal )
            # Recursive Search
            if self.state_rebase == True:   recursive = QDirIterator.Subdirectories
            else:                           recursive = QDirIterator.NoIteratorFlags
            # Files
            it = QDirIterator( qdir, recursive )
            while( it.hasNext() ):
                it_url = os.path.normpath( it.next() )
                list_url.append( it_url )
        # Search Cycles
        path_old = list()
        for i in range( 0, self.pin_count ):
            item = self.pin_list[i]
            url = item["url"]
            if os.path.isfile( url ):
                reader = QImageReader( url )
                qpixmap = QPixmap().fromImageReader( reader )
                if qpixmap.isNull() == False:
                    item["qpixmap"] = qpixmap
                    item["draw"] = self.Pin_Draw_QPixmap( self.pin_list, i )
                else:
                    item["qpixmap"] = None
                    item["draw"] = None
                path_old.append( url )
        # Lista
        for item in lista:
            # Read
            tipo = item["tipo"]
            bx = item["bx"]
            by = item["by"]
            cstate = item["cstate"]
            cl = item["cl"]
            ct = item["ct"]
            cw = item["cw"]
            ch = item["ch"]
            url = item["url"]
            qpixmap = item["qpixmap"]
            # Path
            basename = os.path.basename( url )
            if ( tipo == "image" and qpixmap == None ):
                for fp in list_url:
                    fn = os.path.basename( fp )
                    if basename == fn and fp not in path_old:
                        delta = 20
                        clip = { "cstate":cstate, "cl":cl, "ct":ct, "cw":cw, "ch":ch }
                        self.REFERENCE_PIN_INSERT.emit( "image", bx + delta, by + delta, None, fp, clip )
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

    # Mouse Events
    def mousePressEvent( self, event ):
        # Variable
        self.state_press = True
        # Event
        em = event.modifiers()
        eb = event.buttons()
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
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton:
            if self.state_pickcolor == True:
                self.operation = "color_picker"
                ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
            if self.state_pickcolor == False:
                if self.pin_index == None:
                    self.operation = "select_replace"
                else:
                    self.operation = "pin_move"
                    self.pin_node = 0
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "camera_move"
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "select_add"
            self.Selection_Click( self.pin_index )
        if em == QtCore.Qt.AltModifier and eb == QtCore.Qt.LeftButton:
            self.operation = "drag_drop"
            self.Clip_Pin()
        if em == ( QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier ) and eb == QtCore.Qt.LeftButton:
            self.operation = "pin_transform"
        if em == ( QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier ) and eb == QtCore.Qt.LeftButton:
            self.Pin_Preview( self.pin_index )
        # MMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.MiddleButton:
            self.operation = "camera_move"
        # RMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.RightButton:
            self.dirty = False
            self.operation = None
            self.Context_Menu( event )
        if em == QtCore.Qt.ShiftModifier and eb == QtCore.Qt.RightButton:
            self.operation = "camera_scale"
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.RightButton:
            self.operation = "select_minus"
            self.Selection_Click( self.pin_index )
        if em == QtCore.Qt.AltModifier and eb == QtCore.Qt.RightButton:
            self.operation = "drag_drop"
            self.Clip_Pin()
        # Update
        self.Cursor_Shape( self.operation, self.pin_node )
        self.update()
    def mouseMoveEvent( self, event ):
        # Variable
        self.state_press = True
        # Event
        em = event.modifiers()
        eb = event.buttons()
        ex = event.x()
        ey = event.y()
        self.ex = ex
        self.ey = ey
        # Operations
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, True )
        if self.operation == "pin_move" and self.state_lock == False:
            dx, dy = self.Point_Deltas( ex, ey )
            if em == QtCore.Qt.NoModifier:
                self.Move_Pin( dx, dy, False )
            else:
                self.Move_Pin( dx, dy, True )
            self.dirty = True
        if self.operation == "pin_transform" and self.state_lock == False:
            self.Pin_Transform( ex, ey, self.pin_node )
            self.dirty = True
        if self.operation == "camera_move":
            self.Camera_Move( ex, ey ) 
            self.dirty = True
        if self.operation == "camera_scale":
            self.Camera_Scale( ex, ey )
            self.dirty = True
        if self.operation == "select_add":
            self.Selection_Box( ex, ey, "add" )
            self.dirty = True
        if self.operation == "select_minus":
            self.Selection_Box( ex, ey, "minus" )
            self.dirty = True
        if self.operation == "select_replace":
            self.Selection_Box( ex, ey, "replace" )
            self.dirty = True
        if self.operation == "drag_drop":
            Insert_Drag( self, self.pin_url, self.clip_pin, False )
            self.dirty = True
        # Update
        self.update()
    def mouseDoubleClickEvent( self, event ):
        # Event
        em = event.modifiers()
        eb = event.buttons()
        ex = event.x()
        ey = event.y()
        # LMB
        if em == QtCore.Qt.NoModifier and eb == QtCore.Qt.LeftButton:
            self.Pin_Index( ex, ey )
            self.Pin_Preview( self.pin_index )
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.LeftButton:
            self.Selection_All()
        # RMB
        if em == QtCore.Qt.ControlModifier and eb == QtCore.Qt.RightButton:
            self.Selection_Clear()
    def mouseReleaseEvent( self, event ):
        # Variables
        self.drop = False
        self.drag = False
        # Color Picker
        if self.operation == "color_picker":
            ColorPicker_Event( self, self.ex, self.ey, self.qimage_grab, False )
        # Release
        self.Release_Event()
    def Release_Event( self ):
        # Variables General
        self.state_press = False
        self.operation = None
        self.select_box = False
        # Variables Pin
        self.Pin_Update()
        self.Pin_Previous()
        self.pin_index = None
        self.pin_url = None
        self.pin_basename = None
        self.pin_node = None
        self.pin_count = len( self.pin_list )
        # Variables Limit
        self.limit_x = list()
        self.limit_y = list()

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
        angle = 5
        delta_y = event.angleDelta().y()
        if delta_y >= angle:    self.Camera_Zoom_Step( +1 )
        if delta_y <= -angle:   self.Camera_Zoom_Step( -1 )
        # Update
        self.update()
    # Drag and Drop Event
    def dragEnterEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.drop = True
            event.accept()
        else:
            event.ignore()
        self.update()
    def dragMoveEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
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
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            if ( self.drop == True and self.drag == False and self.state_lock == False ):
                # Event
                event.setDropAction( Qt.CopyAction )
                pos = event.pos()
                bx, by = self.Point_Location( pos.x(), pos.y() )
                # Variables
                self.state_press = True
                self.drop = False
                count = len( mime_data )
                # Progress Bar
                self.ProgressBar_Value( 0 )
                self.ProgressBar_Maximum( count )
                # Pin References
                for i in range( 0, count ):
                    # Progress Bar
                    self.ProgressBar_Value( i + 1 )
                    QApplication.processEvents()
                    # Pin
                    self.REFERENCE_PIN_INSERT.emit( "image", bx, by, None, mime_data[i], clip_false )
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
            selection = list()
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
        try:self.packer_qthread.quit()
        except:pass
        # Garbage
        self.Garbage_Clean()
    # Painter Event
    def paintEvent( self, event ):
        # Variables
        ww = self.ww
        hh = self.hh
        w2 = self.w2
        h2 = self.h2
        side = min( ww, hh )
        self.pin_count = len( self.pin_list )

        # Painter
        painter = QPainter( self )
        painter.setRenderHint( QtGui.QPainter.Antialiasing, True )

        # Mask
        painter.setClipRect( QRect( int( 0 ), int( 0 ), int( ww ), int( hh ) ), Qt.ReplaceClip )

        """
        # Board Scalling
        painter.setPen( QPen( self.c_lite, 1, Qt.SolidLine ) )
        painter.setBrush( QtCore.Qt.NoBrush )
        dl = w2 - w2 * self.cam_z
        dt = h2 - h2 * self.cam_z
        dw = ww * self.cam_z
        dh = hh * self.cam_z
        dr = dl + dw
        db = dt + dh
        painter.drawRect( int(dl), int(dt), int(dw), int(dh) )
        """

        # Board
        if self.state_press == False:
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( color_alpha ) )
            painter.drawRect( int( self.board_l ), int( self.board_t ), int( self.board_w ), int( self.board_h ) )
        # No References Square
        if ( self.pin_count == 0 and self.drop == False ):
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( self.c_dark ) )
            nrs = 0.2 * side
            nrwm = int( w2 - nrs )
            nrwp = int( w2 + nrs )
            nrhm = int( h2 - nrs )
            nrhp = int( h2 + nrs )
            poly_quad = QPolygon( [
                QPoint( nrwm, nrhm ),
                QPoint( nrwp, nrhm ),
                QPoint( nrwp, nrhp ),
                QPoint( nrwm, nrhp ),
                ] )
            painter.drawPolygon( poly_quad )

        # Lost Pins
        if ( self.state_press == False and self.pin_count > 0 ):
            valid = ( self.board_l >= ww ) or ( self.board_r <= 0 ) or ( self.board_t >= hh ) or ( self.board_b <= 0 )
            if valid == True:
                # Variables
                bw2 = self.board_l + self.board_w * 0.5
                bh2 = self.board_t + self.board_h * 0.5
                dot = 5
                # Line
                painter.setPen( QPen( self.c_lite, 2, Qt.SolidLine ) )
                painter.setBrush( QtCore.Qt.NoBrush )
                painter.drawLine( int( w2 ), int( h2 ), int( bw2 ), int( bh2 ) )
                # Dot
                painter.setPen( QtCore.Qt.NoPen )
                painter.setBrush( QBrush( self.c_lite ) )
                painter.drawEllipse( int( w2 - dot ), int( h2 - dot ), int( dot * 2 ), int( dot * 2 ) )

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
                        painter.setPen( QPen( self.c_lite, 1, Qt.SolidLine ) )
                        painter.setBrush( QBrush( self.c_dark ) )
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

                    letter_size = int( letter * self.cam_z )
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
                        painter.drawText( box, QtCore.Qt.AlignCenter|QtCore.Qt.TextWordWrap, text )
                        # Garbage
                        del qfont

        # Decorators
        if self.state_pickcolor == False:
            # Dots Over
            if ( self.select_box == True or self.state_select == True ):
                # Variables
                sel_hor = list()
                sel_ver = list()
                # Painter
                painter.setPen( QtCore.Qt.NoPen )
                painter.setBrush( QBrush( self.c_select, Qt.Dense4Pattern ) )
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
                painter.setPen( QPen( self.c_select, 1, Qt.SolidLine ) )
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
                painter.setPen( QPen( self.c_dark, 1, Qt.SolidLine ) )
                painter.setBrush( QtCore.Qt.NoBrush )
                painter.drawRect( int( dl ), int( dt ), int( dw ), int( dh ) )

                # Triangle
                min_tri = 20
                if ( ww > min_tri and hh > min_tri ):
                    # Variables
                    tri = 10
                    painter.setPen( QPen( color_black, 1, Qt.SolidLine ) )
                    # Scale 1
                    if self.pin_node == 1:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_t1 = QPolygon( [
                        QPoint( int( dl ),       int( dt ) ),
                        QPoint( int( dl + tri ), int( dt ) ),
                        QPoint( int( dl ),       int( dt + tri ) ),
                        ] )
                    painter.drawPolygon( poly_t1 )
                    # scale 3
                    if self.pin_node == 3:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_t3 = QPolygon( [
                        QPoint( int( dr ),       int( dt ) ),
                        QPoint( int( dr ),       int( dt + tri ) ),
                        QPoint( int( dr - tri ), int( dt ) ),
                        ] )
                    painter.drawPolygon( poly_t3 )
                    # Scale 7
                    if self.pin_node == 7:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_t7 = QPolygon( [
                        QPoint( int( dl ),       int( db ) ),
                        QPoint( int( dl ),       int( db - tri ) ),
                        QPoint( int( dl + tri ), int( db ) ),
                        ] )
                    painter.drawPolygon( poly_t7 )
                    # Scale 9
                    if self.pin_node == 9:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
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
                    painter.setPen( QPen( color_black, 1, Qt.SolidLine ) )
                    # Clip 2
                    if self.pin_node == 2:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_s2 = QPolygon( [
                        QPoint( int( dl + dw2 - sq ), int( dt ) ),
                        QPoint( int( dl + dw2 - sq ), int( dt + sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( dt + sq ) ),
                        QPoint( int( dl + dw2 + sq ), int( dt ) ),
                        ] )
                    painter.drawPolygon( poly_s2 )
                    # Clip 4
                    if self.pin_node == 4:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_s4 = QPolygon( [
                        QPoint( int( dl ),      int( dt + dh2 - sq ) ),
                        QPoint( int( dl + sq ), int( dt + dh2 - sq ) ),
                        QPoint( int( dl + sq ), int( dt + dh2 + sq ) ),
                        QPoint( int( dl ),      int( dt + dh2 + sq ) ),
                        ] )
                    painter.drawPolygon( poly_s4 )
                    # Clip 6
                    if self.pin_node == 6:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                    poly_s6 = QPolygon( [
                        QPoint( int( dr ),      int( dt + dh2 - sq ) ),
                        QPoint( int( dr - sq ), int( dt + dh2 - sq ) ),
                        QPoint( int( dr - sq ), int( dt + dh2 + sq ) ),
                        QPoint( int( dr ),      int( dt + dh2 + sq ) ),
                        ] )
                    painter.drawPolygon( poly_s6 )
                    # Clip 8
                    if self.pin_node == 8:  painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                    else:                   painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
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
                        painter.setPen( QPen( color_black, 4, Qt.SolidLine ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( cir_x ), int( cir_y ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( neu_x ), int( neu_y ) )
                        painter.setPen( QPen( color_white, 2, Qt.SolidLine ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( cir_x ), int( cir_y ) )
                        painter.drawLine( int( dl + dw2 ), int( dt + dh2 ), int( neu_x ), int( neu_y ) )
                        # Circle
                        painter.setPen( QPen( color_black, 1, Qt.SolidLine ) )
                        painter.setBrush( QBrush( self.c_chrome, Qt.SolidPattern ) )
                        painter.drawEllipse( int( dl + dw2 - cir ), int( dt + dh2 - cir ), int( 2 * cir ), int( 2 * cir ) )
                    else:
                        painter.setPen( QPen( color_black, 1, Qt.SolidLine ) )
                        painter.setBrush( QBrush( color_white, Qt.SolidPattern ) )
                        painter.drawEllipse( int( dl + dw2 - cir ), int( dt + dh2 - cir ), int( 2 * cir ), int( 2 * cir ) )

        # Cursor Selection Square
        if ( self.state_press == True and self.select_box == True and self.state_pack == False ):
            painter.setPen( QPen( self.c_chrome, 2, Qt.SolidLine ) )
            painter.setBrush( QBrush( self.c_chrome, Qt.Dense7Pattern ) )
            sx = min( self.ox, self.ex )
            sy = min( self.oy, self.ey )
            sw = abs( self.ex - self.ox )
            sh = abs( self.ey - self.oy )
            painter.drawRect( int( sx ), int( sy ), int( sw ), int( sh ) )

        # Pixmap Preview
        if self.pin_preview != None:
            # Back Drop
            painter.setPen( QtCore.Qt.NoPen )
            painter.setBrush( QBrush( color_alpha ) )
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
            if self.state_lock == False:
                Painter_Triangle( painter, w2, h2, side, self.c_chrome )
            elif self.state_lock == True:
                Painter_Locked( painter, w2, h2, side, self.c_chrome )

        """
        # Packing Points
        v = 255
        dot = 20 * self.cam_z
        painter.setPen( QPen( self.c_dark, 2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin ) )
        for item in self.p:
            px = w2 + ( item[0] - w2 ) * self.cam_z
            py = h2 + ( item[1] - h2 ) * self.cam_z
            valid = item[2]
            if valid == True:
                painter.setBrush( QBrush( QColor( 0, v, 0 ) ) )
            elif valid == False:
                painter.setBrush( QBrush( QColor( v, 0, 0 ) ) )
            elif valid == None:
                painter.setBrush( QBrush( self.c_lite ) )
            painter.drawEllipse( int( px - dot ), int( py - dot ), int( dot * 2 ), int( dot * 2 ) )

            # # Point location Text
            # painter.setBrush( QtCore.Qt.NoBrush )
            # painter.setPen( QPen( QColor( self.c_lite ), 1, Qt.SolidLine ) )
            # qfont = QFont( self.label_font, int( 8 * self.cam_z ) )
            # painter.setFont( qfont )
            # box = QRect( int( px ), int( py ), int( 100*self.cam_z ), int( 20*self.cam_z ) )
            # text = f"( {item[0]} , {item[1]} )"
            # painter.drawText( box, Qt.AlignCenter, text )
            # # Garbage
            # del qfont
        """

#endregion
#region Threads

# Grid
class Worker_Reader( QtCore.QObject ):
    GRID_READER = QtCore.pyqtSignal( int, list, float )

    def run( self, source, index, grid_url, gtw, gth, state_fit, grid_method ):
        # Variables
        qpixmap = None
        size = 0
        # File
        if os.path.isfile( grid_url ) == True:
            # Reader
            reader = QImageReader( grid_url )
            check_read = reader.canRead()
            check_anim = reader.supportsAnimation()
            check_comp = zipfile.is_zipfile( grid_url )
            if check_read == True and check_comp == False:
                # Static
                if check_anim == False:
                    qpixmap, size = Fit_Image( reader, gtw, gth, state_fit )
                # Animation
                elif check_anim == True:
                    qpixmap, size = Fit_Image( reader, gtw, gth, state_fit )
            # Compressed
            elif check_comp == True:
                qpixmap, size = Fit_Compressed( grid_url, gtw, gth, state_fit )
        # Directory
        elif os.path.isdir( grid_url ) == True:
            qpixmap, size = Fit_Directory( grid_url, gtw, gth )
        # HTML
        elif Check_Html( grid_url ) == True:
            qpixmap = Download_QPixmap( grid_url )
            if qpixmap != None:
                qpixmap, size = Fit_QPixmap( qpixmap, gtw, gth, state_fit, grid_method )
        # Return
        self.GRID_READER.emit( index, [qpixmap], size )

# Reference
class Worker_Packer( QtCore.QObject ):
    PACKER_CYCLE = QtCore.pyqtSignal( bool )
    PACKER_PB_VALUE = QtCore.pyqtSignal( int )
    PACKER_PB_MAX = QtCore.pyqtSignal( int )
    PACKER_FINISH = QtCore.pyqtSignal( bool )

    # Run Packer
    def run( self, source, thread, mode ):
        # Variables
        self.cycle = False
        pin_list = source.pin_list
        count = len( pin_list )
        pack_area = 1

        # Time Watcher
        start = QtCore.QDateTime.currentDateTimeUtc()

        # List Packs
        perfect_area = 0
        pack_sort = list() # Yes Packing
        pack_other = list() # No Packing
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
        self.PACKER_PB_MAX.emit( count - 1 )
        self.PACKER_PB_VALUE.emit( 0 )

        # Packing
        if mode in ( "GRID", "ROW", "COLUMN", "PILE" ):       pack_area = self.Pack_Linear(  source, mode, pack_sort, pack_other, pin_list )
        if mode in ( "AREA", "PERIMETER", "RATIO", "CLASS" ): pack_area = self.Pack_Optimal( source, mode, pack_sort, pack_other, pin_list )
        # Efficiency
        efficiency = round( ( perfect_area / pack_area ) * 100, 3 )

        # Progress Bar
        self.PACKER_PB_MAX.emit( 1 )
        self.PACKER_PB_VALUE.emit( 0 )

        # Time Watcher
        end = QtCore.QDateTime.currentDateTimeUtc()
        delta = start.msecsTo( end )
        time = QTime( 0,0 ).addMSecs( delta )

        # Print
        string = f"{ DOCKER_NAME } | PACK { time.toString( 'hh:mm:ss.zzz' ) } | COUNT { count } | METHOD { mode } | EFFICIENCY { efficiency } %"
        try:QtCore.qDebug( string )
        except:pass

        # Stop Worker
        self.PACKER_FINISH.emit( thread )

    # Cycle Control
    def Stop( self ):
        self.cycle = True
    def Cycle_Interruption( self, stop ):
        if stop == True:
            message = "Continue Packing ?"
            loop = QMessageBox.question( QWidget(), DOCKER_NAME, message, QMessageBox.Yes, QMessageBox.Abort )
            if loop == QMessageBox.Yes:
                self.PACKER_CYCLE.emit( True )
                stop = False
            if loop == QMessageBox.Abort:
                self.PACKER_CYCLE.emit( False )
                stop = True
        return stop

    # Cycles
    def Pack_Linear( self, source, mode, pack_sort, pack_other, pin_list ):
        # Sorting List
        if mode in ( "GRID", "ROW" ):
            pack_sort = sorted( pack_sort, reverse=True, key=lambda entry:entry["bh"] )
        if mode == "COLUMN":
            pack_sort = sorted( pack_sort, reverse=True, key=lambda entry:entry["bw"] )
        if mode == "PILE":
            pack_sort = sorted( pack_sort, reverse=False, key=lambda entry:entry["area"] )

        # Starting Points
        start_x = min( self.List_Key( pack_sort, "bl" ) )
        start_y = min( self.List_Key( pack_sort, "bt" ) )
        if mode == "GRID":
            total_area = 0
            for i in range( 0, len( pack_sort ) ):
                total_area += pack_sort[i]["area"]
            side = math.sqrt( total_area )
            end_x = start_x + side
        if mode == "PILE":
            lx = max( self.List_Key( pack_sort, "bw" ) )
            ly = max( self.List_Key( pack_sort, "bh" ) )

        # Apply to Reference List
        for s in range( 0, len( pack_sort ) ):
            # Progress Bar
            if s % 5 == 0:
                self.PACKER_PB_VALUE.emit( s + 1 )
                QApplication.processEvents()
            # Stop Cycle
            self.cycle = self.Cycle_Interruption( self.cycle )
            if self.cycle == True:
                self.cycle = False
                break

            # Index
            pin_index = pack_sort[s]["index"]

            # Calculation
            if s == 0:
                if mode in ( "GRID", "ROW", "COLUMN" ):
                    px = start_x
                    py = start_y
                if mode == "GRID":
                    above = start_y + pack_sort[s]["bh"]
                if mode == "PILE":
                    px = start_x - pack_sort[s]["bw"] * 0.5 + lx * 0.5
                    py = start_y - pack_sort[s]["bh"] * 0.5 + ly * 0.5
            else:
                if mode == "GRID":
                    if pack_sort[s-1]["br"] >= end_x:
                        px = start_x
                        py = above
                        above += pack_sort[s]["bh"]
                    else:
                        px = pack_sort[s-1]["br"]
                        py = pack_sort[s-1]["bt"]
                if mode == "ROW":
                    px = pack_sort[s-1]["br"]
                    py = pack_sort[s-1]["bt"]
                if mode == "COLUMN":
                    px = pack_sort[s-1]["bl"]
                    py = pack_sort[s-1]["bb"]
                if mode == "PILE":
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
    def Pack_Optimal( self, source, mode, pack_sort, pack_other, pin_list ):
        # Sorting List
        if mode == "AREA":
            pack_sort = sorted( pack_sort, reverse=True, key = lambda entry:entry["area"] )
        if mode == "PERIMETER":
            pack_sort = sorted( pack_sort, reverse=True, key = lambda entry:entry["perimeter"] )
        if mode == "RATIO":
            pack_sort = sorted( pack_sort, reverse=False, key = lambda entry:entry["ratio"] )
        if mode == "CLASS":
            # Variables
            ratio_0 = list()
            ratio_1 = list()
            ratio_2 = list()
            # Sorting
            for i in range( 0, len( pack_sort ) ):
                ratio = pack_sort[i]["ratio"]
                if ratio < 1:
                    ratio_0.append( pack_sort[i] )
                if ratio == 1:
                    ratio_1.append( pack_sort[i] )
                if ratio > 1:
                    ratio_2.append( pack_sort[i] )
            pack_sort = list()
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
        list_bw = list()
        list_bh = list()
        for s in range( 0, len( pack_sort ) ):
            bw = pack_sort[s]["bw"]
            bh = pack_sort[s]["bh"]
            ox = start_x - bw
            oy = start_y - bh
            list_bw.append( bw )
            list_bh.append( bh )
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
        mini_bw = min( list_bw )
        mini_bh = min( list_bh )

        # Apply to Sort List
        for s in range( 0, count ):
            # Progress Bar
            if s % 5 == 0:
                self.PACKER_PB_VALUE.emit( s + 1 )
                QApplication.processEvents()
            # Stop Cycle
            self.cycle = self.Cycle_Interruption( self.cycle )
            if self.cycle == True:
                self.cycle = False
                break

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
                if delta_x >= delta_y:  side = delta_x
                else:                   side = delta_y
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
                        overlap = ( gl >= el and gl < er ) and ( gt >= et and gt < eb )
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
                            fit = ( gl < er and gr > el ) and ( gt < eb and gb > et )
                            # Square Shape
                            if delta_x >= delta_y:
                                square = gr >= square_x
                            else:
                                square = gb >= square_y
                            # Contact is Valid
                            cl = ( gl == er ) and ( gt <= eb and gb >= et )
                            ct = ( gt == eb ) and ( gl <= er and gr >= el )
                            contact = cl == True or ct == True
                            # Eliminate Small Gaps
                            sgx = fit == True and el >= gl and ( ( el - gl ) < mini_bw )
                            sgy = fit == True and et >= gt and ( ( et - gt ) < mini_bh )

                            # Logic
                            if fit == True or square == True or sgx == True or sgy == True:
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
                    self.cycle = True
                    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( f"{ DOCKER_NAME } | ERROR packer cycle" ) )

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
                grid_points = self.Extra_Points( gl, gr, gt, gb, arranged, grid_points, start_x, start_y )
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
    def Extra_Points( self, gl, gr, gt, gb, arranged, grid_points, start_x, start_y ):
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
#region Widgets

class List_Data( QtWidgets.QListWidget ):
    LIST_URL = QtCore.pyqtSignal( list )
    LIST_FILES = QtCore.pyqtSignal()
    LIST_REMOVE = QtCore.pyqtSignal()
    LIST_CLEAR = QtCore.pyqtSignal()

    # Init
    def __init__( self, parent=None ):
        super( List_Data, self ).__init__( parent )

    # Interaction
    def dragEnterEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            event.accept()
        else:
            super().dragEnterEvent( event )
    def dragMoveEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            event.accept()
        else:
            super().dragMoveEvent( event )
    def dropEvent( self, event ):
        mime_data, format_id = Insert_Drop( self, event )
        if len( mime_data ) > 0 or format_id == drag_id:
            self.LIST_URL.emit( mime_data )
            event.accept()
        else:
            super().dropEvent( event )

    # Context Menu
    def contextMenuEvent( self, event ):
        # Menu
        qmenu = QMenu( self )
        # General
        action_files = qmenu.addAction( "Add Files" )
        action_remove = qmenu.addAction( "Remove Selected" )
        action_clear = qmenu.addAction( "Clear List" )

        # Mapping
        action = qmenu.exec_( self.mapToGlobal( event.pos() ) )
        # General
        if action == action_files:
            self.LIST_FILES.emit()
        if action == action_remove:
            self.LIST_REMOVE.emit()
        if action == action_clear:
            self.LIST_CLEAR.emit()

class Drive_TreeView( QtWidgets.QTreeView ):

    # Init
    def __init__( self, parent ):
        super( Drive_TreeView, self ).__init__( parent )
        # Variables
        self.file_sort = QDir.Name

    # Relay    
    def Set_File_Sort( self, file_sort ):
        self.file_sort = file_sort
        self.update()

    # Interaction
    def dragEnterEvent( self, event: QDragEnterEvent ):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dragMoveEvent( self, event: QDragEnterEvent ):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dropEvent( self, event: QDropEvent ):
        if event.mimeData().hasUrls():
            # Variables
            model = self.model()

            # URL
            url_mime = event.mimeData().urls()[0]
            url_path = url_mime.toLocalFile()

            # Directory Path Construction
            parent_list = [ os.path.dirname( url_path ) ]
            for i in range( 0, 50 ):
                child_item = parent_list[-1]
                parent_item = os.path.dirname( child_item )
                if child_item == parent_item:
                    break
                parent_list.append( parent_item )
            parent_list.reverse()
            parent_list.append( url_path )

            # Cascate Open Folders
            for i in range( 0, len( parent_list )-1 ):
                parent_path = parent_list[i]
                model_list = self.Dir_Model_Items( model, parent_path )
                child_item = self.Model_Item_Path( model, parent_list[i+1] )
                for model_item in model_list:
                    self.setCurrentIndex( model_item )
                self.setCurrentIndex( child_item )
                self.scrollTo( child_item, QAbstractItemView.PositionAtCenter )

            event.acceptProposedAction()
    # Items
    def Dir_Model_Items( self, model, parent_path ):
        # QDir
        qdir = QDir()
        qdir.setPath( parent_path )
        qdir.setSorting( self.file_sort )
        qdir.setFilter( QDir.AllEntries | QDir.NoSymLinks | QDir.NoDotAndDotDot )
        info_list = qdir.entryInfoList()
        # Model
        model_list = list()
        for item in info_list:
            file_path = item.filePath()
            model_item = self.Model_Item_Path( model, file_path )
            model_list.append( model_item)
        return model_list
    def Model_Item_Path( self, model, url ):
        model_item = model.index( url )
        return model_item

#endregion

