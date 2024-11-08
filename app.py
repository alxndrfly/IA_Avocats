import streamlit as st
import os
import io
import fitz  # PyMuPDF
from google.cloud import vision
from google.cloud.vision_v1 import types
from openai import OpenAI
import tempfile
import json
import atexit
# from dotenv import load_dotenv          # Commented out for deployed environment
from docx import Document
from docx.shared import Inches, Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION

############# Deployed variables #############

# Convert AttrDict to a regular dictionary
google_creds = dict(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])

# Create a temporary file
creds_temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)

# Write the credentials to the temporary file
json.dump(google_creds, creds_temp_file)
creds_temp_file.flush()

# Set the environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_temp_file.name


# Add the cleanup function and register it
def cleanup_temp_file():
    if os.path.exists(creds_temp_file.name):
        os.unlink(creds_temp_file.name)

atexit.register(cleanup_temp_file)

# Initialize the OpenAI client with the secret
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

############# END OF Deployed environment variables #############


############# Local environment variables #############
# Load environment variables from .env file
# load_dotenv()

# Set the Google Cloud credentials for this session
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Initialize the OpenAI client
# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

############# END OF Local environment variables #############


# Function to extract text from PDFs using Google Vision API with the name of each Pièce nºx.pdf
def extract_text_from_pdfs(pdf_files, dpi=300):
    client = vision.ImageAnnotatorClient()
    extracted_texts = []

    for pdf_file in pdf_files:
        pdf_content = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        text = f"<{os.path.splitext(pdf_file.name)[0]}>\n\n"
        print(f"Processing: {pdf_file.name}")

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes()

            image = types.Image(content=img_bytes)
            response = client.document_text_detection(image=image)
            page_text = response.full_text_annotation.text
            
            if page_text:
                text += f"Page {page_num + 1}:\n{page_text}\n\n"
                print(f"    Text extracted from page {page_num + 1}")
            else:
                text += f"Page {page_num + 1}: No text found\n\n"
                print(f"    No text found on page {page_num + 1}")

        text += f"\n</{os.path.splitext(pdf_file.name)[0]}>"
        extracted_texts.append(text)
        print(f"Extracted text from PDF: {pdf_file.name}")

    print("Text extraction complete.")
    return extracted_texts

# Function to convert PDFs to Word documents
def convert_pdf_to_word(pdf_file, dpi=300):
    client = vision.ImageAnnotatorClient()
    doc = Document()
    
    # Read PDF content
    pdf_content = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    
    print(f"Processing: {pdf_file.name}")
    
    # Set up the document page size and margins
    first_page = pdf_document[0]
    page_width = first_page.rect.width * 0.352778
    page_height = first_page.rect.height * 0.352778
    
    # Slightly larger margins for better readability
    margin = 15  # 15mm margins
    
    def setup_section(section):
        section.page_width = Mm(page_width)
        section.page_height = Mm(page_height)
        section.left_margin = Mm(margin)
        section.right_margin = Mm(margin)
        section.top_margin = Mm(margin)
        section.bottom_margin = Mm(margin)
    
    # Configure initial section
    setup_section(doc.sections[0])
    
    # Process each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Create new section for each page except the first
        if page_num > 0:
            doc.add_section(WD_SECTION.NEW_PAGE)
            setup_section(doc.sections[page_num])
        
        # Convert page to image
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes()
        
        # Perform OCR
        image = types.Image(content=img_bytes)
        response = client.document_text_detection(image=image)
        
        if response.full_text_annotation:
            # Get page dimensions
            page_height = pix.height
            page_width = pix.width
            
            # Group blocks by their vertical position (approximate lines)
            blocks = response.full_text_annotation.pages[0].blocks
            
            # Sort blocks primarily by vertical position
            blocks = sorted(blocks, key=lambda b: min(v.y for v in b.bounding_box.vertices))
            
            current_y = -1
            line_blocks = []
            all_lines = []
            
            # Group blocks into lines based on vertical position
            for block in blocks:
                block_y = min(v.y for v in block.bounding_box.vertices)
                
                # If this block is significantly lower than the previous one, start a new line
                if current_y == -1 or (block_y - current_y) > 20:  # Threshold for new line
                    if line_blocks:
                        all_lines.append(line_blocks)
                    line_blocks = [block]
                    current_y = block_y
                else:
                    line_blocks.append(block)
            
            # Add the last line if it exists
            if line_blocks:
                all_lines.append(line_blocks)
            
            # Process each line of blocks
            for line in all_lines:
                # Sort blocks in the line by horizontal position
                line = sorted(line, key=lambda b: min(v.x for v in b.bounding_box.vertices))
                
                # Create a new paragraph for each line
                paragraph = doc.add_paragraph()
                paragraph.space_before = Pt(3)
                paragraph.space_after = Pt(3)
                
                # Determine line alignment based on all blocks in the line
                left_positions = [min(v.x for v in b.bounding_box.vertices) / page_width for b in line]
                right_positions = [max(v.x for v in b.bounding_box.vertices) / page_width for b in line]
                
                # Build the complete text for this line first
                line_text = ""
                for block in line:
                    for para in block.paragraphs:
                        for word in para.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            line_text += word_text + ' '
                
                # Default to left alignment
                alignment = WD_ALIGN_PARAGRAPH.LEFT
                
                # Only center if it's very clearly meant to be centered (like titles)
                if (len(line_text.strip()) < 100 and  # Only center shorter text
                    all(0.35 < left_pos < 0.65 for left_pos in left_positions) and
                    all(0.35 < right_pos < 0.65 for right_pos in right_positions)):
                    alignment = WD_ALIGN_PARAGRAPH.CENTER
                # Only right-align if it's very clearly meant to be right-aligned
                elif (len(line_text.strip()) < 50 and  # Only right-align very short text
                      all(right_pos > 0.85 for right_pos in right_positions)):
                    alignment = WD_ALIGN_PARAGRAPH.RIGHT
                
                paragraph.alignment = alignment
                
                # Process each block in the line
                for block in line:
                    for para in block.paragraphs:
                        text = ""
                        for word in para.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            text += word_text + ' '
                        
                        if text.strip():
                            run = paragraph.add_run(text.strip() + ' ')
                            font = run.font
                            font.size = Pt(11)
            
            print(f"    Processed page {page_num + 1}")
        else:
            print(f"    No text found on page {page_num + 1}")
    
    # Save to bytes buffer
    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)
    
    print("Conversion complete.")
    return doc_buffer


