import pandas as pd
import json
from databaseOperation import DatabaseOperation

def file_create(file_name):
    with open(file_name, 'w') as file:
        file.write('')

def file_close(file_name):
    with open(file_name, 'a') as file:
        file.write('')

def file_append(file_name, data_sample, is_first):
    with open(file_name, 'a') as file:
        if not is_first:
            file.write(',')
        json.dump(data_sample, file)

def file_append_string(file_name, x):
    with open(file_name, 'a') as file:
        file.write(x)

def trim_last_character(file_name):
    with open(file_name, 'r') as file:
        content = file.read()
    modified_content = content[:-1]
    with open(file_name, 'w') as file:
        file.write(modified_content)

dbm = DatabaseOperation()

sql1 = "select * from prompts order by pid"
resultSet1, resultSet1Count = dbm.dbSelect(sql1)

def get_promptInfo_by_pid(pid):
    for row in resultSet1:
        if row[1] == pid:
            db_searching_area = row[3]
            db_prompt = row[6]
            db_paraphrased = row[7]

            return db_prompt, db_paraphrased, db_searching_area
    return None

sql2 = "select * from allfiles where f_operation = 'training' order by fid"
resultSet2, resultSet2Count = dbm.dbSelect(sql2)

def get_fid_by_trfname(fid, search_area):
    for row in resultSet2:
        if row[1] == fid:
            db_input_text = """"""
            match search_area:
                case 'all':
                    db_input_text = row[5]
                    return db_input_text

                case 'affidavit':
                    db_input_text = row[6]
                    return db_input_text

                case 'warrant':
                    db_input_text = row[7]
                    return db_input_text

                case 'return':
                    db_input_text = row[8]
                    return db_input_text

                case _:
                    print("Problem")
                    return db_input_text

            return db_input_text
    return None

file_name = '/Users/mdrahman/AugustaUniversity/idxv2/program/files/idx2trainingset_parquet.json'
perquet_file_name = '/Users/mdrahman/AugustaUniversity/idxv2/program/files/idx2trainingset_parquet.parquet'
file_create(file_name)

file_append_string(file_name, "{\"conversations\":[")
data_samples1 = {"from": "system", "value": "As a qualified Legal Advisor, please carefully evaluate the Search Warrant given. Also analyze the given text as a Forensic Investigator and a Lawyer."}
file_append(file_name, data_samples1, True)

data_samples1 = {"from": "human", "value": ""}
file_append(file_name, data_samples1, False)

data_samples1 = {"from": "gpt", "value": ""}
file_append(file_name, data_samples1, False)

file_append_string(file_name, "]}\n")

sql3 = "select * from trainingset order by tid"
resultSet3, resultSet3Count = dbm.dbSelect(sql3)
for row in resultSet3:
    db_fid = row[2]
    db_pid = row[3]
    db_label = row[4]

    instruction_text, db_paraphrased, db_search_area = get_promptInfo_by_pid(db_pid)
    input_text = get_fid_by_trfname(db_fid, db_search_area)     #input
    output_text = db_label                                      #response

    file_append_string(file_name, "{\"conversations\":[")
    data_samples1 = {"from": "human", "value": "CONTEXT: " + input_text}
    file_append(file_name, data_samples1, True)
    data_samples1 = {"from": "human", "value": instruction_text}
    file_append(file_name, data_samples1, False)
    data_samples1 = {"from": "gpt", "value": output_text}
    file_append(file_name, data_samples1, False)
    file_append_string(file_name, "]}\n")

    tokens = db_paraphrased.split(",")
    for value in tokens:
        instruction_text = value
        file_append_string(file_name, "{\"conversations\":[")
        data_samples1 = {"from": "human", "value": "CONTEXT: " + input_text}
        file_append(file_name, data_samples1, True)
        data_samples1 = {"from": "human", "value": instruction_text}
        file_append(file_name, data_samples1, False)
        data_samples1 = {"from": "gpt", "value": output_text}
        file_append(file_name, data_samples1, False)
        file_append_string(file_name, "]}\n")

trim_last_character(file_name)
file_close(file_name)

df = pd.read_json(file_name, orient="records", lines=True)
df.to_parquet(perquet_file_name)

print("Parquet file saved successfully!")
print("Done")