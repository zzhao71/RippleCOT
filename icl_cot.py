import json
import torch
import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import argparse
from dataset import load_mquake, load_ripple

argparser = argparse.ArgumentParser()
argparser.add_argument("--prompt_type", type=str)
argparser.add_argument("--prompt_model", type=str)
argparser.add_argument("--num_shot", type=int)
argparser.add_argument("--num_human_icl", type=int)
argparser.add_argument("--json", type=str)
argparser.add_argument("--dataset", type=str)
argparser.add_argument("--out_dir", type=str)
argparser.add_argument("--debug", action="store_true")

args = argparser.parse_args()

os.makedirs(args.out_dir, exist_ok=True)



    
if args.dataset == "mquake":
    dataset = load_mquake(args.json)
    from icl_generator import human_icl_only, human_icl, chatgpt_icl_by_human_icl, chatgpt_icl_by_zeroshot, gptj_icl_by_human_icl
    if args.prompt_type == "chatgpt_icl_by_human_icl":
        icl_prompt = chatgpt_icl_by_human_icl(args.prompt_model,args.num_shot, args.num_human_icl) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_chatgpt-icl-by-human-icl_pmodel-{args.prompt_model}_num-shot-{args.num_shot}_num-human-icl-{args.num_human_icl}.json"
    elif args.prompt_type == "chatgpt_icl_by_zeroshot":
        icl_prompt = chatgpt_icl_by_zeroshot(args.prompt_model, args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_chatgpt-icl-by-zeroshot_pmodel-{args.prompt_model}_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "human_icl":
        icl_prompt = human_icl(args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_human-icl_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "human_icl_only":
        icl_prompt = human_icl_only(args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_human-icl-only_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "zero_shot":
        icl_prompt = ""
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_zero-shot.json"
    elif args.prompt_type == "gptj_icl_by_human_icl_generate_on_the_fly":
        icl_prompt = gptj_icl_by_human_icl(args.num_human_icl, args.num_shot, True)
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_gptj_icl_by_human_icl_generate_on_the_fly_num-shot-{args.num_shot}_num-human-icl-{args.num_human_icl}.json"
    elif args.prompt_type == "gptj_icl_by_human_icl":
        icl_prompt = gptj_icl_by_human_icl(-1, args.num_shot, False)
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_gptj_icl_by_human_icl_num-shot-{args.num_shot}.json"
elif args.dataset == "ripple":
    dataset = load_ripple(args.json)
    from ripple_icl_generator import human_icl, human_icl_cot, chatgpt_icl_cot_by_human_icl_cot, chatgpt_icl_cot_by_zeroshot, gptj_icl_cot_by_human_icl_cot
    if args.prompt_type == "chatgpt_icl_cot_by_human_icl_cot":
        icl_prompt = chatgpt_icl_cot_by_human_icl_cot(args.prompt_model,args.num_shot, args.num_human_icl) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_chatgpt-icl-cot-by-human-icl-cot_pmodel-{args.prompt_model}_num-shot-{args.num_shot}_num-human-icl-{args.num_human_icl}.json"
    elif args.prompt_type == "chatgpt_icl_by_zeroshot":
        icl_prompt = chatgpt_icl_cot_by_zeroshot(args.prompt_model, args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_chatgpt-icl-cot-by-zeroshot_pmodel-{args.prompt_model}_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "human_icl":
        icl_prompt = human_icl(args.json, args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_human-icl_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "human_icl_cot":
        icl_prompt = human_icl_cot(args.num_shot) + "\n\n"
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_human-icl-cot_num-shot-{args.num_shot}.json"
    elif args.prompt_type == "zero_shot":
        icl_prompt = ""
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_zero-shot.json"
    elif args.prompt_type == "gptj_icl-cot_by_human_icl_generate_on_the_fly":
        icl_prompt = gptj_icl_cot_by_human_icl_cot(args.num_human_icl, args.num_shot, True)
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_gptj-icl-cot-by-human-icl-cot_generate_on_the_fly_num-shot-{args.num_shot}_num-human-icl-{args.num_human_icl}.json"
    elif args.prompt_type == "gptj_icl_by_human_icl":
        icl_prompt = gptj_icl_cot_by_human_icl_cot(-1, args.num_shot, False)
        out_filename = f"{os.path.basename(args.json).split('.')[0]}_output_gptj-icl-cot-by-human-icl-cot_num-shot-{args.num_shot}.json"
    

if os.path.exists(os.path.join(args.out_dir, out_filename)):
    print("already exists!!!")
    import sys
    sys.exit()

if args.debug:
    dataset = dataset[:2]
    
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B").to(device)
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

output = []
for i, entry in enumerate(tqdm.tqdm(dataset)):
    
    answers = []
    
    for question in entry['formated_questions']:
    
        prompt = icl_prompt + question
        
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)

        gen_tokens = model.generate(
            input_ids,
            do_sample=True,
            temperature=0.9,
            max_length=500,
            max_new_tokens=50,
        )
        generated_token_ids = gen_tokens[0][input_ids.shape[1]:]
        generated_text = tokenizer.decode(generated_token_ids, skip_special_tokens=True)
        answers.append(generated_text)

    entry['output_by_model'] = answers
    output.append(entry)


with open(os.path.join(args.out_dir, out_filename), 'w') as f:
    json.dump(output, f, indent=4)
    
