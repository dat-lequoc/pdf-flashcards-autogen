from flask import Flask, request, jsonify, render_template, make_response
import anthropic
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_flashcard', methods=['POST'])
def generate_flashcard():
    data = request.json
    prompt = data['prompt']
    api_key = request.headers.get('X-API-Key')

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        print(content)
        lines = content.split('\n')
        question = ''
        answer = ''

        for line in lines:
            if line.startswith('Q:'):
                question = line[2:].strip()
            elif line.startswith('A:'):
                answer = line[2:].strip()
                break

        response = make_response(jsonify({'question': question, 'answer': answer}))

        # Set cookie with the API key
        response.set_cookie('last_working_api_key', api_key, secure=True, httponly=True, samesite='Strict')

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
