"""
version: 1.0.0
author: Wuyilingwei
This module provides class of translators
Support OPENAI-STYLED LLM API Translator
TODO: Google Translator
"""
import time
import json
import logging
import requests
from deep_translator import GoogleTranslator


class Translator:
    """
    Base class for translators
    This class difines the basic structure of a translator
    It should not be instantiated
    """
    min_length: int
    max_length: int
    rate_limit: str
    rate_limit_num: int
    rate_limit_seconds: int
    request_history: list[float]
    logger: logging.Logger

    def __init__(self, min_length: int = 0, max_length: int = 1000, rate_limit: str = "10/s") -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.rate_limit = rate_limit
        self.request_history = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self._parse_rate_limit()

    def _parse_rate_limit(self) -> None:
        """
        Parse the rate limit string into number and unit
        """
        if self.rate_limit:
            num, unit = self.rate_limit.split('/')
            self.rate_limit_num = int(num)
            if unit == 's':
                self.rate_limit_seconds = 1
            elif unit == 'm':
                self.rate_limit_seconds = 60
            elif unit == 'h':
                self.rate_limit_seconds = 3600
            else:
                raise ValueError("Unsupported rate limit unit")
        else:
            self.rate_limit_num = None
            self.rate_limit_seconds = None

    def _check_rate_limit(self) -> None:
        """
        Check if the rate limit is exceeded
        """
        if not self.rate_limit_num:
            return
        current_time = time.time()
        self.request_history = [t for t in self.request_history if current_time - t < self.rate_limit_seconds]
        if len(self.request_history) >= self.rate_limit_num:
            sleep_time = self.rate_limit_seconds - (current_time - self.request_history[0])
            self.logger.info(f"Rate limit exceeded, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            self.request_history = [t for t in self.request_history if current_time - t < self.rate_limit_seconds]

    def translate(self, text: str, aim: str) -> dict:
        """
        Translate the text to the target language
        """
        raise NotImplementedError

    def get_price(self) -> float:
        """
        Calculate the usage cost of the translator
        """
        raise NotImplementedError


class TranslatorGoogle(Translator):
    """
    Google Translator
    THIS CLASS COULD NOT WORK
    """
    def __init__(self, min_length: int = 3, max_length: int = 1000, rate_limit: str = "10/s") -> None:
        super().__init__(min_length, max_length, rate_limit)
        raise NotImplementedError("Google Translator is not supported yet")

    def translate(self, text: str, aim: str) -> dict:
        self.logger.info(f"Translating text: {text}")
        self._check_rate_limit()
        self.request_history.append(time.time())
        if text == "":
            self.logger.warning("Empty text")
            return {"text": "", "code": -1}
        elif len(text) < self.min_length:
            self.logger.warning("Text too short")
            return {"text": text, "code": -1}
        try:
            GoogleTranslator(source='auto', target=aim).translate(text)
            self.logger.info(f"Translated text: {text}")
            return {"text": text, "code": 200}
        except (requests.RequestException, ValueError) as e:
            self.logger.error(f"Translation failed: {e}")
            return {"text": "Failed", "code": -1}

    def get_price(self) -> float:
        """
        Calculate the usage cost of the translator
        """
        # Google Translator does not provide a usage cost
        return 0.0

    def translate_with_context(self, text: str, context: dict, target_lang: str) -> dict:
        """Google翻译的上下文翻译（简化版）"""
        import time
        
        # Google翻译不支持复杂上下文，使用普通翻译
        # 但可以利用历史翻译进行一致性检查
        translation = self.translate(text, target_lang)
        
        # 检查与历史翻译的一致性
        if context.get('previous_translations'):
            for prev in context['previous_translations']:
                if prev['raw'] == text and prev['translation']:
                    # 如果找到完全相同的历史翻译，优先使用
                    translation = prev['translation']
                    break
        
        return {
            'translation': translation,
            'auxiliary_lang': '',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }


class TranslatorLLM(Translator):
    """
    OPENAI-STYLED LLM API Translator
    """
    llm_data: dict

    def __init__(self, min_length: int = 3, max_length: int = 1000, rate_limit: str = "10/s",
                 llm_info: dict = None) -> None:
        if llm_info is None:
            llm_info = {}
        self.llm_data = {
            "api": llm_info.get("api", "https://api.openai.com/v1/chat/completions"),
            "token": llm_info.get("token", ""),
            "model": llm_info.get("model", "gpt-4o-mini"),
            "prompt": llm_info.get("prompt", "You are a helpful assistant that helps people with translation."
                                   "Translate the given text to {language} (Language Code) and only return the translated text."),
            "input_price": llm_info.get("input_price", 0.0),
            "output_price": llm_info.get("output_price", 0.0),
            "input_token": 0,
            "output_token": 0
        }
        super().__init__(min_length, max_length, rate_limit)

    def translate(self, text: str, aim: str) -> dict:
        if self.llm_data["token"] == "":
            raise ValueError("API token is required")
        self._check_rate_limit()
        self.request_history.append(time.time())
        if text == "":
            self.logger.warning("Empty text")
            return {"text": "", "code": -1}
        elif len(text) < self.min_length:
            self.logger.warning("Text too short")
            return {"text": text, "code": -1}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_data['token']}"
        }

        data = {
            "model": self.llm_data["model"],
            "messages": [
                {
                    "role": "system",
                    "content": self.llm_data["prompt"].replace("{language}", aim)
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        }

        try:
            self.logger.debug(headers)
            self.logger.debug(data)
            response = requests.post(self.llm_data["api"], headers=headers, data=json.dumps(data))
            response_data = response.json()
            if 'usage' in response_data:
                self.logger.debug(f"Prompt tokens: {response_data['usage']['prompt_tokens']},"
                                  f"Completion tokens: {response_data['usage']['completion_tokens']}")
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
        """
        Calculate the usage cost of the translator
        """
        usage = (self.llm_data["input_token"] * self.llm_data["input_price"]
                 + self.llm_data["output_token"] * self.llm_data["output_price"])
        self.logger.info(f"Usage cost: {usage}")
        return usage

    def translate_with_context(self, text: str, context: dict, target_lang: str) -> dict:
        """使用上下文信息进行翻译"""
        import time
        
        # 构建提示词
        prompt = self._build_context_prompt(text, context, target_lang)
        
        try:
            # 调用LLM进行翻译
            result = self._call_llm_with_context(prompt)
            
            return {
                'translation': result.get('translation', ''),
                'auxiliary_lang': result.get('auxiliary_lang', ''),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.logger.error(f"LLM translation with context failed: {e}")
            # 降级到普通翻译
            return {
                'translation': self.translate(text, target_lang),
                'auxiliary_lang': '',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _build_context_prompt(self, text: str, context: dict, target_lang: str) -> str:
        """构建包含上下文的提示词"""
        prompt_parts = [
            f"请将以下文本翻译为{target_lang}:",
            f"原文: {text}",
            f"上下文: 这是游戏mod '{context.get('mod_name', '')}' 中键 '{context.get('key', '')}' 的翻译"
        ]
        
        # 添加历史翻译信息
        if context.get('previous_translations'):
            prompt_parts.append("\n历史翻译参考:")
            for prev in context['previous_translations'][:3]:  # 最多3个参考
                prompt_parts.append(f"- 版本{prev['version']}: '{prev['raw']}' -> '{prev['translation']}'")
        
        # 添加相似翻译信息
        if context.get('similar_translations'):
            prompt_parts.append("\n相似文本翻译参考:")
            for sim in context['similar_translations'][:2]:  # 最多2个参考
                prompt_parts.append(f"- '{sim['raw']}' -> '{sim['translation']}'")
        
        prompt_parts.append("\n请提供准确且一致的翻译:")
        
        return "\n".join(prompt_parts)
    
    def _call_llm_with_context(self, prompt: str) -> dict:
        """调用LLM API进行上下文翻译"""
        # 这里需要根据你的LLM配置实现具体的API调用
        # 返回格式: {'translation': '翻译结果', 'auxiliary_lang': '辅助语言(可选)'}
        
        # 示例实现 - 需要根据实际LLM API调整
        try:
            # 假设使用某个LLM API
            response = self._make_llm_request(prompt)
            return {
                'translation': response.get('text', ''),
                'auxiliary_lang': ''
            }
        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            raise
