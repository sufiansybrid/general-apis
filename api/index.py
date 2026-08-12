from flask import Flask, request, jsonify, render_template
import json
import re
from flask_cors import CORS
import os
from bs4 import BeautifulSoup
import html

import requests

# app = Flask(__name__, template_folder='templates')
# Initialize Flask app with custom template folder path
app = Flask(
    __name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates")
)

CORS(app)  # Enable CORS for all route


@app.route("/")
def home():
    return "Hello World"


@app.route("/about")
def about():
    return "About"


@app.route("/number_to_words_with_formatting")
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
        num = request.args.get("num", default=1000000, type=str)

        print(num)

        # Extract only the digits from the input
        num = "".join(re.findall(r"\d", num))

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
        result = [
            {
                # Format the number with commas for readability
                "In Numbers:": f"{float(num):,}",
                "In Words:": capitalized_sentence,  # The capitalized word form of the number
            }
        ]

        # Return the result as a formatted JSON string (pretty-printed)
        # return json.dumps(result, indent=2)
        return jsonify(result)

    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        # return json.dumps(e)
        return jsonify({"error": str(e)}), 400


@app.route("/chat", methods=["POST"])
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
        user_message = request.json.get("question", "").lower()
        response = responses.get(user_message, "Sorry, I don't understand that.")
        return jsonify({"answer": response})
    except Exception as e:
        # If an error occurs, return the exception message as a JSON string
        return json.dumps(e)


@app.route("/psw_stream")
def psw_stream():
    return render_template("index_stream.html")


@app.route("/psw")
def psw():
    return render_template("psw.html")


@app.route("/psw_home")
def psw_home():
    return render_template("psw_home.html")


@app.route("/ffc_home")
def ffc_home():
    return render_template("ffc_index.html")


@app.route("/api/owner-details", methods=["GET", "POST"])
def get_owner_details():
    # Get number from query param or JSON body
    number = request.args.get("number") or request.json.get("number")

    if not number:
        return jsonify({"success": False, "error": "No phone number provided."}), 400

    HEADERS = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://dbcenter.pk",
        "referer": "https://dbcenter.pk/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    payload = {"action": "db_center_uk_search", "search_term": number}

    try:
        response = requests.post(
            "https://dbcenter.pk/wp-admin/admin-ajax.php",
            headers=HEADERS,
            data=payload,
            timeout=8,
        )
        response.raise_for_status()
        html = response.text

        owner_details = {}

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Look through div with id='resultCard' and find 'Owner Details'
        owner_cards = soup.find("div", {"id": "resultCard"})

        if owner_cards and "Owner Details" in owner_cards.text:
            try:
                rows = owner_cards.find_all("tr")
                for row in rows:
                    try:
                        key = row.find("th").text.strip().lower()
                        value = row.find("td").text.strip()
                        owner_details[key] = value
                    except AttributeError:
                        continue  # Skip rows with missing th or td
            except Exception as e:
                return (
                    jsonify(
                        {"success": False, "error": f"Error parsing owner details: {e}"}
                    ),
                    500,
                )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No owner details found for this number.",
                    }
                ),
                404,
            )

        return jsonify(owner_details)

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Request failed: {e}"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {"success": False, "error": "Request to external server timed out."}
            ),
            504,
        )


@app.route("/api/cnic-information", methods=["GET", "POST"])
def cnic_information():
    # cnic = request.args.get('cnic') or (request.json and request.json.get('cnic'))
    # cnic = request.args.get('cnic') or (request.json and request.json.get('cnic'))
    cnic = request.args.get("cnic")
    if not cnic:
        return jsonify({"success": False, "error": "Missing CNIC number."}), 400

    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,en-GB-oxendict;q=0.7,ur;q=0.6",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://dbcenter.pk",
        "priority": "u=0, i",
        "referer": "https://dbcenter.pk/cnic-information-system/",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    }

    payload = {"search_term": cnic}

    try:
        response = requests.post(
            "https://dbcenter.pk/cnic-information-system/",
            headers=HEADERS,
            data=payload,
            timeout=8,
        )
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", {"id": "resultCard"})

        all_owner_details = []

        for card in cards:
            if "Owner Details" in card.text:
                rows = card.find_all("tr")
                details = {}
                for row in rows:
                    try:
                        key = row.find("th").text.strip().lower()
                        value = row.find("td").text.strip()
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
        return (
            jsonify(
                {"success": False, "error": "Request to external server timed out."}
            ),
            504,
        )


