import streamlit as st
from openai import OpenAI
import requests
from PyPDF2 import PdfReader
from io import BytesIO

# GitHub raw URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/UnniAmbady/SecuritySystemQuiz/main/Security_Systems_Notes.pdf"

# Fetch the PDF from GitHub
@st.cache_data
def fetch_pdf(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

pdf_data = fetch_pdf(GITHUB_RAW_URL)

if pdf_data:
    reader = PdfReader(BytesIO(pdf_data))
    document = "".join(page.extract_text() for page in reader.pages)
else:
    st.error("Failed to load Security_Systems_Notes.pdf from GitHub.")
    st.stop()

# Retain rest of your original functionalities

# Define your global session state variables
if "sys_qn" not in st.session_state:
    st.session_state.sys_qn = "Q yet to come"
if "sys_ans" not in st.session_state:
    st.session_state.sys_ans = "Ans not ready"
if "st_answer" not in st.session_state:
    st.session_state.st_answer = "student to answer"

# Continue with existing functionality to generate and validate questions using OpenAI
openai_api_key = st.secrets["openai"]["secret_key"]
client = OpenAI(api_key=openai_api_key)

# Place the rest of your code for question and answer generation below
# Example:
st.title("📄 Security Quiz 🎈")
st.write("Read the Document given above and Answer the Questions. The answers are not graded—read the feedback for your improvement.")

if st.button("Ask Question"):
    query = "Create a random Question with an Answer. Answer must be short."

    messages = [
        {"role": "system", "content": f"Keep the scope of answering strictly within the context of the document: {document}."},
        {"role": "user", "content": query}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=False
    )

    generated_content = response.choices[0].message.content
    st.session_state.sys_qn, st.session_state.sys_ans = generated_content.split("Answer:")
    st.session_state.sys_qn = st.session_state.sys_qn.replace("Question:", "").strip()
    st.session_state.sys_ans = st.session_state.sys_ans.strip()

    st.write("Question:", st.session_state.sys_qn)
    st.write("Answer:", st.session_state.sys_ans)

if st_answer := st.chat_input("Type your Answer here"):
    st.session_state.st_answer = st_answer
    # Call your Validate function here if needed
