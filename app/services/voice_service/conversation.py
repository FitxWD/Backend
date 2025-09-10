import re

questions = [
    "First, may I know your age?",
    "What is your gender? (Male, Female, or Other)",
    "Could you tell me your height in centimeters?",
    "And your weight in kilograms?",
    "Do you have any health conditions such as hypertension, diabetes, or obesity?",
    "How would you describe the severity of your condition? (Mild, Moderate, or Severe)",
    "How active are you in your daily life? (Sedentary, Moderate, or Active)",
    "On average, how many calories do you eat per day? If you’re not sure, that’s okay—just let me know.",
    "What is your cholesterol level in mg/dL? If you don’t know, that’s fine, but sharing it helps me make a more accurate plan.",
    "What is your blood pressure in mmHg? If you’re unsure, no worries—just let me know.",
    "What is your glucose level in mg/dL? If you don’t know, that’s okay.",
    "Do you have any dietary restrictions, such as low sodium or low sugar?",
    "Are you allergic to any foods, like gluten or peanuts?",
    "What type of cuisine do you prefer? (Mexican, Indian, Chinese, or Italian)",
    "How many hours do you exercise per week?"
]

conversation_state = {
    "current_index": -1,
    "answers": {},
    "started": False
}

def is_user_question(text):
    """Detect if user input is a question."""
    text = text.strip().lower()
    return (
        text.endswith("?") or
        text.startswith(("what", "why", "how", "when", "where", "who"))
    )

def get_next_prompt(user_text, llm_answer_func=None):
    if not conversation_state["started"]:
        conversation_state["started"] = True
        conversation_state["current_index"] = -1
        return "Hi! I’m your wellness assistant. I’ll help recommend a diet plan. May I ask you a few quick questions?"

    if conversation_state["current_index"] == -1:
        conversation_state["current_index"] = 0
        return questions[0]

    idx = conversation_state["current_index"]

    if is_user_question(user_text):
        if llm_answer_func:
            answer = llm_answer_func(user_text, questions[idx])
            return f"{answer}\n\nWhen you're ready, could you please answer: {questions[idx]}"
        else:
            return f"That's a good question!\n\nWhen you're ready, could you please answer: {questions[idx]}"

    conversation_state["answers"][f"Q{idx+1}"] = user_text
    conversation_state["current_index"] += 1

    if conversation_state["current_index"] < len(questions):
        return questions[conversation_state["current_index"]]
    else:
        return "Thanks! I have all the information I need. I’ll now generate your diet recommendation plan."
