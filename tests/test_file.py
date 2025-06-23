# -*- coding: utf-8 -*-

import os
import random
import string

import pytest

from models.file import File


@pytest.fixture
def setup():
    """Create test file"""
    # Setup test folder
    if not os.path.exists("./tests/test_files/"):
        os.makedirs("./tests/test_files/")

    # Setup letters for random text generation
    letters = string.ascii_lowercase

    # Create test file
    with open("./tests/test_files/test_file_1.txt", "w") as f:
        f.write("This is a test file. Checking splitting and encryption\n")
        f.write("The rest of the file will contain random letters:\n")
        f.write("".join(random.choice(letters) for i in range(3 * 1024 * 1024)))
        f.write("\nEnding the file. This is the last bit of text, but it")
        f.write("should still be readable.")

    yield_path = "./tests/test_files/test_file_1.txt"
    yield yield_path

    os.remove(os.path.join("./tests/test_files", "test_file_1.txt"))
    os.rmdir("./tests/test_files")


def test_file_load(setup):
    """Check file load works"""
    print(type(setup))
    print(setup)
    f = File(setup)
    assert f.name == "test_file_1.txt"
    assert f.path == setup
    assert f.size >= (3 * 1024 * 1024)
    with open(setup, "r") as t:
        assert "This is a test file" in t.readline()
