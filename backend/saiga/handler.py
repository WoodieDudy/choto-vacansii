import json
import logging

import re
import torch
from ts.torch_handler.base_handler import BaseHandler

from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

DEFAULT_MESSAGE_TEMPLATE = "<s>{role}\n{content}</s>\n"
DEFAULT_SYSTEM_PROMPT = "Ты — Сайга, русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им."

from conversation import Conversation, generate

logger = logging.getLogger(__name__)

MODEL_ZIP = 'model.zip'
MODEL_NAME = 'IlyaGusev/saiga_13b_lora'
RAW_WEIGHTS = ''
CHECKPOINT = ''


class ModelHandler(BaseHandler):
    def __init__(self):
        self.initialized = False
        self.map_location = None
        self.device = None
        self.model = None

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
        self.generation_config = GenerationConfig.from_pretrained(MODEL_NAME)
        setattr(self.generation_config, 'temperature', 0.6)
        setattr(self.generation_config, 'top_k', 15)
        print(self.generation_config)

    def initialize(self, context):
        properties = context.system_properties
        model_dir = properties.get('model_dir')

        gpu_id = properties.get('gpu_id')

        self.map_location, self.device = \
            (f'cuda:{gpu_id}', torch.device(f'cuda:{gpu_id}')) if torch.cuda.is_available() else \
                ('cpu', torch.device('cpu'))
        logger.info(f'Using device {self.device}')

        # if not os.path.exists(os.path.join(model_dir, "model")):
        #   with zipfile.ZipFile(os.path.join(model_dir, MODEL_ZIP), 'r') as zip_ref:
        #      zip_ref.extractall(model_dir)

        config = PeftConfig.from_pretrained(MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path,
            load_in_8bit=True,
            torch_dtype=torch.float16,
            device_map=self.device
        )
        self.model = PeftModel.from_pretrained(
            self.model,
            MODEL_NAME,
            torch_dtype=torch.float16
        )
        self.model.eval()

    def _filter_text(self, text):
        filtered_text = re.sub(r'[^а-яА-Яa-zA-Z0-9.,!?;:\-\'" \n<>/]', '', text)
        filtered_text = re.sub(r'([.,!?;:\-\'"])\1+', r'\1', filtered_text)

        return filtered_text

    def _get_prompt(self, q, fields):
        points = ["\"" + p + "\"" for p in fields]
        example_text = \
            """"Почепта Дальневосточной железной дороги  Мост 1222. армирование каркаса  Обязанности:  - Строительство Ж/Д путей; - бетонирование опор.  Требования: -опыт в строительстве приветствуется -работа в бригаде  Условия: - продолжительность вахты 60/30 (продление вахты возможно) - Официальное трудоустройство. - ЗП в срок и без задержек - Авансирование дважды в месяц по 15 000 рублей, 15 и 30 числа - Питание трехразовое за счет организации - выдача спецодежды и Сизов без вычета из заработной платы - Организованные отправки до объекта (покупка билетов) - Помощь в прохождение медицинского осмотра - Возможность получить квалификационные удостоверения - Карьерный рост до бригадира/мастера"
            """

        example_ans = \
            """"требования к соискателю": "Работа в бригаде. Опыт в строительстве приветствуется."
            "условия": продолжительность вахты 60/30 (продление вахты возможно) - Официальное трудоустройство. - ЗП в срок и без задержек - Авансирование дважды в месяц по 15 000 рублей, 15 и 30 числа - Питание трехразовое за счет организации - выдача спецодежды и Сизов без вычета из заработной платы - Организованные отправки до объекта (покупка билетов) - Помощь в прохождение медицинского осмотра - Возможность получить квалификационные удостоверения - Карьерный рост до бригадира/мастера"
            "описание вакансии": "Почепта Дальневосточной железной дороги  Мост 1222. армирование каркаса."
            "обязанности": "Строительство Ж/Д путей; - бетонирование опор."
            """

        return f'''Задание: Дан текст вакансии, выдели из этого текста пункты {', '.join(points)} и напиши их в такой форме:
<format-example>
{example_ans}
</format-example>
Если какой-то пункт отсутствует, то оставь после него пустую строку. Пункты кроме {', '.join(points)} писать запрещено.
Повторять одинаковые пункты несколько раз запрещено.
Приведу пример вакансии и ответа:
<example>
Текст вакансии: 
<text>
{example_text}
</text>
Для такой вакансии хорошим ответом будет:
<answer>
{example_ans}
</answer> 
</example>
Теперь я дам тебе настоящий текст вакансии, выдели из него нужные пункты в заданном формате.
Текст вакансии:
<text>
{q}
</text>
Ответ:
'''

    def parse_model_answer(self, text: str, fields: list):
        rows = text.split('\n')
        res = {}
        for row in rows:
            for point in fields:
                point = "\"" + point + "\""
                row = row.strip()
                if row.startswith(point):
                    key = point.replace("\"", "")
                    res[key] = row.replace(point + ": ", "").replace("\"", "").strip()
        return res

    def preprocess(self, requests):
        data = requests[0].get('body')
        prompt = self._get_prompt(self._filter_text(data['text']), data['fields'])
        return prompt, data['fields']

    def inference(self, model_input):
        conversation = Conversation()
        conversation.add_user_message(model_input)
        prompt = conversation.get_prompt(self.tokenizer)

        output = generate(self.model, self.tokenizer, prompt, self.generation_config)
        logger.info('Predictions successfully created.')

        return output

    def postprocess(self, model_output, fields):
        logger.info(f'Predictions: {model_output}')

        response = self.parse_model_answer(model_output, fields)

        return [json.dumps({'fields': response, 'output': model_output}, ensure_ascii=False)]

    def handle(self, data, context):
        model_input, fields = self.preprocess(data)
        model_output = self.inference(model_input)
        return self.postprocess(model_output, fields)
