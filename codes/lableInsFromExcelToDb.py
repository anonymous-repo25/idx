#Lables insert to DB from Excel File

import pandas as pd
import math
from databaseOperation import DatabaseOperation

def contentSanitized(content):
    if content is None or len(str(content).strip()) == 0 or str(content).lower() == "nan" or (isinstance(content, float) and math.isnan(content)):
        return "NOT MENTIONED"
    else:
        return str(content).replace("'", "\\'").replace('"', '\\"').replace('[', '').replace(']', '').upper().strip()

dbm = DatabaseOperation()

sql2 = "select * from allfiles where f_operation = 'test' order by fid"
resultSet2, resultSet2Count = dbm.dbSelect(sql2)

def get_fid_by_trfname(trfname):
    for row in resultSet2:
        db_fid = row[1]
        if row[3] == trfname:
            return db_fid
    return None

df1 = pd.read_excel('../files/mapping_prompt_lable.xlsx')
df1_len = len(df1)
prompt_map = [int(df1.iloc[i, 1]) for i in range(df1_len)]

#df2 = pd.read_excel('../files/lables.xlsx')
df2 = pd.read_excel('../files/test_lables.xlsx')
df2_len = len(df2)

for i in range(df2_len):
#for i in range(1):
    tid = str(df2.iloc[i, 0])
    trfname = str(df2.iloc[i, 4])
    fid = str(get_fid_by_trfname(trfname))

    for j in range(len(prompt_map)):
        pid = str(j + 1)
        content = str(df2.iloc[i, prompt_map[j]])
        content_sanitized = contentSanitized(content)
        sql = "insert into testset(tid, fid, pid, label) values(" + tid + ", " + fid + ", " + pid + ", '" + content_sanitized + "')"
        #print(sql)
        dbm.dbInsert(sql)
        print(trfname + ":" + str(pid))

print("Done")
