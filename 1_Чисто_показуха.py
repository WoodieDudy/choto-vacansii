import re

import streamlit as st


def extract_field(text: str, field: str) -> str:
    match = re.findall(rf"{field}\s*:\s*(.+?);", text)
    best_match = ''
    for m in match:
        if m.strip() and len(m) > len(best_match):
            best_match = m
    return best_match if best_match else 'null'


def generate(text: str) -> str:
    # Do magic
    return text


def pipeline(text: str, output_columns: list[str]) -> dict:
    fields = "\n".join(oc + ':' for oc in output_columns)
    prompt = f"""Дано описание вакансии;
Нужно из него выделить следующие поля, если они есть, иначе оставить пустыми;
Выводи поля по одному в строке в формате [поле]: [значение];
{fields}s
-    
Описание вакансии;
{text}
"""

    answer = generate(prompt)
    print(answer)
    result = {field: extract_field(answer, field) for field in output_columns}
    print(result)
    return result


resp = {}


def streamlit_main():
    global resp

    st.set_page_config(
        page_title='Чисто показуха',
        layout='wide'
    )
    st.header('AUE')

    col1, col2 = st.columns(2)
    input_text = col1.text_area('Введите текст', height=300)

    output_columns = [
        'Условия',
        'Требования',
        'Место',
        'Время',
        'Примечания'
    ]

    st_output_columns = [col2.empty() for _ in output_columns]

    run_button = col1.button('Амогус')
    if run_button:
        if not input_text:
            col1.error('Введите описание вакансии')
        else:
            resp = pipeline(input_text, output_columns)

    for st_oc, oc in zip(st_output_columns, output_columns):
        if resp and oc in resp:
            st_oc.text_area(oc, value=resp[oc], height=100)
        else:
            st_oc.text_area(oc, value='', disabled=True, height=100)


if __name__ == "__main__":
    streamlit_main()
