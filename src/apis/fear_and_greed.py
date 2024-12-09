import requests

def get_fear_and_greed_index():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response. json()
        return data['data' ] [0]
    else:
        print(f"Failed to fetch Fear and Greed Index. Status code: {response.status_code}")
        return None

print(get_fear_and_greed_index())