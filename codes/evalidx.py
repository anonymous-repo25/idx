import ssl
import nltk
import json
import ollama
import re
from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from bert_score import score as bert_score
from databaseOperation import DatabaseOperation

def ssl_connectivity():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download('punkt')
    nltk.download('wordnet')

def calculate_bleu_score(reference, candidate, n=4):
    smoothing = SmoothingFunction().method1
    weights = tuple(1/n for _ in range(n))
    return corpus_bleu(reference, candidate, weights=weights, smoothing_function=smoothing)

def calculate_bleu_ngram_score(reference, candidate, n=1):
    weights = [1 if i == n - 1 else 0 for i in range(4)]
    smoothing = SmoothingFunction().method1
    return corpus_bleu(reference, candidate, weights=tuple(weights), smoothing_function=smoothing)

def calculate_rouge_scores(reference, candidate):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    return scorer.score(reference, candidate)

def calculate_bert_score(reference_sentences, candidate_sentences, model_type="bert-base-uncased"):
    cands = [line.rstrip('\n') for line in candidate_sentences]
    cand = [''.join(cands)]

    refs = [line.rstrip('\n') for line in reference_sentences]
    ref = [''.join(refs).upper()]

    #P, R, F1 = bert_score(candidate_sentences, reference_sentences, model_type=model_type, verbose=False)
    P, R, F1 = bert_score(cand, ref, model_type=model_type, verbose=False)
    return P.mean().item(), R.mean().item(), F1.mean().item()

def flatten_json_to_string(json_string: str) -> str:
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return json_string

    extracted_values = []

    def _recursive_flatten(item):
        if isinstance(item, dict):
            for value in item.values():
                _recursive_flatten(value)
        elif isinstance(item, list):
            for element in item:
                _recursive_flatten(element)

        elif item is None:
            extracted_values.append("null")
        elif isinstance(item, bool):
            extracted_values.append(str(item).lower())
        else:
            extracted_values.append(str(item))

    _recursive_flatten(data)
    return " ".join(extracted_values)

def check_by_llm(src, dst, context):

    src = src.replace("'", "").replace("`", "") .replace('"', '').replace("[", "").replace("]", "").upper().strip()
    dst = dst.replace("'", "").replace("`", "").replace('"', '').replace("[", "").replace("]", "").upper().strip()

    query = (
            "Do these 2 phrases share the same concept or context, even if one includes more specific information? If there are numbers in the sentences, try to find the presence of the number in another sentence. "
            "If 2 sentences are identical return 1. If the sentences represent similar concept return 1 otherwise return 0. "
            "The context of the phrases is ``` " + context + "``` "
            "Your entire response must be a valid JSON object containing a single key (e.g., \"is_similar\") with a numerical value of 1 or 0. For example: {\"is_similar\": 1}. "
            "The sentences are denoted by triple backticks.")

    delimiter = "```"
    query = query + " " + delimiter + src + delimiter + " vs " + delimiter + dst + delimiter
    response = ollama.generate(model=model, prompt=query, options={"num_ctx": 8192, "temperature": 0, "seed": 131, "num_predict": 150, "format":"json"})

    #print(query)
    #print(response['response'])
    return response['response']

def extract_is_similar_value(text_blob: str) -> int | None:
    #pattern = r'\{\s*"is_similar"\s*:\s*(\d+)\s*\}'
    pattern = r'"is_similar"\s*:\s*(\d+)'

    try:
        matches = re.findall(pattern, text_blob)

        if matches:
            last_number_str = matches[-1]
            return int(last_number_str)
        else:
            return 0

    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

