import streamlit as st
import google.generativeai as genai
import pandas as pd
import streamlit_authenticator as stauth
import pydeck as pdk

# Load apartment data from an Excel file
def load_apartment_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame() 

apartment_data = load_apartment_data('Apartment_DB.xlsx')

st.set_page_config(
    page_title="LeasyBot",
    
)

st.title("Chat with LeasyBot")
st.caption("A Chatbot Powered by Google Gemini Pro")

# Ensure the session state for the API key and conversation history
if "app_key" not in st.session_state:
    app_key = st.text_input("Please enter your Gemini API Key", type='password')
    if app_key:
        st.session_state.app_key = app_key

if "history" not in st.session_state:
    st.session_state.history = []

if "conversation_type" not in st.session_state:
    st.session_state.conversation_type = None

# Initialize the chatbot API if the API key is available
try:
    genai.configure(api_key=st.session_state.app_key)
except AttributeError as e:
    st.warning("Please Put Your Gemini API Key First")

model = genai.GenerativeModel("gemini-pro")


# Initialize session state variables
if "credentials" not in st.session_state:
    st.session_state.credentials = {}  # Store usernames and passwords

if "login_username" not in st.session_state:
    st.session_state.login_username = ""

if "login_password" not in st.session_state:
    st.session_state.login_password = ""

if "signup_mode" not in st.session_state:
    st.session_state.signup_mode = False  # Toggle for showing the sign-up form

if "login_mode" not in st.session_state:
    st.session_state.login_mode = False  # Toggle for showing the login form


with st.sidebar:
    st.title("**Hi, EasyLeasy users!**")
    st.markdown("")
    st.markdown("Chat with LeasyBot for instant apartment and roommate recommendations, or to report any issues with your account!")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    

    if st.button("Clear Chat Window", use_container_width=True, type="primary"):
        st.session_state.history = []
        st.session_state.conversation_type = None
        st.rerun()

    # Toggle between sign-in and sign-up modes
    if st.button("Sign In", icon="🔑", use_container_width=True):
        st.session_state.signup_mode = False
        st.session_state.login_mode = True

    if st.button("Sign Up", icon="👤", use_container_width=True):
        st.session_state.login_mode = False
        st.session_state.signup_mode = True

    # Sign In Form
    if st.session_state.login_mode:
        st.write("**Login to Your Account**")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type='password', key="login_password")

        if st.button("Login", use_container_width=True):
            if username in st.session_state.credentials and \
                    st.session_state.credentials[username] == password:
                st.success("Login Successful!")
                st.session_state.history = []
                st.session_state.conversation_type = None
            else:
                st.error("Invalid username or password")

    # Sign Up Form
    if st.session_state.signup_mode:
        with st.form("signup_form"):
            st.write("**Create a New Account**")
            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input("Choose a password", type='password', key="signup_password")
            confirm_password = st.text_input("Confirm password", type='password', key="signup_confirm_password")
            full_name = st.text_input("Full Name", key="signup_full_name")
            submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif new_username in st.session_state.credentials:
                st.error("Username already exists! Please choose a different one.")
            else:
                st.session_state.credentials[new_username] = new_password
                st.success(f"Account created successfully for {full_name}!")
                st.session_state.history = []
                st.session_state.conversation_type = None
                st.session_state.signup_mode = False  # Close sign-up form after success


# Show conversation options if no conversation type is chosen yet
if st.session_state.conversation_type is None:
    st.write("Hi, how may I assist you today?")
    
# Create columns for side-by-side buttons
col1, col2, col3 = st.columns(3)

# Set the button states dynamically based on conversation_type
with col1:
    st.button("I'm looking for an apartment", 
              on_click=lambda: st.session_state.update({"conversation_type": "apartment"}),
              disabled=st.session_state.conversation_type is not None)

with col2:
    st.button("I'm looking for roommates", 
              on_click=lambda: st.session_state.update({"conversation_type": "roommate"}),
              disabled=st.session_state.conversation_type is not None)

with col3:
    st.button("I require tech support", 
              on_click=lambda: st.session_state.update({"conversation_type": "tech Support"}),
              disabled=st.session_state.conversation_type is not None)

# Add a visual indicator for the selected option
if st.session_state.conversation_type is not None:
    st.write(f"**Selected Option:** {st.session_state.conversation_type.replace('_', ' ').capitalize()}")

