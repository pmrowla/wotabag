#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wotabag RPC server.

Manages playback via JSON-RPC.

"""

import enum
import subprocess
import time
from io import IOBase
from threading import Event, Thread, Semaphore

import dbus
import dbus.mainloop.glib

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

import gevent
import gevent.queue
from gevent.event import Event as GEvent
from gevent.pywsgi import WSGIServer

from mpv import MPV

from ruamel.yaml import YAML

from tinyrpc.exc import BadRequestError
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.wsgi import WsgiServerTransport
from tinyrpc.server.gevent import RPCServerGreenlets
from tinyrpc.dispatch import public, RPCDispatcher

from . import ble
from .led import (
    aqours,
    aqours_rainbow,
    aqours_units,
    saint_snow,
    muse,
    muse_units,
    BladeColor,
    init_strip,
    pixel_index,
    test_wipe,
    WOTA_TYPE,
)

from .sdp import SDPServerTransport


@enum.unique
class WotabagStatus(enum.IntEnum):

    IDLE = 0
    PLAYING = 1


class WotabagManager(object):

    def __init__(self, config_file):
        yaml = YAML(typ='safe')
        if isinstance(config_file, IOBase):
            config = yaml.load(config_file)
        else:
            with open(config_file) as f:
                config = yaml.load(f)
        self.rpc_host = config.get('rpc_host', '127.0.0.1')
        self.rpc_port = config.get('rpc_port', 60715)
        self._load_playlist(config.get('playlist', []))
        volume = int(config.get('volume', 0))
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        self.volume = volume
        self.current_track = 0
        self.status = WotabagStatus.IDLE
        self._status_lock = Semaphore()

        # init LED strip
        self.strip = init_strip()
        self.strip.begin()

        # init playback
        self.player = MPV(vid='no', hwdec='mmal', keep_open='yes', volume=volume)
        self.song = None
        self._stopped = Event()
        self._stopped.set()
        self._playback_thread = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.status == WotabagStatus.PLAYING:
            self._stopped.set()
            if self._playback_thread:
                self._playback_thread.join()
            if self.player:
                self.player.terminate()

    def _load_file(self, yaml_file):
        yaml = YAML(typ='safe')
        with open(yaml_file) as f:
            song = yaml.load(f)
        print('loaded {} ({})'.format(song['title'], song['filename']))
        self.song = song

    def _load_playlist(self, playlist):
        yaml = YAML(typ='safe')
        self.playlist = []
        for yaml_file in playlist:
            with open(yaml_file) as f:
                song = yaml.load(f)
                self.playlist.append((yaml_file, song['title']))

    def _play(self):
        self._stop()
        self._stopped.clear()

        self._status_lock.acquire()
        self.status = WotabagStatus.PLAYING
        self._status_lock.release()

        self.player.volume = self.volume
        self._playback_thread = Thread(target=self._wota_playback)
        print('starting wota playback thread')
        self._playback_thread.start()

    def _stop(self):
        self._stopped.set()
        if self._playback_thread:
            self._playback_thread.join()
            self._playback_thread = None
        if self.player:
            self.player.command('stop')
        self.song = None

        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, BladeColor.NONE.value)
        self.strip.show()

        self._status_lock.acquire()
        self.status = WotabagStatus.IDLE
        self._status_lock.release()

    def _wota_playback(self):
        while self.current_track < len(self.playlist):
            song, _ = self.playlist[self.current_track]
            self._load_file(song)

            print('[mpv] playing: {}'.format(self.song['filename']))
            self.player.play(self.song['filename'])

            # wait for mpv to actually start playing
            playback_lock = Semaphore(value=0)

            def observer(name, val):
                if val is not None:
                    playback_lock.release()

            self.player.observe_property('time-pos', observer)
            playback_lock.acquire()
            self.player.unobserve_property('time-pos', observer)

            start = time.time()
            ticks = 0
            # drift = 0
            bpm = 120
            cur_colors = {
                'left': BladeColor.YOSHIKO,
                'center': BladeColor.YOSHIKO,
                'right': BladeColor.YOSHIKO,
            }

            initial_offset = self.song.get('initial_offset', 0)
            if initial_offset:
                time.sleep((start + initial_offset / 1000) - time.time())

            last_tick = time.perf_counter()
            # play led patterns
            for pattern in self.song['patterns']:
                if 'bpm' in pattern:
                    bpm = pattern['bpm']
                for k in ['left', 'center', 'right']:
                    if k in pattern:
                        if isinstance(pattern[k], list):
                            colors = []
                            for c in pattern[k]:
                                color = c.upper()
                                if color in BladeColor.__members__:
                                    colors.append(BladeColor[color])
                            cur_colors[k] = tuple(colors)
                        else:
                            color = pattern[k].upper()
                            if color in BladeColor.__members__:
                                cur_colors[k] = BladeColor[color]
                kwargs = pattern.get('kwargs', {})
                kwargs.update(cur_colors)
                wota = WOTA_TYPE[pattern['type']](bpm=bpm, strip=self.strip, **kwargs)
                count = pattern.get('count', 1)
                for i in range(count):
                    for _ in range(len(wota)):
                        if self._stopped.is_set():
                            return
                        next_tick = last_tick + wota.tick_s
                        # if i == 0 or i == count - 1:
                        #     loop = False
                        # else:
                        #     loop = True
                        loop = True
                        wota.tick(loop=loop)
                        diff = next_tick - time.perf_counter()
                        last_tick = next_tick
                        # drift = 0
                        if diff > 0:
                            time.sleep(diff)
                        # elif diff < 0:
                        #     drift = diff
                        ticks += 1

            with self.player._playback_cond:
                # wait for mpv to reach the end of the audio file or 5 seconds,
                # whichever comes first
                self.player._playback_cond.wait(5)

            # end of song, setup next track
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, BladeColor.NONE.value)
            self.strip.show()
            self.current_track += 1

        self.current_track = 0
        self._status_lock.acquire()
        self.status = WotabagStatus.IDLE
        self._status_lock.release()

    @public
    def get_playlist(self):
        """Return this wotabag's playlist."""
        return [title for _, title in self.playlist]

    @public
    def get_status(self):
        """Return current status."""
        result = {
            'status': self.status.name,
            'volume': self.volume,
        }
        if self.status == WotabagStatus.IDLE:
            if self.playlist:
                _, title = self.playlist[self.current_track]
                result['next_track'] = title
            else:
                result['next_track'] = None
        elif self.status == WotabagStatus.PLAYING:
            _, title = self.playlist[self.current_track]
            result['current_track'] = title
            next_track = self.current_track + 1
            if next_track < len(self.playlist):
                _, title = self.playlist[next_track]
                result['next_track'] = title
            else:
                result['next_track'] = None
        return result

    @public
    def get_volume(self):
        """Return current volume."""
        return self.volume

    @public
    def set_volume(self, volume):
        """Set volume."""
        volume = int(volume)
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        self.volume = volume
        if self.player:
            self.player.volume = self.volume
        return self.volume

    @public
    def get_colors(self):
        """Return list of available colors."""
        colors = ['None'] + \
            [x.name.capitalize() for x in aqours] + list(aqours_units.keys()) + ['Aqours Rainbow'] + \
            [x.name.capitalize() for x in saint_snow] + ['Saint Snow'] + \
            [x.name.capitalize() for x in muse] + list(muse_units.keys())
        return colors

    @public
    def set_color(self, color):
        """Set all LEDs to the specified color or color sequence."""
        if color == 'Aqours Rainbow':
            colors = aqours_rainbow
        elif color in aqours_units:
            colors = aqours_units[color]
        elif color == 'Saint Snow':
            colors = saint_snow
        elif color in muse_units:
            colors = muse_units[color]
        elif color.upper() in BladeColor.__members__:
            colors = (BladeColor[color.upper()],)
        else:
            raise BadRequestError('Unknown color')

        strip = self.strip
        if len(colors) == 1:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, colors[0].value)
            strip.show()
        elif len(colors) <= 3:
            if len(colors) == 2:
                colors = colors + (colors[0],)
            for x, color in (enumerate(colors)):
                for y in range(9):
                    strip.setPixelColor(pixel_index(x, y), color.value)
            strip.show()
        elif len(colors) == 9:
            for x in range(3):
                for y, color in enumerate(colors):
                    strip.setPixelColor(pixel_index(x, y), color.value)
            strip.show()

    @public
    def power_off(self):
        """Power off the device.

        Note:
            If 'shutdown -h' fails, the returncode will be returned.
            If shutdown succeeds, the connection will be dropped immediately
            (this will appear as a returned None to a tinyrpc client).

        """
        # clear led's before power off otherwise they will stay turned on until
        # the separate led battery source is manually switched off
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, BladeColor.NONE.value)
        self.strip.show()
        proc = subprocess.run(['shutdown', '-h', 'now'])
        return proc.returncode

    @public
    def play(self):
        """Start playback of the next song."""
        self._play()

    @public
    def play_index(self, index):
        """Start playback of the specified song."""
        if index >= len(self.playlist) or index < 0:
            raise BadRequestError('Invalid song index')
        self.current_track = index
        self._play()

    @public
    def stop(self):
        """Stop playback."""
        self._stop()

    @public
    def test_pattern(self):
        """Display test color wipe patterns."""
        gevent.spawn_later(0, test_wipe, self.strip, clear=True)


