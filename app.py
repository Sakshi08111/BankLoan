import streamlit as st
import numpy as np
import pickle
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import traceback
from datetime import datetime

# Database Connection
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
            st.success("Connected to MySQL successfully!")
            return connection
    except Error as e:
        st.error(f"MySQL Connection Error: {e}")
        return None

# Load Model
def load_model():
    try:
        possible_paths = [
            "build.pkl",
            os.path.join(os.path.dirname(__file__), "build.pkl"),
            r"C:\Users\A2Z\Desktop\Cloud\build.pkl"
        ]
        
        for model_path in possible_paths:
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    st.success(f"Model loaded from {model_path}")
                    return model
                except Exception as e:
                    st.warning(f"Error loading {model_path}: {e}")
        
        st.error("Model file not found in any of these locations:\n" + "\n".join(possible_paths))
        return None
        
    except Exception as e:
        st.error(f"Model loading failed: {e}\n{traceback.format_exc()}")
        return None

# Data Encoding
def encode_data(gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth):
    gender = 1 if gender == 'Male' else 0
    married = 1 if married == 'Yes' else 0
    education = 1 if education == 'Graduate' else 0
    self_employed = 1 if self_employed == 'Yes' else 0
    previous_loan_taken = 1 if previous_loan_taken == 'Yes' else 0

    property_area_mapping = {'Urban': 2, 'Semiurban': 1, 'Rural': 0}
    customer_bandwidth_mapping = {'Low': 0, 'Medium': 1, 'High': 2}
    
    property_area = property_area_mapping[property_area]
    customer_bandwidth = customer_bandwidth_mapping[customer_bandwidth]
    
    return gender, married, education, self_employed, previous_loan_taken, property_area, customer_bandwidth

# Database Operations
def save_to_db(data):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO loan_applications 
                (customer_age, family_member, income, loan_amount, cibil_score, tenure, 
                 gender, married, education, self_employed, previous_loan_taken, 
                 property_area, customer_bandwith, prediction, submission_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, data)
            conn.commit()
            return True
        except Error as e:
            st.error(f"Database Error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def fetch_recent_applications(limit=5):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM loan_applications ORDER BY submission_date DESC LIMIT {limit}")
            return cursor.fetchall()
        except Error as e:
            st.error(f"Fetch Error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

# Streamlit UI
st.title('Loan Approval Prediction')
st.write('Enter the details below to check your loan approval status.')

# Input Form
with st.form("loan_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        customer_age = st.number_input('Customer Age', min_value=18, max_value=100, value=30)
        income = st.number_input('Income', min_value=0.0, value=5000.0, step=100.0)
        loan_amount = st.number_input('Loan Amount', min_value=0.0, value=10000.0, step=100.0)
        tenure = st.number_input('Tenure (months)', min_value=6, max_value=120, value=12, step=6)
        gender = st.selectbox('Gender', ['Male', 'Female'])
        education = st.selectbox('Education', ['Graduate', 'Not Graduate'])
        property_area = st.selectbox('Property Area', ['Urban', 'Semiurban', 'Rural'])
        
    with col2:
        family_member = st.number_input('Family Members', min_value=0, max_value=10, value=1)
        cibil_score = st.number_input('Cibil Score', min_value=300, max_value=900, value=700)
        married = st.selectbox('Married', ['Yes', 'No'])
        self_employed = st.selectbox('Self Employed', ['Yes', 'No'])
        previous_loan_taken = st.selectbox('Previous Loan Taken', ['Yes', 'No'])
        customer_bandwidth = st.selectbox('Customer Bandwidth', ['Low', 'Medium', 'High'])
    
    submitted = st.form_submit_button("Predict Loan Approval")

# Prediction Logic
if submitted:
    model = load_model()
    if model:
        try:
            # Encode categorical data
            encoded_data = encode_data(gender, married, education, self_employed, 
                                     previous_loan_taken, property_area, customer_bandwidth)
            
            # Prepare features for prediction
            features = pd.DataFrame([[customer_age, family_member, income, loan_amount, 
                                    cibil_score, tenure] + list(encoded_data)],
                                  columns=['Age', 'Dependents', 'ApplicantIncome', 'LoanAmount', 
                                           'Cibil_Score', 'Tenure', 'Gender', 'Married', 
                                           'Education', 'Self_Employed', 'Previous_Loan_Taken', 
                                           'Property_Area', 'Customer_Bandwith'])
            
            # Make prediction
            prediction = model.predict(features)
            result = 'Approved' if prediction[0] == 0 else 'Rejected'
            
            # Display result
            if prediction[0] == 0:
                st.success("Loan Approved!")
            else:
                st.error("Loan Rejected!")
            
            # Save to database
            db_data = (customer_age, family_member, income, loan_amount, cibil_score, tenure,
                      gender, married, education, self_employed, previous_loan_taken,
                      property_area, customer_bandwidth, result, datetime.now())
            
            if save_to_db(db_data):
                st.success("Application saved to database!")
            else:
                st.warning("Application could not be saved to database")
                
        except Exception as e:
            st.error(f"Prediction Error: {e}\n{traceback.format_exc()}")

# Display Recent Applications
if st.sidebar.checkbox("Show Recent Applications"):
    recent_apps = fetch_recent_applications()
    if recent_apps:
        st.sidebar.subheader("Recent Loan Applications")
        st.sidebar.dataframe(pd.DataFrame(recent_apps))
    else:
        st.sidebar.warning("No applications found in database")

# Database Verification (Admin Section)
if st.sidebar.checkbox("Database Admin"):
    st.sidebar.subheader("Database Verification")
    if st.sidebar.button("Check Connection"):
        if create_connection():
            st.sidebar.success("Database connection working!")
            
    if st.sidebar.button("Count Records"):
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM loan_applications")
            count = cursor.fetchone()[0]
            st.sidebar.info(f"Total applications: {count}")
            cursor.close()
            conn.close()
