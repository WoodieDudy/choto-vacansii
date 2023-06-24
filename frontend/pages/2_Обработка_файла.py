import json
from typing import Iterable

import pandas as pd
import streamlit as st
import streamlit_tags

from common.generation import DEFAULT_COLUMNS, generate
from common.export import export_as_csv, export_as_excel

from collections import defaultdict

st.set_page_config(
    page_title='Обработка файла',
    layout='wide'
)


def infer_text_field(json_data: list[dict]) -> str:
    field_lengths = defaultdict(list)
    for item in json_data:
        for k, v in item.items():
            if v:
                try:
                    field_lengths[k].append(len(str(v)))
                except Exception:
                    pass

    avg_field_length = {k: sum(v) / len(v) if v else 0 for k, v in field_lengths.items()}
    return max(avg_field_length, key=avg_field_length.get)


def pipeline(json_data: list[dict], text_field: str, fields: list[str]) -> Iterable[dict]:
    for item in json_data:
        text = item[text_field].strip()

        resp = generate(text, fields) if text else None
        for field in fields:
            item[field] = resp['fields'].get(field) if resp else None

        yield item


def handle_upload_tab(session):
    df_file = st.file_uploader('Загрузите .xlsx, .csv или .json файл', type=['csv', 'xlsx', 'json'])
    if df_file:
        file_name = df_file.name
        try:
            if file_name.endswith('.xlsx'):
                session['json_data'] = pd.read_excel(df_file, index_col=False).to_json(orient='records',
                                                                                       force_ascii=False)
            elif file_name.endswith('.csv'):
                session['json_data'] = pd.read_csv(df_file, index_col=False).to_json(orient='records',
                                                                                     force_ascii=False)
            else:
                session['json_data'] = json.load(df_file)
        except Exception:
            st.error('Не удалось прочитать файл. Возможно он поврежден')
        else:
            session['input_field'] = infer_text_field(session['json_data'])

    run_col, xlsx_col, csv_col = st.columns([1, 0.12, 0.12])

    if run_col.button('Запустить'):
        if not session['json_data'] or not session['json_data'][0]:
            st.error('Необходимо загрузить файл')
        elif session['input_field'] not in session['json_data'][0]:
            st.error(f"В файле нет поля '{session['input_field']}'")
        elif not session['fields']:
            st.error('Список полей для выделения пуст')
        else:
            total = len(session['json_data'])

            pbar = st.progress(0, text='Операция запущена. Это может занять много времени', total=total)

            session['result'] = []

            for i, resp in enumerate(pipeline(session['json_data'], session['input_field'], session['fields'])):
                session['result'].append(resp)
                pbar.progress((i + 1) / total)

    if session['result']:
        output_path = export_as_excel(session['result'])
        with open(output_path, 'rb') as f:
            xlsx_col.download_button('Скачать .xlsx', data=f.read(),
                                     mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        csv_col.download_button('Скачать .csv', export_as_csv(session['result']), mime='text/csv')


def handle_settings_tab(session):
    if not session['json_data'] or not session['json_data'][0]:
        session['input_field'] = st.text_input('Названия колонки, в которой лежит описание вакансии',
                                               value=session['input_field'])
    else:
        session['input_field'] = st.selectbox('Названия колонки, в которой лежит описание вакансии',
                                              options=session['json_data'][0].keys(), index=0)
    session['fields'] = streamlit_tags.st_tags(session['fields'], label='Список полей для выделения',
                                               text='Добавьте или удалите поле')
    st.warning('Это экспериментальная функция.\nНе стоит задавать слишком сложные поля и слишком много полей.')


def init_session():
    if 'fields' not in st.session_state:
        st.session_state.fields = DEFAULT_COLUMNS
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'input_field' not in st.session_state:
        st.session_state.input_field = 'text'
    if 'result' not in st.session_state:
        st.session_state.result = None
    return st.session_state


def streamlit_main():
    upload_tab, settings_tab = st.tabs(['Загрузка', 'Настройки'])

    session = init_session()

    with upload_tab:
        handle_upload_tab(session)

    with settings_tab:
        handle_settings_tab(session)


if __name__ == "__main__":
    streamlit_main()
