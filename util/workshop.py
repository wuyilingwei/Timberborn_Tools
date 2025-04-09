"""
version: 0.1.0
author: Wuyilingwei
Get the latest mods from the Steam Workshop
"""
import logging
import requests
from bs4 import BeautifulSoup


class WorkshopNewMods:
    """
    Class to get the latest mods from the Steam Workshop
    """
    game_id: int
    text: str
    headers: dict
    ids: list[int]
    logger: logging.Logger

    def __init__(self, game_id: int, text: str = "Mod",
                 headers: dict = None) -> None:
        self.ids = []
        self.game_id = game_id
        self.text = text
        if headers is None:
            self.headers = {'User-Agent': 'Mozilla/5.0 '
                            '(Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/121.0.0.0 Safari/537.36',
                            'Accept-Language': 'en-US,en;q=0.9'}
        else:
            self.headers = headers
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_mods(self, depth: int = 1) -> list[int]:
        """
        Returns a list of the latest mods from the Steam Workshop
        depth: the number of pages to search for mods
        """
        def response_to_ids(response: requests.Response) -> None:
            soup = BeautifulSoup(response.content, 'html.parser')
            mod_elements = soup.find_all('a', {'class': 'ugc'})
            for mod in mod_elements:
                mod_url = mod.get('href')
                if mod_url and 'id=' in mod_url:
                    mod_text = mod_url.split('id=')[-1]
                    mod_id = mod_text.split('&')[0]
                    if mod_id not in self.ids:
                        self.ids.append(mod_id)
            self.ids.sort()
        for i in range(1, depth + 1):
            url = (f'https://steamcommunity.com/workshop/browse/'
                   f'?appid={self.game_id}&browsesort=mostrecent'
                   f'&requiredtags%5B%5D={self.text}&p={i}')
            logging.info(f'Getting mods from page {i}')
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                response_to_ids(response)
            else:
                logging.warning(f'Failed to get mods from page {i}')
        logging.info(f'Got {self.ids}')
        return self.ids


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={'disable': ['E9999', 'W1203'], "max-line-length": 120})

    fetcher = WorkshopNewMods(107410)
    fetcher.get_mods(3)
