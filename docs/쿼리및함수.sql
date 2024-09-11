''' 1. 컨텐츠번호로 컨텐츠,탭,소제목 내용을 조회하는 쿼리 '''
def get_sql(cn_id):
    return f'''SELECT k01.cntnt_id AS cntnt_id 
             , k01.titl AS titl_nm
             , k13.cntnt_nm AS sec_nm
             , k13.cntnt_no as sec_id
             , k24.sub_cntnt_nm AS para_nm
             , k24.sub_cntnt_no as para_id
             , k24.contn AS contn
             , bb.ctgr_path
        FROM   tbctkk01 k01
             , tbctkk13 k13
             , tbctkk24 k24
             ,(  SELECT  CTGR_ID
                        , CTGR_NM
                        , CTGR_PATH
                        , CONNECT_BY_ISLEAF AS IS_LEAF
                        FROM TBCTKK12
                        START WITH USE_YN ='Y'
                       AND CTGR_ID = 'CA'
                CONNECT BY PRIOR CTGR_ID = HGRK_CTGR_ID AND USE_YN ='Y' ) bb
        where k01.cntnt_id = {cn_id}
          AND k01.cntnt_id = k13.cntnt_id
          AND k13.cntnt_id = k24.CNTNT_ID 
          AND k13.cntnt_no = k24.CNTNT_NO 
          AND k01.use_yn = 'Y'
          AND k13.use_yn = 'Y'
          AND k24.use_yn = 'Y'
          and k01.CTGR_ID = BB.CTGR_ID
        ORDER BY k13.sort_ord, k24.sort_ord'''


'''2, 컨텐츠를 json으로 변화하는 함수'''
def make_contents_to_json(cn_id):
    sql = get_sql(cn_id)
    # 주어진 쿼리로 kms db connect, execute, db-> dataframe으로 반환하는 함수call
    df = db.get_kms_datadf(sql)

    if df is None:
        print(cn_id, ' No Data')
        return False
    df = df.fillna('')  # null을 ''으로 치환
    
    '''공공사업실 방법 ==> 최종 24.5.2 '''
    dic = {}
    temp_dic = {}
    sec_i, para_i = [0, 0]
    titl_nm,sec_id,para_id  = ["", "", ""]

    lst = []
    for idx, row in df.iterrows():
        sec_i = sec_i + 1 if row.sec_id != sec_id else sec_i
        para_i = 0 if row.sec_id != sec_id else  para_i  #텝이 바뀌면 순번 restart
        para_i = para_i + 1 if row.para_id != para_id else para_i
        temp_dic = {}
        temp_dic['title'] = row.titl_nm
        temp_dic['section'] = row.sec_nm
        temp_dic['paragraph'] = row.para_nm
        html_string = row.contn
        html_string = delete_tag(html_string,"all")
        temp_dic['contents'] = html_string
        temp_dic['primary_key'] = f"{row.cntnt_id}>{row.sec_id}>{row.para_id}"
        temp_dic['path'] = row.ctgr_path
        lst.append(temp_dic)
        titl_nm, sec_id, para_id = row.titl_nm, row.sec_id, row.para_id

    o_name = 'docs/' + str(cn_id) + '.json'
    dd = dict({'data':lst})
    with open(o_name, 'w', encoding='utf8') as f:
         f.write(json.dumps(dd, ensure_ascii=False))
    print('succ')


'''3. 정규표현식을 활용한 tag제거 '''
import re
# 함수선언
def subResult(regex, repl, text):
    value = re.sub(regex, repl, text)
#     if value == text:
#         print ('# -- '+ regex, '\n', value, '\n', '-' * 30)
    return value

def delete_tag(text,method="partial"):
    if text is None:
        return ''
    pattern = r'<style[^>]*>.*?</style>|style="[^"]*"'       # style= " " 태그 제거 
    value = subResult(pattern, "", text)
    if method=='all':
        value = subResult("<(/)?p[^>]*>", "", value)        # <p~></p~> 태그 제거
        value = subResult("<(/)?b[^>]*>", "", value)        # <b~></b~> 태그 제거
        value = subResult(r">\s+<", "><", value)            # 닫는 tag와 시작tag 사이의 공백제거
    else:
        value = subResult("<p[^>]*>", "", value)              # <p~> 태그 제거
    value = subResult("<(/)?span[^>]*>", " ", value)         # <spn~></span~> 태그 제거
    value = ' '.join(value.split())                          # 두개 이상의 공백을 하나로
    value = value.replace('&nbsp;','')
    return value

'''4. 위 함수를 이용하여 52451, 52448 컨텐츠를 json으로 생성 '''
cn_list = [52451,52448]
for cn_id in cn_list:
    make_contents_to_json(cn_id)


'''5. update_contents_batch api에서는 '''
code와 컨텐츠 번호를 넣고, files = json 파일을 넘기면 됨