from .diet_questions import get_diet_questions
from .fitness_questions import get_fitness_questions
import re

# Store conversation state for each plan type
user_conversations = {}

def get_user_state(user_id, plan_type="diet"):
    """Get or create user conversation state"""
    print(f"get_user_state called with user_id={user_id}, plan_type={plan_type}")
    
    key = f"{user_id}_{plan_type}"
    if key not in user_conversations:
        # Get the correct questions based on plan type
        if plan_type == "fitness":
            questions = get_fitness_questions()
            print(f"Loading FITNESS questions: {len(questions)} total")
        else:
            questions = get_diet_questions()
            print(f"Loading DIET questions: {len(questions)} total")
            
        user_conversations[key] = {
            "current_index": -1,  # Start at -1 to handle greeting first
            "answers": {},
            "questions": questions,
            "plan_type": plan_type,
            "greeted": False,
            "validation_attempts": 0  # Track validation attempts for current question
        }
        print(f"Created new conversation state for {key} with {len(questions)} questions")
        print(f"Plan type: {plan_type}, First question: {questions[0] if questions else 'None'}")
    else:
        print(f"Using existing conversation state for {key}")
        print(f"Existing plan_type: {user_conversations[key]['plan_type']}")
    
    return user_conversations[key]

def get_question_validation_rules(question_index, plan_type):
    """Define validation rules for each question"""
    
    if plan_type == "fitness":
        fitness_rules = {
            0: {"type": "number", "min": 16, "max": 100, "field": "age"},  # Age
            1: {"type": "choice", "choices": ["male", "female", "other", "m", "f"], "field": "gender"},  # Gender
            2: {"type": "number", "min": 100, "max": 250, "field": "height"},  # Height in cm
            3: {"type": "number", "min": 30, "max": 300, "field": "weight"},  # Weight in kg
            4: {"type": "number", "min": 0, "max": 24, "field": "sleep_hours"},  # Sleep hours
            5: {"type": "number", "min": 0, "max": 10, "field": "water_intake"},  # Water intake in litres
            6: {"type": "number", "min": 0, "max": 50000, "field": "daily_steps"},  # Daily steps
            7: {"type": "number", "min": 40, "max": 150, "field": "resting_heart_rate", "optional": True},  # Resting HR (optional)
            8: {"type": "number", "min": 80, "max": 200, "field": "systolic_bp", "optional": True},  # Systolic BP (optional)
            9: {"type": "number", "min": 50, "max": 130, "field": "diastolic_bp", "optional": True},  # Diastolic BP (optional)
            10: {"type": "choice", "choices": ["beginner", "intermediate", "advanced"], "field": "fitness_level"},
            11: {"type": "number", "min": 0, "max": 180, "field": "workout_duration"},  # Duration (0 for no workouts)
            12: {"type": "choice", "choices": ["low", "moderate", "high"], "field": "intensity"},
            13: {"type": "choice", "choices": ["low", "average", "high"], "field": "endurance"},
            14: {"type": "number", "min": 1, "max": 10, "field": "stress_level"},  # Stress level 1-10
            15: {"type": "choice", "choices": ["current smoker", "former smoker", "non-smoker"], "field": "smoking"},
            16: {"type": "text", "field": "health_conditions"}  # Health conditions - free text
        }
        return fitness_rules.get(question_index)
    
    else:  # diet
        diet_rules = {
            0: {"type": "number", "min": 16, "max": 100, "field": "age"},  # Age
            1: {"type": "choice", "choices": ["male", "female", "other", "m", "f"], "field": "gender"},  # Gender
            2: {"type": "number", "min": 100, "max": 250, "field": "height"},  # Height in cm
            3: {"type": "number", "min": 30, "max": 300, "field": "weight"},  # Weight in kg
            4: {"type": "text", "field": "health_conditions"},  # Health conditions - free text
            5: {"type": "choice", "choices": ["mild", "moderate", "severe"], "field": "condition_severity"},  # Severity
            6: {"type": "choice", "choices": ["sedentary", "moderate", "active"], "field": "activity_level"},
            7: {"type": "number", "min": 100, "max": 400, "field": "cholesterol_level", "optional": True},  # Cholesterol (optional)
            8: {"type": "text", "field": "blood_pressure", "optional": True},  # Blood pressure (optional, format varies)
            9: {"type": "number", "min": 60, "max": 400, "field": "glucose_level", "optional": True},  # Glucose (optional)
            10: {"type": "text", "field": "dietary_restrictions"},  # Dietary restrictions - free text
            11: {"type": "text", "field": "food_allergies"},  # Food allergies - free text
            12: {"type": "choice", "choices": ["mexican", "indian", "chinese", "italian"], "field": "cuisine_preference"},
            13: {"type": "number", "min": 0, "max": 50, "field": "exercise_hours_per_week"}  # Exercise hours per week
        }
        return diet_rules.get(question_index)
    
    return None

