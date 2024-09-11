import sys, os

# sys.path.append('../gpt/libs')

import streamlit as st
import tiktoken
from loguru import logger

# from langchain.chains import ConversationalRetrievalChain
# from langchain.chat_models import ChatOpenAI

# from langchain.document_loaders import PyPDFLoader
# from langchain.document_loaders import Docx2txtLoader
# from langchain.document_loaders import UnstructuredPowerPointLoader
# from langchain.document_loaders import UnstructuredHTMLLoader

# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings import HuggingFaceEmbeddings

# from langchain.memory import ConversationBufferMemory
# from langchain.vectorstores import FAISS

# # from streamlit_chat import message
# from langchain.callbacks import get_openai_callback
# from langchain.memory import StreamlitChatMessageHistory

import libs.faiss_vector as faiss_v   #user defined function
import models.database as db
import models.html as htm
import pandas as pd
from pages import QA_chat as qa_chat
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

OPENAI_API_KEY = st.secrets["opai_api_key"]['api_key']

def app():
    ''' main function'''
    tab1, tab2, tab3 = st.tabs([" 🗄️ Contents List", " 🗂️ Embedding History", " 💹 Dashboard"])

    if "contents_df" not in st.session_state:
        st.session_state.contents_df = None
    if "min_dt" not in st.session_state:
        st.session_state.min_dt = None
    if "max_dt" not in st.session_state:
        st.session_state.max_dt = None
    
    #----------------------------------------------------------------#
    # tab1 #
    #----------------------------------------------------------------#
    with tab1:
        # st.markdown('### KMS contents Retrieval ###')
        sql = f""" SELECT k10.cd_nm
                    FROM tbctkc10 k10
                    where k10.group_cd ='SAVE_STAT_CD'
                    and use_yn = 'Y' and cd <> '****'
                """
        if (df := db.get_kms_datadf(sql)) is None:
            st.sidebar.warning('No data found', icon="⚠️")
            st.stop()
        
        sql = f""" SELECT min(his_dt) min_dt, max(his_dt) max_dt
                    FROM tbctkk04 
                """
        if (df_date := db.get_kms_datadf(sql)) is None:
            st.sidebar.warning('No data found', icon="⚠️")
            st.stop()

        min_dt, max_dt = df_date['min_dt'][0], df_date['max_dt'][0]
        min_dt, max_dt = datetime.strptime(min_dt, '%Y%m%d'), datetime.strptime(max_dt, '%Y%m%d')
        min_dt = datetime( year=min_dt.year, month=min_dt.month,day=min_dt.day,hour=0,minute=0,second=0)
        max_dt = datetime( year=max_dt.year, month=max_dt.month,day=max_dt.day,hour=23,minute=59,second=59)
        
        code_df = db.get_common_code('CTGR_USE_CD')
        code_dict = dict(zip(code_df['cd_nm'],code_df['cd']))

        cols = st.columns((5,1))
        with cols[0]:
            col1, col2,col3,col4,col5 = st.columns(5)
            with col1:
                ctgr_nm = st.selectbox('Choose category', list(code_dict.keys()), 
                                        placeholder="Choose a Category", index=None, label_visibility="collapsed")
            with col2:
                option_nm = st.selectbox('Choose contents status', ['전체'] + list(df['cd_nm'].unique()), 
                                        placeholder="Choose a Status", index=None, label_visibility="collapsed", key="option_ctgr")
            with col3:
                include_embded = st.checkbox(':blue[임베딩건 포함]', value=False)
            with col4:
                min_dt = st.date_input('시작일',value = min_dt.date(), label_visibility="collapsed")
                st.session_state['min_dt'] = datetime(year=min_dt.year, month=min_dt.month,day=min_dt.day,hour=0,minute=0,second=0)
            with col5:
                max_dt = st.date_input('종료일',value = max_dt.date(), label_visibility="collapsed")
                st.session_state['max_dt'] = datetime(year=max_dt.year, month=max_dt.month,day=max_dt.day,hour=23,minute=59,second=59)

        with cols[1]:
             opt = st.button('검색', type="primary")

        ctgr_cd = code_dict.get(ctgr_nm,"CA") #전체 =  CA
        # print('ctgr_cd = ',ctgr_cd)
   
        if opt:
            print('submit-----------')
            db.get_kms_datadf.clear()
            df = get_contents_list(ctgr_cd, include_embded)
            display_list(df, include_embded, "전체")
        elif ctgr_nm:  # select box change
            print(' category change-----------')
            df = get_contents_list(ctgr_cd, include_embded, option_nm)
            display_list(df, include_embded, option_nm)
        elif option_nm:  # select box change
            print(' category change2-----------')
            df = get_contents_list(ctgr_cd, include_embded, option_nm)
            display_list(df, include_embded, option_nm)
        elif st.session_state.contents_df is not None:   # column select click
                print(' select change-----------')
                display_list(st.session_state.contents_df, include_embded, option_nm if option_nm else '전체')
                
    #----------------------------------------------------------------#
    # tab2 #
    #----------------------------------------------------------------#
    with tab2:
        st.markdown('### :orange[KMS] :rainbow[embedding history] ###')
      
        sql = f""" SELECT k01.cntnt_id as 컨텐츠번호
            ,k01.titl as 컨텐츠명
            ,k10.cd_nm as 상태
            ,k01.upd_dttm as 컨텐츠수정일
            ,g10.vtr_nm as 벡터명
            ,g10.vtr_id as 벡터ID
            ,g10.it_processing as 임베딩일자
        FROM tbctkk01 k01
        inner JOIN tbcgpt10 g10
            on k01.cntnt_id= g10.cntnt_id
        inner JOIN tbctkc10 k10
            on k10.group_cd ='SAVE_STAT_CD'
               and k01.save_stat_cd = k10.cd
        where k01.use_yn = 'Y'"""
        
        col_left, col_right = st.columns([2,1])
        
        cache_clear = col_left.checkbox("Refresh")
        if cache_clear:
            db.get_kms_datadf.clear()

        if (df := db.get_kms_datadf(sql)) is None:
            st.warning('No data found', icon="⚠️")
        else:
            col_right.write(f'Total : {len(df)} 건')
            disp_df(df)

    #----------------------------------------------------------------#
    # tab3 #
    #----------------------------------------------------------------#
    with tab3:
        dashboard()

