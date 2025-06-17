from databaseOperation3 import DatabaseOperation
import ollama
import chromadb
import time

embedmodel = "nomic-embed-text"
#models = ['llama3.1','ftllama3.1','phi3.5','ftphi3.5']
models = ['llama3.1:8b-instruct-fp16','ftllama3.1','phi4:14b','ftphi4']
#models = ['llama3.1:8b-instruct-fp16','ftllama3.1','phi4:14b']
chroma = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma.get_or_create_collection("idx", metadata={"hnsw:space": "cosine", "hnsw:M": 64, "hnsw:search_ef": 200, "hnsw:construction_ef": 400})
#collection = chroma.get_or_create_collection("idx", metadata={"hnsw:space": "cosine"})

dbm = DatabaseOperation()

def inference(fid, pid, mainmodel, query, src, limit):
    sql3 = "select id from infer where fid = " + fid + " and pid = " + pid + " and modelname = '" + mainmodel + "'"
    resultSet3, resultSet3Count = dbm.dbSelect(sql3)

    if int(resultSet3Count) < 1:
        # print("OK")
        start_time1 = time.perf_counter()
        queryembed = ollama.embeddings(model=embedmodel, prompt=query)['embedding']
        relevantdocs = ""
        flag = 0

        try:
           relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=20)["documents"][0]
           flag = 1
           print("20")
        except:
           print("Ex 20")
           pass

        try:
            if flag == 0:
                relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=10)["documents"][0]
                flag = 1
                print("10")
        except:
            print("Ex 10")
            pass

        try:
            if flag == 0:
                relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=5)["documents"][0]
                flag = 1
                print("5")
        except:
            print("Ex 5")
            pass

        try:
            if flag == 0:
                relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=3)["documents"][0]
                flag = 1
                print("3")
        except:
            print("Ex 3")
            pass

        try:
            if flag == 0:
                relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=2)["documents"][0]
                flag = 1
                print("2")
        except:
            print("Ex 2")
            pass

        try:
            if flag == 0:
                relevantdocs = \
                    collection.query(query_embeddings=[queryembed], where={"source": src}, n_results=1)["documents"][0]
                flag = 1
                print("1")
        except:
            print("Ex 1")
            pass

        docs = " ".join(relevantdocs)
        if len(docs.strip()) == 0:
            print("No Doc")  
        end_time1 = time.perf_counter()
        doc_time = (end_time1 - start_time1)

        delimiter = "```"

        system_message = ("As a qualified LEGAL ADVISOR, please carefully evaluate the search warrant given below. Also analyze the given text as a forensic investigator.")

        user_message = f"{delimiter}{docs}{delimiter}\n\n{query}>"

        modelquery = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]

        modelprompt = (
               "<|im_start|>system\n"
               "As a qualified LEGAL ADVISOR, please carefully evaluate the search warrant given below. Also analyze the given text as a forensic investigator. <|im_end|>\n"
               "<|im_start|>user\n"
               f"{delimiter}{docs}{delimiter}\n\n{query}<|im_end|>\n"
               "<|im_start|>assistant\n"
        )

        start_time2 = time.perf_counter()
        #print(modelquery)

        if limit == 0:
            if mainmodel == 'ftphi4':
                system_prompt = "As a qualified LEGAL ADVISOR, please carefully evaluate the search warrant given below. Also analyze the given text as a forensic investigator."
                stream = ollama.generate(model=mainmodel, prompt=modelprompt, system=system_prompt, format="json", stream=False, options={"num_ctx": 8192, "temperature": 0, "seed": 123, "num_predict": 150})
            elif mainmodel == 'ftllama3.1':
                stream = ollama.chat(model=mainmodel, messages=modelquery, stream=True, options={"num_ctx": 8192, "temperature": 0, "seed": 123, "num_predict": 150})
            else:
                stream = ollama.chat(model=mainmodel, messages=modelquery, format="json", stream=True, options={"num_ctx": 8192, "temperature": 0, "seed": 123, "num_predict": 150})
        else:
            if mainmodel == 'ftphi4':
                system_prompt = "As a qualified LEGAL ADVISOR, please carefully evaluate the search warrant given below. Also analyze the given text as a forensic investigator."
                stream = ollama.generate(model=mainmodel, prompt=modelprompt, system=system_prompt, format="json", stream=False, options={"num_ctx": 8192, "temperature": 0, "seed": 123})
            elif mainmodel == 'ftllama3.1':
                stream = ollama.chat(model=mainmodel, messages=modelquery, stream=True, options={"num_ctx": 8192, "temperature": 0, "seed": 123})
            else:
                stream = ollama.chat(model=mainmodel, messages=modelquery, format="json", stream=True, options={"num_ctx": 8192, "temperature": 0, "seed": 123})

        if mainmodel == 'ftphi4':
            output = stream["response"]
        else:
            output = ""
            for chunk in stream:
                if chunk['message']['content']:
                    # print(chunk['message']['content'], end='', flush=True)
                    text = chunk['message']['content'].replace('\n', '').replace('\r', '')
                    output += text

        end_time2 = time.perf_counter()
        res_time = (end_time2 - start_time2)

        docs = str(docs).replace("'", "\\'").replace('"', '\\"').upper()
        output = str(output).replace("'", "\\'").replace('"', '\\"').upper()

        sql4 = "insert into infer (fid, pid, doc, doctime, response, responsetime, modelname) values(" + str(fid) + ", " + str(pid) + ", '" + docs + "', " + str(doc_time) + ", '" + output + "', " + str(res_time) + ", '"+ mainmodel + "')"
        dbm.dbInsert(sql4)
        print(f"Saved : {fid}:{pid}")

    else:
        print(f"Skipped : {fid}:{pid}")