# Function to call the GPT API
def call_gpt(
    user_prompt,
    temperature=1.0,
    system_prompt=None,
    model="gpt-4o-mini-2024-07-18",
    max_tokens=None,
    top_p=1.0,
    n=1,
    stream=False,
    stop=None,
    presence_penalty=0,
    frequency_penalty=0,
    logit_bias=None,
    user=None
):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            n=n,
            stream=stream,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            user=user
        )
        return response
    except Exception as e:
        print(f"Error calling GPT API: {e}")
        return None

# Function to summarize the transcripts using a prompt template
def summarize_transcripts(prompt_template, transcripts):
    summaries = []
    
    for transcript in transcripts:
        prompt = prompt_template.format(transcript)
        response = call_gpt(user_prompt=prompt, temperature=0)
        
        if response:
            summary = response.choices[0].message.content
            summaries.append(summary)
        else:
            summaries.append(f"Failed to generate summary for {transcript[:50]}...")
        
        print(f"Summary generated for transcript")

    return "\n\n------\n\n".join(summaries)

# Define the prompt template
prompt_template_summary = """
Résume le texte entre les triples parenthèses en suivant ces directives :

- Extrait les faits et informations importantes à mentionner
- Résume et output en français.
- Accorde les verbes au passé composé ou à l'imparfait.
- Ajoute le numéro de pièce à la fin du paragraphe comme dans la structure à suivre
- Extrait et ajoute la date en format "JJ mois AAAA" 

Met la totalité du texte en forme une seule fois en suivant cette structure :

Le <date>, <brève explication des faits>.

<Explication résumée des faits en utilisant les termes clés> (Pièce nºx).

((({})))"""


prompt_template_bordereau = """

Tu reçois un transcript d'une pièce juridique entre les triples parenthèses.
Tu vas générer une ligne de bordereau de pièce en suivant ces directives :

- Extrait le titre de la pièce qui décrit le plus justement la pièce en utilisant la terminologie juridique.
- Sois précis et concis dans le titre.
- Écris le titre avec une majuscule au début et le reste en minuscule.
- Extrait le numéro de la pièce, que tu trouveras au début du transcript sous le format (Pièce Nºx)
- Ajoute le numéro de pièce en notant simplement son chiffre comme dans la structure à suivre
- Extrait et ajoute la date des faits de la pièce en format "JJ mois AAAA" 

Output en suivant cette structure :

<nº de pièce> - <Titre de la pièce> - du <JJ mois AAAA>

IMPORTANT :
- Relis ton output et verifie les conditions suivantes :
- Dans le cas précis où la pièce est une attestation de témoin, mentionne le genre (Monsieur ou Madame) et le nom de famille de l'individu seulement (tout en majuscules).

((({})))"""




