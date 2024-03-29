#!/usr/bin/env python
# /etc/init.d/glu_grad.py
### BEGIN INIT INFO
# Provides:          glu_grad.py
# Required-Start:    $all
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

import os
import sys
import time
import yaml
import unicornhat as unicorn
from pydexcom import Dexcom
from colour import Color
import colorsys


glucose_values = {
    "danger_low": (0, 50),
    "low": (50, 70),
    "normal_low": (70, 100),
    "normal": (100, 150),
    "normal_high": (150, 200),
    "high": (200, 300),
    "danger_high": (300, 99999),
}

glucose_colors = {
    # blue
    "danger_low": "#0000FF",
    # light blue
    "low": "#0195FF",
    # teal
    "normal_low": "#00E09A",
    # green
    "normal": "#00C600",
    # yellow
    "normal_high": "#FFE401",
    # orange
    "high": "#FF5701",
    # red
    "danger_high": "#FF0061",
}

# arrow on 4x8 grid
arrows = {
    "DoubleUp": [
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
    ],
    "SingleUp": [
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
    ],
    "FortyFiveUp": [
        [0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
    ],
    "Flat": [
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "FortyFiveDown": [
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0],
    ],
    "SingleDown": [
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
    ],
    "DoubleDown": [
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
    ],
}


def get_glucose_level_color(value):
    if value is None:
        color = (255, 255, 255)
    elif value > len(color_gradient) - 1:
        color = color_gradient[-1]
    else:
        color = color_gradient[value]
    return color


def show_color(color, blink_color=None, direction=None):
    if blink_color:
        # Blink for 60 seconds on and off
        # Freq 1 sec per flash
        for _ in range(30):
            set_arrow(color, direction=direction)
            time.sleep(1.5)
            set_arrow(blink_color, direction=direction)
            time.sleep(0.5)
    else:
        # Show color for 180 seconds
        set_arrow(color, direction=direction)
        time.sleep(60)


def set_arrow(color, direction=None):
    direction = direction if direction in arrows.keys() else None
    if direction is None:
        unicorn.set_all(*color)
        unicorn.show()
        return
    for y in range(4):
        for x in range(8):
            if arrows[direction][y][x]:
                # Set white
                unicorn.set_pixel(x, y, 255, 255, 255)
            else:
                unicorn.set_pixel(x, y, *color)
    unicorn.show()


def pulse_white_blue():
    # Pulse white-blue for 30 seconds
    # Freq 1.2 sec white, 0.3 sec light purple
    for _ in range(20):
        unicorn.set_all(150, 150, 150)
        unicorn.show()
        time.sleep(1.2)
        unicorn.set_all(186, 104, 200)
        unicorn.show()
        time.sleep(0.3)


color_gradient = []
for idx, level in enumerate(glucose_values):
    if idx == len(glucose_values) - 1:
        break
    min_value, max_value = glucose_values[level]
    color1 = glucose_colors[level]
    color2 = glucose_colors[list(glucose_values.keys())[idx + 1]]
    color1 = Color(color1)
    color2 = Color(color2)
    colors = list(color1.range_to(color2, max_value - min_value))
    colors = [c.rgb for c in colors]
    colors = [tuple(int(255 * c) for c in color) for color in colors]
    color_gradient.extend(colors)


unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(0)
unicorn.brightness(1.0)
width, height = unicorn.get_shape()

# Parse the configuration file
with open("/home/pi/Pimoroni/unicornhat/glu/config.yaml", "r") as f:
    config = yaml.safe_load(f)
    email = config["email"]
    password = config["password"]

while True:
    # Get initial glucose reading
    try:
        dexcom = Dexcom(email, password, ous=True)
        glucose_reading = dexcom.get_current_glucose_reading()
    except Exception as e:
        # Write the exception to a file
        with open("/home/pi/glu_error.log", "a") as f:
            f.write(str(e))
        pulse_white_blue()
        continue

    if glucose_reading is None:
        sys.stdout.write("No glucose reading available.")
        color = (150, 150, 150)
        blink_color = (0, 0, 0)
    else:
        sys.stdout.write(str(glucose_reading.value))
        color = get_glucose_level_color(glucose_reading.value)
        direction = glucose_reading.trend_direction
        blink_color = None

    while True:
        show_color(color, blink_color=blink_color, direction=direction)

        try:
            glucose_reading = dexcom.get_current_glucose_reading()
        except Exception as e:
            # Write the exception to a file
            with open("/home/pi/glu_error.log", "a") as f:
                f.write(str(e))
            blink_color = (150, 150, 150)
            continue

        if glucose_reading is None:
            sys.stdout.write("NA")
            blink_color = (0, 0, 0)
        else:
            color = get_glucose_level_color(glucose_reading.value)
            sys.stdout.write(str(glucose_reading.value))
            blink_color = None