@app.route("/api/get-numbers-on-cnic-from-simownerdetails", methods=["GET"])
def get_numbers_on_cnic_from_simownerdetails():

    def parse_html(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        result_cards = soup.select(".result-card")
        records = []

        for card in result_cards:
            fields = card.select(".field")
            record = {}

            for field in fields:
                label = field.select_one("label.info")
                value = field.find("div")

                # print(f"label: {label.text} and value: {value.text}")
                if label and value:
                    key = label.text.strip().upper()
                    record[key] = value.text.strip()

            if record:
                records.append(record)

        return records

    cnic = request.args.get("cnic")

    if not cnic or not cnic.isdigit() or len(cnic) != 13:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "A valid 13-digit CNIC without dashes is required",
                }
            ),
            400,
        )

    HEADERS = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,en-GB-oxendict;q=0.7,ur;q=0.6",
        "local-cache": "yes",
        "priority": "u=1, i",
        "referer": "https://simownerdetails.org.pk/",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
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
            return jsonify({"success": False, "error": "No data found"}), 404

        return jsonify(
            {"success": True, "records_found": len(parsed_data), "data": parsed_data}
        )

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid JSON received"}), 500
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {"success": False, "error": "Request to external server timed out."}
            ),
            504,
        )


@app.route("/api/track-cnic", methods=["GET"])
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
            response = session.get("https://cnic.pk/")
            # response.raise_for_status()
        except Exception as e:
            return {"error": f"Failed to fetch CSRF token: {str(e)}"}
        # response = session.get('https://cnic.pk/')
        # response.raise_for_status()

        # Parse the HTML to find the CSRF token
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token_input = soup.find("input", {"name": "csrf_token"})
        if not csrf_token_input or not csrf_token_input.get("value"):
            raise ValueError("CSRF token not found on the page.")

        csrf_token = csrf_token_input["value"]
        print(f"Fetched CSRF Token: {csrf_token}")

        # Step 2: Prepare POST data
        files = {
            "csrf_token": (None, csrf_token),
            "user_input": (None, request.args.get("cnic")),
        }

        headers = {
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0",
            "referer": "https://cnic.pk/",
        }

        # Step 3: POST using the same session
        post_response = session.post(
            "https://cnic.pk/track", files=files, headers=headers
        )
        post_response.raise_for_status()

        # Try to return JSON if available
        try:
            return post_response.json()
        except ValueError:
            return post_response.text

    except Exception as e:
        return {"error": str(e)}


@app.route("/api/track_challan", methods=["GET"])
def track_challan() -> dict:
    """
    Track challan information from sindhpolice.gov.pk.

    Args:
        vehicle_number (str): Vehicle number, e.g. "KGI-6908".
        cnic_number (str): Optional CNIC number.

    Returns:
        dict: A structured response indicating success or failure.
    """

    vehicle_number = request.args.get("vehicle_number")
    cnic_number = request.args.get("cnic_number")
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
    payload = {"_token": csrf_token, "vehicle": vehicle_number, "cnic": cnic_number}

    # 4. Required headers
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://sindhpolice.gov.pk/challan-check",
        "X-CSRF-TOKEN": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
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
        return {
            "status": "not_found",
            "message": "No challan record found",
            "raw": text[:100],
        }

    return {"status": "found", "message": "Challan record found", "raw": text[:100]}


