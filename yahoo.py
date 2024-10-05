import yfinance as yf
import time
import json
import os

# File to store the JSON data
json_file = 'nifty_fin_service_data_new.json'

# Create an empty list to store the rows if the file doesn't exist
if not os.path.exists(json_file):
    with open(json_file, 'w') as f:
        json.dump([], f)

while True:
    # Download the data
    data = yf.download("RELIANCE.NS", period="1d", interval="1m")

    # Check if there are at least 2 rows
    if len(data) >= 2:
        # Get the second-to-last row as a dictionary
        row_to_append = data.iloc[-2].to_dict()

        # Get the corresponding datetime from the index
        datetime_to_append = data.index[-2].isoformat()  # Convert datetime to ISO format

        # Include datetime in the row
        row_to_append['datetime'] = datetime_to_append

        # Read the existing data from the JSON file
        with open(json_file, 'r') as f:
            existing_data = json.load(f)

        # Append the new row
        existing_data.append(row_to_append)

        # Write the updated data back to the JSON file
        with open(json_file, 'w') as f:
            json.dump(existing_data, f, indent=4)

        print(f"Appended row: {row_to_append}")

    # Wait for 60 seconds before fetching again
    time.sleep(60)