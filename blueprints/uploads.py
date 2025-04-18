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
    if 'user' not in session or session.get('role') != 'custodian':
        flash('You must be logged in as a custodian to upload issuer information.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                try:
                    # Read the file to get column headers
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:  # Excel file
                        df = pd.read_excel(file_path)
                    
                    columns = df.columns.tolist()
                    
                    # Define required and optional fields
                    required_fields = ['issuer_name']
                    optional_fields = []
                    for i in range(1, 6):  # Up to 5 contacts
                        optional_fields.extend([f'contact_name_{i}', f'contact_email_{i}'])
                    
                    # Auto-map fields where possible
                    field_mapping = {}
                    for field in required_fields + optional_fields:
                        if field in columns:
                            field_mapping[field] = field
                    
                    # Store in session
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
                except Exception as e:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    flash(f'Error processing file: {str(e)}', 'danger')
                    return redirect(url_for('custodian.dashboard'))
        
        elif 'map_fields' in request.form:
            try:
                file_path = session.get('temp_file_path')
                if not file_path:
                    raise ValueError("No file uploaded")
                
                # Get field mapping from form
                field_mapping = {}
                required_fields = session.get('required_fields', [])
                optional_fields = session.get('optional_fields', [])
                
                # Process required fields
                for field in required_fields:
                    mapped_column = request.form.get(field)
                    if mapped_column:
                        field_mapping[field] = mapped_column
                
                # Process optional fields
                for field in optional_fields:
                    mapped_column = request.form.get(field)
                    if mapped_column:
                        field_mapping[field] = mapped_column
                
                # Process the file with mapping
                result = process_issuer_file(file_path, field_mapping)
                
                if result['errors']:
                    error_messages = '; '.join(result['errors'][:3])  # Show first 3 errors
                    flash(f"Processed {result['processed']} issuers with errors: {error_messages}", 'warning')
                else:
                    flash(f"Successfully processed {result['processed']} issuers", 'success')
                
                # Clean up
                if os.path.exists(file_path):
                    os.remove(file_path)
                session.pop('temp_file_path', None)
                session.pop('file_columns', None)
                session.pop('field_mapping', None)
                session.pop('required_fields', None)
                session.pop('optional_fields', None)
                
                return redirect(url_for('custodian.dashboard'))
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('custodian.dashboard'))
    
    return render_template('upload_issuers.html')

@uploads_bp.route('/upload_securities', methods=['GET', 'POST'])
def upload_securities():
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:  # Excel file
                    df = pd.read_excel(file_path)
                
                columns = df.columns.tolist()
                
                required_fields = ['security_id', 'ISIN', 'issuer', 'description']
                
                optional_fields = ['currency', 'maturity_date']
                
                field_mapping = {}
                for field in required_fields + optional_fields:
                    if field in columns:
                        field_mapping[field] = field
                
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
            field_mapping = {}
            required_fields = session.get('required_fields', [])
            
            for field in required_fields + session.get('optional_fields', []):
                mapped_column = request.form.get(field)
                if mapped_column:
                    field_mapping[field] = mapped_column
            
            custom_fields = {}
            for i in range(1, 9):  # Up to 8 custom fields
                custom_field_key = f'custom_field_{i}'
                if custom_field_key in request.form and request.form[custom_field_key]:
                    original_column = request.form[custom_field_key]
                    custom_fields[original_column] = f'Custom Field {i}'
            
            missing_fields = [field for field in required_fields if field not in field_mapping]
            if missing_fields:
                flash(f'Required fields not mapped: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('uploads.upload_securities'))
            
            try:
                file_path = session.get('temp_file_path')
                process_securities_file(file_path, field_mapping, custom_fields)
                flash('Security information uploaded successfully', 'success')
                
                os.remove(file_path)
                session.pop('temp_file_path', None)
                session.pop('file_columns', None)
                session.pop('field_mapping', None)
                session.pop('required_fields', None)
                session.pop('optional_fields', None)
                
                return redirect('/')  # Redirect to home page for now
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('uploads.upload_securities'))
    
    return render_template('upload_securities.html')

