import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

# Function to fetch PurpleAir sensor status
def fetch_sensor_status(api_key):
    url = ("https://api.purpleair.com/v1/sensors?"
           "fields=sensor_index,name,last_seen,latitude,longitude,rssi&"
           "read_keys=KHZ6YLXBQPD2TFH3,SX0ZMXE1NW72I1CB&"
           "show_only=185129,203577,185115,181253,57955,134468,185085,53495,"
           "203633,203601,203607,203619,203585,159841,203597")
    headers = {
        "X-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

def convert_to_ny_time(unix_time):
    utc_time = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    ny_tz = pytz.timezone('America/New_York')
    ny_time = utc_time.astimezone(ny_tz)
    return ny_time

def determine_status(last_seen_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - last_seen_time

    if time_difference <= timedelta(hours=1):
        return "green"
    elif time_difference <= timedelta(hours=8):
        return "lightgreen"
    elif time_difference <= timedelta(hours=12):
        return "yellow"
    else:
        return "red"
    
def calculate_notes(last_seen_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - last_seen_time
    if(time_difference <= timedelta(hours=1)):
        return 'Sensor online'
    return 'Time since sensor offline'+' '+str(time_difference)

def main():

    st.set_page_config(layout="wide")

    st.title("PurpleAir Sensor Status")

    st.write("Enter your PurpleAir API key to fetch the latest sensor status.")
    
    api_key = st.text_input("API Key (leave blank to use default)")
    use_default = st.checkbox("Use default API key")
    default_api_key = st.secrets["api_key"]

    if st.button("Fetch Latest Status"):
        if use_default or not api_key:
            api_key = default_api_key
        if api_key:
            sensor_data = fetch_sensor_status(api_key)
            if sensor_data:
                fields = sensor_data['fields']
                data = sensor_data['data']
                
                df = pd.DataFrame(data, columns=fields)
                
                df['last_seen'] = df['last_seen'].apply(lambda x: convert_to_ny_time(x))
                df['status'] = df['last_seen'].apply(lambda x: determine_status(x))
                df['notes'] = df['last_seen'].apply(lambda x: calculate_notes(x))

                
                # Define custom colors for the status column
                def color_status(val):
                    color = val
                    return f'background-color: {color}'
                
                st.write("## Sensor Data")
                st.dataframe(df[['sensor_index', 'name', 'last_seen', 'latitude', 'longitude', 'status','notes']].style.applymap(color_status, subset=['status']),height=700)

                st.write("## Status Color Coding")
                st.markdown("""
                    - **Green**: Last seen within 1 hour
                    - **Light Green**: Last seen within 8 hours
                    - **Yellow**: Last seen within 12 hours
                    - **Red**: Last seen more than 12 hours ago
                """)
        else:
            st.warning("Please enter the API Key.")

if __name__ == "__main__":
    main()
