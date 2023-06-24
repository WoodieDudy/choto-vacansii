import os
import zipfile
import logging
from io import BytesIO

import torch
from ts.torch_handler.base_handler import BaseHandler

from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from src.conversation import Conversation, generate


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

                
    def initialize(self, context):
        properties = context.system_properties
        model_dir = properties.get('model_dir')
 
        gpu_id = properties.get('gpu_id')

        self.map_location, self.device = \
            (f'cuda:{gpu_id}', torch.device(f'cuda:{gpu_id}')) if torch.cuda.is_available() else \
            ('cpu', torch.device('cpu'))
        logger.info(f'Using device {self.device}')

        if not os.path.exists(os.path.join(model_dir, "model")):
            with zipfile.ZipFile(os.path.join(model_dir, MODEL_ZIP), 'r') as zip_ref:
                zip_ref.extractall(model_dir)

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

    def preprocess(self, requests):
        data = requests[0].get('body')
        return data['text']

    def inference(self, model_input):
        conversation = Conversation()
        conversation.add_user_message(model_input)
        prompt = conversation.get_prompt(self.tokenizer)

        output = generate(self.model, self.tokenizer, prompt, self.generation_config)
        logger.info('Predictions successfully created.')
        
        return output

    def postprocess(self, model_output):
        preds = model_output.detach().cpu().tolist()
        logger.info(f'Predictions: {preds}')
        return preds

    def handle(self, data, context):
        model_input = self.preprocess(data).to(self.device)
        model_output = self.inference(model_input)
        return self.postprocess(model_output)
