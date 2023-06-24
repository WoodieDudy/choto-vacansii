import pandas as pd
import streamlit as st
import streamlit_tags as stt


def pipeline(df, resp_column, required_columns):
    # Do nasty things
    return df


def streamlit_main():
    st.header('Загрузка данных')
    upload_tab, settings_tab = st.tabs(['Данные', 'Настройки'])

    df = None
    input_column = 'text'

    with upload_tab:
        csv_path = st.file_uploader('Загрузите .csv файл', type='csv')
        if csv_path:
            df = pd.read_csv(csv_path, index_col=0)

    with settings_tab:
        col1, col2 = st.columns(2)
        resp_df_column_input = col1.text_input('Колонка ответа', value=input_column)
        if resp_df_column_input:
            input_column = resp_df_column_input

        if df:
            resp_df_column = col2.selectbox('Показать доступные колонки', options=df.columns)
            if resp_df_column:
                input_column = resp_df_column

        required_columns = stt.st_tags(label='Колонка для ответа')

    can_continue = df and required_columns and input_column
    run_button = st.button('Запустить', disabled=not can_continue)

    if run_button:
        if input_column not in df.columns:
            st.error(f"В .csv файле нет колонки '{input_column}'")
        else:
            df = pipeline(df, input_column, required_columns)
            st.dataframe(df)


if __name__ == "__main__":
    st.set_page_config(
        page_title='Обработка файла',
        layout='wide'
    )
    streamlit_main()
