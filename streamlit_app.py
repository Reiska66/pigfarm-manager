import streamlit as st
from supabase import create_client, Client
from supabase_client import get_client
from utils import org_header

st.set_page_config(page_title="PigFarm Manager", page_icon="🐖", layout="wide")

sb: Client = get_client()

st.title("🐖 PigFarm Manager")
st.info("For admins/managers: enable MFA in Supabase Auth settings for stronger security.")
tab_login, tab_about = st.tabs(["Sign In / Sign Up", "About"])

import streamlit as st
import psycopg2, psycopg2.extras
from supabase import create_client, Client
from supabase_client import get_client  # if you already use this helper

# --- Supabase Auth client ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Postgres connection for roles (users table) ---
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        port=st.secrets.get("DB_PORT", 5432),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

def fetch_or_create_role(email: str) -> str:
    """Return role for this email; if missing, create as worker and return 'worker'."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select role, is_active from users where email = %s", (email,))
        row = cur.fetchone()
        if row:
            if not row["is_active"]:
                raise PermissionError("Your account is deactivated. Contact admin.")
            return row["role"]

        # not found → create default worker entry
        cur.execute(
            """
            insert into users (email, role, is_active)
            values (%s, 'worker', true)
            on conflict (email) do nothing
            """,
            (email,),
        )
        return "worker"

# --- Login UI ---
st.header("Sign In / Sign Up")
mode = st.radio("Mode", ["Sign In", "Sign Up"], horizontal=True)
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if mode == "Sign In":
    if st.button("Sign In"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user = res.user
            if not user:
                st.error("Sign in failed.")
            else:
                role = fetch_or_create_role(user.email)
                st.session_state["email"] = user.email
                st.session_state["role"] = role
                st.success(f"Signed in as {user.email} · role: {role}")
        except Exception as e:
            st.error(f"Sign in error: {e}")

else:
    if st.button("Sign Up"):
        try:
            supabase.auth.sign_up({"email": email, "password": password})
            st.success("Account created. Check your email for confirmation, then Sign In.")
        except Exception as e:
            st.error(f"Sign up error: {e}")
    st.markdown(
        """
        **Secure, multi-user pig farm records** with org-based isolation and roles.
        Use the sidebar to access Pigs, Feed Logs, Invoices, and Admin (for org & roles mapping).
        """
    )
