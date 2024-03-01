# digipi_nextion
Experimental Digipi script to display on Nextion Screens

This is deisgned to run on a [digipi](https://digipi.org/) device and is a modified version of this [script](https://github.com/craigerl/direwatch) by Craig KM6LYW

# This is a work in progress and still very experimental

Prequisites
pip3 install gpsd-py3
pip3 install nextion
pip3 install maidenhead

Setup GPSD
*   Connect GPS device and work out which port it is (for me /dev/ttyACM0)
  *   cat /dev/ACM0 and look at the output
*   Edit /etc/default/gpsd to reflect the correct serial port
*   gpsmon should show vaild data   

Setup Nextion
* Wire to the serial Pins on the pi and power as per [this](https://www.f5uii.net/en/tutorial-nextion-screen-on-mmdvm-raspberry-pi/)
* run raspi-config -> interface options -> serial port
* Select No (login Shell) and then Yes (Serial port hardware)


# Modification

The HMI file can be editied in the nextion editor which is only available for Windows. The supporting PNG files will likely have to be uploaded and provide for each state of the buttons, and the background.

They should be uploaded with Button OFF being image 0, Button ON image 1 and background image 2
