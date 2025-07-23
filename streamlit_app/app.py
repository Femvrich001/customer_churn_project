import streamlit as st
import pandas as pd
import plotly.express as px
from utils.connection_utils import get_mysql_connection

# --- Streamlit Page Settings ---
st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

# --- Title ---
st.title("📊 Customer Churn Analysis Dashboard")

# --- Cached DB Loader ---
@st.cache_data
def load_data():
    """Load and merge all churn-related tables"""
    try:
        conn = get_mysql_connection()
        customers = pd.read_sql("SELECT * FROM customers", conn)
        services = pd.read_sql("SELECT * FROM services", conn)
        billing = pd.read_sql("SELECT * FROM billing", conn)
        churn = pd.read_sql("SELECT * FROM churn_outcomes", conn)
        conn.dispose()

        # Merge all tables
        df = (
            customers
            .merge(services, on="customer_id", how="left")
            .merge(billing, on="customer_id", how="left")
            .merge(churn, on="customer_id", how="left")
        )
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()

# Load data
with st.spinner("Loading data from database..."):
    df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

with st.sidebar.form("filter_form"):
    gender_filter = st.multiselect(
        "Gender",
        options=df["gender"].dropna().unique(),
        default=df["gender"].dropna().unique()
    )

    contract_filter = st.multiselect(
        "Contract Type",
        options=df["contract"].dropna().unique(),
        default=df["contract"].dropna().unique()
    )

    churn_filter = st.multiselect(
        "Churn Status",
        options=df["churn_status"].dropna().unique(),
        default=df["churn_status"].dropna().unique()
    )

    st.markdown("### 🔍 Advanced Filters")

    tenure_filter = st.slider(
        "Tenure (months)",
        min_value=int(df['tenure'].min()),
        max_value=int(df['tenure'].max()),
        value=(0, int(df['tenure'].max()))
    )

    revenue_filter = st.slider(
        "Monthly Charges Range",
        min_value=float(df['monthly_charges'].min()),
        max_value=float(df['monthly_charges'].max()),
        value=(0.0, float(df['monthly_charges'].max()))
    )

    high_risk_toggle = st.checkbox("Show Only High-Risk Customers")

    apply_filters = st.form_submit_button("🚀 Apply Filters")

st.sidebar.markdown("## ℹ️ About")
st.sidebar.info("""
This dashboard provides strategic insights into customer churn patterns.
- **Red metrics** indicate risk areas  
- **Green metrics** show positive trends  
- Click charts for detailed views  
""")

