#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wotabag GPIO/LED controller module.

Contains methods to display animations on a 3x9 grid of ws281x NeoPixel LEDs.
Can also be run directly from command line for test purposes.
Based on rpi-ws281x-python strandtest.py.

"""

import logging
import time
from collections import OrderedDict
from enum import Enum

from rpi_ws281x import PixelStrip, Color


logger = logging.getLogger('wotabag')


# LED strip configuration:
LED_COUNT = 27          # Number of LED pixels.
LED_PIN = 18            # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10            # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000    # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10            # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 128    # Set to 0 for darkest and 255 for brightest
LED_INVERT = False      # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0         # set to '1' for GPIOs 13, 19, 41, 45 or 53


class BladeColor(Enum):
    """LoveLive WS2812 RGB color values.

    Values should give a rough visual approximation to the original Kingblade
    colors when using WS2812 LEDs.

    """

    NONE = Color(0, 0, 0)   # Off

    # NOTE: Aqours colors tested via visual comparison to:
    #   official 2L KB
    #   official Landing Action Fanmeeting KB
    #   official 4L KB
    #   official Asia Tour KB

    CHIKA = Color(0xff, 0x4d, 0x00)     # Mikan orange - Ruifan RGBW(0xff, 0x23, 0x00, 0x00)
    RIKO = Color(0xff, 0x4b, 0x81)      # Sakura pink - Ruifan RGBW(0xff, 0x2d, 0x4b, 0x00)
    KANAN = Color(0x00, 0xa8, 0x2f)     # Emerald green - Ruifan RGBW(0x00, 0xaa, 0x14, 0x00)
    DIA = Color(0xff, 0x00, 0x00)       # Red - Ruifan RGBW(0xff, 0x00, 0x00, 0x00)
    YOU = Color(0x00, 0x7c, 0xff)       # Light blue - Ruifan RGBW(0x00, 0x46, 0xff, 0x00)
    YOSHIKO = Color(0xff, 0xff, 0xff)   # White - Ruifan RGBW(0x00, 0x00, 0x00, 0xff)
    HANAMARU = Color(0x91, 0xb9, 0x00)  # Yellow - Ruifan RGBW(0x91, 0xb9, 0x00, 0x00)
    MARI = Color(0x37, 0x00, 0xff)      # Violet - Ruifan RGBW(0x1e, 0x00, 0xff, 0x00)
    RUBY = Color(0xff, 0x00, 0x50)      # Pink - Ruifan RGBW(0xff, 0x00, 0x4b, 0x00)

    # NOTE: Saint Snow colors untested

    SERA = Color(0x00, 0xa2, 0xbe)      # Sky blue - Ruifan RGBW(0x00, 0x8c, 0xbe, 0x00)
    LEAH = Color(0x064, 0x5a, 0x5a)     # Pure white - Ruifan RGBW(0x64, 0x32, 0x32, 0xff)

    # NOTE: μ's colors untested

    HONOKA = Color(0xff, 0x23, 0x00)    # Orange - Ruifan RGBW(0xff, 0x23, 0x00, 0x00)
    NOZOMI = Color(0xb3, 0x00, 0xc8)    # Purple - Ruifan RGBW(0xb3, 0x00, 0xc8, 0x00)
    RIN = Color(0xff, 0xff, 0x00)       # Yellow - Ruifan RGBW(0xff, 0xff, 0x00, 0x00)
    HANAYO = Color(0x00, 0xff, 0x00)    # Green - Ruifan RGBW(0x00, 0xff, 0x00, 0x00)
    NICO = Color(0xff, 0x00, 0x4b)      # Pink - Ruifan RGBW(0xff, 0x00, 0x4b, 0x00)
    KOTORI = Color(0xff, 0xff, 0xff)    # White - Ruifan RGBW(0x00, 0x00, 0x00, 0xff)
    UMI = Color(0x00, 0x00, 0xff)       # Blue - Ruifan RGBW(0x00, 0x00, 0xff, 0x00)
    ELI = Color(0x00, 0xff, 0xff)       # Light blue - Ruifan RGBW(0x00, 0xff, 0xff, 0x07)
    MAKI = Color(0xff, 0x00, 0x01)      # Red - Ruifan RGBW(0xff, 0x00, 0x01, 0x00)


# Color sequence in official Aqours Kingblade order
aqours = (
    BladeColor.CHIKA,
    BladeColor.RIKO,
    BladeColor.KANAN,
    BladeColor.DIA,
    BladeColor.YOU,
    BladeColor.YOSHIKO,
    BladeColor.HANAMARU,
    BladeColor.MARI,
    BladeColor.RUBY,
)

aqours_1y = (
    BladeColor.HANAMARU,
    BladeColor.RUBY,
    BladeColor.YOSHIKO,
)

aqours_2y = (
    BladeColor.CHIKA,
    BladeColor.YOU,
    BladeColor.RIKO,
)

aqours_3y = (
    BladeColor.DIA,
    BladeColor.KANAN,
    BladeColor.MARI,
)

aqours_rainbow = aqours_2y + aqours_1y + aqours_3y

guilty_kiss = (
    BladeColor.RIKO,
    BladeColor.YOSHIKO,
    BladeColor.MARI,
)

cyaron = (
    BladeColor.CHIKA,
    BladeColor.YOU,
    BladeColor.RUBY,
)

azalea = (
    BladeColor.HANAMARU,
    BladeColor.KANAN,
    BladeColor.DIA,
)

aqours_units = OrderedDict([
    ('Aqours 1st Years', aqours_1y),
    ('Aqours 2nd Years', aqours_2y),
    ('Aqours 3rd Years', aqours_3y),
    ('Guilty Kiss', guilty_kiss),
    ('CYaRon!', cyaron),
    ('AZALEA', azalea),
])

saint_snow = (
    BladeColor.SERA,
    BladeColor.LEAH,
)

saint_aqours_snow = aqours + saint_snow

muse = (
    BladeColor.HONOKA,
    BladeColor.NOZOMI,
    BladeColor.RIN,
    BladeColor.HANAYO,
    BladeColor.NICO,
    BladeColor.KOTORI,
    BladeColor.UMI,
    BladeColor.ELI,
    BladeColor.MAKI,
)

muse_1y = (
    BladeColor.MAKI,
    BladeColor.RIN,
    BladeColor.HANAYO,
)

muse_2y = (
    BladeColor.UMI,
    BladeColor.HONOKA,
    BladeColor.KOTORI,
)

muse_3y = (
    BladeColor.NOZOMI,
    BladeColor.NICO,
    BladeColor.ELI,
)

bibi = (
    BladeColor.MAKI,
    BladeColor.NICO,
    BladeColor.ELI,
)

lily_white = (
    BladeColor.UMI,
    BladeColor.NOZOMI,
    BladeColor.RIN,
)

printemps = (
    BladeColor.KOTORI,
    BladeColor.HONOKA,
    BladeColor.HANAYO,
)

muse_units = OrderedDict([
    ("μ's 1st Years", muse_1y),
    ("μ's 2nd Years", muse_2y),
    ("μ's 3rd Years", muse_3y),
    ('BiBi', bibi),
    ('Lily white', lily_white),
    ('Printemps', printemps),
])


def pixel_index(x, y):
    return 9 * x + y


def get_aqours_rainbow(reverse=False):
    if reverse:
        return tuple(reversed(aqours_rainbow))
    return aqours_rainbow


# Define functions which animate LEDs in various ways.
def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel(
                (int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


class BaseWota(object):

    def __init__(self, strip=None, beats=0, bpm=120, *args, **kwargs):
        """Base wota pattern abstract class.

        Parameters:
            strip (PixelStrip): The ws281x strip used to display this pattern.
            beats (int): Number of beats this pattern takes.

        """
        self.strip = strip
        self.beats = beats
        self.bpm = bpm
        self.rainbow = None

    def __len__(self):
        return self.beats * 8

    @property
    def tick_s(self):
        """Return the length of one tick in seconds."""
        return 1 / (self.bpm * 8 / 60)

    def tick(self, *args, **kwargs):
        """Perform one tick from this movement, and then return.

        Every wota subclass must implement this method.

        One tick = 1/8th of a beat - i.e. every of `self.beats * 8` calls to `tick()` should form one complete movement.

        Note: This function may call `time.sleep()`, but will return as soon as all LED actions are completed,
        which will almost always be faster than the full duration of a single tick. To guarantee proper overall timing,
        the caller is responsible for sleeping until the end of a tick.

        """
        raise NotImplementedError

    # Convenience methods for common lighting effects

    def all_off(self):
        for i in range(27):
            self.strip.setPixelColor(i, 0)
        self.strip.show()

    def light_chase(self, left=True, center=True, right=True):
        """Display a chase effect."""
        q = self._count % 3
        for i in range(0, 27, 3):
            x = (i + q) // 9
            y = (i + q) % 9
            if x == 0 and left:
                if self.rainbow:
                    color = self.rainbow[y]
                else:
                    color = self.colors[0]
                    if isinstance(color, tuple):
                        color = color[y % len(color)]
            elif x == 1 and center:
                if self.rainbow:
                    color = self.rainbow[y]
                else:
                    color = self.colors[1]
                    if isinstance(color, tuple):
                        color = color[y % len(color)]
            elif x == 2 and right:
                if self.rainbow:
                    color = self.rainbow[y]
                else:
                    color = self.colors[2]
                    if isinstance(color, tuple):
                        color = color[y % len(color)]
            else:
                color = BladeColor.NONE
            self.strip.setPixelColor(i + q, color.value)
        self.strip.show()
        for i in range(0, 27, 3):
            self.strip.setPixelColor(i + q, BladeColor.NONE.value)


class WotaNormal(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, rainbow=False,
                 reverse=False, *args, **kwargs):
        """Default aqours wota pattern.

        Alternates waving between half height (odd beats) and full height (even beats).

        """
        super().__init__(beats=2, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    # TODO: split this into even_tick and odd_tick functions, and make
    # WotaNormalOdd and WotaNormalEven just inherit from this class and use the
    # appropriate tick function. Currently all of this code is duplicated in
    # the even/odd classes
    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern.

        Parameters:
            loop (bool): True if this is part of a loop (should generally be False for the first and last
                items in a sequence).

        """
        count = self._count % len(self)

        # beat 1
        if count == 0:
            # half height
            for y in range(9):
                for x, color in enumerate(self.colors):
                    if y < 5:
                        if self.rainbow:
                            color = self.rainbow[y]
                        elif isinstance(color, tuple):
                            color = color[y % len(color)]
                        self.strip.setPixelColor(pixel_index(x, y), color.value)
                    else:
                        self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 3:
            time.sleep(self.tick_s / 3)
            for y in range(5, 3, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 4:
                    time.sleep(self.tick_s / 3)
        elif count == 4:
            for y in range(3, 0, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 1:
                    time.sleep(self.tick_s / 3)
        elif count == 5:
            for x in range(3):
                self.strip.setPixelColor(pixel_index(x, 0), BladeColor.NONE.value)
            self.strip.show()
            time.sleep(self.tick_s / 3)
            for y in range(0, 2):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 1:
                    time.sleep(self.tick_s / 3)
        elif count == 6:
            for y in range(2, 5):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 3:
                    time.sleep(self.tick_s / 3)
        elif count == 7:
            for y in range(5, 8):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 7:
                    time.sleep(self.tick_s / 3)

        # Beat 2
        elif count == 8:
            # full height
            for y in range(9):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 11 and loop:
            time.sleep(2 * self.tick_s / 3)
            for x in range(3):
                self.strip.setPixelColor(pixel_index(x, 8), BladeColor.NONE.value)
            self.strip.show()
        elif count == 12 and loop:
            for y in range(7, 4, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 5:
                    time.sleep(self.tick_s / 3)
        elif count == 13 and loop:
            for y in range(4, 1, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 2:
                    time.sleep(self.tick_s / 3)
        elif count == 14 and loop:
            for y in range(1, -1, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                time.sleep(self.tick_s / 3)
            for x, color in enumerate(self.colors):
                if self.rainbow:
                    color = self.rainbow[0]
                elif isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(x, 0), color.value)
            self.strip.show()
        elif count == 15 and loop:
            for y in range(1, 4):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[0]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 3:
                    time.sleep(self.tick_s / 3)
        self._count += 1


class WotaNormalOdd(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, rainbow=False,
                 reverse=False, *args, **kwargs):
        """Odd beat half of aqours default wota pattern.

        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern.

        Parameters:
            loop (bool): True if this is part of a loop (should generally be False for the first and last
                items in a sequence).

        """
        count = self._count % len(self)

        # beat 1
        if count == 0:
            # half height
            for y in range(9):
                for x, color in enumerate(self.colors):
                    if y < 5:
                        if self.rainbow:
                            color = self.rainbow[y]
                        self.strip.setPixelColor(pixel_index(x, y), color.value)
                    else:
                        self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 3:
            time.sleep(self.tick_s / 3)
            for y in range(5, 3, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 4:
                    time.sleep(self.tick_s / 3)
        elif count == 4:
            for y in range(3, 0, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 1:
                    time.sleep(self.tick_s / 3)
        elif count == 5:
            for x in range(3):
                self.strip.setPixelColor(pixel_index(x, 0), BladeColor.NONE.value)
            self.strip.show()
            time.sleep(self.tick_s / 3)
            for y in range(0, 2):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 1:
                    time.sleep(self.tick_s / 3)
        elif count == 6:
            for y in range(2, 5):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 3:
                    time.sleep(self.tick_s / 3)
        elif count == 7:
            for y in range(5, 8):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 7:
                    time.sleep(self.tick_s / 3)
        self._count += 1


class WotaNormalEven(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, rainbow=False,
                 reverse=False, *args, **kwargs):
        """Even beat half of default aqours wota pattern.

        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, **kwargs):
        """Perform one tick from this pattern.

        """
        count = self._count % len(self)

        # Beat 1
        if count == 0:
            # full height
            for y in range(9):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 3:
            time.sleep(2 * self.tick_s / 3)
            for x in range(3):
                self.strip.setPixelColor(pixel_index(x, 8), BladeColor.NONE.value)
            self.strip.show()
        elif count == 4:
            for y in range(7, 4, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 5:
                    time.sleep(self.tick_s / 3)
        elif count == 5:
            for y in range(4, 1, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                if y > 2:
                    time.sleep(self.tick_s / 3)
        elif count == 6:
            for y in range(1, -1, -1):
                for x in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
                self.strip.show()
                time.sleep(self.tick_s / 3)
            for x, color in enumerate(self.colors):
                if self.rainbow:
                    color = self.rainbow[y]
                self.strip.setPixelColor(pixel_index(x, 0), color.value)
            self.strip.show()
        elif count == 7:
            for y in range(1, 4):
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
                if y < 3:
                    time.sleep(self.tick_s / 3)
        self._count += 1


class WotaSlow(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, rainbow=False,
                 reverse=False, *args, **kwargs):
        """Default aqours slow wota pattern.

        4-beat wave up to full height

        """
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern.

        Beat 1-4: slow full height wipe

        """
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                if self.rainbow:
                    color = self.rainbow[0]
                elif isinstance(color, tuple):
                    color = color[0]
                self.strip.setPixelColor(pixel_index(x, 0), color.value)
                for y in range(1, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count % 2 == 0:
            y = count // 2
            if y < 9:
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
        elif count == 31:
            self.all_off()

        self._count += 1


class WotaSlow3(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, hold=False,
                 rainbow=False, reverse=False, *args, **kwargs):
        """3-beat version of aqours slow wota pattern.

        """
        super().__init__(beats=3, *args, **kwargs)
        self.colors = (left, center, right)
        self.hold = hold
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern.

        Beat 1-3: slow full height wipe

        """
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                if self.rainbow:
                    color = self.rainbow[0]
                elif isinstance(color, tuple):
                    color = color[0]
                self.strip.setPixelColor(pixel_index(x, 0), color.value)
                for y in range(1, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count % 2 == 0:
            y = count // 2
            if y < 9:
                for x, color in enumerate(self.colors):
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
        elif count == 23 and not self.hold:
            self.all_off()

        self._count += 1


class WotaHold(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, hold=False,
                 rainbow=False, reverse=False, *args, **kwargs):
        """1-beat long hold.

        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self.hold = hold
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern.

        Beat 1-3: slow full height wipe

        """
        count = self._count % len(self)

        if count == 0:
            for x in range(len(self.colors)):
                for y in range(0, 9):
                    color = self.colors[x]
                    if self.rainbow:
                        color = self.rainbow[y]
                    elif isinstance(color, tuple):
                        color = color[y % len(color)]
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 7 and not self.hold:
            self.all_off()

        self._count += 1


class WotaHai(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aqours repeated Hai! wota pattern.

        Alternates between off (odd beats) and light chase pattern (even beats)

        """
        super().__init__(beats=2, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, *args, **kwargs):
        """Perform one tick from this pattern.

        """
        count = self._count % len(self)

        # beat 1
        if count == 0:
            self.all_off()

        # Beat 2
        elif count >= 8:
            self.light_chase()
        self._count += 1


class WotaSenoHai(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aqours Seno Hai!- Hai!- 4xHai! wota pattern.

        Should almost always start on beat 3 of a 4/4 measure.

        """
        super().__init__(beats=10, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, **kwargs):
        """Perform one tick from this pattern.

        """
        count = self._count % len(self)

        # start of beats 1, 2 (Se, no)
        if count == 0 or count == 8:
            for y in range(9):
                for x, color in enumerate(self.colors):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()

        # end of beats 1, 2, start of beats 4, 6
        elif count in (6, 14, 24, 40):
            self.all_off()

        # beats 3, 5, 10
        elif (count >= 16 and count < 24) or (count >= 32 and count < 40) or (count >= 72):
            self.light_chase()

        # beat 7
        elif count >= 48 and count < 56:
            self.light_chase(center=False, right=False)

        # beat 8
        elif count >= 56 and count < 64:
            self.light_chase(left=False, right=False)

        # beat 9
        elif count >= 64 and count < 72:
            self.light_chase(left=False, center=False)

        self._count += 1


class WotaOhHai(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aqours slow Oh---Hai! wota pattern.

        Generally follows a WotaSenoHai.

        Beat 1-3: slow full height wipe
        Beat 4: light chase

        """
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                self.strip.setPixelColor(pixel_index(x, 0), color.value)
                for y in range(1, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count < 24 and (count % 2 == 0):
            y = count // 2
            if y < 9:
                for x, color in enumerate(self.colors):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                self.strip.show()
        elif count >= 24:
            self.light_chase()

        self._count += 1


class WotaFlash(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Single beat duration flash."""
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 7:
            self.all_off()

        self._count += 1


class WotaFlash2(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Single beat duration double flash.

        Flashes on 1/8th note down/up beats of a 4/4 beat.
        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 4):
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count in (3, 7):
            self.all_off()

        self._count += 1


class WotaFufu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Single beat duration double flash.

        Flashes on first two 1/16th notes of a 4/4 beat."""
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 3):
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count in (1, 7):
            self.all_off()

        self._count += 1


class WotaChase(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, rainbow=False,
                 reverse=False, *args, **kwargs):
        """1-beat long chase.

        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        if rainbow:
            self.rainbow = get_aqours_rainbow(reverse)

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        self.light_chase()

        self._count += 1


class WotaSpin(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, reverse=False,
                 *args, **kwargs):
        """1 beat spin."""
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        self.reverse = reverse

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        for x, color in enumerate(self.colors):
            for y in range(9):
                if x in (0, 2):
                    if self.reverse:
                        n = 8 - count
                    else:
                        n = count
                else:
                    if self.reverse:
                        n = count
                    else:
                        n = 8 - count
                if y in (n, (n + 4) % 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                else:
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
        self.strip.show()

        self._count += 1


class WotaAozoraHora(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aozora Jumping Heart "Hora! issho ni ne!" pattern."""
        super().__init__(beats=8, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0 or count == 4:
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 3 or count == 7:
            self.all_off()
        elif count == 16:
            for x, color in enumerate(self.colors):
                for y in range(0, 2):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 28:
            for x, color in enumerate(self.colors):
                for y in range(2, 4):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 40:
            for x, color in enumerate(self.colors):
                for y in range(4, 6):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 48:
            for x, color in enumerate(self.colors):
                for y in range(6, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()

        self._count += 1


class WotaAozoraAshita(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aozora Jumping Heart "ashita e... seishun masshigura!" pattern."""
        super().__init__(beats=16, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x in range(3):
                for y in range(9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
        if count < 96 and count % 2 == 0:
            if count < 32:
                on = 2
                off = None
            elif count < 64:
                on = 0
                off = 2
            else:
                on = 1
                off = 0
            color = self.colors[on]
            y = count % 32 // 2
            if y < 9:
                self.strip.setPixelColor(pixel_index(on, y), color.value)
                if off is not None:
                    self.strip.setPixelColor(pixel_index(off, 8 - y), BladeColor.NONE.value)
            self.strip.show()
        elif count >= 96:
            self.light_chase(left=False, right=False)

        self._count += 1


class WotaAozoraMasshigura(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Aozora Jumping Heart final "...masshigura" pattern."""
        super().__init__(beats=8, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        height = count // 2

        q = self._count % 3
        for i in range(0, 27, 3):
            x = (i + q) // 9
            y = (i + q) % 9
            if x == 0:
                if y <= height:
                    color = self.colors[0]
                else:
                    color = BladeColor.NONE
            elif x == 1:
                color = self.colors[1]
            elif x == 2:
                if y <= height:
                    color = self.colors[2]
                else:
                    color = BladeColor.NONE
            else:
                color = BladeColor.NONE
            self.strip.setPixelColor(i + q, color.value)
        self.strip.show()
        for i in range(0, 27, 3):
            self.strip.setPixelColor(i + q, BladeColor.NONE.value)

        self._count += 1


class WotaHPTIntroFu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """HPT intro "--|-fu|-fu|-fu|..." pattern."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            self.all_off()
        elif count == 12:
            color = self.colors[0]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(0, y), color.value)
            self.strip.show()
        elif count == 20:
            color = self.colors[1]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 28:
            color = self.colors[2]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(2, y), color.value)
            self.strip.show()

        self._count += 1


class WotaHPTSyncoFu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """HPT verse syncopated "fu-|-fu|-fu|--|..." pattern."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                for y in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                for y in range(3, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 12:
            for x, color in enumerate(self.colors):
                for y in range(3, 6):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 20:
            for x, color in enumerate(self.colors):
                for y in range(6, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()

        self._count += 1


class WotaHPTFufufu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """HPT "|fufu|fu-|..." pattern."""
        super().__init__(beats=2, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            color = self.colors[0]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(0, y), color.value)
            for x in range(1, 3):
                for y in range(9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 4:
            color = self.colors[1]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 8:
            color = self.colors[2]
            for y in range(9):
                self.strip.setPixelColor(pixel_index(2, y), color.value)
            self.strip.show()

        self._count += 1


class WotaKoiNiFufu(BaseWota):
    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, reverse=False,
                 *args, **kwargs):
        """Koi ni naritai aquarium "|fufu|... pattern."""
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0
        self.reverse = reverse

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            if self.reverse:
                colors = (BladeColor.NONE, self.colors[1], BladeColor.NONE)
            else:
                colors = (self.colors[0], BladeColor.NONE, self.colors[2])
            for x, color in enumerate(colors):
                for y in range(9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 4:
            for x, color in enumerate(self.colors):
                for y in range(9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()

        self._count += 1


class WotaKoiNiTottemo(BaseWota):
    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO,
                 *args, **kwargs):
        """Koi ni naritai aquarium "tottemo (tottemo tanoshisou...) pattern."""
        super().__init__(beats=2, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                for y in range(0, 3):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                for y in range(3, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 4:
            for x, color in enumerate(self.colors):
                for y in range(3, 6):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 6:
            for x, color in enumerate(self.colors):
                for y in range(6, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 15:
            self.all_off()

        self._count += 1


class WotaKoiNiOpen(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Koi ni "OPEN!/WELCOME" pattern.

        Essentially just syncopated offset version of Flash2
        """
        super().__init__(beats=1, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 5):
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 4:
            self.all_off()

        self._count += 1


class WotaATPSeichou(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO,
                 *args, **kwargs):
        """Awaken the Power "Seichou shitta ne" pattern."""
        super().__init__(beats=6, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 40):
            self.all_off()
        elif count == 4:
            # sei
            for y in range(9):
                color = self.colors[0]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(0, y), color.value)
            self.strip.show()
        elif count == 12:
            # cho-
            for y in range(9):
                color = self.colors[2]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(2, y), color.value)
            self.strip.show()
        elif count == 20:
            # shi-
            for y in range(3):
                color = self.colors[1]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 24:
            # -ta
            for y in range(3, 6):
                color = self.colors[1]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 28:
            # ne
            for y in range(6, 9):
                color = self.colors[1]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()

        self._count += 1


class WotaATPFighting(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO,
                 *args, **kwargs):
        """Awaken the Power "Fighting fighting!" pattern."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            # figh-
            for y in range(9):
                color = self.colors[0]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(0, y), color.value)
            self.strip.show()
        elif count == 6:
            # -ting
            for y in range(9):
                color = self.colors[2]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(2, y), color.value)
            self.strip.show()
        elif count == 12:
            # figh-
            for y in range(5):
                color = self.colors[1]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 20:
            # -ting
            for y in range(5, 9):
                color = self.colors[1]
                if isinstance(color, tuple):
                    color = color[y % len(color)]
                self.strip.setPixelColor(pixel_index(1, y), color.value)
            self.strip.show()
        elif count == 31:
            self.all_off()

        self._count += 1


class WotaYumeFufu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Yume Kataru chorus "fufu"."""
        super().__init__(beats=2, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 7, 15):
            self.all_off()
        elif count in (4, 8):
            for x, color in enumerate(self.colors):
                for y in range(0, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()

        self._count += 1


class WotaYumeFufufu(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Yume Kataru break (L-R-L) "-fu|-fu|-fu|--|--|".

        Starts on beat 4.
        """
        super().__init__(beats=5, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 39):
            self.all_off()
        elif count >= 4 and count < 12:
            self.light_chase(center=False, right=False)
        elif count >= 12 and count < 20:
            self.light_chase(left=False, center=False)
        elif count >= 20:
            self.light_chase(center=False, right=False)

        self._count += 1


class WotaJimoAi(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Jimo Ai."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            for x, color in enumerate(self.colors):
                for y in range(9):
                    c = BladeColor.NONE
                    if x == 1 or (x == 0 and y <= 4) or (x == 2 and y >= 4):
                        if isinstance(color, tuple):
                            c = color[y % len(color)]
                        else:
                            c = color
                    self.strip.setPixelColor(pixel_index(x, y), c.value)
            self.strip.show()
        elif count == 16:
            for x, color in enumerate(self.colors):
                for y in range(9):
                    c = BladeColor.NONE
                    if x == 1 or (x == 0 and y >= 4) or (x == 2 and y <= 4):
                        if isinstance(color, tuple):
                            c = color[y % len(color)]
                        else:
                            c = color
                    self.strip.setPixelColor(pixel_index(x, y), c.value)
            self.strip.show()

        self._count += 1


class WotaHajimariYamenai(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Hajimari Road "-ya|-me|nai-|yo-|..." pattern."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count == 0:
            self.all_off()
        elif count == 4:
            for x, color in enumerate(self.colors):
                for y in range(3):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
                for y in range(3, 9):
                    self.strip.setPixelColor(pixel_index(x, y), BladeColor.NONE.value)
            self.strip.show()
        elif count == 12:
            for x, color in enumerate(self.colors):
                for y in range(3, 6):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count == 16:
            for x, color in enumerate(self.colors):
                for y in range(6, 9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count >= 24:
            self.light_chase()

        self._count += 1


class WotaHajimariGoEast(BaseWota):

    def __init__(self, left=BladeColor.YOSHIKO, center=BladeColor.YOSHIKO, right=BladeColor.YOSHIKO, *args, **kwargs):
        """Hajimari Road "go-|-east|--|go-|..." pattern."""
        super().__init__(beats=4, *args, **kwargs)
        self.colors = (left, center, right)
        self._count = 0

    def tick(self, loop=False, **kwargs):
        """Perform one tick from this pattern."""
        count = self._count % len(self)

        if count in (0, 12, 24):
            for x, color in enumerate(self.colors):
                for y in range(9):
                    self.strip.setPixelColor(pixel_index(x, y), color.value)
            self.strip.show()
        elif count in (8, 20):
            self.all_off()

        self._count += 1


WOTA_TYPE = {
    'slow': WotaSlow,
    'slow3': WotaSlow3,
    'hold': WotaHold,
    'normal': WotaNormal,
    'normalodd': WotaNormalOdd,
    'normaleven': WotaNormalEven,
    'hai': WotaHai,
    'senohai': WotaSenoHai,
    'ohhai': WotaOhHai,
    'flash': WotaFlash,
    'flash2': WotaFlash2,
    'fufu': WotaFufu,
    'chase': WotaChase,
    'spin': WotaSpin,
    'aozorahora': WotaAozoraHora,
    'aozoraashita': WotaAozoraAshita,
    'aozoramasshigura': WotaAozoraMasshigura,
    'hptintrofu': WotaHPTIntroFu,
    'hptsyncofu': WotaHPTSyncoFu,
    'hptfufufu': WotaHPTFufufu,
    'koinifufu': WotaKoiNiFufu,
    'koinitottemo': WotaKoiNiTottemo,
    'koiniopen': WotaKoiNiOpen,
    'atpseichou': WotaATPSeichou,
    'atpfighting': WotaATPFighting,
    'yumefufu': WotaYumeFufu,
    'yumefufufu': WotaYumeFufufu,
    'jimoai': WotaJimoAi,
    'hajimariyamenai': WotaHajimariYamenai,
    'hajimarigoeast': WotaHajimariGoEast,
}


def init_strip():
    return PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)


def test_wipe(strip, clear=False):
    try:
        logger.info('Test color wipe animations.')
        for color in BladeColor:
            logger.debug(color)
            color_wipe(strip, color.value)
        if clear:
            color_wipe(strip, Color(0, 0, 0), 10)
    except KeyboardInterrupt:
        if clear:
            color_wipe(strip, Color(0, 0, 0), 10)


def main():
    import argparse
    # Process arguments
    parser = argparse.ArgumentParser(description='Display a test pattern.')
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    parser.add_argument('--test-color', action='store', default=None)
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    if args.test_color:
        color_wipe(strip, BladeColor[args.test_color.upper()].value)
        return

    print('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    test_wipe(strip, args.clear)


if __name__ == '__main__':
    main()
