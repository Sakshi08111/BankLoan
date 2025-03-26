import streamlit as st
import numpy as np
import pickle
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import traceback


    

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='bankloan'
        )
        if connection.is_connected():
            print("Connected to MySQL")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

connection = create_connection()

# Load the model safely
# Load the model safely - use this instead of your current code
try:
    # Try to find the model in several possible locations
    possible_paths = [
        "build.pkl",  # Same directory
        os.path.join(os.path.dirname(__file__), "build.pkl"),  # Next to script
        r"C:\Users\A2Z\Desktop\Cloud\build.pkl"  # Your original path
    ]
    
    model = None
    for model_path in possible_paths:
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                st.success(f"Model loaded successfully from {model_path}")
                break
            except Exception as e:
                st.warning(f"Found model at {model_path} but couldn't load: {e}")
    
    if model is None:
        st.error("Could not find or load model file in any of these locations:\n" + 
                "\n".join(possible_paths))
        st.stop()
        
except Exception as e:
    st.error(f"Error loading model: {e}\n{traceback.format_exc()}")
    st.stop()
    
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
            connection = create_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO loan_applications 
                    (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth, prediction)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth, result))
                connection.commit()
                st.success("Data saved to database.")
            else:
                st.error("Failed to save data. Database connection not established.")
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    else:
        st.error("Model is not loaded. Please check the model file.")
