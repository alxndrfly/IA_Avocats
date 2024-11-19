# APP IA - AVOCATS

## Description
This Streamlit application helps legal professionals process and summarize documents using AI. It offers three main functionalities:

1. **Legal Document Summaries with Bordereau**
   - Summarizes multiple legal documents
   - Describes images within documents
   - Generates a bordereau
   - Provides both chronological and original order views
   - Outputs in Word or TXT format

2. **PDF to Word Conversion**
   - High-quality OCR-based conversion
   - Layout preservation
   - Support for French language

3. **Single Document Summary**
   - Supports both PDF and Word documents
   - Smart text extraction
   - Adjusts summary length based on content
   - Download options in TXT or Word format

## Features
- Upload multiple PDF files
- Extract text using Google Cloud Vision API
- Generate summaries using OpenAI's GPT models
- Image content description
- Chronological sorting of summaries
- Multiple export formats
- Adobe PDF Services integration for high-quality conversions


## Usage
1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Select your desired function from the sidebar:
   - RÉSUMÉ DE PIÈCES JURIDIQUES AVEC BORDEAUX
   - PDF À WORD
   - RÉSUMÉ DE DOCUMENT PDF OU WORD

3. Follow the on-screen instructions for each function.


## Important Notes
- For legal document summaries:
  - Each PDF should contain one legal document
  - Name files with piece numbers (e.g., "Pièce nº1.pdf")
  - High-quality scans recommended
  - AI-generated content should be reviewed

- For PDF to Word conversion:
  - Better quality PDFs yield better conversions
  - Complex layouts may affect conversion accuracy

- For single document summaries:
  - One document at a time
  - Supports PDF and Word (.doc, .docx)
  - Text-only extraction and summarization