server_done = GEvent()


class WotabagRPCServerGreenlets(RPCServerGreenlets):

    def serve_forever(self):
        while not server_done.is_set():
            # wait for message then handle it
            if self.transport.messages.empty():
                gevent.sleep(0)
            else:
                self.receive_one_message()

    def start(self):
        return gevent.spawn(self.serve_forever)


def gevent_main(wotabag, dispatcher, sdp_transport):
    """Secondary thread for gevent event loop.

    Needed so that it does not conflict with dbus/glib event loop.

    """
    ble_rpc_server = WotabagRPCServerGreenlets(
        sdp_transport,
        JSONRPCProtocol(),
        dispatcher
    )

    # Configure WSGI (HTTP) RPC server
    wsgi_transport = WsgiServerTransport(queue_class=gevent.queue.Queue)
    wsgi_server = WSGIServer((wotabag.rpc_host, wotabag.rpc_port), wsgi_transport.handle)
    gevent.spawn(wsgi_server.serve_forever)
    wsgi_rpc_server = WotabagRPCServerGreenlets(
        wsgi_transport,
        JSONRPCProtocol(),
        dispatcher
    )

    try:
        greenlets = []
        print("Running RPC server at {}:{}".format(wotabag.rpc_host, wotabag.rpc_port))
        greenlets.append(wsgi_rpc_server.start())
        greenlets.append(ble_rpc_server.start())
        gevent.sleep(0)
        server_done.wait()
    finally:
        gevent.joinall(greenlets)
        print("RPC server finished")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Wotabag rpi server daemon.")
    parser.add_argument('config_file', type=argparse.FileType('r'),
                        help='YAML configuration file.')
    args = parser.parse_args()

    # Initialize dbus (this must be done before spawning any threads)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    dbus.mainloop.glib.threads_init()
    bus = dbus.SystemBus()
    mainloop = GObject.MainLoop()

    with WotabagManager(args.config_file) as wotabag:
        # Register RPC endpoints
        dispatcher = RPCDispatcher()
        dispatcher.register_instance(wotabag, 'wotabag.')

        # Configure BLE GATT server
        sdp_transport = SDPServerTransport(queue_class=gevent.queue.Queue)
        ble.advertising_main(mainloop, bus, '')
        ble.gatt_server_main(mainloop, bus, '', sdp_transport)

        gevent_thread = Thread(target=gevent_main, args=(wotabag, dispatcher, sdp_transport))

        try:
            # Start gevent (RPC server) thread
            gevent_thread.start()

            # Run GATT server
            print("Running BLE server")
            mainloop.run()
        except KeyboardInterrupt:
            print("Done, cleaning up...")
        finally:
            server_done.set()
            mainloop.quit()
            print("BLE server finished")
            gevent_thread.join()


if __name__ == '__main__':
    main()
