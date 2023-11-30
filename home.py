import streamlit as st

def home_page():
    st.title('Welcome to Our Streamlit Application!')
    st.subheader('This application is designed to provide a concise summary of your PDF documents.')
    st.markdown("""

        1. **Prepare Your Documents:** 
           - Ensure that your PDF documents are placed in the 'streamlit-folder' directory.

        2. **API Keys Requirement:** 
           - Make sure you have the necessary API keys that the application requires to function.

        3. **Selecting Your Document:** 
           - Use the sidebar to choose a PDF document from the 'streamlit-folder'.

        4. **Automatic Summary and Visualization:** 
           - The app will read your PDF and generate a concise summary. It then creates a visual 'markmap' from this summary for easier understanding.

        5. **Interactive and User-Friendly:** 
           - Navigate through the application using interactive elements. You have the option to reset or clear your selections at any point.

    """)

if __name__ == "__main__":
    home_page()
