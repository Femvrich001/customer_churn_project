import streamlit as st
import pandas as pd
from utils.connection_utils import get_mysql_connection

# --- Streamlit Page Settings ---
st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

# --- Title ---
st.title("📊 Customer Churn Analysis Dashboard")

# --- Sidebar ---
st.sidebar.header("Filters")

st.sidebar.markdown("## ℹ️ About")
st.sidebar.info("""
This dashboard provides interactive insights into customer churn patterns.
- Use filters to explore churn across segments.
- View KPIs and charts dynamically.
""")

# --- DB Connection + Load ---
with st.spinner("Loading data from database..."):
    try:
        engine = get_mysql_connection()  # ✅ returns a SQLAlchemy engine

        customers = pd.read_sql("SELECT * FROM customers", engine)
        services = pd.read_sql("SELECT * FROM services", engine)
        billing = pd.read_sql("SELECT * FROM billing", engine)
        churn = pd.read_sql("SELECT * FROM churn_outcomes", engine)

        # ✅ Correct cleanup for SQLAlchemy
        engine.dispose()

    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()

# --- Merge all tables ---
df = (
    customers
    .merge(services, on="customer_id", how="left")
    .merge(billing, on="customer_id", how="left")
    .merge(churn, on="customer_id", how="left")
)

# --- Sidebar Filters ---
gender_filter = st.sidebar.multiselect(
    "Gender",
    options=df["gender"].dropna().unique(),
    default=df["gender"].dropna().unique()
)

contract_filter = st.sidebar.multiselect(
    "Contract Type",
    options=df["contract"].dropna().unique(),
    default=df["contract"].dropna().unique()
)

churn_filter = st.sidebar.multiselect(
    "Churn Status",
    options=df["churn_status"].dropna().unique(),
    default=df["churn_status"].dropna().unique()
)

# Apply filters
df_filtered = df[
    (df["gender"].isin(gender_filter)) &
    (df["contract"].isin(contract_filter)) &
    (df["churn_status"].isin(churn_filter))
]

# --- KPIs ---
st.markdown("## 🎯 KPIs")
col1, col2, col3, col4 = st.columns(4)

total_customers = df_filtered["customer_id"].nunique()
churn_rate = round(
    (df_filtered["churn_status"] == "Yes").sum() / total_customers * 100, 2
) if total_customers > 0 else 0
avg_tenure = round(df_filtered["tenure"].mean(), 2) if total_customers > 0 else 0
avg_revenue = round(df_filtered["monthly_charges"].mean(), 2) if total_customers > 0 else 0

col1.metric("Total Customers", f"{total_customers}")
col2.metric("Churn Rate (%)", f"{churn_rate}%")
col3.metric("Avg Tenure (months)", f"{avg_tenure}")
col4.metric("Avg Monthly Revenue", f"${avg_revenue}")

st.divider()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Churn Breakdown", "Advanced SQL Analysis", "Data Preview"])

# ✅ Tab 1: Simple Charts
with tab1:
    st.markdown("### 📊 Churn by Gender")
    churn_by_gender = df_filtered.groupby(["gender", "churn_status"])["customer_id"].count().reset_index()
    if churn_by_gender.empty:
        st.warning("⚠️ No data for Churn by Gender. Adjust filters.")
    else:
        st.bar_chart(
            churn_by_gender.pivot(index="gender", columns="churn_status", values="customer_id"),
            use_container_width=True
        )

    st.markdown("### 📊 Churn by Contract Type")
    churn_by_contract = df_filtered.groupby(["contract", "churn_status"])["customer_id"].count().reset_index()
    if churn_by_contract.empty:
        st.warning("⚠️ No data for Churn by Contract. Adjust filters.")
    else:
        st.bar_chart(
            churn_by_contract.pivot(index="contract", columns="churn_status", values="customer_id"),
            use_container_width=True
        )

# ✅ Tab 2: Direct SQL queries
with tab2:
    try:
        engine = get_mysql_connection()

        st.markdown("#### 🔍 Churn Rate by Internet Service")
        q1 = """
        SELECT 
            internet_service,
            COUNT(*) AS total_customers,
            SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
            ROUND(100.0 * SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate
        FROM services s
        JOIN churn_outcomes c ON s.customer_id = c.customer_id
        GROUP BY internet_service
        ORDER BY churn_rate DESC;
        """
        df1 = pd.read_sql(q1, engine)
        st.dataframe(df1)
        if not df1.empty:
            st.bar_chart(df1.set_index("internet_service")["churn_rate"])

        st.markdown("#### 🔍 Monthly Charges vs Churn Segment")
        q2 = """
        SELECT 
            CASE 
                WHEN monthly_charges < 30 THEN 'Low'
                WHEN monthly_charges < 60 THEN 'Medium'
                ELSE 'High'
            END AS charge_segment,
            AVG(tenure) AS avg_tenure,
            AVG(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) AS churn_probability
        FROM billing b
        JOIN customers c ON b.customer_id = c.customer_id
        JOIN churn_outcomes ch ON c.customer_id = ch.customer_id
        GROUP BY charge_segment;
        """
        df2 = pd.read_sql(q2, engine)
        st.dataframe(df2)
        if not df2.empty:
            st.bar_chart(df2.set_index("charge_segment")["churn_probability"])

        st.markdown("#### 🔍 Churn Rate by Payment Method")
        q3 = """
        SELECT 
            payment_method,
            COUNT(*) AS customers,
            SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) AS churned,
            ROUND(SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS churn_rate
        FROM billing b
        JOIN churn_outcomes c ON b.customer_id = c.customer_id
        GROUP BY payment_method
        ORDER BY churn_rate DESC;
        """
        df3 = pd.read_sql(q3, engine)
        st.dataframe(df3)
        if not df3.empty:
            st.bar_chart(df3.set_index("payment_method")["churn_rate"])

        engine.dispose()
    except Exception as e:
        st.error(f"❌ SQL queries failed: {e}")

# ✅ Tab 3: Raw Data Preview
with tab3:
    st.markdown("#### 🔎 Filtered Data Preview")
    st.dataframe(df_filtered)

# --- Download filtered data ---
csv = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data as CSV", data=csv, file_name="filtered_churn_data.csv", mime="text/csv")
