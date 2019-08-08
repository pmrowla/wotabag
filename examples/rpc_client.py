#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example RPC client for controlling a wotabag.

Requires tinrypc[httpclient] (https://github.com/mbr/tinyrpc).

"""

import time

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc import RPCClient

rpc_client = RPCClient(
    JSONRPCProtocol(),
    HttpPostClientTransport('http://raspberrypi.local:60715/')
)

server = rpc_client.get_proxy(prefix='wotabag.')

# Retrieve server status
result = server.get_status()
print(result)

# Retrieve server playlist
result = server.get_playlist()
print(result)

# Test LED patterns
server.test_pattern()

# Start playback
server.play()

time.sleep(10)

# # Stop playback
server.stop()

# Power off the Pi
# result = remote_server.power_off()
