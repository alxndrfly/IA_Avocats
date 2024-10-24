# Générateur de résumés de pièces juridiques à partir de PDF

## Description
This Streamlit application generates summaries of legal documents from PDF files. It uses Google Cloud Vision API for text extraction from PDFs and OpenAI's GPT model for summarization.

## Features
- Upload multiple PDF files
- Extract text from PDFs using Google Cloud Vision API
- Generate summaries of legal documents using OpenAI's GPT model
- Display summaries in the Streamlit interface
- Download summaries as a text file

## Requirements
- Python 3.7+
- Streamlit
- PyMuPDF
- Google Cloud Vision API
- OpenAI API

## Installation
1. Clone this repository:
   ```
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Google Cloud Vision API credentials and OpenAI API key as Streamlit secrets.

## Usage
1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open the provided URL in your web browser.

3. Upload your PDF files using the file uploader.

4. Click on "Générer le résumé" to process the files and generate summaries.

5. View the generated summaries in the app interface.

6. Download the summaries as a text file using the provided button.

## Important Notes
- Each PDF file should contain only images.
- Each PDF should contain only one legal document (can have multiple pages).
- PDF files should be named in the format: "Pièce nºx.pdf"
- Use the highest quality images possible for best results.

## Configuration
The application uses Streamlit secrets for API credentials. Make sure to set up the following in your Streamlit secrets:
- `GOOGLE_APPLICATION_CREDENTIALS`: Your Google Cloud service account key (JSON format)
- `OPENAI_API_KEY`: Your OpenAI API key

If you want to run the app locally, you can use a `.env` file to store your API keys.