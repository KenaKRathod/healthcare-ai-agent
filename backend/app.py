import streamlit as st
from database import add_medication, get_medications
from chatbot import health_chatbot

st.title("Healthcare AI Agent")

st.header("Medication Reminder")

medicine_name = st.text_input("Enter Medicine Name")
medicine_time = st.time_input("Select Time")

if st.button("Add Medication"):
    add_medication(medicine_name, str(medicine_time))
    st.success("Medication added successfully!")

st.subheader("Scheduled Medications")

medications = get_medications()

for med in medications:
    st.write(f"{med[1]} at {med[2]}")

st.header("Health Chatbot")

user_input = st.text_input("Ask a health question")

if user_input:
    response = health_chatbot(user_input)
    st.write(response)