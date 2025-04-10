import os
import json
import pandas as pd
import re
from datetime import datetime

def process_securities_file(file_path, field_mapping, custom_fields=None):
    # Determine file type and read accordingly
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # Excel file
        df = pd.read_excel(file_path)
    
    # Load existing issuers data to validate issuer references
    issuers_file = 'storage/issuers.json'
    if not os.path.exists(issuers_file):
        raise ValueError("No issuers found. Please upload issuer information first.")
    
    with open(issuers_file, 'r') as f:
        issuers_data = json.load(f)
    
    # Load existing securities data if available
    securities_file = 'storage/securities.json'
    if os.path.exists(securities_file):
        with open(securities_file, 'r') as f:
            securities_data = json.load(f)
    else:
        securities_data = {}
    
    # Process each row in the dataframe
    validation_errors = []
    processed_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because idx is 0-based and we skip header row
        
        try:
            # Get required fields using the mapping
            security_id_col = field_mapping.get('security_id')
            isin_col = field_mapping.get('ISIN')
            issuer_col = field_mapping.get('issuer')
            description_col = field_mapping.get('description')
            
            # Check if required fields exist and are not empty
            if not security_id_col or pd.isna(row[security_id_col]):
                validation_errors.append(f"Row {row_num}: Missing security_id")
                continue
                
            if not isin_col or pd.isna(row[isin_col]):
                validation_errors.append(f"Row {row_num}: Missing ISIN")
                continue
                
            if not issuer_col or pd.isna(row[issuer_col]):
                validation_errors.append(f"Row {row_num}: Missing issuer")
                continue
                
            if not description_col or pd.isna(row[description_col]):
                validation_errors.append(f"Row {row_num}: Missing description")
                continue
            
            # Get values
            security_id = str(row[security_id_col])
            isin = str(row[isin_col])
            issuer = str(row[issuer_col])
            description = str(row[description_col])
            
            # Validate security_id length
            if len(security_id) > 13:
                validation_errors.append(f"Row {row_num}: security_id exceeds 13 characters")
                continue
            
            # Validate ISIN format (2 letters followed by 10 digits)
            isin_pattern = re.compile(r'^[A-Z]{2}[0-9A-Z]{10}$')
            if not isin_pattern.match(isin):
                validation_errors.append(f"Row {row_num}: Invalid ISIN format. Must be 2 letters followed by 10 alphanumeric characters")
                continue
            
            # Validate issuer exists
            if issuer not in issuers_data:
                validation_errors.append(f"Row {row_num}: Issuer '{issuer}' not found in uploaded issuers")
                continue
            
            # Validate description length
            if len(description) > 256:
                validation_errors.append(f"Row {row_num}: Description exceeds 256 characters")
                continue
            
            # Get optional fields
            currency = None
            if 'currency' in field_mapping and not pd.isna(row[field_mapping['currency']]):
                currency = str(row[field_mapping['currency']])
                # Validate currency is 3 characters
                if len(currency) != 3:
                    validation_errors.append(f"Row {row_num}: Currency must be 3 characters")
                    continue
            else:
                currency = "USD"  # Default
            
            maturity_date = None
            if 'maturity_date' in field_mapping and not pd.isna(row[field_mapping['maturity_date']]):
                # Try to parse the date
                try:
                    # Handle different date formats
                    date_val = row[field_mapping['maturity_date']]
                    if isinstance(date_val, datetime):
                        maturity_date = date_val.strftime('%Y-%m-%d')
                    else:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                            try:
                                maturity_date = datetime.strptime(str(date_val), fmt).strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                        
                        if not maturity_date:
                            validation_errors.append(f"Row {row_num}: Invalid maturity date format")
                            continue
                except Exception as e:
                    validation_errors.append(f"Row {row_num}: Error parsing maturity date: {str(e)}")
                    continue
            
            # Create security entry
            security_data = {
                'security_id': security_id,
                'ISIN': isin,
                'currency': currency,
                'issuer': issuer,
                'description': description,
                'custom_fields': {}
            }
            
            if maturity_date:
                security_data['maturity_date'] = maturity_date
            
            # Process custom fields
            if custom_fields:
                for original_col, custom_field_name in custom_fields.items():
                    if original_col in df.columns and not pd.isna(row[original_col]):
                        security_data['custom_fields'][custom_field_name] = str(row[original_col])
            
            # Add to securities data
            securities_data[security_id] = security_data
            processed_count += 1
            
        except Exception as e:
            validation_errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
    
    # Check if any securities were processed
    if processed_count == 0:
        if validation_errors:
            raise ValueError(f"No securities were processed due to validation errors: {'; '.join(validation_errors[:5])}" + 
                            (f" and {len(validation_errors) - 5} more errors" if len(validation_errors) > 5 else ""))
        else:
            raise ValueError("No valid securities found in the file")
    
    # Save updated securities data
    with open(securities_file, 'w') as f:
        json.dump(securities_data, f, indent=4)
    
    # Return summary
    return {
        'processed': processed_count,
        'errors': validation_errors
    } 