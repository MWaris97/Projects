
"""  **** Created by: Muhammad Waris ******
     ********** Date: 28-Oct-2019 *********  """

import pandas as pd
import numpy as np

df = pd.read_csv("ouladdata/studentInfo.csv", index_col = 0)
df1 = pd.read_csv('ouladdata/studentAssessment.csv', index_col = 0)
df2 = pd.read_csv('ouladdata/studentVle_0.csv', index_col = 0)

studentInfo = df[['id_student', 'highest_education', 
'studied_credits', 'num_of_prev_attempts', 'final_result',
'disability']]

studentAssessment = df1[['id_student', 'date_submitted', 'score']]

studentVle = df2[['id_student', 'sum_click']]

sumOfsum_click = studentVle.groupby('id_student')['sum_click'].sum()

a = pd.merge(studentInfo, sumOfsum_click, on = 'id_student', how = 'outer')
a['sum_click'] = a['sum_click'].replace(to_replace = np.nan, value = "0")

final = pd.merge(a, studentAssessment, on = 'id_student')
print(final.head)
final.to_csv('ouladdata/abc.csv') 