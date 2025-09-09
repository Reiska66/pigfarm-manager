# PigFarm Manager (Streamlit + Supabase)

A secure, multi-user pig farm management app for ~200 pigs. Features per-organization
data isolation with Supabase Row-Level Security (RLS), per-user roles, and basic modules:
Pigs, Feed Logs, and Invoices.

## Quick Start (Streamlit Cloud)

1. **Create Supabase Project**
   - Go to Supabase and create a new project.
   - Copy your `SUPABASE_URL` and **anon** `SUPABASE_ANON_KEY`.

2. **Run the SQL schema**
   - In Supabase SQL editor, paste & run `supabase_schema.sql` from this repo.
   - This creates tables, roles, and RLS policies.

3. **Set Streamlit Secrets**
   - In Streamlit Cloud → App → Settings → Secrets, add:
     ```toml
     SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
     SUPABASE_ANON_KEY="YOUR_PUBLIC_ANON_KEY"
     ```

4. **Deploy**
   - Push these files to a new GitHub repo (e.g., `Reiska66/pigfarm-manager`) or upload directly.
   - Deploy on Streamlit Cloud, selecting `streamlit_app.py` as the entry point.

5. **Invite Users**
   - Use the app's Admin → "Invite user" to create an auth user and link them to your org as `admin`, `manager`, or `worker`.

## Local Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Modules
- **Pigs:** register pigs (tag, DOB, notes)
- **Feed Logs:** date, pig, feed type, qty_kg, cost_kes
- **Invoices:** customer_name, numbers, totals; generate summaries

## Security Notes
- Uses **Supabase Auth** (email/password), JWT sessions.
- **RLS** enforces organization data isolation.
- Only use the **anon** key in Streamlit. Never expose service_role key in the frontend.
- Storage uploads (e.g., invoice PDFs) should use signed URLs and storage policies (see TODO section).

## TODO (nice-to-haves)
- 2FA enforcement for admin/manager
- File storage for invoices (signed URLs)
- Offline cache & sync (SQLCipher)
- Audit logs
