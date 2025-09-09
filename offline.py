import streamlit as st
from typing import Dict, Any, List

def get_queue() -> List[Dict[str, Any]]:
    if "offline_queue" not in st.session_state:
        st.session_state["offline_queue"] = []
    return st.session_state["offline_queue"]

def enqueue(action: str, table: str, payload: dict):
    q = get_queue()
    q.append({"action": action, "table": table, "payload": payload})
    st.toast(f"Queued offline: {action} -> {table}")

def flush_queue(supabase_client):
    q = get_queue()
    sent = 0
    remaining = []
    for item in q:
        try:
            if item["action"] == "insert":
                supabase_client.table(item["table"]).insert(item["payload"]).execute()
            elif item["action"] == "upsert":
                supabase_client.table(item["table"]).upsert(item["payload"]).execute()
            else:
                continue
            sent += 1
        except Exception:
            remaining.append(item)
    st.session_state["offline_queue"] = remaining
    return sent, len(remaining)
