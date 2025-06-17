#Prompts insert to DB from Excel File

import pandas as pd
from databaseOperation import DatabaseOperation

dbm = DatabaseOperation()

df = pd.read_excel('../files/prompts.xlsx')
df_len = len(df)

for i in range(df_len):
    #id = autoincrement
    pid = str(df.iloc[i, 0])
    item = str(df.iloc[i, 1]).replace("'", "\\'").replace('"', '\\"')
    searching_area = str(df.iloc[i, 2])
    category = str(df.iloc[i, 3])
    description = str(df.iloc[i, 4]).replace("'", "\\'").replace('"', '\\"').upper()
    prompt = str(df.iloc[i, 5]).replace("'", "\\'").replace('"', '\\"').upper()
    paraphrased_questions = str(df.iloc[i, 6]).replace("'", "\\'").replace('"', '\\"').upper()
    annotation = str(df.iloc[i, 7]).upper() or " "
    ctx = str(df.iloc[i, 8])

    sql = "insert into prompts(pid,item,searching_area,category,description,prompt,paraphrased_questions,annotation,ctx) values(" + pid + ", '" + item+"', '"+searching_area+"', '"+category+"', '"+description+"', '"+prompt+"', '"+paraphrased_questions+"', '"+annotation+"', "+ctx+")"
    dbm.dbInsert(sql)

print("Done")
