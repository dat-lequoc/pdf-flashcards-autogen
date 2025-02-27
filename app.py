from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
from litellm import completion
import os
import json
from datetime import datetime
import base64
from llm_utils import generate_completion
import re
import epitran
from gtts import gTTS
import io
from ipa_speech import IPATranscriber

app = Flask(__name__)

# Use an environment variable for the upload folder, with a default to /tmp/uploads
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize epitran for different languages
epitran_models = {
    'English': epitran.Epitran('eng-Latn'),
    'French': epitran.Epitran('fra-Latn'),
    # Add more languages as needed
}

# Initialize IPATranscriber for better IPA and audio generation
ipa_transcriber = IPATranscriber()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/')
def index():
    recent_files = get_recent_files()
    response = make_response(render_template('index.html', recent_files=recent_files))
    return response

def get_recent_files():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    valid_files = [f for f in files if f.lower().endswith(('.pdf', '.txt'))]
    valid_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return [{'filename': file, 'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], file))).isoformat()} for file in valid_files[:5]]

@app.route('/get_recent_files')
def get_recent_files_route():
    return jsonify(get_recent_files())

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and (file.filename.lower().endswith(('.pdf', '.txt', '.epub'))):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200
    return jsonify({'error': 'Invalid file type. Please upload a PDF, TXT, or EPUB file.'}), 400

@app.route('/get_epub_content/<path:filename>')
def get_epub_content(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and filename.endswith('.epub'):
        with open(file_path, 'rb') as file:
            epub_content = base64.b64encode(file.read()).decode('utf-8')
        return jsonify({'epub_content': epub_content})
    return jsonify({'error': 'File not found or not an EPUB'}), 404

@app.route('/open_pdf/<path:filename>')
def open_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/generate_flashcard', methods=['POST'])
def generate_flashcard():
    data = request.json
    prompt = data['prompt']
    mode = data.get('mode', 'flashcard')
    model = data.get('model')

    try:
        # Use llm_utils to generate completion with the selected model
        content = generate_completion(prompt, model=model)
        print(content)

        if mode == 'language':
            try:
                # Extract the JSON substring from the content in case there is extra text.
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    json_text = json_match.group(0)
                    flashcard = json.loads(json_text)
                    return jsonify({'flashcard': flashcard})
                else:
                    raise ValueError("No JSON object found in response")
            except Exception as parse_err:
                print("JSON parsing error in language mode: ", parse_err)
                return jsonify({'error': 'JSON parsing error in language mode: ' + str(parse_err)})
        elif mode == 'flashcard':
            try:
                # Extract the JSON array substring from the content in case there is extra text.
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    json_text = json_match.group(0)
                    flashcards = json.loads(json_text)
                    return jsonify({'flashcards': flashcards})
                else:
                    raise ValueError("No JSON array found in response")
            except Exception as parse_err:
                return jsonify({'error': 'JSON parsing error in flashcard mode: ' + str(parse_err)})
        elif mode == 'explain':
            # For explanation mode, try parsing as JSON first, but always fall back to the raw content
            try:
                # First try to see if it's a JSON object with an "explanation" key
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    json_text = json_match.group(0)
                    parsed = json.loads(json_text)
                    if 'explanation' in parsed:
                        return jsonify({'explanation': parsed['explanation']})
                
                # If we get here, either the JSON parsing failed or there was no "explanation" key
                # Just return the raw content as the explanation
                return jsonify({'explanation': content})
            except Exception as parse_err:
                # If JSON parsing fails, return the raw content
                print("Using raw content for explanation: ", parse_err)
                return jsonify({'explanation': content})
        else:
            return jsonify({'error': 'Invalid mode'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_ipa', methods=['POST'])
def get_ipa():
    data = request.json
    word = data.get('word', '')
    language = data.get('language', 'English')
    
    print(f"GET_IPA REQUEST: word='{word}', language='{language}'")
    
    try:
        # First try using the ipa_transcriber for improved IPA
        if language == 'English':
            ipa = ipa_transcriber.get_ipa(word)
            print(f"IPATranscriber result for '{word}': '{ipa}'")
            if ipa:
                return jsonify({'ipa': ipa})
        
        # Fallback to epitran if needed
        if language in epitran_models:
            ipa = epitran_models[language].transliterate(word)
            print(f"Epitran fallback for '{word}': '{ipa}'")
            return jsonify({'ipa': ipa})
        else:
            print(f"Language '{language}' not supported for IPA")
            return jsonify({'ipa': '', 'error': f'Language {language} not supported for IPA'})
    except Exception as e:
        print(f"ERROR in /get_ipa: {str(e)}")
        return jsonify({'ipa': '', 'error': str(e)})

@app.route('/get_audio', methods=['POST'])
def get_audio():
    data = request.json
    word = data.get('word', '')
    language = data.get('language', 'en')
    audio_type = data.get('type', 'word')  # 'word' or 'phrase'
    
    # Map language names to language codes for gTTS
    language_codes = {
        'English': 'en',
        'French': 'fr',
        # Add more languages as needed
    }
    
    lang_code = language_codes.get(language, 'en')
    
    try:
        if audio_type == 'word':
            # Use gTTS for word pronunciation
            audio_data = ipa_transcriber.text_to_speech_gtts(
                word, 
                lang=lang_code, 
                return_base64=True
            )
        else:
            # Use AWS Polly for phrase pronunciation (better quality)
            # Choose an appropriate voice based on language
            voice_id = 'Joanna' if lang_code == 'en' else 'Celine'  # Celine for French
            audio_data = ipa_transcriber.text_to_speech_polly(
                word,
                voice_id=voice_id,
                return_base64=True
            )
        
        return jsonify({'audio': audio_data})
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/test_ipa')
def test_ipa():
    test_words = ["hello", "world", "test"]
    results = {}
    
    for word in test_words:
        try:
            # Test eng_to_ipa
            eng_ipa = ipa_transcriber.get_ipa(word)
            # Test epitran
            epi_ipa = epitran_models['English'].transliterate(word)
            
            results[word] = {
                "eng_to_ipa": eng_ipa,
                "epitran": epi_ipa
            }
        except Exception as e:
            results[word] = {"error": str(e)}
            
    return jsonify(results)

@app.route('/remove_recent_file', methods=['POST'])
def remove_recent_file():
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'error': 'No filename provided'}), 400
    
    try:
        # Read the recent files from localStorage
        # Note: We're not actually deleting the file, just removing it from the recent files list
        recent_files = get_recent_files()
        recent_files = [f for f in recent_files if f['filename'] != filename]
        
        # Here you could optionally save the updated list to a server-side storage
        # For now, we just return success and let the client update its localStorage
        
        return jsonify({'success': True, 'message': f'Removed {filename} from recent files'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variables to determine the run mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=7860)
