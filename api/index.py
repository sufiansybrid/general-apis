from flask import Flask, request, jsonify
import json
import re
from flask_cors import CORS

app = Flask(__name__)

CORS(app)  # Enable CORS for all route


@app.route('/')
def home():
    return 'Hello World'


@app.route('/about')
def about():
    return 'About'


@app.route('/number_to_words_with_formatting')
def number_to_words_with_formatting():
    """
    Converts a given number into words with proper formatting, including capitalizing each word 
    and returning the result in a JSON format.

    The endpoint accepts a query parameter 'num' in the URL. If 'num' is not provided, it defaults to 1000000.
    The function converts the number to words and capitalizes each word in the resulting string.

    Example:
        URL: "/number_to_words_with_formatting?num=1000000"
        Response: 
            {
                "In Numbers:": "1,000,000.0",
                "In Words:": "One Million"
            }

    Returns:
        str: A JSON string containing the formatted result with the number and its word form.

    Raises:
        Exception: If any error occurs during processing, an exception is returned as a JSON string.
    """
    try:
        # Get the 'num' parameter from the URL query string, defaulting to 1000000 if not present
        num = request.args.get('num', default=1000000, type=str)

        print(num)

        # Extract only the digits from the input
        num = ''.join(re.findall(r'\d', num))

        # Import the 'inflect' library to convert numbers to words
        import inflect
        p = inflect.engine()  # Create an inflect engine instance

        # Convert the number to words and capitalize the first letter of the sentence
        sentence = p.number_to_words(num)
        sentence = sentence.capitalize()

        # Split the sentence into words, then capitalize each word
        words = sentence.split()
        capitalized_words = [word.capitalize() for word in words]

        # Join the capitalized words back into a sentence
        capitalized_sentence = " ".join(capitalized_words)

        # Prepare the result as a dictionary with the number in both numeric and word form
        result = [{
            # Format the number with commas for readability
            "In Numbers:": f"{float(num):,}",
            "In Words:": capitalized_sentence  # The capitalized word form of the number
        }]

        # Return the result as a formatted JSON string (pretty-printed)
        return json.dumps(result, indent=2)

    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        return json.dumps(e)


@app.route('/chat', methods=['POST'])
def chat():
    # Predefined responses
    responses = {
        "hello": "Hi there! How can I help you?",
        "how are you": "I'm just a bot, but I'm here to help!",
        "what is your name": "I'm a chatbot created to assist you.",
        "why subscription fees was expired": """
            Your subscription fee may have expired due to the following reasons:\n

                1. Tenure Duration: The PSW User Subscription is valid for a period of two years. If you have not renewed your subscription within this timeframe, it will expire.\n

                2. Notification: The PSW system prompts users one month prior to the renewal date. If you did not take action during this notification period, your subscription would have expired.\n

                3. Failure to Renew: If you did not complete the renewal process, which includes making the renewal subscription fee payment and undergoing biometric verification, your subscription would not remain active.\n

                If you need to renew your subscription, please follow the steps outlined in the context provided.
                """,
        "bye": "Goodbye! Have a great day!",
    }
    try:
        user_message = request.json.get('question', '').lower()
        response = responses.get(
            user_message, "Sorry, I don't understand that.")
        return jsonify({"answer": response})
    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        return json.dumps(e)
