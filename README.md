# Batch TIN Verification

A Python script for batch processing Taxpayer Identification Number (TIN) verification using the Vouched API.

## Features

- **Batch Processing**: Process multiple TIN verifications from a CSV file
- **Comprehensive Logging**: Detailed logging of all API requests and responses
- **Error Handling**: Robust error handling for network issues and API errors
- **JSON Output**: Results saved in both structured JSON and raw response formats
- **DataFrame Integration**: Seamlessly integrates API responses with original data

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API credentials:
```bash
VOUCHED_PRIVATE_API_KEY=your_api_key_here
CALLBACK_URL=https://your-domain.com/callback  # Optional
```

## Input File Format

Your CSV file must contain the following columns:
- `firstName`: First name of the person
- `lastName`: Last name of the person  
- `tin`: Taxpayer Identification Number
- `phone`: Phone number

Example CSV:
```csv
firstName,lastName,tin,phone
John,Doe,123456789,555-1234
Jane,Smith,987654321,555-5678
```

## Usage

Run the script:
```bash
python main.py
```

The script will prompt you for the path to your CSV file and then process each row.

## Output Files

The script generates several output files:

1. **`tin_verification_results.csv`**: Main results file with original data plus all API response fields as separate columns
2. **`response_structure.json`**: Summary of all response fields found in the API responses
3. **`raw_api_responses.json`**: Raw API responses for debugging
4. **`tin_verification.log`**: Detailed log file with all operations

## API Response Integration

The script automatically parses API responses and adds them as new columns to your original DataFrame:

- `api_status_code`: HTTP status code from the API
- `api_success`: Boolean indicating if the request was successful
- `api_error`: Error message if the request failed
- `api_response_*`: Individual fields from the API response (dynamically added based on response structure)

### JSON Response Parsing

The script extracts only the essential fields from the API response:

- **`id`**: The unique identifier for the verification request
- **`submitted`**: The timestamp when the request was submitted
- **`result.status`**: The verification result status (e.g., "MATCH", "NO_MATCH")

Example: If the API returns:
```json
{
  "id": "ABC123",
  "status": "completed",
  "completed": true,
  "submitted": "2025-10-06T20:21:08.438Z",
  "updatedAt": "2025-10-06T20:21:08.438Z",
  "request": {
    "phone": "2065551234",
    "tinType": "ITIN",
    "lastName": "Smith",
    "firstName": "John"
  },
  "result": {
    "status": "MATCH",
    "tinType": "ITIN"
  }
}
```

The CSV will have columns:
- `api_response_id` (e.g., "wFc9rmU1d")
- `api_response_submitted` (e.g., "2025-10-06T20:21:08.438Z")
- `api_response_result_status` (e.g., "MATCH")

**Note**: Request information and other response fields are not included in the output to keep the data focused on verification results.

## Error Handling

The script captures the exact API responses for all scenarios:
- **Successful requests (200)**: Extracts `id`, `submitted`, and `result.status`
- **API errors (4xx, 5xx)**: Captures the exact error response from the API
- **Network timeouts**: Logs timeout information
- **Request exceptions**: Captures any response content if available
- **Missing or invalid input data**: Validates input before processing
- **File I/O errors**: Handles file operations gracefully

All responses (successful and error) are logged with their exact content, and the script continues processing remaining rows.
