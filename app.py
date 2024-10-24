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
prompt_template = """
Résume le texte entre les triples parenthèses en suivant ces directives :

- Extrait les faits et informations importantes à mentionner
- Résume et output en français.
- Accorde les verbes au passé composé ou à l'imparfait.
- Ajoute le numéro de pièce à la fin du paragraphe comme dans la structure à suivre
- Extrait et ajoute la date en format "JJ mois AAAA" 

Met le texte en forme en suivant cette structure :

Le <date>, <brève explication des faits>.

<Explication résumée des faits en utilisant les termes clés> (Pièce nºx).

((({})))"""

def process_uploaded_files(uploaded_files):
    extracted_texts = extract_text_from_pdfs(uploaded_files, dpi=300)
    summary = summarize_transcripts(prompt_template, extracted_texts)
    return summary

# Streamlit app
st.title("Générateur de résumés de pièces juridiques à partir de PDF")
st.markdown("####")
st.markdown("#####  IMPORTANT POUR CHAQUE FICHIER PDF :")
st.markdown("######  - Contenir seulement des images.")
st.markdown("######  - Contenir qu'une seule pièce (peut contenir plusieurs pages).")
st.markdown("######  - Être nommé avec le format suivant : Pièce nºx.pdf")
st.markdown("######  - Avoir la meilleure qualité d'image possible.")

st.markdown("####")

# Initialize session state
if 'summary' not in st.session_state:
    st.session_state.summary = None

st.markdown("#### Ajoutez tous vos fichiers PDF ci-dessous")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, label_visibility="visible", key="pdf_uploader")

if uploaded_files:
    if st.button("Générer le résumé"):
        with st.spinner("Nous générons votre résumé..."):
            st.session_state.summary = process_uploaded_files(uploaded_files)

if st.session_state.summary:
    st.markdown("### ")
    st.markdown("### Résumé")
    st.markdown(st.session_state.summary)  # Display the summary in a markdown cell
    st.markdown("### ")
    # Add buttons for copying and downloading
    col1, col2 = st.columns(2)

    st.download_button(
        label="📥 Télécharger en .txt",
        data=st.session_state.summary,
        file_name="summary.txt",
        mime="text/plain"
    )