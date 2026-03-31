create table if not exists public.beta_interest_signals (
    id uuid primary key default gen_random_uuid(),
    clerk_user_id text not null unique,
    email text,
    full_name text,
    institution text,
    role_title text,
    selected_plan text not null default 'free_beta',
    tell_friend_signal text not null default 'maybe',
    primary_use_case text,
    feedback text,
    github_url text,
    linkedin_url text,
    research_interests jsonb not null default '[]'::jsonb,
    source text not null default 'github_pages_beta',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint beta_interest_signals_tell_friend_signal_check
        check (tell_friend_signal in ('yes', 'maybe', 'not_yet'))
);

create index if not exists beta_interest_signals_tell_friend_signal_idx
    on public.beta_interest_signals(tell_friend_signal, updated_at desc);

create index if not exists beta_interest_signals_selected_plan_idx
    on public.beta_interest_signals(selected_plan, updated_at desc);

alter table public.beta_interest_signals enable row level security;

do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'beta_interest_signals'
          and policyname = 'anon_can_insert_beta_interest_signals'
    ) then
        create policy anon_can_insert_beta_interest_signals
        on public.beta_interest_signals
        for insert
        to anon, authenticated
        with check (true);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'beta_interest_signals'
          and policyname = 'anon_can_update_own_beta_interest_signals_by_clerk_user_id'
    ) then
        create policy anon_can_update_own_beta_interest_signals_by_clerk_user_id
        on public.beta_interest_signals
        for update
        to anon, authenticated
        using (true)
        with check (true);
    end if;
end $$;

create or replace function public.set_beta_interest_signals_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists beta_interest_signals_set_updated_at on public.beta_interest_signals;
create trigger beta_interest_signals_set_updated_at
before update on public.beta_interest_signals
for each row
execute function public.set_beta_interest_signals_updated_at();
