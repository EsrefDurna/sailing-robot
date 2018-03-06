#!/bin/bash
set -e

defaultname='blackpython'

echo "Name of the calibration file [" $defaultname "]"
read name

if [ ! "$name" ]
then 
  name=$defaultname
fi


echo '----------------------------------------------------------'
echo 'Calibration of the Compass, be ready to dance!'
echo '----------------------------------------------------------'

#python2 compasscalib_roll


echo '----------------------------------------------------------'
echo "Let's calibrate the wind vane"
echo 'hit enter when ready'
echo '----------------------------------------------------------'
read

python2 wind_direction_calib


rosparam dump  ../src/sailing_robot/launch/parameters/calibration_${name}.yaml /calibration
