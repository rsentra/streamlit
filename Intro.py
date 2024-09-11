import time
import pandas as pd
import numpy as np
import streamlit as st
import cx_Oracle

def tab1_func():
    print('tab1')
    st.write('### Hello My Pages')
    st.markdown(
        '''
        이 홈페이지는 여러가지 기능을 테스트하기 위한  인트로 페이지입니다.
        git 주소는 [클릭](https://github.com/rsentra) 하세요
        
        - ##### The First Function is  ...
        - ##### The Second Function is  ...
        '''
    )
    st.image('../gpt/data/sunrise.png', caption='Sunrise by the mountains',width=100,use_column_width='never')
    st.markdown('#### :red[Emoji name] [Click here!!!](https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/)',)

    cola, colb  = st.columns(2)
    with cola:
        st.markdown(
            '''
             QA_chat 화면을 :red[새창]으로 열려면 [클릭](QA_chat) 하세요
            '''
        )
    with colb:
        st.markdown(':red[QA Chat] 화면을 바로 열려면 <a href="/QA_chat" target="_self"> Click :white_check_mark:</a> 하세요', unsafe_allow_html=True)

    col1, col2, col3  = st.columns(3)
    check, res = False, False
    with col1:
        st.title("column1 area")
        sel_names = ['CheckBox','Radio']
        selected = st.radio('Select', sel_names)
        st.write("** select returns : **", selected)
        if selected == 'CheckBox':
            st.subheader("Welcome to the Checkbox")
            st.write("Nice to see you :wave:")
            check = st.checkbox("Click Here")
            st.write('state of checkbox: ', check)
        if check:
            st.write(':smile:'*12)
        else:
            st.subheader("welcome to button")
            st.write(':thumbsup:')
            res = st.button('Click Here')
            st.write('state of checkbox: ', res)
        if res:
            st.write(':smile:')
        st.success('This is a success message!', icon="✅")

    with col2:
        st.title("column2 area")
        

        option = st.selectbox(
        "How would you like to be contacted?",
        ("Email", "Home phone", "Mobile phone"),
        index=None,
        placeholder="Select contact method...",
        )
        st.write('You selected:', option)

        options = st.multiselect(
        'What are your favorite colors',
            ['Green', 'Yellow', 'Red', 'Blue'],
            ['Yellow', 'Red'],
            help = '선택을 위한 help'
        )
        for i in options:
            st.write('You selected:', i)

        with st.spinner('Wait for it...'):
            time.sleep(0.5)
        # st.balloons()
        # st.snow()
        txt  = st.text_area('text area...')

    with st.container():
        with col3:
            st.title("column3 area")
            # Initialization
            if 'key' not in st.session_state:
                st.session_state['key'] = 'value'
        
            # Session State also supports attribute based syntax
            if 'key' not in st.session_state:
                st.session_state.key = 'value'
            st.write('Session key: ', st.session_state.key)
            st.session_state.key = 'updated session value'
            st.write('Session key after update: ', st.session_state.key)

            col11,col12 = st.columns([1,2])
            col11.write('Sum:')

            with st.form('addition'):
                txt  = st.text_input('text input...')

                a = st.number_input('a')
                b = st.number_input('b')
                submit = st.form_submit_button('add')

                if submit:
                    col12.write(f'{a+b:.2f}')


def tab2_func():
    print('tab2')
    st.info("tab은 페이지가 로드될때 모두 refresh됩니다")
    name  = st.text_input('name input...')
    if not name:
       st.warning('Please input a name.')
    #    st.stop()
    st.success('name inputed.')

    if "value" not in st.session_state:
        st.session_state.value = "Title"

    ##### Option using st.rerun #####
    st.header(st.session_state.value)

    if st.button("Foo"):
        st.session_state.value = "Foo"
        st.rerun()

    st.write(st.session_state.value)
    st.metric(label="Temperature", value="70 °F", delta="1.2 °F")

    st.markdown("이미 존재하는 widget을 업데이트하는 방법은 empty()를 이용한다")
    placeholder2 = st.empty()
    placeholder3 = st.empty()

    mySecondCheckbox = placeholder2.checkbox("Original Text 2")
    myThirdInput = placeholder3.text_input("Original Text 3")

    update_w = st.checkbox('update widget')

    if update_w:
        mySecondCheckbox = placeholder2.checkbox("Next Text 2")
        myThirdInput = placeholder3.text_input(label="Original Text 3", value="변경된 값")
   
