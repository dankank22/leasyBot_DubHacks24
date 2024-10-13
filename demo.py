import streamlit as st
import google.generativeai as genai
import pandas as pd
import pydeck as pdk
import json
import os
import time

def load_apartment_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame() 

def load_user_txt(username):
    txt_path = f"txt/{username}.txt"
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # half_length = len(content) // 8
            # trimmed_content = content[:half_length]
            return content
    else:
        return ""
    
def format_profile(user_profile, user_label):
    profile_info = f"""
                    {user_label}'s Profile:
                    - Full Name: {user_profile.get('full_name', 'N/A')}
                    - Age: {user_profile.get('age', 'N/A')}
                    - Gender: {user_profile.get('gender', 'N/A')}
                    - College: {user_profile.get('college', 'N/A')}
                    - Major: {user_profile.get('major', 'N/A')}
                    - School Year: {user_profile.get('school_year', 'N/A')}
                    - Smoking Habits: {user_profile.get('smoking_habits', 'N/A')}
                    - Sleeping Habits: {user_profile.get('sleeping_habits', 'N/A')}
                    - Guest Preferences: {user_profile.get('guest_preferences', 'N/A')}
                    - Has Pet: {'Yes' if user_profile.get('has_pet') else 'No'}
                    - Bio: {user_profile.get('bio', 'N/A')}
                    """
    return profile_info

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

