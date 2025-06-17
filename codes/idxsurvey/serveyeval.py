import mysql.connector
import pandas as pd
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='idxsurvey'
)
query = "SELECT modelname, actor, pid, human_eval FROM humanevaluation"
df = pd.read_sql(query, conn)
likert_map = {'VB': 1, 'B': 2, 'M': 3, 'G': 4, 'VG': 5}
df['human_eval_num'] = df['human_eval'].map(likert_map)
pivot1 = df.pivot_table(index='pid', columns='modelname', values='human_eval_num', aggfunc='mean')
pivot1 = pivot1.reset_index()
pivot1 = pivot1.round(2)
pivot1.to_csv("model_pid_avg.csv", index=False)
pivot2 = df.pivot_table(index=['pid', 'actor'], columns='modelname', values='human_eval_num', aggfunc='mean')
pivot2 = pivot2.reset_index()
pivot2 = pivot2.round(2)
pivot2.to_csv("pivot_model_eval_by_actor.csv", index=False)
conn.close()
