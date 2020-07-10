#!/usr/bin/env python3

import os
import sys
from src.PixDown import api

if sys.version[0] == "3":
    _src = os.listdir()

else:
    sys.stdout.write("We need python version >= 3.5 !\a\n")

pixiv = api.pixAPI()
# pixiv.downloadFollowWorks()
