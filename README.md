```bash
pip install -r requirements.txt
python app.py
```

# PDF with Flashcard Generation: AI-Powered Study Companion

Elevate your learning experience with our AI-driven document viewer and flashcard generator! This web application transforms your PDFs, TXT files, and EPUBs into interactive flashcards and explanations using Claude AI, perfect for importing into Anki. Ideal for students, researchers, and lifelong learners looking to enhance their study sessions and spaced repetition practice.

## Key Features:
- 📚 Upload and view PDFs, TXT files, and EPUBs directly in your browser
- 🤖 Generate flashcards and explanations with Claude AI
- 🌐 Language learning mode for vocabulary acquisition
- 🖍️ Highlight important text for focused learning
- 💾 Save and export your flashcard collections to Anki-compatible format
- 📱 Responsive design for desktop and mobile use
- 🔄 Seamless integration with Anki for optimized spaced repetition

Dive into your documents, emerge with knowledge at your fingertips, and supercharge your Anki decks!

## Getting Started

### Prerequisites
- Docker
- Anthropic API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/document-viewer-flashcard-generator.git
   cd document-viewer-flashcard-generator
   ```

2. Build the Docker image:
   ```
   docker build -t document-viewer-flashcard-generator .
   ```

3. Run the Docker container:
   ```
   docker run -p 7860:7860 document-viewer-flashcard-generator
   ```

4. Open your web browser and navigate to `http://localhost:7860`

## Usage

1. Upload a PDF, TXT, or EPUB file using the file input at the top of the page
2. Navigate through the document using the page controls or by scrolling
3. Select text in the document viewer
4. Choose a mode (Flashcard, Explain, or Language) and click "Generate" to create content from the selected text
5. For language mode, double-click a word to generate a flashcard
6. View, remove, or export generated flashcards
7. Use the highlight mode (Alt+Select) to mark important text in the document

## API Key Setup

This application requires a Claude API key to function:

1. Sign up for an API key at [https://www.anthropic.com](https://www.anthropic.com)
2. In the application, click the gear icon to open the settings panel
3. Enter your API key in the provided input field

## Deployment on HuggingFace Spaces

This application is designed to be easily deployed on HuggingFace Spaces:

1. Fork this repository to your GitHub account
2. Create a new Space on HuggingFace and choose "Docker" as the SDK
3. Connect your GitHub repository to the HuggingFace Space
4. HuggingFace will automatically build and deploy your Docker container

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For discussing improvements or new features, we encourage you to open an Issue first to facilitate community discussion.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PDF.js](https://mozilla.github.io/pdf.js/) for PDF rendering
- [ePub.js](https://github.com/futurepress/epub.js/) for EPUB rendering
- [Anthropic](https://www.anthropic.com) for the Claude AI API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Docker](https://www.docker.com/) for containerization

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference for more information on HuggingFace Spaces configuration.
