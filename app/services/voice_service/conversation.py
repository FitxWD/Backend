from .diet_questions import get_diet_questions
from .fitness_questions import get_fitness_questions

# Store conversation state for each plan type
user_conversations = {}

def get_user_state(user_id="default", plan_type="diet"):
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
            "current_index": 0,
            "answers": {},
            "questions": questions,
            "plan_type": plan_type
        }
        print(f"Created new conversation state for {key} with {len(questions)} questions")
        print(f"Plan type: {plan_type}, First question: {questions[0] if questions else 'None'}")
    else:
        print(f"Using existing conversation state for {key}")
        print(f"Existing plan_type: {user_conversations[key]['plan_type']}")
    
    return user_conversations[key]

def get_next_prompt(user_text, user_id="default", plan_type="diet", llm_answer_func=None):
    """Get next question or generate plan when complete"""
    print(f"get_next_prompt called with plan_type: {plan_type}")
    
    state = get_user_state(user_id, plan_type)
    questions = state["questions"]
    
    print(f"Current state - Index: {state['current_index']}, Total questions: {len(questions)}")
    print(f"Questions type: {'fitness' if 'fitness level' in str(questions) else 'diet'}")
    print(f"Sample question: {questions[0] if questions else 'None'}")
    
    # If this is the first interaction (index 0), just return the first question
    if state["current_index"] == 0:
        current_question = questions[0]
        state["current_index"] = 1
        print(f"Returning first question: {current_question}")
        return current_question
    
    # Store the answer for the previous question
    if state["current_index"] > 0:
        prev_question_key = f"Q{state['current_index'] - 1}"
        state["answers"][prev_question_key] = user_text
        print(f"Stored answer for {prev_question_key}: {user_text}")

    # Check if we have more questions
    if state["current_index"] < len(questions):
        current_question = questions[state["current_index"]]
        
        # Check for side questions (optional)
        side_question_indicators = ["what", "how", "why", "can you", "tell me", "explain"]
        if any(indicator in user_text.lower() for indicator in side_question_indicators):
            if llm_answer_func:
                side_answer = llm_answer_func(user_text, current_question)
                state["current_index"] += 1
                return f"{side_answer}\n\nNow, {current_question}"
        
        # Move to next question
        state["current_index"] += 1
        print(f"Returning question {state['current_index'] - 1}: {current_question}")
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

def reset_conversation(user_id="default", plan_type="diet"):
    """Reset conversation state"""
    key = f"{user_id}_{plan_type}"
    if key in user_conversations:
        del user_conversations[key]
        print(f"Reset conversation for {key}")

def get_user_answers(user_id="default", plan_type="diet"):
    """Get all user answers"""
    state = get_user_state(user_id, plan_type)
    return state["answers"]