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
import math
import random
import urllib
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Plugin Modules
from .imagine_board_constants import *

#endregion


#region Krita

# Kritarc
def Kritarc_Read( group, key, default, tipo ):
    variable = default
    read = Krita.instance().readSetting( group, key, "" )
    if read not in [ "", None ]:
        read = tipo( read )
        if type( default ) == type( read ):
            variable = read
    if variable == default:
        Kritarc_Write( group, key, default )
    return variable
def Kritarc_Write( group, key, value ):
    Krita.instance().writeSetting( group, key, str( value ) )

# Communication
def Message_Log( operation, message ):
    string = f"{ DOCKER_NAME } | { operation } { message }"
    try:QtCore.qDebug( string )
    except:pass
def Message_Warnning( operation, message ):
    string = f"{ DOCKER_NAME } | { operation } { message }"
    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )
def Message_Float( operation, message, icon ):
    ki = Krita.instance()
    string = f"{ DOCKER_NAME } | { operation } { message }"
    ki.activeWindow().activeView().showFloatingMessage( string, ki.icon( icon ), 5000, 0 )
def Message_Error( error="null image" ):
    Message_Float( "ERROR", str( error ), "broken-preset" )

#endregion
#region Limiters

def Limit_Float( value ):
    if value <= 0:
        value = 0
    if value >= 1:
        value = 1
    return value
def Limit_Range( value, minimum, maximum ):
    if value <= minimum:
        value = minimum
    if value >= maximum:
        value = maximum
    return value
def Limit_Loop( value, limit ):
    if value < 0:
        value = limit
    if value > limit:
        value = 0
    return value
def Limit_Looper( value, limit ):
    while value < 0:
        value += limit
    while value > limit:
        value -= limit
    return value
def Limit_Angle( angle, inter ):
    angle = angle // inter
    even = angle % 2
    if even == 0: # Even
        angle = angle * inter
    else: # Odd
        angle = ( angle + 1 ) * inter
    return angle
def Limit_Mini( value, minimum ):
    if value <= minimum:
        value = minimum
    return value

#endregion
#region Range

def Lerp_1D( percent, bot, top ):
    delta = top - bot
    lerp = bot + ( delta * percent )
    return lerp
def Lerp_2D( percent, x1, y1, x2, y2 ):
    dx = x2 - x1
    dy = y2 - y1
    lx = x1 + ( dx * percent )
    ly = y1 + ( dy * percent )
    return lx, ly

def Random_Range( range ):
    time = int( QtCore.QTime.currentTime( ).toString( 'hhmmssms' ) )
    random.seed( time )
    random_value = random.randint( 0, range )
    return random_value

#endregion
#region Statistics

def Stat_Mean( lista ):
    length = len( lista )
    add = 0
    for i in range( 0, length ):
        add = add + lista[i]
    mean = add / ( length )
    return mean

#endregion
#region Trignometry

def Trig_2D_Points_Distance( x1, y1, x2, y2 ):
    dd = math.sqrt( math.pow( ( x1-x2 ),2 ) + math.pow( ( y1-y2 ),2 ) )
    return dd
def Trig_2D_Points_Lines_Angle( x1, y1, x2, y2, x3, y3 ):
    v1 = ( x1-x2, y1-y2 )
    v2 = ( x3-x2, y3-y2 )
    v1_theta = math.atan2( v1[1], v1[0] )
    v2_theta = math.atan2( v2[1], v2[0] )
    angle = ( v2_theta - v1_theta ) * ( 180.0 / math.pi )
    if angle < 0:
        angle += 360.0
    return angle
def Trig_2D_Points_Lines_Intersection( x1, y1, x2, y2, x3, y3, x4, y4 ):
    try:
        xx = ( ( x2*y1-x1*y2 )*( x4-x3 )-( x4*y3-x3*y4 )*( x2-x1 ) ) / ( ( x2-x1 )*( y4-y3 )-( x4-x3 )*( y2-y1 ) )
        yy = ( ( x2*y1-x1*y2 )*( y4-y3 )-( x4*y3-x3*y4 )*( y2-y1 ) ) / ( ( x2-x1 )*( y4-y3 )-( x4-x3 )*( y2-y1 ) )
    except:
        xx = 0
        yy = 0
    return xx, yy