def process_issuer_file(file_path, field_mapping):
    if 'user' not in session or session.get('role') != 'custodian':
        raise ValueError("Unauthorized access")
    
    custodian = session['user']
    
    # Debug logging
    print(f"Processing file: {file_path}")
    print(f"Field mapping: {field_mapping}")
    
    # Read the file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # Excel file
        df = pd.read_excel(file_path)
    
    # Debug logging
    print(f"DataFrame columns: {df.columns.tolist()}")
    print(f"First row of data: {df.iloc[0].to_dict()}")
    
    # Load or create issuers file
    issuers_file = 'storage/issuers.json'
    os.makedirs(os.path.dirname(issuers_file), exist_ok=True)
    
    if os.path.exists(issuers_file):
        with open(issuers_file, 'r') as f:
            issuers_data = json.load(f)
    else:
        issuers_data = {}
    
    validation_errors = []
    processed_count = 0
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Get issuer name using mapped column
            issuer_name_col = field_mapping.get('issuer_name')
            print(f"Looking for issuer name in column: {issuer_name_col}")
            
            if not issuer_name_col:
                validation_errors.append(f"Row {idx + 2}: Issuer name column not mapped")
                continue
            
            if pd.isna(row[issuer_name_col]):
                validation_errors.append(f"Row {idx + 2}: Missing issuer name")
                continue
            
            issuer_name = str(row[issuer_name_col]).strip()
            print(f"Processing issuer: {issuer_name}")
            
            # Create or update issuer entry
            if issuer_name not in issuers_data:
                issuers_data[issuer_name] = {
                    'custodian': custodian,
                    'contacts': []
                }
            elif issuers_data[issuer_name].get('custodian') != custodian:
                validation_errors.append(f"Row {idx + 2}: Issuer '{issuer_name}' is already associated with another custodian")
                continue
            
            # Process contacts
            contacts = []
            for i in range(1, 6):
                name_col = field_mapping.get(f'contact_name_{i}')
                email_col = field_mapping.get(f'contact_email_{i}')
                
                if name_col and email_col and not pd.isna(row[name_col]) and not pd.isna(row[email_col]):
                    contact_name = str(row[name_col]).strip()
                    contact_email = str(row[email_col]).strip()
                    
                    # Basic email validation
                    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                    if not email_pattern.match(contact_email):
                        validation_errors.append(f"Row {idx + 2}: Invalid email format for contact {i}")
                        continue
                    
                    contacts.append({
                        'name': contact_name,
                        'email': contact_email
                    })
            
            if contacts:
                issuers_data[issuer_name]['contacts'] = contacts
            
            processed_count += 1
            print(f"Successfully processed issuer: {issuer_name}")
            
        except Exception as e:
            print(f"Error processing row {idx + 2}: {str(e)}")
            validation_errors.append(f"Row {idx + 2}: Unexpected error: {str(e)}")
    
    # Save the updated data
    with open(issuers_file, 'w') as f:
        json.dump(issuers_data, f, indent=4)
    
    print(f"Processing complete. Processed: {processed_count}, Errors: {len(validation_errors)}")
    return {
        'processed': processed_count,
        'errors': validation_errors
    }

