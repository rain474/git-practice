import os
from fastapi import FastAPI, HTTPException
import httpx
from database import supabase

app = FastAPI()

# Dumaguete City exact coordinates
LATITUDE = 9.3072
LONGITUDE = 123.3066

# Helper function to convert Open-Meteo WMO weather codes into plain words
def get_condition_string(code: int) -> str:
    # Standard WMO Weather Interpretation Codes
    if code == 0: return "Clear sky"
    elif code in: return "Mainly clear or partly cloudy"
    elif code in: return "Foggy"
    elif code in: return "Drizzle / Light Rain"
    elif code in: return "Rain"
    elif code in: return "Snow"
    elif code in: return "Rain showers"
    elif code in: return "Thunderstorm"
    return "Cloudy"

# Rule engine for clothing, umbrellas, and sun safety
def generate_recommendations(temperature: float, uv_index: float, condition: str):
    gear = []
    clothing = []
    sun_safety = {}

    # 1. Umbrella Check
    rain_keywords = ["rain", "drizzle", "shower", "thunderstorm", "storm"]
    if any(word in condition.lower() for word in rain_keywords):
        gear.append("Bring an umbrella")

    # 2. Clothing advice for Philippine climate (Celsius)
    if temperature < 24:
        clothing.append("Wear long sleeves or a light cardigan")
    elif 24 <= temperature < 30:
        clothing.append("Short sleeves or t-shirts are fine")
    else:
        clothing.append("Wear lightweight, loose clothing")
        gear.append("Bring a cold water bottle to stay hydrated")

    # 3. UV / Sunburn / Tanning Metrics
    if uv_index <= 2:
        sun_safety["risk"] = "Low"
        sun_safety["sunburn_time"] = "Safe for up to 60 minutes"
        sun_safety["tan_viability"] = "Very low tanning potential"
    elif 3 <= uv_index <= 5:
        sun_safety["risk"] = "Moderate"
        sun_safety["sunburn_time"] = "Burns after 30-45 minutes unprotected"
        sun_safety["tan_viability"] = "Gradual tanning possible with SPF"
        gear.append("Wear sunglasses")
        clothing.append("Apply SPF 15+ sunscreen")
    elif 6 <= uv_index <= 7:
        sun_safety["risk"] = "High"
        sun_safety["sunburn_time"] = "Burns in 15-20 minutes unprotected"
        sun_safety["tan_viability"] = "Fast tanning, high sunburn danger"
        gear.append("Wear sunglasses and a cap")
        clothing.append("Apply SPF 30+ sunscreen")
    else:  # UV 8+
        sun_safety["risk"] = "Very High / Extreme"
        sun_safety["sunburn_time"] = "Burns in under 10 minutes unprotected"
        sun_safety["tan_viability"] = "Extreme damage risk; skip tanning"
        gear.append("Wear UV sunglasses and a wide-brim hat")
        clothing.append("Apply SPF 50+ sunscreen")
        if temperature > 32:
            sun_safety["heat_warning"] = "High risk of heat exhaustion. Stay indoors."

    return {
        "gear_to_bring": gear,
        "clothing_suggestions": clothing,
        "sun_and_heat_safety": sun_safety
    }

@app.get("/")
def home():
    return {"message": "Dumaguete Weather Monitor is Online using Open-Meteo!"}

# Single endpoint to trigger the live API request
@app.get("/weather")
async def get_dumaguete_weather():
    # Build Open-Meteo URL targeting Dumaguete directly with current temperature, weather code, and UV Index
    weather_url = (
        f"https://open-meteo.com?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&current=temperature_2m,weather_code,uv_index"
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(weather_url)
        
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Open-Meteo API connection issue.")
        
    weather_data = response.json()
    
    # Extract live data points directly from Open-Meteo response
    current_data = weather_data["current"]
    temp_celsius = current_data["temperature_2m"]
    weather_code = current_data["weather_code"]
    live_uv = current_data["uv_index"]
    
    # Translate WMO code into readable words
    condition_desc = get_condition_string(weather_code)

    # Insert live data into your Supabase table history
    try:
        payload = {
            "city": "Dumaguete",
            "temperature": temp_celsius,
            "condition": condition_desc,
            "uv_index": live_uv
        }
        supabase.table("weather").insert(payload).execute()
    except Exception as db_err:
        print(f"Database save warning: {str(db_err)}")

    # Run recommendation logic
    tips = generate_recommendations(temp_celsius, live_uv, condition_desc)
    
    return {
        "city": "Dumaguete City",
        "live_metrics": {
            "temperature_celsius": temp_celsius,
            "condition": condition_desc,
            "live_uv_index": live_uv
        },
        "smart_advice": tips
    }
