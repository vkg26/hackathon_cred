from flask import Flask, render_template, request, jsonify, session, url_for
import os, json, uiautomator2 as u2
from datetime import datetime
from werkzeug.utils import secure_filename
from voice import transcribe_audio  # Uses your voice.py function
from context_handler import ConversationContext
from intent_classification import classify_user_intent
from embedding_utils import generate_embedding
from insight_provider import query_insights, answer_with_llm
from rrf import get_best_match, extract_keywords_with_llm
from step_utils import generate_detailed_steps, get_next_action, get_text_coordinates
import re

app = Flask(__name__, static_folder='static')
app.secret_key = 'copilot-secret'
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
context = ConversationContext()

def save_screenshot(d, prefix='step'):
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(app.static_folder, 'screens', filename)
    d.screenshot(filepath)
    return url_for('static', filename=f'screens/{filename}', _external=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    audio_file.save(file_path)

    transcript = transcribe_audio(file_path)
    return jsonify({'transcript': transcript or "Could not transcribe"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get("message")
    context_prompt = context.get_context_prompt()
    logs = []

    try:
        intent_json = classify_user_intent(user_query, context_prompt)
        intent = json.loads(intent_json)
    except Exception as e:
        return jsonify({"response": "Sorry, intent classification failed."})

    if intent["intent_type"] == "insight":
        top_chunks = query_insights(user_query)
        response = answer_with_llm(user_query, top_chunks, context_prompt)
        context.add_turn(user_query, response)
        return jsonify({"response": response})

    query_embedding = generate_embedding(user_query)
    query_keywords = extract_keywords_with_llm(user_query, context_prompt)
    matched = get_best_match(user_query, query_embedding, query_keywords)
    plan = generate_detailed_steps(user_query, matched, context_prompt)
    session["high_level_plan"] = plan
    session["past_actions"] = []

    # Initial device setup and screenshot
    d = u2.connect()
    initial_img_url = save_screenshot(d, 'initial')

    first_action = get_next_action(plan, [], image_path=os.path.join(app.static_folder, 'screens', initial_img_url.split('/')[-1]), context_prompt=context_prompt)
    
    try:
        exec(first_action, {'d': d})
        next_img_url = save_screenshot(d, 'exec')
    except Exception as e:
        next_img_url = ''
        first_action = f"❌ Failed to execute first action: {str(e)}"

    session["past_actions"].append(first_action)

    response = f"🧠 Plan ready. First action executed."
    return jsonify({
        "response": response,
        "logs": logs,
        "image_url": initial_img_url,
        "next_action": first_action,
        "next_image": next_img_url
    })

@app.route('/next-action', methods=['POST'])
def next_action():
    d = u2.connect()
    plan = session.get("high_level_plan", "")
    past_actions = session.get("past_actions", [])
    context_prompt = context.get_context_prompt()

    img_url = save_screenshot(d, 'step')
    image_path = os.path.join(app.static_folder, 'screens', img_url.split('/')[-1])

    error_msg = None
    next_step = None
    max_retries = 3

    for attempt in range(max_retries):
        next_step = get_next_action(
            plan,
            past_actions,
            image_path=image_path,
            context_prompt=context_prompt,
            error_message=error_msg
        )

        print(f"Attempt {attempt + 1}: {next_step}")
        try:
            exec(next_step, {'d': d})
            next_img_url = save_screenshot(d, 'exec')
            break
        except Exception as e:
            error_msg = str(e)
            next_img_url = ""
            print(f"❌ Retry {attempt + 1}: {error_msg}")

            # OCR fallback logic on first retry
            if attempt == max_retries - 3 and 'text' in next_step:
                print("next_step:", next_step)
                match = re.search(r'(?:text|textContains|textMatches)\s*=\s*["\'](.*?)["\']', next_step)


                print(f"Regex match: {match}")
                if match:
                    clicked_text = match.group(1)
                    clicked_text = re.sub(r'\(\?i\)', '', clicked_text, flags=re.IGNORECASE)
                    clicked_text = re.sub(r'[.*?^$\\[\](){}|]', '', clicked_text)
                    clicked_text = clicked_text.strip()

                    coords = get_text_coordinates(image_path, clicked_text)
                    print(f"Clicked text: {clicked_text}, Coordinates: {coords}")
                    if coords:
                        x, y = coords
                        try:
                            d.click(x, y)
                            next_img_url = save_screenshot(d, 'exec')
                            next_step = f'd.click({x}, {y})  # OCR fallback for \"{clicked_text}\"'
                            break
                        except Exception as fallback_e:
                            error_msg = str(fallback_e)
                            print(f"⚠️ OCR Fallback also failed: {error_msg}")

            next_step = f"❌ Failed to execute: {error_msg}"

    else:
        print("❌ All retries failed.")

    past_actions.append(next_step)
    session["past_actions"] = past_actions

    return jsonify({
        "next_action": next_step,
        "image_url": img_url,
        "next_image": next_img_url
    })

@app.route('/reset', methods=['POST'])
def reset():
    context.clear()
    session.clear()
    return jsonify({"message": "Reset successfully."})

if __name__ == "__main__":
    os.makedirs(os.path.join(app.static_folder, 'screens'), exist_ok=True)
    app.run(debug=True)
