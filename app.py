from flask import Flask, request, jsonify
import requests
import PyPDF2
import json
from openpyxl import Workbook
import os

app = Flask(__name__)

# Define your API key and endpoint URL
API_KEY = 'AIzaSyATdOo-sWAQqVPmdaf8nHZvUhmn8Sc3aGw'  # Replace with your actual API key
url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Function to send text to Gemini AI API
def process_text_with_gemini(prompt):
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

# Function to parse Markdown table and save to Excel
def save_markdown_to_excel(markdown_text, file_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Gemini API Results"

    lines = markdown_text.strip().split('\n')
    if not lines or len(lines) < 3:
        sheet.append(["Error", "Markdown text is not in expected format or is empty."])
        workbook.save(file_path)
        return

    headers = [header.strip() for header in lines[0].strip('|').split('|') if header.strip()]
    sheet.append(headers)

    for line in lines[2:]:
        row = [cell.strip() for cell in line.strip('|').split('|') if cell.strip()]
        sheet.append(row)

    workbook.save(file_path)

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    file = request.files['file']
    pdf_path = os.path.join('/tmp', file.filename)
    file.save(pdf_path)

    pdf_text = extract_text_from_pdf(pdf_path)
    custom_text = "make me a summary in table format for excel for HS CODE, Number and Kind, Description, Invoice No., Dutiable Value, CUD and VAT"
    combined_text = custom_text + "\n\n" + pdf_text

    gemini_response = process_text_with_gemini(combined_text)

    if 'error' in gemini_response:
        return jsonify(gemini_response), 400

    candidates = gemini_response.get('candidates', [{}])
    parts = candidates[0].get('content', {}).get('parts', [{}])
    markdown_text = parts[0].get('text', '')

    if not markdown_text:
        return jsonify({"error": "No content found in API response."}), 400

    excel_file_path = os.path.join('/tmp', 'gemini_response.xlsx')
    save_markdown_to_excel(markdown_text, excel_file_path)

    return jsonify({"message": "PDF processed successfully.", "file": excel_file_path}), 200

if __name__ == '__main__':
    app.run(debug=True)
