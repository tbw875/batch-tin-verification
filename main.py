#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import requests as r
import pandas as pd

# Constants
VOUCHED_PRIVATE_API_KEY = os.getenv('VOUCHED_PRIVATE_API_KEY')
TIN_ENDPOINT = 'https://verify.vouched.id/api/tin/verify'
CALLBACK_URL = os.getenv('CALLBACK_URL')

def load_file(file_path):
    # Fetch file from user input
    file_path = input('Enter the path to the file: ')
    df = pd.read_csv(file_path)

    # Verify the file contents has columns ['firstName','lastName','tin','phone']
    if not all(col in df.columns for col in ['firstName','lastName','tin','phone']):
        raise ValueError('File must have columns ["firstName","lastName","tin","phone"]')
    return df

# For each row in the dataframe, make a request to the Vouched API
def run_tin_verification(row):
    payload = {
        'firstName': row['firstName'],
        'lastName': row['lastName'],
        'tin': row['tin'],
        'phone': row['phone'],
        'tinType': 'ITIN'
        'callbackUrl': CALLBACK_URL}
    response = r.post(TIN_ENDPOINT, headers={f'X-API-Key: {VOUCHED_PRIVATE_API_KEY}'}, json=payload)

    # Basic logging
    print(f'Row {row.index}: {response.status_code}')
    
    # For each response, save the response to a csv file
    with open('responses.csv', 'a') as f:
        f.write(response.json())
    return response.json()

def main():
    df = load_file()
    for index, row in df.iterrows():
        run_tin_verification(row)

if __name__ == "__main__":
    main()
