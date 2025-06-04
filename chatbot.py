import openai
import os
import re

# Set up the Azure OpenAI API key and endpoint
openai.api_type = "azure"
openai.api_key="5mOKzsEcttZmsVPuapJqwDynFvAHVjdlpM6KBJs1RvV0SWIx5sebJQQJ99BFAC77bzfXJ3w3AAAAACOG0KBx"
openai.azure_endpoint="https://varad1.openai.azure.com/"
openai.api_version = "2025-01-01-preview"

system_prompt = """You are a helpful assistant that collects customer details in order to
recommend them the right credit card. Ask ONE question at a time from the following list, and wait for the user's response.
After each response, save it in the appropriate category and ask the next question. Format your responses naturally but consistently.

Questions and valid options:
1. What type of rewards do you prefer?
Options: Cashback, Travel Miles, Shopping Points, Fuel Benefits, Other

2. How much do you typically spend each month on your credit card?
Options: Less than 10000, 10000-25000, 25000-50000, more than 50k

3. Which categories do you spend most on? (select top 2)?
Options: Dining, Fuel, Groceries, Online Shopping, Travel, Utilities, Entertainment

4. How important is a low interest rate (APR) to you?
Options: Very Important, Somewhat Important, Not Important

5. Do you usually pay your full balance each month or carry a balance?
Options: Always pay in full, Sometimes carry a balance, Often carry a balance

6. Are you concerned about late fees or missed payments?
Options: Yes, I want reminders and fee waivers OR No, I manage payments well

7. Do you travel frequently (domestic or international)?
Options: Yes-Both, Yes-Domestic only, No

8. Are you interested in co-branded cards (e.g. airlines, retail stores)?
Options: Yes, No preference, No

9. Do you prefer cards with annual fees if benefits are high?
Options: Yes, if value>fee | No annual fees only | Depends on benefits

10. What matters most in a credit card for you?
Options: Maximizing rewards, Saving on interest, Premium perks, Simplicity

After collecting all responses, provide a summary of the customer's preferences."""

def extract_spending_categories(text):
    categories = ["Dining", "Fuel", "Groceries", "Online Shopping", "Travel", "Utilities", "Entertainment"]
    found_categories = []
    for category in categories:
        if category.lower() in text.lower():
            found_categories.append(category)
    return found_categories[:2]  # Return only top 2 categories

def update_customer_data(user_input, customer_data, assistant_last_question):
    # Convert input and question to lowercase for easier matching
    input_lower = user_input.lower()
    
    # Update customer data based on the last question asked
    if "rewards do you prefer" in assistant_last_question.lower():
        options = ["cashback", "travel miles", "shopping points", "fuel benefits", "other"]
        for option in options:
            if option in input_lower:
                customer_data["rewards_preference"] = option.title()
                break
    
    elif "spend each month" in assistant_last_question.lower():
        if "less than 10000" in input_lower or "<10000" in input_lower:
            customer_data["monthly_spend"] = "Less than 10000"
        elif "10000-25000" in input_lower:
            customer_data["monthly_spend"] = "10000-25000"
        elif "25000-50000" in input_lower:
            customer_data["monthly_spend"] = "25000-50000"
        elif "more than 50k" in input_lower or ">50k" in input_lower:
            customer_data["monthly_spend"] = "More than 50k"
    
    elif "categories do you spend most" in assistant_last_question.lower():
        categories = extract_spending_categories(user_input)
        if categories:
            customer_data["top_spending_categories"] = categories
    
    elif "interest rate" in assistant_last_question.lower():
        if "very" in input_lower:
            customer_data["interest_rate_importance"] = "Very Important"
        elif "somewhat" in input_lower:
            customer_data["interest_rate_importance"] = "Somewhat Important"
        elif "not" in input_lower:
            customer_data["interest_rate_importance"] = "Not Important"
    
    elif "pay your full balance" in assistant_last_question.lower():
        if "always" in input_lower or "full" in input_lower:
            customer_data["balance_payment_habit"] = "Always pay in full"
        elif "sometimes" in input_lower:
            customer_data["balance_payment_habit"] = "Sometimes carry a balance"
        elif "often" in input_lower:
            customer_data["balance_payment_habit"] = "Often carry a balance"
    
    elif "late fees" in assistant_last_question.lower():
        if "yes" in input_lower or "reminder" in input_lower:
            customer_data["late_payment_concern"] = "Yes, wants reminders and fee waivers"
        elif "no" in input_lower or "manage" in input_lower:
            customer_data["late_payment_concern"] = "No, manages payments well"
    
    elif "travel frequently" in assistant_last_question.lower():
        if "both" in input_lower:
            customer_data["travel_frequency"] = "Yes-Both"
        elif "domestic" in input_lower:
            customer_data["travel_frequency"] = "Yes-Domestic only"
        elif "no" in input_lower:
            customer_data["travel_frequency"] = "No"
    
    elif "co-branded cards" in assistant_last_question.lower():
        if "yes" in input_lower:
            customer_data["cobranded_preference"] = "Yes"
        elif "no preference" in input_lower:
            customer_data["cobranded_preference"] = "No preference"
        elif "no" in input_lower:
            customer_data["cobranded_preference"] = "No"
    
    elif "annual fees" in assistant_last_question.lower():
        if "yes" in input_lower and "value" in input_lower:
            customer_data["annual_fee_preference"] = "Yes, if value exceeds fee"
        elif "no" in input_lower and "only" in input_lower:
            customer_data["annual_fee_preference"] = "No annual fees only"
        elif "depend" in input_lower:
            customer_data["annual_fee_preference"] = "Depends on benefits"
    
    elif "matters most" in assistant_last_question.lower():
        if "maximizing" in input_lower or "reward" in input_lower:
            customer_data["priority_feature"] = "Maximizing rewards"
        elif "interest" in input_lower or "saving" in input_lower:
            customer_data["priority_feature"] = "Saving on interest"
        elif "premium" in input_lower or "perk" in input_lower:
            customer_data["priority_feature"] = "Premium perks"
        elif "simple" in input_lower:
            customer_data["priority_feature"] = "Simplicity"
    
    return customer_data

def chatbot(user_input, conversation, customer_data):
    # Find the last assistant message to determine context
    assistant_last_question = ""
    for msg in reversed(conversation):
        if msg["role"] == "assistant":
            assistant_last_question = msg["content"]
            break
    
    # Update customer data based on user's response
    updated_data = update_customer_data(user_input, customer_data, assistant_last_question)
    
    # Get chatbot's response
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=conversation + [
            {'role': 'system', 'content': system_prompt}, 
            {"role": "user", "content": user_input}
        ],
        max_tokens=150,
        temperature=0.7
    )
    chatbot_response = response.choices[0].message.content
    
    # Return the response, updated conversation, and updated customer data
    return chatbot_response, conversation + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": chatbot_response}
    ], updated_data

if __name__ == "__main__":
    print("Welcome to the Credit Card Recommender Chatbot!")
    print("I will ask you for some details to assist you better.")