def dashboard():

    plt.rc('font', family='Malgun Gothic') 

    # st.write(" 컨텐츠 상태별")
    if "contents_df"  in st.session_state:
        df = st.session_state['contents_df']
    if df is None:
        print("---- retry for query --------")
        df = get_contents_list("CA", include_embded=True)
    elif st.session_state.option_ctgr != "전체":  #대시보드 이므로 전체가 필요함
        df = get_contents_list("CA", include_embded=True)

    col1, col2 = st.columns(2)
    if 'site' not in df.columns:
        df['site']   = df['ctgr_path'].apply(lambda x: x.split('>')[1])
        df['reg_dt'] = df['reg_dttm'].apply(lambda x: x.date())
         
    with col1:
        st.subheader('Embedding 현황')
        opt = st.multiselect("Embedding Count By Site", df['site'].unique(),default=None, placeholder="Choose a Site"
                             ,label_visibility="collapsed")
        df['emb_c'] = [ 1 if x > 0 else 0  for x in df['emb_cnt'] ]
        
        if opt:
           df1 = df[df['site'].isin(opt)]
        else:
           df1 = df

        # bar chart
        c_mode = 'px'
        bar_chart(df1, c_mode, 'emb')
            
    with col2:
        st.subheader('Contents 보유현황')
        opt = st.selectbox("Contents Count By Site", df['site'].unique(),index=None, placeholder="Choose a Site",label_visibility="collapsed")
        if opt:
            df11 = df[df['site']==opt]
        else:
            df11 = df
        
        # 상태별 파이차트
        if opt:
            df11['cnt'] = 1
            # st.write(opt, ':컨텐츠상태별')
            fig = px.pie(df11, values = 'cnt', names = "cd_nm", template = "gridon",
                         hole = 0.5,height=400, width = 500)
            fig.update_traces(text = df11["cd_nm"], textposition = "outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            c_mode = 'px'
            bar_chart(df11, c_mode, 'status')
       
    with st.expander(':rainbow[View data of contents status] :sunglasses: '):
       df2 = df.groupby(['site','cd_nm']).agg({'cntnt_id':'count','emb_c':'sum'}).reset_index()
       df2['%'] = round(df2['emb_c'] * 100 / df2['cntnt_id'],0).map('{:.1f}%'.format)

       df2.rename(columns={'cntnt_id':'cntnt_cnt'},inplace=True)
       disp_df(df2)

    chk1 = st.checkbox('최근 등록/조회건수 보기 :memo: ')
    if chk1:
        df = st.session_state['contents_df']
        df_a = df[df['cd_nm']!='삭제'].groupby(['reg_dt'])[['cntnt_id']].count().rename(columns={'cntnt_id':'reg_cnt'}).sort_index(ascending=False)
        
        show_cnt = 30
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df_a.index[:show_cnt], y=df_a['reg_cnt'][:show_cnt], name="등록건수",
                       mode="lines+markers+text",text=df_a['reg_cnt'][:show_cnt]),
            row=1, col=1, secondary_y=False, 
        )
        fig.update_xaxes(title_text=None, tickangle=-60, tickfont_family='Rockwell',
                         tickfont_color='green', tickfont_size=12, tickformat = '%y.%m.%d',ticklen=10)
        fig.update_yaxes(title_text="등록건수")
        fig.update_yaxes(title_text="조회건수",secondary_y=True)
        fig.update_layout({
            'plot_bgcolor':  'Azure',
            'paper_bgcolor': 'Ivory',
        })
 
        df_inq = get_inquiry_cnt()
        df_inq['req_dt'] = df_inq['reg_dttm'].dt.date
        df_inq = df_inq.groupby(['req_dt'])[['inq_cnt']].sum().sort_index(ascending=False)
        fig.add_trace(
            go.Scatter(x=df_inq.index[:show_cnt], y=df_inq['inq_cnt'][:show_cnt], name="조회건수",
                       mode="lines+markers+text", text=df_inq['inq_cnt'][:show_cnt]),
            row=1, col=1, secondary_y=True,
        )
        fig.update_traces(textposition='top center')

        st.plotly_chart(fig, use_container_width=True, height = 200)

        with st.expander('View data'):
            dd = df_a.merge(df_inq, how='outer', left_index=True, right_index=True).fillna(0).sort_index(ascending=False).astype(int)
            disp_df(dd, False)
            # disp_df(df_a.reset_index().sort_values(by='reg_dt',ascending=False))

    chk2 = st.checkbox('월별 조회건수 보기:thumbsup: ')
    if chk2:
        # from_dt = st.session_state['min_dt'].date().strftime('%Y%m%d')
        # to_dt = st.session_state['max_dt'].date().strftime('%Y%m%d')
        # df = get_inquiry_cnt(from_dt, to_dt)
        df = get_inquiry_cnt()

        df['ym'] = df['reg_dttm'].dt.strftime("%Y%m")
        df['site'] = df['ctgr_path'].apply(lambda x: x.split('>')[1])
        df_inq = df.groupby(['ym','site'])['inq_cnt'].sum().reset_index()
        ym = sorted(df['ym'].unique(), reverse=True)
        
        sel_ym = st.multiselect("월", ym, default=ym[0], placeholder="년월을 선택~",label_visibility="collapsed")
     
        fig = px.bar(df_inq[df_inq['ym'].isin(sel_ym)], 
                     x="inq_cnt", y="site", color='ym',
                     template = "seaborn", text_auto=True,
                     orientation="h",
                     color_discrete_sequence=px.colors.qualitative.Pastel* len(df_inq))
                    #  color_discrete_sequence=["#0083B8"] * len(df_inq))
                     
        fig.update_yaxes(title_text=None)
        fig.update_xaxes(title_text="조회건수")
        fig.update_layout(legend_title_text= "년월")
        fig.update_layout({
            'plot_bgcolor':  'Azure',
            'paper_bgcolor': 'Ivory',
        })
   
        st.plotly_chart(fig, use_container_width=True, height = 200)
        with st.expander('View data'):
            # disp_df(df_inq.sort_values(by='ym', ascending=False))
            st.write(df_inq.sort_values(by='ym', ascending=False).style.background_gradient(cmap="Oranges"))


