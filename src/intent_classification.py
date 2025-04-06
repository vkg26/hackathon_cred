from client import client

def classify_user_intent(user_query, context_prompt=""):
    prompt = f"""
You are an intelligent voice assistant that classifies user queries into structured intents.

Use the following past conversation for additional context if needed:
{context_prompt}

Now, classify the new user query below. Return a JSON with the following fields:
- query: original user query
- intent_type: "insight" or "action"
- intent_category: a specific label like "spending_analysis", "book_flight", "add_to_cart", etc.

Only return a well-formatted JSON. Do not include '''json''' or any other text.
User Query: "{user_query}"
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a precise and structured intent classifier."},
            {"role": "user", "content": prompt}
        ]
    )

    output = response.choices[0].message.content
    print("✅ Classified Intent:\n")
    print(output)
    return output
