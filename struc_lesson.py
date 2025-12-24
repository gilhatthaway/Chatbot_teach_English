from copy import deepcopy

LESSON_TEMPLATE = {
    "topic": "",
    "vocabulary": [
        {"word": "", "pronunciation": "", "english_meaning": "", "vietnamese_meaning": "", "example": ""} for _ in range(10)
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
        {"type": "fill_in_blank", "question": "", "options": [], "answer": ""} for _ in range(3)
    ] + [
        {"type": "sentence_order", "scrambled": [], "answer": ""} for _ in range(3)
    ] + [
        {"type": "make_sentence", "word": "", "example": ""} for _ in range(3)
    ]
}

def standardize_lesson(ai_json: dict, topic: str) -> dict:
    """
    Chuẩn hóa JSON bài học AI trả về sang cấu trúc chuẩn LESSON_TEMPLATE.
    """
    if not isinstance(ai_json, dict):
        ai_json = {"topic": topic}

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
        vocab_list = [vocab_list]

    for i, vocab in enumerate(vocab_list):
        if not isinstance(vocab, dict):
            if isinstance(vocab, str):
                vocab = {"word": vocab}
            else:
                continue

        if i >= len(result['vocabulary']):
            break
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
        examples_data = [examples_data]

    for i, ex in enumerate(examples_data):
        if not isinstance(ex, dict):
            if isinstance(ex, str):
                ex = {"sentence": ex}
            else:
                continue
        if i >= len(result['example_sentences']):
            break

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
        conv_list = [conv_list]
    
    # Xử lý conversation có thể có cấu trúc khác nhau
    for i, msg in enumerate(conv_list):
        if not isinstance(msg, dict):
            if isinstance(msg, str):
                msg = {"dialogue": msg}
            else:
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
    exercises_data = ai_json.get('exercises')

    if exercises_data:
        if not isinstance(exercises_data, list):
            exercises_data = [exercises_data]

        normalized_exercises = []
        for ex in exercises_data:
            if not isinstance(ex, dict):
                continue

            ex_type = ex.get('type') or ex.get('exercise_type')
            if ex_type == 'fill_in_blank':
                question = ex.get('question') or ex.get('sentence') or ''
                options = ex.get('options') or ex.get('choices') or []
                answer = ex.get('answer') or ex.get('correct') or ''

                if isinstance(options, str):
                    options = [opt.strip() for opt in options.split(',') if opt.strip()]
                if not isinstance(options, list):
                    options = [options] if options else []

                if answer and answer not in options:
                    options.append(answer)

                if not question or not options:
                    continue

                normalized_exercises.append({
                    "type": "fill_in_blank",
                    "question": question,
                    "options": options,
                    "answer": answer
                })

            elif ex_type == 'sentence_order':
                scrambled = ex.get('scrambled') or ex.get('words') or []
                if isinstance(scrambled, str):
                    scrambled = [w.strip() for w in scrambled.split() if w.strip()]
                answer = ex.get('answer') or ex.get('solution') or ''

                normalized_exercises.append({
                    "type": "sentence_order",
                    "scrambled": scrambled,
                    "answer": answer
                })

            elif ex_type == 'make_sentence':
                word = ex.get('word') or ex.get('words') or ''
                example = ex.get('example') or ex.get('answer') or ''

                normalized_exercises.append({
                    "type": "make_sentence",
                    "word": word,
                    "example": example
                })

        # Nếu không normalize được bài tập nào hợp lệ, fallback sang bài tập mẫu
        result['exercises'] = normalized_exercises or create_sample_exercises(result['vocabulary'])
    else:
        # Nếu AI không trả về exercises, tạo exercises mẫu từ vocabulary
        result['exercises'] = create_sample_exercises(result['vocabulary'])

        # Đảm bảo mỗi loại bài tập có ít nhất 3 bài
        result['exercises'] = ensure_exercise_counts(result['exercises'], result['vocabulary'])

    return result

def create_sample_exercises(vocabulary):
    """Tạo exercises mẫu từ vocabulary"""
    exercises = []
    
    # Fill in blank exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('word') and vocab.get('example'):
            word = vocab['word'].lower()
            example = vocab['example']
            
            # Tạo câu hỏi điền từ
            if word in example.lower():
                question = example.replace(word, '_____').replace(word.capitalize(), '_____')
                # Tạo options
                options = [word]
                other_words = [v.get('word', '').lower() for v in vocabulary if v != vocab and v.get('word')]
                options.extend(other_words[:3])
                
                exercises.append({
                    "type": "fill_in_blank",
                    "question": question,
                    "options": options,
                    "answer": word
                })
    
    # Sentence order exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('example'):
            example = vocab['example']
            words = example.split()
            if len(words) > 3:
                exercises.append({
                    "type": "sentence_order", 
                    "scrambled": words,
                    "answer": example
                })
    
    # Make sentence exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('word') and vocab.get('example'):
            exercises.append({
                "type": "make_sentence",
                "word": vocab['word'],
                "example": vocab['example']
            })
    
    return exercises


def ensure_exercise_counts(exercises, vocabulary):
    """Đảm bảo mỗi loại bài tập có tối thiểu 3 bài, bổ sung từ mẫu nếu thiếu."""
    target_types = ["fill_in_blank", "sentence_order", "make_sentence"]
    sample_pool = create_sample_exercises(vocabulary)

    # Gom exercises mẫu theo loại để dùng khi thiếu
    sample_by_type = {
        ex_type: [ex for ex in sample_pool if ex.get("type") == ex_type]
        for ex_type in target_types
    }

    final_exercises = []

    for ex_type in target_types:
        typed_exercises = [ex for ex in exercises if ex.get('type') == ex_type]

        # Bổ sung từ sample nếu chưa đủ
        while len(typed_exercises) < 3 and sample_by_type[ex_type]:
            typed_exercises.append(sample_by_type[ex_type].pop(0))

        # Nếu vẫn thiếu, thêm placeholder cơ bản
        while len(typed_exercises) < 3:
            if ex_type == "fill_in_blank":
                typed_exercises.append({
                    "type": "fill_in_blank",
                    "question": "Điền từ thích hợp vào chỗ trống.",
                    "options": ["A", "B", "C"],
                    "answer": ""
                })
            elif ex_type == "sentence_order":
                typed_exercises.append({
                    "type": "sentence_order",
                    "scrambled": [],
                    "answer": ""
                })
            elif ex_type == "make_sentence":
                typed_exercises.append({
                    "type": "make_sentence",
                    "word": "",
                    "example": ""
                })

        # Chỉ giữ 3 bài cho mỗi loại để giao diện hiển thị ổn định
        final_exercises.extend(typed_exercises[:3])

    return final_exercises