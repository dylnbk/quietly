import streamlit as st
import uuid
from deta import Deta

# load & inject style sheet
def local_css(file_name):

    # write <style> tags to allow custom css
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# generate the see info box
def info_box():

    # create an info box
    with st.expander("See info"):

        st.write("### Thanks for visiting Hushy!")

        st.write("""
            This website was made using Python, you can view the source [here](https://github.com/dylnbk/hushy).
            
            Send secrets that self destruct after being viewed & expire based on a timer.
            
            To show support, you can ☕ [buy me a coffee](https://www.buymeacoffee.com/dylnbk).

            **CAUTION** 
            - All secrets will expire after 7 days.
            """)

        st.write("***")

        st.write("""
            ##### Hide
            - Send a secret - you will get a code to send to the recipient.
            - Choose how many days until the secret expires.
            """)
        
        st.write("***")

        st.write("""
            ##### Reveal
            - Show a secret - enter your code to reveal the secret message.
            - Once the message has been viewed it will self destruct.
            """)

        st.write("")
        st.write("")

# generate random file names
def file_name():

    # use uuid to create random strings, use .hex to get alphanumeric only
    result = str(uuid.uuid4().hex)

    return result

# create a new secret message database entry, return the secrets key
def insert_pass(secret, expire):
    
    key = file_name()

    db.put({"key": key, "secret": secret, "viewed": False}, expire_in=expire)

    return key

# update database entry when it has been viewed to delete the secret
def viewed(key):

    db.put({"key": key, "secret": "Aaaaand it's gone.", "viewed": True}, expire_in=10)

# return the secret for a specific key
def get_secret(key):

    return db.get(key)["secret"]

# main VISUAL ELEMENTS BEGIN HERE <<----------------------------------------------------------------------------||

# burger menu config
st.set_page_config(
    page_title="Whisper it.",
    page_icon="👀",
    menu_items={
        'Report a bug': "mailto:dyln.bk@gmail.com",
        'Get help': None,
        'About': "Made by dyln.bk"
    }
)

# connect with NoSQL API Deta
deta = Deta(st.secrets["DETA_KEY"])

# open database
db = deta.Base("secret_control")

# inject css
local_css("style.css")

# page title
st.title('Whisper it.')

# define tabs
tab1, tab2, tab3 = st.tabs(["Message", "Password", "Reveal"])

# start script
if __name__ == "__main__":

    try:

        # hide a secret message
        with tab1:

            with st.form("input_message", clear_on_submit=True):   

                # text area for user input limited to 1.5k chars
                user_input = st.text_area('Enter a message:', max_chars=1500)

                # create a column layout
                col1, col2 = st.columns([3, 1])

                # offer a slider selection
                with col1:
                    expire = st.slider("Expires:", 1, 7, 7) * 86400
                
                # submit button
                with col2:
                    # submit button with onclick that sends the message to be entered to the database
                    confirm_hide = st.form_submit_button("Submit")

                info_box()

                if confirm_hide:

                    key = insert_pass(user_input, expire)
                    st.write('Private key:')
                    st.subheader(db.get(key)["key"])

        # generate and hide a password 
        with tab2:

            with st.form("input_password", clear_on_submit=True):   

                # create a column layout
                col1, col2 = st.columns([3, 1])

                # offer a slider selection
                with col1:
                    expire_password = st.slider("Expires:", 1, 7, 7) * 86400
                
                # submit button
                with col2:
                    # submit button with onclick that sends the message to be entered to the database
                    confirm_password = st.form_submit_button("Submit")

                info_box()

                if confirm_password:
                    secret = file_name()
                    final_secret = insert_pass(secret, expire_password)
                    st.write("Password:")
                    st.subheader(secret)
                    st.write("Private key:")
                    st.subheader(db.get(final_secret)["key"])
        
        # reveal a secret
        with tab3:

            with st.form("input_reveal", clear_on_submit=True):   

                # text area for user to input their code
                user_input = st.text_input('Enter a code:')

                # submit button with onclick that grabs the corresponding database entry
                confirm_reveal = st.form_submit_button("Submit")

                info_box()

                if confirm_reveal:

                    st.write("Secret:")
                    st.subheader(get_secret(user_input))
                    viewed(user_input)

    # pain
    except Exception as e:
                st.error(e, icon="💔")