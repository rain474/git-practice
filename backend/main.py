
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"], # Vite & CRA ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# DUMAGUETE CITY LOCATION
# ==========================================

DUMAGUETE_LATITUDE = 9.3001
DUMAGUETE_LONGITUDE = 123.2995


# ==========================================
# CONVERT WMO WEATHER CODE TO DESCRIPTION
# ==========================================

def get_condition_string(code: int) -> str:

    if code == 0:
        return "Clear sky"

    elif code in [1, 2, 3]:
        return "Mainly clear or partly cloudy"

    elif code in [45, 48]:
        return "Foggy"

    elif code in [51, 53, 55, 56, 57]:
        return "Drizzle / Light Rain"

    elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "Rain"

    elif code in [71, 73, 75, 77, 85, 86]:
        return "Snow"

    elif code in [95, 96, 99]:
        return "Thunderstorm"

    return "Cloudy"


# ==========================================
# GENERATE PERSONALIZED RECOMMENDATIONS
# ==========================================

def generate_recommendations(
    temperature: float,
    uv_index: float,
    condition: str
):

    gear = []
    clothing = []
    sun_safety = {}

    # -----------------------------
    # WEATHER / UMBRELLA
    # -----------------------------

    rain_keywords = [
        "rain",
        "drizzle",
        "shower",
        "thunderstorm",
        "storm"
    ]

    if any(word in condition.lower() for word in rain_keywords):
        gear.append("Bring an umbrella")

    # -----------------------------
    # TEMPERATURE
    # -----------------------------

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

    # -----------------------------
    # UV INDEX
    # -----------------------------

    if uv_index <= 2:

        sun_safety["risk"] = "Low"
        sun_safety["sunburn_time"] = "Safe for up to 60 minutes"
        sun_safety["tan_viability"] = "Very low tanning potential"

    elif 3 <= uv_index <= 5:

        sun_safety["risk"] = "Moderate"
        sun_safety["sunburn_time"] = (
            "Burns after 30-45 minutes unprotected"
        )
        sun_safety["tan_viability"] = (
            "Gradual tanning possible with SPF"
        )

        gear.append("Wear sunglasses")
        clothing.append("Apply SPF 15+ sunscreen")

    elif 6 <= uv_index <= 7:

        sun_safety["risk"] = "High"
        sun_safety["sunburn_time"] = (
            "Burns in 15-20 minutes unprotected"
        )
        sun_safety["tan_viability"] = (
            "Fast tanning, high sunburn danger"
        )

        gear.append("Wear sunglasses and a cap")
        clothing.append("Apply SPF 30+ sunscreen")

    else:

        sun_safety["risk"] = "Very High / Extreme"
        sun_safety["sunburn_time"] = (
            "Burns in under 10 minutes unprotected"
        )
        sun_safety["tan_viability"] = (
            "Extreme damage risk; skip tanning"
        )

        gear.append("Wear UV sunglasses and a wide-brim hat")
        clothing.append("Apply SPF 50+ sunscreen")

        if temperature > 32:

            sun_safety["heat_warning"] = (
                "High risk of heat exhaustion. Stay indoors."
            )

    return {
        "gear_to_bring": gear,
        "clothing_suggestions": clothing,
        "sun_and_heat_safety": sun_safety
    }


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "WeatherWise App is online!",
        "location": "Dumaguete City, Philippines"
    }


# ==========================================
# GET CURRENT DUMAGUETE WEATHER
# ==========================================

@app.get("/weather")
def get_dumaguete_weather():

    try:

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": DUMAGUETE_LATITUDE,
            "longitude": DUMAGUETE_LONGITUDE,

            "current": (
                "temperature_2m,"
                "weather_code,"
                "uv_index"
            ),

            "timezone": "Asia/Manila"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data["current"]

        temperature = current["temperature_2m"]
        weather_code = current["weather_code"]
        uv_index = current["uv_index"]

        condition = get_condition_string(weather_code)

        tips = generate_recommendations(
            temperature,
            uv_index,
            condition
        )

        return {

            "city": "Dumaguete City",

            "source": "Open-Meteo",

            "weather": {
                "temperature_celsius": temperature,
                "weather_code": weather_code,
                "condition": condition,
                "uv_index": uv_index
            },

            "advice": tips

        }

    except requests.RequestException as e:

        raise HTTPException(
            status_code=503,
            detail=f"Weather API error: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

