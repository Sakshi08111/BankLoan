import streamlit as st
import numpy as np
import pickle
import mysql.connector
import pandas as pd
import os
import traceback

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456789',
            database='bankloan',
            port=3306
        )
        if connection.is_connected():
            st.success("Connected to the database successfully!")
            cursor = connection.cursor()

            # Create table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_age INT,
                family_member INT,
                income FLOAT,
                loan_amount FLOAT,
                cibil_score INT,
                tenure INT,
                gender VARCHAR(10),
                married VARCHAR(10),
                education VARCHAR(15),
                self_employed VARCHAR(10),
                previous_loan_taken VARCHAR(10),
                property_area VARCHAR(15),
                customer_bandwidth VARCHAR(10),
                prediction VARCHAR(15)
            )
            """)
            connection.commit()
            cursor.close()
            return connection
    except mysql.connector.Error as e:
        st.error(f"Database connection error: {e}")
        return None

# Load the model safely
model_path = os.path.join(os.path.dirname(__file__), 'build.pkl')  # Relative path

# Debug: Print the model path
st.write(f"Model path: {model_path}")

if not os.path.exists(model_path):
    st.error(f"Model file not found at: {model_path}")
    st.stop()  # Stop the app if the model is not found
else:
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        st.success("Model loaded successfully.")
    except pickle.UnpicklingError:
        st.error("Error: The model file might be corrupted or not a valid pickle file.")
        model = None
    except Exception as e:
        st.error(f"Error loading model: {e}\n{traceback.format_exc()}")
        model = None


st.title('Loan Approval Prediction')
st.write('Enter the details below to check your loan approval status.')

# Input fields
customer_age = st.number_input('Customer Age', min_value=18, max_value=100, step=1)
family_member = st.number_input('Family Member', min_value=0, step=1)
income = st.number_input('Income', min_value=0.0, step=100.0)
loan_amount = st.number_input('Loan Amount', min_value=0.0, step=100.0)
cibil_score = st.number_input('Cibil Score', min_value=300, max_value=900, step=1)
tenure = st.number_input('Tenure (in months)', min_value=6, step=6)
gender = st.selectbox('Gender', ['Male', 'Female'])
married = st.selectbox('Married', ['Yes', 'No'])
education = st.selectbox('Education', ['Graduate', 'Not Graduate'])
self_employed = st.selectbox('Self Employed', ['Yes', 'No'])
previous_loan_taken = st.selectbox('Previous Loan Taken', ['Yes', 'No'])
property_area = st.selectbox('Property Area', ['Urban', 'Semiurban', 'Rural'])
customer_bandwidth = st.selectbox('Customer Bandwidth', ['Low', 'Medium', 'High'])

# Predict button
if st.button('Predict'):
    if model is not None:
        try:
            # Map the input data to the feature names expected by the model
            input_data = pd.DataFrame([[customer_age, family_member, income, loan_amount, cibil_score, tenure]], 
                                       columns=['Age', 'Dependents', 'ApplicantIncome', 'LoanAmount', 'Cibil_Score', 'Tenure'])
            prediction = model.predict(input_data)
            result = 'Loan Approved' if prediction[0] == 0 else 'Loan Rejected'

            if prediction[0] == 1:
                st.error('Loan is Rejected')
            else:
                st.success('Loan is Approved')

            # Save to MySQL
            conn = create_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO loan_applications 
                    (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth, prediction)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth, result))
                conn.commit()
                st.success("Data saved to database.")
                cursor.close()
                conn.close()
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Model is not loaded. Please check the model file.")
