#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wotabag playback module.

"""

import os.path
import time
from threading import thread, Event

from mpv import MPV

from ruamel.yaml import YAML

from rpi_ws281x import Color, PixelStrip

import led


class WotabagPlayer(object):

    def __init__(self, strip, volume=0):
        self.strip = strip
        self._volume = volume
        self.mpv = None
        self.song = None
        self._stop = Event()
        self._stop.set()
        self._playback_thread = None

    def terminate(self):
        self._stop.set()
        if self._playback_thread:
            self._playback_thread.join()
        self.mpv.terminate()

    def set_volume(self, volume):
        self._volume = volume
        if self.mpv:
            self.mpv.volume = volume

    def load_file(self, yaml_file):
        yaml = YAML(typ='safe')
        with open(yaml_file) as f:
            song = yaml.load(f)
        print('loaded {} ({})'.format(song['title'], song['filename']))
        self.song = song

    def play(self):
        self.stop()
        self._stop.clear()
        if not self.song:
            return
        self.mpv = MPV(vid='no')
        self.mpv.volume = self._volume
        self._playback_thread = Thread(
        self.mpv.play(song['filename'])

    def stop(self):
        self._stop().set()
        if self._playback_thread:
            self._playback_thread.join()
            self._playback_thread = None
        if self.mpv:
            self.mpv.stop()
            self.mpv.terminate()
            self.mpv = None



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file')
    args = parser.parse_args()

    yaml = YAML(typ='safe')
    with open(args.yaml_file) as f:
        song = yaml.load(f)

    if not os.path.isfile(song['filename']):
        parser.exit('{} is not a valid filename'.format(song['filename']))

    # init neopixel strip
    strip = PixelStrip(led.LED_COUNT, led.LED_PIN, led.LED_FREQ_HZ, led.LED_DMA, led.LED_INVERT, led.LED_BRIGHTNESS, led.LED_CHANNEL)
    strip.begin()

    # init mpv
    player = MPV(vid='no')

    print('loaded {} ({})'.format(song['title'], song['filename']))

    # start audio playback
    try:
        player.volume = 25
        player.play(song['filename'])

        start = time.time()
        ticks = 0
        drift = 0
        bpm = 120
        cur_colors = {
            'left': led.BladeColor.YOSHIKO,
            'center': led.BladeColor.YOSHIKO,
            'right': led.BladeColor.YOSHIKO,
        }

        initial_offset = song.get('initial_offset')
        if initial_offset:
            time.sleep((start + initial_offset / 1000) - time.time())

        last_tick = time.perf_counter()
        # play led patterns
        for pattern in song['patterns']:
            if 'bpm' in pattern:
                bpm = pattern['bpm']
            for k in ['left', 'center', 'right']:
                if k in pattern:
                    color = pattern[k].upper()
                    if color in led.BladeColor.__members__:
                        cur_colors[k] = led.BladeColor[color]
            kwargs = pattern.get('kwargs', {})
            kwargs.update(cur_colors)
            wota = led.WOTA_TYPE[pattern['type']](bpm=bpm, strip=strip, **kwargs)
            count = pattern.get('count', 1)
            for i in range(count):
                for _ in range(len(wota)):
                    next_tick = last_tick + wota.tick_s
                    # if i == 0 or i == count - 1:
                    #     loop = False
                    # else:
                    #     loop = True
                    loop = True
                    wota.tick(loop=loop)
                    diff = next_tick - time.perf_counter()
                    last_tick = next_tick
                    drift = 0
                    if diff > 0:
                        time.sleep(diff)
                    elif diff < 0:
                        drift = diff
                    ticks += 1

        # wait for audio to finish
        player.wait_for_playback()
        led.color_wipe(strip, Color(0, 0, 0), 10)
    except KeyboardInterrupt:
        print('exiting (ctrl+c)')
        led.color_wipe(strip, Color(0, 0, 0), 10)
    finally:
        if player:
            player.terminate()
