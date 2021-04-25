import streamlit as st
import numpy as np
import pandas as pd
import pickle 
import io
import base64
from pandas_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
import df_helper as helper # custom script 

def highlight(txt):
    return '<span style="color: #F04E4E">{}</span>'.format(txt)

def download_file(df, extension):
    if extension == 'csv': # csv 
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode() 
    else: # pickle
        b = io.BytesIO()
        pickle.dump(df, b)
        b64 = base64.b64encode(b.getvalue()).decode()
    
    href = f'<a href="data:file/csv;base64,{b64}" download="new_file.{extension}">Download {extension}</a>'
    st.write(href, unsafe_allow_html=True) 

def explore(df):
    pr = ProfileReport(df, explorative=True)
    expander_df = st.beta_expander('Data frame')
    expander_df.write(df)
    st_profile_report(pr)

def transform(df):
    # SAMPLE
    expander_sample = st.beta_expander('Sample size (%)')
    expander_sample.text('Select a random sample from this dataset')
    frac = expander_sample.slider('Random sample (%)', 1, 100, 100)
    if frac < 100:
        df = df.sample(frac=frac/100)

    # COLUMNS / FIELDS
    expander_fields = st.beta_expander('Select fields')
    expander_fields.text('Select and order the fields')
    cols = expander_fields.multiselect('Columns', df.columns.tolist(), df.columns.tolist())
    df = df[cols]
    if len(cols)<1:
        st.write('You must select at least one column.')
        return
    types = {'-':None, 'Boolean': '?', 'Byte': 'b', 'Integer':'i',
                 'Floating point': 'f', 'Date Time': 'M', 
                 'Time': 'm', 'Unicode String':'U', 
                 'Object': 'O'}
    new_types = {}
    
    # CONVERT DATA TYPES
    expander_types = st.beta_expander('Convert Data Types')
    
    for i, col in enumerate(df.columns):
        txt = f'Convert {col} from {highlight(df[col].dtypes)} to:'
        expander_types.markdown(txt, unsafe_allow_html=True)
        new_types[i] = expander_types.selectbox('Type:'
                                            ,[*types]
                                            ,index=0
                                            ,key=i)

    # HANDLE NULLS
    expander_nulls = st.beta_expander('Missing values')
    null_dict = {'-':None, 'Remove': 0, 'Note':1, 
                 'Average': 2, 'Median': 3, 'Zero':4}
    
    n_dict = {}
    cols_null = []
    for i, c in enumerate(df.columns):
        if df[c].isnull().values.any():
            cols_null.append(c)
            txt = '{} has {} null values'.format(c, df[c].isnull().sum())
            expander_nulls.write(txt)
            n_dict[i] = expander_nulls.selectbox('What to do with Nulls:'
                                                ,[*null_dict]
                                                ,index=0
                                                ,key=i)
    
    # HANDLE DUPLICATES
    expander_duplicates = st.beta_expander('Duplicate rows')
    duplicates_count = len(df[df.duplicated(keep=False)])
    if duplicates_count > 0:
        expander_duplicates.write(df[df.duplicated(keep=False)].sort_values(df.columns.tolist()))
        duplicates_dict = {'Keep':None, 'Remove all':False, 'Keep first':'first', 'Keep last':'last'}
        action = expander_duplicates.selectbox('Handle duplicates:', [*duplicates_dict])
    else:
        expander_duplicates.write('No duplicate rows')
    
    # ORDER VALUES
    expander_sort = st.beta_expander('Order values')
    sort_by = expander_sort.multiselect('Sort by:', df.columns.values)
    order_dict = {'Ascending':True, 'Descending':False}
    ascending = []
    for i, col in enumerate(sort_by):
        order = expander_sort.radio(f'{col} order:', [*order_dict])
        ascending.append(order_dict[order])

    # DOWNLOAD BUTTONS
    st.text(" \n") #break line
    col1, col2, col3 = st.beta_columns([.3, .3, 1])
    with col1:
        btn1 = st.button('Show Data')
    with col2:
        btn2 = st.button('Get CSV')
    with col3:
        btn3 = st.button('Get Pickle')

    if btn1 or btn2 or btn3:
        st.spinner()
        with st.spinner(text='In progress'):
            # Transform
            df = helper.convert_dtypes(df, types, new_types)
            df = helper.handle_nulls(df, null_dict, n_dict)
            if duplicates_count > 0:
                df = helper.handle_duplicates(df, duplicates_dict, action)
            if sort_by: 
                df = df.sort_values(sort_by, ascending=ascending)
            # Display/ download
            if btn1:
                st.write(df)
            if btn2:
                download_file(df, "csv")
            if btn3:
                download_file(df, "pickle")
    
    #return df

def main():
    st.title('Fast Review')
    st.write('A general purpose data exploration app to validate and perform small corrections')

    file = st.file_uploader("Upload file", type=['csv', 'xlsx', 'pickle'])

    if not file:
        st.write(f"Upload a {highlight('.csv')}, {highlight('.xlsx')} or {highlight('.pickle')} to get started",
                unsafe_allow_html = True)
        return

    task = st.sidebar.radio('Task', ['Explore', 'Transform'], 0)

    df = helper.get_df(file)

    if task == 'Explore':
        explore(df)
    else:
        transform(df)

main()