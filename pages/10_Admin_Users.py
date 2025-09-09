import streamlit as st
import psycopg2
import psycopg2.extras

# ====== ACCESS GUARD ==========================================================
# Only admins may open this page.
role = st.session_state.get("role", None)
if role != "admin":
    st.error("Admin only. Please log in as an admin.")
    st.stop()

st.set_page_config(page_title="Admin · Users", page_icon="👤")
st.title("👤 Admin · Users")

# ====== DB CONNECTION =========================================================
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

def run_query(sql, params=None, fetch=False):
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        if fetch:
            return cur.fetchall()
    return None

# ====== HELPERS ===============================================================
def list_users():
    return run_query(
        """
        select id, username, role, is_active, created_at
        from users
        order by created_at desc
        """,
        fetch=True,
    )

def add_user(username, password, role="worker", active=True):
    run_query(
        """
        insert into users (username, password_hash, role, is_active)
        values (%s, crypt(%s, gen_salt('bf')), %s, %s)
        on conflict (username) do nothing
        """,
        (username, password, role, active),
    )

def change_password(username, new_password):
    run_query(
        """
        update users
        set password_hash = crypt(%s, gen_salt('bf'))
        where username = %s
        """,
        (new_password, username),
    )

def set_role(username, role):
    run_query(
        """
        update users
        set role = %s
        where username = %s
        """,
        (role, username),
    )

def set_active(username, is_active: bool):
    run_query(
        """
        update users
        set is_active = %s
        where username = %s
        """,
        (is_active, username),
    )

# ====== UI: ADD USER ==========================================================
st.subheader("Add new user")
with st.form("add_user_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_username = st.text_input("Username", placeholder="farmer2", max_chars=50)
        new_password = st.text_input("Temporary password", type="password")
    with col2:
        new_role = st.selectbox("Role", ["worker", "manager", "admin"], index=0)
        new_active = st.checkbox("Active", value=True)
    submitted = st.form_submit_button("Add user")
    if submitted:
        if not new_username or not new_password:
            st.warning("Username and password are required.")
        else:
            try:
                add_user(new_username.strip(), new_password, new_role, new_active)
                st.success(f"User '{new_username}' added.")
            except Exception as e:
                st.error(f"Failed to add user: {e}")

st.divider()

# ====== UI: MANAGE EXISTING USERS ============================================
st.subheader("Manage users")

users = list_users() or []
if not users:
    st.info("No users found yet.")
else:
    for u in users:
        with st.expander(f"{u['username']} · {u['role']} · {'active' if u['is_active'] else 'inactive'}"):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.caption("Change password")
                npw = st.text_input(f"New password for {u['username']}", type="password", key=f"pw_{u['id']}")
                if st.button("Update password", key=f"pw_btn_{u['id']}"):
                    if npw:
                        try:
                            change_password(u["username"], npw)
                            st.success("Password updated.")
                        except Exception as e:
                            st.error(f"Failed: {e}")
                    else:
                        st.warning("Enter a new password first.")

            with c2:
                st.caption("Change role")
                new_role_val = st.selectbox(
                    f"Role for {u['username']}",
                    ["worker", "manager", "admin"],
                    index=["worker", "manager", "admin"].index(u["role"]),
                    key=f"role_{u['id']}",
                )
                if st.button("Update role", key=f"role_btn_{u['id']}"):
                    try:
                        set_role(u["username"], new_role_val)
                        st.success("Role updated.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

            with c3:
                st.caption("Activation")
                tgt_active = st.toggle("Active", value=u["is_active"], key=f"act_{u['id']}")
                if st.button("Save status", key=f"act_btn_{u['id']}"):
                    try:
                        set_active(u["username"], tgt_active)
                        st.success("Status updated.")
                    except Exception as e:
                        st.error(f"Failed: {e}")
