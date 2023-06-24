import json

import pandas as pd
import streamlit as st
import streamlit_tags

from common.params import DEFAULT_COLUMNS

from common.export import export_as_csv, export_as_excel


def pipeline(json_data, resp_column, required_columns):
    # Do nasty things
    return json_data


def handle_upload_tab(session):
    df_file = st.file_uploader('Загрузите .xlsx, .csv или .json файл', type=['csv', 'xlsx', 'json'])
    if df_file:
        file_name = df_file.name
        try:
            if file_name.endswith('.xslx'):
                session['json_data'] = pd.read_excel(df_file).to_json()
            elif file_name.endswith('.csv'):
                session['json_data'] = pd.read_csv(df_file, index_col=0).to_json()
            else:
                session['json_data'] = json.load(df_file)
        except Exception:
            st.error('Не удалось прочитать файл. Возможно он поврежден')

    run_col, xlsx_col, csv_col = st.columns([1, 0.12, 0.12])

    if run_col.button('Запустить'):
        if not session['json_data'] or not session['json_data'][0]:
            st.error('Необходимо загрузить файл')
        elif session['input_field'] not in session['json_data'][0]:
            st.error(f"В файле нет поля '{session['input_field']}'")
        elif not session['fields']:
            st.error('Список полей для выделения пуст')
        else:
            session['result'] = pipeline(session['json_data'], session['input_field'], session['fields'])

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
    st.set_page_config(
        page_title='Обработка файла',
        layout='wide'
    )
    streamlit_main()
