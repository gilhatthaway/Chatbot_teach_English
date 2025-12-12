from copy import deepcopy

LESSON_TEMPLATE = {
    "topic": "",
    "vocabulary": [
        {"word": "", "pronunciation": "", "english_meaning": "", "vietnamese_meaning": "", "example": ""} for _ in range(5)
    ],
    "example_sentences": [
        {"english": "", "translation": ""} for _ in range(5)
    ],
    "conversation": [
        {"speaker": "A", "text": "", "translation": ""},
        {"speaker": "B", "text": "", "translation": ""},
        {"speaker": "A", "text": "", "translation": ""},
        {"speaker": "B", "text": "", "translation": ""}
    ],
    "exercises": [
        {
            "type": "fill_in_blank",
            "question": "Chọn từ đúng để điền vào chỗ trống.",
            "items": [
                {"sentence": "", "options": [], "answer": ""}
            ]
        },
        {
            "type": "sentence_order",
            "question": "Sắp xếp các từ sau thành câu hoàn chỉnh.",
            "items": [
                {"scrambled_words": [], "answer": ""}
            ]
        },
        {
            "type": "make_sentence",
            "question": "Tạo một câu hoàn chỉnh sử dụng các từ cho sẵn.",
            "items": [
                {"prompt_words": [], "example_answer": ""}
            ]
        }
    ]
}