def validate_answer(answer, validation_rule):
    """Validate user answer against rules"""
    if not validation_rule:
        return True, answer, ""  # No validation needed
    
    answer_clean = answer.strip().lower()
    rule_type = validation_rule["type"]
    field = validation_rule["field"]
    is_optional = validation_rule.get("optional", False)
    
    # Handle optional fields - accept "don't know", "not sure", "no", etc.
    if is_optional:
        optional_responses = [
            "don't know", "dont know", "not sure", "unsure", "no", "none", 
            "i don't know", "i dont know", "i'm not sure", "im not sure",
            "no idea", "not available", "n/a", "na", "unknown", "unclear",
            "that's fine", "thats fine", "no worries", "that's okay", "thats okay"
        ]
        if any(resp in answer_clean for resp in optional_responses):
            return True, "unknown", ""
    
    if rule_type == "number":
        # Extract number from text
        numbers = re.findall(r'\d+\.?\d*', answer)
        if not numbers:
            if is_optional:
                return True, "unknown", ""
            return False, answer, f"Please provide a number for {field}."
        
        try:
            number = float(numbers[0])
            min_val = validation_rule.get("min", float('-inf'))
            max_val = validation_rule.get("max", float('inf'))
            
            if number < min_val or number > max_val:
                return False, answer, f"Please provide a {field} between {min_val} and {max_val}."
            
            # Return the number as string for consistency
            return True, str(number), ""
            
        except ValueError:
            return False, answer, f"Please provide a valid number for {field}."
    
    elif rule_type == "choice":
        choices = validation_rule["choices"]
        # Check if answer contains any of the valid choices
        # Prefer whole-word matches and favor longer choices (so "female" doesn't match "male")
        for choice in sorted(choices, key=lambda x: -len(x)):
            pattern = r'\b' + re.escape(choice.lower()) + r'\b'
            if re.search(pattern, answer_clean):
                return True, choice, ""  # Return the matched choice
        
        choices_str = ", ".join(choices)
        return False, answer, f"Please choose from: {choices_str}"
    
    elif rule_type == "text":
        # Text answers are always valid, but check if not empty
        if len(answer.strip()) == 0:
            return False, answer, f"Please provide an answer for {field}."
        return True, answer, ""
    
    return True, answer, ""

