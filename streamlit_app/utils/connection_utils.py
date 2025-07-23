import streamlit as st
import os
from sqlalchemy import create_engine

def get_mysql_connection():
    """Create a MySQL connection for Streamlit Cloud or local .env"""

    try:
        # ✅ 1. Try secrets on Streamlit Cloud
        if "mysql" in st.secrets:
            db_config = st.secrets["mysql"]
        else:
            # ✅ 2. Fallback for local .env
            from dotenv import load_dotenv
            load_dotenv()
            db_config = {
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "database": os.getenv("DB_NAME"),
            }

        # ✅ Build connection string
        connection_url = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        return create_engine(connection_url)

    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None
