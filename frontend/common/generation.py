import json
from typing import Optional

import requests

import logging

logger = logging.getLogger(__name__)

MODEL_ENDPOINT = 'https://bert-is-bad.serveo.net/predictions/saiga'

DEFAULT_COLUMNS = [
    'условия',
    'требования к соискателю',
    'описание вакансии',
    'обязанности',
]


def generate(text: str, fields: list, model_endpoint: str = MODEL_ENDPOINT) -> Optional[dict]:
    try:
        resp = requests.post(model_endpoint, json={'text': text, 'fields': fields}, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        logger.exception(e)
        return None

    try:
        # print(resp.content.decode('utf-8'))
        return json.loads(resp.content.decode('utf-8'))
    except Exception as e:
        logger.exception(e)
        return None
