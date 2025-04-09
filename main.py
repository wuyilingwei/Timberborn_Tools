from util.workshop import *
from util.translator import *
from util.config import *
from util.file import *
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Do all tasks", action="store_true")
parser.add_argument("-t", help="Translate mode", action="store_true")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG)


a = WorkshopNewMods(107410)
a.get_mods(1)