def bar_chart(df2, mode, name):
    # plotly 이용방법
    if mode == 'px' and name == 'emb':
       df2['emb_status'] = [ '완료' if x > 0 else '미완료'   for x in df2['emb_cnt']]
       df2 = df2.groupby(by = ["site",'emb_status'], as_index = False).agg({"cntnt_id":'count'})
       y_max = df2['cntnt_id'].max()  + 50
       fig = px.bar(df2, x = "site", y = 'cntnt_id',
                    template = "seaborn", color="emb_status",
                    barmode = 'stack', text_auto=True, color_discrete_sequence=px.colors.qualitative.G10)
       fig.update_xaxes(title_text=None,tickangle=-45, tickfont_family='Rockwell', tickfont_color='green', tickfont_size=12)
       fig.update_yaxes(title_text=None,range=[0,y_max])
       fig.update_layout(legend_title_text=None,
                         legend_orientation="h",
                         legend_yanchor="top",legend_y=0.99,
                         legend_xanchor="left",legend_x=0.01)
       st.plotly_chart(fig,use_container_width=True, height = 200)
    
    if mode == 'px' and name == 'status':
        df2 = df2.groupby(by = ["site",'cd_nm'], as_index = False).agg({"cntnt_id":'count'})
        y_max = df2['cntnt_id'].max()  + 50
        fig = px.bar(df2, x = "site", y = 'cntnt_id' ,
                     template = "seaborn", color="cd_nm", 
                     barmode = 'stack', text_auto=True)
        fig.update_xaxes(title_text=None,tickangle=-45, tickfont_family='Rockwell', tickfont_color='green', tickfont_size=12)
        fig.update_yaxes(title_text=None,range=[0,y_max])
        fig.update_layout(legend_title_text=None,
                         legend_orientation="h",
                         legend_yanchor="top",legend_y=0.99,
                         legend_xanchor="left",legend_x=0.01)
        st.plotly_chart(fig,use_container_width=True, height = 200)

    # pyplot 이용방법
    if mode == 'plt' and name == 'emb':
        df2['emb_status'] = [ '완료' if x > 0 else '미완료'   for x in df2['emb_cnt']]
        df_sum = df2.groupby(['site','emb_status']).agg({'cntnt_id':'count'}).reset_index()
        df_sum.rename(columns={'cntnt_id':'cntnt_cnt'},inplace=True)
        y_max = df_sum['cntnt_cnt'].max()  + 50

        df2 = df_sum.pivot(index='site', columns='emb_status', values='cntnt_cnt').fillna(0)
        df2.reset_index(inplace=True)
        
        width, height = 2, 1
        fig, ax = plt.subplots(figsize=(width, height))
        colors = sns.color_palette('hls',len(df2.columns[1:]))

        ax = df2.plot.bar(x='site', stacked=True, color=colors)
        # ax.set_title('임베딩상태별', fontsize=10)
        ax.set_ylim(0, y_max)
        ax.tick_params(axis='x',direction='out', length=0, labelsize=10, labelcolor='g', labelrotation=70)
        ax.legend(loc='upper left')
        plt.xlabel('',loc=None)
        st.pyplot(ax.figure)

    if mode == 'plt' and name == 'status':
        df2 = df2.groupby(['site','cd_nm'])['cntnt_id'].agg('count').reset_index()
        y_max = df2['cntnt_id'].max()  + 50
        df2 = df2.pivot(index='site', columns='cd_nm', values='cntnt_id').fillna(0)
        df2.reset_index(inplace=True)
        # width = st.sidebar.slider("plot width", 0.1, 25., 3.)
        # height = st.sidebar.slider("plot height", 0.1, 25., 1.)
        width, height = 2, 1
        fig, ax = plt.subplots(figsize=(width, height))

        colors = sns.color_palette('hls',len(df2.columns[1:]))
        ax = df2.plot.bar(x='site', stacked=True, color=colors)
        # ax.set_title('컨텐츠상태별', fontsize=10)
        ax.set_ylim(0,y_max)
        ax.tick_params(axis='x',direction='out', length=0, labelsize=10, labelcolor='g', labelrotation=70)
        ax.legend(loc='upper left')
        plt.xlabel('',loc=None)
        st.pyplot(ax.figure)

