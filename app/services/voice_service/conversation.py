from .diet_questions import get_diet_questions
from .fitness_questions import get_fitness_questions

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
            "greeted": False
        }
        print(f"Created new conversation state for {key} with {len(questions)} questions")
        print(f"Plan type: {plan_type}, First question: {questions[0] if questions else 'None'}")
    else:
        print(f"Using existing conversation state for {key}")
        print(f"Existing plan_type: {user_conversations[key]['plan_type']}")
    
    return user_conversations[key]

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
        
        # Store the answer for the current question
        question_key = f"Q{state['current_index']}"
        state["answers"][question_key] = user_text
        print(f"Stored answer for {question_key}: {user_text}")

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
            return f"Thanks! I have all the information I need. {plan_text}"
        else:
            plan = generate_diet_plan(user_answers)
            plan_text = format_plan_response(plan, "diet")
            return f"Thanks! I have all the information I need. {plan_text}"
    
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