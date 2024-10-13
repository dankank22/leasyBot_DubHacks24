import streamlit as st
import google.generativeai as genai
import pandas as pd
import pydeck as pdk
import json
import os

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

# Path to the JSON file
USERS_FILE = 'users.json'

# Function to load users from the JSON file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

# Function to save users to the JSON file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Initialize session state variables
if "signup_mode" not in st.session_state:
    st.session_state.signup_mode = False  # Toggle for showing the sign-up form

if "login_mode" not in st.session_state:
    st.session_state.login_mode = False  # Toggle for showing the login form

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
        # Toggle between sign-in and sign-up modes
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
        age = st.number_input("Age", min_value=13, max_value=100, key="signup_age")
        gender = st.selectbox("Gender", options=["Male", "Female", "Non-binary", "Prefer not to say", "Other"], key="signup_gender")
        smoking_habits = st.selectbox("Smoking Habits", options=["Non-smoker", "Occasional smoker", "Regular smoker"], key="signup_smoking")
        sleeping_habits = st.selectbox("Sleeping Habits", options=["Night owl", "Early bird", "Both"], key="signup_sleeping")
        guest_preferences = st.selectbox("Guest Preferences", options=["I like having guests over frequently", "I occasionally host people", "No guests"], key="signup_guests")
        has_pet = st.checkbox("Do you have a pet?", key="signup_pet")
        bio = st.text_area("Tell us about yourself", key="signup_bio")
        
        submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        elif new_username in users:
            st.error("Username already exists! Please choose a different one.")
        else:
            # Save the new user's credentials and profile
            users[new_username] = {
                'password': new_password,
                'full_name': full_name,
                'college': college,
                'school_year': school_year,
                'major': major,
                'age': age,
                'gender': gender,
                'smoking_habits': smoking_habits,
                'sleeping_habits': sleeping_habits,
                'guest_preferences': guest_preferences,
                'has_pet': has_pet,
                'bio': bio
            }
            save_users(users)
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
            'age': age,
            'gender': gender,
            'smoking_habits': smoking_habits,
            'sleeping_habits': sleeping_habits,
            'guest_preferences': guest_preferences,
            'has_pet': has_pet,
            'bio': bio
        })
        save_users(users)
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
        # Your existing code for apartment search
        pass  # Replace with your existing apartment code

    elif st.session_state.conversation_type == "roommate":
        # Your existing code for roommate search
        pass  # Replace with your existing roommate code

    elif st.session_state.conversation_type == "tech Support":
        # Your existing code for tech support
        pass  # Replace with your existing tech support code

else:
    st.write("Please log in to use the application.")
