from scipy.stats import kruskal
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:@localhost/idxsurvey")
df = pd.read_sql("SELECT modelname, actor, pid, human_eval FROM humanevaluation", engine)
likert_map = {'VB': 1, 'B': 2, 'M': 3, 'G': 4, 'VG': 5}
df['human_eval_num'] = df['human_eval'].map(likert_map)
#model_groups = [group['human_eval_num'].values for _, group in df.groupby('modelname')]
model_groups = [group['human_eval_num'].values for _, group in df.groupby('actor')]
stat, p = kruskal(*model_groups)
print("Kruskal–Wallis H-statistic:", stat)
print("p-value:", p)
if p < 0.05:
    print("→ Significant difference in human evaluations across models.")
else:
    print("→ No significant difference in human evaluations across models.")