# Function to summarize the pdfs into ready to use summaries for conclusions
def process_uploaded_files(uploaded_files):
    extracted_texts = extract_text_from_pdfs(uploaded_files, dpi=300)
    
    # Generate summary
    summary = summarize_transcripts(prompt_template_summary, extracted_texts)
    
    # Generate bordereau entries for each piece
    bordereau_entries = []
    for transcript in extracted_texts:
        response = call_gpt(user_prompt=prompt_template_bordereau.format(transcript), temperature=0)
        if response:
            bordereau_entry = response.choices[0].message.content.strip()
            bordereau_entries.append(bordereau_entry)
            print(f"Bordereau entry generated: {bordereau_entry}")
    
    # Combine summary and bordereau with newlines between entries
    bordereau_section = "BORDEREAU DE PIECES COMMUNIQUEES\n\n" + "\n".join(entry + "\n" for entry in bordereau_entries)
    complete_document = f"{summary}\n\n{'='*50}\n\n{bordereau_section}"
    return complete_document


# Keep existing function unchanged for legal documents
def create_summary_word_document(summary_text):
    doc = Document()
    
    title = doc.add_paragraph("Résumé des pièces")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.runs[0]
    title_run.font.size = Pt(14)
    title_run.font.bold = True
    
    doc.add_paragraph(summary_text)
    
    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)
    
    return doc_buffer

# Add new function for single document summaries
def create_single_document_summary_word(summary_text, document_name):
    doc = Document()
    
    # Add title with document name
    title_text = f"Résumé - {document_name}"
    title = doc.add_paragraph(title_text)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.runs[0]
    title_run.font.size = Pt(14)
    title_run.font.bold = True
    
    # Add some spacing
    doc.add_paragraph()
    
    # Add the summary text, preserving paragraph breaks
    for paragraph in summary_text.split('\n'):
        if paragraph.strip():  # Only add non-empty paragraphs
            p = doc.add_paragraph()
            p.add_run(paragraph)
        else:
            # Add empty paragraph for spacing
            doc.add_paragraph()
    
    # Save to bytes buffer
    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)
    
    return doc_buffer

def extract_text_from_word(file):
    doc = Document(file)
    text = ""
    
    # Extract text from paragraphs
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():  # Only add non-empty paragraphs
            text += paragraph.text + "\n"
    
    # Extract text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text += cell.text + "\n"
    
    return text

def extract_text_from_single_document(file):
    if file.name.lower().endswith('.pdf'):
        # Reuse existing PDF extraction but for single file
        extracted_text = extract_text_from_pdfs([file])[0]
        # Remove the filename tags that were used for multiple files
        extracted_text = extracted_text.split('>\n\n', 1)[-1].rsplit('</', 1)[0]
        return extracted_text
    elif file.name.lower().endswith(('.doc', '.docx')):
        return extract_text_from_word(file)
    else:
        raise ValueError("Format de fichier non supporté. Veuillez mettre en ligne un document PDF ou Word.")

# Add new prompt template for general summarization
prompt_template_general = """

Résume le texte entre les triples parenthèses en suivant ces directives :
- Idées et points clés
- Détails importants et conclusions
- Flux logique de l'information
- Conclusions ou résultats

Structure le résumé en paragraphes clairs et conserve le sens original tout en étant concis.

Texte à résumer :
((({})))
"""

def summarize_single_document(file):
    try:
        # Extract text
        extracted_text = extract_text_from_single_document(file)
        
        # Generate summary using GPT
        prompt = prompt_template_general.format(extracted_text)
        response = call_gpt(user_prompt=prompt, temperature=0)
        
        if response:
            summary = response.choices[0].message.content
            return summary
        else:
            return "Failed to generate summary. Please try again."
            
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Simple sidebar navigation
st.sidebar.title("Navigation")

# Fix radio button label
selected_function = st.sidebar.radio(
    label="Navigation Options",  # Add descriptive label
    options=["Générer un résumé de pièces juridiques avec bordereau", "PDF à Word", "Résumé de document PDF ou Word"],
    label_visibility="collapsed"  # Hide the label
)

