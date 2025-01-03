from flask import Flask, request, jsonify, send_file, send_from_directory
import pandas as pd
import os
import ftfy
import sys
import codecs
import chardet
from datetime import datetime
import csv
from io import BytesIO
import base64

app = Flask(__name__)

# Configure Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def fix_text_encoding(text):
    """
    Fix text encoding using multiple methods.
    Returns the fixed text if successful, or the original text if no fix is needed.
    """
    if not text:
        return text

    # Method 1: UTF-8 -> Latin1 -> UTF-8
    try:
        fixed_text = text.encode('latin1').decode('utf-8')
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    # Method 2: Use ftfy library
    try:
        fixed_text = ftfy.fix_text(text)
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    # Method 3: CP1252 -> UTF-8
    try:
        fixed_text = text.encode('cp1252').decode('utf-8')
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    return text

def detect_encoding(file_path):
    """
    Detect the encoding of a file using chardet.
    Returns the detected encoding or 'utf-8' as fallback.
    """
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception:
        return 'utf-8'

def read_file_with_encoding(file_path):
    """
    Read a file with the correct encoding and fix the text.
    Returns the fixed content or None if unsuccessful.
    """
    encoding = detect_encoding(file_path)
    try:
        with codecs.open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            return fix_text_encoding(content)
    except Exception as e:
        print(f"Error reading file: {e}")
        # Try with UTF-8 as fallback
        try:
            with codecs.open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return fix_text_encoding(content)
        except Exception as e:
            print(f"Error reading with UTF-8: {e}")
            return None

def save_file_with_encoding(file_path, content, encoding='utf-8'):
    """
    Save a file with the specified encoding.
    Returns True if successful, False otherwise.
    """
    try:
        with codecs.open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

@app.route('/convert', methods=['POST'])
def convert_text():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided'
            }), 400
            
        text = data['text']
        fixed_text = fix_text_encoding(text)
        
        return jsonify({
            'status': 'success',
            'text': fixed_text
        })
            
    except Exception as e:
        print(f"Error in convert_text: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/convert_csv', methods=['POST'])
def convert_csv():
    if 'files[]' not in request.files:
        print("No files found in request")
        return jsonify({
            'status': 'error',
            'message': 'No file uploaded'
        }), 400

    files = request.files.getlist('files[]')
    results = []
    
    for file in files:
        temp_input = None
        temp_output = None
        
        try:
            if file.filename == '':
                continue

            print(f"Processing file: {file.filename}")

            if not file.filename.endswith('.csv'):
                print(f"Unsupported file format: {file.filename}")
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'Unsupported file format'
                })
                continue

            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            # Create unique temporary filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            temp_input = os.path.join(temp_dir, f'temp_input_{timestamp}_{file.filename}')
            temp_output = os.path.join(temp_dir, f'temp_output_{timestamp}_{file.filename}')
            
            print(f"Saving uploaded file to: {temp_input}")
            file.save(temp_input)
            
            # Detect encoding
            with open(temp_input, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] if result and result['encoding'] else 'utf-8'
                print(f"Detected encoding for {file.filename}: {encoding}")
            
            # Read file line by line and write directly to output
            print(f"Processing file {file.filename}...")
            with open(temp_input, 'r', encoding=encoding) as f_in, \
                 open(temp_output, 'w', encoding='utf-8-sig', newline='') as f_out:
                for line in f_in:
                    # Clean extra semicolons
                    line = line.strip().split(';;')[0]
                    # Apply encoding fix if line is not empty
                    if line:
                        line = fix_text_encoding(line)
                    # Write the line (even if empty)
                    f_out.write(f"{line}\n")
            
            # Read output file into memory
            with open(temp_output, 'rb') as f:
                file_data = BytesIO(f.read())
                base64_data = base64.b64encode(file_data.getvalue()).decode('utf-8')
                print(f"File {file.filename} processed successfully, base64 length: {len(base64_data)}")
            
            # Add result
            results.append({
                'filename': file.filename,
                'status': 'success',
                'data': base64_data
            })

        except Exception as e:
            print(f"Error processing {file.filename}: {str(e)}")
            results.append({
                'filename': file.filename,
                'status': 'error',
                'message': str(e)
            })
        
        finally:
            # Clean up temporary files
            if temp_input and os.path.exists(temp_input):
                os.remove(temp_input)
                print(f"Temporary file deleted: {temp_input}")
            if temp_output and os.path.exists(temp_output):
                os.remove(temp_output)
                print(f"Temporary file deleted: {temp_output}")
    
    response_data = {
        'status': 'success',
        'results': results
    }
    print("Sending response:", response_data)
    return jsonify(response_data)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
