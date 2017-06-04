import os
from time import time


def time_ms():
    return int(round(time() * 1000))


def list_files(path):
    filelist = []
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path):
            filelist.append(full_path)
    return filelist
