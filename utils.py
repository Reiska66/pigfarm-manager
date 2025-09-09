import streamlit as st

def require_session():
    if "sb_session" not in st.session_state or st.session_state["sb_session"] is None:
        st.warning("Please sign in to continue.")
        st.stop()

def get_user_info():
    sess = st.session_state.get("sb_session")
    if not sess:
        return None
    user = sess.user
    return {"id": user.id, "email": user.email}

def org_header(org_name: str = None):
    st.markdown(f"### PigFarm Manager {('- ' + org_name) if org_name else ''}")
import pandas as pd
from io import StringIO

def df_download_button(df: pd.DataFrame, label: str, file_prefix: str):
    if df is None or len(df)==0:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, file_name=f"{file_prefix}.csv", mime="text/csv")
