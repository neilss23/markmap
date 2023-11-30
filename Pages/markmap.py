import streamlit as st
from streamlit_markmap import markmap
from markmap_utils import (
    read_pdf_content,
    segment_text,
    append_to_file,
    interact_with_model,
)
from prompt import sparse_gpt, markdown_creator
import os
import tempfile
import concurrent.futures


def clean_markmap_file(file_path):
    # Read the content of the file
    with open(file_path, "r") as file:
        content = file.read()

    # Remove specific characters
    content = content.replace("```", "").replace("'''", "")

    # Write the cleaned content back to the file
    with open(file_path, "w") as file:
        file.write(content)


def create_summary(document, model="gpt-4-1106-preview"):
    pdf = read_pdf_content(document)
    seg = segment_text(pdf, chunk_size=40000)

    filename = os.path.splitext(os.path.basename(document))[0]
    summary_dir = "summary"
    summary_file = f"{summary_dir}/{filename}_summary.txt"

    os.makedirs(summary_dir, exist_ok=True)

    def process_segment(segment):
        return interact_with_model(segment, sparse_gpt, model)

    outputs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_segment = {
            executor.submit(process_segment, seg): idx
            for idx, seg in enumerate(seg.values())
        }

        for future in concurrent.futures.as_completed(future_to_segment):
            outputs.append(future.result())

    with open(summary_file, "w") as f:
        for output in outputs:
            f.write(output)

    return summary_file


def st_file_selector(
    st_placeholder,
    path="streamlit-folder",
    label="Please, select a file to process...",
    level=0,
):
    """
    This function creates a file selector widget that can be used to select a file on Streamlit.
    """
    if not os.path.isdir("streamlit-folder"):
        os.mkdir("streamlit-folder")
        st_placeholder.write(
            "Add documents to be processed in the streamlit-folder directory."
        )

    # get base path (directory)
    base_path = "streamlit-folder" if path is None or path == "" else path
    base_path = base_path if os.path.isdir(base_path) else os.path.dirname(base_path)
    base_path = (
        "streamlit-folder" if base_path is None or base_path == "" else base_path
    )

    # list folders and files in base path directory
    items = os.listdir(base_path)
    directories = [f for f in items if os.path.isdir(os.path.join(base_path, f))]
    files = [
        f
        for f in items
        if os.path.isfile(os.path.join(base_path, f)) and f.endswith(".pdf")
    ]  # only pdf files for now

    if base_path != "streamlit-folder":
        directories.insert(0, "Back")

    directories.insert(0, "streamlit-folder")
    all_items = directories + files

    # Create a unique key by appending level info to the base_path
    unique_key = f"{base_path}_{level}"

    selected_item = st_placeholder.selectbox(
        label=label, options=all_items, key=unique_key
    )

    if selected_item == "streamlit-folder":
        return os.path.normpath(base_path)

    if selected_item == "Back":
        selected_path = os.path.normpath(os.path.join(base_path, ".."))
    else:
        selected_path = os.path.normpath(os.path.join(base_path, selected_item))

    if os.path.isdir(selected_path):
        level += 1  # Increase the level for the next recursive call
        selected_path = st_file_selector(
            st_placeholder=st_placeholder, path=selected_path, label=label, level=level
        )

    return selected_path


def create_markmap_from_summary(summary_file, model="gpt-4-1106-preview"):
    markmap_dir = "markmap"
    filename = os.path.splitext(os.path.basename(summary_file))[0].replace(
        "_summary", ""
    )
    markmap_file = f"{markmap_dir}/{filename}_markmap_md.md"

    os.makedirs(markmap_dir, exist_ok=True)

    with open(summary_file, "r") as f:
        summary = f.read()

    markmap_md = interact_with_model(summary, markdown_creator, model)

    with open(markmap_file, "w") as f:
        f.write(markmap_md)

    markmap_md = clean_markmap_file(markmap_file)

    return markmap_md


# Define the Streamlit app configuration
st.set_page_config(page_title="markmap", layout="wide")


if "selected_file" not in st.session_state:
    st.session_state["selected_file"] = None
# Sidebar upload
st.sidebar.title("Select a File")
st.sidebar.write("Please select a folder to process PDF files.")
placeholder = st.sidebar.empty()
uploaded_file = st_file_selector(placeholder)
st.session_state["selected_file"] = uploaded_file


# Clear button
if st.sidebar.button("Clear"):
    # Clearing any previous states or actions
    if "summary_file" in st.session_state:
        del st.session_state.summary_file
    if "markmap_file" in st.session_state:
        del st.session_state.markmap_file
    if "selected_file" in st.session_state:
        del st.session_state.selected_file

# Main container
with st.container():
    if uploaded_file is not None:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(
            temp_dir, os.path.basename(uploaded_file)
        )  # Use basename to extract the file name
        try:
            with open(file_path, "wb") as temp_file:
                with open(
                    uploaded_file, "rb"
                ) as original_file:  # Open the original file
                    temp_file.write(original_file.read())
        except:
            pass

        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(file_path))[0]

        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(file_path))[0]
        summary_file = f"summary/{filename}_summary.txt"
        markmap_file = f"markmap/{filename}_markmap_md.md"

        if st.sidebar.button("Generate Markmap"):
            # check if file is pdf
            if os.path.splitext(file_path)[1] != ".pdf":
                st.sidebar.warning("Please select a PDF file.")

            else:
                if os.path.exists(summary_file):
                    with st.container():
                        st.subheader("Document Summary")
                        with open(summary_file, "r") as f:
                            summary_content = f.read()
                        # make it collapsible
                        with st.expander("Show summary"):
                            # make the text area read only
                            st.text_area(
                                "Summary",
                                value=summary_content,
                                height=400,
                            )
                if os.path.exists(summary_file) and not os.path.exists(markmap_file):
                    create_markmap_from_summary(summary_file)
                elif not os.path.exists(summary_file):
                    st.write("Generating summary...")
                    summary_file = create_summary(file_path)
                    create_markmap_from_summary(summary_file)

                if os.path.exists(markmap_file):
                    with open(markmap_file, "r") as f:
                        markmap_content = f.read()
                    markmap(markmap_content, 1000)
