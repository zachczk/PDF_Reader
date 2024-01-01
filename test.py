import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from htmlTemplates import css, bot_template, user_template

from langchain.llms import HuggingFaceHub

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        # Create pdf object with pages
        pdf_reader = PdfReader(pdf)
        # Extract pages from pdf into a single chunk of raw text
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
def get_text_chunks(text):    
    # Break up raw text into chunks using CharacterTextSplitter from LangChain
    text_splitter = CharacterTextSplitter(
        separator = "\n",
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len
    )
    # Returns a list of chunks of text each with 1000 characters
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    # embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceInstructEmbeddings(model_name = "hkunlp/instructor-xl")

    # FAISS from_texts takes a list of text chunks (text_chunks) and their corresponding embeddings (embedding) to build the vector store
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store

def get_conversation_chain(vectorstore):
    
    # llm = ChatOpenAI()
    llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever,
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.write(response)

def main():
    load_dotenv()

    # Set user interface page configuration
    st.set_page_config(page_title="Chat with multiple PDFs",
                       page_icon=":books:")
   
    # Write CSS at the start of the webpage
    st.write(css, unsafe_allow_html=True)
   
    if "conversation" not in st.session_state:
       st.session_state.conversation = None

    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
       handle_userinput(user_question)

    # Show html inside webpage
    st.write(user_template.replace("{{MSG}}", "Hello robot"), unsafe_allow_html=True) 
    st.write(bot_template.replace("{{MSG}}", "Hello human"), unsafe_allow_html=True)
   
    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):                
                # Get raw text from pdf
                raw_text = get_pdf_text(pdf_docs)
                # st.write(raw_text)

                # Get text chunks from raw text
                text_chunks = get_text_chunks(raw_text)
                # st.write(text_chunks)

                # Get vector store from text chunks
                vectorstore = get_vectorstore(text_chunks)

                # Create conversation chain
                st.session_state.conversation = get_conversation_chain(
                    vectorstore) # Link variable to the session so that it's no reloaded
        

if __name__ == "__main__":
    main()


