import os
import json
from voice import transcribe_audio
from embedding_utils import generate_embedding
from rrf import get_best_match, extract_keywords_with_llm
from step_utils import get_next_action, generate_detailed_steps
from intent_classification import classify_user_intent
from insight_provider import query_insights, answer_with_llm
from client import client

AUDIO_PATH = r"C:\Users\Admin\Downloads\hackathon_cred\marathi_audio.mp3"
MATCHED_RESULT_PATH = "data/matched_result.json"
SCREENSHOT_PATH = "data/prediction_Screenshots"  # demo folder

def get_screen_description_from_image_path(image_path):
    print(f"🖼️ Describing image: {image_path}")
    
    with open(image_path, "rb") as img_file:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that describes mobile app screens."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is shown on this mobile app screen? Describe it briefly."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_file.read().encode('base64').decode()}"}}
                    ]
                }
            ]
        )

    description = response.choices[0].message.content.strip()
    print(f"📄 LLM-generated screen description: {description}")
    return description

def main():
    context_prompt = ""  # Start empty

    print("\n🔊 Step 1: Transcribing Audio...")
    user_query = transcribe_audio(AUDIO_PATH)
    if not user_query:
        print("❌ Transcription failed. Exiting.")
        return
    print(f"\n🧠 Transcribed Query: {user_query}")

    print("\n🧭 Step 2: Classifying Intent...")
    intent_json = classify_user_intent(user_query, context_prompt)
    intent = json.loads(intent_json)
    print(f"\n🎯 Intent Type: {intent['intent_type']} | Category: {intent['intent_category']}")

    if intent["intent_type"] == "insight":
        print("\n🔍 Fetching insight from structured user data...")
        top_chunks = query_insights(user_query)
        answer = answer_with_llm(user_query, top_chunks, context_prompt)
        print("\n💡 Insight Response:\n")
        print(answer)

        # Update context
        context_prompt += f"User: {user_query}\nAssistant: {answer}\n"
        return

    print("\n🔍 Step 3: RAG Matching from Past Queries...")
    query_embedding = generate_embedding(user_query)
    query_keywords = set([kw.lower() for kw in extract_keywords_with_llm(user_query, context_prompt)])
    matched = get_best_match(user_query, query_embedding, query_keywords)

    print("\n✅ Top Matched Past Query:")
    print(f"> {matched['query']}")

    with open(MATCHED_RESULT_PATH, "w") as f:
        json.dump(matched, f, indent=2)

    print("\n🛠️ Step 4: Generating High-Level Steps...")
    steps_text = generate_detailed_steps(user_query, matched, context_prompt)
    steps_list = [line.strip("1234567890. ").strip() for line in steps_text.splitlines() if line.strip()]

    print("\n🎮 Step 5: Iterative Execution Using LLM + Screen Context...\n")

    past_actions = []

    for idx in range(len(steps_list)):  # simulate up to N steps
        image_file = os.path.join(SCREENSHOT_PATH, f"step{idx}.png")
        screen_description = get_screen_description_from_image_path(image_file)

        print(f"\n🖼️ Using Screenshot: {image_file}")
        print(f"📄 Screen Description: {screen_description}")

        next_action = get_next_action(
            high_level_plan=steps_text,
            past_actions=past_actions,
            screen_description=screen_description,
            context_prompt=context_prompt
        )

        print(f"🪜 Next Action: {next_action}")
        past_actions.append(next_action)

        input("🔁 Press Enter to simulate next screen...\n")

    print("\n✅ Task simulation complete!")

if __name__ == "__main__":
    main()
