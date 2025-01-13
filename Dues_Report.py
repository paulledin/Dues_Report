# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 13:40:15 2024

@author: Paul Ledin
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(
    page_title="America's Credit Unions",
    layout="wide",
    initial_sidebar_state="expanded")

thePassPhrase = st.secrets["thePassPhrase"]
dbConn = st.connection("snowflake")
###############################################################################
#Function Definitions
###############################################################################
@st.cache_data
def getCUData(nimble_cuna_id):
    return (dbConn.session().sql("SELECT f1.nimble_cuna_id, f1.name, f1.st_address, f1.st_city, f1.st_state FROM acus_data.core_data.core_data f1 WHERE f1.nimble_cuna_id='" + nimble_cuna_id + "' ").to_pandas())

@st.cache_data
def getStateNames():
    return (dbConn.session().sql("SELECT full_name FROM acus_data.core_data.state_codes ").to_pandas())

@st.cache_data
def getLeagueNames():
    return (dbConn.session().sql("SELECT distinct(league_name) FROM acus_data.core_data.core_data WHERE league_name IS NOT NULL AND league_name!='Alternatives FCU' AND status='A' ORDER BY league_name ").to_pandas())

###############################################################################
#Start building Streamlit App
###############################################################################
with st.sidebar:
    st.markdown('![alt text](https://raw.githubusercontent.com/paulledin/data/master/ACUS.jpg)')
    passphrase = st.text_input("### Please enter the passphrase:")

if (passphrase != thePassPhrase):
    if len(passphrase) > 0:
        st.markdown('# Passphrase not correct....')
        st.markdown('### Please try again or contact: pledin@americascreditunions.org for assistance.')
else:
    with st.sidebar:
        st.title('AFL / Dues Report')
    
        report_type = ['Individual CU','State', 'League']
        selected_report_type = st.selectbox('Report Type:', report_type)

        if (selected_report_type == 'State'):
            selected_state = st.selectbox('State:', getStateNames())
        elif (selected_report_type == 'League'):
            selected_league = st.selectbox('League:', getLeagueNames())
        else:
            nimble_cuna_id = st.text_input("NIMBLE_CUNA_ID:", "10013583")  
                
    
    col = st.columns((6, 6), gap='medium')
    with col[0]:
        if (selected_report_type == 'Individual CU'):
            st.markdown('NIMBLE_CUNA_ID: ' + nimble_cuna_id)
            thisCU = getCUData(nimble_cuna_id)
            st.write(len(thisCU))
            #st.write(thisCU)
        

    with col[1]:
        st.markdown('')
        