def is_side_question(user_text):
    """Detect if user is asking a side question instead of answering"""
    user_lower = user_text.lower().strip()
    
    # Extensive list of side question indicators
    side_question_indicators = [
        # Question words
        "what", "how", "why", "when", "where", "which", "who", "whose",
        "what's", "how's", "why's", "when's", "where's", "who's",
        "what is", "how is", "why is", "when is", "where is", "which is",
        "what are", "how are", "why are", "when are", "where are",
        "what does", "how does", "why does", "when does", "where does",
        "what do", "how do", "why do", "when do", "where do",
        "what will", "how will", "why will", "when will", "where will",
        "what would", "how would", "why would", "when would", "where would",
        "what can", "how can", "why can", "when can", "where can",
        "what could", "how could", "why could", "when could", "where could",
        "what should", "how should", "why should", "when should", "where should",
        "what might", "how might", "why might", "when might", "where might",
        "what may", "how may", "why may", "when may", "where may",
        
        # Direct question phrases
        "can you", "could you", "would you", "will you", "should you",
        "do you", "did you", "have you", "are you", "were you",
        "is it", "are they", "was it", "were they",
        "tell me", "explain", "describe", "define", "clarify",
        "tell me about", "explain to me", "help me understand",
        "i want to know", "i need to know", "i'm curious about",
        "i wonder", "i'm wondering", "wondering about",
        "i don't understand", "i don't know", "i'm confused",
        "i'm not sure", "not sure about", "unclear about",
        
        # Information seeking
        "more about", "more information", "additional info",
        "details about", "information on", "info about",
        "learn about", "know more", "find out",
        "research", "study", "investigate",
        
        # Help requests
        "help", "assist", "guide", "advise", "recommend",
        "help me", "assist me", "guide me", "advise me",
        "help with", "assist with", "guidance on",
        "need help", "need assistance", "need guidance",
        "could use help", "looking for help",
        
        # Comparison and evaluation
        "difference between", "compare", "comparison",
        "better", "worse", "best", "worst", "prefer",
        "which one", "what's better", "what's worse",
        "pros and cons", "advantages", "disadvantages",
        "benefits", "drawbacks", "side effects",
        
        # Health and fitness specific
        "calories", "nutrition", "protein", "carbs", "fat",
        "exercise", "workout", "training", "muscle",
        "weight loss", "weight gain", "diet", "meal",
        "supplement", "vitamin", "mineral",
        "cardio", "strength", "flexibility", "endurance",
        "injury", "pain", "recovery", "rest",
        
        # Time and frequency
        "how often", "how long", "how much", "how many",
        "frequency", "duration", "amount", "quantity",
        "daily", "weekly", "monthly", "per day", "per week",
        
        # Methods and processes
        "how to", "way to", "method", "process", "procedure",
        "steps", "instructions", "guide", "tutorial",
        "technique", "approach", "strategy",
        
        # Uncertainty expressions
        "maybe", "perhaps", "possibly", "probably",
        "i think", "i believe", "i assume", "i guess",
        "it seems", "appears", "looks like",
        "not certain", "not confident", "unsure",
        
        # Question endings
        "right?", "correct?", "true?", "isn't it?", "aren't they?",
        "doesn't it?", "don't they?", "?"
    ]
    
    # Check if the text contains any side question indicators
    contains_indicator = any(indicator in user_lower for indicator in side_question_indicators)
    
    # Additional checks for question structure
    ends_with_question = user_text.strip().endswith('?')
    starts_with_question_word = any(user_lower.startswith(word) for word in 
                                   ["what", "how", "why", "when", "where", "which", "who", "can", "could", "would", "will", "should", "do", "did", "are", "is"])
    
    # More sophisticated detection
    is_question = contains_indicator or ends_with_question or starts_with_question_word
    
    # Exclude simple answers that might contain question words
    simple_answers = ["i don't know", "not sure", "maybe", "yes", "no", "none"]
    is_simple_answer = user_lower in simple_answers or len(user_text.split()) <= 3
    
    result = is_question and not is_simple_answer
    
    if result:
        print(f"🤔 Detected side question: '{user_text}'")
        print(f"   - Contains indicator: {contains_indicator}")
        print(f"   - Ends with ?: {ends_with_question}")
        print(f"   - Starts with question word: {starts_with_question_word}")
    
    return result

def answer_side_question_with_rag(user_question):
    """Use RAG service to answer side questions"""
    try:
        print(f"🔍 Using RAG to answer side question: '{user_question}'")
        
        # Import RAG service
        from app.services.rag_service.rag import get_rag_service
        
        # Get RAG service instance
        rag_service = get_rag_service()
        
        # Query the RAG service
        result = rag_service.hybrid_rag_answer(query=user_question, top_k=3)
        
        if result["source"] == "none":
            # If RAG doesn't have an answer, provide a helpful response
            print("❌ RAG couldn't find relevant information")
            return "I don't have specific information about that in my knowledge base. Let's continue with the questions so I can help you with your personalized plan."
        else:
            print(f"✅ RAG found answer from source: {result['source']}")
            return result["answer"]
            
    except Exception as e:
        print(f"❌ Error using RAG service: {str(e)}")
        return "I'm having trouble accessing my knowledge base right now. Let's continue with the questions to create your personalized plan."

