
def make_html(df):
    cntnt_id = df.cntnt_id[0]
    html_doc = ''
    titl_nm,tab_nm,sub_nm  = ['','','']
    s1 = ''
    #탭은 h2, 소제목은 h3 tag로 생성
    for idx, row in df.iterrows():
        titl_nm =  row.titl_nm
        s2 =  '<h2>' + row.tab_nm +'</h2>' if row.tab_nm != tab_nm else ""
        s3 =  '<h3>' + row.sub_nm +'</h3>' if row.sub_nm != sub_nm else ""
        html_doc = html_doc + s1 + s2 + s3 + row.contn
        titl_nm, tab_nm, sub_nm = row.titl_nm,row.tab_nm,row.sub_nm
        
    titl_nm = f'({cntnt_id}) {titl_nm}'  # 제목앞에 컨텐츠 (관리번호) 붙임
    html_doc = make_header(html_doc,titl_nm)
    return html_doc

def make_header(cntnt_body, titl_nm):
    html_header = f'<!DOCTYPE html> \
    <html> \
    <head><meta http-equiv="X-UA-Compatible" content="IE=Edge"> \
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"> \
        <title> {titl_nm} </title> \
    </head> <body>'
    html_footer = '</body> </html>'
   #컨텐츠 제목은 h1 tag로 생성
    titl = '<h1>' + titl_nm + '</h1>' 
    
    html_doc  = html_header + titl + cntnt_body + html_footer
    return html_doc