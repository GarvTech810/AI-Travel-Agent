import streamlit as st
import json
import os
import requests
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime

# Streamlit UI setup
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
        }
        .stSlider > div {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and intro
st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip with AI! Get personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

# Inputs
st.markdown("### 🌍 Where are you headed?")
source = st.text_input("🛫 Departure City (IATA Code):", "BOM")
destination = st.text_input("🛬 Destination (IATA Code):", "DEL")

st.markdown("### 📅 Plan Your Adventure")
num_days = st.slider("🕒 Trip Duration (days):", 1, 14, 5)
travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"]
)

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: #ffecd1; 
        border-radius: 10px; 
        margin-top: 20px;
    ">
        <h3>🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
        <p>Let's find the best flights, stays, and experiences for your unforgettable journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Helper: format time
def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")
    except:
        return "N/A"

# User preferences
activity_preferences = st.text_area(
    "🌍 What activities do you enjoy?",
    "Relaxing on the beach, exploring historical sites"
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# Sidebar
st.sidebar.title("🌎 Travel Assistant")
st.sidebar.subheader("Personalize Your Trip")

budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

st.sidebar.subheader("🎒 Packing Checklist")
packing_list = {
    "👕 Clothes": True,
    "🩴 Comfortable Footwear": True,
    "🕶️ Sunglasses & Sunscreen": False,
    "📖 Travel Guidebook": False,
    "💊 Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

st.sidebar.subheader("🛂 Travel Essentials")
visa_required = st.sidebar.checkbox("🛃 Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("🛡️ Get Travel Insurance")
currency_converter = st.sidebar.checkbox("💱 Currency Exchange Rates")

# API keys (replace with your own)
SERPAPI_KEY = "8a9533909cc980bde8401c1f2293efa631a4c10eb6959d3bfb2be7898d96a60a"
GOOGLE_API_KEY = "AIzaSyDP6K4SKU6cn1sdLkts7szrqJUWJekL9lUpython -m streamlit run travelagent.py"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ✈️ Function to fetch flights (no GoogleSearch needed)
def fetch_flights(source, destination, departure_date, return_date):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": str(departure_date),
        "return_date": str(return_date),
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"⚠️ SerpAPI request failed: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"❌ Error fetching flights: {e}")
        return {}

# Extract cheapest flights
def extract_cheapest_flights(flight_data):
    best_flights = flight_data.get("best_flights", [])
    sorted_flights = sorted(best_flights, key=lambda x: x.get("price", float("inf")))[:3]
    return sorted_flights

# AI Agents
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user.",
        "Gather detailed information on the destination.",
        "Find popular attractions and must-visit places.",
        "Match activities with the user’s interests and travel style.",
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
)

planner = Agent(
    name="Planner",
    instructions=[
        "Create a detailed itinerary with activities and estimated costs.",
        "Ensure convenience and enjoyment.",
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Find highly rated hotels and restaurants near attractions.",
        "Prioritize based on user preferences, ratings, and availability.",
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
)

# 🚀 Generate Travel Plan
if st.button("🚀 Generate Travel Plan"):
    with st.spinner("✈️ Fetching best flight options..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("🔍 Researching best attractions & activities..."):
        research_prompt = (
            f"Research attractions in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
            f"User enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
            f"Hotel Rating: {hotel_rating}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("🏨 Searching for hotels & restaurants..."):
        hotel_restaurant_prompt = (
            f"Find the best hotels and restaurants near attractions in {destination}. "
            f"Budget: {budget}. Hotel Rating: {hotel_rating}. Activities: {activity_preferences}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    with st.spinner("🗺️ Creating your personalized itinerary..."):
        planning_prompt = (
            f"Create a {num_days}-day itinerary for a {travel_theme.lower()} trip to {destination}. "
            f"Activities: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
            f"Research: {research_results.content}. Hotels & Restaurants: {hotel_restaurant_results.content}."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    # ✈️ Show flights
    st.subheader("✈️ Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_name = flight.get("airline", "Unknown Airline")
                price = flight.get("price", "Not Available")
                total_duration = flight.get("total_duration", "N/A")

                flights_info = flight.get("flights", [{}])
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})

                departure_time = format_datetime(departure.get("time", "N/A"))
                arrival_time = format_datetime(arrival.get("time", "N/A"))

                booking_link = "https://www.google.com/travel/flights"

                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ddd;
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                        margin-bottom: 20px;
                    ">
                        <h3>{airline_name}</h3>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Duration:</strong> {total_duration} min</p>
                        <h2 style="color: #008000;">💰 {price}</h2>
                        <a href="{booking_link}" target="_blank" style="
                            display: inline-block;
                            padding: 10px 20px;
                            color: #fff;
                            background-color: #007bff;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 10px;
                        ">🔗 Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.warning("⚠️ No flight data available.")

    st.subheader("🏨 Hotels & Restaurants")
    st.write(hotel_restaurant_results.content)

    st.subheader("🗺️ Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("✅ Travel plan generated successfully!")
