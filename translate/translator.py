import json
import logging
import requests
from deep_translator import GoogleTranslator

class Translator:
    """
    Base class for translators
    """
    min_length: int
    max_length: int
    rate_limit: str
    logger: logging.Logger
    def __init__(self, min_length: int = 0, max_length: int = 1000, rate_limit: str = "") -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.rate_limit = rate_limit
        self.logger = logging.getLogger(self.__class__.__name__)

    def translate(self, text: str, aim: str) -> dict:
        raise NotImplementedError

class GoogleTranslator(Translator):

    def __init__(self, min_length: int = 0):
        super().__init__(min_length, self.max_length)

    def translate(self, text: str, aim: str) -> dict:
        self.logger.info(f"Translating text: {text}")
        # Add your implementation here
        pass

class LLMTranslator(Translator):
    """
    """
    def __init__(self, min_length: int = 0, LLM_token: str = "", rate_limit: str = "",
                 LLM_API: str = "", LLM_model: str = "", LLM_prompt: str = "",
                 LLM_input_price: float = 0.0, LLM_output_price: float = 0.0) -> None:
        self.LLM_token = LLM_token
        if LLM_API == "":
            self.LLM_API = "https://api.openai.com/v1/completions"
        else:
            self.LLM_API = LLM_API
        self.LLM_model = LLM_model
        if self.LLM_prompt == "":
            self.LLM_prompt = "You are a helpful assistant that helps people with translation. Translate the following text to {language}:"
        else:
            self.LLM_prompt = LLM_prompt
        self.LLM_input_price = LLM_input_price
        self.LLM_output_price = LLM_output_price
        self.LLM_input_token = 0
        self.LLM_output_token = 0
        super().__init__(min_length, self.max_length, rate_limit)

    def translate(self, text: str, aim: str) -> dict:
        if text == "":
            self.logger.warning("Empty text")
            return {"text": "", "code": -1}
        elif len(text) < self.min_length:
            self.logger.warning("Text too short")
            return {"text": text, "code": -1}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.LLM_token}"
        }

        data = {
            "model": self.LLM_model,
            "messages": [
                {
                    "role": "system",
                    "content": self.LLM_prompt.replace("{language}", aim)
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        }

        try:
            response = requests.post(self.LLM_API, headers=headers, data=json.dumps(data))
            response_data = response.json()
            if 'usage' in response_data:
                self.logger.debug(f"Prompt tokens: {response_data['usage']['prompt_tokens']}, Completion tokens: {response_data['usage']['completion_tokens']}")
            else:
                self.logger.warning('No usage data found')

            if response.status_code == 200:
                openai_result = response_data['choices'][0]['message']['content']
                self.logger.info(f'{text} -> {openai_result}')
                return {"text": openai_result, "code": response.status_code}
            else:
                self.logger.error(f"Request failed, status code: {response.status_code}")
                self.logger.error(headers)
                self.logger.error(data)
                self.logger.error(response.text)
                return {"text": "Unexpected", "code": response.status_code}
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return {"text": "Failed", "code": -1}

    def get_price(self) -> float:
        usage = (self.LLM_input_token * self.LLM_input_price +
                self.LLM_output_token * self.LLM_output_price)
        self.logger.info(f"Usage cost: {usage}")
        return usage

if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={'disable': ['E9999', 'W1203']})