def disp_df(edited_df, hide_idx=True):
        disp_df = edited_df.copy()
        DICT_COL = {'cntnt_id':'컨텐츠번호','titl':'컨텐츠명','cd_nm':'상태','ctgr_path':'경로','upd_dttm':'수정일','att_cnt':'첨부',
                    'emb_cnt':'임베딩회수','emb_c':'임베딩건수','ctgr_id':'카테고리번호','cntnt_cnt':'컨텐츠건수','reg_dt':'등록일',
                    'ym':'년월','site':'싸이트','inq_cnt':'조회건수','reg_cnt':'등록건수'}   
        disp_df.columns = [DICT_COL.get(x,x) for x in disp_df.columns]

        st.dataframe(disp_df.style.set_properties(**{'background-color': 'white',
                            'color': 'black',
                            'border-color': 'blue'}),
                    hide_index=hide_idx, width=1000)

def display_modal(html_doc):
    from streamlit_modal import Modal
    import streamlit.components.v1 as components

    modal = Modal("Demo Modal",key='modal', padding=10, max_width=200)
    with modal.container():
        html_string = ''' 
            <h1>HTML string in RED</h1>

            <script language="javascript">
            document.querySelector("h1").style.color = "red";
            </script>
            '''
        components.html(html_string)
        # components.html(html_doc)

