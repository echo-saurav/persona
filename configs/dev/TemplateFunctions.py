from textwrap import dedent
from src.context import Context
from dotenv import load_dotenv
import os

load_dotenv()
default_api_timeout = 5


def user_profile(context: Context):
    return context.user_profile()


def current_time(context: Context):
    return context.current_time()


def user_location(context: Context):
    location = os.getenv(key='LOCATION')
    return location


def last_conversations(context: Context):
    return context.get_last_conversations(
        context.api_key,
        include_info=False
    )


def long_last_conversation(context: Context):
    conversations = context.get_last_conversations(
        context.api_key,
        include_info=True,
        limit=30
    )
    return conversations


def current_chat(context: Context):
    return context.current_chat()


def __get_current_location_location(context):
    lat = os.getenv(key='LAT')
    lon = os.getenv(key='LON')
    return {
        "lat": lat,
        "lon": lon
    }


def __weather_call(context):
    from dotenv import load_dotenv
    import time
    import os
    load_dotenv()
    loc = __get_current_location_location(context)
    API_KEY = os.getenv('OPENWEATHER_API')
    units = "metric"
    api_endpoint = f"https://api.openweathermap.org/data/2.5/weather?lat={loc.get('lat')}&lon={loc.get('lon')}&units={units}&appid={API_KEY}"

    import requests
    try:
        res = requests.get(api_endpoint, timeout=default_api_timeout)
        res = res.json()
        return res
    except:
        return None


def current_weather(context):
    res = __weather_call(context)
    if res is None:
        return ""
    else:
        from datetime import datetime

        current_weather_array = res.get('weather')
        current_temp = res.get("main").get("temp")
        current_temp_feels_like = res.get("main").get("feels_like")
        temp_min = res.get("main").get("temp_min")
        temp_max = res.get("main").get("temp_max")
        humidity = res.get("main").get("humidity")
        wind_speed = res.get("wind").get("speed")
        wind_deg = res.get("wind").get("deg")
        cloud_percentage = res.get("clouds").get("all")
        sunrise_unix = res.get("sys").get("sunrise")
        sunset_unix = res.get("sys").get("sunset")
        # Convert Unix time to human-readable format
        sunrise_human = datetime.fromtimestamp(sunrise_unix).strftime('%I:%m %p')
        sunset_human = datetime.fromtimestamp(sunset_unix).strftime('%I:%m %p')

        current_weather_prompt = ""
        for weather_ in current_weather_array:
            main = weather_.get("main")
            desc = weather_.get("description")
            current_weather_prompt = f"{current_weather_prompt}\n{main} : {desc}"

        prompt = dedent(f"""
        Current weather:
        {current_weather_prompt.strip()}
        ---
        Temperature:
        current temp: {current_temp} celsius
        current temp feels like: {current_temp_feels_like} celsius
        
        Max Temperature: {temp_max}
        Min Temperature: {temp_min}
        
        Humidity: {humidity}
        Wind speed: {wind_speed} 
        Wind degree: {wind_deg}
        
        Cloudy percentage: {cloud_percentage}
        
        Sunrise: {sunrise_human}
        sunset: {sunset_human}
        """)

        return prompt.strip()
