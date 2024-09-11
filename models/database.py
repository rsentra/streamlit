import streamlit as st
import cx_Oracle
import datetime
import pandas as pd


def get_conn_ora_st():
    ''' st.connection이용 '''
    # 오라클 클라이언트를 선언: windows 환경변수에 path를 잡으면 필요없음
    try:
        cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_4")
    except Exception as e:
        pass

   # Initialize connection.
   # st.connection은 .streamlit/secrets.toml 파일을 참조함
    return st.connection("oracle", type="sql")


def get_conn_ora():
    """
    This function creates an Oracle connection using the cx_Oracle package.

    Args:
        None

    Returns:
        connection (object): An Oracle connection object

    """
    username = st.secrets["connections_oracle"]["username"]
    password = st.secrets["connections_oracle"]["password"]
    dsn = f'{st.secrets["connections_oracle"]["host"]}:{st.secrets["connections_oracle"]["port"]}/{st.secrets["connections_oracle"]["database"]}'
    encoding = st.secrets["connections_oracle"]["encoding"]

    # 오라클 클라이언트를 선언: windows 환경변수에 path를 잡으면 필요없음
    try:
        cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_4")
    except Exception as e:
        pass

    try:
        connection = cx_Oracle.connect(username, password, dsn, encoding=encoding)
    except Exception as ex:
        print('Could not connect to database:', ex)
        return ex

    print("SUCCESS: Connecting database succeeded")
    return connection

def save_embed_history(cntnt_id,vector_nm,idx):
    """
    This function saves the embedding vector id and the content id in the database.

    Args:
        cntnt_id (char): The content id.
        vector_id (char): The embedding vector id.

    Returns:
        (bool): Returns True if the operation is successful, False otherwise.

    """
    it_processing = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # it_processing = pd.to_datetime(it_processing)
  
    vector_id = str(idx)
    print('db insert: ', cntnt_id, ' ', vector_nm,' ',vector_id,' ', it_processing)
    
    # f-string을 쓸때 문자열은 ''로 감싸주어야 oracle에러 방지됨
    sql = f"""insert into tbcgpt10(cntnt_id, vtr_id, vtr_nm,  it_processing)
              values({cntnt_id}, {vector_id}, '{vector_nm}', '{it_processing}')"""
    # print(sql)

    try:
        connection = get_conn_ora()
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(sql)
            
        connection.close()

    except Exception as ex:
        err, = ex.args
        print('error code :', err.code)
        print('error message :', err.message)
        return False
   
    return True


@st.cache_data
def get_kms_datadf(sql):
    """
    This function retrieves data from the database using the SQL query provided.

    Args:
        sql (str): The SQL query to be executed.

    Returns:
        pd.DataFrame: A pandas dataframe containing the results of the query.

    Raises:
        Exception: If there is an error connecting to the database or executing the query.

    """
    try:
        connection = get_conn_ora()
     
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
        return None
   
    if len(df) ==0:
        print('No data found')  
        return None

    return df

@st.cache_data
def get_common_code(cd):
    sql = f""" SELECT k10.cd_nm, k10.cd
                    FROM tbctkc10 k10
                    where k10.group_cd = '{cd}'
                    and use_yn = 'Y' and cd <> '****'
                    ORDER BY K10.SORT_ORD
                """
    try:
        connection = get_conn_ora()
     
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            cols = [x[0].lower() for x in cursor.description]
   
        df = pd.DataFrame(rows, columns = cols)
   
        connection.close()

    except Exception as ex:
        err, = ex.args
        print('error code :', err.code)
        print('error message :', err.message)
        return None
   
    if len(df) ==0:
        print('No data found')  
        return None

    return df