def standardize_lesson(ai_json: dict, topic: str) -> dict:
    """
    Chuẩn hóa JSON bài học AI trả về sang cấu trúc chuẩn LESSON_TEMPLATE.
    """
    # Đảm bảo ai_json là dictionary
    if not isinstance(ai_json, dict):
        print(f"⚠️ ai_json không phải dict: {type(ai_json)}, sử dụng giá trị mặc định")
        ai_json = {}
    
    result = deepcopy(LESSON_TEMPLATE)
    result['topic'] = ai_json.get('topic', topic)

    # --- Vocabulary ---
    vocab_mapping = {
        "word": ["word"],
        "pronunciation": ["pronunciation"],
        "english_meaning": ["english_meaning", "english_definition", "meaning"],
        "vietnamese_meaning": ["vietnamese_meaning", "vietnamese_definition", "translation"],
        "example": ["example"]
    }
    
    vocab_list = ai_json.get('vocabulary', [])
    if not isinstance(vocab_list, list):
        print(f"⚠️ vocabulary không phải list: {type(vocab_list)}")
        vocab_list = []
    
    for i, vocab in enumerate(vocab_list):
        if i >= len(result['vocabulary']):
            break
        if not isinstance(vocab, dict):
            print(f"⚠️ vocab item {i} không phải dict: {type(vocab)}")
            continue
        
        new_vocab = {}
        for k, keys in vocab_mapping.items():
            for key in keys:
                if key in vocab:
                    new_vocab[k] = vocab[key]
                    break
            else:
                new_vocab[k] = ""
        result['vocabulary'][i].update(new_vocab)

    # --- Example sentences ---
    ex_mapping = {
        "english": ["sentence", "english"],
        "translation": ["vietnamese_translation", "translation"]
    }
    # Tìm examples từ AI response 
    examples_data = ai_json.get('examples', ai_json.get('example_sentences', []))
    if not isinstance(examples_data, list):
        print(f"⚠️ examples_data không phải list: {type(examples_data)}")
        examples_data = []
    
    for i, ex in enumerate(examples_data):
        if i >= len(result['example_sentences']):
            break
        if not isinstance(ex, dict):
            print(f"⚠️ example item {i} không phải dict: {type(ex)}")
            continue
        
        new_ex = {}
        for k, keys in ex_mapping.items():
            for key in keys:
                if key in ex:
                    new_ex[k] = ex[key]
                    break
            else:
                new_ex[k] = ""
        result['example_sentences'][i].update(new_ex)

    # --- Conversation ---
    conv_mapping = {
        "speaker": ["speaker"],
        "text": ["dialogue", "text", "sentence"],
        "translation": ["vietnamese_translation", "translation"]
    }
    conv_list = ai_json.get('conversation', [])
    if not isinstance(conv_list, list):
        print(f"⚠️ conversation không phải list: {type(conv_list)}")
        conv_list = []
    
    # Xử lý conversation có thể có cấu trúc khác nhau
    for i, msg in enumerate(conv_list):
        if not isinstance(msg, dict):
            print(f"⚠️ conversation item {i} không phải dict: {type(msg)}")
            continue
        
        new_msg = {}
        
        # Xử lý trường hợp dialogue chứa cả A và B trong một string
        if 'dialogue' in msg and isinstance(msg['dialogue'], str):
            dialogue_text = msg['dialogue']
            translation = msg.get('vietnamese_translation', '')
            
            # Parse format "A: Do you like apples? B: Yes, I love apples!"
            if "A:" in dialogue_text and "B:" in dialogue_text:
                parts = dialogue_text.split("B:")
                if len(parts) == 2:
                    # Thêm message A
                    a_text = parts[0].replace("A:", "").strip()
                    if a_text:
                        new_msg_a = {"speaker": "A", "text": a_text, "translation": translation}
                        if i * 2 >= len(result['conversation']):
                            result['conversation'].append(new_msg_a)
                        else:
                            result['conversation'][i * 2].update(new_msg_a)
                    
                    # Thêm message B  
                    b_text = parts[1].strip()
                    if b_text:
                        new_msg_b = {"speaker": "B", "text": b_text, "translation": translation}
                        if i * 2 + 1 >= len(result['conversation']):
                            result['conversation'].append(new_msg_b)
                        else:
                            result['conversation'][i * 2 + 1].update(new_msg_b)
                    continue
        
        # Xử lý object thông thường
        for k, keys in conv_mapping.items():
            for key in keys:
                if key in msg:
                    new_msg[k] = msg[key]
                    break
            else:
                new_msg[k] = ""
        
        if i >= len(result['conversation']):
            result['conversation'].append(new_msg)
        else:
            result['conversation'][i].update(new_msg)

    # --- Exercises ---
    exercises_list = ai_json.get('exercises', [])
    if not isinstance(exercises_list, list):
        print(f"⚠️ exercises không phải list: {type(exercises_list)}")
        exercises_list = []
    
    # Nếu AI trả về exercises, xử lý cấu trúc của nó
    processed_exercises = []
    for exercise in exercises_list:
        if not isinstance(exercise, dict):
            print(f"⚠️ exercise item không phải dict: {type(exercise)}")
            continue
        
        exercise_type = exercise.get('type', '')
        
        # Nếu exercise có cấu trúc mới với items array
        if 'items' in exercise and isinstance(exercise['items'], list):
            # Normalize từng item trong items array
            normalized_items = []
            for item in exercise['items']:
                if not isinstance(item, dict):
                    continue
                
                if exercise_type == 'fill_in_blank':
                    normalized_items.append({
                        "sentence": item.get('sentence', ''),
                        "options": item.get('options', []),
                        "answer": item.get('answer', '')
                    })
                elif exercise_type == 'sentence_order':
                    # Xử lý cả scrambled_words và scrambled
                    scrambled = item.get('scrambled_words') or item.get('scrambled', [])
                    normalized_items.append({
                        "scrambled_words": scrambled,
                        "answer": item.get('answer', '')
                    })
                elif exercise_type == 'make_sentence':
                    # Xử lý cả prompt_words/words và example_answer/suggested_answer
                    words = item.get('prompt_words') or item.get('words', [])
                    answer = item.get('example_answer') or item.get('suggested_answer', '')
                    normalized_items.append({
                        "prompt_words": words,
                        "example_answer": answer
                    })
            
            if normalized_items:
                processed_exercises.append({
                    "type": exercise_type,
                    "question": exercise.get('question', ''),
                    "items": normalized_items
                })
        # Nếu exercise có cấu trúc cũ, convert sang cấu trúc mới
        elif exercise_type == 'fill_in_blank' and 'options' in exercise:
            processed_exercises.append({
                "type": exercise_type,
                "question": exercise.get('question', 'Chọn từ đúng để điền vào chỗ trống.'),
                "items": [{
                    "sentence": exercise.get('question', ''),
                    "options": exercise.get('options', []),
                    "answer": exercise.get('answer', '')
                }]
            })
        elif exercise_type == 'sentence_order' and ('scrambled' in exercise or 'scrambled_words' in exercise):
            scrambled = exercise.get('scrambled_words') or exercise.get('scrambled', [])
            processed_exercises.append({
                "type": exercise_type,
                "question": exercise.get('question', 'Sắp xếp các từ sau thành câu hoàn chỉnh.'),
                "items": [{
                    "scrambled_words": scrambled,
                    "answer": exercise.get('answer', '')
                }]
            })
        elif exercise_type == 'make_sentence':
            words = exercise.get('prompt_words') or exercise.get('words', [exercise.get('word', '')])
            answer = exercise.get('example_answer') or exercise.get('suggested_answer', '')
            processed_exercises.append({
                "type": exercise_type,
                "question": exercise.get('question', 'Tạo một câu hoàn chỉnh sử dụng các từ cho sẵn.'),
                "items": [{
                    "prompt_words": words,
                    "example_answer": answer
                }]
            })
    
    # Nếu AI không trả về exercises hoặc exercises rỗng, tạo exercises mẫu từ vocabulary
    if not processed_exercises:
        result['exercises'] = create_sample_exercises(result['vocabulary'])
    else:
        result['exercises'] = processed_exercises

    return result

