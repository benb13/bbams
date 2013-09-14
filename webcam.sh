#! /bin/bash
LD_PRELOAD=/usr/lib/libv4l/v4l2convert.so fswebcam -r 640x480 -d /dev/video0 -v /srv/http/img/webcam.jpg -t "My Webcam" -D 3 -s brightness=90%
