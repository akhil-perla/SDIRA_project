import pandas as pd
import json
import os

def process_issuer_file(file_path, custodian_username):
    # Determine file type and read accordingly
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # Excel file
        df = pd.read_excel(file_path)
    
    # Validate required columns
    required_columns = ['issuer_name']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in the file")
    
    # Load existing issuers data if available
    issuers_file = 'storage/issuers.json'
    if os.path.exists(issuers_file):
        with open(issuers_file, 'r') as f:
            issuers_data = json.load(f)
    else:
        issuers_data = {}
    
    # Load user data to verify custodian
    with open('storage/users.json', 'r') as f:
        users_data = json.load(f)
    
    if custodian_username not in users_data or users_data[custodian_username]['role'] != 'custodian':
        raise ValueError("Invalid custodian user")
    
    # Process each row in the dataframe
    for _, row in df.iterrows():
        issuer_name = row['issuer_name']
        
        # Create or update issuer entry
        if issuer_name not in issuers_data:
            issuers_data[issuer_name] = {
                'custodian': custodian_username,
                'contacts': []
            }
        
        # Process contacts (up to 5)
        contacts = []
        for i in range(1, 6):
            name_col = f'contact_name_{i}'
            email_col = f'contact_email_{i}'
            
            if name_col in row and email_col in row and pd.notna(row[name_col]) and pd.notna(row[email_col]):
                contacts.append({
                    'name': row[name_col],
                    'email': row[email_col]
                })
        
        # Update contacts
        issuers_data[issuer_name]['contacts'] = contacts
    
    # Save updated issuers data
    with open(issuers_file, 'w') as f:
        json.dump(issuers_data, f, indent=4) 