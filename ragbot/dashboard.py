import streamlit as st
import openai
import oai_utils
import weav
import st_utils
from config import OPENAI_API_KEY, get_client
import utils
import time


# Set OpenAI and Weaviate API keys
openai.api_key = OPENAI_API_KEY
client = get_client()
weaviate_classname = 'New_manuals'


st.title(":high_brightness: nanobot")
st.markdown(" #### **Select the manual/domain in the sidebar**")


with st.sidebar:
    st.sidebar.markdown("# :high_brightness: nanobot")
    st.sidebar.markdown("---")
    if st.button('Clear message history'):
        st_utils.clear_messages()
    tenants = weav.write_tenants(weaviate_classname)
    selected_manual = st.sidebar.selectbox('Select a Manual', tenants)
    # gets the manual link from the google doc
    url = utils.get_tenant_info_from_df('url_link', selected_manual)
    button_text = 'Click for manual link'
    st.markdown(f'<a href="{url}" target="_blank"><button>{button_text}</button></a>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.subheader("Retrieval Parameters:")
    k = st.number_input('top-k most salient embeds', 
                        min_value=1, 
                        max_value=50, 
                        value=10, 
                        on_change=st_utils.clear_history)
    st.sidebar.markdown("---")

# Initialize the message list if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    role = message.get("role")
    content = message.get("content")
    if role and content:  # then it is not just initializing
        with st.chat_message(role):
            st.markdown(content)
            if (message.get("role") == "assistant" and 
                "retrieved_texts" in message):
                with st.expander("Show Retrieved Texts"):
                    st.markdown(message["retrieved_texts"], 
                                unsafe_allow_html=True)


user_message = st.chat_input("Enter your question here: ")

if user_message is not None and user_message.strip() != "":
    st.session_state.messages.append({
        "role": "user", 
        "content": user_message
    })

    with st.chat_message("user"):
        st.markdown(user_message)
    with st.spinner('Retriving results ...'):
        try:
            retrieved_texts = weav.query_weaviate(
                user_message, k, weaviate_classname, selected_manual
            )
            description = utils.get_tenant_info_from_df(
                'description', selected_manual
            )
            system_message = oai_utils.get_system_tool_message(
                retrieved_texts, description
            )
            messages = [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': (
                    f"{oai_utils.delimiter}{user_message}{oai_utils.delimiter}"
                )}
            ]
            response = oai_utils.get_completion_from_messages(messages)
            # this holds the entire message history including the dropdowns
            st.session_state.messages.append({
                'role':'assistant', 
                'content': response,
                'retrieved_texts': (
                    st_utils.format_retrieved_texts(retrieved_texts)
                )
            })
            # show the response 
            with st.chat_message("assistant"):
                st.markdown(response)
            # show the dropdown option with the data
            with st.expander("Show Retrieved Texts"):
                st_utils.display_retrieved_texts(retrieved_texts)
    
        except Exception as e:
            st.write(f"Error: {e}")

