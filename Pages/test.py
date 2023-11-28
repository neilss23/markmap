from markmap_utils import read_pdf_content
import os
import tempfile


# Example usage in a Streamlit app
import streamlit as st

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")


if uploaded_file is not None:
    temp_dir = tempfile.mkdtemp()

    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as temp_file:
                temp_file.write(uploaded_file.getvalue())
    pdf_content = read_pdf_content(file_path)
    st.write(pdf_content)