def get_next_prompt(user_text, user_id, plan_type="diet", llm_answer_func=None):
    """Get next question or generate plan when complete"""
    print(f"get_next_prompt called with plan_type: {plan_type}")
    print(f"User said: {user_text}")
    
    state = get_user_state(user_id, plan_type)
    questions = state["questions"]
    
    print(f"Current state - Index: {state['current_index']}, Total questions: {len(questions)}")
    print(f"Greeted: {state.get('greeted', False)}")
    print(f"Validation attempts: {state.get('validation_attempts', 0)}")
    
    # Handle initial greeting
    if state["current_index"] == -1 and not state.get("greeted", False):
        greeting_words = ["hi", "hello", "hey", "start", "begin", "good morning", "good afternoon", "good evening"]
        user_lower = user_text.lower().strip()
        
        if any(word in user_lower for word in greeting_words):
            state["greeted"] = True
            if plan_type == "fitness":
                return "Hi! I'm your fitness assistant. I'll help recommend a personalized workout plan for you. May I ask you a few quick questions to get started?"
            else:  # diet
                return "Hi! I'm your nutrition assistant. I'll help recommend a personalized diet plan for you. May I ask you a few quick questions to get started?"
        else:
            # If they don't greet properly, prompt them
            if plan_type == "fitness":
                return "Hello! I'm your fitness assistant. Say 'hi' or 'hello' to get started with your personalized workout plan!"
            else:
                return "Hello! I'm your nutrition assistant. Say 'hi' or 'hello' to get started with your personalized diet plan!"
    
    # Handle user confirmation after greeting
    if state["current_index"] == -1 and state.get("greeted", False):
        confirmation_words = ["yes", "yeah", "sure", "okay", "ok", "go ahead", "continue", "start", "let's go", "proceed"]
        user_lower = user_text.lower().strip()
        
        if any(word in user_lower for word in confirmation_words):
            # User confirmed, start with first question
            state["current_index"] = 0
            state["validation_attempts"] = 0
            current_question = questions[0]
            print(f"User confirmed, starting with first question: {current_question}")
            return current_question
        else:
            # User didn't confirm, ask again
            if plan_type == "fitness":
                return "Great! Just say 'yes' or 'sure' when you're ready to start answering questions for your fitness plan."
            else:
                return "Great! Just say 'yes' or 'sure' when you're ready to start answering questions for your diet plan."
    
    # Normal question flow
    if state["current_index"] >= 0:
        # Check if this is a side question before processing as an answer
        if is_side_question(user_text):
            print(f"🤔 Processing side question: {user_text}")
            
            # Answer the side question using RAG
            side_answer = answer_side_question_with_rag(user_text)
            
            # Return the RAG answer + repeat current question
            current_question = questions[state["current_index"]]
            return f"{side_answer}\n\nNow, let's get back to your plan. {current_question}"
        
        # Validate the answer
        validation_rule = get_question_validation_rules(state["current_index"], plan_type)
        is_valid, validated_answer, error_message = validate_answer(user_text, validation_rule)
        
        if not is_valid:
            print(f"❌ Invalid answer: {error_message}")
            
            # Increment validation attempts
            state["validation_attempts"] = state.get("validation_attempts", 0) + 1
            
            # Provide different messages based on attempts
            if state["validation_attempts"] == 1:
                return f"{error_message} Please try again."
            elif state["validation_attempts"] == 2:
                return f"{error_message} Let me ask again: {questions[state['current_index']]}"
            elif state["validation_attempts"] >= 3:
                # After 3 attempts, provide more detailed help
                current_question = questions[state["current_index"]]
                if validation_rule["type"] == "number":
                    min_val = validation_rule.get("min", "any")
                    max_val = validation_rule.get("max", "any")
                    return f"{error_message} Please provide just a number between {min_val} and {max_val}. For example: '25' or 'twenty-five'. Let me ask again: {current_question}"
                elif validation_rule["type"] == "choice":
                    choices = ", ".join(validation_rule["choices"])
                    return f"Please choose one of these options: {choices}. Let me ask again: {current_question}"
                else:
                    return f"{error_message} Let me ask again: {current_question}"
            else:
                return f"{error_message}"
        
        # Answer is valid - store it and move to next question
        print(f"✅ Valid answer: {validated_answer}")
        
        # Store the validated answer
        question_key = f"Q{state['current_index']}"
        state["answers"][question_key] = validated_answer
        print(f"Stored answer for {question_key}: {validated_answer}")
        
        # Reset validation attempts for next question
        state["validation_attempts"] = 0

        # Move to next question index
        next_index = state["current_index"] + 1
        
        # Check if we have more questions
        if next_index < len(questions):
            current_question = questions[next_index]
            
            # Move to next question
            state["current_index"] = next_index
            print(f"Returning question {state['current_index']}: {current_question}")
            return current_question
        
        # All questions answered - generate plan
        user_answers = state["answers"]
        plan_type = state["plan_type"]
        
        print(f"All questions answered for {plan_type} plan")
        print(f"User answers: {user_answers}")
        
        # Import here to avoid circular imports
        from .plan_generator import generate_diet_plan, generate_fitness_plan, format_plan_response
        
        if plan_type == "fitness":
            plan = generate_fitness_plan(user_answers)
            plan_text = format_plan_response(plan, "fitness")
            return f"Thanks! I have all the information I need. Your personalized fitness plan is now being generated. PLease visit dashboard to view it."
        else:
            plan = generate_diet_plan(user_answers)
            plan_text = format_plan_response(plan, "diet")
            return f"Thanks! I have all the information I need. Your personalized diet plan is now being generated. Please visit dashboard to view it."

    # Fallback - shouldn't reach here
    return "I'm sorry, something went wrong. Please say 'hi' to start over."

def reset_conversation(user_id, plan_type="diet"):
    """Reset conversation state"""
    key = f"{user_id}_{plan_type}"
    if key in user_conversations:
        del user_conversations[key]
        print(f"Reset conversation for {key}")

def get_user_answers(user_id, plan_type="diet"):
    """Get all user answers"""
    state = get_user_state(user_id, plan_type)
    return state["answers"]