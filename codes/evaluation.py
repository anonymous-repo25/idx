import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction, corpus_bleu
from rouge import Rouge
from bert_score import score as bert_score
#from moverscore import word_mover_score
from sacrerouge.metrics import moverscore
import ssl

def ssl_connectivity():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    nltk.download('wordnet')
    nltk.download('punkt')
    nltk.download('punkt_tab')

def calculate_bleu_score(reference, candidate, n=4):
    smoothing = SmoothingFunction().method1
    return corpus_bleu(reference, candidate, weights=tuple(1/n for _ in range(n)), smoothing_function=smoothing)

def calculate_bleu_ngram_score(reference, candidate, n=1):
    weights = [1 if i == n - 1 else 0 for i in range(n)] + [0] * (4 - n)
    smoothing = SmoothingFunction().method1
    return corpus_bleu(reference, candidate, weights=weights, smoothing_function=smoothing)

def calculate_rouge_score(reference, candidate):
    rouge = Rouge()
    scores = rouge.get_scores(candidate, reference)[0]
    return scores

def calculate_rouge_l_score(reference, candidate):
    rouge_scores = calculate_rouge_score(reference, candidate)
    return rouge_scores['rouge-l']['f']

def calculate_bert_score(reference, candidate, model_type="bert-base-uncased", num_layers=None, verbose=False):
    P, R, F1 = bert_score(candidate, reference, model_type=model_type, num_layers=num_layers, verbose=verbose)
    return P.mean().item(), R.mean().item(), F1.mean().item()

def calculate_moverscore(reference, candidate, n_gram=1, remove_stopwords=False):
    scores = word_mover_score(references=reference, hypotheses=candidate, n_gram=n_gram, stop_words='' if not remove_stopwords else 'english')
    return sum(scores) / len(scores) if scores else 0.0

if __name__ == "__main__":
    ssl_connectivity()
    source_paragraph = ""
    candidate_paragraph = ""

    source_sentences_tokens = [nltk.word_tokenize(sent.lower()) for sent in nltk.sent_tokenize(source_paragraph)]
    candidate_sentences_tokens = [nltk.word_tokenize(sent.lower()) for sent in nltk.sent_tokenize(candidate_paragraph)]
    reference_bleu = [word for sent in source_sentences_tokens for word in sent]
    candidate_bleu = [word for sent in candidate_sentences_tokens for word in sent]

    source_sentences_str = nltk.sent_tokenize(source_paragraph.lower())
    candidate_sentences_str = nltk.sent_tokenize(candidate_paragraph.lower())

    bleu_score = calculate_bleu_score([reference_bleu], [candidate_bleu])
    print(f"BLEU Score: {bleu_score:.4f}")

    bleu_1_score = calculate_bleu_ngram_score([reference_bleu], [candidate_bleu], n=1)
    print(f"BLEU-1 Score: {bleu_1_score:.4f}")
    bleu_2_score = calculate_bleu_ngram_score([reference_bleu], [candidate_bleu], n=2)
    print(f"BLEU-2 Score: {bleu_2_score:.4f}")
    bleu_3_score = calculate_bleu_ngram_score([reference_bleu], [candidate_bleu], n=3)
    print(f"BLEU-3 Score: {bleu_3_score:.4f}")
    bleu_4_score = calculate_bleu_ngram_score([reference_bleu], [candidate_bleu], n=4)
    print(f"BLEU-4 Score: {bleu_4_score:.4f}")

    rouge_scores = calculate_rouge_score(source_paragraph.lower(), candidate_paragraph.lower())
    print("\nROUGE Scores:")
    for key, value in rouge_scores.items():
        print(f"{key}: {value}")

    rouge_l = calculate_rouge_l_score(source_paragraph.lower(), candidate_paragraph.lower())
    print(f"ROUGE-L Score (F1): {rouge_l:.4f}")

    bert_precision, bert_recall, bert_f1 = calculate_bert_score(source_sentences_str, candidate_sentences_str)
    print(f"\nBERTScore:")
    print(f"  Precision: {bert_precision:.4f}")
    print(f"  Recall: {bert_recall:.4f}")
    print(f"  F1 Score: {bert_f1:.4f}")

    moverscore = calculate_moverscore(source_sentences_str, candidate_sentences_str)
    print(f"\nMoverScore: {moverscore:.4f}")