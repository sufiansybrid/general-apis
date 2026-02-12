from flask import Flask, request, jsonify, render_template
import json
import re
from flask_cors import CORS
import os
from bs4 import BeautifulSoup
import html
import pandas as pd

import requests

# app = Flask(__name__, template_folder='templates')
# Initialize Flask app with custom template folder path
app = Flask(__name__, template_folder=os.path.join(
    os.path.dirname(__file__), '..', 'templates'))

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
        # return json.dumps(result, indent=2)
        return jsonify(result)

    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        # return json.dumps(e)
        return jsonify({"error": str(e)}), 400


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


@app.route('/psw_stream')
def psw_stream():
    return render_template('index_stream.html')


@app.route('/psw')
def psw():
    return render_template('psw.html')


@app.route('/psw_home')
def psw_home():
    return render_template('psw_home.html')

@app.route('/ffc_home')
def ffc_home():
    return render_template('ffc_index.html')

@app.route('/api/owner-details', methods=['GET', 'POST'])
def get_owner_details():
    # Get number from query param or JSON body
    number = request.args.get('number') or request.json.get('number')

    if not number:
        return jsonify({"success": False, "error": "No phone number provided."}), 400

    HEADERS = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://dbcenter.pk',
        'referer': 'https://dbcenter.pk/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    payload = {
        'action': 'db_center_uk_search',
        'search_term': number
    }

    try:
        response = requests.post(
            'https://dbcenter.pk/wp-admin/admin-ajax.php',
            headers=HEADERS,
            data=payload,
            timeout=8
        )
        response.raise_for_status()
        html = response.text

        owner_details = {}

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Look through div with id='resultCard' and find 'Owner Details'
        owner_cards = soup.find('div', {'id': 'resultCard'})

        if owner_cards and "Owner Details" in owner_cards.text:
            try:
                rows = owner_cards.find_all('tr')
                for row in rows:
                    try:
                        key = row.find('th').text.strip().lower()
                        value = row.find('td').text.strip()
                        owner_details[key] = value
                    except AttributeError:
                        continue  # Skip rows with missing th or td
            except Exception as e:
                return jsonify({"success": False, "error": f"Error parsing owner details: {e}"}), 500
        else:
            return jsonify({"success": False, "error": "No owner details found for this number."}), 404

        return jsonify(owner_details)

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Request failed: {e}"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Request to external server timed out."}), 504


@app.route('/api/cnic-information', methods=['GET', 'POST'])
def cnic_information():
    # cnic = request.args.get('cnic') or (request.json and request.json.get('cnic'))
    # cnic = request.args.get('cnic') or (request.json and request.json.get('cnic'))
    cnic = request.args.get('cnic')
    if not cnic:
        return jsonify({"success": False, "error": "Missing CNIC number."}), 400

    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,en-GB;q=0.8,en-GB-oxendict;q=0.7,ur;q=0.6',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://dbcenter.pk',
        'priority': 'u=0, i',
        'referer': 'https://dbcenter.pk/cnic-information-system/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }

    payload = {'search_term': cnic}

    try:
        response = requests.post(
            'https://dbcenter.pk/cnic-information-system/', headers=HEADERS, data=payload, timeout=8)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', {'id': 'resultCard'})

        all_owner_details = []

        for card in cards:
            if 'Owner Details' in card.text:
                rows = card.find_all('tr')
                details = {}
                for row in rows:
                    try:
                        key = row.find('th').text.strip().lower()
                        value = row.find('td').text.strip()
                        details[key] = value
                    except AttributeError:
                        continue
                if details:
                    all_owner_details.append(details)

        if not all_owner_details:
            return jsonify({"success": False, "error": "No owner details found."}), 404

        return jsonify(all_owner_details)

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Request failed: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Request to external server timed out."}), 504

