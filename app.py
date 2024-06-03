from flask import Flask, request, render_template
import fitz  # PyMuPDF
import requests
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB upload limit

OCR_SPACE_API_KEY = os.getenv('OCR_SPACE_API_KEY')

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
def upload_file_handler():
    tags = request.form['tags'].split(',')
    tags = [tag.strip().lower() for tag in tags]

    f = request.files['file']
    filename = secure_filename(f.filename)
    file_path = os.path.join('/tmp', filename)
    f.save(file_path)

    if filename.lower().endswith(('.pdf','.docx','.doc','.txt','.xls', '.xlsx')):
        words_list = extract_text_from_doc(file_path)
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        words_list = extract_text_from_image(file_path)
    else:
        delete_file(file_path)
        return render_template('result.html', result="Unsupported file type")

    words_list = [word.lower() for word in words_list]
    common_elements = set(tags).intersection(words_list)

    print("Tags List: ",tags)
    print("Words List: ",words_list)
    print("Common List: ",common_elements)

    delete_file(file_path)  # Delete the file after processing

    if len(common_elements) >= int(len(tags) / 2):
        result = "Document uploaded is correct"
    else:
        result = "Document uploaded is incorrect"

    return render_template('result.html', result=result)

def extract_text_from_doc(doc_path):
    words_list = []
    document = fitz.open(doc_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text()
        words = text.split()
        words_list.extend(words)
    return words_list

def extract_text_from_image(image_path):
    with open(image_path, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={image_path: f},
            data={'apikey': OCR_SPACE_API_KEY, 'language': 'eng'}
        )
    result = response.json()
    words_list = []
    if result.get('IsErroredOnProcessing') is False:
        parsed_results = result.get('ParsedResults', [])
        if parsed_results:
            text = parsed_results[0].get('ParsedText', '')
            words_list = text.split()
    return words_list

def delete_file(file_path):
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Error: {file_path} : {e.strerror}")

if __name__ == '__main__':
    app.run(debug=True)
