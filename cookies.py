import time
import requests

SERVER_URL = "http://13.61.152.136:5000"  # replace with your EC2 IP or domain

def acquire_cookie(retry_delay=60):
    """
    Try to acquire a cookie from the server.
    If none is available, sleep and retry until successful.
    """
    while True:
        try:
            response = requests.post(f"{SERVER_URL}/start")
            data = response.json()
            
            if data.get("cookie_file"):
                print(f"✅ Acquired cookie: {data['cookie_file']}")
                return data["cookie_file"]
            else:
                print(f"❌ No cookie available, retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        except Exception as e:
            print(f"⚠️ Error connecting to server: {e}")
            time.sleep(retry_delay)


def release_cookie(cookie_file):
    """
    Release the cookie back to the server.
    """
    try:
        response = requests.post(f"{SERVER_URL}/end", json={"cookie_file": cookie_file})
        data = response.json()
        print(f"🔄 Released cookie: {cookie_file}, server says: {data}")
    except Exception as e:
        print(f"⚠️ Error releasing cookie: {e}")
