# PDF Flashcard Generator

A web application that allows users to upload PDFs, view them, and generate flashcards using Claude AI.

## Features

- PDF upload and viewing
- Text selection for flashcard generation
- AI-powered flashcard creation using Claude API
- Flashcard management (view, remove, export to CSV)
- Recent PDF history
- Highlight mode for PDF text

## Getting Started

### Prerequisites

- Python 3.7+
- Flask
- Anthropic API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pdf-flashcard-generator.git
   cd pdf-flashcard-generator
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Sign up for an API key at [https://www.anthropic.com](https://www.anthropic.com)
   - Add your API key to the application when prompted

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Upload a PDF file using the file input at the top of the page
2. Navigate through the PDF using the page controls or by scrolling
3. Select text in the PDF viewer
4. Click "Generate Flashcard" to create flashcards from the selected text
5. View, remove, or export generated flashcards
6. Use the highlight mode to mark important text in the PDF

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PDF.js](https://mozilla.github.io/pdf.js/) for PDF rendering
- [Anthropic](https://www.anthropic.com) for the Claude AI API
