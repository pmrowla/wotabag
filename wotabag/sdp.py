#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python implemenation of Simple Datagram Protocol (SDP) based RPC server."""

import itertools
import math
import struct
from queue import Queue

from tinyrpc.transports import ServerTransport


# IOS_MTU_SIZE = 185
IOS_MTU_SIZE = 48


class DatagramHeader(object):

    BYTE_COUNT = 9

    def __init__(self, key, offset, message_length):
        self.key = key
        self.offset = offset
        self.message_length = message_length

    def __hash__(self):
        return hash((self.key, self.offset, self.message_length))

    def __bytes__(self):
        return struct.pack('!BII', self.key, self.offset, self.message_length)


class Datagram(object):

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload

    def __hash__(self):
        return hash((self.header, self.payload))

    def __len__(self):
        return len(self.header) + len(self.payload)

    def __bytes__(self):
        return bytes(self.header) + self.payload

    @classmethod
    def decode(cls, data):
        try:
            key, offset, message_length = struct.unpack_from('!BII', data)
        except struct.error:
            return None
        hdr = DatagramHeader(key, offset, message_length)
        return Datagram(hdr, data[DatagramHeader.BYTE_COUNT:])


class DatagramView(object):

    def __init__(self, message, datagram_max_size=IOS_MTU_SIZE):
        self.message = message
        self.datagram_max_size = datagram_max_size
        self.payload_max_size = datagram_max_size - 2


class Message(object):

    def __init__(self, key, data):
        self.key = key
        self.data = data

    def __hash__(self):
        return hash((self.key, self.data))

    def datagrams(self, datagram_max_size=IOS_MTU_SIZE):
        assert(datagram_max_size > DatagramHeader.BYTE_COUNT)
        payload_max_size = datagram_max_size - DatagramHeader.BYTE_COUNT
        datagram_count = int(math.ceil(len(self.data) / payload_max_size))
        for i in range(datagram_count):
            offset = i * payload_max_size
            hdr = DatagramHeader(self.key, offset, len(self.data))
            yield Datagram(hdr, self.data[offset:offset + payload_max_size])


class MessageBuilder(object):

    def __init__(self, message_length, on_complete=None):
        self.remaining_indices = set(range(0, message_length))
        self._data = list([b'\x00'] * message_length)
        self.message_length = message_length
        self.on_complete = on_complete

    @property
    def data(self):
        return bytes(self._data)

    def insert(self, payload, offset):
        for i in range(len(payload)):
            data_index = offset + i
            self._data[data_index] = payload[i]
            self.remaining_indices.remove(data_index)
        if not self.remaining_indices:
            if self.on_complete:
                self.on_complete(self.data)


class SDPServerTransport(ServerTransport):
    """SDP tinyrpc server transport."""

    def __init__(self, queue_class=Queue):
        self._queue_class = queue_class
        self.messages = self._queue_class()
        # self.replies = self._queue_class()
        self.builders = {}
        self._key_iter = itertools.count()
        self.reply_callback = None

    def receive_message(self):
        msg = self.messages.get()
        return msg

    def send_reply(self, context, reply):
        print('Sending RPC response: {}'.format(reply.decode('utf-8')))
        if not self.reply_callback:
            print('Reply callback is not set, cannot send RPC response.')
            return
        key = next(self._key_iter)
        response = Message(key, reply)
        for dgram in response.datagrams():
            if callable(self.reply_callback):
                self.reply_callback(bytes(dgram))

    def handle_message(self, data):
        """Handle an assembled SDP message."""
        print('Got RPC request: "{}"'.format(data.decode('utf-8')))
        self.messages.put((None, data))

    def process(self, data):
        """Process a partial SDP message."""
        dgram = Datagram.decode(data)
        key = dgram.header.key
        message_length = dgram.header.message_length
        builder = self.builders.get(key, MessageBuilder(message_length, on_complete=self.handle_message))
        builder.insert(dgram.payload, dgram.header.offset)
        if builder.remaining_indices:
            self.builders[key] = builder
        elif key in self.builders:
            del self.builders[key]
