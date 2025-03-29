import os
import json
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from icalendar import Calendar
from dateutil import parser
from werkzeug.utils import secure_filename

# Configure Flask
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Secure API Key Handling
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro-vision')

# Web Scraping Function
def scrape_food_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        food_items = {}

        districts = soup.find_all('div', class_='food-district')
        for district in districts:
            district_name = district.find('h2').text.strip()
            items = [item.text.strip() for item in district.find_all('li')]
            food_items[district_name] = items

        return food_items
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Meal Planning Function
def generate_meal_plan(food_data, macros, schedule):
    prompt = f"""
    Generate a balanced meal plan based on the following food availability:
    {json.dumps(food_data)}

    Target macros: {json.dumps(macros)}

    User's schedule: {schedule}

    Return the meal plan as a valid JSON object with meal times and nutritional values.
    """

    response = model.generate_content(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "Invalid AI response"}

# Macro Tracking Function
def track_macros(meal_plan_data, existing_macros=None):
    if existing_macros is None:
        existing_macros = {"calories": 0, "protein": 0, "sodium": 0, "carbs": 0, "fat": 0}
    
    prompt = f"""
    Analyze the following meal plan and extract macros.
    {json.dumps(meal_plan_data)}

    Return the results as a valid JSON object.
    """

    response = model.generate_content(prompt)
    try:
        new_macros = json.loads(response.text)
        for key, value in new_macros.items():
            if key in existing_macros and isinstance(value, (int, float)):
                existing_macros[key] += value
    except json.JSONDecodeError:
        return {"error": "Invalid AI response"}

    return existing_macros

# Parse Calendar Function
def parse_schedule(file_path):
    try:
        if file_path.endswith('.ics'):
            with open(file_path, 'rb') as f:
                gcal = Calendar.from_ical(f.read())
            
            schedule_events = []
            for component in gcal.walk('VEVENT'):
                start = parser.parse(component.get('dtstart').to_ical().decode('utf-8')).isoformat()
                end = parser.parse(component.get('dtend').to_ical().decode('utf-8')).isoformat()
                summary = component.get('summary')
                schedule_events.append({"summary": summary, "start": start, "end": end})
            
            return schedule_events

        elif file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                calendar_data = json.load(f)
            
            schedule_events = []
            for event in calendar_data.get('items', []):
                start = parser.parse(event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')).isoformat()
                end = parser.parse(event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')).isoformat()
                summary = event.get('summary')
                schedule_events.append({"summary": summary, "start": start, "end": end})

            return schedule_events

    except Exception as e:
        return {"error": str(e)}

# API Endpoints
@app.route("/scrape-food", methods=["GET"])
def scrape_food():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    return jsonify(scrape_food_data(url))

@app.route("/meal-plan", methods=["POST"])
def meal_plan():
    data = request.json
    food_data = data.get("food_data")
    macros = data.get("macros")
    schedule = data.get("schedule")

    if not food_data or not macros or not schedule:
        return jsonify({"error": "Missing parameters"}), 400

    return jsonify(generate_meal_plan(food_data, macros, schedule))

@app.route("/track-macros", methods=["POST"])
def track():
    data = request.json
    meal_plan_data = data.get("meal_plan_data")
    existing_macros = data.get("existing_macros", {})

    if not meal_plan_data:
        return jsonify({"error": "Missing meal plan data"}), 400

    return jsonify(track_macros(meal_plan_data, existing_macros))

@app.route("/upload-calendar", methods=["POST"])
def upload_calendar():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    return jsonify(parse_schedule(file_path))

if __name__ == "__main__":
    app.run(debug=True)
