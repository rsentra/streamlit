import sys, os
# sys.path.append('../gpt/libs')

import streamlit as st
import tiktoken
from loguru import logger

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PyMuPDFLoader
# from langchain.document_loaders import Docx2txtLoader
# from langchain.document_loaders import UnstructuredPowerPointLoader
from langchain.document_loaders import UnstructuredHTMLLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS

# from streamlit_chat import message
from langchain.callbacks import get_openai_callback
from langchain.memory import StreamlitChatMessageHistory

import libs.faiss_vector as faiss_v   #user defined function
import models.database as db
import models.html as htm
import pandas as pd

# 참고소스
# https://github.com/insightbuilder/python_de_learners_data/blob/main/code_script_notebooks/projects/LLM_practical_appln/multiFileEmbedFaiss.ipynb 

OPENAI_API_KEY = st.secrets["opai_api_key"]['api_key']
 
def run():
    # st.set_page_config(
    # page_title="Chat for POC of KMS",
    # page_icon=":books:")
    
    tabs_font_css = """
    <style>
    div[class*="stTextArea"] label p {
    font-size: 12px;
    color: red;
    }

    div[class*="stTextInput"] label p {
    font-size:12px;
    color: blue;
    }

    div[class*="stNumberInput"] label p {
    font-size: 12px;
    color: green;
    }

    </style>
    """
    st.markdown(tabs_font_css, unsafe_allow_html=True)
       
    st.title("_KMS :red[QA Chat]_ :books:")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    if "processComplete" not in st.session_state:
        st.session_state.processComplete = None

    if "docName" not in st.session_state:
        st.session_state.docName = None

    if "vectorList" not in st.session_state:
        st.session_state.vectorList = None

    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = None

    process = None
    reset = None
    with st.sidebar:
        # st.info('KMS Chat poc를 위한 페이지입니다')
