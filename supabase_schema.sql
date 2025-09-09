-- Enable required extensions
create extension if not exists pgcrypto;

-- Organizations
create table if not exists orgs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz default now()
);

-- App users linked to Supabase Auth
create table if not exists app_users (
  user_id uuid primary key, -- auth.uid()
  org_id uuid not null references orgs(id) on delete cascade,
  role text not null check (role in ('admin','manager','worker')),
  created_at timestamptz default now()
);

-- Pigs
create table if not exists pigs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs(id) on delete cascade,
  tag text not null,
  dob date,
  notes text,
  created_by uuid not null, -- auth.uid()
  created_at timestamptz default now()
);

-- Feed logs
create table if not exists feed_logs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs(id) on delete cascade,
  pig_id uuid not null references pigs(id) on delete cascade,
  date date not null,
  feed_type text not null,
  qty_kg numeric not null check (qty_kg >= 0),
  cost_kes numeric not null check (cost_kes >= 0),
  created_by uuid not null,
  created_at timestamptz default now()
);

-- Invoices
create table if not exists invoices (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs(id) on delete cascade,
  number text not null,
  customer_name text,
  subtotal numeric not null check (subtotal >= 0),
  tax numeric not null check (tax >= 0),
  total numeric not null check (total >= 0),
  issued_on date not null,
  created_by uuid not null,
  created_at timestamptz default now()
);

-- View of current user
create or replace view me as
  select au.user_id, au.org_id, au.role
  from app_users au
  where au.user_id = auth.uid();

-- Enable Row Level Security
alter table app_users enable row level security;
alter table pigs enable row level security;
alter table feed_logs enable row level security;
alter table invoices enable row level security;

-- Policies for app_users (admin of same org can read)
drop policy if exists "read own app_user" on app_users;
create policy "read own app_user" on app_users
for select to authenticated
using (user_id = auth.uid() or org_id = (select org_id from me));

-- Pigs policies
drop policy if exists "read pigs own org" on pigs;
create policy "read pigs own org" on pigs
for select to authenticated
using (org_id = (select org_id from me));

drop policy if exists "insert pigs manager+" on pigs;
create policy "insert pigs manager+" on pigs
for insert to authenticated
with check (org_id = (select org_id from me) and (select role from me) in ('admin','manager'));

drop policy if exists "update pigs manager+" on pigs;
create policy "update pigs manager+" on pigs
for update to authenticated
using (org_id = (select org_id from me))
with check (org_id = (select org_id from me) and (select role from me) in ('admin','manager'));

-- Feed logs policies
drop policy if exists "read feed own org" on feed_logs;
create policy "read feed own org" on feed_logs
for select to authenticated
using (org_id = (select org_id from me));

drop policy if exists "insert feed worker+" on feed_logs;
create policy "insert feed worker+" on feed_logs
for insert to authenticated
with check (org_id = (select org_id from me) and (select role from me) in ('admin','manager','worker'));

drop policy if exists "update feed creator or manager+" on feed_logs;
create policy "update feed creator or manager+" on feed_logs
for update to authenticated
using (org_id = (select org_id from me) and (created_by = auth.uid() or (select role from me) in ('admin','manager')))
with check (org_id = (select org_id from me));

-- Invoices policies
drop policy if exists "read invoices own org" on invoices;
create policy "read invoices own org" on invoices
for select to authenticated
using (org_id = (select org_id from me));

drop policy if exists "insert invoices manager+" on invoices;
create policy "insert invoices manager+" on invoices
for insert to authenticated
with check (org_id = (select org_id from me) and (select role from me) in ('admin','manager'));

-- Helper function to create an org + admin user mapping (call with service role via SQL console, or use UI safely)
-- For production, use a secure Edge Function; here is a SQL convenience ONLY for your initial bootstrap.

-- Bootstrap additions

-- RLS for orgs
alter table orgs enable row level security;

-- Users can read orgs only if they belong to them (after linking),
-- but allow insert for any authenticated user to create their org.
drop policy if exists "select own orgs" on orgs;
create policy "select own orgs" on orgs
for select to authenticated
using (exists (select 1 from app_users au where au.org_id = orgs.id and au.user_id = auth.uid()));

drop policy if exists "insert orgs any authenticated" on orgs;
create policy "insert orgs any authenticated" on orgs
for insert to authenticated
with check (true);

-- Self-link policy so a new user can link themselves to an org as admin/manager/worker
drop policy if exists "self link to org" on app_users;
create policy "self link to org" on app_users
for insert to authenticated
with check (user_id = auth.uid());

-- Storage & MFA additions

-- === Storage: invoice PDFs ===
-- Create bucket in Supabase Storage UI named: invoice-files (public = false)

-- Storage policies (execute in SQL editor after bucket exists)
create policy if not exists "invoice files read own org"
on storage.objects for select to authenticated
using (
  bucket_id = 'invoice-files'
  and (storage.foldername(name))[1] = (select org_id::text from me) -- expects path 'ORG_ID/INVOICE_ID.pdf'
);

create policy if not exists "invoice files insert own org"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'invoice-files'
  and (storage.foldername(name))[1] = (select org_id::text from me)
);

create policy if not exists "invoice files delete manager+"
on storage.objects for delete to authenticated
using (
  bucket_id = 'invoice-files'
  and (storage.foldername(name))[1] = (select org_id::text from me)
  and (select role from me) in ('admin','manager')
);

-- === MFA enforcement note ===
-- In Supabase Auth settings, enable MFA (One-Time Password) for your project.
-- For soft enforcement, we show a banner in the app for admin/manager accounts.