sql1 = "select fid, tr_fname from allfiles order by fid"
resultSet1, resultSet1Count = dbm.dbSelect(sql1)

sql2 = "select pid, searching_area, description, prompt, ctx from prompts order by pid"
resultSet2, resultSet2Count = dbm.dbSelect(sql2)

for row1 in resultSet1:
    fid = str(row1[0])
    trfname = str(row1[1])

    for row2 in resultSet2:
        pid = str(row2[0])
        sa = str(row2[1])
        des = str(row2[2]).strip()
        model_prompt = prompt + " " + des
        ctx = int(row2[4])

        src = ""
        match sa:
            case 'all':
                src = trfname + "_all"
                inference(fid, pid, models[0], model_prompt, src, ctx)
                inference(fid, pid, models[1], model_prompt, src, ctx)
                inference(fid, pid, models[2], model_prompt, src, ctx)
                inference(fid, pid, models[3], model_prompt, src, ctx)

            case 'affidavit':
                src = trfname + "_affi"
                inference(fid, pid, models[0], model_prompt, src, ctx)
                inference(fid, pid, models[1], model_prompt, src, ctx)
                inference(fid, pid, models[2], model_prompt, src, ctx)
                inference(fid, pid, models[3], model_prompt, src, ctx)

            case 'warrant':
                src = trfname + "_sw"
                inference(fid, pid, models[0], model_prompt, src, ctx)
                inference(fid, pid, models[1], model_prompt, src, ctx)
                inference(fid, pid, models[2], model_prompt, src, ctx)
                inference(fid, pid, models[3], model_prompt, src, ctx)

            case 'return':
                src = trfname + "_rtn"
                inference(fid, pid, models[0], model_prompt, src, ctx)
                inference(fid, pid, models[1], model_prompt, src, ctx)
                inference(fid, pid, models[2], model_prompt, src, ctx)
                inference(fid, pid, models[3], model_prompt, src, ctx)

            case _:
                src = ""
                print("Problem")

print("Done")
