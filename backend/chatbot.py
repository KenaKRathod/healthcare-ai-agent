def health_chatbot(user_input):

    user_input = user_input.lower()

    if "medicine" in user_input:
        return "You can add medicine reminders in the medication section."

    elif "health" in user_input:
        return "Remember to drink water, exercise, and take medicines on time."

    elif "hello" in user_input:
        return "Hello! I'm your healthcare assistant."

    elif "fever" in user_input:
        return "If you have fever, rest well and consult a doctor if it persists."

    else:
        return "I'm here to help with medication reminders and basic health advice."