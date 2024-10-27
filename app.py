from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from googletrans import Translator, LANGUAGES
import os
import io
from datetime import datetime

app = Flask(__name__)

# Set the Tesseract command path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Set TESSDATA_PREFIX environment variable
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR'

# In-memory storage for recent files
history = []

@app.route('/')
def index():
    # Pass LANGUAGES and history to the template
    return render_template('index.html', languages=LANGUAGES, history=history)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    ocr_language = request.form.get('ocr_language', 'eng')
    target_language = request.form.get('language', 'en')
    
    if file:
        image = Image.open(file.stream)
        extracted_text = pytesseract.image_to_string(image, lang=ocr_language)
        
        translator = Translator()
        translated_text = translator.translate(extracted_text, dest=target_language).text

        # Save to history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "timestamp": timestamp,
            "filename": file.filename,
            "extracted_text": extracted_text,
            "translated_text": translated_text
        })

        # Convert translated text to an image
        text_image = text_to_image(translated_text)

        # Save image in memory for download
        img_io = io.BytesIO()
        text_image.save(img_io, 'PNG')
        img_io.seek(0)

        # Pass both extracted and translated text along with languages to the template
        return render_template('index.html', 
                               extracted_text=extracted_text, 
                               translated_text=translated_text, 
                               languages=LANGUAGES, 
                               history=history,
                               download_url=url_for('download_image', timestamp=timestamp))
    return redirect(url_for('index'))

def text_to_image(text):
    # Define font and line spacing
    font = ImageFont.load_default()  # Or you can specify a specific font file and size
    lines = text.splitlines()
    
    # Calculate width and height for the image
    max_width = max(font.getlength(line) for line in lines) + 20
    line_height = font.getbbox("A")[3] + 10  # Adjust for line spacing
    total_height = len(lines) * line_height + 10

    # Create the image with white background
    image = Image.new("RGB", (int(max_width), int(total_height)), "white")
    draw = ImageDraw.Draw(image)

    # Draw each line of text
    y_text = 10
    for line in lines:
        draw.text((10, y_text), line, font=font, fill="black")
        y_text += line_height

    return image

@app.route('/download_image/<timestamp>')
def download_image(timestamp):
    # Find the matching history entry
    for entry in history:
        if entry["timestamp"] == timestamp:
            text_image = text_to_image(entry["translated_text"])

            # Save image in memory for download
            img_io = io.BytesIO()
            text_image.save(img_io, 'PNG')
            img_io.seek(0)
            return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='translated_image.png')

    return "Image not found."

if __name__ == '__main__':
    app.run(debug=True)
