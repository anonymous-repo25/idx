#Files insert to DB from Excel File

import PyPDF2
import re

import pandas as pd
from databaseOperation import DatabaseOperation

fileFolder = "/Users/mdrahman/AugustaUniversity/idxv2/program/pdf/"
def fileContent(fname):
    filePath = fileFolder + fname
    pdfFileObj = open(filePath, 'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    pdfPages = len(pdfReader.pages)
    content = """"""
    for page in range(pdfPages):
        pageObj = pdfReader.pages[page]
        content += pageObj.extract_text()
    pdfFileObj.close()
    return content

def contentSanitized(content):
    content = str(content).replace("'", "\\'").replace('"', '\\"').upper()
    return content

def contentParse(content, operation):
    parsed_content = """"""
    match operation:
        case 1:
            regexAffidavit = r"(?<=AFFIDAVIT FOR SEARCH WARRANT).*?(?=/S/)"
            rmatch = re.search(regexAffidavit, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if rmatch:
                parsed_content = rmatch.group().strip()
            return parsed_content

        case 2:
            regexSearchWarrant = r"(?<=SEARCH WARRANT\nNO).*?(?=/S/)"
            rmatch = re.search(regexSearchWarrant, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if rmatch:
                parsed_content = rmatch.group().strip()
            else:
                regexSearchWarrant = r"SEARCH WARRANT(.*?)NO(.*?)/S/"
                rmatch = re.search(regexSearchWarrant, parsed_content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
                if rmatch:
                    parsed_content = rmatch.group(2).strip()
                else:
                    regexSearchWarrant = r"(SEARCH WARRANT.*?/S/)"
                    rmatch = re.search(regexSearchWarrant, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
                    if rmatch:
                        parsed_content = rmatch.group(1).strip()
            return parsed_content

        case 3:
            regexReturn = r"(?<=RETURN TO SEARCH WARRANT\nNO).*?(?=/S/)"
            rmatch = re.search(regexReturn, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if rmatch:
                parsed_content = rmatch.group().strip()
            else:
                regexReturn = r"(RETURN TO SEARCH WARRANT.*?/S/)"
                rmatch = re.search(regexReturn, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
                if rmatch:
                    parsed_content = rmatch.group(1).strip()
            return parsed_content

        case _:
            print("Problem")
            return parsed_content

dbm = DatabaseOperation()

df = pd.read_excel('../files/files.xlsx')
df_len = len(df)

for i in range(df_len):
    #id = autoincrement

    fname = str(df.iloc[i, 0])

    #fid = str(df.iloc[i, 0])
    #trfname = str(df.iloc[i, 2])
    #fop = str(df.iloc[i, 3])

    f_content = fileContent(fname)
    f_content_sanitized = contentSanitized(f_content)
    f_affidavit = contentParse(f_content_sanitized, 1)
    f_warrant = contentParse(f_content_sanitized, 2)
    f_return = contentParse(f_content_sanitized, 3)
    f_content = str(f_content).replace("'", "\\'").replace('"', '\\"')

    #print(f"{fname}:{len(f_warrant)}:{len(f_return)}")

    sql = "update allfiles set f_warrant = '"+ f_warrant +"', f_return = '"+ f_return +"' where fname = '"+ fname +"'"
    print(fname)
    dbm.dbInsert(sql)

print("Done")