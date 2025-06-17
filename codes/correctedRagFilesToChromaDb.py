from mattsollamatools import chunk_text_by_sentences
from databaseOperation import DatabaseOperation
from dotenv import load_dotenv

import nltk
import chromadb
import ssl
import ollama
import os

def ssl_connectivity():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download('punkt')
    nltk.download('punkt_tab')

def getEnv():
    load_dotenv(dotenv_path=".env")
    embedmodel = os.getenv('embedmodel')
    mainmodel = os.getenv('mainmodel')
    print(embedmodel + ":" + mainmodel)
    return embedmodel, mainmodel

def chunk_text(text, chunk_size, overlap):
    chunks = chunk_text_by_sentences(source_text=text, sentences_per_chunk=chunk_size, overlap=overlap)
    return chunks

def chromaDBConfig():
    collectionname = "idx"
    chroma = chromadb.HttpClient(host="localhost", port=8000)
    collection = chroma.get_or_create_collection(name=collectionname, metadata={"hnsw:space": "cosine", "hnsw:M": 12000, "hnsw:search_ef": 12000, "hnsw:construction_ef": 12000})
    return collection

ssl_connectivity()
collection = chromaDBConfig()
embedmodel, model = getEnv()

count = 0
result = collection.get()
#result = collection.peek(limit=400000)
files = result['metadatas']
my_list = []
for val in files:
    value_to_append = val['source']
    if value_to_append not in my_list:
        my_list.append(value_to_append)

dbm = DatabaseOperation()
sql1 = "select tr_fname, f_content_sanitized, f_affidavit, f_warrant, f_return from allfiles order by fid"
resultSet1, resultSet1Count = dbm.dbSelect(sql1)

for row in resultSet1:
    print(row[0])
    source_name = row[0].strip()
    source_name_all = source_name + "_all"
    source_name_affi = source_name + "_affi"
    source_name_sw = source_name + "_sw"
    source_name_rtn = source_name + "_rtn"
    print(source_name)

    all = row[1].strip()
    affi = row[2].strip()
    sw = row[3].strip()
    rtn = row[4].strip()

    if source_name_all not in my_list:
        count += 1
        chunked_text = chunk_text(all, 10, 1)
        for index, chunk in enumerate(chunked_text):
            pdf_file = source_name_all + "_" + str(index)
            embed = ollama.embeddings(model=embedmodel, prompt=chunk)['embedding']
            print(".", end="", flush=True)
            # collection.delete([pdf_file], {"source": source_name_affi})
            collection.add([pdf_file], [embed], documents=[chunk], metadatas={"source": source_name_all})
        print("All Done")

    if source_name_affi not in my_list:
        count += 1
        chunked_text = chunk_text(affi, 10, 1)
        for index, chunk in enumerate(chunked_text):
            pdf_file = source_name_affi + "_" + str(index)
            embed = ollama.embeddings(model=embedmodel, prompt=chunk)['embedding']
            print(".", end="", flush=True)
            #collection.delete([pdf_file], {"source": source_name_affi})
            collection.add([pdf_file], [embed], documents=[chunk], metadatas={"source": source_name_affi})
        print("Affi Done")

    if source_name_sw not in my_list:
        count += 1
        chunked_text = chunk_text(sw, 10, 1)
        for index, chunk in enumerate(chunked_text):
            pdf_file = source_name_sw + "_" + str(index)
            embed = ollama.embeddings(model=embedmodel, prompt=chunk)['embedding']
            print(".", end="", flush=True)
            #collection.delete([pdf_file], {"source": source_name_sw})
            collection.add([pdf_file], [embed], documents=[chunk], metadatas={"source": source_name_sw})
        print("SW Done")

    if source_name_rtn not in my_list:
        count += 1
        chunked_text = chunk_text(rtn, 10, 1)
        for index, chunk in enumerate(chunked_text):
            pdf_file = source_name_rtn + "_" + str(index)
            embed = ollama.embeddings(model=embedmodel, prompt=chunk)['embedding']
            print(".", end="", flush=True)
            #collection.delete([pdf_file], {"source": source_name_rtn})
            collection.add([pdf_file], [embed], documents=[chunk], metadatas={"source": source_name_rtn})
        print("Rtn Done")

print("Done")
print(count)