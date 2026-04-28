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


#region Import

# Krita
from krita import *

#endregion


#region File Formats

# Extensions
extensions = [
    # Native
    "kra",
    "krz",
    "ora",
    "bundle",
    # Gimp
    "xcf",
    # PS
    "psd",
    "psb",
    "psdt",
    # Static
    "bmp",
    "bw",
    "cur",
    "hdr",
    "icns",
    "ico",
    "jpeg",
    "jpg",
    "jfif",
    "pbm",
    "pcx",
    "pdd",
    "pgm",
    "pic",
    "png",
    "ppm",
    "ras",
    "rgb",
    "rgba",
    "sgi",
    "tga",
    "tif",
    "tiff",
    "wbmp",
    "xbm",
    "xpm",
    # PDF
    # "pdf",
    # Vector
    "svg",
    "svgz",
    # Animation
    "ani",
    "gif",
    "webp",
    # Compressed
    "zip",
    "zip2", # fail safe view
    ]

# File Sort
file_normal = list()
for e in extensions:
    file_normal.append( f"*.{ e }" )
file_backup = list()
for e in extensions:
    file_backup.append( f"*.{ e }~" )
file_all = list()
for n in file_normal:
    file_all.append( n )
for b in file_backup:
    file_all.append( b )

# File Types
file_animation = [ "ani", "gif", "webp", "webm", ]
file_vector = [ "svg", "svgz", ]
file_compact = [ "kra", "krz", "ora", "bundle", "zip", "zip2" ]
file_web = [ "http", "https", "ftp", "//", ]
file_wend = ( "jpg", "jpeg", "png", "gif", "webp", "webm", )
file_krita = ( "kra", "krz", "ora", "bundle", )
# Construct Lists
file_static = list()
for e in extensions:
    if ( e not in file_animation and e not in file_compact ):
        file_static.append( f"{ e }" )
file_search = list()
for e in extensions:
    if e not in file_compact:
        file_search.append( f"{ e }" )

#endregion
#region Others

# Variables
DOCKER_NAME = "Imagine Board"
qt_max = 16777215
encode = "utf-8"
zf = 6 # zfill constant
icon_size = 50
clip_false = { "cstate" : False, "cl" : 0, "ct" : 0, "cr" : 1, "cb" : 1 }
drag_id = "krita/imagine_board"
merged_png = "mergedimage.png" # KRA KRZ ORA
preview_png = "preview.png" # Bundle
metadata_key = "Keywords"
invalid = [ "", ".", "..", " ", None ]
color_white = QColor( "#ffffff" )
color_gray = QColor( "#7f7f7f" )
color_black = QColor( "#000000" )
color_alpha = QColor( 0, 0, 0, 50 )

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

