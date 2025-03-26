import streamlit as st
import numpy as np
import pickle
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import traceback
from datetime import datetime

# Database Connection with improved error handling
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='bankloan',
            connect_timeout=5  # Add timeout to prevent hanging
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"MySQL Connection Error: {e}")
        # More specific error messages
        if "Access denied" in str(e):
            st.error("Authentication failed. Check username/password.")
        elif "Can't connect" in str(e):
            st.error("Cannot connect to MySQL server. Check if MySQL is running.")
        return None

# Load Model with better path handling
def load_model():
    model = None
    try:
        # More robust path checking
        possible_paths = [
            os.path.join(os.getcwd(), "build.pkl"),
            os.path.join(os.path.dirname(__file__), "build.pkl"),
            r"C:\Users\A2Z\Desktop\Cloud\build.pkl",
            "build.pkl"  # Check current directory last
        ]
        
        for model_path in possible_paths:
            try:
                if os.path.exists(model_path):
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    st.success(f"Model loaded successfully from {model_path}")
                    return model
            except Exception as e:
                st.warning(f"Found model at {model_path} but couldn't load: {str(e)[:100]}...")
                continue
        
        st.error("Model file not found in any of these locations:\n" + 
                "\n".join(f"- {p}" for p in possible_paths))
        return None
        
    except Exception as e:
        st.error(f"Critical error loading model: {str(e)[:200]}")
        st.text(traceback.format_exc())  # Show full traceback in app
        return None

# Data Encoding - unchanged (works well)
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

# Improved Database Operations with connection pooling
connection_pool = None

def init_connection_pool():
    global connection_pool
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="loan_pool",
            pool_size=5,
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='bankloan'
        )
        st.success("Connection pool created successfully")
    except Error as e:
        st.error(f"Failed to create connection pool: {e}")

# Initialize the pool when the app starts
if 'connection_pool' not in globals():
    init_connection_pool()