def create_sample_exercises(vocabulary):
    """Tạo exercises mẫu từ vocabulary với cấu trúc mới (items array)"""
    exercises = []
    
    # Fill in blank exercises với items array
    fill_in_blank_items = []
    for i, vocab in enumerate(vocabulary[:5]):
        if vocab.get('word') and vocab.get('example'):
            word = vocab['word']
            example = vocab['example']
            
            # Tạo câu hỏi điền từ
            if word.lower() in example.lower():
                question = example.replace(word, '_____').replace(word.capitalize(), '_____')
                # Tạo options (4 lựa chọn)
                options = [word]
                other_words = [v.get('word', '') for v in vocabulary if v != vocab and v.get('word')]
                options.extend(other_words[:3])
                
                if len(options) > 0 and word:
                    fill_in_blank_items.append({
                        "sentence": f"{i+1}. {question}",
                        "options": options,
                        "answer": word
                    })
    
    if fill_in_blank_items:
        exercises.append({
            "type": "fill_in_blank",
            "question": "Chọn từ đúng để điền vào chỗ trống.",
            "items": fill_in_blank_items
        })
    else:
        # Tạo default items nếu vocabulary trống
        exercises.append({
            "type": "fill_in_blank",
            "question": "Chọn từ đúng để điền vào chỗ trống.",
            "items": [
                {"sentence": "1. _____ is a popular fast food.", "options": ["Pizza", "Book", "Car", "House"], "answer": "Pizza"}
            ]
        })
    
    # Sentence order exercises với items array
    sentence_order_items = []
    for i, vocab in enumerate(vocabulary[:4]):
        if vocab.get('example'):
            example = vocab['example']
            words = example.split()
            if len(words) > 3:
                sentence_order_items.append({
                    "scrambled_words": words,
                    "answer": example
                })
    
    if sentence_order_items:
        exercises.append({
            "type": "sentence_order",
            "question": "Sắp xếp các từ sau thành câu hoàn chỉnh.",
            "items": sentence_order_items
        })
    else:
        # Tạo default items nếu vocabulary trống
        exercises.append({
            "type": "sentence_order",
            "question": "Sắp xếp các từ sau thành câu hoàn chỉnh.",
            "items": [
                {"scrambled_words": ["like", "I", "pizza"], "answer": "I like pizza"}
            ]
        })
    
    # Make sentence exercises với items array
    make_sentence_items = []
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('word') and vocab.get('example'):
            make_sentence_items.append({
                "prompt_words": [vocab['word']],
                "example_answer": vocab['example']
            })
    
    if make_sentence_items:
        exercises.append({
            "type": "make_sentence",
            "question": "Tạo một câu hoàn chỉnh sử dụng các từ cho sẵn.",
            "items": make_sentence_items
        })
    else:
        # Tạo default items nếu vocabulary trống
        exercises.append({
            "type": "make_sentence",
            "question": "Tạo một câu hoàn chỉnh sử dụng các từ cho sẵn.",
            "items": [
                {"prompt_words": ["pizza", "love"], "example_answer": "I love pizza"}
            ]
        })
    
    return exercises