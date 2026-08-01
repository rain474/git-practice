from fastapi import FastAPI
from database import supabase

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "WeatherWise API is running!"
    }

@app.get("/test")
def test():
    return {
        "status": "Supabase client initialized successfully!"
    }