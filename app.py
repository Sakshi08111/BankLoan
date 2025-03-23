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
                education VARCHAR(15