def Trig_2D_Points_Rotate( origin_x, origin_y, dist, angle ):
    cx = origin_x - ( dist * math.cos( math.radians( angle ) ) )
    cy = origin_y - ( dist * math.sin( math.radians( angle ) ) )
    return cx, cy
def Trig_2D_Triangle_Extrapolation( x1, y1, x2, y2, percent_12, percent_23 ):
    hor = x2 - x1
    ver = y2 - y1
    p23_hor = ( percent_23 * hor ) / percent_12
    p23_ver = ( percent_23 * ver ) / percent_12
    x3 = x2 + p23_hor
    y3 = y2 + p23_ver
    return x3, y3

#endregion
#region Compressed

# Compressed
def Compressed_QPixmap( archive, name ):
    qpixmap = None
    buffer = Compressed_Buffer( archive, name )
    reader = QImageReader( buffer )
    if reader.canRead():
        reader.setAutoTransform( True )
        qpixmap = QPixmap().fromImageReader( reader )
    return qpixmap
def Compressed_Buffer( archive, name ):
    # Archive
    extract = archive.open( name )
    image_data = extract.read()
    # Buffer
    byte_array = QByteArray( image_data )
    buffer = QBuffer()
    buffer.setData( byte_array )
    buffer.open( QIODevice.OpenModeFlag.ReadOnly )
    # Return
    return buffer
def Compressed_Sort( lista ):
    list_name = list()
    list_order = list()
    for item in lista:
        list_name.append( [ os.path.basename( item ), item ] )
    list_name.sort()
    for item in list_name:
        list_order.append( item[1] )
    return list_order

#endregion
#region Metadata

def Metadata_Read( url ):
    qimage_reader = QImageReader( url )
    text = qimage_reader.text( metadata_key )
    return text
def Metadata_Write( mode, tag, url ):
    basename = os.path.basename( url )
    try:
        # Reader
        reader = QImageReader( url )
        rformat = reader.format()
        text = reader.text( metadata_key )
        # Variables
        if len( tag ) > 0:
            tag = set( tag )
        text = set( text.split( " " ) )
        # Mode
        if mode == "KEY_ADD":       keywords = text|tag
        elif mode == "KEY_REPLACE": keywords = tag
        elif mode == "KEY_REMOVE":  keywords = text-tag
        elif mode == "KEY_CLEAN":   keywords = set( "" )
        # Write
        if text != keywords:
            # Variables
            keywords = list( keywords )
            keywords.sort()
            keywords = " ".join( keywords )
            # QImage
            qimage = reader.read()
            # Write
            writer = QImageWriter()
            writer.setText( metadata_key, str( keywords ) )
            writer.setCompression( 0 )
            wformat = writer.supportedImageFormats()
            if rformat in wformat:
                writer.setFileName( url )
                writer.write( qimage )
                if mode == "KEY_CLEAN":
                    keywords = "*"
                string = f"{ DOCKER_NAME } | WRITE { keywords } >> { basename }"
            else:
                string = f"{ DOCKER_NAME } | ERROR format not supported | { basename }"
        else:
            string = f"{ DOCKER_NAME } | SAME no change | { basename }"
    except Exception as e:
        string = f"{ DOCKER_NAME } | ERROR { e } | { basename }"
    try:QtCore.qDebug( string )
    except:pass

#endregion
#region Internet

# Internet
def Check_Html( url ):
    if QtCore.QUrl( url ).scheme() in file_web:
        boolean = True
    else:
        boolean = False
    return boolean
def Download_QPixmap( url ):
    qpixmap = None
    data = Download_Data( url )
    if data != None:
        pix = QtGui.QPixmap()
        pix.loadFromData( data )
        if pix.isNull() == False:
            qpixmap = pix
    return qpixmap
def Download_Data( url ):
    # replace user agent from : https://httpbin.io/headers
    try:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0" }
        request = urllib.request.Request( url, headers=headers )
        response = urllib.request.urlopen( request )
        data = response.read()
    except:
        data = None
    return data

#endregion
#region Troubleshooting

# Inspect
def Inspect():
    functions = list()
    ins = inspect.stack()
    for item in ins:
        functions.append( item[3] )
    string = f"Inspect = { functions }"
    QtCore.qDebug( string )
    # QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )

#endregion
