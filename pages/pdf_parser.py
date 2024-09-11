import time
import pandas as pd
import streamlit as st

def parsing_pdfminer():
    import tempfile,os
    #방식2. markdown
    import base64
    
    # uploaded_files =  st.file_uploader("select file",type=['pdf','docx','html'],accept_multiple_files=False, label_visibility="collapsed")
    # if uploaded_files is not None:
    #     print('---', uploaded_files.name)
    #     temp_dir = tempfile.mkdtemp()
    #     doc_nm = os.path.join(temp_dir, uploaded_files.name)
    #     with open(doc_nm, "wb") as f:
    #         f.write(uploaded_files.getvalue())
    #     with open(doc_nm, "rb") as f:
    #         base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    #     displ(base64_pdf)
    file = "docs/여비규정.pdf"
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
    col1, col2 = st.columns(spec=[1, 1], gap="small")
    with col1:
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf">'
        # Displaying File
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
        for page in extract_pages(file):
            cnts = ''
            line_cnt = 0
            for i,element in enumerate(page):
                if isinstance(element, LTTextContainer):
                    text = element.get_text()
                    if text:
                        line_cnt += 1
                        cnts += text.replace('  ',' ')  #한글2byte공백으로 인식하여 1 byte로 강제변환함
            st.text_area('lbl',cnts,height=line_cnt*10, label_visibility='collapsed')



#--------- editor -------------------html편집기능은 없음... html=True는 입력내용을 html로 리턴할건지 지정하는 옵션임
    from streamlit_quill import st_quill
    ccc = '화면을 바로w 열려면 <a href="QA_chat" target="_self"> Click :white_check_mark:</a> 하세요'
    ccc = f''' <tr>
  <td>Hi, I'm your first cell.</td>
  <td>I'm your second cell.</td>
  <td>I'm your third cell.</td>
  <td>I'm your fourth cell.</td>
 </tr>'''
    content = st_quill(ccc, html=True, readonly=False)
    st.write(content)

def parsing_html():    
    # st.write("check out this [link](https://share.streamlit.io/mesmith027/streamlit_webapps/main/MC_pi/streamlit_app.py)")
    st.write("check out this [link](http://localhost:8501/pagest/Main.py)")

    import streamlit_extras
    from streamlit_extras.switch_page_button import switch_page 
    want_to_contribute = st.button("I want to contribute!")
    if want_to_contribute:
        switch_page("test")

    f_name = 'out-doctype제거.html'
    with open(f'docs/{f_name}','r', encoding='utf-8') as f:
        data = f.readlines()
        data2 = ''.join(data)
        # md = st.markdown(data, unsafe_allow_html=True)
        # print(md)
        print('html2------------\n', data2)
        components.html(data2, width=1024, height=2000, scrolling=True)

def pdf_viewer():
    from streamlit_pdf_viewer import pdf_viewer
    # print('pdf view')
    # pdf_viewer("docs/여비규정.pdf")
               
def app():
    parsing_pdfminer()

if __name__ == '__main__':
    app()