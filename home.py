import streamlit as st
from streamlit_markmap import markmap
from markmap_utils import read_pdf_content, segment_text, append_to_file, interact_with_model
from prompt import sparse_gpt, markdown_creator
import os
import tempfile
import concurrent.futures


def create_markmap(document, model="gpt-4-1106-preview"):
    pdf = read_pdf_content(document)
    seg = segment_text(pdf, chunk_size=20000)

    filename = os.path.splitext(os.path.basename(document))[0]
    summary_dir = 'summary'
    markmap_dir = 'markmap'
    summary_file = f"{summary_dir}/{filename}_summary.txt"
    markmap_file = f"{markmap_dir}/{filename}_markmap_md.md"

    if os.path.exists(summary_file) and os.path.exists(markmap_file):
        with open(markmap_file, "r") as f:
            return f.read()

    os.makedirs(summary_dir, exist_ok=True)
    os.makedirs(markmap_dir, exist_ok=True)

    def process_segment(segment):
        return interact_with_model(segment, sparse_gpt, model)

    outputs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map segments to the processing function
        future_to_segment = {executor.submit(process_segment, seg): idx for idx, seg in enumerate(seg.values())}

        # Collect results in the order they were submitted
        for future in concurrent.futures.as_completed(future_to_segment):
            outputs.append(future.result())

    # Append outputs in order to the file
    with open(summary_file, "w") as f:
        for output in outputs:
            f.write(output)

    with open(summary_file, "r") as f:
        summary = f.read()

    markmap_md = interact_with_model(summary, markdown_creator, model)

    with open(markmap_file, "w") as f:
        f.write(markmap_md)

    return markmap_md


st.set_page_config(page_title="markmap", layout="wide")

#side bar upload
st.sidebar.title("Upload a file")

uploaded_file = st.sidebar.file_uploader("Choose a file")
# create a session state variable to store the markmap
if "markmap" not in st.session_state:
    st.session_state.markmap = None
    
# clear button
if st.sidebar.button("Clear"):
    st.session_state.markmap = None

st.container()
with st.container():
    if uploaded_file is not None:
        temp_dir = tempfile.mkdtemp()

        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, 'wb') as temp_file:
                    temp_file.write(uploaded_file.getvalue())

        st.session_state.markmap = create_markmap(file_path)

    if st.session_state.markmap is not None:
        markmap(st.session_state.markmap,1000)