def process_securities_file(file_path, field_mapping, custom_fields=None):
    if 'user' not in session or session.get('role') != 'custodian':
        raise ValueError("Unauthorized access")
    
    custodian = session['user']
    
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # Excel file
        df = pd.read_excel(file_path)
    
    # Load issuers data to validate and get contact information
    issuers_file = 'storage/issuers.json'
    if not os.path.exists(issuers_file):
        raise ValueError("No issuers found. Please upload issuer information first.")
    
    with open(issuers_file, 'r') as f:
        issuers_data = json.load(f)
    
    # Load or create securities file
    securities_file = 'storage/securities.json'
    os.makedirs(os.path.dirname(securities_file), exist_ok=True)
    
    if os.path.exists(securities_file):
        with open(securities_file, 'r') as f:
            securities_data = json.load(f)
    else:
        securities_data = {}
    
    validation_errors = []
    processed_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        try:
            # Get required fields
            security_id_col = field_mapping.get('security_id')
            isin_col = field_mapping.get('ISIN')
            issuer_col = field_mapping.get('issuer')
            description_col = field_mapping.get('description')
            
            # Validate required fields presence
            if not all([security_id_col, isin_col, issuer_col, description_col]):
                missing_fields = [field for field, col in {
                    'security_id': security_id_col,
                    'ISIN': isin_col,
                    'issuer': issuer_col,
                    'description': description_col
                }.items() if not col]
                validation_errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                continue
            
            # Get values
            security_id = str(row[security_id_col]).strip()
            isin = str(row[isin_col]).strip()
            issuer = str(row[issuer_col]).strip()
            description = str(row[description_col]).strip()
            
            # Validate issuer exists and belongs to current custodian
            if issuer not in issuers_data:
                validation_errors.append(f"Row {row_num}: Issuer '{issuer}' not found")
                continue
            
            issuer_info = issuers_data[issuer]
            if issuer_info.get('custodian') != custodian:
                validation_errors.append(f"Row {row_num}: Issuer '{issuer}' is not associated with your account")
                continue
            
            # Validate ISIN format
            isin_pattern = re.compile(r'^[A-Z]{2}[0-9A-Z]{10}$')
            if not isin_pattern.match(isin):
                validation_errors.append(f"Row {row_num}: Invalid ISIN format for '{isin}'")
                continue
            
            # Get optional fields
            currency = None
            if 'currency' in field_mapping and not pd.isna(row[field_mapping['currency']]):
                currency = str(row[field_mapping['currency']]).strip().upper()
                if len(currency) != 3:
                    validation_errors.append(f"Row {row_num}: Currency code must be 3 characters")
                    continue
            else:
                currency = "USD"
            
            # Process maturity date
            maturity_date = None
            if 'maturity_date' in field_mapping and not pd.isna(row[field_mapping['maturity_date']]):
                try:
                    date_val = row[field_mapping['maturity_date']]
                    if isinstance(date_val, datetime):
                        maturity_date = date_val.strftime('%Y-%m-%d')
                    else:
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                            try:
                                maturity_date = datetime.strptime(str(date_val), fmt).strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    validation_errors.append(f"Row {row_num}: Invalid date format - {str(e)}")
                    continue
            
            # Create security entry with issuer contact information
            security_data = {
                'security_id': security_id,
                'ISIN': isin,
                'currency': currency,
                'issuer': issuer,
                'description': description,
                'custodian': custodian,
                'issuer_contacts': issuer_info.get('contacts', []),
                'custom_fields': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if maturity_date:
                security_data['maturity_date'] = maturity_date
            
            # Process custom fields
            if custom_fields:
                for original_col, custom_field_name in custom_fields.items():
                    if original_col in df.columns and not pd.isna(row[original_col]):
                        security_data['custom_fields'][custom_field_name] = str(row[original_col]).strip()
            
            # Save security data
            securities_data[security_id] = security_data
            processed_count += 1
            
        except Exception as e:
            validation_errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
    
    if processed_count == 0:
        if validation_errors:
            raise ValueError(f"No securities were processed due to errors: {'; '.join(validation_errors[:3])}")
        else:
            raise ValueError("No valid securities found in the file")
    
    # Save updated securities data
    with open(securities_file, 'w') as f:
        json.dump(securities_data, f, indent=4)
    
    return {
        'processed': processed_count,
        'errors': validation_errors
    } 