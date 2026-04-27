#!/usr/bin/env python

import ast
import glob
import sys
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import seaborn as sns

from utils import set_config

def get_linux_map(f_name):
    f = open(f_name, 'r')

    my_map = []

    my_map.append((0, 0, 'nothing'))

    for line in f:

        func, b = line.strip().split(' ')
        start, end = b.split('-')

        func = func[:-1]
        
        my_map.append((int(start, 16), int(end, 16), func))

    my_map.sort()

    list_map = [x[0] for x in my_map]

    return list_map