# --- Apply Filters ---
if apply_filters or not st.session_state.get('filters_applied', False):
    st.session_state.filters_applied = True

    df_filtered = df[
        (df["gender"].isin(gender_filter)) &
        (df["contract"].isin(contract_filter)) &
        (df["churn_status"].isin(churn_filter)) &
        (df["tenure"].between(tenure_filter[0], tenure_filter[1])) &
        (df["monthly_charges"].between(revenue_filter[0], revenue_filter[1]))
    ]

    if high_risk_toggle:
        df_filtered = df_filtered[
            (df_filtered['tenure'] < 6) & (df_filtered['churn_status'] == 'Yes')
        ]

    # --- Executive Summary ---
    st.markdown("## 🎯 Executive Summary")

    total_customers = df_filtered["customer_id"].nunique()
    churned_customers = (df_filtered["churn_status"] == "Yes").sum()
    churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0
    revenue_at_risk = df_filtered[df_filtered['churn_status']=='Yes']['monthly_charges'].sum() * 12
    high_risk_count = df_filtered[(df_filtered['tenure']<3) & (df_filtered['churn_status']=='Yes')].shape[0]
    avg_tenure = df_filtered['tenure'].mean()
    premium_count = df_filtered[df_filtered['monthly_charges'] > df['monthly_charges'].median()].shape[0]
    loyal_count = df_filtered[df_filtered['tenure']>24].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", f"{total_customers:,}", help="Total customers matching filters")
    col1.metric("Avg Tenure", f"{avg_tenure:.1f} months" if not pd.isna(avg_tenure) else "N/A")

    col2.metric("Churn Rate", f"{churn_rate:.1f}%" if total_customers > 0 else "0%",
                delta=f"-{churned_customers} customers" if churned_customers > 0 else "")
    col2.metric("High-Risk Customers", f"{high_risk_count}",
                delta=f"{(high_risk_count/total_customers*100):.1f}%" if total_customers > 0 else "0%")

    col3.metric("Revenue at Risk", f"${revenue_at_risk:,.0f}" if not pd.isna(revenue_at_risk) else "$0")
    col3.metric("Premium Customers", f"{premium_count}",
                delta=f"{(premium_count/total_customers*100):.1f}%" if total_customers > 0 else "0%")

    col4.metric("Loyal Customers", f"{loyal_count}",
                delta=f"{(loyal_count/total_customers*100):.1f}%" if total_customers > 0 else "0%",
                delta_color="inverse")

    if total_customers > 0:
        insight = "👍 Healthy retention" if churn_rate < 10 else "⚠️ High churn risk"
        st.markdown(f"**Quick Insight:** {insight}")

    st.divider()

    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["Churn Analysis", "Revenue Impact", "CLV Analysis", "Raw Data"])

    # ✅ TAB 1: Churn Analysis
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Churn by Gender")
            fig_gender = px.pie(df_filtered, names='gender', color='churn_status',
                                color_discrete_map={'Yes':'red', 'No':'green'})
            st.plotly_chart(fig_gender, use_container_width=True)

        with col_b:
            st.markdown("#### Churn by Contract")
            fig_contract = px.histogram(df_filtered, x='contract', color='churn_status',
                                        barmode='group', text_auto=True)
            st.plotly_chart(fig_contract, use_container_width=True)

        st.markdown("### 🔥 Top Churn Predictors")
        churn_numeric = df_filtered['churn_status'].map({'Yes':1, 'No':0})
        corr_matrix = df_filtered[['tenure', 'monthly_charges', 'senior_citizen']].corrwith(churn_numeric)
        fig_corr = px.bar(corr_matrix, orientation='h', color=corr_matrix,
                          color_continuous_scale='RdBu', range_color=[-1,1])
        st.plotly_chart(fig_corr, use_container_width=True)

    # ✅ TAB 2: Revenue Impact
    with tab2:
        st.markdown("### 💰 Revenue Impact Analysis")

        # Revenue Funnel
        df_funnel = df_filtered.groupby('churn_status')['monthly_charges'].sum().reset_index()
        fig_funnel = px.funnel(df_funnel, x='monthly_charges', y='churn_status')
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Revenue by Contract (from filtered df, no SQL needed)
        df_rev = df_filtered.groupby('contract').agg(
            total_revenue=('monthly_charges','sum'),
            churned_revenue=('monthly_charges', lambda x: x[df_filtered['churn_status']=='Yes'].sum())
        ).reset_index()
        fig_rev = px.bar(df_rev, x='contract', y=['total_revenue', 'churned_revenue'],
                         barmode='group', text_auto='.2s')
        st.plotly_chart(fig_rev, use_container_width=True)

    # ✅ TAB 3: CLV Analysis
    with tab3:
        st.markdown("### 📈 Customer Lifetime Value")
        df_clv = df_filtered.groupby('contract').agg(
            avg_clv=('total_charges','mean'),
            customers=('customer_id','count'),
            churned=('churn_status', lambda x: (x=='Yes').sum())
        ).reset_index()
        fig_clv = px.scatter(df_clv, x='avg_clv', y='customers', size='churned',
                             color='contract', hover_name='contract',
                             labels={'avg_clv':'Avg Lifetime Value ($)'})
        st.plotly_chart(fig_clv, use_container_width=True)
        st.dataframe(df_clv.style.format({'avg_clv': '${:,.2f}'}))

    # ✅ TAB 4: Raw Data
    with tab4:
        st.markdown("### 🔎 Filtered Data Preview")
        st.dataframe(df_filtered)
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", data=csv,
                           file_name="churn_analysis.csv", mime='text/csv')

else:
    st.info("ℹ️ Adjust filters and click 'Apply Filters' to update the dashboard.")