def tab3_func():
    print('tab3')
    df1 = pd.DataFrame(np.random.randn(50, 20), columns=("col %d" % i for i in range(20)))
    
    # st.title('DataFrame')
    # st.dataframe(df1)  # Same as st.write(df)
    
    st.title('DataFrame Editor')
    edited_df = st.data_editor(df1)

    # max_val = edited_df.loc[edited_df["col 3"].idxmax()]["col 1"]
    # st.markdown(f"Your col 1 value of max col 3 value  is **{max_val}** 🎈")

    # st.title('DataFrame Chart')
    # my_table = st.table(df1)
    df2 = pd.DataFrame(np.random.randn(1, 20), columns=("col %d" % i for i in range(20)))
    # my_table.add_rows(df2)
    my_chart = st.line_chart(df1.iloc[:10,:3])
    my_chart.add_rows(df2.iloc[:,:3])

    # df3 = get_st_db()
    df3 = get_db()
    
    # Print results.
    # for row in df.itertuples():
    #     st.write(f"{row.unity_blbd_id} has a :{row.unity_blbd_nm}:")
    st.title('from kms')
    st.dataframe(df3)  # Same as st.write(df)

def tab4_func(): 
    pass

def get_st_db():
    ''' st.connection이용 '''
    # 오라클 클라이언트를 선언: windows 환경변수에 path를 잡으면 필요없음
    try:
        cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_12")
    except Exception as e:
        pass

   # Initialize connection.
   # st.connection은 .streamlit/secrets.toml 파일을 참조함
    conn = st.connection("oracle", type="sql")

    # Perform query.
    df = conn.query('SELECT * FROM DPKMAPP.TBCTKB01')
    return df

def get_db():
    ''' cx_oracle패키지 이용 '''
    username = 'DPKMAPP'
    password = 'Kms12#$'
    dsn = '61.106.19.217:33389/CDB1'
    encoding = 'UTF-8'
    # 오라클 클라이언트를 선언: windows 환경변수에 path를 잡으면 필요없음
    try:
        cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_12")
    except Exception as e:
        pass

    try:
        connection = cx_Oracle.connect(username, password, dsn, encoding=encoding)
    except Exception as ex:
        print('Could not connect to database:', ex)

    print("SUCCESS: Connecting database succeeded")

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM DPKMAPP.TBCTKB01"
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [x[0].lower() for x in cursor.description]
    except Exception as ex:
        print('Could not fetch data:', ex)
   
    df = pd.DataFrame(rows)
    df.columns = columns
    connection.close()
    return df

# 페이지 로딩될때 각 탭이 모두 실행됨
def app():
    tab1, tab2, tab3, tab4 = st.tabs(["Cat", "Dog", "Owl",'tiger'])
    with tab1:
        tab1_func()

    with tab2:
        tab2_func()

    with tab3:
        tab3_func()

    with tab4:
        tab4_func()

        # st.page_link(page="pages/KMS_embed", label="Home", icon="🏠")  => 오류
        # https://your_app.streamlit.app/?first_key=1&second_key=two&third_key=true
       
        #1. 새로운 창으로 정상작동(pages폴더안에 있어야 인식함) ->
        # st.link_button("Go to gallery", "http://192.168.0.187:8501/test") 
       
        #2. 현재 창에서 페이지 스위칭 정상작동함
        # from streamlit_extras.switch_page_button import switch_page
        # chk = st.button("I want to change!")
        # if chk:
        #     switch_page("KMS_embed")   

if __name__ == '__main__':
    app()
    