# Conditional content based on selection
if selected_function == "Générer un résumé de pièces juridiques avec bordereau":
    st.title("Générateur de résumés de pièces juridiques et de bordereau à partir de PDF")
    
    st.markdown("####")
    st.markdown("#####  COMMENT UTILISER CET OUTIL ?")
    st.markdown("######  1. Préparez vos fichiers PDF en suivant les directives ci-dessous.")
    st.markdown("######  2. Soumettez la totalité de vos pièces juridiques.")
    st.markdown("######  3. L'IA générera le résumé et le bordereau.")
    st.markdown("######  4. Téléchargez le résultat en Word ou .txt.")

    st.markdown("#####")
    st.markdown("#####  IMPÉRATIF POUR CHAQUE FICHIER PDF :")
    st.markdown("######  - Une seule pièce juridique par PDF (le fichier peut contenir plusieurs pages).")
    st.markdown("######  - Contenir seulement des images / scans de documents.")
    st.markdown("######  - Être nommé avec le format suivant : Pièce Nºx.pdf")
    st.markdown("######  - Avoir la meilleure qualité d'image possible.")

    st.markdown("####")

    # Initialize session state
    if 'summary' not in st.session_state:
        st.session_state.summary = None

    st.markdown("#### Ajoutez tous vos fichiers PDF ci-dessous")
    uploaded_files = st.file_uploader(
        label="Upload des pièces juridiques",  # Added label
        type="pdf", 
        accept_multiple_files=True, 
        label_visibility="collapsed",  # Hide the label
        key="pdf_uploader_summary"
    )

    if uploaded_files:
        if st.button("Générer le résumé"):
            with st.spinner("Nous générons votre résumé..."):
                st.session_state.summary = process_uploaded_files(uploaded_files)

    if st.session_state.summary:
        st.markdown("### ")
        st.markdown("### Résumé et Bordereau")
        st.markdown(st.session_state.summary)
        st.markdown("### ")
        
        # Create two columns for download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Télécharger en .txt",
                data=st.session_state.summary,
                file_name="resume_et_bordereau.txt",
                mime="text/plain"
            )
        
        with col2:
            word_buffer = create_summary_word_document(st.session_state.summary)
            st.download_button(
                label="📥 Télécharger en Word",
                data=word_buffer,
                file_name="resume_et_bordereau.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

elif selected_function == "PDF à Word":
    st.title("Convertisseur PDF vers Word")
    st.markdown("####")
    st.markdown("#####  IMPORTANT :")
    st.markdown("######  - Le PDF doit avoir une bonne qualité d'image pour une meilleure conversion.")
    st.markdown("######  - La conversion peut prendre quelques minutes selon le nombre de pages.")
    st.markdown("####")
    
    st.markdown("#### Ajoutez votre fichier PDF ci-dessous")
    uploaded_file = st.file_uploader(
        label="Upload du PDF",  # Added label
        type="pdf", 
        accept_multiple_files=False, 
        label_visibility="collapsed",  # Hide the label
        key="pdf_uploader_word"
    )
    
    if uploaded_file:
        if st.button("Convertir en Word"):
            with st.spinner("Conversion en cours... Cela peut prendre quelques minutes."):
                try:
                    word_buffer = convert_pdf_to_word(uploaded_file)
                    st.success("Conversion réussie!")
                    st.download_button(
                        label="📥 Télécharger le document Word",
                        data=word_buffer,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de la conversion: {str(e)}")

elif selected_function == "Résumé de document PDF ou Word":
    st.title("Générateur de résumé de document PDF ou Word")
    st.markdown("####")
    st.markdown("#####  IMPORTANT :")
    st.markdown("######  - Un seul document à la fois.")
    st.markdown("######  - Formats acceptés : PDF et Word (.doc, .docx)")
    st.markdown("######  - Pour les PDFs : meilleure qualité d'image possible")
    st.markdown("####")
    
    # Initialize session state for summary
    if 'general_summary' not in st.session_state:
        st.session_state.general_summary = None
    
    st.markdown("#### Ajoutez votre document ci-dessous")
    uploaded_file = st.file_uploader(
        label="Document Upload",  # Add descriptive label
        type=["pdf", "doc", "docx"], 
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="document_uploader_summary"
    )
    
    if uploaded_file:
        if st.button(
            label="Générer le résumé",  # Add label for button
            key="generate_summary_button"
        ):
            with st.spinner("Génération du résumé en cours..."):
                st.session_state.general_summary = summarize_single_document(uploaded_file)
    
    if st.session_state.general_summary:
        st.markdown("### ")
        st.markdown("### Résumé")
        st.markdown(st.session_state.general_summary)
        st.markdown("### ")
        
        # Get document name without extension
        doc_name = os.path.splitext(uploaded_file.name)[0]
        
        # Create formatted text with title for txt download
        formatted_text = f"Résumé - {doc_name}\n\n{st.session_state.general_summary}"
        
        # Create two columns for download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Télécharger en .txt",  # Add label for download button
                data=formatted_text,
                file_name=f"resume_{doc_name}.txt",
                mime="text/plain",
                key="download_txt_button"
            )
        
        with col2:
            word_buffer = create_single_document_summary_word(
                st.session_state.general_summary,
                document_name=doc_name
            )
            st.download_button(
                label="📥 Télécharger en Word",  # Add label for download button
                data=word_buffer,
                file_name=f"resume_{doc_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_word_button"
            )

