from google.colab import drive
from google.colab import files
drive.mount('/content/drive')

import json
train_set_json = "/content/drive/MyDrive/idx2/idx2trainingset_alpaca.json"

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# import os
# if "COLAB_" not in "".join(os.environ.keys()):
#     !pip install unsloth
# else:
#     # Do this only in Colab notebooks! Otherwise use pip install unsloth
#     !pip install --no-deps bitsandbytes accelerate xformers==0.0.29 peft trl triton
#     !pip install --no-deps cut_cross_entropy unsloth_zoo
#     !pip install sentencepiece protobuf datasets huggingface_hub hf_transfer
#     !pip install --no-deps unsloth

from unsloth import FastLanguageModel
import torch
model_name = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
max_seq_length = 8192 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True # Use 4bit quantization to reduce memory usage. Can be False.

model, tokenizer = FastLanguageModel.from_pretrained (
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    device_map = "auto",
)

from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(
      tokenizer,
      chat_template = "llama-3.1"
  )
tokenizer.pad_token = '<|reserved_special_token_250|>'
tokenizer.pad_token_id = 128255

model = FastLanguageModel.get_peft_model(
    model,
    r = 32, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    use_rslora = False,  # We support rank stabilized LoRA
    loftq_config = None, # And LoftQ
)

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }
pass

from datasets import load_dataset
dataset = load_dataset("json", data_files=train_set_json, split = "train")
dataset = dataset.map(formatting_prompts_func, batched = True,)

from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        #max_steps = 300,
        num_train_epochs=3,
        learning_rate = 1e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        #fp16 = not is_bfloat16_supported(),
        #bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "/content/drive/MyDrive/idx2/output_llama3_1",
        report_to = "none", # Use this for WandB etc
    ),
)

#trainer_stats = trainer.train()
trainer_stats = trainer.train(resume_from_checkpoint = True)

model.save_pretrained("/content/drive/MyDrive/idx2/model_llama3_1/llama3_1_ft_dfair") # Local saving
tokenizer.save_pretrained("/content/drive/MyDrive/idx2/model_llama3_1/llama3_1_ft_dfair")
#model.save_pretrained_gguf("model", tokenizer,)

#model.save_pretrained_gguf("llama3_q4_k_m", tokenizer, quantization_method = "q4_k_m")
model.save_pretrained_gguf("/content/drive/MyDrive/idx2/model_llama3_1/llama3_1_ft16_dfair", tokenizer, quantization_method = "f16")

!curl -fsSL https://ollama.com/install.sh | sh

import subprocess
subprocess.Popen(["ollama", "serve"])
import time
time.sleep(3)

print(tokenizer._ollama_modelfile)
filepath = "/content/drive/MyDrive/idx2/model_llama3_1/Modelfile"

with open(filepath, "w") as f:
  f.write(str(tokenizer._ollama_modelfile))

print(f"File saved to: {filepath}")