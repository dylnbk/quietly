import streamlit as st
import uuid
import secrets
import string
import hashlib
from deta import Deta
from base64 import b64encode, b64decode
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes

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
                 
            Check out my personal website [dylnbk.page](https://dylnbk.page).

            Store a message that can be revealed using the corresponding public key.

            Generate a password which can also be revealed using the public key.

            Share your public key, once the message has been viewed it self-destructs!
                 
            Use the passphrase option to encrypt your message before it is stored in our database.
            
            To show support, please consider ☕ [buying me a coffee](https://www.buymeacoffee.com/dylnbk).

            """)

        st.write("***")

        st.write("""
            ##### Message
            - Store a secret message that can be viewed using the public key.
            - Choose how many days until the secret expires.
            - Optionally encrypt your message with a passphrase.
            """)
        
        st.write("***")

        st.write("""
            ##### Password
            - Press submit to generate a password & public key.
            - Choose how many days until the password expires.
            - Optionally encrypt your password with a passphrase.
            """)
        
        st.write("***")

        st.write("""
            ##### Reveal
            - Enter the public key & optional passphrase to reveal the message.
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
        result = ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(18)))

    return result

# create a new secret message database entry, return the secrets key
def insert_pass(secret, expire, nonce, tag, is_password):
    
    # create a public key
    key = randomizer(False)

    # store the secret in the Deta base
    db.put({"key": key, "secret": secret, "viewed": False, "nonce": nonce, "tag": tag,"pass": is_password}, expire_in=expire)

    return key

# update database entry when it has been viewed to delete the secret
def viewed(key):

    # write over the secret and set it to expire in 10 seconds
    db.put({"key": key, "secret": "Aaaaand it's gone.", "viewed": True}, expire_in=10)

# return the secret for a specific key
def get_secret(key):

    return db.get(key)["secret"], db.get(key)["nonce"], db.get(key)["tag"]

# return the secret for a specific key
def check_pass(key):

    return db.get(key)["pass"]

# function to encrypt a message using a given passphrase
def encrypt(message: str, passphrase: str) -> str:
    # generate a private key using scrypt hash function
    # the input passphrase is encoded to bytes and a salt (to add randomness) is added
    # the cost factor (N), block size factor (r) and parallelization factor (p) are set to specify the CPU/memory cost factor, block size factor and maximum parallelization respectively.
    private_key = hashlib.scrypt(
        passphrase.encode(), salt=b'salt_', n=2**14, r=8, p=1, dklen=32)

    # create a new AES cipher object using the generated private key and AES MODE_GCM (Galois/Counter Mode)
    cipher_config = AES.new(private_key, AES.MODE_GCM)

    # encrypt the message and generate an authentication tag using the configured AES cipher
    cipher_text, tag = cipher_config.encrypt_and_digest(bytes(message, 'utf-8'))

    # return the nonce (random value used for encryption), tag and encrypted text, each one has been encoded using base64
    return b64encode(cipher_config.nonce).decode('utf-8'), b64encode(tag).decode('utf-8'), b64encode(cipher_text).decode('utf-8')

# function to decrypt an encrypted message using the given nonce, tag, ciphertext and a passphrase
def decrypt(nonce: str, tag: str, ciphertext: str, passphrase: str) -> str:
    # generate the private key just as we did during encryption
    private_key = hashlib.scrypt(
        passphrase.encode(), salt=b'salt_', n=2**14, r=8, p=1, dklen=32)

    # create the new AES cipher object using the generated private key and MODE_GCM, but also using the original nonce and mac_len
    cipher_config = AES.new(private_key, AES.MODE_GCM,
                            nonce=b64decode(nonce),
                            mac_len=16)

    # update the cipher object with the tag which has been decoded from base64
    cipher_config.update(b64decode(tag))

    # decrypt the ciphertext after decoding it from base64
    decrypted = cipher_config.decrypt(b64decode(ciphertext))

    # return the decrypted message as a string
    return decrypted.decode()

# create the message menu
def message_menu():

    # create a form
    with st.form("input_message", clear_on_submit=True):   

        # text area for user input
        user_input = st.text_area('Enter a message:')

        # password used to encrypt the message
        passphrase = st.text_input("Passphrase (optional):")

        nonce, tag, message = encrypt(user_input, passphrase)

        # offer a slider selection
        expire = st.slider("Expires (days):", 1, 7, 7) * 86400
        
        # submit button
        confirm_hide = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user submits
        if confirm_hide:
            
            # input the message to the Deta base & return the public key
            key = insert_pass(message, expire, nonce, tag, False)

            # write the public key to the screen
            st.write('Public key:')
            st.subheader(key)

            if passphrase:
                # write the passphrase to the screen
                st.write("")
                st.write('Passphrase:')
                st.subheader(passphrase)

# create the password menu
def pass_menu():

    # create a form
    with st.form("input_password", clear_on_submit=True):   

        # passphrase used to encrypt the message
        passphrase = st.text_input("Passphrase (optional):")

        # offer a slider selection
        expire_password = st.slider("Expires:", 1, 7, 7) * 86400
        
        # submit button
        confirm_password = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user submits
        if confirm_password:

            # create a password
            password = randomizer(True)

            nonce, tag, message = encrypt(password, passphrase)

            # store to Deta base and return the public key
            secret = insert_pass(message, expire_password, nonce, tag, True)

            # write the password to the screen
            st.write("Password:")
            st.subheader(password)

            # write the public key to the screen
            st.write("")
            st.write("Public key:")
            st.subheader(secret)

            if passphrase:
                # write the passphrase to the screen
                st.write("")
                st.write('Passphrase:')
                st.subheader(passphrase)

# create the menu for reveal tab
def reveal_menu():

    # create a form
    with st.form("input_reveal", clear_on_submit=True):   

        # text area for user to input their code
        user_input = st.text_input('Enter a key:')

        # passphrase used to encrypt the message
        passphrase = st.text_input("Passphrase (if provided):")

        # submit button 
        confirm_reveal = st.form_submit_button("Submit")

        # info - here due to layout prefereces
        info_box()

        # if the user hasnt submitted
        if not confirm_reveal:

            # do nothing
            return None
            
        # check the users input, call get_secret
        encrypted, nonce, tag = get_secret(user_input)

        decrypted = decrypt(nonce, tag, encrypted , passphrase)
        
        # check if it's a password
        if check_pass(user_input):

            # write the password in a large font style
            st.write("Password:")
            st.subheader(decrypted)

        # not a password    
        else:

            # write as a regular text format
            st.write("Secret message:")
            st.write(decrypted)
            
        # flag that the content has been viewed, destroys the message
        viewed(user_input)

# burger menu config
st.set_page_config(
    page_title="Whisper it.",
    page_icon="👀",
    menu_items={
        'Report a bug': "mailto:dyln.bk@gmail.com",
        'Get help': None
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
                st.error("Secret already revealed or passphrase required...", icon="💔")
