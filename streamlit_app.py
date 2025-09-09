import streamlit as st
from supabase import create_client, Client
from supabase_client import get_client
from utils import org_header

st.set_page_config(page_title="PigFarm Manager", page_icon="🐖", layout="wide")

sb: Client = get_client()

st.title("🐖 PigFarm Manager")
st.info("For admins/managers: enable MFA in Supabase Auth settings for stronger security.")
tab_login, tab_about = st.tabs(["Sign In / Sign Up", "About"])

with tab_login:
    mode = st.radio("Mode", ["Sign In", "Sign Up"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Sign In":
        if st.button("Sign In"):
            try:
                auth = sb.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["sb_session"] = auth.session
                st.success("Signed in! Use the sidebar to navigate pages.")
            except Exception as e:
                st.error(f"Sign-in failed: {e}")
    else:
        org_name = st.text_input("Your Organization/Farm Name")
        if st.button("Create Account"):
            try:
                auth = sb.auth.sign_up({"email": email, "password": password})
                st.session_state["sb_session"] = auth.session
                st.info("Account created. Ask your admin to assign you to an org.")

                # Note: In production, map user->org using a secure Edge Function or admin UI.
                st.warning("Admin must link this user to an org in Admin page.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

with tab_about:
    st.markdown(
        """
        **Secure, multi-user pig farm records** with org-based isolation and roles.
        Use the sidebar to access Pigs, Feed Logs, Invoices, and Admin (for org & roles mapping).
        """
    )