# Handling different conversation types
if st.session_state.conversation_type == "apartment":
    st.write("*Please adjust the sliders and options to define your preferences.*")
    
    # User Inputs for apartment
    price_range = st.slider("What is your budget range?", 500, 3000, (900, 1400))
    num_bedrooms = st.slider("How many bedrooms are you looking for?", 1, 6, (1,2))
    allow_pets = st.checkbox("Do you have a pet?")
    need_parking = st.checkbox("Do you require parking?")
    need_gym = st.checkbox("Do you require a gym?")
    
    if st.button("Submit Preferences"):
        preferences = f"Looking for apartments with a budget range of {price_range[0]} to {price_range[1]}, with {num_bedrooms} bedrooms. Pets allowed: {allow_pets}, Parking needed: {need_parking}, Gym: {need_gym}."
        st.session_state.history.append({"role": "user", "parts": [{"text": preferences}]})
    
        
        filtered_apartments = apartment_data[
            (apartment_data['Cost'] >= price_range[0]) &
            (apartment_data['Cost'] <= price_range[1]) &
            (apartment_data['Bedrooms'] >= num_bedrooms[0]) &
            (apartment_data['Bedrooms'] <= num_bedrooms[1]) &
            (apartment_data['Allow Pets?'].astype(bool) == allow_pets if allow_pets else True) &  
            (apartment_data['Parking?'].astype(bool) == need_parking if need_parking else True) & 
            (apartment_data['Gymnasium?'].astype(bool) == need_gym if need_gym else True)        
        ]

        # Check if filtered apartments are available
        if not filtered_apartments.empty:
            st.write("### Apartments that match your preferences:")
            st.dataframe(filtered_apartments)

            # Extract latitude and longitude
            if 'Latitude' in filtered_apartments.columns and 'Longitude' in filtered_apartments.columns:
                map_data = filtered_apartments[['Latitude', 'Longitude']].dropna()
                map_data = map_data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'})
                map_data = map_data.astype({'latitude': 'float', 'longitude': 'float'})

                if not map_data.empty:
                    # Define a Pydeck layer with smaller circle markers
                    layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=map_data,
                        get_position='[longitude, latitude]',
                        get_color='[200, 30, 0, 160]',  # Red color with some transparency
                        get_radius=50,  # Radius of each circle (in meters)
                        pickable=True,  # Enables interactivity
                    )

                    # Create the Pydeck map
                    view_state = pdk.ViewState(
                        latitude=map_data['latitude'].mean(),
                        longitude=map_data['longitude'].mean(),
                        zoom=12,  # Adjust zoom for a better view
                        pitch=0
                    )

                    # Render the map with Pydeck
                    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

                else:
                    st.write("No valid coordinates available for the selected apartments.")
            else:
                st.write("Latitude and Longitude data not found in the filtered results.")
        else:
            st.write("No apartments match your preferences. Try adjusting the filters.")



        


elif st.session_state.conversation_type == "roommate":
    st.write("*Please provide your preferences for finding a roommate.*")
    
    # Roommate preferences
    roommate_gender = st.selectbox("Preferred Roommate Gender", options=["Any", "Male", "Female", "LBGTQIA+"])
    allow_smoking = st.checkbox("Roommate can smoke?")
    allow_pets_roommate = st.checkbox("Roommate can have pets?")
    roommate_year = st.selectbox("Preferred Year", options=["Any", "Freshman", "Sophomore", "Junior", "Senior", "Other"])
    night_person = st.checkbox("Night person?")
    gatherings = st.selectbox("Guests?", options=["Any","Does not like having many guests over", "Likes to invite small groups", "Likes to have parties"])
    
    if st.button("Submit Preferences"):
        # Append the roommate preferences to the chat history
        preferences = f"Looking for roommates. Preferred gender: {roommate_gender}, Can smoke: {allow_smoking}, Can have pets: {allow_pets_roommate}."
        st.session_state.history.append({"role": "user", "parts": [{"text": preferences}]})
        
        # Display the user's preferences
        st.write(f"Searching for roommates with the following criteria:")
        st.write(f"**Preferred Gender:** {roommate_gender}")
        st.write(f"**Can Smoke:** {'Yes' if allow_smoking else 'No'}")
        st.write(f"**Can Have Pets:** {'Yes' if allow_pets_roommate else 'No'}")
        st.write(f"**Preferred Year:** {roommate_year}")
        st.write(f"**Sleeping habits:** {'Yes' if night_person else 'No'}")
        st.write(f"**Guest preferences:** {gatherings}")
        
        # Generate a response from the chatbot based on the input
        chat = model.start_chat(history=st.session_state.history)
        full_response = chat.send_message(preferences)
        st.session_state.history = chat.history
        
        # Display the chatbot's response
        for message in full_response:
            with st.chat_message("assistant"):
                st.markdown(message['text'])

elif st.session_state.conversation_type == "tech Support":
    st.write("*Please provide more details for tech support.*")
    
    # User input for tech support
    issue_description = st.text_area("Describe the issue you're facing:")
    
    if st.button("Submit Issue"):
        # Append the tech support issue to the chat history
        st.session_state.history.append({"role": "user", "parts": [{"text": issue_description}]})
        
        # Generate a response from the chatbot based on the input
        chat = model.start_chat(history=st.session_state.history)
        full_response = chat.send_message(issue_description)
        st.session_state.history = chat.history
        
        # Display the chatbot's response
        for message in full_response:
            with st.chat_message("assistant"):
                st.markdown(message['text'])
