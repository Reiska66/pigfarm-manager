import streamlit as st
import psycopg2
import psycopg2.extras
from supabase import create_client, Client

# ──────────────────────────────────────────────────────────────────────────────
# Page config
st.set_page_config(page_title="PigFarm Manager", page_icon="🐖")

st.title("🐖 PigFarm Manager")
st.info("For admins/managers: enable MFA in Supabase Auth for stronger security.")

# ──────────────────────────────────────────────────────────────────────────────
# Supabase (Auth) client
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Postgres connection (for roles in users table)
@st.cache_resource(show_spinner=False)
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
    """Return role for this email; if missing, create 'worker' and return it."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select role, is_active from users where email = %s", (email,))
        row = cur.fetchone()
        if row:
            if not row["is_active"]:
                raise PermissionError("Your account is deactivated. Contact admin.")
            return row["role"]
        # create default worker entry if not present
        cur.execute(
            """
            insert into users (email, role, is_active)
            values (%s, 'worker', true)
            on conflict (email) do nothing
            """,
            (email,),
        )
        return "worker"

# ──────────────────────────────────────────────────────────────────────────────
# Auth UI
st.subheader("Sign In / Sign Up")

mode = st.radio("Mode", ["Sign In", "Sign Up"], horizontal=True)
email = st.text_input("Email")
password = st.text_input("Password", type="password")

colA, colB = st.columns(2)
with colA:
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
                st.success("Account created. Confirm via email, then Sign In.")
            except Exception as e:
                st.error(f"Sign up error: {e}")

with colB:
    if st.button("Sign Out"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.success("Signed out.")

# ──────────────────────────────────────────────────────────────────────────────
# Status + navigation hints
role = st.session_state.get("role")
if role:
    st.success(f"You are logged in as **{st.session_state['email']}** · role: **{role}**")
    st.write("Open the sidebar to navigate pages.")
    if role == "admin":
        st.info("Admin: you should now be able to open **Admin · Users** in the sidebar.")
else:
    st.warning("Not logged in yet.")
