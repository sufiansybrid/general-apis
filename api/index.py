from flask import Flask, request
import json

app = Flask(__name__)

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
        num = request.args.get('num', default=1000000, type=int)

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
            "In Numbers:": f"{float(num):,}",  # Format the number with commas for readability
            "In Words:": capitalized_sentence  # The capitalized word form of the number
        }]

        # Return the result as a formatted JSON string (pretty-printed)
        return json.dumps(result, indent=2)

    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        return json.dumps(e)
