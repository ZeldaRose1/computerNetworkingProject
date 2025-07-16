#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 14:14:55 2025

@author: zelda
"""
import threading

from utils.config import Config
from utils.connection import Connection


def test_connection_punch():
    p1 = Connection()
    p2 = Connection()

    # Localhost used for both peers
    t1 = threading.Thread(
        target=p1.initiate_hole_punch,
        args=("127.0.0.1", 5002, 5001)
    )

    t2 = threading.Thread(
        target=p2.initiate_hole_punch,
        args=("127.0.0.1", 5001, 5002)
    )

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert hasattr(p1, "active_socket")
    assert hasattr(p2, "active_socket")

    # Exchange test message
    try:
        p1.active_socket.sendall(b"Hello from p1")
        data = p2.active_socket.recv(1024)
        print("p2 received:", data.decode())

        p2.active_socket.sendall(b"Hello from p2")
        data = p1.active_socket.recv(1024)
        print("p1 received:", data.decode())
        assert True
    except Exception as e:
        print("Error during socket communication:", e)
        assert False

    # try:
    #     p1.active_socket.send(b"TCP Hole punching successful")
    #     success = True
    #     assert success
    # except OSError as e:
    #     print("Socket is not connected!\t\t", e)
    # finally:
    #     assert success