#Sign Up Form
if st.session_state.get('signup_mode'):
    with st.form("signup_form"):
        st.write("**Create a New Account**")
        new_username = st.text_input("Choose a username", key="signup_username")
        new_password = st.text_input("Choose a password", type='password', key="signup_password")
        confirm_password = st.text_input("Confirm password", type='password', key="signup_confirm_password")
        
        # profile info
        full_name = st.text_input("Full Name", key="signup_full_name")
        college = st.text_input("College", key="signup_college")
        school_year = st.selectbox("School Year", options=["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "Other"], key="signup_school_year")
        major = st.text_input("Major", key="signup_major")
        apartment_option = st.text_input("Where have you signed at? (If you have not found an apartment, enter 'Still Searching')", key="signup_apartment")
        age = st.number_input("Age", min_value=18, max_value=100, key="signup_age")
        gender = st.selectbox("Gender", options=["Male", "Female", "Non-binary", "Prefer not to say", "Other"], key="signup_gender")
        smoking_habits = st.checkbox("Do you smoke?", key="signup_smoking")
        sleeping_habits = st.selectbox("Sleeping Habits?", options=["Night owl", "Early bird", "Both"], key="signup_sleeping")
        guest_preferences = st.selectbox("Guest Preferences?", options=["I like having guests over frequently", "I occasionally host people", "No guests"], key="signup_guests")
        has_pet = st.checkbox("Do you have a pet?", key="signup_pet")
        bio = st.text_area("Tell us about yourself", key="signup_bio")

        # .txt file
        txt_file = st.file_uploader("Upload a chat.txt file to automate roommate conversations", type="txt", key="signup_txt_file")

        looking_for_roommate = st.selectbox("Are you looking for a roommate?", options=["Yes", "No"], key="signup_looking_for_roommate")

        if looking_for_roommate == "Yes":
            roommate_smoking = st.checkbox("Roommate can smoke?", key="signup_roommate_smoking")
            roommate_has_pets = st.checkbox("Roommate can have pets?", key="signup_roommate_has_pets")
            roommate_year = st.selectbox("Preferred Year", options=["Any", "Freshman", "Sophomore", "Junior", "Senior", "Other"], key="signup_roommate_year")
            night_person = st.selectbox("Sleeping Habits", options=["Night owl", "Early bird", "Both"], key="signup_night_person")
            gatherings = st.selectbox("Guests?", options=["I like having guests over frequently", "I occasionally host people", "No guests"], key="signup_gatherings")
        
        submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        elif new_username in users:
            st.error("Username already exists! Please choose a different one.")
        elif txt_file is None:
            st.error("Please upload a .txt file.")
        else:
            # save creds
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

            with open(f"txt/{new_username}.txt", "wb") as f:
                f.write(txt_file.getbuffer())

            st.success(f"Account created successfully for {full_name}!")
            st.session_state.signup_mode = False

# Profile Page
if 'username' in st.session_state and st.session_state.get('show_profile', False):
    st.write("## Your Profile")

    current_user = users[st.session_state.username]

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
        save_users(users)
        st.success("Profile updated successfully!")


# Main app logic
if 'username' in st.session_state:
    if st.session_state.conversation_type is None:
        st.write("Hi, how may I assist you today?")
        
    col1, col2, col3 = st.columns(3)
    
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
    
    if st.session_state.conversation_type is not None:
        st.write(f"**Selected Option:** {st.session_state.conversation_type.replace('_', ' ').capitalize()}")
    
    if st.session_state.conversation_type == "apartment":
        st.write("*Please adjust the sliders and options to define your preferences.*")
    
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
            if not filtered_apartments.empty:
                st.write("### Apartments that match your preferences:")
                st.dataframe(filtered_apartments)
                if 'Latitude' in filtered_apartments.columns and 'Longitude' in filtered_apartments.columns:
                    map_data = filtered_apartments[['Latitude', 'Longitude']].dropna()
                    map_data = map_data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'})
                    map_data = map_data.astype({'latitude': 'float', 'longitude': 'float'})
                    if not map_data.empty:
                        layer = pdk.Layer(
                            'ScatterplotLayer',
                            data=map_data,
                            get_position='[longitude, latitude]',
                            get_color='[200, 30, 0, 160]',
                            get_radius=50,
                            pickable=True,
                        )
                        view_state = pdk.ViewState(
                            latitude=map_data['latitude'].mean(),
                            longitude=map_data['longitude'].mean(),
                            zoom=12,  # adjust zoom
                            pitch=0
                        )
                        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
                    else:
                        st.write("No valid coordinates available for the selected apartments.")
                else:
                    st.write("Latitude and Longitude data not found in the filtered results.")
            else:
                st.write("No apartments match your preferences. Try adjusting the filters.")

    elif st.session_state.conversation_type == "roommate":
        st.write("*Finding a roommate based on your preferences...*")

        current_user = users[st.session_state.username]

        # user is looking for a roommate
        if current_user.get('looking_for_roommate') == "Yes":
            # filter matching users
            matching_users = []
            for username, user_data in users.items():
                if username != st.session_state.username and user_data.get('looking_for_roommate') == "Yes":
                    # check if the user fits the criteria
                    count = 0
                    if user_data.get('smoking_habits') == current_user.get('roommate_smoking'):
                        count += 1
                    if user_data.get('has_pet') == current_user.get('roommate_has_pets'):
                        count += 1
                    if user_data.get('school_year') == current_user.get('roommate_year'):
                        count += 1
                    if user_data.get('sleeping_habits') == current_user.get('night_person'):
                        count += 1
                    if user_data.get('guest_preferences') == current_user.get('gatherings'):
                        count += 1

                    if count > 0:
                        matching_users.append((username, count))

            matching_users.sort(key=lambda x: x[1], reverse=True)

            if matching_users:
                for match, count in matching_users:
                    st.write(f"**Username**: {match}, **Matches**: {count}")

                    if st.button(f"Simulate Conversation with {match}"):
                        # Load txt files for both users
                        current_user_text = load_user_txt(st.session_state.username)
                        matched_user_text = load_user_txt(match)
                        current_user_profile = users[st.session_state.username]
                        matched_user_profile = users[match]
                        current_user_info = format_profile(current_user_profile, "User A")
                        matched_user_info = format_profile(matched_user_profile, "User B")
                    
                    # Check if txt files are not empty
                        if not current_user_text:
                            st.error(f"No texting style data found for {st.session_state.username}. Please upload a valid .txt file.")
                            continue
                        if not matched_user_text:
                            st.error(f"No texting style data found for {match}.")
                            continue
                        
                        # Prepare a prompt for the language model
                        prompt = f"""
                                You are to simulate a text conversation between two users (you must use full names, dont use user A and user B) who are texting for the first time to discuss becoming roommates.

                                Base User A's texting style off this text exchange with their friend:
                                {current_user_text}

                                use this profile info for user a:
                                {current_user_info}

                                User B's texting style texting style off this text exchange with their friend:
                                {matched_user_text}

                                use this profile info for user b:
                                {matched_user_info}
                                """
                            # Ensure the API key is set
                        # if "app_key" not in st.session_state:
                        #     app_key = st.text_input("Please enter your Gemini API Key", type='password')
                        #     st.write(app_key)
                        #     if app_key:
                        #         st.write("does api key register?")
                        #         st.session_state.app_key = app_key

                        # Configure the API key
                        if "app_key" in st.session_state:
                            try:
                                genai.configure(api_key=st.session_state.app_key)
                                st.success("API key configured successfully.")
                                model = genai.GenerativeModel("gemini-pro")
                                # time.sleep(30)
                                response = model.generate_content(prompt)
                                st.write(response.text)
                                # Display the conversation
                                # generated_conversation = response.candidates[0]['output']
                                # st.write("Done")
                                # st.write(generated_conversation)
                            except Exception as e:
                                st.error(f"Error generating conversation: {e}")
                            
            else:
                st.write("No matching roommates found based on your preferences.")
        else:
            st.write("It looks like you are not looking for a roommate based on your profile settings.")

    elif st.session_state.conversation_type == "tech Support":
        st.write("*Please provide more details for tech support.*")    
        # # User input for tech support
        # issue_description = st.text_area("Describe the issue you're facing:")
        
        # if st.button("Submit Issue"):
        #     # Append the tech support issue to the chat history
        #     st.session_state.history.append({"role": "user", "parts": [{"text": issue_description}]})
            
        #     # Generate a response from the chatbot based on the input
        #     chat = model.start_chat(history=st.session_state.history)
        #     full_response = chat.send_message(issue_description)
        #     st.session_state.history = chat.history
            
        #     # Display the chatbot's response
        #     for message in full_response:
        #         with st.chat_message("assistant"):
        #             st.markdown(message['text'])

else:
    st.write("Please log in to use the application.")
