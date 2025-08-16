
import os
import re
from flask import Flask, request, render_template_string, send_from_directory
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'output'

# HTML template for the web page as a string
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extractor de Hojas de PDF</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; background-color: #f4f4f9; color: #333; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #444; }
        textarea { width: 95%; padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
        input[type="text"], input[type="file"] { width: 95%; padding: 10px; margin-bottom: 1em; border-radius: 4px; border: 1px solid #ddd; }
        input[type="submit"] { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        input[type="submit"]:hover { background-color: #0056b3; }
        .message { padding: 1em; margin-top: 1em; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .file-list { list-style-type: none; padding: 0; }
        .file-list li { background: #e9ecef; margin-bottom: 5px; padding: 10px; border-radius: 4px; }
        .file-list a { text-decoration: none; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Extractor de Hojas de PDF</h1>
        <form method="post" enctype="multipart/form-data">
            <label for="pdf_file">1. Sube el archivo PDF general:</label><br>
            <input type="file" name="pdf_file" required><br><br>

            <label for="identifiers">2. Pega los nombres o identificaciones (uno por línea):</label><br>
            <textarea name="identifiers" rows="10" required></textarea><br><br>

            <label for="month">3. Escribe el mes para el nombre del archivo (ej: Enero, Febrero):</label><br>
            <input type="text" name="month" required><br><br>

            <input type="submit" value="Extraer Hojas">
        </form>
        {% if message %}
            <div class="message {{ 'success' if 'Éxito' in message else 'error' }}">
                <p>{{ message }}</p>
                {% if files %}
                    <h3>Archivos Generados:</h3>
                    <ul class="file-list">
                        {% for file in files %}
                            <li><a href="/output/{{ file }}" target="_blank">{{ file }}</a></li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

def sanitize_filename(name):
    """Remove invalid characters for a filename."""
    return re.sub(r'[\/*?:"<>|]',"", name).replace(" ", "_")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = None
        files = []
        try:
            if 'pdf_file' not in request.files or 'identifiers' not in request.form or 'month' not in request.form:
                message = "Error: Faltan campos en el formulario."
                return render_template_string(HTML_TEMPLATE, message=message)
            
            pdf_file = request.files['pdf_file']
            identifiers = request.form['identifiers'].strip().splitlines()
            month = request.form['month'].strip()

            if pdf_file.filename == '' or not identifiers or not month:
                message = "Error: Todos los campos son obligatorios."
                return render_template_string(HTML_TEMPLATE, message=message)

            reader = PdfReader(pdf_file.stream)
            
            for identifier in identifiers:
                identifier = identifier.strip()
                if not identifier:
                    continue

                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if identifier.lower() in text.lower():
                        writer = PdfWriter()
                        writer.add_page(page)
                        
                        sanitized_id = sanitize_filename(identifier)
                        sanitized_month = sanitize_filename(month)
                        output_filename = f"{sanitized_id}_{sanitized_month}.pdf"
                        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                        
                        with open(output_path, "wb") as f:
                            writer.write(f)
                        
                        if output_filename not in files:
                            files.append(output_filename)
                        break

            if not files:
                message = "No se encontraron coincidencias para los identificadores proporcionados."
            else:
                message = f"Éxito: Se procesaron {len(files)} archivos."

            return render_template_string(HTML_TEMPLATE, message=message, files=files)

        except Exception as e:
            message = f"Error al procesar el PDF: {e}"
            return render_template_string(HTML_TEMPLATE, message=message)

    return render_template_string(HTML_TEMPLATE)

@app.route('/output/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(port=2791,debug=True)
