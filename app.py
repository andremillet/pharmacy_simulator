from flask import Flask, render_template, request, flash
from cryptography.fernet import Fernet
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'pharmacy_simulator_secret'  # Required for flash messages

# Allowed file extensions
ALLOWED_EXTENSIONS = {'med', 'key'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def decrypt_med_file(med_content, key_content):
    try:
        cipher = Fernet(key_content)
        decrypted_data = cipher.decrypt(med_content)
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception as e:
        flash(f"Erro ao descriptografar: {str(e)}")
        return None

def extract_medication_info(decrypted_data):
    medications = []
    if decrypted_data and 'extension' in decrypted_data:
        for ext in decrypted_data['extension']:
            if 'valueCodeableConcept' in ext and 'text' in ext['valueCodeableConcept']:
                conducts = json.loads(ext['valueCodeableConcept']['text'])
                for conduct in conducts:
                    if conduct['type'] == "Prescrição de medicamento":
                        details = conduct['details']
                        medications.append({
                            'medication': details.get('medication', 'N/A'),
                            'dose': details.get('dose', 'N/A'),
                            'administration': details.get('administration', 'N/A')
                        })
    return medications

@app.route('/', methods=['GET', 'POST'])
def index():
    medications = []
    if request.method == 'POST':
        # Check if files are uploaded
        if 'med_file' not in request.files or 'key_file' not in request.files:
            flash('Por favor, envie ambos os arquivos .med e .key.')
            return redirect(request.url)

        med_file = request.files['med_file']
        key_file = request.files['key_file']

        # Validate file uploads
        if med_file.filename == '' or key_file.filename == '':
            flash('Nenhum arquivo selecionado.')
            return redirect(request.url)

        if not (allowed_file(med_file.filename) and allowed_file(key_file.filename)):
            flash('Apenas arquivos .med e .key são permitidos.')
            return redirect(request.url)

        # Read file contents
        med_content = med_file.read()
        key_content = key_file.read()

        # Decrypt and extract medication info
        decrypted_data = decrypt_med_file(med_content, key_content)
        if decrypted_data:
            medications = extract_medication_info(decrypted_data)
            if not medications:
                flash('Nenhuma prescrição de medicamento encontrada no arquivo.')

    return render_template('index.html', medications=medications)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
