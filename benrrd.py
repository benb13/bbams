#! /usr/bin/python2
#######################################################
# File:     	benrrdgraph.py
# Author:   	Benjamin Bordonaro
# Copyright:    copyright 2012-2013   
# Source:       http://www.benjaminbordonaro.com
# Version:  	13.01.02
# Features:
# - Graphing of Arduino Monitoring System RRDTool DB
#######################################################
import rrdtool
import datetime
import time

def ams_rrd_graph(graphtime, graphname, graphtext):
    #Store current date and time
    tdnow = time.strftime('%m-%d-%Y %H:%M', (time.localtime(time.time())))
    tdnow2 = time.strftime('%m-%d-%Y %H:%M:%S', (time.localtime(time.time())))

    ret = rrdtool.graph( "/srv/http/img/%s.png" %(graphname),
 	"--start", "%s" %(graphtime),
        "--end", "now", 
    	"--height", "125", 
       	"--slope-mode", 
       	"--title", graphtext,
       	"--watermark", tdnow,
      	"DEF:temp1=/srv/arduino/ttemp2.rrd:temp1:AVERAGE",
	"DEF:min1=/srv/arduino/ttemp2.rrd:temp1:MIN",
	"DEF:max1=/srv/arduino/ttemp2.rrd:temp1:MAX",
      	"DEF:temp2=/srv/arduino/ttemp2.rrd:temp2:AVERAGE",
	"DEF:min2=/srv/arduino/ttemp2.rrd:temp2:MIN",
	"DEF:max2=/srv/arduino/ttemp2.rrd:temp2:MAX",
      	"DEF:temp3=/srv/arduino/ttemp2.rrd:temp3:AVERAGE",
	"DEF:min3=/srv/arduino/ttemp2.rrd:temp3:MIN",
	"DEF:max3=/srv/arduino/ttemp2.rrd:temp3:MAX",
        "LINE1:temp1#AA0000:room1",
        "LINE2:temp2#00AA00:wine1",
        "LINE3:temp3#0000AA:wine2\\r",
	"GPRINT:temp1:MIN:Room Min\: %6.2lf",
	"GPRINT:temp1:MAX:Max\: %6.2lf",
	"GPRINT:temp1:AVERAGE:Avg\: %6.2lf", 
	"GPRINT:temp1:LAST:Current\: %6.2lf \\r",
	"GPRINT:temp2:MIN:Wine1 Min\: %6.2lf",
	"GPRINT:temp2:MAX:Max\: %6.2lf",
	"GPRINT:temp2:AVERAGE:Avg\: %6.2lf", 
	"GPRINT:temp2:LAST:Current\: %6.2lf \\r",
	"GPRINT:temp3:MIN:Wine2 Min\: %6.2lf",
	"GPRINT:temp3:MAX:Max\: %6.2lf",
	"GPRINT:temp3:AVERAGE:Avg\: %6.2lf", 
	"GPRINT:temp3:LAST:Current\: %6.2lf \\r")

#"AREA:temp1#000066:temp1",

ams_rrd_graph("end-1h","temp1h","Wine Temperature - Last Hour")
ams_rrd_graph("end-4h","temp4h","Wine Temperature - Last 4 Hours")
ams_rrd_graph("end-1d","temp1d","Wine Temperature - Last 24 Hours")
ams_rrd_graph("end-7d","temp7d","Wine Temperature - Last 7 Days")
ams_rrd_graph("end-30d","temp30d","Wine Temperature - Last 30 Days")
ams_rrd_graph("end-90d","temp90d","Wine Temperature - Last 90 Days")
ams_rrd_graph("end-365d","temp365d","Wine Temperature - Last Year")