@app.route("/claude-chat")
def claude_chat():
    return render_template("claude-chat.html")


@app.route("/marked-1")
def marked1():
    return render_template("marked-1.html")


@app.route("/marked-2")
def marked2():
    return render_template("marked-2.html")


@app.route("/marked-3")
def marked3():
    return render_template("marked-3.html")


def fetch_ssgc_bill(customer_number: str) -> dict:
    """Helper function to fetch bill data from SSGC and return a structured dictionary."""
    url = "https://viewbill.ssgc.com.pk/web/"

    cookies = {
        '_gcl_au': '1.1.67700686.1786084287',
        '_ga_H6YLY258B5': 'GS2.1.s1786084288$o1$g0$t1786084296$j52$l0$h0',
        '_ga': 'GA1.3.1629238666.1786084289',
        '__utma': '147246261.1629238666.1786084289.1786085306.1786085306.1',
        '__utmz': '147246261.1786085306.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
        '_gid': 'GA1.3.916068457.1786350642',
        'PHPSESSID': '9vhng51j7e11j5sbe2cidgd7pa',
        '_gat': '1',
        '_ga_1FE7NXRM1T': 'GS2.3.s1786523277$o9$g1$t1786523279$j58$l0$h0',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,ur;q=0.8,en-GB;q=0.7,en-GB-oxendict;q=0.6',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://viewbill.ssgc.com.pk',
        'Referer': 'https://viewbill.ssgc.com.pk/web/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-gpc': '1',
        # 'Cookie': '_gcl_au=1.1.67700686.1786084287; _ga_H6YLY258B5=GS2.1.s1786084288$o1$g0$t1786084296$j52$l0$h0; _ga=GA1.3.1629238666.1786084289; __utma=147246261.1629238666.1786084289.1786085306.1786085306.1; __utmz=147246261.1786085306.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _gid=GA1.3.916068457.1786350642; PHPSESSID=9vhng51j7e11j5sbe2cidgd7pa; _gat=1; _ga_1FE7NXRM1T=GS2.3.s1786523277$o9$g1$t1786523279$j58$l0$h0',
    }

    payload = {
        "b": customer_number,
        'g-recaptcha-response': '0cAFcWeA4WEaeHou2q4NzzrD5FaYjeExWfjIQ6jRVoxHvf7KVgKXp_1Vqsubvn80Lr6HMzLAp4B1IwYumoORhamtZ0VuXmeYV_8Il3z06wHuM8vVM0HD5n-dhFzO72FXrFYJZLYYJeuz9rTfQ22n83uyIp4uk_-SdZ1RPH7_WPfYZ7C3D3NnhReKCHoiULh752_Mp9e1Qp2DzxLTtqvBOHLi5akgDSXgo4hyIifztlJ6GUvAy_Ks4-tbw8wz6QDuDqPt3D9waxqAV7QFnlFuqBRkM9mLH0G5bKEL_BJBfGgwv12NeWvy4tyf2-LJGBxv9Qh68k9Z21u7MlnhUAnbO67jjCPHW5ZWJkvEsrzm2DO8M3RyrC3vseJKdSl6ceTWmjSInJA_LnjyZveL_xbAaIa7Oq6bLNDcqL3Fctn6GHjBtro2ngoCSTzA1x-M3xYg86BDdUoRqaGwwaNRNKaD5b7eTxQ4546RpyF-pj09kOG7R1d-Lg53bkJ6hYVNItCCQheYcZs4UyeTTKeDKEkGrfMofOSwILtK3Mda43XNY3aMV3WBZtcxusYeptsjJE6PdV3MszZ48XiAwk-Bwt1FrJGwm8AVQGOTamP9cdflePcWSxCty0zQn48sglVg9kNmrK9tDdnzPqPdfj8taaeRy6lmnzp6XQlf6xIF9anOgeqxK25h1sUmeGnDXsuixOj6926KEgFt0MdvC6QPqxqMI0fQvTjqPvyCyEgNwwZxfEM9dzqaXkKHjLIjuzJ1iDuSZwhzIKtyypt5NdjYgZGWwHaJIunt3hm8QjfIb7BEqm1wHdaj1qfcmcQQnYbIWL0Ac9dNUpzMsqiFUA8Lb4RICUksMaIPUDZZiPNafemyTszdFQ2Wft4KUlvTjtmH4ZJjUEAL6_y2Cw3AorTByiRWlaib8pQMlqrGgmSKHVwr8KGZ5MXz-13lzD3HnwNsfOG7xgbZBkHIgD32qJBmcMsJIoCrJlhzPjOUEHzbM290n2LEKzeAaVIkp3qQyv6D2GF61dwv5w2ud38CxMdcvkCwy6_hXyMYJfOFui71Jw7hdRk6usom6JXozXbTdPtnDOtNxqzxP4uZD1Cvzq7dPFjqvTTplQkv6oNfE4ta8dlWxblIkMbRi1WMynPsTdd6UxVJCvPngSzZdvoRQAISq4QVZr78ZbsNupcEPjLT5FQQaQA6QPzzDYNtvY6lL1tNB-MLqIThCmZdCwDPQAWv5zhk7XEFzc7yjJIDhqzRVkxlqhK1rP6ONZkbyABhCLRq3p1LMFvUqwtJbJcFGSh5awFw93qztQYLmGGHNg45kHoiU7n4db66riFXwoh-iug9kDUX04Kv6JcOfiFDQ2UH2oijQG7aQmBrenwnqVQ4js4wtH2b28syCraU1J2lamzzH4Zpf8RRLJryWVwnDPxeTT4s5nTPGBb8amAPSuMRIrinj5-TR88tomvsBsytKXMLfPHs6hvQ7fxpSOtUP_F6lWcoiDvUHyF2X1WN80qnIWFT-EFrVIPWF0bGCabpCfR8fLnKKEiXWENCatFaX03Fkvallky3BGiFKatEWdEPjSLExlk84e0AD7Jf4xBYHYPj0lGwe3uNxz3hy-As7hLyksGrEcVIAGBdURTnY3hr35JDczBIMC55Lhv6bumxvxaq86I41WRw-6cc3HAN0h5ugyyZS-P7Y7GLDg-mhTDXHGJ-M68EkHf7GGI-KGYMFCdakww73BxGf3O7ONzlqifZHmwHD6e7EVrMEw4eXybQssHb1q-_sFfWvkUSsX9dgpT7dwZoo4YgW9YKXgRAnDCHYUoE8TJ8ETyGlpUrn1AkgBnUL5jOUntL2rTaN6UurIM8IQK49_M2BjQmIAFKumIopGDgBgavSxzUDErkCS7PMJq3KTAAjii6aKJv9C1j32xlKKEK3UfIxykkDkvdfej_ArbOeHoV6qJMSiju8b0XHyGoZbJUAU-cm8_t41w6QrSfKzgadfe3TBMny7QVuImvdDW_UznMfId8uJWCxd7zlR4qN48vkYzT4SYyZScbcEuHcgBMOetncSYtRvEHI-WjKKmat8kAQNgETMWPS2eH2cqUbGNCzFGGzUIb2M3z3_01yOOuaKXsm3XDRgl2B4WJWdggLg4j0GWVanMmRXEBJu6qm5Hk03x4OcrPu87BEiTgLN_JpfLzBHv3j392pyhgOB1HlNg1aTz5iCtffiMvMXLhihzg5wAxFQmzc3sww8bC-u8gQzq_SLLgtkLJvQCZNhvBGFkSlEAcQ1REZjGMrWhH0ilTGZ-LzUq7Bo8iQ',
        '_wpnonce': '92ed8e1566',
        '_wp_http_referer': '/web/',
    }

    try:
        response = requests.post(
            url, cookies=cookies, headers=headers, data=payload, timeout=15
        )
        response.raise_for_status()

        # Parse HTML string using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        extracted_data = {}

        # Extract rows
        for row in soup.find_all("div", class_="row"):
            label_div = row.find("div", class_="one_half")
            if label_div:
                label = label_div.get_text(strip=True).rstrip(":")
                value_div = label_div.find_next_sibling("div")
                value = value_div.get_text(strip=True) if value_div else ""

                # Normalize key names for JSON friendliness
                key = label.lower().replace(" ", "_")
                extracted_data[key] = value

        return extracted_data

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch bill details: {str(e)}"}


