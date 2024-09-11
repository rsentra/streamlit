import tiktoken
from loguru import logger
import os

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PyMuPDFLoader
# from langchain.document_loaders import Docx2txtLoader
# from langchain.document_loaders import UnstructuredPowerPointLoader
from langchain.document_loaders import UnstructuredHTMLLoader
from langchain_community.document_loaders import BSHTMLLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import HTMLHeaderTextSplitter

from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS

# from streamlit_chat import message
from langchain.callbacks import get_openai_callback
from langchain.memory import StreamlitChatMessageHistory
    # 참고소스
    # https://github.com/insightbuilder/python_de_learners_data/blob/main/code_script_notebooks/projects/LLM_practical_appln/multiFileEmbedFaiss.ipynb 

def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return len(tokens)

def get_text(docs):
    """
    This function takes a list of uploaded files and returns a list of text documents.
    The function determines the appropriate loader based on the file extension and loads the file.
    If the file extension is not supported, the function raises an exception.

    Args:
        docs (list): A list of uploaded files.

    Returns:
        list: A list of text documents and document type

    Raises:
        ValueError: If the file extension is not supported.
    """
    headers_to_split_on = [  # 분할할 HTML 헤더 태그와 해당 헤더의 이름을 지정합니다.
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
            ("h4", "Header 4"),
        ]
    doc_list = []
    
    for doc in docs:
        file_type = ''
        if 'docs/' in doc.name:
            file_name = doc.name
        else:
            file_name = 'docs/' + doc.name  # doc 객체의 이름을 파일 이름으로 사용

        with open(file_name, "rb") as file:  # 파일을 doc.name으로 저장
#             file.write(doc.getvalue())
            logger.info(f"Uploaded {file_name}")
        if '.pdf' in doc.name:
            # loader = PyPDFLoader(file_name)
            loader = PyMuPDFLoader(file_name)
            documents = loader.load_and_split()
        elif '.docx' in doc.name:
            loader = Docx2txtLoader(file_name)
            documents = loader.load_and_split()
        elif '.pptx' in doc.name:
            loader = UnstructuredPowerPointLoader(file_name)
            documents = loader.load_and_split()
        elif '.html' in doc.name:
            # unicode_html = file.read().decode('utf-8', 'ignore')
            # loader = UnstructuredHTMLLoader(file_name,mode='elements')
            #--case 1: 업로더
            loader = BSHTMLLoader(file_name,'utf-8')
            documents = loader.load_and_split()
            #--case 2: html 헤더 텍스트 분할방법
            # file_type = 'html'
            # html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            # documents = html_splitter.split_text_from_file(file_name)
            #---참고-- SBI저축은행 컨텐츠로 테스트해보면 두 방법간의 차이는 별로 없어 보임
        doc_list.extend(documents)
    return doc_list, file_type


def get_text_chunks(text, types):
    """
    This function takes a string of text and returns a list of text chunks.
    The function uses a text splitter that splits the text into chunks based on
    the length of the chunks and the overlap between chunks.

    Args:
        text (str): A string of text.
        types (str): type of text

    Returns:
        List[str]: A list of text chunks.

    """        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=100,
        length_function=tiktoken_len
    )
    chunks = text_splitter.split_documents(text)
    return chunks


def get_vectorstore(text_chunks):
    """
    This function takes a list of text chunks and returns a FAISS vector store.

    Args:
        text_chunks (List[str]): A list of text chunks.

    Returns:
        FAISS: A FAISS vector store.

    """
    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )  
#     vectordb = FAISS.from_documents(text_chunks, embeddings)
    vectordb, append_db= embed_index(doc_list=text_chunks,
               embed_fn= embeddings,
               index_store='new_index')
    # print(vectordb)
    return vectordb, append_db

def get_vectorstore_by_name(text_chunks,index_name):
    ''' func: vector store를 업로드 파일마다 생성 
        args: text_chunks, index name 
        return: exsisting vector, new_vector '''
    """
    This function takes a list of text chunks and an index name and returns an existing vector store 
          and a new vector store.

    Args:
        text_chunks (List[str]): A list of text chunks.
        index_name (str): The name of the index.

    Returns:
        Tuple[FAISS, bool]: A tuple containing an existing vector store and a boolean indicating whether a new vector store was created.

    """
    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )  
#     vectordb = FAISS.from_documents(text_chunks, embeddings)
    vectordb, append_db = embed_index(doc_list=text_chunks,
               embed_fn = embeddings,
               index_store = 'new_index',
               index_nm = index_name)
    # print(vectordb)
    return vectordb, append_db


