import requests

CITY = "北京"

url = f"https://wttr.in/{CITY}?format=j1"
response = requests.get(url)
data = response.json()


current = data["current_condition"][0]
city = data["nearest_area"][0]["areaName"][0]["value"]
temp = current["temp_C"]
weather = current["weatherDesc"][0]["value"]
humidity = current["humidity"]
wind = current["windspeedKmph"]

print("====实时天气=======")
print(f"城市:{city}")
print(f"天气:{weather} ")
print(f"温度:{humidity} ℃")
print(f"湿度:{humidity} %")
print(f"风速:{wind} km/h")

