#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class for individual files to facilitate bundling and encryption

Need to import data from config file
"""


class File:
    def __init__(self, name, size=0, chunks={}):
        self.name = name
        self.size = size
        self.chunks = chunks

    def __del__(self):
        del self.name
        del self.size
        self.chunks.clear()
        del self.chunks


if __name__ == "__main__":
    pass