#         st.image('data/sunrise.png', caption='Sunrise by the mountains')
        # upload = st.toggle('Upload Document :open_file_folder: ')
        job = st.radio("select", ["Upload","KMS"], label_visibility="collapsed",horizontal =True,index=None)
        if job == "Upload":
           uploaded_files =  st.file_uploader("select file",type=['pdf','docx','html'],accept_multiple_files=False, label_visibility="collapsed")
           kms_vector = False
        elif job == "KMS":
             content_id = st.text_input("content id", key="content_id", label_visibility="collapsed",placeholder="KMS content id here!!! ")
             
             with st.container():
                 kms_vector = st.checkbox("KMS 통합임베딩", key = "custom_checkbox")

        openai_api_key = st.text_input(":key: OpenAI API Key", key="chatbot_api_key", type="password")

        if job == "Upload":
            col1, col2 = st.columns(2)
            with col1:
                process = st.button("Process", on_click = upload_process, args = [openai_api_key,uploaded_files, kms_vector])
            with col2:    
                reset = st.button("Reset Vector", on_click = reset_vector)
        elif job == "KMS":
            db_process = st.button("Process", on_click = query_process, args = [openai_api_key,content_id, kms_vector])

        st.session_state.vectorList = faiss_v.get_vectored_files()
        vector_sel = st.multiselect(
            ':blue[Vectorised Documents]', options = st.session_state.vectorList,placeholder="Choose an option for query"
        )
        st.info(f'query to {",".join(vector_sel)}')
       
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [{"role": "assistant", 
                                        "content": "대상 문서를 선택 후 질문!!!"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    history = StreamlitChatMessageHistory(key="chat_messages")

    # Chat logic
    if query := st.chat_input("질문을 입력해주세요."):
        st.session_state.messages.append({"role": "user", "content": query})
        if not openai_api_key:
            openai_api_key = OPENAI_API_KEY
            # st.info("Please add your OpenAI API key to continue.--222")
            # st.stop()
        
        if len(vector_sel)==0:
            st.info("Please  select your documents to continue.")
            st.stop()

        with st.chat_message("user"):
            st.markdown(query)

        # 선택한 문서로 llm chain가져옴
        # if (not st.session_state.docName) or (st.session_state.docName != vector_sel):
        #     get_vector_chain(vector_sel, openai_api_key)
        #     st.session_state['docName'] =  vector_sel
        # else:
        #      print('>>> old : ',vector_sel)
        #      print(st.session_state.conversation)
        get_vector_chain(vector_sel, openai_api_key)
        st.session_state['docName'] =  vector_sel

        with st.chat_message("assistant"):
            chain = st.session_state.conversation

            with st.spinner("Thinking..."):
                result = chain({"question": query})
                with get_openai_callback() as cb:
                    st.session_state.chat_history = result['chat_history']
                response = result['answer']
                source_documents = result['source_documents']

                st.markdown(response)
                with st.expander("참고 문서 확인"):
                    for i in range(len(source_documents)):
                        # print('==> ', source_documents[i])
                        if 'source' in source_documents[i].metadata:
                            st.markdown(source_documents[i].metadata['source'], help = source_documents[i].page_content)
                        # html 헤더 텍스트로 split한 경우 메타정보를 Header로 생성하였음 <= get_text()에서 처리함
                        if 'Header 1' in source_documents[i].metadata:
                            src = []
                            for key, val in source_documents[i].metadata.items():
                                if key == 'Header 1' or key == 'Header 2':  # 제목(header1) 과 탭명(header2)을 표시 
                                    src = src + ' > ' + val if src else val
                            st.markdown(src, help = source_documents[i].page_content)
                                       
# Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


def upload_process(openai_api_key,uploaded_files,kms_vector, cntnt_id = None, ctgr_path=None):    
    if not openai_api_key:
        openai_api_key = OPENAI_API_KEY
        # st.info("Please add your OpenAI API key to continue.")
        # st.stop()
        
    # if st.session_state.conversation:
    #     print('vertor store established!!!')
    #     st.sidebar.write("Vector Store Already Created")
        
    if openai_api_key:
        if not isinstance(uploaded_files,list):  # faiss_v.get_tex에서 리스트객체를 받으므로 single upload이면 list로 바꿈
            uploaded_files = [uploaded_files]

        files_text,files_type  = faiss_v.get_text(uploaded_files)
        if not files_text:
            st.info("Please add your File to continue.")
            st.stop()
        
        text_chunks= faiss_v.get_text_chunks(files_text, files_type)
        if cntnt_id:
            if ctgr_path: 
                idx_name = 'KMS_' + ctgr_path
            else:
                idx_name = 'KMS_ALL'
        elif kms_vector:
            idx_name = 'KMS통합임베딩'
        else:
            # 벡터 이력은 첫번째 파일로 생성=>업로드를 single로 하는것으로 가정함
            idx_name = uploaded_files[0].name.replace('docs/','')
            # 벡터화된 목록 보관 -화면 용
        idx = faiss_v.save_vector_info(idx_name)

        if cntnt_id:
            db.save_embed_history(cntnt_id,idx_name,idx)
        # 동일 이름의 벡터db삭제
        elif kms_vector:
            pass
        elif faiss_v.delete_vector_db('new_index', idx):
            print('delete succ')
        else:
            print('no data')

        # 벡터db 생성    
        vetorestore, new_vetorestore = faiss_v.get_vectorstore_by_name(text_chunks, idx)
 
        # st.session_state.conversation = faiss_v.get_conversation_chain(vetorestore,openai_api_key) 
        st.session_state.processComplete = True

        if not uploaded_files[0].name in st.session_state.vectorList:
            st.session_state.vectorList.append(idx_name)
        
        st.session_state.docName = None # 채팅 query를 위해 초기화해줌

def reset_vector():   
    st.session_state.conversation = None

def get_vector_chain(docName, openai_api_key):
    print('>>> get : ',docName)

    st.session_state.conversation = faiss_v.get_vectorstore_by_docname(docName, openai_api_key)
    print(st.session_state.conversation)


def get_kms_contents(content_id):
    ''' content_id로 kms의 컨텐츠 내용을 조회 '''
    sql = f""" SELECT k01.cntnt_id AS cntnt_id 
         , k01.titl AS titl_nm
         , k13.cntnt_nm AS tab_nm
         , k24.sub_cntnt_nm AS sub_nm
         , k24.contn AS contn
    FROM   tbctkk01 k01
         , tbctkk13 k13
         , tbctkk24 k24
    where k01.cntnt_id = {content_id}
      AND k01.cntnt_id = k13.cntnt_id
      AND k13.cntnt_id = k24.CNTNT_ID 
      AND k13.cntnt_no = k24.CNTNT_NO 
      AND k01.use_yn = 'Y'
      AND k13.use_yn = 'Y'
      AND k24.use_yn = 'Y'
    ORDER BY k13.sort_ord, k24.sort_ord """
    
    try:
        connection = db.get_conn_ora()
     
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            cols = [x[0].lower() for x in cursor.description]
   
        df = pd.DataFrame(rows, columns = cols)
        for c in df.columns:
            if df[c].dtype == object:
               df[c] = df[c].astype("string")

        connection.close()

    except Exception as ex:
        err, = ex.args
        print('error code :', err.code)
        print('error message :', err.message)
        return False
   
    if len(df) ==0:
        print('No data found')  
        st.sidebar.warning('No data found', icon="⚠️")
        return False
    
    return df

def query_process(openai_api_key,content_id,kms_vector):
    ''' content_id로 임베딩 및 이력 기록 '''
    df = get_kms_contents(content_id)
    
    f_name = ''.join(df.cntnt_id[0]) + '.html' #파일명 = 컨텐츠id
      
    html_doc = htm.make_html(df)

    with open(f'docs/{f_name}','w', encoding='utf-8') as f:
        f.write(html_doc)

    print('file read............................',f_name)
 
    with open(f'docs/{f_name}','r', encoding='utf-8') as f:
        upload_process(openai_api_key,f,kms_vector)
    
    return True

if __name__ == '__main__':
    run()