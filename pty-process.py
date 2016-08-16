#!/bin/env python3
import pty
import sys

pty.spawn(sys.argv[1:])
