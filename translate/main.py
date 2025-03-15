from workshop import WorkshopNewMods
from translator import Translator, LLMTranslator, GoogleTranslator
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", help="Do all tasks", action="store_true")
parser.add_argument("-t", help="Translate mode", action="store_true")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG)


a = WorkshopNewMods(107410)
a.get_mods(1)