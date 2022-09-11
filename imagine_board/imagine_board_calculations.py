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


#\\ Imports ####################################################################
import math
import random
from PyQt5 import QtCore
#//


#\\ Limiters ###################################################################
def Limit_Float(value):
    if value <= 0:
        value = 0
    if value >= 1:
        value = 1
    return value
def Limit_Range(value, minimum, maximum):
    if value <= minimum:
        value = minimum
    if value >= maximum:
        value = maximum
    return value
def Limit_Loop(value, limit):
    if value < 0:
        value = limit
    if value > limit:
        value = 0
    return value
def Limit_Looper(value, limit):
    while value < 0:
        value += limit
    while value > limit:
        value -= limit
    return value

#//
#\\ Range ######################################################################
def Lerp_1D(percent, bot, top):
    delta = top - bot
    lerp = bot + ( delta * percent)
    return lerp
def Lerp_2D(percent, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    lx = x1 + ( dx * percent)
    ly = y1 + ( dy * percent)
    return lx, ly
def Random_Range(range):
    time = int(QtCore.QTime.currentTime().toString('hhmmssms'))
    random.seed(time)
    random_value = random.randint(0, range)
    return random_value

#//
#\\ Statistics #################################################################
def Stat_Mean(lista):
    length = len(lista)
    add = 0
    for i in range(0, length):
        add = add + lista[i]
    mean = add / (length)
    return mean

#//
#\\ Trignometry ################################################################
def Trig_2D_Points_Distance(x1, y1, x2, y2):
    dd = math.sqrt( math.pow((x1-x2),2) + math.pow((y1-y2),2) )
    return dd
def Trig_2D_Points_Lines_Angle(x1, y1, x2, y2, x3, y3):
    v1 = (x1-x2, y1-y2)
    v2 = (x3-x2, y3-y2)
    v1_theta = math.atan2(v1[1], v1[0])
    v2_theta = math.atan2(v2[1], v2[0])
    angle = (v2_theta - v1_theta) * (180.0 / math.pi)
    if angle < 0:
        angle += 360.0
    return angle
def Trig_2D_Points_Lines_Intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    try:
        xx = ((x2*y1-x1*y2)*(x4-x3)-(x4*y3-x3*y4)*(x2-x1)) / ((x2-x1)*(y4-y3)-(x4-x3)*(y2-y1))
        yy = ((x2*y1-x1*y2)*(y4-y3)-(x4*y3-x3*y4)*(y2-y1)) / ((x2-x1)*(y4-y3)-(x4-x3)*(y2-y1))
    except:
        xx = 0
        yy = 0
    return xx, yy
def Trig_2D_Points_Rotate(origin_x, origin_y, dist, angle):
    cx = origin_x - (dist * math.cos(math.radians(angle)))
    cy = origin_y - (dist * math.sin(math.radians(angle)))
    return cx, cy
def Trig_2D_Triangle_Extrapolation(x1, y1, x2, y2, percent_12, percent_23):
    hor = x2 - x1
    ver = y2 - y1
    p23_hor = (percent_23 * hor) / percent_12
    p23_ver = (percent_23 * ver) / percent_12
    x3 = x2 + p23_hor
    y3 = y2 + p23_ver
    return x3, y3

#//
