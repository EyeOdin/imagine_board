# Import
from PyQt5.QtCore import qDebug

# Path 
# image_file = path_source files or file collection, given by Imagine Board
# path_destination = directory path to save files into, given by Imagine Board

# Notes = prints the image file path in the "Log Viewer" docker

try:QtCore.qDebug( f"image_file = { image_file }" )
except:pass
