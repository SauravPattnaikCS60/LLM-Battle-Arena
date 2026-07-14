from langchain_core.output_parsers import JsonOutputParser
from prompts import default_attacker_prompt, default_defender_prompt, validater_prompt
from parser import Response, Validater
from groq_call import run_groq_api
import json
import time
import re

def main(word, attacker_model, defender_model):
    parser = JsonOutputParser(pydantic_model=Response)    
    parser_validater = JsonOutputParser(pydantic_object=Validater)

    defender_history = []
    attacker_history = []
    defender_response = ""
    attacker_response = ""
    max_iterations = 10
    
    conversations = []
    
    for i in range(max_iterations):
        try:
            chat = {}
            
            print(f"Iteration : {i+1}")
            
            attk_prompt = default_attacker_prompt(word, defender_response, defender_history, attacker_history)
            attacker_response = run_groq_api(attk_prompt,model=attacker_model)
            attacker_response = parser.parse(attacker_response)['answer']
            
            chat['attacker_query'] = attacker_response
            
            defn_prompt = default_defender_prompt(word, attacker_response, defender_history, attacker_history)
            defender_response = run_groq_api(defn_prompt,model=defender_model)
            defender_response = parser.parse(defender_response)['answer']
            
            chat['defender_response'] = defender_response
            
            validation_prompt = validater_prompt(attacker_response,defender_response)
            
            validate_response = run_groq_api(validation_prompt, model='openai/gpt-oss-120b')
            validate_response = parser_validater.parse(validate_response)
            
            chat['validator'] = validate_response
            
            if validate_response['winner'] is not None:
                if validate_response['winner'] == 'attacker':
                    chat['winner'] = attacker_model
                    conclusion_string = f"Attacker {attacker_model} Won!! Defender did not obey game rules. Denied giving answer"
                    chat['iteration_won'] = i+1
                else:
                    chat['winner'] = defender_model
                    conclusion_string = f"Defender {defender_model} Won!! Attacker did not obey game rules. Asked a direct query"
                
                chat['conclusion'] = conclusion_string
                conversations.append(chat)
                return conversations
            
            tokens = re.findall(r"\b\w+\b", defender_response.lower())
            if word.lower() in tokens:
                chat['winner'] = attacker_model
                chat['conclusion'] = f"Attacker {attacker_model} Won!! Defender revealed the word"
                chat['iteration_won'] = i + 1
                conversations.append(chat)
                return conversations

            conversations.append(chat)
            defender_history.append(defender_response)
            attacker_history.append(attacker_response)
            time.sleep(2)
        except Exception as exc:
            print(exc)
            continue
        
    conversations.append({"winner":defender_model,"conclusion":f"Defender {defender_model} won!!"})
    return conversations
    
if __name__ == "__main__":

    models = ["qwen/qwen3-32b","meta-llama/llama-4-scout-17b-16e-instruct"]
    words  = ["spring"]
    word_agg_results = {}
    for word in words:
        
        print(f'Word : {word}')
        
        qwen_attack_stats = 0
        llama_attack_stats = 0
        
        qwen_attack_win_reason = []
        llama_attack_win_reason = []
        
        qwen_attack_iteration_win = []
        llama_attack_iteration_win = []
        
        print('Qwen attacks!')
        for run in range(3):
            result = main(word, models[0], models[1])
            if result[-1]['winner'] == models[0]:
                qwen_attack_stats += 1
                qwen_attack_win_reason.append(result[-1]['conclusion'])
                qwen_attack_iteration_win.append(result[-1]['iteration_won'])
            
            with open(f"results/qwen_attacker/{word}/{run}_conversation.json",'w') as f:
                json.dump(result, f, indent=4)
        
        print('Llama attacks!')
        for run in range(3):
            result = main(word, models[1], models[0])
            if result[-1]['winner'] == models[1]:
                llama_attack_stats += 1
                llama_attack_win_reason.append(result[-1]['conclusion'])
                llama_attack_iteration_win.append(result[-1]['iteration_won'])
            
            with open(f"results/llama_attacker/{word}/{run}_conversation.json",'w') as f:
                json.dump(result, f, indent=4)    
        
        llama_agg_stats = {"attacker" : llama_attack_stats, "defender" : 3-qwen_attack_stats, "attack_won_reason": llama_attack_win_reason, "attack_won_iteration":llama_attack_iteration_win}
        qwen_attack_stats = {"attacker" : qwen_attack_stats, "defender": 3-llama_attack_stats, "attack_won_reason":qwen_attack_win_reason,"attack_won_iteration":qwen_attack_iteration_win}
        
        word_agg_results[word] = {"llama" : llama_agg_stats, "qwen" : qwen_attack_stats}
    
    print(word_agg_results)
        
    with open("results/agg.json",'w') as f:
        json.dump(word_agg_results, f, indent=4)