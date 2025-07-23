import os
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

def get_mysql_connection():
    """Get MySQL connection either from Streamlit secrets (Cloud) or .env (Local)."""

    # ✅ Check if running on Streamlit Cloud with secrets
    has_secrets = hasattr(st, "secrets") and st.secrets and "mysql" in st.secrets

    if has_secrets:
        db_config = st.secrets["mysql"]
        host = db_config.get("host")
        port = db_config.get("port")
        user = db_config.get("user")
        password = db_config.get("password")
        database = db_config.get("database")
    else:
        # ✅ Fallback to local .env
        load_dotenv()
        host = os.getenv("MYSQL_HOST", "localhost")
        port = os.getenv("MYSQL_PORT", "3306")
        user = os.getenv("MYSQL_USER", "root")
        password = os.getenv("MYSQL_PASSWORD", "")
        database = os.getenv("MYSQL_DATABASE", "customer_churn")

    connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(connection_url)
        return engine.connect()
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None
