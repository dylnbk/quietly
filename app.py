import streamlit as st
import uuid
import secrets
import string
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

            Store secrets that self destruct after being viewed & expire based on a timer.
            
            To show support, you can ☕ [buy me a coffee](https://www.buymeacoffee.com/dylnbk).

            **CAUTION**
            - All secrets will be destroyed after they have been viewed.
            """)

        st.write("***")

        st.write("""
            ##### Message
            - Store a secret message that can be viewed using the private key.
            - Choose how many days until the secret expires.
            """)
        
        st.write("***")

        st.write("""
            ##### Password
            - Press submit to generate a password & private key.
            - Choose how many days until the password expires.
            """)
        
        st.write("***")

        st.write("""
            ##### Reveal
            - Show the secret - enter the private key to reveal the message.
            - Once the message has been viewed it will self destruct.
            """)

        st.write("")
        st.write("")

# generate random strings
def randomizer(is_password):

    if is_password:

        result = ''.join((secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(12)))

    else:
        # use uuid to create random strings, use .hex to get alphanumeric only
        result = str(uuid.uuid4().hex)

    return result

# create a new secret message database entry, return the secrets key
def insert_pass(secret, expire, is_password):
    
    key = randomizer(False)

    db.put({"key": key, "secret": secret, "viewed": False, "pass": is_password}, expire_in=expire)

    return key

# update database entry when it has been viewed to delete the secret
def viewed(key):

    db.put({"key": key, "secret": "Aaaaand it's gone.", "viewed": True}, expire_in=10)

# return the secret for a specific key
def get_secret(key):

    return db.get(key)["secret"]

# return the secret for a specific key
def check_pass(key):

    return db.get(key)["pass"]

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

                    key = insert_pass(user_input, expire, False)
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
                    secret = randomizer(True)
                    final_secret = insert_pass(secret, expire_password, True)
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
                    
                    result = get_secret(user_input)
                    
                    if check_pass(user_input):
                        st.write("Password:")
                        st.subheader(result)
                    else:
                        st.write("Secret message:")
                        st.write(result)
                    viewed(user_input)

    # pain
    except Exception as e:
                st.error("Sorry this is not available...", icon="💔")