# Import
from PyQt5.QtGui import QImage
from PyQt5.QtCore import qDebug

# Path 
# image_file = path_source files or file collection, given by Imagine Board
# path_destination = directory path to save files into, given by Imagine Board

# Variables (%)
px = 0.2
py = 0.2
pw = 0.6
ph = 0.6

# Paths
basename = os.path.basename( image_file )
check_dir = os.path.isdir( path_destination )
if check_dir == False:
    path_destination = os.path.dirname( path_destination )
exists_dir = os.path.exists( path_destination )

# QImage
qimage = QImage( image_file )
width = qimage.width()
height = qimage.height()
if ( qimage.isNull() == False and exists_dir == True ):
    save_location = os.path.join( path_destination, basename )
    exists_file = os.path.exists( save_location )
    if exists_file == False:
        qimage = qimage.copy( int(px*width), int(py*height), int(pw*width), int(ph * height) )
        qimage.save( save_location )
