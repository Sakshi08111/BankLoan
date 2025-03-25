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
            create_table(connection)
            return connection
    except mysql.connector.Error as e:
        st.error(f"Database connection error: {e}")
        return None

def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute('''
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
        ''')
        connection.commit()
        st.success("Table 'loan_applications' checked/created successfully.")
    except mysql.connector.Error as e:
        st.error(f"Error creating table: {e}")
    finally:
        cursor.close()

def main():
    st.title("Loan Approval Prediction - Database Management")
    connection = create_connection()
    
    if connection:
        st.write("You can now interact with your database!")
        # Example - Additional options can be added later
        if st.button("Check Connection Again"):
            st.success("Database connection is active.")
# Load the model safely
model_path = os.path.join(os.path.dirname(__file__), 'build.pkl')  # Relative path

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
            # Match features with training data
            input_data = pd.DataFrame([[
                customer_age, family_member, income, loan_amount, cibil_score, tenure,
                gender, married, education, self_employed, previous_loan_taken,
                property_area, customer_bandwidth
            ]], columns=[
                'Age', 'Dependents', 'ApplicantIncome', 'LoanAmount', 'Cibil_Score', 'Tenure',
                'Gender', 'Married', 'Education', 'Self_Employed', 'Previous_Loan_Taken',
                'Property_Area', 'Customer_Bandwith'  # Match feature names from training data
            ])

            # Preprocess categorical data (encode into numerical values)
            input_data['Gender'] = input_data['Gender'].map({'Male': 0, 'Female': 1})
            input_data['Married'] = input_data['Married'].map({'Yes': 1, 'No': 0})
            input_data['Education'] = input_data['Education'].map({'Graduate': 1, 'Not Graduate': 0})
            input_data['Self_Employed'] = input_data['Self_Employed'].map({'Yes': 1, 'No': 0})
            input_data['Previous_Loan_Taken'] = input_data['Previous_Loan_Taken'].map({'Yes': 1, 'No': 0})
            input_data['Property_Area'] = input_data['Property_Area'].map({'Urban': 2, 'Semiurban': 1, 'Rural': 0})
            input_data['Customer_Bandwith'] = input_data['Customer_Bandwith'].map({'Low': 0, 'Medium': 1, 'High': 2})

            # Predict the outcome
            prediction = model.predict(input_data)
            result = 'Loan Approved' if prediction[0] == 0 else 'Loan Rejected'

            # Display the result
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
                    (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender, 
                     married, education, self_employed, previous_loan_taken, property_area, 
                     customer_bandwidth, prediction)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_age, family_member, income, loan_amount, cibil_score, tenure, gender,
                      married, education, self_employed, previous_loan_taken, property_area,
                      customer_bandwidth, result))
                conn.commit()
                st.success("User data stored successfully.")
                cursor.close()
                conn.close()
        except Exception as e:
            st.error(f"An error occurred: {e}\n{traceback.format_exc()}")
    else:
        st.error("Model is not loaded. Please check the model file.")
