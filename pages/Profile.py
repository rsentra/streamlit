import streamlit as st
import pandas as pd

def tab1_func():
    st.write('tab1')


def tab2_func():
    st.write('tab1')

def app():
    tab1, tab2= st.tabs(["Cat", "Dog"])
    with tab1:
        tab1_func()

    with tab2:
        tab2_func()