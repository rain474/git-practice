from fastapi import FastAPI, HTTPException
from database import supabase

app = FastAPI()

def generate_recommendations(temperature: float, uv_index: float, condition: str):
    gear = []
    clothing = []
    sun_safety = {}

    # 1. Weather / Umbrella Logic
    rain_keywords = ["rain", "drizzle", "shower", "thunderstorm", "storm", "typhoon"]
    if any(word in condition.lower() for word in rain_keywords):
        gear.append("Bring an umbrella")
    elif "snow" in condition.lower():
        gear.append("Wear a waterproof hooded jacket")

    # 2. Temperature Logic (Celsius)
    if temperature < 18:
        clothing.append("Wear long sleeves")
        clothing.append("Bring a thick jacket")
    elif 18 <= temperature < 24:
        clothing.append("Wear long sleeves or a light cardigan")
    elif 24 <= temperature < 30:
        clothing.append("Short sleeves or t-shirts are fine")
    else:
        clothing.append("Wear lightweight, loose clothing")
        gear.append("Bring a cold water bottle to stay hydrated")

    # 3. UV / Sunburn / Tanning Logic
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
    else:
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
    return {"message": "WeatherWise App is online!"}

# Send data to Supabase
@app.post("/weather")
def add_weather(city: str, temperature: float, condition: str, uv_index: float):
    try:
        payload = {
            "city": city,
            "temperature": temperature,
            "condition": condition,
            "uv_index": uv_index
        }
        response = supabase.table("weather").insert(payload).execute()
        return {"message": "Saved successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Read data from Supabase and generate smart tips
@app.get("/weather/{city}")
def get_weather(city: str):
    try:
        response = (
            supabase.table("weather")
            .select("*")
            .ilike("city", city)
            .order("created_at", descending=True)
            .limit(1)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No records found for {city}")
            
        latest = response.data[0]
        tips = generate_recommendations(latest["temperature"], latest["uv_index"], latest["condition"])
        
        return {
            "city": latest["city"],
            "metrics": {
                "temperature_celsius": latest["temperature"],
                "condition": latest["condition"],
                "uv_index": latest["uv_index"]
            },
            "advice": tips
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
