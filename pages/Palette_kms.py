import streamlit as st
import requests 

def show_history():
    print('----- show history ==;; ', len(st.session_state['chat']))
    if bool(st.session_state['chat']):
       for i, chat in enumerate(st.session_state['chat']):
           query = chat.get('query')
           answer = chat.get('answer')
           rel_documents = chat.get('rel_docs')
           with st.expander(f'{i}_history'):
               show_message(query,answer,rel_documents)

def show_message(query=None,answer=None,rel_documents=None):
    if query:
        st.markdown(query)

    with st.chat_message('ai'):
        st.markdown(answer)

    for rel in rel_documents:
            # print(rel.get('doc'))
        cntnt_id = rel.get('metadata').get('primary_key').split('>')[0]
        section = rel.get('metadata').get('section')
        para = rel.get('metadata').get('paragraph')
        rel_doc = f'{cntnt_id} : {section} >  {para}'
         # print(rel_doc)
        k_url = 'https://nkms.hkpalette.com/webapps/kk/kn/KkKn003.jsp?TYPE=KN&CNTNT_ID='
        k_url = f'{k_url}{cntnt_id}&MENU_ID='
        with st.chat_message('ai'):
            st.markdown(f'- [{rel_doc}]({k_url})')
    
def app():
    if "chat" not in st.session_state:
        st.session_state.chat = []

    cols = st.columns([4,1])
    with cols[0]:
        code = st.selectbox('Choose category', options=('CW','test'), placeholder="Choose a Category", index=None, label_visibility="collapsed")
    with cols[1]:
        chk = st.checkbox("clear history")  
        if chk:
            st.session_state.chat = []

    query  = st.chat_input('text input...')
    if  query:
        url = f'http://hkcloudai.com:8018/api/v1_1/retrieve/retrieve/retrieval_non_streaming?code={code}&query={query}'
        with st.spinner('Wait for it...'):
            res = requests.get(url)
            print('res cd1::', res.status_code,query)
            answer = ''
            rel_documents = ''
            k_url = ''
            if res.status_code == 200:
                show_history()
                res_str = res.json()  ## dictionary로 넣어줄 필요가 있음
                # print(res_str)
                answer = res_str['llm_response'][0]
                rel_documents = res_str.get('retrieval_docs')

                show_message(query, answer, rel_documents)

                # with st.chat_message('user'):
                #     st.markdown(answer)
   
                # for rel in rel_documents:
                #     print(rel.get('doc'))
                #     cntnt_id = rel.get('metadata').get('primary_key').split('>')[0]
                #     section = rel.get('metadata').get('section')
                #     para = rel.get('metadata').get('paragraph')
                #     rel_doc = f'{cntnt_id} : {section} >  {para}'
                #     # print(rel_doc)
                #     k_url = 'https://nkms.hkpalette.com/webapps/kk/kn/KkKn003.jsp?TYPE=KN&CNTNT_ID='
                #     k_url = f'{k_url}{cntnt_id}&MENU_ID='
                #     with st.chat_message('user'):
                #         st.markdown(f'- [{rel_doc}]({k_url})')
            else:
                st.error('Error occurred while processing your request=>',res.status_code)

            st.session_state['chat'].append({'query':query,'answer':answer,'rel_docs':rel_documents})

if __name__ == '__main__':
    app()