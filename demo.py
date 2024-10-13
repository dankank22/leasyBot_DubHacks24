import streamlit as st
import google.generativeai as genai
import pandas as pd
import pydeck as pdk
import json
import os

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

if "app_key" not in st.session_state:
    app_key = st.text_input("Please enter your Gemini API Key", type='password')
    if app_key:
        st.session_state.app_key = app_key

if "history" not in st.session_state:
    st.session_state.history = []

if "conversation_type" not in st.session_state:
    st.session_state.conversation_type = None

try:
    genai.configure(api_key=st.session_state.app_key)
except AttributeError as e:
    st.warning("Please Put Your Gemini API Key First")

model = genai.GenerativeModel("gemini-pro")

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

if "signup_mode" not in st.session_state:
    st.session_state.signup_mode = False  

if "login_mode" not in st.session_state:
    st.session_state.login_mode = False 

users = load_users()

with st.sidebar:
    st.title("**Hi, EasyLeasy users!**")
    st.markdown("")
    st.markdown("Chat with LeasyBot for instant apartment and roommate recommendations, or to report any issues with your account!")
    st.markdown("")
    st.markdown("")
    st.markdown("")

    if st.button("Clear Chat Window", use_container_width=True, type="primary"):
        st.session_state.history = []
        st.session_state.conversation_type = None
        st.rerun()

    if 'username' in st.session_state:
        st.write(f"Logged in as: {st.session_state.username}")
        if st.button("View/Edit Profile"):
            st.session_state.show_profile = True
        else:
            st.session_state.show_profile = False

        if st.button("Logout"):
            del st.session_state['username']
            st.session_state.history = []
            st.session_state.conversation_type = None
            st.success("Logged out successfully!")
    else:
        if st.button("Sign In", icon="🔑", use_container_width=True):
            st.session_state.signup_mode = False
            st.session_state.login_mode = True

        if st.button("Sign Up", icon="👤", use_container_width=True):
            st.session_state.login_mode = False
            st.session_state.signup_mode = True

# Sign In Form
if st.session_state.get('login_mode'):
    st.write("**Login to Your Account**")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type='password', key="login_password")

    if st.button("Login", use_container_width=True):
        if username in users and users[username]['password'] == password:
            st.success("Login Successful!")
            st.session_state.username = username  # Store the logged-in username in session state
            st.session_state.login_mode = False
            st.session_state.history = []
            st.session_state.conversation_type = None
        else:
            st.error("Invalid username or password")

