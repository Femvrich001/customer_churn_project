import pandas as pd
from sqlalchemy import create_engine

# ================================
# ✅ 1. Load cleaned dataset
# ================================
csv_path = r"C:\Users\Olajide FemVrich\Desktop\Just DATA\SQL\customer_churn_project\data\cleaned\Telco-Customer-Churn-cleaned.csv"
df = pd.read_csv(csv_path)

# ================================
# ✅ 2. Clean BOOLEAN columns (Yes/No → 1/0)
# ================================
bool_cols = ["Partner", "Dependents", "PhoneService", "PaperlessBilling"]

for col in bool_cols:
    df[col] = df[col].map({"Yes": 1, "No": 0})

# SeniorCitizen is already 0/1 in some datasets, but yours has Yes/No → convert too
df["SeniorCitizen"] = df["SeniorCitizen"].map({"Yes": 1, "No": 0})

# ================================
# ✅ 3. Normalize “No phone/internet service” → “No”
# ================================
replace_cols = ["MultipleLines", "OnlineSecurity", "OnlineBackup", 
                "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]

for col in replace_cols:
    df[col] = df[col].replace({"No phone service": "No", "No internet service": "No"})

# ================================
# ✅ 4. Fix TotalCharges (sometimes blank → convert to numeric)
# ================================
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)

# ================================
# ✅ 5. Split into 4 tables
# ================================
customers_df = df[[
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure"
]].copy()
customers_df.rename(columns={
    "customerID": "customer_id",
    "SeniorCitizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents"
}, inplace=True)

services_df = df[[
    "customerID", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies"
]].copy()
services_df.rename(columns={
    "customerID": "customer_id",
    "PhoneService": "phone_service",
    "MultipleLines": "multiple_lines",
    "InternetService": "internet_service",
    "OnlineSecurity": "online_security",
    "OnlineBackup": "online_backup",
    "DeviceProtection": "device_protection",
    "TechSupport": "tech_support",
    "StreamingTV": "streaming_tv",
    "StreamingMovies": "streaming_movies"
}, inplace=True)

billing_df = df[[
    "customerID", "Contract", "PaperlessBilling", "PaymentMethod",
    "MonthlyCharges", "TotalCharges"
]].copy()
billing_df.rename(columns={
    "customerID": "customer_id",
    "Contract": "contract",
    "PaperlessBilling": "paperless_billing",
    "PaymentMethod": "payment_method",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges": "total_charges"
}, inplace=True)

churn_df = df[[
    "customerID", "Churn"
]].copy()
churn_df.rename(columns={
    "customerID": "customer_id",
    "Churn": "churn_status"
}, inplace=True)
churn_df["churn_date"] = None  # You don’t have churn date, so leave it NULL

# ================================
# ✅ 6. Connect to Railway MySQL
# ================================
DB_USER = "root"
DB_PASS = "lqgaAyqkUerUyxfnzxqtbKZySsQTqgeQ"   # <-- YOUR Railway password
DB_HOST = "tramway.proxy.rlwy.net"            # <-- YOUR Railway host
DB_PORT = "37766"                             # <-- YOUR Railway port
DB_NAME = "railway"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ================================
# ✅ 7. Load into MySQL (append mode)
# ================================
print("⏳ Inserting into customers...")
customers_df.to_sql("customers", con=engine, if_exists="append", index=False)

print("⏳ Inserting into services...")
services_df.to_sql("services", con=engine, if_exists="append", index=False)

print("⏳ Inserting into billing...")
billing_df.to_sql("billing", con=engine, if_exists="append", index=False)

print("⏳ Inserting into churn_outcomes...")
churn_df.to_sql("churn_outcomes", con=engine, if_exists="append", index=False)

print("✅ All tables inserted successfully!")
