import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

with open('datasets/MQuAKE-CF-3k.json', 'r') as f:
    dataset = json.load(f)

all_knowledge = []
all_answers = []

# Iterate with an index
for i, entry in enumerate(dataset, start=1):
    thoughts = []
    for rewrite in entry["requested_rewrite"]:
        new_fact = {
            "new_fact": rewrite["prompt"].format(rewrite["subject"]) + " " + rewrite["target_new"]["str"],
        }
        all_knowledge.append(new_fact)
        break

    if i % 5 == 0:
        questions = entry['questions']
        first_question = questions[0]
        knowledge_entry = {
            "Questions": first_question,
        }
        all_knowledge.append(knowledge_entry)
        answer = entry['new_answer']

        answer_aliases = entry.get('new_answer_alias', [])  # Get answer_alias if it exists, else an empty list
        all_answers.append([answer] + answer_aliases)
    else:  # Add detailed processing except for every fifth entry
        questions = entry['questions']
        first_question = questions[0]
        answer = entry['new_answer']

        for hop in entry["new_single_hops"]:
            thought = f"{hop['cloze']} {hop['answer']}."
            thoughts.append(thought)

        if thoughts:
            combined_thoughts = " ".join(thoughts)
            knowledge_entry = {
                "Questions": first_question,
                "Thoughts": combined_thoughts,
                "Answer": answer,
            }
            all_knowledge.append(knowledge_entry)

print("New Knowledge Examples:")
for nk in all_knowledge[:20]:
    print(nk)

print(all_answers[:20])

def is_answer_correct(provided_answer, correct_answers):
    return any(correct_answer.lower() in provided_answer.lower() for correct_answer in correct_answers)

correct_answers = 0
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B").to(device)
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

prompt = []
i = 1
for knowledge_entry in all_knowledge[:10]:  # Example: limit to first 5 entries for demonstration
    if i % 10 == 0:
        prompt.append(f"Question: {knowledge_entry['Questions']}")

        prompt = "\n".join(prompt)
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

        expected_answer = all_answers[int(i / 10) - 1]

        # Checking for answer presence
        if is_answer_correct(generated_text, expected_answer):
            print("The expected answer is contained in the generated text.")
            correct_answers += 1
        else:
            print("The expected answer is NOT contained in the generated text.")

        print("Generated Text:", generated_text)

        print(prompt)

        prompt = []

    else:
        if 'new_fact' in knowledge_entry:
            prompt.append(f"New Fact: {knowledge_entry['new_fact']}")
        else:
            prompt.append(f"Question: {knowledge_entry['Questions']}\nThoughts: {knowledge_entry['Thoughts']}\nAnswer: {knowledge_entry['Answer']}\n")
    i += 1

print(f"Correct Answers: {correct_answers}/{len(all_answers)}")
