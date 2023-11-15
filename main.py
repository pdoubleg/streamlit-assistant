import streamlit as st
from chatbot import Chatbot

# Initialize the chatbot
chatbot = Chatbot()

def main():
    st.title("Streamlit Chatbot App")
    st.write("Welcome to our chatbot app. Ask me anything!")

    user_input = st.text_input("You: ", "")
    if st.button("Send"):
        response = chatbot.get_response(user_input)
        st.write("Chatbot: ", response)

if __name__ == "__main__":
    main()
