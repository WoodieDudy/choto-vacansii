import re
import json
from typing import Iterable

import requests
import streamlit as st
import streamlit_tags

from common.export import export_as_txt, export_as_json

st.set_page_config(
    page_title='Интерактивный режим',
    layout='wide'
)


def extract_field(text: str, field: str) -> str:
    match = re.findall(rf"{field}\s*:\s*(.+?);", text)
    best_match = ''
    for m in match:
        if m.strip() and len(m) > len(best_match):
            best_match = m

    return best_match if best_match else None


def generate(text: str, fields: list) -> dict:
    try:
        resp = requests.post('https://bert-is-bad.serveo.net/predictions/saiga',
                             json={'text': text, 'fields': fields}, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print('Error:', e)
        return None

    try:
        print(resp.content.decode('utf-8'))
        return json.loads(resp.content.decode('utf-8'))
    except Exception as e:
        print('Error:', e)
        return None


def get_pregen_suggestions(text: str) -> Iterable[str]:
    if len(text) < 100:  # For no reason
        yield 'Описание вакансии слишком короткое. Нужно хотя бы 100 символов.'
    if len(text) > 3000:  # Max tokens is 2048
        yield 'Описание вакансии слишком длинное. Максимум - 3000 символов.'


def pipeline(text: str, output_columns: list[str]) -> dict:
    answer = generate(text, output_columns)
    if not answer:
        return {}

    # result = {field: extract_field(answer, field) for field in output_columns}
    return answer['fields']


def init_session():
    if 'text' not in st.session_state:
        st.session_state.text = ''
    if 'fields' not in st.session_state:
        st.session_state.fields = [
            'условия',
            'требования к соискателю',
            'описание вакансии',
            'обязанности',
        ]
    if 'response' not in st.session_state:
        st.session_state.response = {}
    return st.session_state


def handle_int_tab(session):
    col1, col2 = st.columns(2)
    session['text'] = col1.text_area('Введите текст', height=300, value=session['text'])

    st_output_columns = [col2.empty() for _ in session['fields']]

    run_col, reset_col = col1.columns(2)

    if run_col.button('Обработать'):
        if not session['text']:
            col1.error('Введите описание вакансии')
        else:
            pre_suggestions = list(get_pregen_suggestions(session['text']))
            if not pre_suggestions:
                session['response'] = pipeline(session['text'], session['fields'])
                if not session['response']:
                    col1.error('Не удалось отправить запрос. Возможно проблема с соединением.')
            else:
                for sug in pre_suggestions:
                    col1.warning(sug)

    if reset_col.button('Сбросить'):
        st.experimental_rerun()

    for st_oc, oc in zip(st_output_columns, session['fields']):
        if session['response'] and oc in session['response']:
            st_oc.text_area(oc, value=session['response'][oc] or '', height=100)
        else:
            st_oc.text_area(oc, value='', disabled=True, height=100)


def handle_settings_tab(session):
    old = session['fields']
    session['fields'] = streamlit_tags.st_tags(old, label='Список полей для выделения',
                                               text='Добавьте или удалите поле')
    st.warning('Это экспериментальная функция.\nНе стоит задавать слишком сложные поля и слишком много полей.')

    if old != session['fields']:
        if session['response'] or session['text']:
            st.info('Для применения изменений необходимо сбросить данные с первой страницы')
            if st.button('Сбросить?'):
                st.experimental_rerun()
        else:
            st.experimental_rerun()


def handle_export_tab(session):
    resp = session['response']
    if resp:
        st.download_button('Скачать .txt', export_as_txt(resp), mime='text/plain')
        st.download_button('Скачать .json', export_as_json(session['text'], resp), mime='application/json')
    else:
        st.warning('Для экспорта необходимо заполнить какое-либо поле')


def streamlit_main():
    session = init_session()

    int_tab, settings_tab, export_tab = st.tabs(['Запуск', 'Настройки', 'Экспорт'])

    with int_tab:
        handle_int_tab(session)

    with settings_tab:
        handle_settings_tab(session)

    with export_tab:
        handle_export_tab(session)


if __name__ == "__main__":
    streamlit_main()