def get_contents_list(ctgr_cd, include_embded, option="전체"):
    """
    This function is used to retrieve the contents list based on the specified criteria.

    Args:
        ctgr_cd (str): The category code. If set to "CA", all categories will be retrieved.
        include_embded (bool): A boolean value indicating whether to include the contents that have already been embedded.
        option (str, optional): The contents status to filter the results. Defaults to "전체".

    Returns:
        None

    """

    # temp = f" and k12.ctgr_use_cd =   '{ctgr_cd}'" if ctgr_cd !="CA" else '\n'
    # sql = f""" SELECT k01.cntnt_id
    #         ,k01.titl
    #         ,k10.cd_nm
    #         ,k01.ctgr_id
    #         ,k12.ctgr_path
    #         ,k01.upd_dttm
    #         , (SELECT count(*) FROM tbctkk22 t 
    #             WHERE t.cntnt_id = k01.cntnt_id
    #                 AND t.use_yn = 'Y') AS att_cnt
    #         , (SELECT count(*) FROM tbcgpt10 g 
    #             WHERE g.cntnt_id = k01.cntnt_id ) AS emb_cnt
    #     FROM tbctkk01 k01
    #     inner JOIN tbctkk12 k12
    #         on k01.ctgr_id= k12.ctgr_id
    #            {temp}
    #     inner JOIN tbctkc10 k10
    #         on k10.group_cd ='SAVE_STAT_CD'
    #            and k01.save_stat_cd = k10.cd
    #     where k01.use_yn = 'Y'
    #     ORDER BY k01.cntnt_id desc """
    
    ## 전체는 root인 'CA'로 조회, 나머지는 카테고리ROOT코드로 조회
    temp = f" AND CTGR_ID =   '{ctgr_cd}'" if ctgr_cd !='CA' else  " AND CTGR_ID = 'CA' "
    sql = f"""
        SELECT
            AA.CNTNT_ID        
            , AA.TITL 
            , (SELECT CD_NM FROM TBCTKC10 WHERE CD = AA.SAVE_STAT_CD AND GROUP_CD = 'SAVE_STAT_CD') AS CD_NM
            , AA.CTGR_ID
            , AA.CTGR_PATH
            , AA.REG_DTTM
            , AA.UPD_DTTM
            , ((SELECT COUNT(FILE_KEY) FROM TBCTKK08 WHERE CNTNT_ID = AA.CNTNT_ID AND USE_YN='Y') +
               (SELECT COUNT(FILE_KEY) FROM TBCTKK22 WHERE CNTNT_ID = AA.CNTNT_ID AND USE_YN='Y')) AS ATT_CNT
            , (SELECT count(*) FROM TBCGPT10 G WHERE G.CNTNT_ID = AA.CNTNT_ID ) AS EMB_CNT
            FROM (
            SELECT A.CNTNT_ID
                ,(CASE WHEN A.SAVE_STAT_CD = '00' THEN 
                            (SELECT 
                            (CASE WHEN COUNT(*) > 0 THEN 'Y' ELSE 'N' END) AS AUTH_YN
                            FROM TBCTKC21 A
                            INNER JOIN TBCTKC23 B
                                ON  A.ATRT_GROUP_ID = B.ATRT_GROUP_ID
                            WHERE A.ETC_INFO01 > '50') 
                    ELSE 'Y' END) AS VIEW_YN
                , A.TITL
                , A.CTGR_ID
                , A.UPD_DTTM
                , A.REG_DTTM
                , BB.CTGR_PATH
                , A.SAVE_STAT_CD
            FROM TBCTKK01 A
            INNER JOIN
                (  SELECT  CTGR_ID
                    , CTGR_NM
                    , CTGR_PATH
                    , CONNECT_BY_ISLEAF AS IS_LEAF
                    FROM TBCTKK12
                    START WITH USE_YN ='Y'
                {temp}
                CONNECT BY PRIOR CTGR_ID = HGRK_CTGR_ID AND USE_YN ='Y' ) BB
            ON  A.CTGR_ID = BB.CTGR_ID
            ) AA
        WHERE AA.VIEW_YN='Y'
        ORDER BY AA.CNTNT_ID desc
    """

    # print(sql)
    if (df := db.get_kms_datadf(sql)) is None:
        st.warning('No data found', icon="⚠️")
        st.stop()
    df.insert(0,'select', False)
    st.session_state["contents_df"] = df
    
    return df

