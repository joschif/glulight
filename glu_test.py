#!/usr/bin/env python

import time
import unicornhat as unicorn
from pydexcom import Dexcom
from colour import Color

glucose_values = {
    "danger_low": (0, 50),
    "low": (50, 70),
    "normal_low": (70, 90),
    "normal": (90, 120),
    "normal_high": (130, 160),
    "high": (170, 200),
    "danger_high": (200, 99999),
}

glucose_colors = {
    # blue
    "danger_low": "#0000FF",
    # lightblue
    "low": "#2196F3",
    # teal
    "normal_low": "#1ABC9C",
    # green
    "normal": "#008000",
    # yellow
    "normal_high": "#FFFF00",
    # orange
    "high": "#FFA500",
    # red
    "danger_high": "#FF0000",
}

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


def hex_to_rgb(value):
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def get_glucose_level_color(value):
    """Return the glucose level based on the glucose value."""

    if value is None:
        return hex_to_rgb(glucose_colors["low"])

    for level, (min_value, max_value) in glucose_values.items():
        if min_value <= value < max_value:
            return hex_to_rgb(glucose_colors[level])


unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(0)
unicorn.brightness(1.0)
width, height = unicorn.get_shape()

# Parse the configuration file
with open("/home/pi/Pimoroni/unicornhat/glu/config.yaml", "r") as f:
    config = yaml.safe_load(f)
    email = config["email"]
    password = config["password"]

dexcom = Dexcom(email, password, ous=True)

# Test: rotate through all levels
while True:
    for idx, color in enumerate(color_gradient):
        print(idx)
        unicorn.set_all(color[0], color[1], color[2])
        unicorn.show()
        time.sleep(0.05)

# # Get initial glucose reading
# glucose_reading = dexcom.get_current_glucose_reading()
# color = get_glucose_level_color(glucose_reading.value)

# while True:
#     for y in range(height):
#         for x in range(width):
#             unicorn.set_pixel(x, y, color[0], color[1], color[2])
#             unicorn.show()

#     time.sleep(180)

#     glucose_reading = dexcom.get_current_glucose_reading()
#     color = get_glucose_level_color(glucose_reading.value)
