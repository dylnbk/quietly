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

        st.write("### Thanks for visiting Quietly!")

        st.write("""
            This website was made using Python, you can view the source [here](https://github.com/dylnbk/hushy).

            Store a message that can be revealed using the corresponding private key.

            Generate a password which can also be revealed using the private key.

            Share your private key, once the message has been viewed it self-destructs!
            
            To show support, you can ☕ [buy me a coffee](https://www.buymeacoffee.com/dylnbk).

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

    # for passwords use the secrets import to randomize a 12 character password
    if is_password:
        result = ''.join((secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(12)))

    # use uuid to create random strings, use .hex to get alphanumeric only
    else:
        result = str(uuid.uuid4().hex)

    return result

# create a new secret message database entry, return the secrets key
def insert_pass(secret, expire, is_password):
    
    # create a private key
    key = randomizer(False)

    # store the secret in the Deta base
    db.put({"key": key, "secret": secret, "viewed": False, "pass": is_password}, expire_in=expire)

    return key

# update database entry when it has been viewed to delete the secret
def viewed(key):

    # write over the secret and set it to expire in 10 seconds
    db.put({"key": key, "secret": "Aaaaand it's gone.", "viewed": True}, expire_in=10)

# return the secret for a specific key
def get_secret(key):

    return db.get(key)["secret"]

# return the secret for a specific key
def check_pass(key):

    return db.get(key)["pass"]

# create the message menu
def message_menu():

    # create a form
    with st.form("input_message", clear_on_submit=True):   

        # text area for user input
        user_input = st.text_area('Enter a message:')

        # create a column layout
        col1, col2 = st.columns([3, 1])

        # offer a slider selection
        with col1:
            expire = st.slider("Expires:", 1, 7, 7) * 86400
        
        # submit button
        with col2:
            confirm_hide = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user submits
        if confirm_hide:
            
            # input the message to the Deta base & return the private key
            key = insert_pass(user_input, expire, False)

            # write the private key to the screen
            st.write('Private key:')
            st.subheader(key)

# create the password menu
def pass_menu():

    # create a form
    with st.form("input_password", clear_on_submit=True):   

        # create a column layout
        col1, col2 = st.columns([3, 1])

        # offer a slider selection
        with col1:
            expire_password = st.slider("Expires:", 1, 7, 7) * 86400
        
        # submit button
        with col2:
            confirm_password = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user submits
        if confirm_password:

            # create a password
            password = randomizer(True)

            # store to Deta base and return the private key
            secret = insert_pass(password, expire_password, True)

            # write the password to the screen
            st.write("Password:")
            st.subheader(password)

            # write the private key to the screen
            st.write("Private key:")
            st.subheader(secret)

# create the menu for reveal tab
def reveal_menu():

    # create a form
    with st.form("input_reveal", clear_on_submit=True):   

        # text area for user to input their code
        user_input = st.text_input('Enter a code:')

        # submit button 
        confirm_reveal = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user hasnt submitted
        if not confirm_reveal:

            # do nothing
            return None
            
        # check the users input, call get_secret
        result = get_secret(user_input)
        
        # check if it's a password
        if check_pass(user_input):

            # write the password in a large font style
            st.write("Password:")
            st.subheader(result)

        # not a password    
        else:

            # write as a regular text format
            st.write("Secret message:")
            st.write(result)
            
        # flag that the content has been viewed, destroys the message
        viewed(user_input)

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
            message_menu()

        # generate and hide a password 
        with tab2:
            pass_menu()
        
        # reveal a secret
        with tab3:
            reveal_menu()

    # pain
    except Exception as e:
                st.error("Sorry this is not available...", icon="💔")