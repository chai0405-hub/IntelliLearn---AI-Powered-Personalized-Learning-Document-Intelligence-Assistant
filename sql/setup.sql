-- IntelliLearn Supabase setup
-- Run this entire file in Supabase Dashboard -> SQL Editor.

create extension if not exists vector;

-- ============================================================
-- 1. USER PROFILE
-- ============================================================

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null,
    username text not null unique,
    email text not null unique,
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
on public.profiles for select
to authenticated
using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

-- Automatically create profile after Auth signup.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, full_name, username, email)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'full_name', 'Student'),
        lower(new.raw_user_meta_data ->> 'username'),
        lower(new.email)
    );
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- Supabase Auth itself signs in with email/password.
-- This server-side function lets the Streamlit app translate username -> email.
create or replace function public.get_email_for_username(p_username text)
returns text
language sql
stable
security definer
set search_path = public
as $$
    select email
    from public.profiles
    where username = lower(trim(p_username))
    limit 1;
$$;

revoke all on function public.get_email_for_username(text) from public;
grant execute on function public.get_email_for_username(text) to anon, authenticated;

-- ============================================================
-- 2. DOCUMENTS
-- ============================================================

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
    filename text not null,
    storage_path text not null,
    page_count integer not null default 0,
    created_at timestamptz not null default now()
);

alter table public.documents enable row level security;

drop policy if exists "Users can read own documents" on public.documents;
create policy "Users can read own documents"
on public.documents for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own documents" on public.documents;
create policy "Users can insert own documents"
on public.documents for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own documents" on public.documents;
create policy "Users can delete own documents"
on public.documents for delete
to authenticated
using (auth.uid() = user_id);

-- ============================================================
-- 3. DOCUMENT CHUNKS + VECTOR EMBEDDINGS
-- ============================================================

create table if not exists public.document_chunks (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    document_id uuid not null references public.documents(id) on delete cascade,
    page_number integer not null,
    chunk_index integer not null,
    content text not null,
    embedding vector(768) not null,
    created_at timestamptz not null default now(),
    unique(document_id, page_number, chunk_index)
);

alter table public.document_chunks enable row level security;

drop policy if exists "Users can read own chunks" on public.document_chunks;
create policy "Users can read own chunks"
on public.document_chunks for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own chunks" on public.document_chunks;
create policy "Users can insert own chunks"
on public.document_chunks for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own chunks" on public.document_chunks;
create policy "Users can delete own chunks"
on public.document_chunks for delete
to authenticated
using (auth.uid() = user_id);

create index if not exists document_chunks_document_idx
on public.document_chunks(document_id);

-- For a small final-year project, exact vector search is reliable and simple.
-- Add an HNSW vector index later if the number of chunks becomes large.

create or replace function public.match_document_chunks(
    query_embedding vector(768),
    p_document_id uuid,
    match_count integer default 6
)
returns table (
    id bigint,
    document_id uuid,
    page_number integer,
    content text,
    similarity double precision
)
language sql
stable
security invoker
set search_path = public
as $$
    select
        dc.id,
        dc.document_id,
        dc.page_number,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity
    from public.document_chunks dc
    where dc.user_id = auth.uid()
      and dc.document_id = p_document_id
    order by dc.embedding <=> query_embedding
    limit least(match_count, 10);
$$;

grant execute on function public.match_document_chunks(vector, uuid, integer)
to authenticated;

-- ============================================================
-- 4. QUIZ ATTEMPTS
-- ============================================================

create table if not exists public.quiz_attempts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
    topic text not null,
    score integer not null,
    total integer not null,
    percentage numeric(5,2) not null,
    created_at timestamptz not null default now()
);

alter table public.quiz_attempts enable row level security;

drop policy if exists "Users can read own quiz attempts" on public.quiz_attempts;
create policy "Users can read own quiz attempts"
on public.quiz_attempts for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own quiz attempts" on public.quiz_attempts;
create policy "Users can insert own quiz attempts"
on public.quiz_attempts for insert
to authenticated
with check (auth.uid() = user_id);

-- ============================================================
-- 5. STUDY PLANS
-- ============================================================

create table if not exists public.study_plans (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
    exam_date date not null,
    daily_minutes integer not null,
    subjects text[] not null,
    plan_markdown text not null,
    created_at timestamptz not null default now()
);

alter table public.study_plans enable row level security;

drop policy if exists "Users can read own study plans" on public.study_plans;
create policy "Users can read own study plans"
on public.study_plans for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own study plans" on public.study_plans;
create policy "Users can insert own study plans"
on public.study_plans for insert
to authenticated
with check (auth.uid() = user_id);

-- ============================================================
-- 6. STORAGE BUCKET + STORAGE RLS
-- ============================================================

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;

drop policy if exists "Users can upload own PDFs" on storage.objects;
create policy "Users can upload own PDFs"
on storage.objects for insert
to authenticated
with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Users can read own PDFs" on storage.objects;
create policy "Users can read own PDFs"
on storage.objects for select
to authenticated
using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Users can delete own PDFs" on storage.objects;
create policy "Users can delete own PDFs"
on storage.objects for delete
to authenticated
using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================
-- 7. DATA API PERMISSIONS
-- ============================================================

grant usage on schema public to anon, authenticated;

grant select, update on public.profiles to authenticated;
grant select, insert, delete on public.documents to authenticated;
grant select, insert, delete on public.document_chunks to authenticated;
grant select, insert on public.quiz_attempts to authenticated;
grant select, insert on public.study_plans to authenticated;

grant usage, select on sequence public.document_chunks_id_seq to authenticated;
