from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
import re
from datetime import datetime

uploads_bp = Blueprint('uploads', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route('/upload_issuers', methods=['GET', 'POST'])
def upload_issuers():
    if request.method == 'POST':
        # Check if we're in the file upload phase or the mapping phase
        if 'file' in request.files:
            # File upload phase
            file = request.files['file']
            
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                # Read the file to get column headers
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:  # Excel file
                    df = pd.read_excel(file_path)
                
                # Get column headers
                columns = df.columns.tolist()
                
                # Define required fields
                required_fields = ['issuer_name']
                
                # Define optional fields
                optional_fields = []
                for i in range(1, 6):
                    optional_fields.append(f'contact_name_{i}')
                    optional_fields.append(f'contact_email_{i}')
                
                # Auto-map fields where possible
                field_mapping = {}
                for field in required_fields + optional_fields:
                    if field in columns:
                        field_mapping[field] = field
                
                # Store the file path and mapping in session for the next step
                session['temp_file_path'] = file_path
                session['file_columns'] = columns
                session['field_mapping'] = field_mapping
                session['required_fields'] = required_fields
                session['optional_fields'] = optional_fields
                
                return render_template('map_columns.html', 
                                      columns=columns, 
                                      required_fields=required_fields,
                                      optional_fields=optional_fields,
                                      field_mapping=field_mapping)
        
        elif 'map_fields' in request.form:
            # Mapping phase - process the mapping and the file
            field_mapping = {}
            required_fields = session.get('required_fields', [])
            
            # Get the mapping from the form
            for field in required_fields + session.get('optional_fields', []):
                mapped_column = request.form.get(field)
                if mapped_column:
                    field_mapping[field] = mapped_column
            
            # Get custom field mappings
            custom_fields = {}
            for i in range(1, 9):  # Up to 8 custom fields
                custom_field_key = f'custom_field_{i}'
                if custom_field_key in request.form and request.form[custom_field_key]:
                    original_column = request.form[custom_field_key]
                    custom_fields[original_column] = f'Custom Field {i}'
            
            # Check if all required fields are mapped
            missing_fields = [field for field in required_fields if field not in field_mapping]
            if missing_fields:
                flash(f'Required fields not mapped: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('uploads.upload_issuers'))
            
            # Process the file with the mapping
            try:
                file_path = session.get('temp_file_path')
                process_issuer_file(file_path, field_mapping, custom_fields)
                flash('Issuer information uploaded successfully', 'success')
                
                # Clean up
                os.remove(file_path)
                session.pop('temp_file_path', None)
                session.pop('file_columns', None)
                session.pop('field_mapping', None)
                session.pop('required_fields', None)
                session.pop('optional_fields', None)
                
                # Redirect to dashboard (use the correct URL)
                return redirect('/')  # Redirect to home page for now
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('uploads.upload_issuers'))
    
    return render_template('upload_issuers.html')

@uploads_bp.route('/upload_securities', methods=['GET', 'POST'])
def upload_securities():
    if request.method == 'POST':
        # Check if we're in the file upload phase or the mapping phase
        if 'file' in request.files:
            # File upload phase
            file = request.files['file']
            
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                # Read the file to get column headers
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:  # Excel file
                    df = pd.read_excel(file_path)
                
                # Get column headers
                columns = df.columns.tolist()
                
                # Define required fields
                required_fields = ['security_id', 'ISIN', 'issuer', 'description']
                
                # Define optional fields
                optional_fields = ['currency', 'maturity_date']
                
                # Auto-map fields where possible
                field_mapping = {}
                for field in required_fields + optional_fields:
                    if field in columns:
                        field_mapping[field] = field
                
                # Store the file path and mapping in session for the next step
                session['temp_file_path'] = file_path
                session['file_columns'] = columns
                session['field_mapping'] = field_mapping
                session['required_fields'] = required_fields
                session['optional_fields'] = optional_fields
                
                return render_template('map_securities.html', 
                                      columns=columns, 
                                      required_fields=required_fields,
                                      optional_fields=optional_fields,
                                      field_mapping=field_mapping)
        
        elif 'map_fields' in request.form:
            # Mapping phase - process the mapping and the file
            field_mapping = {}
            required_fields = session.get('required_fields', [])
            
            # Get the mapping from the form
            for field in required_fields + session.get('optional_fields', []):
                mapped_column = request.form.get(field)
                if mapped_column:
                    field_mapping[field] = mapped_column
            
            # Get custom field mappings
            custom_fields = {}
            for i in range(1, 9):  # Up to 8 custom fields
                custom_field_key = f'custom_field_{i}'
                if custom_field_key in request.form and request.form[custom_field_key]:
                    original_column = request.form[custom_field_key]
                    custom_fields[original_column] = f'Custom Field {i}'
            
            # Check if all required fields are mapped
            missing_fields = [field for field in required_fields if field not in field_mapping]
            if missing_fields:
                flash(f'Required fields not mapped: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('uploads.upload_securities'))
            
            # Process the file with the mapping
            try:
                file_path = session.get('temp_file_path')
                process_securities_file(file_path, field_mapping, custom_fields)
                flash('Security information uploaded successfully', 'success')
                
                # Clean up
                os.remove(file_path)
                session.pop('temp_file_path', None)
                session.pop('file_columns', None)
                session.pop('field_mapping', None)
                session.pop('required_fields', None)
                session.pop('optional_fields', None)
                
                # Redirect to dashboard (use the correct URL)
                return redirect('/')  # Redirect to home page for now
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('uploads.upload_securities'))
    
    return render_template('upload_securities.html')

def process_issuer_file(file_path, field_mapping, custom_fields=None):
    # Determine file type and read accordingly
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # Excel file
        df = pd.read_excel(file_path)
    
    # Print debug information
    print("Field mapping:", field_mapping)
    print("First row of data:", df.iloc[0].to_dict())
    print("DataFrame columns:", df.columns.tolist())
    
    # Load existing issuers data if available
    issuers_file = 'storage/issuers.json'
    os.makedirs(os.path.dirname(issuers_file), exist_ok=True)
    
    if os.path.exists(issuers_file):
        with open(issuers_file, 'r') as f:
            issuers_data = json.load(f)
    else:
        issuers_data = {}
    
    # Process each row in the dataframe
    validation_errors = []
    processed_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because idx is 0-based and we skip header row
        
        try:
            # Get issuer name using the mapping
            issuer_name_col = field_mapping.get('issuer_name')
            if not issuer_name_col or pd.isna(row[issuer_name_col]):
                validation_errors.append(f"Row {row_num}: Missing issuer_name")
                continue
            
            issuer_name = str(row[issuer_name_col]).strip()
            
            # Create or update issuer entry
            if issuer_name not in issuers_data:
                issuers_data[issuer_name] = {
                    'contacts': []
                }
            
            # Process contacts - look for any columns that might contain contact information
            contacts = []
            
            # Check if we have explicit contact name/email mappings
            has_explicit_contacts = False
            for i in range(1, 6):
                name_col = field_mapping.get(f'contact_name_{i}')
                email_col = field_mapping.get(f'contact_email_{i}')
                
                if name_col and email_col and name_col in row.index and email_col in row.index:
                    has_explicit_contacts = True
                    if not pd.isna(row[name_col]) and not pd.isna(row[email_col]):
                        contact_name = str(row[name_col]).strip()
                        contact_email = str(row[email_col]).strip()
                        
                        # Basic email validation
                        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                        if contact_email and not email_pattern.match(contact_email):
                            validation_errors.append(f"Row {row_num}: Invalid email format for {contact_name}")
                            continue
                        
                        contacts.append({
                            'name': contact_name,
                            'email': contact_email
                        })
            
            # If no explicit contacts were mapped, look for columns that might contain contact info
            if not has_explicit_contacts:
                # Look for columns named "Contact X" or similar
                contact_cols = [col for col in df.columns if 'contact' in col.lower() or 'email' in col.lower()]
                
                for col in contact_cols:
                    if not pd.isna(row[col]):
                        value = str(row[col]).strip()
                        
                        # Check if it looks like an email
                        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                        if email_pattern.match(value):
                            # Use the column name as the contact name if it's an email
                            contact_name = col.replace('_', ' ').title()
                            contacts.append({
                                'name': contact_name,
                                'email': value
                            })
            
            # Process custom fields
            if custom_fields:
                if 'custom_fields' not in issuers_data[issuer_name]:
                    issuers_data[issuer_name]['custom_fields'] = {}
                
                for original_col, custom_field_name in custom_fields.items():
                    if original_col in df.columns and not pd.isna(row[original_col]):
                        issuers_data[issuer_name]['custom_fields'][custom_field_name] = str(row[original_col])
            
            # Update the contacts array
            if contacts:
                issuers_data[issuer_name]['contacts'] = contacts
            
            processed_count += 1
            
        except Exception as e:
            validation_errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
            print(f"Exception in row {row_num}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Check if any issuers were processed
    if processed_count == 0:
        if validation_errors:
            raise ValueError(f"No issuers were processed due to validation errors: {'; '.join(validation_errors[:5])}" + 
                            (f" and {len(validation_errors) - 5} more errors" if len(validation_errors) > 5 else ""))
        else:
            raise ValueError("No valid issuers found in the file")
    
    # Save updated issuers data
    with open(issuers_file, 'w') as f:
        json.dump(issuers_data, f, indent=4)
    
    # Print the final data for debugging
    print("Final issuers data:", issuers_data)
    
    # Return summary
    return {
        'processed': processed_count,
        'errors': validation_errors
    }

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
    os.makedirs(os.path.dirname(securities_file), exist_ok=True)
    
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
            
            # Validate ISIN format (2 letters followed by 10 alphanumeric characters)
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