def get_inquiry_cnt(from_dt=None, to_dt=None):
    if from_dt is None:
        from_dt = st.session_state['min_dt'].date().strftime('%Y%m%d')
    if to_dt is None:
        to_dt = st.session_state['max_dt'].date().strftime('%Y%m%d')

    sql = f"""
    SELECT  	ROW_NUMBER() OVER (ORDER BY A.INQ_CNT DESC)  AS ROW_NUMBER
     , A.CNTNT_ID
     , A.DT
    , A.TITL
    , A.INQ_CNT
    , A.CTGR_PATH
    , A.REG_DTTM
    , DPKMAPP.FNCTK_GET_USERNAME(A.REGR_ID, A.REGR_DEPT_CD, 'DEPT') AS REGR_NM
     FROM (
    SELECT   
    		 A.CNTNT_ID
    	   , A.DT
    	   , MAX(B.TITL)							AS TITL
    	   , SUM(nvl(A.INQ_CNT, 0))					AS INQ_CNT
    	   , MAX(B.CTGR_ID)							AS CTGR_ID
    	   , MAX(C.CTGR_PATH) 						AS CTGR_PATH
    	   , MAX(B.REG_DTTM) 						AS REG_DTTM
     	   , MAX(B.REGR_ID)							AS REGR_ID
     	   , MAX(B.REGR_DEPT_CD)					AS REGR_DEPT_CD
      FROM DPKMAPP.TBCTKK03 A	   /* 컨텐츠 마스터  */
    INNER JOIN DPKMAPP.TBCTKK01 B ON (A.CNTNT_ID = B.CNTNT_ID)							
     INNER JOIN (
            SELECT CTGR_ID
                 , CTGR_NM
                 , CTGR_PATH
              FROM DPKMAPP.TBCTKK12
             START WITH 1=1
			   AND CTGR_ID      ='CA'
               CONNECT BY PRIOR CTGR_ID = HGRK_CTGR_ID AND USE_YN ='Y'
            ) C 
            ON (B.CTGR_ID = C.CTGR_ID)  /* 카테고리 */
	  WHERE 1=1
 	  AND DT BETWEEN {from_dt} AND {to_dt}							
      GROUP BY A.CNTNT_ID, A.DT
     ) A
    """
    if (df_inq := db.get_kms_datadf(sql)) is None:
        st.warning('No data found', icon="⚠️")
        st.stop()
    
    return df_inq

