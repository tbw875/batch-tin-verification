#!/usr/bin/env python3

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests as r
import pandas as pd

# Load environment variables
load_dotenv()

# Constants
VOUCHED_PRIVATE_API_KEY = os.getenv('VOUCHED_PRIVATE_API_KEY')
TIN_ENDPOINT = 'https://verify.vouched.id/api/tin/verify'
CALLBACK_URL = os.getenv('CALLBACK_URL')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tin_verification.log'),
        logging.StreamHandler()
    ]
)

def load_file(file_path=None):
    """Load and validate the input CSV file."""
    if file_path is None:
        file_path = input('Enter the path to the file: ')
    
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Loaded file: {file_path} with {len(df)} rows")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading file: {e}")
        raise

    # Verify the file contents has required columns
    required_columns = ['firstName', 'lastName', 'tin', 'phone']
    if not all(col in df.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df.columns]
        error_msg = f'File must have columns {required_columns}. Missing: {missing_cols}'
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for empty values in required columns
    for col in required_columns:
        if df[col].isna().any():
            logging.warning(f"Found empty values in column '{col}'")
    
    return df

def run_tin_verification(row, index):
    """Make a request to the Vouched TIN Verification API for a single row."""
    try:
        payload = {
            'firstName': str(row['firstName']).strip(),
            'lastName': str(row['lastName']).strip(),
            'tin': str(row['tin']).strip(),
            'phone': str(row['phone']).strip(),
            'tinType': 'ITIN',
            'callbackUrl': CALLBACK_URL
        }
        
        headers = {
            'X-API-Key': VOUCHED_PRIVATE_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = r.post(TIN_ENDPOINT, headers=headers, json=payload, timeout=30)
        
        logging.info(f"Row {index}: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            return {
                'status_code': response.status_code,
                'success': True,
                'response': response_data,
                'error': None
            }
        else:
            error_msg = f"API request failed with status {response.status_code}"
            logging.error(f"Row {index}: {error_msg}")
            return {
                'status_code': response.status_code,
                'success': False,
                'response': None,
                'error': error_msg
            }
            
    except r.exceptions.Timeout:
        error_msg = "Request timeout"
        logging.error(f"Row {index}: {error_msg}")
        return {
            'status_code': None,
            'success': False,
            'response': None,
            'error': error_msg
        }
    except r.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logging.error(f"Row {index}: {error_msg}")
        return {
            'status_code': None,
            'success': False,
            'response': None,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logging.error(f"Row {index}: {error_msg}")
        return {
            'status_code': None,
            'success': False,
            'response': None,
            'error': error_msg
        }

def extract_specific_fields(json_obj):
    """Extract only the specific fields we want from the API response."""
    extracted = {}
    
    if isinstance(json_obj, dict):
        # Extract id
        if 'id' in json_obj:
            extracted['id'] = json_obj['id']
        
        # Extract submitted (from submitted field)
        if 'submitted' in json_obj:
            extracted['submitted'] = json_obj['submitted']
        
        # Extract result.status (nested field)
        if 'result' in json_obj and isinstance(json_obj['result'], dict):
            if 'status' in json_obj['result']:
                extracted['result_status'] = json_obj['result']['status']
    
    return extracted

def save_results_to_csv(df, results, output_file='tin_verification_results.csv'):
    """Save the original DataFrame with API results to a CSV file."""
    try:
        # Create a copy of the original DataFrame
        result_df = df.copy()
        
        # Add basic API result columns
        result_df['api_status_code'] = [r['status_code'] for r in results]
        result_df['api_success'] = [r['success'] for r in results]
        result_df['api_error'] = [r['error'] for r in results]
        
        # Collect all possible response columns from all responses
        all_response_columns = set()
        extracted_responses = []
        
        for result in results:
            if result['success'] and result['response']:
                # Extract only the specific fields we want
                extracted = extract_specific_fields(result['response'])
                extracted_responses.append(extracted)
                all_response_columns.update(extracted.keys())
            else:
                extracted_responses.append({})
        
        # Add all response columns to DataFrame
        for col in sorted(all_response_columns):
            result_df[f'api_response_{col}'] = None
            for i, extracted in enumerate(extracted_responses):
                if extracted:
                    result_df.at[i, f'api_response_{col}'] = extracted.get(col)
        
        # Save to CSV
        result_df.to_csv(output_file, index=False)
        logging.info(f"Results saved to {output_file}")
        
        # Also save a summary of the response structure
        if all_response_columns:
            response_structure = {
                'extracted_columns': sorted(list(all_response_columns)),
                'total_columns': len(all_response_columns),
                'sample_extracted_response': extracted_responses[0] if extracted_responses else {},
                'note': 'Only extracting: id, submitted, and result.status from API responses'
            }
            with open('response_structure.json', 'w') as f:
                json.dump(response_structure, f, indent=2)
            logging.info("Response structure saved to response_structure.json")
        
        return result_df
        
    except Exception as e:
        logging.error(f"Error saving results to CSV: {e}")
        raise

def save_raw_responses(results, output_file='raw_api_responses.json'):
    """Save raw API responses for debugging purposes."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"Raw responses saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving raw responses: {e}")

def main():
    """Main function to orchestrate the TIN verification process."""
    try:
        # Validate environment variables
        if not VOUCHED_PRIVATE_API_KEY:
            logging.error("VOUCHED_PRIVATE_API_KEY environment variable is not set")
            raise ValueError("VOUCHED_PRIVATE_API_KEY environment variable is required")
        
        if not CALLBACK_URL:
            logging.warning("CALLBACK_URL environment variable is not set - callbacks will not work")
        
        # Load the input file
        df = load_file()
        
        # Initialize results list
        results = []
        
        # Process each row
        logging.info(f"Starting TIN verification for {len(df)} rows")
        for index, row in df.iterrows():
            result = run_tin_verification(row, index)
            results.append(result)
        
        # Save results
        result_df = save_results_to_csv(df, results)
        save_raw_responses(results)
        
        # Print summary
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = len(results) - successful_requests
        
        logging.info(f"Processing complete. Successful: {successful_requests}, Failed: {failed_requests}")
        print(f"\nTIN Verification Complete!")
        print(f"Total rows processed: {len(df)}")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Results saved to: tin_verification_results.csv")
        print(f"Response structure saved to: response_structure.json")
        print(f"Raw responses saved to: raw_api_responses.json")
        print(f"Log file: tin_verification.log")
        
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()