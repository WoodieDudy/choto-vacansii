import json

import pandas as pd


def export_as_json(input_text: str, fields: dict):
    data = {
        'raw_text': input_text,
        'fields': fields
    }

    return json.dumps(data, ensure_ascii=False, indent=4)


def export_as_txt(fields: dict):
    return '\n\n'.join(f'{field}:\n{value}' for field, value in fields.items() if value)


def export_as_csv(json_data: list[dict]):
    return pd.DataFrame(json_data).to_csv(index=False)


def export_as_excel(json_data: list[dict]):
    pd.DataFrame(json_data).to_excel('.temp.xlsx', index=False)
    return '.temp.xlsx'