def display_list(df, include_embded, option="전체"):
    """
    This function is used to display filtered datarame.

    Args:
        df (pd.DataFrame): The dataframe containing the content metadata.
        include_embded (bool): A boolean value indicating whether to include the contents that have already been embedded.
        option (str, optional): The contents status to filter the results. Defaults to "전체".

    Returns:
        None
    """

    if not include_embded:
        df = df[df['emb_cnt']==0]
    option = "전체" if option == None else option

    # 날짜로 filter
    df = df[(df['upd_dttm'] >= st.session_state.min_dt ) & (df['upd_dttm'] <= st.session_state.max_dt)]
    # print(st.session_state.min_dt, st.session_state.max_dt)
  
    df.reset_index(drop=True, inplace=True)
    edited_df = st.data_editor (
        df if option =='전체' else df[df['cd_nm']==option],
        hide_index=True,
        column_order = ("select","cntnt_id", "titl", "cd_nm","att_cnt", "ctgr_path", "upd_dttm"),
        column_config= {
            "select": st.column_config.CheckboxColumn(
                "Choice?",
                help="check for **embedding** ",
                default=False,
            ),
            "cntnt_id": st.column_config.TextColumn("컨텐츠번호"),
            "titl": st.column_config.TextColumn("컨텐츠명"),
            "cd_nm": st.column_config.TextColumn("상태"),
            "att_cnt": st.column_config.NumberColumn(
                "첨부파일수",
                format="📁 %d",
            ),
            "ctgr_path": st.column_config.TextColumn("경로"),
            "upd_dttm": st.column_config.DatetimeColumn("수정일"),
        },
        disabled=['cntnt_id'],
        height=320,
        key = "data_grid",
    )
    col1, col2 = st.columns([6, 1])
    with col2:
        st.write('Total', len(df if option =='전체' else df[df['cd_nm']==option]), '건')

    st.markdown('##### ⛓️ :orange[Contents] :rainbow[to embed] #####')
    selected_df = edited_df[edited_df['select']==True]
    if len(selected_df) > 0:
        disp_df(selected_df)

        col1, col2 = st.columns([6, 1])
        with col1:
            st.button(":pushpin: Click to Embed", on_click = embedding_process, args = [selected_df,col2])
        with col2:
            st.write("Total", len(selected_df),"건")


def embedding_process(selected_df,col2):
    """
    This function is used to perform embedding on the selected dataframe.

    Args:
        selected_df (pd.DataFrame): The dataframe containing the content id and other metadata.
        col2 (object): The column object where the progress bar will be displayed.

    Returns:
        bool: Returns True if the embedding process is successful, else False.

    """
    print("embedding start -------------------")

    openai_api_key = OPENAI_API_KEY
    st.session_state.vectorList = faiss_v.get_vectored_files()

    progress_text = "Operation in progress. Please wait."
    with col2:
        my_bar = st.progress(0, text=progress_text)
    
    for idx, row in selected_df.iterrows():
        cntnt_id = row["cntnt_id"]
        ctgr_path  = row["ctgr_path"].split('>')[1]
        
        df = qa_chat.get_kms_contents(cntnt_id)
        if df is None:
            st.warning(f'{cntnt_id} content details is empty')
            continue
        df.fillna('',inplace=True)

        f_name = ''.join(df.cntnt_id[0]) + '.html' #파일명 = 컨텐츠id
               
        html_doc = htm.make_html(df)

        with open(f'docs/{f_name}','w', encoding='utf-8') as f:
            f.write(html_doc)

        print('file read............................',f_name)

        kms_vector = True # 'KMS통합임베딩'
        with open(f'docs/{f_name}','r', encoding='utf-8') as f:
            qa_chat.upload_process(openai_api_key,f,kms_vector,cntnt_id=cntnt_id,ctgr_path=ctgr_path)

        my_bar.progress(idx, text=progress_text)

    my_bar.empty()

    db.get_kms_datadf.clear() #임베딩 이후에는 캐시를 지워 다른 이벤트 발생시 db 재조회함

    return True

if __name__ == '__main__':
    app()