def embed_index(doc_list, embed_fn, index_store, index_nm=None):
    ''' Function takes in existing vector_store
    new doc_list and embedding function that is 
    initialized on appropriate model. Local or online. 
    New embedding is merged with the existing index. If no 
    index given a new one is created '''
  #check whether the doc_list is documents, or text
    
    try:
        faiss_db = FAISS.from_documents(doc_list, 
                              embed_fn)  
    except Exception as e:
        faiss_db = FAISS.from_texts(doc_list, 
                              embed_fn)
  
#     if os.path.exists(index_store):
    if os.path.isfile(f"{index_store}/{index_nm}.faiss"):
        if index_nm:
            local_db = FAISS.load_local(index_store,embed_fn,index_nm)
        #merging the new embedding with the existing index store
            local_db.merge_from(faiss_db)
            local_db.save_local(index_store,index_nm)
        else:
            local_db = FAISS.load_local(index_store,embed_fn)
        #merging the new embedding with the existing index store
            local_db.merge_from(faiss_db)
            local_db.save_local(index_store)
        print("Updated index saved")
        return local_db, faiss_db
    else:
        if index_nm:
            faiss_db.save_local(folder_path=index_store,index_name = index_nm)
        else: 
            faiss_db.save_local(folder_path=index_store)
        print("New store created...")
        return faiss_db, faiss_db

    
def get_conversation_chain(vetorestore,openai_api_key):
    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-3.5-turbo',temperature=0)
#     retriever = vetorestore.as_retriever(search_type = 'mmr', vervose = True, search_kwargs={"k": 3})
    retriever = vetorestore.as_retriever(search_type = 'mmr', vervose = True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever, 
            memory=ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer'),
            get_chat_history=lambda h: h,
            return_source_documents=True,
            verbose = True
        )

    return conversation_chain

def get_docstoreId_by_idName(v_store, id_name):
    '''index 값으로 docstore_id 찾기  '''
    matching_keys = [key for key, value in v_store.index_to_docstore_id.items() if value == id_name]
    return matching_keys[0] if matching_keys else None

def delete_docstore_by_idName(v_store, id_name):
    '''index 값으로 docstore 삭제  '''
    del_id = get_docstoreId_by_idName(v_store, id_name)
    if id:
        del v_store.index_to_docstore_id[del_id]

def save_vector_info(doc_name):
    '''vector index파일정보를 갱신'''
    max_val  = 100
    if os.path.isfile(f"index_info.txt"):
        with open('index_info.txt','r') as f:
            temp =  f.read()
            dic = eval(temp)  # string to dictionary
        max_key = max(dic, key = dic.get) # max value를 가진 key를 추출
        max_val = dic.get(doc_name,dic.get(max_key) + 1) # 기존 문서이면 value유지, 아니면 value증가
        dic[doc_name] = max_val
    else:
        dic = dict({doc_name:max_val})
    
    with open('index_info.txt','w') as f:
        # print(dic)
        dic[doc_name] = max_val
        f.write(str(dic))
        # print('af:', dic)
    return max_val

def delete_vector_db(index_store,index_nm):
    ''' 동일한 이름의 벡터파일을 지움 '''
    if os.path.isfile(f"{index_store}/{index_nm}.faiss"):
        os.remove(f"{index_store}/{index_nm}.faiss")
        os.remove(f"{index_store}/{index_nm}.pkl")
        return True
    else:
        return False

def get_vectored_files():
    ''' vectorised file name search 
        args: None
        return: 문서명 -> str '''
    with open('index_info.txt','r') as f:
        dic = f.read()
        return list(eval(dic).keys())

def get_vectorstore_by_docname(doc_name, llm_api_key=None):
    ''' func: 문서파일명으로 벡터 db를 로딩
        args: 문서명, api_key 
        retrun: api_key가 있으면 chain, 없으면 vector_db '''
    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        ) 
       
    # index파일을 읽음
    with open('index_info.txt','r') as f:
        temp = f.read()
        dic = eval(temp)

    # string으로 오면 list로 변환함
    if not isinstance(doc_name,list):
        doc_name = [doc_name]

    local_db = None

   # doc명으로 index파일명을 찾아서 vector db를 읽고 합침
    for doc in doc_name:
        index_nm = dic.get(doc)
        index_store = 'new_index'
        faiss_db = FAISS.load_local(index_store,embeddings,index_nm)
        if local_db:
            local_db.merge_from(faiss_db)
        else:
            local_db = faiss_db

    # api_key가 있으면 chain을 return, 없으면 vector db를 return
    if llm_api_key:
        return get_conversation_chain(local_db,llm_api_key)
    else:
        return local_db