# Sign Up Form
if st.session_state.get('signup_mode'):
    with st.form("signup_form"):
        st.write("**Create a New Account**")
        new_username = st.text_input("Choose a username", key="signup_username")
        new_password = st.text_input("Choose a password", type='password', key="signup_password")
        confirm_password = st.text_input("Confirm password", type='password', key="signup_confirm_password")
        
        # Profile Information
        full_name = st.text_input("Full Name", key="signup_full_name")
        college = st.text_input("College", key="signup_college")
        school_year = st.selectbox("School Year", options=["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "Other"], key="signup_school_year")
        major = st.text_input("Major", key="signup_major")
        apartment_option = st.text_input("Where have you signed at? (If you have not found an apartment, enter 'Still Searching')", key="signup_apartment")
        age = st.number_input("Age", min_value=18, max_value=100, key="signup_age")
        gender = st.selectbox("Gender", options=["Male", "Female", "Non-binary", "Prefer not to say", "Other"], key="signup_gender")
        smoking_habits = st.selectbox("Smoking Habits", options=["Non-smoker", "Occasional smoker", "Regular smoker"], key="signup_smoking")
        sleeping_habits = st.selectbox("Sleeping Habits", options=["Night owl", "Early bird", "Both"], key="signup_sleeping")
        guest_preferences = st.selectbox("Guest Preferences", options=["I like having guests over frequently", "I occasionally host people", "No guests"], key="signup_guests")
        has_pet = st.checkbox("Do you have a pet?", key="signup_pet")
        bio = st.text_area("Tell us about yourself", key="signup_bio")

        # File upload field for a .txt file
        txt_file = st.file_uploader("Upload a chat.txt file to automate roommate conversations", type="txt", key="signup_txt_file")

        # Roommate related questions
        looking_for_roommate = st.selectbox("Are you looking for a roommate?", options=["Yes", "No"], key="signup_looking_for_roommate")

        if looking_for_roommate == "Yes":
            roommate_smoking = st.checkbox("Roommate can smoke?", key="signup_roommate_smoking")
            roommate_has_pets = st.checkbox("Roommate can have pets?", key="signup_roommate_has_pets")
            roommate_year = st.selectbox("Preferred Year", options=["Any", "Freshman", "Sophomore", "Junior", "Senior", "Other"], key="signup_roommate_year")
            night_person = st.checkbox("Night person?", key="signup_night_person")
            gatherings = st.selectbox("Guests?", options=["Any", "Does not like having many guests over", "Likes to invite small groups", "Likes to have parties"], key="signup_gatherings")
        
        submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        elif new_username in users:
            st.error("Username already exists! Please choose a different one.")
        elif txt_file is None:
            st.error("Please upload a .txt file.")
        else:
            # Save the new user's credentials and profile
            user_data = {
                'password': new_password,
                'full_name': full_name,
                'college': college,
                'school_year': school_year,
                'major': major,
                'apartment_option': apartment_option,
                'age': age,
                'gender': gender,
                'smoking_habits': smoking_habits,
                'sleeping_habits': sleeping_habits,
                'guest_preferences': guest_preferences,
                'has_pet': has_pet,
                'bio': bio,
                'looking_for_roommate': looking_for_roommate
            }

            # Add roommate preferences if the user is looking for a roommate
            if looking_for_roommate == "Yes":
                user_data.update({
                    'roommate_smoking': roommate_smoking,
                    'roommate_has_pets': roommate_has_pets,
                    'roommate_year': roommate_year,
                    'night_person': night_person,
                    'gatherings': gatherings
                })

            users[new_username] = user_data
            save_users(users)

            # Save the uploaded .txt file in the 'txt' directory
            with open(f"txt/{new_username}.txt", "wb") as f:
                f.write(txt_file.getbuffer())

            st.success(f"Account created successfully for {full_name}!")
            st.session_state.signup_mode = False  # Close sign-up form after success

# Profile Page
if 'username' in st.session_state and st.session_state.get('show_profile', False):
    st.write("## Your Profile")

    # Load current user's data
    current_user = users[st.session_state.username]

    # Profile editing form
    with st.form("profile_form"):
        full_name = st.text_input("Full Name", value=current_user['full_name'])
        college = st.text_input("College", value=current_user['college'])
        school_year = st.selectbox("School Year", options=["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "Other"], index=["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "Other"].index(current_user['school_year']))
        major = st.text_input("Major", value=current_user['major'])
        apartment_option = st.text_input("Where have you signed at? (If you have not found an apartment, enter 'Still Searching')", value=current_user['apartment_option'])
        age = st.number_input("Age", min_value=13, max_value=100, value=current_user['age'])
        gender = st.selectbox("Gender", options=["Male", "Female", "Non-binary", "Prefer not to say", "Other"], index=["Male", "Female", "Non-binary", "Prefer not to say", "Other"].index(current_user['gender']))
        smoking_habits = st.selectbox("Smoking Habits", options=["Non-smoker", "Occasional smoker", "Regular smoker"], index=["Non-smoker", "Occasional smoker", "Regular smoker"].index(current_user['smoking_habits']))
        sleeping_habits = st.selectbox("Sleeping Habits", options=["Night owl", "Early bird", "Both"], index=["Night owl", "Early bird", "Both"].index(current_user['sleeping_habits']))
        guest_preferences = st.selectbox("Guest Preferences", options=["I like having guests over frequently", "I occasionally host people", "No guests"], index=["I like having guests over frequently", "I occasionally host people", "No guests"].index(current_user['guest_preferences']))
        has_pet = st.checkbox("Do you have a pet?", value=current_user['has_pet'])
        bio = st.text_area("Tell us about yourself", value=current_user['bio'])

        submit_profile = st.form_submit_button("Save Changes")

    if submit_profile:
        # Update user profile
        users[st.session_state.username].update({
            'full_name': full_name,
            'college': college,
            'school_year': school_year,
            'major': major,
            'apartment_option': apartment_option,
            'age': age,
            'gender': gender,
            'smoking_habits': smoking_habits,
            'sleeping_habits': sleeping_habits,
            'guest_preferences': guest_preferences,
            'has_pet': has_pet,
            'bio': bio
        })
        print(users[st.session_state.username])
        save_users(users)  # Save updated user data to JSON
        st.success("Profile updated successfully!")


# Main Application Logic
if 'username' in st.session_state:
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
        st.write("*Finding a roommate based on your preferences...*")
        
        # Load current user's data
        current_user = users[st.session_state.username]

        # Extract roommate preferences from the user profile
        if current_user.get('looking_for_roommate') == "Yes":
            roommate_gender = current_user.get('roommate_gender', 'Any')
            allow_smoking = current_user.get('roommate_smoking', False)
            allow_pets_roommate = current_user.get('roommate_has_pets', False)
            roommate_year = current_user.get('roommate_year', 'Any')
            night_person = current_user.get('night_person', False)
            gatherings = current_user.get('gatherings', 'Any')

            # Display the user's preferences
            st.write(f"Searching for roommates with the following criteria:")
            st.write(f"**Preferred Gender:** {roommate_gender}")
            st.write(f"**Can Smoke:** {'Yes' if allow_smoking else 'No'}")
            st.write(f"**Can Have Pets:** {'Yes' if allow_pets_roommate else 'No'}")
            st.write(f"**Preferred Year:** {roommate_year}")
            st.write(f"**Night Person:** {'Yes' if night_person else 'No'}")
            st.write(f"**Guest preferences:** {gatherings}")

            # Generate a response from the chatbot based on the stored input
            preferences = f"Looking for roommates. Preferred gender: {roommate_gender}, Can smoke: {allow_smoking}, Can have pets: {allow_pets_roommate}."
            st.session_state.history.append({"role": "user", "parts": [{"text": preferences}]})
            
            chat = model.start_chat(history=st.session_state.history)
            full_response = chat.send_message(preferences)
            st.session_state.history = chat.history
            
            # Display the chatbot's response
            for message in full_response:
                with st.chat_message("assistant"):
                    st.markdown(message['text'])
        else:
            st.write("It looks like you are not looking for a roommate based on your profile settings.")

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

else:
    st.write("Please log in to use the application.")
