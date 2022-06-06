import pyowm
import requests

place = requests.get("https://ipinfo.io")
API_KEY = pyowm.OWM("9e0bc90057058384e14422eb9614bac4")


def getGeoLocation():
    data = place.json()
    return data['city']


def getWeatherInfo_Min():
    weatherBot = API_KEY.weather_manager()
    weatherData = weatherBot.weather_at_place(getGeoLocation())
    dictWeatherData = weatherData.to_dict()
    return dictWeatherData.get("weather").get("status")


def getWeatherInfo_IMG():
    weatherBot = API_KEY.weather_manager()
    weatherData = weatherBot.weather_at_place(getGeoLocation())
    dictWeatherData = weatherData.to_dict()
    dictWeatherData = dictWeatherData.get("weather").get('status')
    return dictWeatherData


def getWeatherInfo_Temperature():
    weatherBot = API_KEY.weather_manager()
    weatherData = weatherBot.weather_at_place(getGeoLocation())
    WeatherData1 = weatherData.weather
    weatherData2 = WeatherData1.temperature("celsius")
    return weatherData2


def getWeatherInfo_Detailed():
    Detailed = {}
    weatherBot = API_KEY.weather_manager()
    weatherData = weatherBot.weather_at_place(getGeoLocation())
    dictWeatherData = weatherData.to_dict()
    dictLocationData = weatherData.to_dict().get('location')
    dictWeatherData = dictWeatherData.get('weather')
    Detailed['country'] = dictLocationData.get('country')
    Detailed['name'] = dictLocationData.get('name')
    Detailed['detailed_status'] = dictWeatherData.get('detailed_status')
    Detailed['temperature'] = str(getWeatherInfo_Temperature().get('temp'))
    Detailed['humidity'] = dictWeatherData.get('humidity')
    return Detailed


def getWeatherInfo_Detailed_Header():
    return list(getWeatherInfo_Detailed().keys())


def getWeatherInfo_Detailed_List():
    return list(getWeatherInfo_Detailed().values())