if __name__ == "__main__":
    model = 'llama3.2:3b-instruct-fp16'
    ssl_connectivity()
    dbm = DatabaseOperation()

    sql1 = "select i.fid, i.pid, i.doc, i.response, i.modelname, ts.label from infer i left join testset ts on i.fid = ts.fid and i.pid = ts.pid where i.fid > 70"
    resultSet1, resultSet1Count = dbm.dbSelect(sql1)

    sql2 = "select prompt from prompts order by pid"
    resultSet2, resultSet2Count = dbm.dbSelect(sql2)

    for row1 in resultSet1:
        fid = str(row1[0])
        pid = str(row1[1])
        pid_idx = int(pid) - 1
        prompt = resultSet2[pid_idx][0].replace("NO INTRODUCTION IS REQUIRED, JUST DIRECTLY PROVIDE THE ANSWER. ANSWER BASED ON THE GIVEN TEXT ONLY. IF THE ANSWER IS NOT MENTIONED, PLEASE RETURN 'NOT MENTIONED'.","").strip()
        modelname = str(row1[4])
        doc = str(row1[2])
        response = flatten_json_to_string(str(row1[3])).strip()
        label = str(row1[5]).strip()

        source_text = label if len(label) > 0 else doc
        candidate_text = response

        sql3 = "select eid from evaluation where fid = " + fid + " and pid = " + pid + " and modelname = '" + modelname + "'"
        resultSet3, resultSet3Count = dbm.dbSelect(sql3)

        if int(resultSet3Count) < 1:

            ref_tokens = [nltk.word_tokenize(sent.lower()) for sent in nltk.sent_tokenize(source_text)]
            hyp_tokens = [nltk.word_tokenize(sent.lower()) for sent in nltk.sent_tokenize(candidate_text)]
            ref_flat = [token for sent in ref_tokens for token in sent]
            hyp_flat = [token for sent in hyp_tokens for token in sent]

            src_sentences = nltk.sent_tokenize(source_text)
            cand_sentences = nltk.sent_tokenize(candidate_text)
            bert_precision, bert_recall, bert_f1 = calculate_bert_score(src_sentences, cand_sentences)

            bleu_base = calculate_bleu_score([ref_flat], [hyp_flat])
            bleu_1 = calculate_bleu_ngram_score([ref_flat], [hyp_flat], n=1)
            bleu_2 = calculate_bleu_ngram_score([ref_flat], [hyp_flat], n=2)
            bleu_3 = calculate_bleu_ngram_score([ref_flat], [hyp_flat], n=3)
            bleu_4 = calculate_bleu_ngram_score([ref_flat], [hyp_flat], n=4)

            rouge = calculate_rouge_scores(source_text, candidate_text)
            rouge_1_precision = rouge['rouge1'][0]
            rouge_1_recall = rouge['rouge1'][1]
            rogue_1_f1 = rouge['rouge1'][2]

            rouge_2_precision = rouge['rouge2'][0]
            rouge_2_recall = rouge['rouge2'][1]
            rogue_2_f1 = rouge['rouge2'][2]

            rouge_L_precision = rouge['rougeL'][0]
            rouge_L_recall = rouge['rougeL'][1]
            rogue_L_f1 = rouge['rougeL'][2]

            accuracy = extract_is_similar_value(check_by_llm(source_text, candidate_text, prompt))
            #print(f"{fid}:{pid}:{modelname}:{accuracy}")

            query = """
            insert into evaluation(modelname, fid, pid, bert_precision, bert_recall, bert_f1, bleu_base, bleu_1, bleu_2, bleu_3, bleu_4,
                       rouge_1_precision, rouge_1_recall, rogue_1_f1, rouge_2_precision, rouge_2_recall, rouge_2_f1,
                       rouge_L_precision, rouge_L_recall, rouge_L_f1, accuracy, human_eval)
            values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            data = {
                'modelname': modelname,
                'fid': fid,
                'pid': pid,
                'bert_precision': bert_precision,
                'bert_recall': bert_recall,
                'bert_f1': bert_f1,
                'bleu_base': bleu_base,
                'bleu_1': bleu_1,
                'bleu_2': bleu_2,
                'bleu_3': bleu_3,
                'bleu_4': bleu_4,
                'rouge_1_precision': rouge_1_precision,
                'rouge_1_recall': rouge_1_recall,
                'rogue_1_f1': rogue_1_f1,
                'rouge_2_precision': rouge_2_precision,
                'rouge_2_recall': rouge_2_recall,
                'rogue_2_f1': rogue_2_f1,
                'rouge_L_precision': rouge_L_precision,
                'rouge_L_recall': rouge_L_recall,
                'rogue_L_f1': rogue_L_f1,
                'accuracy': accuracy,
                'human_eval': 0.0
            }

            values = (
                data['modelname'], data['fid'], data['pid'],
                data['bert_precision'], data['bert_recall'], data['bert_f1'],
                data['bleu_base'], data['bleu_1'], data['bleu_2'], data['bleu_3'], data['bleu_4'],
                data['rouge_1_precision'], data['rouge_1_recall'], data['rogue_1_f1'],
                data['rouge_2_precision'], data['rouge_2_recall'], data['rogue_2_f1'],
                data['rouge_L_precision'], data['rouge_L_recall'], data['rogue_L_f1'],
                data['accuracy'], data['human_eval']
            )

            dbm.mycursor.execute(query, values)
            dbm.mydb.commit()

            print(f"Saved:{fid}:{pid}:{modelname}:{accuracy}")