@app.route("/api/view-gas-bill", methods=["GET", "POST"])
def get_gas_bill():
    # Accept customer number via JSON body, URL parameters, or Form data
    customer_number = None

    if request.is_json:
        data = request.get_json()
        customer_number = data.get("customer_number") or data.get("b")
    elif request.method == "POST":
        customer_number = request.form.get("customer_number") or request.form.get("b")
    else:
        customer_number = request.args.get("customer_number") or request.args.get("b")

    if not customer_number:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Missing 'customer_number' or 'b' parameter.",
                }
            ),
            400,
        )

    bill_details = fetch_ssgc_bill(customer_number)

    if "error" in bill_details:
        return jsonify({"status": "error", "message": bill_details["error"]}), 502

    if not bill_details:
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": "No account summary found for the provided customer number.",
                }
            ),
            404,
        )

    return jsonify({"status": "success", "data": bill_details}), 200


def to_num(val, default=0):
    """Safely cast numeric string fields into int/float."""
    if val is None or val == "":
        return default
    try:
        return float(val) if "." in str(val) else int(val)
    except ValueError:
        return default


def transform_billing_json(raw_data: dict) -> dict:
    """Transforms raw KW&SC JSON payload into structured camelCase JSON."""
    inner = raw_data.get("data", {}) or {}

    # Extract dynamic 12-month billing history
    billing_history = []
    for i in range(1, 13):
        month_key = f"billinG_MONTH_{i}"
        if month_key in inner and inner[month_key]:
            billing_history.append({
                "month": inner.get(month_key),
                "amountBilled": to_num(inner.get(f"amounT_BILLED_{i}")),
                "amountPaid": to_num(inner.get(f"amounT_PAID_{i}")),
                "paymentDate": inner.get(f"paymenT_DATE_{i}")
            })
    
    # Reverse to keep chronological order (Oldest -> Recent)
    billing_history.reverse()

    return {
        "status": raw_data.get("status", 0),
        "billStatus": raw_data.get("billstatus", "Unknown"),
        "data": {
            "consumer": {
                "consumerNo": inner.get("conS_NO"),
                "consumerIdCheckDigit": inner.get("consumeR_ID_CHK_DG"),
                "name": inner.get("consumeR_NAME"),
                "address": {
                    "line1": inner.get("adD1"),
                    "line2": (inner.get("adD2") or "").strip(),
                    "townName": inner.get("towN_NAME"),
                    "townCode": inner.get("towN_CODE"),
                    "townAbbreviation": inner.get("towN_ABBRI"),
                    "zoneName": inner.get("zonE_NAME")
                },
                "propertyDetails": {
                    "plotType": inner.get("ploT_TYPE"),
                    "plotSizeSqFt": to_num(inner.get("ploT_SIZE")),
                    "flatSizeSqFt": to_num(inner.get("flaT_SIZE")),
                    "additionalStories": to_num(inner.get("additionaL_STORY"))
                }
            },
            "billDetails": {
                "billPeriod": inner.get("bilL_PERIOD"),
                "issueDate": inner.get("issU_DT"),
                "dueDate": inner.get("duE_DT"),
                "barcode": inner.get("baR_CODE"),
                "noticeMessage": inner.get("messeagE_rebate"),
                "contactInfo": inner.get("towN_MSG")
            },
            "charges": {
                "currentCharges": {
                    "water": to_num(inner.get("wateR_CURRENT")),
                    "sewerage": to_num(inner.get("seweragE_CURRENT")),
                    "conservancy": to_num(inner.get("conservancY_CURRENT")),
                    "fire": to_num(inner.get("firE_CURRENT")),
                    "waterSurcharge": to_num(inner.get("wateR_SURCHARGE"))
                },
                "arrears": {
                    "water": to_num(inner.get("wateR_ARREARS")),
                    "sewerage": to_num(inner.get("seweragE_ARREARS")),
                    "conservancy": to_num(inner.get("conservancY_ARREARS")),
                    "fire": to_num(inner.get("fire_ARREARS")),
                    "total": to_num(inner.get("outstandinG_ARREARS"))
                },
                "totals": {
                    "waterTotal": to_num(inner.get("totaL_WATER")),
                    "sewerageTotal": to_num(inner.get("totaL_SEWERAGE")),
                    "conservancyTotal": to_num(inner.get("totaL_CONSERVANCY")),
                    "fireTotal": to_num(inner.get("totaL_FIRE")),
                    "bankCharges": to_num(inner.get("banK_CHARGES"))
                },
                "rebates": {
                    "water": to_num(inner.get("waterRebate")),
                    "sewerage": to_num(inner.get("sewerageRebate")),
                    "conservancy": to_num(inner.get("conservancyRebate")),
                    "fire": to_num(inner.get("fireRebate")),
                    "total": to_num(inner.get("totalRebate")),
                    "percentage": to_num(inner.get("rebatePercentage"))
                },
                "paymentSummary": {
                    "payableByDueDate": to_num(inner.get("payablE_DUE_DATE")),
                    "payableAfterDueDate": to_num(inner.get("payablE_AFTER_DATE"))
                }
            },
            "billingHistory": billing_history
        }
    }


