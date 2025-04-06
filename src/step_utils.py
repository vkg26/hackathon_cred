import json
import mimetypes
import base64
from client import client
from pathlib import Path
import pytesseract
from PIL import Image

# === HIGH LEVEL PLAN GENERATOR ===

def generate_detailed_steps(user_query, matched, context_prompt=""):
    system_msg = {
        "role": "system",
        "content": "You are a helpful assistant for mobile app automation. Generate high-level steps to complete the user's task. Use the matched example as inspiration."
    }

    example = f"User Query: {matched['query']}\nSteps:\n"
    for step in matched["steps"]:
        example += f"- {step['action']}\n"

    user_msg = {
        "role": "user",
        "content": (
            f"User Query: {user_query}\n"
            f"Matched Example:\n{example}\n"
            f"Instructions:\nGenerate a list of short and clear steps to accomplish the user query."
        )
    }

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[system_msg, user_msg]
    )

    return response.choices[0].message.content.strip()

# === NEXT ACTION GENERATOR ===

def get_next_action(high_level_plan, past_actions, screen_description=None, image_path=None, context_prompt="", error_message=None):
    base_prompt = """
You are a smart mobile automation agent. Your task is to generate an accurate next action for the UIAutomator2 framework to interact with an Android application, based on:
- The current screen description or screenshot
- A high-level plan of steps
- Past actions already taken
- An optional error from the previous failed step

Your response MUST be a valid Python code snippet (no markdown!) compatible with uiautomator2, using actions like:
- d(text="Text").click() — tap an element by visible text
- d(textContains="partial").wait(timeout=10) — wait for a partial text
- d(resourceId="com.example:id/element").click() — click by resource ID
- d.set_fastinput_ime(True); d.send_keys("some text") — enter text
- d.press("home") or d.press("back") — navigation
- d.screenshot("path") — take screenshot (not required in your step)

Important Rules:
- Combine `.wait()` before `.click()` to ensure the element is present.
- DO NOT guess. Base actions on the actual visible text or UI.
- Use `textMatches="(?i).*partial.*"` for case-insensitive robustness.
- Never wrap actions in markdown (```).

### FEW-SHOT EXAMPLES:

Query: "Add Dell laptop to cart in Flipkart"
Plan: [Tap Electronics], [Go to Laptops], [Tap Dell Vostro tile], [Open Dell Vostro 3520], [Go to cart]

Screen: Flipkart home with Grocery, Fashion, Electronics...
d(textContains="Electronics").wait(timeout=10); d(textContains="Electronics").click()

Screen: Laptops promo section
d(textContains="Laptops").wait(timeout=10); d(textContains="Laptops").click()

Screen: Dell Vostro product tile
d(textContains="Vostro").wait(timeout=10); d(textContains="Vostro").click()

Screen: Dell 3520 search result
d(textContains="3520").wait(timeout=10); d(textContains="3520").click()

Screen: 'Go to Cart' confirmation
d(textContains="GO TO CART").wait(timeout=10); d(textContains="GO TO CART").click()

--- END OF EXAMPLES ---

Now, generate the next best action to complete the plan.
Use multiple lines if needed. No markdown. Be reliable.
"""

    plan_part = f"\n\n=== HIGH-LEVEL PLAN ===\n{high_level_plan.strip()}"
    past_part = f"\n\n=== PAST ACTIONS ===\n{json.dumps(past_actions, indent=2)}"
    error_part = f"\n\n=== LAST ERROR ===\n{error_message}" if error_message else ""

    full_prompt = base_prompt + plan_part + past_part + error_part

    system_msg = {
        "role": "system",
        "content": "You are a helpful assistant that generates precise mobile automation actions using uiautomator2."
    }

    if image_path:
        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type = mime_type or "image/png"

        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        messages = [
            system_msg,
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}}
                ]
            }
        ]
    else:
        full_prompt += f"\n\n=== SCREEN DESCRIPTION ===\n{screen_description or '(none)'}"
        messages = [system_msg, {"role": "user", "content": full_prompt}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    try:
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ LLM Response Error:", response)
        return "⚠️ LLM failed to respond with a valid action."


# === OCR MATCHER FOR FALLBACK COORDINATE CLICKS ===

def get_text_coordinates(image_path, text):
    """Use OCR to find coordinates of the text on screen."""
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    for i in range(len(data['text'])):
        if text.lower() in data['text'][i].lower():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            center_x = x + w // 2
            center_y = y + h // 2
            return (center_x, center_y)
    return None


def retry_with_coordinates(action, image_path):
    """
    If original action fails, try parsing it.
    If it's a d(text=...).click(), get the text and use OCR to find coordinates and tap.
    """
    import re
    match = re.search(r'd\(text(?:Contains)?="([^"]+)"\).*\.click\(\)', action)
    if match:
        text_to_find = match.group(1)
        coords = get_text_coordinates(image_path, text_to_find)
        if coords:
            x, y = coords
            return f'd.click({x}, {y})'
    return None