@app.route('/api/get-numbers-on-cnic-from-simownerdetails', methods=['GET'])
def get_numbers_on_cnic_from_simownerdetails():

    def parse_html(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        result_cards = soup.select('.result-card')
        records = []

        for card in result_cards:
            fields = card.select('.field')
            record = {}

            for field in fields:
                label = field.select_one('label.info')
                value = field.find('div')

                # print(f"label: {label.text} and value: {value.text}")
                if label and value:
                    key = label.text.strip().upper()
                    record[key] = value.text.strip()

            if record:
                records.append(record)

        return records

    cnic = request.args.get('cnic')

    if not cnic or not cnic.isdigit() or len(cnic) != 13:
        return jsonify({'success': False, 'error': 'A valid 13-digit CNIC without dashes is required'}), 400

    HEADERS = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,en-GB;q=0.8,en-GB-oxendict;q=0.7,ur;q=0.6',
        'local-cache': 'yes',
        'priority': 'u=1, i',
        'referer': 'https://simownerdetails.org.pk/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }

    BASE_URL = "https://simownerdetails.org.pk/wp-admin/admin-ajax.php"

    url = f"{BASE_URL}?action=get_number_data&get_number_data=searchdata={cnic}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        response.raise_for_status()

        json_data = json.loads(response.text)
        raw_html = html.unescape(json_data.get("data", ""))  # unescape HTML string

        parsed_data = parse_html(raw_html)

        if not parsed_data:
            return jsonify({'success': False, 'error': 'No data found'}), 404
        
        return jsonify({
            'success': True,
            'records_found': len(parsed_data),
            'data': parsed_data
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid JSON received'}), 500
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Request to external server timed out."}), 504

@app.route('/api/track-cnic', methods=['GET'])
def track_cnic():
    """
    Fetches CNIC tracking information from cnic.pk.
    
    Args:
        cnic_number (str): The CNIC number to track (without dashes).
    
    Returns:
        dict | str: JSON response from the server if successful, 
                    otherwise the raw HTML/text for debugging.
    """
    try:
        # Create a session to persist cookies
        session = requests.Session()

        # Step 1: GET the homepage to fetch a fresh CSRF token
        try:
            response = session.get('https://cnic.pk/')
            # response.raise_for_status()
        except Exception as e:
            return {"error": f"Failed to fetch CSRF token: {str(e)}"}
        # response = session.get('https://cnic.pk/')
        # response.raise_for_status()

        # Parse the HTML to find the CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token_input = soup.find('input', {'name': 'csrf_token'})
        if not csrf_token_input or not csrf_token_input.get('value'):
            raise ValueError("CSRF token not found on the page.")

        csrf_token = csrf_token_input['value']
        print(f"Fetched CSRF Token: {csrf_token}")

        # Step 2: Prepare POST data
        files = {
            'csrf_token': (None, csrf_token),
            'user_input': (None, request.args.get('cnic')),
        }

        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0',
            'referer': 'https://cnic.pk/',
        }

        # Step 3: POST using the same session
        post_response = session.post('https://cnic.pk/track', files=files, headers=headers)
        post_response.raise_for_status()

        # Try to return JSON if available
        try:
            return post_response.json()
        except ValueError:
            return post_response.text

    except Exception as e:
        return {"error": str(e)}

@app.route('/api/track_challan', methods=['GET'])
def track_challan() -> dict:
    """
    Track challan information from sindhpolice.gov.pk.
    
    Args:
        vehicle_number (str): Vehicle number, e.g. "KGI-6908".
        cnic_number (str): Optional CNIC number.
    
    Returns:
        dict: A structured response indicating success or failure.
    """

    vehicle_number = request.args.get('vehicle_number')
    cnic_number = request.args.get('cnic_number')
    if not vehicle_number:
        return {"status": "error", "message": "Vehicle number is required"}

    # Create a session to persist cookies

    session = requests.Session()

    # 1. GET — Fetch CSRF token
    try:
        r = session.get("https://sindhpolice.gov.pk/challan-check", timeout=15)
        r.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"Failed to load page: {e}"}

    soup = BeautifulSoup(r.text, "html.parser")
    meta_token = soup.find("meta", {"name": "csrf-token"})

    if not meta_token:
        return {"status": "error", "message": "CSRF token not found"}

    csrf_token = meta_token.get("content")
    print(f"Fetched CSRF Token: {csrf_token}")

    # 2. Correct POST endpoint
    post_url = "https://sindhpolice.gov.pk/challan-get"

    # 3. POST payload
    payload = {
        "_token": csrf_token,
        "vehicle": vehicle_number,
        "cnic": cnic_number
    }

    # 4. Required headers
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://sindhpolice.gov.pk/challan-check",
        "X-CSRF-TOKEN": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # 5. POST request
    try:
        response = session.post(post_url, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"POST request failed: {e}"}

    # 6. Interpret response
    text = response.text.strip()

    if "No records found" in text:
        return {"status": "not_found", "message": "No challan record found", "raw": text[:100]}

    return {"status": "found", "message": "Challan record found", "raw": text[:100]}

def scrape_prices(type: str) -> pd.DataFrame:
    """
    Scrape silver or gold price data from bullion-rates.com and perform analysis.
    Returns a pandas DataFrame with historical prices and calculated metrics.
    """
    try:
        # Fetch the webpage
        response = requests.get(
            f"https://id.bullion-rates.com/{type}/PKR-history.htm",
            timeout=10
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get the main price table
        table = soup.find("table", {"id": "dtDGrid"})
        
        if not table:
            raise ValueError("Price table not found on the page")
        
        # Extract data from table rows
        rows = []
        for row in table.find_all("tr", class_="DataRow"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                date = cols[0].text.strip()
                price_oz = cols[1].text.strip()
                price_gram = cols[2].text.strip()
                rows.append([date, price_oz, price_gram])
        
        if not rows:
            raise ValueError("No data rows found in the table")
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=["Date", f"{type}_Price_gram", f"{type}_Price_oz"])
        
        # Convert Date column
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y")
        
        # 🔹 Clean Silver_Price_gram (European format)
        df[f"{type}_Price_gram"] = (
            df[f"{type}_Price_gram"]
                .astype(str)
                .str.replace(".", "", regex=False)   # remove thousands dots
                .str.replace(",", ".", regex=False)  # convert decimal comma to dot
                .astype(float)
        )

        # 🔹 Clean Silver_Price_oz (dot = thousands)
        df[f"{type}_Price_oz"] = (
            df[f"{type}_Price_oz"]
                .astype(str)
                .str.replace(".", "", regex=False)   # remove thousands dots
                .astype(float)
        )
        
        # Sort by date (important for formulas like pct_change)
        df = df.sort_values("Date").reset_index(drop=True)
        
        # Calculate metrics
        df[f"Daily_Change_{type}_Price_oz"] = df[f"{type}_Price_oz"].diff().round(2)
        df[f"Daily_Change_{type}_Price_gram"] = df[f"{type}_Price_gram"].diff().round(2)
        df[f"Pct_Change_%"] = (df[f"{type}_Price_oz"].pct_change() * 100).round(2)
        df[f"MA_7"] = df[f"{type}_Price_oz"].rolling(window=7).mean().round(2)
        df[f"Volatility_7"] = df[f"{type}_Price_oz"].rolling(7).std().round(2)
        
        return df
        
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch data: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")


@app.route('/api/silver-prices', methods=['GET'])
def get_silver_prices():
    """
    API endpoint to get silver price data.
    
    Query parameters:
    - limit: Number of recent records to return (optional)
    - start_date: Filter records from this date onwards (format: YYYY-MM-DD, optional)
    - end_date: Filter records up to this date (format: YYYY-MM-DD, optional)
    
    Returns:
    JSON response with silver price data and calculated metrics
    """
    try:
        # Scrape and process data
        df = scrape_prices(type='Silver')
        
        # Get query parameters
        limit = request.args.get('limit', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Apply date filters if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['Date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df['Date'] <= end_dt]
        
        # Apply limit if provided (get most recent records)
        if limit:
            df = df.tail(limit)

        # Clean the DataFrame: convert all NaN to None
        df = df.fillna(0).replace({pd.NA: None, pd.NaT: None})
        
        # Convert Date to string format for JSON serialization
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        import math

        # Summary values with NaN handling
        latest_oz = df.iloc[-1]['Silver_Price_oz'] if len(df) > 0 else None
        latest_gram = df.iloc[-1]['Silver_Price_gram'] if len(df) > 0 else None

        avg_oz = df['Silver_Price_oz'].mean() if len(df) > 0 else None
        min_oz = df['Silver_Price_oz'].min() if len(df) > 0 else None
        max_oz = df['Silver_Price_oz'].max() if len(df) > 0 else None

        response_data = {
            'success': True,
            'record_count': len(df),
            "type": "Silver",
            'data': df.to_dict(orient='records'),
            'summary': {
                'latest_price_oz': None if latest_oz is None or math.isnan(latest_oz) else float(latest_oz),
                'latest_price_gram': None if latest_gram is None or math.isnan(latest_gram) else float(latest_gram),
                'latest_date': df.iloc[-1]['Date'] if len(df) > 0 else None,
                'avg_price_oz': None if avg_oz is None or math.isnan(avg_oz) else float(round(avg_oz, 2)),
                'min_price_oz': None if min_oz is None or math.isnan(min_oz) else float(min_oz),
                'max_price_oz': None if max_oz is None or math.isnan(max_oz) else float(max_oz),
            }
        }

        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gold-prices', methods=['GET'])
def get_gold_prices():
    """
    API endpoint to get gold price data.
    
    Query parameters:
    - limit: Number of recent records to return (optional)
    - start_date: Filter records from this date onwards (format: YYYY-MM-DD, optional)
    - end_date: Filter records up to this date (format: YYYY-MM-DD, optional)
    
    Returns:
    JSON response with gold price data and calculated metrics
    """
    try:
        # Scrape and process data
        df = scrape_prices(type='Gold')
        
        # Get query parameters
        limit = request.args.get('limit', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Apply date filters if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['Date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df['Date'] <= end_dt]
        
        # Apply limit if provided (get most recent records)
        if limit:
            df = df.tail(limit)

        # Clean the DataFrame: convert all NaN to None
        df = df.fillna(0).replace({pd.NA: None, pd.NaT: None})
        
        # Convert Date to string format for JSON serialization
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        import math

        # Summary values with NaN handling
        latest_oz = df.iloc[-1]['Gold_Price_oz'] if len(df) > 0 else None
        latest_gram = df.iloc[-1]['Gold_Price_gram'] if len(df) > 0 else None

        avg_oz = df['Gold_Price_oz'].mean() if len(df) > 0 else None
        min_oz = df['Gold_Price_oz'].min() if len(df) > 0 else None
        max_oz = df['Gold_Price_oz'].max() if len(df) > 0 else None

        response_data = {
            'success': True,
            'record_count': len(df),
            "type": "Gold",
            'data': df.to_dict(orient='records'),
            'summary': {
                'latest_price_oz': None if latest_oz is None or math.isnan(latest_oz) else float(latest_oz),
                'latest_price_gram': None if latest_gram is None or math.isnan(latest_gram) else float(latest_gram),
                'latest_date': df.iloc[-1]['Date'] if len(df) > 0 else None,
                'avg_price_oz': None if avg_oz is None or math.isnan(avg_oz) else float(round(avg_oz, 2)),
                'min_price_oz': None if min_oz is None or math.isnan(min_oz) else float(min_oz),
                'max_price_oz': None if max_oz is None or math.isnan(max_oz) else float(max_oz),
            }
        }

        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/silver-prices/latest', methods=['GET'])
def get_latest_price():
    """
    API endpoint to get only the latest silver price.
    
    Returns:
    JSON response with the most recent silver price data
    """
    try:
        df = scrape_prices(type='Silver')
        
        if len(df) == 0:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
        
        # Get the latest record
        latest = df.iloc[-1]
        
        response_data = {
            'success': True,
            'data': {
                'date': latest['Date'].strftime('%Y-%m-%d'),
                'silver_price_oz': float(latest['Silver_Price_oz']),
                'silver_price_gram': float(latest['Silver_Price_gram']),
                'daily_change_oz': float(latest['Daily_Change_Silver_Price_oz']) if pd.notna(latest['Daily_Change_Silver_Price_oz']) else None,
                'daily_change_gram': float(latest['Daily_Change_Silver_Price_gram']) if pd.notna(latest['Daily_Change_Silver_Price_gram']) else None,
                'pct_change': float(latest['Pct_Change_%']) if pd.notna(latest['Pct_Change_%']) else None,
                'ma_7': float(latest['MA_7']) if pd.notna(latest['MA_7']) else None,
                'volatility_7': float(latest['Volatility_7']) if pd.notna(latest['Volatility_7']) else None,
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===========================
# Run Flask App
# ===========================

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)