def fetch_from_upstream(consumer_id: str):
    """Utility to query the upstream KW&SC API."""

    # Headers matching your curl setup
    HEADERS = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ur;q=0.8,en-GB;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.kwsc.gos.pk',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-gpc': '1',
    }

    COOKIES = {
        'cookie-consent': 'declined',
    }

    HEADERS['Referer'] = f'https://www.kwsc.gos.pk/bill/view?consumerId={consumer_id}'

    try:
        response = requests.post(
            'https://www.kwsc.gos.pk/api/bill/get-bill',
            headers=HEADERS,
            cookies=COOKIES,
            json={'consumerId': consumer_id},
            timeout=10
        )
        response.raise_for_status()
        raw_json = response.json()
    except requests.exceptions.HTTPError as exc:
        return {"error": "Upstream KW&SC API returned an error.", "details": str(exc)}, exc.response.status_code
    except requests.exceptions.RequestException as exc:
        return {"error": "Failed to connect to upstream server.", "details": str(exc)}, 500

    if not raw_json.get("data"):
        return {"error": "Bill record not found for this Consumer ID."}, 404

    return transform_billing_json(raw_json), 200


@app.route('/api/view-water-bill', methods=['GET', 'POST'])
def get_water_bill():
    """GET endpoint: /api/view-water-bill/ \n
    Accepts consumer_id as a query parameter or JSON body and fetches water bill details."""

    consumer_id = None
    
    if request.is_json:
        data = request.get_json()
        consumer_id = data.get("consumer_id")
    elif request.method == "POST":
        consumer_id = request.form.get("consumer_id")
    else:
        consumer_id = request.args.get("consumer_id")
        
    result, status_code = fetch_from_upstream(consumer_id)
    return jsonify(result), status_code


# ===========================
# Run Flask App
# ===========================

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=False)