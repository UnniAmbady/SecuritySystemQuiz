# Question and Answer on a Given Topic 
# Topic file is uploaded as a Text

import streamlit as st
from openai import OpenAI
from QnA_Utils import fetch_pdf_in_chunks
from PyPDF2 import PdfReader
import subprocess
from datetime import datetime
import pytz
from github import Github
import base64
#import re
#import json
# GitHub raw URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/UnniAmbady/SecuritySystemQuiz/main/Security_Systems_Notes.pdf"


# deifine global variables
if "sys_qn" not in st.session_state:
    st.session_state.sys_qn = "Q yet to come"
if "sys_ans" not in st.session_state:
    st.session_state.sys_ans = "Ans not ready"
if "st_answer" not in st.session_state:
    st.session_state.st_answer = "student to answer"
if "st_answered" not in st.session_state:
    st.session_state.st_answered = 0


# Show title and description.
st.title("📄 Security Systems Qns 🎈")
st.write("Read your lecture notes & refer to the PDF before answering. "
    "Students need to answer at least 2 Questions.")


query = "Create a random Question with an Answer. Answer must be short."
document = None  # Initially set to None to indicate no document is uploaded
uploaded_file = None  # Define uploaded_file ly

#parse
# Function to parse the input string

def extract_question_and_answer(generated_content):
    
    """
    Extracts the question and answer from a given string based on the keywords 'Question:' and 'Answer:'.
    
    Parameters:
        generated_content (str): The input string containing the question and answer.
        
    Returns:
        tuple: A tuple containing the question (qn) and the answer (ans).
    """
    try:
        # Split the content into parts based on the keywords
        question_part = generated_content.split("Question:", 1)[-1]
        answer_part = question_part.split("Answer:", 1)
        
        # Extract the question and answer
        qn = answer_part[0].strip()  # Question part
        ans = answer_part[1].strip() if len(answer_part) > 1 else ""  # Answer part
        # Remove '**' from the question and answer
        qn = qn.replace("**", "")
        ans = ans.replace("**", "")
        return qn, ans
    except Exception as e:
        raise ValueError(f"Error parsing content: {e}")
#end of parsing


# Define the function to be called when the button is clicked
def AskQn():
    # Placeholder for future implementation
    global document, query   # Access the global variables
 
    # Conditionally avoid redundant parsing of the file
    if not document:
        document = uploaded_file.read().decode()

    messages = [
        {"role": "system", "content": f"Keep the scope of answering strictly within the context of the document: {document}."},
        {"role": "system", "content": f"If a question is not within the scope of the document, respond with 'I am not sure'."},
        {"role": "user", "content": f"Here's a document: {document} \n\n---\n\n {query}"}
    ]
    
                # Generate an answer using the OpenAI API.
    stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=False)
    generated_content = stream.choices[0].message.content
    sys_qn, sys_ans = extract_question_and_answer(generated_content)
    st.write(sys_qn)
    # if(not hide_ans):
        # st.write(sys_ans)  
    return sys_qn, sys_ans
#function ended

# Add the Validate function
def Validate():
    sys_qn = st.session_state.sys_qn
    sys_ans = st.session_state.sys_ans
    st_answer = st.session_state.st_answer
    #to do 28 Nov 2024
    st.write("Thanks: The results will be sent to you at a later date.")
###########################################################################30 Nov
    messages =  [{"role": "user",
    "content": f"[Ignore Grammar and Spelling errors]. \
                [Respond in bullet Form as brief as possible] \
                 [Compare the and Comment on any Logical Errors] \
                 [Be very lenient & dont flash too many errors. AWARD a higher grade, cap at 90%] \
                 [Based on the logical correctness, **AWARD** a Grade  0 to 100% scale] \
                 [Correct Answer {sys_ans}] \n\n---\n\n [Student_Ans{st_answer} ]"
                 }]            
        
                # Generate an answer using the OpenAI API.
    stream1 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages, 
                    temperature= 0.6,  # Added temperature parameter.
                    stream=True,
                )
    st.write( f"**Question:** {sys_qn}\n " )
    st.write( f"**Modal Ans:** {sys_ans}\n " )
    st.write( f"**Your Answer:**\n {st_answer}\n " )
    st.write_stream(stream1)
    # Call log_and_commit function after the above Streamlit writes
    log_and_commit(sys_qn, sys_ans, st_answer, stream1)

