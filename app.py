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

            # Preprocess categorical data if required (e.g., encoding)
            input_data['Gender'] = input_data['Gender'].map({'Male': 0, 'Female': 1})
            input_data['Married'] = input_data['Married'].map({'Yes': 1, 'No': 0})
            input_data['Self_Employed'] = input_data['Self_Employed'].map({'Yes': 1, 'No': 0})
            input_data['Previous_Loan_Taken'] = input_data['Previous_Loan_Taken'].map({'Yes': 1, 'No': 0})
            input_data['Property_Area'] = input_data['Property_Area'].map({'Urban': 2, 'Semiurban': 1, 'Rural': 0})
            input_data['Customer_Bandwith'] = input_data['Customer_Bandwith'].map({'Low': 0, 'Medium': 1, 'High': 2})

            # Debug: Print input data
            st.write("Input Data:")
            st.write(input_data)

            # Predict the outcome
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
                """, (
                    customer_age, family_member, income, loan_amount, cibil_score, tenure,
                    'Male' if gender == 0 else 'Female',
                    'Yes' if married == 1 else 'No',
                    education, 'Yes' if self_employed == 1 else 'No',
                    'Yes' if previous_loan_taken == 1 else 'No',
                    'Urban' if property_area == 2 else 'Semiurban' if property_area == 1 else 'Rural',
                    'Low' if customer_bandwidth == 0 else 'Medium' if customer_bandwidth == 1 else 'High',
                    result
                ))
                conn.commit()
                st.success("Data saved to database.")
                cursor.close()
                conn.close()
        except Exception as e:
            st.error(f"An error occurred: {e}\n{traceback.format_exc()}")
    else:
        st.error("Model is not loaded. Please check the model file.")
