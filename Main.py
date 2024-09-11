import streamlit as st

from streamlit_option_menu import option_menu
import Settings as stng
from pages import QA_chat as chat
from pages import Intro as intro
from pages import KMS_embed as KMS
from pages import Chart as cht
from pages import pdf_parser as pdf_parser
from pages import Palette_kms as plt

if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'auto'

st.set_page_config(
    page_title="KMS QA Prototyping",
    page_icon="house",
    layout="wide",  # 또는 wide / centered
    initial_sidebar_state=st.session_state.sidebar_state,  # auto / collapsed
    menu_items={
        'Get Help': 'https://www.naver.com',
        'Report a bug': 'https://www.naver.com',
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

def hide_sidebar():
    # st.markdown("""
    # <style>
    #     section[data-testid="stSidebar"][aria-expanded="true"]{
    #         display: none;
    #     }
    # </style>
    # """, unsafe_allow_html=True)
    from st_pages import hide_pages
    hide_pages(['Main', 'Chart','Intro','KMS_embed','QA_chat', 'pdf_parser','Palette_kms'])  #main과 pages 디렉토리에 있는 메뉴를 숨김

hide_sidebar() 

with st.sidebar:
    selected = option_menu("Main Menu", [ 'KMS Embedding','Chat',"Prompt",'Parser','Setting','Palette'], 
            icons=[ 'book','android','list-task','gear'], menu_icon="house", default_index=0,
            styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "menu-title": {"font-size": "14px","color": "green"},
            "menu-icon": {"font-size": "14px"},
            "icon": {"color": "orange", "font-size": "20px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "lightblue"},
            "nav-link-selected": {"background-color": "cadetblue"},
    })
 
st.markdown(
    """
    <style>
    [data-testid="baseButton-secondary"] {
        font-size: 10px;
        color: white;
        background-color: lightskyblue;
    },
    [data-testid="stMarkdownContainer"]  {
        font-size: 10px;
        color: red;
    },
   </style>
    """,
    unsafe_allow_html=True
)

if selected == 'Intro':
    intro.app()

    with st.sidebar:
        st.markdown('## Side Bar ##')
        picture = st.camera_input("Take a picture")

        if picture:
           st.image(picture)

if selected == 'Chat':
    chat.run()

if selected == 'Setting':
    # cht.app()
    intro.app()

if selected == 'Parser':
    pdf_parser.app()

if selected == 'Prompt':
    st.subheader("Prompt Admin Panel")
    st.write("This is a prompt admin panel to be developed")


if selected == 'KMS Embedding':
    KMS.app()

if selected == 'Palette':
    plt.app()

# from st_pages import show_pages_from_config, add_page_title
# add_page_title()
# show_pages_from_config()