##############################################################################30 Nov
  
    return




def log_and_commit(sys_qn: str, sys_ans: str, st_ans: str, writer):
    """
    sys_qn, sys_ans, st_ans = question, model’s answer, student’s answer
    writer = a Streamlit placeholder (e.g. stream1 = st.empty())
    """

    # 0) Authenticate
    github_token = st.secrets["github"]["token"]
    gh           = Github(github_token)
    repo         = gh.get_repo("UnniAmbady/SecuritySystemQuiz")

    # 1) Build timestamped entry
    ts = datetime.now(pytz.timezone("Asia/Singapore")) \
             .strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"Timestamp:    {ts}\n"
        f"Question:     {sys_qn}\n"
        f"Modal Answer: {sys_ans}\n"
        f"Student Ans:  {st_ans}\n"
        + "-"*40 + "\n"
    )

    # 2) Update or create Activity_log.txt
    log_path = "Activity_log.txt"
    try:
        existing = repo.get_contents(log_path, ref="main")
        new_body = existing.decoded_content.decode() + entry
        repo.update_file(
            path=log_path,
            message=f"Update log at {ts}",
            content=new_body,
            sha=existing.sha,
            branch="main"
        )
        writer.write("✅ Activity_log.txt updated on GitHub.")
    except GithubException as e:
        if e.status == 404:
            repo.create_file(
                path=log_path,
                message=f"Create log at {ts}",
                content=entry,
                branch="main"
            )
            writer.write("✅ Activity_log.txt created on GitHub.")
        else:
            raise   # re-raise any other errors

    # 3) (Optional) ensure the workflow YAML exists
    wf_path = ".github/workflows/log-processor.yml"
    wf_yaml = """\
    name: Process Activity Log

    on:
      push:
        paths:
          - 'Activity_log.txt'

    jobs:
      parse:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Display log
            run: |
              echo "::group::Activity Log"
              cat Activity_log.txt
              echo "::endgroup::"
    """
    try:
        wf_file = repo.get_contents(wf_path, ref="main")
        repo.update_file(
            path=wf_path,
            message=f"Update workflow at {ts}",
            content=wf_yaml,
            sha=wf_file.sha,
            branch="main"
        )
        writer.write("✅ Workflow updated on GitHub.")
    except GithubException as e:
        if e.status == 404:
            repo.create_file(
                path=wf_path,
                message=f"Add log-processor workflow at {ts}",
                content=wf_yaml,
                branch="main"
            )
            writer.write("✅ Workflow created on GitHub.")
        else:
            raise

    return

### __mail__ body Starts from here

# openai_api_key = st.text_input("OpenAI API Key", type="password")
openai_api_key = st.secrets["openai"]["secret_key"]
client = OpenAI(api_key=openai_api_key)

if not client:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Streamlit app layout
    st.title("Interactive Q&A Generator")
    pdf_data = fetch_pdf_in_chunks(GITHUB_RAW_URL)

    if pdf_data:
        reader = PdfReader(pdf_data)
        document = ""
        for page in reader.pages:
            document += page.extract_text() or ""
    else:
        st.error("Failed to load Security_Systems_Notes.pdf from GitHub.")
        st.stop()
        
    uploaded_file= document #used back old variable name

    if uploaded_file:             
        if st.button("Ask Question"):         
            sys_qn, sys_ans = AskQn()
            st.session_state.sys_qn =sys_qn
            st.session_state.sys_ans =sys_ans
            
        if st_answer := st.chat_input("Type your Answer here"):
            st.session_state.st_answer = st_answer
            st.session_state.st_answered = 1
            #save_global(sys_qn, sys_ans, st_answer)              
            Validate()     
    
  
    if not uploaded_file:
        st.write("Upload a file before you can ask a Question.")
        



