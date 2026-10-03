-- IntelliLearn Curriculum Intelligence upgrade
-- Run this ONCE in Supabase SQL Editor on an existing IntelliLearn database.

create extension if not exists vector;

-- ============================================================
-- 1. CURRICULA
-- ============================================================

create table if not exists public.curricula (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
    subject_name text not null,
    course_name text not null default '',
    semester text not null default '',
    source_type text not null check (source_type in ('syllabus', 'question_bank', 'syllabus+question_bank')),
    syllabus_filename text,
    syllabus_storage_path text,
    question_bank_filename text,
    question_bank_storage_path text,
    created_at timestamptz not null default now()
);

alter table public.curricula enable row level security;

drop policy if exists "Users can read own curricula" on public.curricula;
create policy "Users can read own curricula"
on public.curricula for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own curricula" on public.curricula;
create policy "Users can insert own curricula"
on public.curricula for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own curricula" on public.curricula;
create policy "Users can delete own curricula"
on public.curricula for delete
to authenticated
using (auth.uid() = user_id);

-- ============================================================
-- 2. CURRICULUM UNITS
-- ============================================================

create table if not exists public.curriculum_units (
    id uuid primary key default gen_random_uuid(),
    curriculum_id uuid not null references public.curricula(id) on delete cascade,
    unit_number text not null default '',
    unit_title text not null,
    is_official boolean not null default false,
    sort_order integer not null default 0,
    created_at timestamptz not null default now()
);

alter table public.curriculum_units enable row level security;

drop policy if exists "Users can read own curriculum units" on public.curriculum_units;
create policy "Users can read own curriculum units"
on public.curriculum_units for select
to authenticated
using (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_units.curriculum_id
          and c.user_id = auth.uid()
    )
);

drop policy if exists "Users can insert own curriculum units" on public.curriculum_units;
create policy "Users can insert own curriculum units"
on public.curriculum_units for insert
to authenticated
with check (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_units.curriculum_id
          and c.user_id = auth.uid()
    )
);

-- ============================================================
-- 3. CURRICULUM TOPICS + EMBEDDINGS
-- ============================================================

create table if not exists public.curriculum_topics (
    id uuid primary key default gen_random_uuid(),
    curriculum_id uuid not null references public.curricula(id) on delete cascade,
    unit_id uuid not null references public.curriculum_units(id) on delete cascade,
    topic_name text not null,
    topic_description text not null default '',
    is_official boolean not null default false,
    sort_order integer not null default 0,
    embedding vector(768) not null,
    created_at timestamptz not null default now()
);

alter table public.curriculum_topics enable row level security;

drop policy if exists "Users can read own curriculum topics" on public.curriculum_topics;
create policy "Users can read own curriculum topics"
on public.curriculum_topics for select
to authenticated
using (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_topics.curriculum_id
          and c.user_id = auth.uid()
    )
);

drop policy if exists "Users can insert own curriculum topics" on public.curriculum_topics;
create policy "Users can insert own curriculum topics"
on public.curriculum_topics for insert
to authenticated
with check (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_topics.curriculum_id
          and c.user_id = auth.uid()
    )
);

create index if not exists curriculum_topics_curriculum_idx
on public.curriculum_topics(curriculum_id);

-- ============================================================
-- 4. QUESTION BANK ITEMS
-- ============================================================

create table if not exists public.curriculum_questions (
    id uuid primary key default gen_random_uuid(),
    curriculum_id uuid not null references public.curricula(id) on delete cascade,
    unit_id uuid references public.curriculum_units(id) on delete set null,
    topic_id uuid references public.curriculum_topics(id) on delete set null,
    question_text text not null,
    topic_hint text not null default '',
    created_at timestamptz not null default now()
);

alter table public.curriculum_questions enable row level security;

drop policy if exists "Users can read own curriculum questions" on public.curriculum_questions;
create policy "Users can read own curriculum questions"
on public.curriculum_questions for select
to authenticated
using (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_questions.curriculum_id
          and c.user_id = auth.uid()
    )
);

drop policy if exists "Users can insert own curriculum questions" on public.curriculum_questions;
create policy "Users can insert own curriculum questions"
on public.curriculum_questions for insert
to authenticated
with check (
    exists (
        select 1 from public.curricula c
        where c.id = curriculum_questions.curriculum_id
          and c.user_id = auth.uid()
    )
);

-- ============================================================
-- 5. LINK STUDY DOCUMENTS TO CURRICULA
-- ============================================================

alter table public.documents
add column if not exists document_type text not null default 'notes';

alter table public.documents
add column if not exists curriculum_id uuid references public.curricula(id) on delete set null;

create index if not exists documents_curriculum_idx
on public.documents(curriculum_id);

-- ============================================================
-- 6. SEMANTIC MATCH: QUESTION -> CURRICULUM TOPIC
-- ============================================================

create or replace function public.match_curriculum_topics(
    query_embedding vector(768),
    p_curriculum_id uuid,
    match_count integer default 5
)
returns table (
    id uuid,
    curriculum_id uuid,
    unit_id uuid,
    subject_name text,
    unit_number text,
    unit_title text,
    topic_name text,
    topic_description text,
    is_official boolean,
    similarity double precision
)
language sql
stable
security invoker
set search_path = public
as $$
    select
        ct.id,
        ct.curriculum_id,
        ct.unit_id,
        c.subject_name,
        cu.unit_number,
        cu.unit_title,
        ct.topic_name,
        ct.topic_description,
        ct.is_official,
        1 - (ct.embedding <=> query_embedding) as similarity
    from public.curriculum_topics ct
    join public.curricula c on c.id = ct.curriculum_id
    join public.curriculum_units cu on cu.id = ct.unit_id
    where ct.curriculum_id = p_curriculum_id
      and c.user_id = auth.uid()
    order by ct.embedding <=> query_embedding
    limit least(match_count, 10);
$$;

-- ============================================================
-- 7. SEMANTIC SEARCH ACROSS ALL MATERIALS IN A CURRICULUM
-- ============================================================

create or replace function public.match_curriculum_document_chunks(
    query_embedding vector(768),
    p_curriculum_id uuid,
    match_count integer default 10
)
returns table (
    id bigint,
    document_id uuid,
    filename text,
    document_type text,
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
        d.filename,
        d.document_type,
        dc.page_number,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity
    from public.document_chunks dc
    join public.documents d on d.id = dc.document_id
    where dc.user_id = auth.uid()
      and d.user_id = auth.uid()
      and d.curriculum_id = p_curriculum_id
    order by dc.embedding <=> query_embedding
    limit least(match_count, 20);
$$;

-- ============================================================
-- 8. PERMISSIONS
-- ============================================================

grant select, insert, delete on public.curricula to authenticated;
grant select, insert on public.curriculum_units to authenticated;
grant select, insert on public.curriculum_topics to authenticated;
grant select, insert on public.curriculum_questions to authenticated;

grant execute on function public.match_curriculum_topics(vector, uuid, integer)
to authenticated;

grant execute on function public.match_curriculum_document_chunks(vector, uuid, integer)
to authenticated;
