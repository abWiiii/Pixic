#!/usr/bin/env python3

import os
import sys
from src.PixDown import pixdown

if sys.version[0] == "3":
    _src = os.listdir()
    print(sys.path)

else:
    sys.stdout.write("We need python version >= 3.5 !\a\n")

pixiv = pixdown.PixDown()
pixiv.downloadFollowWorks()
