from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd

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
                
                return redirect(url_for('dashboard'))
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
                process_security_file(file_path, field_mapping, custom_fields)
                flash('Security information uploaded successfully', 'success')
                
                # Clean up
                os.remove(file_path)
                session.pop('temp_file_path', None)
                session.pop('file_columns', None)
                session.pop('field_mapping', None)
                session.pop('required_fields', None)
                session.pop('optional_fields', None)
                
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('uploads.upload_securities'))
    
    return render_template('upload_securities.html') 