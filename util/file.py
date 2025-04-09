import os
import csv
import logging
from translator import *

def search_file(path: str) -> str:
    # Add your implementation here
    pass



class CSV_File:
    """
    csv file reader and translator
    all target languages should be import as a list of strings
    eg: ['en', 'zh', 'ja', 'ko']
    the retruned data should be a dict of dicts
    eg: {key1: {raw: 'import value1', en: 'value1', zh: '值1'}, key2: {raw: 'import value2', en: 'value2', zh: '值2'}}

    """
    id: int
    target: list[str]
    old_data: dict[str, dict]
    data: dict[str, dict]
    translator: Translator
    logger: logging.Logger

    def __init__(self, id: int, raw: str, target: list[str], translator: Translator) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id
        self.old_data = {}
        self.data = {}
        self.target = target
        self.translator = translator
        self.load_raw(raw)
        self.transfer_data()

    def load_raw(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    key = row[0]
                    if key == 'id' or key == 'ID':
                        continue
                    values = row[1:]
                    self.data[key] = {'raw': values[0]}
            self.logger.info(f"Loaded data from {path}")
            self.logger.debug(f"Data: {self.data}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {path}")
        except Exception as e:
            self.logger.error(f"Error loading data from {path}: {e}")

    def load_old_data(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.old_data = {row[0]: row[1:] for row in reader}
                self.logger.info(f"Loaded old data from {path}")
                self.logger.debug(f"Old Data: {self.old_data}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {path}")
        except Exception as e:
            self.logger.error(f"Error loading old data from {path}: {e}")

    def save_data(self, path: str) -> None:
        pass


    def save_result(self, path: str, lang: str) -> None:
        pass

    def transfer_data(self) -> dict[str, dict]:
        for lang in self.target:
            # for each language
            if lang == 'raw':
                continue
            for key, values in self.data.items():
                # check if the key is in old data and the value is the same
                if key in self.old_data and lang in self.old_data[key] and values['raw'] == self.old_data[key]['raw']:
                    self.data[key][lang] = self.old_data[key][lang]
                    self.logger.info(f"Matched {values['raw']} to {lang}: {self.data[key][lang]}")
                else:
                    try:
                        # check if the value is empty
                        max_retries = 3
                        while max_retries > 0:
                            result = self.translator.translate(values['raw'], lang)
                            self.logger.debug(f"Translation result: {result}")
                            if result["code"] == 200:
                                break
                            else:
                                max_retries -= 1
                                self.logger.warning(f"Retrying translation for {values['raw']} to {lang}, attempts left: {max_retries}")
                        if max_retries == 0 and result["code"] != 200:
                            self.logger.error(f"Translation failed for {values['raw']} to {lang}: {result['text']}")
                            self.data[key][lang] = 'Error'
                            raise Exception("Max retries exceeded")
                        self.data[key][lang] = result["text"]
                    except Exception as e:
                        self.logger.error(f"Error translating {values['raw']} to {lang}: {e}")
                        self.data[key][lang] = 'Error'
        self.logger.info("Data transfer completed")
        self.logger.debug(f"Final Data: {self.data}")
        return self.data

    def get_data(self) -> dict[str, list]:
        # Add your implementation here
        pass

if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={'disable': ['E9999', 'W1203'], "max-line-length": 120})