def save_to_db(data):
    try:
        if connection_pool:
            conn = connection_pool.get_connection()
            cursor = conn.cursor()
            
            # Verify table exists
            cursor.execute("SHOW TABLES LIKE 'loan_applications'")
            if not cursor.fetchone():
                st.error("Error: 'loan_applications' table doesn't exist!")
                return False
                
            query = """
                INSERT INTO loan_applications 
                (customer_age, family_member, income, loan_amount, cibil_score, tenure, 
                 gender, married, education, self_employed, previous_loan_taken, 
                 property_area, customer_bandwith, prediction, submission_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, data)
            conn.commit()
            st.success("✅ Data saved to database successfully!")
            return True
        else:
            st.error("No database connection available")
            return False
    except Error as e:
        st.error(f"Database Error: {e}")
        if conn.is_connected():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def fetch_recent_applications(limit=5):
    try:
        if connection_pool:
            conn = connection_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if table exists first
            cursor.execute("SHOW TABLES LIKE 'loan_applications'")
            if not cursor.fetchone():
                st.warning("No 'loan_applications' table found")
                return None
                
            cursor.execute(f"""
                SELECT customer_age, gender, income, loan_amount, prediction, submission_date
                FROM loan_applications 
                ORDER BY submission_date DESC 
                LIMIT {limit}
            """)
            return cursor.fetchall()
        else:
            st.error("No database connection available")
            return None
    except Error as e:
        st.error(f"Fetch Error: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# Streamlit UI with better organization
st.set_page_config(page_title="Loan Approval Predictor", layout="wide")
st.title('🏦 Loan Approval Prediction System')
st.write('Enter applicant details to check loan approval status.')

# Input Form with validation
with st.form("loan_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Details")
        customer_age = st.number_input('Age', min_value=18, max_value=100, value=30, help="Applicant age in years")
        gender = st.selectbox('Gender', ['Male', 'Female'])
        married = st.selectbox('Marital Status', ['Yes', 'No'])
        family_member = st.number_input('Dependents', min_value=0, max_value=10, value=1, 
                                      help="Number of family dependents")
        
    with col2:
        st.subheader("Financial Details")
        income = st.number_input('Monthly Income ($)', min_value=0.0, value=5000.0, step=100.0)
        loan_amount = st.number_input('Loan Amount ($)', min_value=0.0, value=10000.0, step=100.0)
        cibil_score = st.slider('Credit Score', min_value=300, max_value=900, value=700)
        tenure = st.selectbox('Loan Term (months)', options=[6, 12, 24, 36, 48, 60], index=1)
    
    st.subheader("Additional Information")
    col3, col4 = st.columns(2)
    with col3:
        education = st.selectbox('Education', ['Graduate', 'Not Graduate'])
        self_employed = st.selectbox('Employment Type', ['Yes', 'No'], 
                                   help="Is the applicant self-employed?")
    with col4:
        previous_loan_taken = st.selectbox('Previous Loans', ['Yes', 'No'])
        property_area = st.selectbox('Property Location', ['Urban', 'Semiurban', 'Rural'])
        customer_bandwidth = st.selectbox('Income Band', ['Low', 'Medium', 'High'])
    
    submitted = st.form_submit_button("Check Approval Status")

# Prediction Logic with improved flow
if submitted:
    with st.spinner("Processing your application..."):
        model = load_model()
        if model:
            try:
                # Encode data
                encoded_data = encode_data(gender, married, education, self_employed, 
                                         previous_loan_taken, property_area, customer_bandwidth)
                
                # Create feature DataFrame
                features = pd.DataFrame([[customer_age, family_member, income, loan_amount, 
                                        cibil_score, tenure] + list(encoded_data)],
                                      columns=['Age', 'Dependents', 'ApplicantIncome', 'LoanAmount', 
                                               'Cibil_Score', 'Tenure', 'Gender', 'Married', 
                                               'Education', 'Self_Employed', 'Previous_Loan_Taken', 
                                               'Property_Area', 'Customer_Bandwith'])
                
                # Make prediction
                prediction = model.predict(features)[0]
                result = 'Approved' if prediction == 0 else 'Rejected'
                
                # Show result with emoji
                if prediction == 0:
                    st.balloons()
                    st.success("🎉 Loan Approved!")
                else:
                    st.error("❌ Loan Rejected")
                
                # Prepare data for database
                db_data = (customer_age, family_member, income, loan_amount, cibil_score, tenure,
                          gender, married, education, self_employed, previous_loan_taken,
                          property_area, customer_bandwidth, result, datetime.now())
                
                # Save to database
                if not save_to_db(db_data):
                    st.warning("Note: Application details were not saved to database")
                
                # Show feature importance if available
                if hasattr(model, 'feature_importances_'):
                    st.subheader("Key Decision Factors")
                    feat_importance = pd.DataFrame({
                        'Feature': features.columns,
                        'Importance': model.feature_importances_
                    }).sort_values('Importance', ascending=False)
                    st.bar_chart(feat_importance.set_index('Feature'))
                
            except Exception as e:
                st.error(f"An error occurred during prediction: {str(e)[:200]}")
                st.text(traceback.format_exc())

# Sidebar with enhanced admin tools
with st.sidebar:
    st.header("Database Tools")
    
    if st.button("🔄 Check Database Connection"):
        conn = None
        try:
            conn = create_connection()
            if conn:
                st.success("✅ Successfully connected to MySQL!")
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                st.info(f"MySQL Server Version: {version}")
                cursor.close()
        except Error as e:
            st.error(f"Connection failed: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    if st.button("📊 Show Recent Applications"):
        with st.spinner("Loading recent applications..."):
            recent_apps = fetch_recent_applications(10)
            if recent_apps:
                st.subheader("Last 10 Applications")
                df = pd.DataFrame(recent_apps)
                st.dataframe(df.style.highlight_max(axis=0))
            else:
                st.warning("No applications found in database")
    
    if st.button("🧹 Create Table (Admin)"):
        conn = None
        try:
            conn = create_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS loan_applications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        customer_age INT,
                        family_member INT,
                        income DECIMAL(12,2),
                        loan_amount DECIMAL(12,2),
                        cibil_score INT,
                        tenure INT,
                        gender VARCHAR(10),
                        married VARCHAR(3),
                        education VARCHAR(15),
                        self_employed VARCHAR(3),
                        previous_loan_taken VARCHAR(3),
                        property_area VARCHAR(10),
                        customer_bandwith VARCHAR(10),
                        prediction VARCHAR(10),
                        submission_date DATETIME
                    )
                """)
                conn.commit()
                st.success("Table 'loan_applications' created successfully!")
        except Error as e:
            st.error(f"Error creating table: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()

# Add footer
st.markdown("---")
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f1f1f1;
    color: black;
    text-align: center;
    padding: 10px;
}
</style>
<div class="footer">
    <p>Loan Approval Prediction System © 2023 | Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)
