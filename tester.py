import requests
import json

url = "http://localhost:5000/init"

# Example data structure to match your model's expectations
# example_data = {
#     "grid": [
#         [  # row 0
#             {"x": 0, "y": 0, "fire": False, "smoke": False, "victim": False, "poi": False, "hot_spot": False, "firefighter": None},
#             {"x": 0, "y": 1, "fire": True, "smoke": False, "victim": False, "poi": False, "hot_spot": False, "firefighter": None}
#         ],
#         [  # row 1
#             {"x": 1, "y": 0, "fire": False, "smoke": True, "victim": False, "poi": False, "hot_spot": False, "firefighter": None},
#             {"x": 1, "y": 1, "fire": False, "smoke": False, "victim": True, "poi": False, "hot_spot": False, "firefighter": None}
#         ]
#     ]
# }

example_data = {
    "grid": []
}

# JSON payload to send
payload = {
    "mode": "dumb",  # or "smart"
    "data": example_data
}

try:
    # Send POST request
    response = requests.post(url, json=payload)
    
    # Print response status
    print(f"Status Code: {response.status_code}")
    
    # Try to parse JSON response
    try:
        json_response = response.json()
        print("Response JSON:")
        # print(json.dumps(json_response, indent=2))
        with open("last_response.json", "w", encoding="utf-8") as f:
            json.dump(json_response, f, indent=2, ensure_ascii=False)
            print("✅ JSON response written to 'last_response.json'")
    except requests.exceptions.JSONDecodeError:
        print("Response is not valid JSON:")
        print(f"Response text: '{response.text}'")
        print(f"Response headers: {dict(response.headers)}")
    
    # Test the step endpoint if initialization was successful
    # if response.status_code == 200:
    #     print("\nTesting step endpoint...")
    #     step_response = requests.post("http://localhost:5000/step")
    #     print(f"Step Status Code: {step_response.status_code}")
    #     try:
    #         step_json = step_response.json()
    #         print("Step Response JSON:")
    #         print(json.dumps(step_json, indent=2))
    #     except requests.exceptions.JSONDecodeError:
    #         print("Step response is not valid JSON:")
    #         print(f"Step response text: '{step_response.text}'")

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server. Make sure your Flask app is running on localhost:5000")
except Exception as e:
    print(f"Unexpected error: {e}")