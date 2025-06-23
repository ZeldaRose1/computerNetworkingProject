#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 16:47:07 2025

@author: zelda
"""

import os
from utils.config import Config

# TODO: Write tests to verify read ability of the config file.
# Specifically with regard to friends public keys and files


def test_pass():
    # Ensure folder is clean to start
    if os.path.exists("./conf_test"):
        for file in os.listdir("./conf_test"):
            os.remove(os.join("./conf_test", file))
        os.rmdir("./conf_test")

    # Begin testing
    try:
        os.mkdir("./conf_test")
        c = Config("./conf_test")
        assert len(c.personal["p"]["SECRET_KEY"]) == 64
        assert len(c.personal["p"]["PUBLIC_KEY"]) == 64
    except Exception as e:
        print("Could not create test folder.")
        print(e)
        assert False
    finally:

        try:
            os.remove("./conf_test/personal.ini")
            os.remove("./conf_test/friends.ini")
            os.remove("./conf_test/files.ini")
        except Exception:
            print("Error, file does not exist to delete!")
            assert False

        os.rmdir("./conf_test")
        assert True

    assert True
