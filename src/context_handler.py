# context_handler.py

class ConversationContext:
    def __init__(self, max_turns=5):
        self.history = []
        self.max_turns = max_turns

    def add_turn(self, user_query, response):
        self.history.append({"user": user_query, "bot": response})
        self.history = self.history[-self.max_turns:]

    def get_context_prompt(self):
        prompt = ""
        for turn in self.history:
            prompt += f"User: {turn['user']}\nAssistant: {turn['bot']}\n"
        return prompt.strip()

    def clear(self):
        self.history = []
