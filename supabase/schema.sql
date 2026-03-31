create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    id uuid primary key default gen_random_uuid(),
    clerk_user_id text not null unique,
    username text,
    email text,
    full_name text,
    first_name text,
    last_name text,
    avatar_url text,
    institution text,
    role_title text,
    github_url text,
    linkedin_url text,
    research_interests jsonb not null default '[]'::jsonb,
    onboarding_notes text,
    plan text not null default 'free',
    auth_provider text not null default 'clerk',
    is_admin boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.saved_papers (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    work_id text not null,
    document_id text,
    title text,
    source_system text,
    institution text,
    author text,
    topic text,
    citation text,
    published text,
    pdf_url text,
    entry_url text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create unique index if not exists saved_papers_profile_work_id_idx
    on public.saved_papers(profile_id, work_id);

create index if not exists saved_papers_profile_created_at_idx
    on public.saved_papers(profile_id, created_at desc);

create table if not exists public.reading_queue (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    work_id text not null,
    document_id text,
    title text,
    source_system text,
    institution text,
    created_at timestamptz not null default now()
);

create unique index if not exists reading_queue_profile_work_id_idx
    on public.reading_queue(profile_id, work_id);

create index if not exists reading_queue_profile_created_at_idx
    on public.reading_queue(profile_id, created_at desc);

create table if not exists public.favorite_papers (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    work_id text not null,
    document_id text,
    title text,
    source_system text,
    institution text,
    created_at timestamptz not null default now()
);

create unique index if not exists favorite_papers_profile_work_id_idx
    on public.favorite_papers(profile_id, work_id);

create index if not exists favorite_papers_profile_created_at_idx
    on public.favorite_papers(profile_id, created_at desc);

create table if not exists public.paper_notes (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    paper_work_id text,
    paper_document_id text,
    paper_title text,
    content text,
    tags jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists paper_notes_profile_created_at_idx
    on public.paper_notes(profile_id, created_at desc);

create table if not exists public.paper_comparisons (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    title text not null,
    work_ids jsonb not null default '[]'::jsonb,
    paper_titles jsonb not null default '[]'::jsonb,
    question text,
    summary text,
    created_at timestamptz not null default now()
);

create index if not exists paper_comparisons_profile_created_at_idx
    on public.paper_comparisons(profile_id, created_at desc);

create table if not exists public.paper_activity_events (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    event_type text not null,
    event_source text not null default 'api',
    action_context text,
    search_query text,
    search_mode text,
    work_id text,
    document_id text,
    title text,
    source_system text,
    author text,
    institution text,
    topic text,
    result_count integer,
    result_rank integer,
    event_value double precision not null default 1,
    recommendation_context jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists paper_activity_events_profile_created_at_idx
    on public.paper_activity_events(profile_id, created_at desc);

create index if not exists paper_activity_events_profile_event_type_idx
    on public.paper_activity_events(profile_id, event_type, created_at desc);

create index if not exists paper_activity_events_profile_work_id_idx
    on public.paper_activity_events(profile_id, work_id, created_at desc);

create table if not exists public.profile_paper_interests (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    work_id text not null,
    document_id text,
    title text,
    source_system text,
    author text,
    institution text,
    topic text,
    first_interaction_at timestamptz not null default now(),
    last_interaction_at timestamptz not null default now(),
    last_event_type text,
    last_search_query text,
    search_count integer not null default 0,
    view_count integer not null default 0,
    save_count integer not null default 0,
    queue_count integer not null default 0,
    favorite_count integer not null default 0,
    compare_count integer not null default 0,
    note_count integer not null default 0,
    question_count integer not null default 0,
    upload_count integer not null default 0,
    recommendation_score double precision not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists profile_paper_interests_profile_work_id_idx
    on public.profile_paper_interests(profile_id, work_id);

create index if not exists profile_paper_interests_profile_score_idx
    on public.profile_paper_interests(profile_id, recommendation_score desc, last_interaction_at desc);

create index if not exists profile_paper_interests_profile_topic_idx
    on public.profile_paper_interests(profile_id, topic, last_interaction_at desc);

create table if not exists public.profile_topic_interests (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    topic text not null,
    interaction_count integer not null default 0,
    search_count integer not null default 0,
    save_count integer not null default 0,
    compare_count integer not null default 0,
    question_count integer not null default 0,
    recommendation_score double precision not null default 0,
    last_interaction_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists profile_topic_interests_profile_topic_idx
    on public.profile_topic_interests(profile_id, topic);

create index if not exists profile_topic_interests_profile_score_idx
    on public.profile_topic_interests(profile_id, recommendation_score desc, last_interaction_at desc);

create table if not exists public.subscription_plans (
    code text primary key,
    name text not null,
    billing_interval text not null default 'month',
    price_monthly_cents integer not null default 0,
    stripe_price_id text,
    seats_included integer not null default 1,
    usage_caps jsonb not null default '{}'::jsonb,
    is_active boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.billing_customers (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid unique references public.profiles(id) on delete cascade,
    clerk_user_id text unique,
    stripe_customer_id text unique,
    email text,
    full_name text,
    plan_code text references public.subscription_plans(code),
    lifecycle_stage text not null default 'lead',
    sales_segment text,
    acquisition_channel text,
    marketing_campaign text,
    conversion_source text,
    is_active boolean not null default true,
    first_paid_at timestamptz,
    last_active_at timestamptz,
    total_orders integer not null default 0,
    total_revenue_cents bigint not null default 0,
    monthly_recurring_revenue_cents integer not null default 0,
    lifetime_value_cents bigint not null default 0,
    upgrade_propensity_score double precision not null default 0,
    churn_risk_score double precision not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists billing_customers_plan_code_idx
    on public.billing_customers(plan_code, updated_at desc);

create index if not exists billing_customers_lifecycle_stage_idx
    on public.billing_customers(lifecycle_stage, updated_at desc);

create table if not exists public.billing_subscriptions (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references public.profiles(id) on delete cascade,
    billing_customer_id uuid references public.billing_customers(id) on delete set null,
    stripe_subscription_id text unique,
    stripe_customer_id text,
    plan_code text references public.subscription_plans(code),
    status text not null default 'incomplete',
    billing_interval text not null default 'month',
    currency text not null default 'usd',
    unit_amount_cents integer not null default 0,
    seats integer not null default 1,
    current_period_start timestamptz,
    current_period_end timestamptz,
    cancel_at_period_end boolean not null default false,
    canceled_at timestamptz,
    trial_end timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists billing_subscriptions_profile_status_idx
    on public.billing_subscriptions(profile_id, status, updated_at desc);

create index if not exists billing_subscriptions_plan_status_idx
    on public.billing_subscriptions(plan_code, status, updated_at desc);

create table if not exists public.billing_transactions (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references public.profiles(id) on delete cascade,
    billing_customer_id uuid references public.billing_customers(id) on delete set null,
    subscription_id uuid references public.billing_subscriptions(id) on delete set null,
    stripe_invoice_id text unique,
    stripe_payment_intent_id text,
    stripe_checkout_session_id text,
    transaction_type text not null default 'invoice',
    status text not null default 'pending',
    currency text not null default 'usd',
    amount_subtotal_cents bigint not null default 0,
    amount_discount_cents bigint not null default 0,
    amount_tax_cents bigint not null default 0,
    amount_total_cents bigint not null default 0,
    collected_at timestamptz,
    refunded_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists billing_transactions_profile_collected_at_idx
    on public.billing_transactions(profile_id, collected_at desc);

create index if not exists billing_transactions_status_idx
    on public.billing_transactions(status, collected_at desc);

create table if not exists public.stripe_event_log (
    id uuid primary key default gen_random_uuid(),
    stripe_event_id text not null unique,
    event_type text not null,
    livemode boolean not null default false,
    api_version text,
    status text not null default 'received',
    processed_at timestamptz,
    error_message text,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists stripe_event_log_event_type_idx
    on public.stripe_event_log(event_type, created_at desc);

create table if not exists public.profile_usage_daily (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    usage_date date not null,
    plan_code text not null default 'free',
    event_count integer not null default 0,
    search_count integer not null default 0,
    view_count integer not null default 0,
    save_count integer not null default 0,
    question_count integer not null default 0,
    compare_count integer not null default 0,
    upload_count integer not null default 0,
    active_minutes integer not null default 0,
    last_event_at timestamptz,
    top_topics jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists profile_usage_daily_profile_date_idx
    on public.profile_usage_daily(profile_id, usage_date);

create index if not exists profile_usage_daily_usage_date_idx
    on public.profile_usage_daily(usage_date desc, plan_code);

create table if not exists public.customer_sales_profiles (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    billing_customer_id uuid references public.billing_customers(id) on delete set null,
    current_plan_code text references public.subscription_plans(code),
    lifecycle_stage text not null default 'lead',
    engagement_status text not null default 'new',
    revenue_band text not null default 'prepaid',
    buyer_persona text,
    best_fit_upgrade_plan text references public.subscription_plans(code),
    upgrade_reason text,
    upgrade_propensity_score double precision not null default 0,
    churn_risk_score double precision not null default 0,
    health_score double precision not null default 0,
    acquisition_channel text,
    product_fit_summary text,
    top_topics jsonb not null default '[]'::jsonb,
    recent_activity jsonb not null default '[]'::jsonb,
    next_best_actions jsonb not null default '[]'::jsonb,
    last_seen_at timestamptz,
    first_value_at timestamptz,
    total_revenue_cents bigint not null default 0,
    monthly_recurring_revenue_cents integer not null default 0,
    total_orders integer not null default 0,
    total_searches integer not null default 0,
    total_views integer not null default 0,
    total_comparisons integer not null default 0,
    total_questions integer not null default 0,
    total_uploads integer not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists customer_sales_profiles_plan_idx
    on public.customer_sales_profiles(current_plan_code, health_score desc);

create index if not exists customer_sales_profiles_upgrade_idx
    on public.customer_sales_profiles(best_fit_upgrade_plan, upgrade_propensity_score desc);

create table if not exists public.team_members (
    id uuid primary key default gen_random_uuid(),
    clerk_user_id text unique,
    email text,
    full_name text,
    role text not null default 'operator',
    department text not null default 'operations',
    employment_status text not null default 'active',
    manager_name text,
    start_date date,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.open_access_sources (
    id uuid primary key default gen_random_uuid(),
    source_key text not null unique,
    source_system text not null,
    source_type text not null default 'repository_record',
    ingestion_method text not null default 'api',
    access_basis text not null default 'open_access',
    verification_status text not null default 'verified',
    verification_method text not null default 'connector_policy',
    source_domain text,
    source_paper_id text,
    title text not null,
    translated_title text,
    abstract text,
    summary_seed_text text,
    audio_seed_text text,
    language_code text not null default 'und',
    authors jsonb not null default '[]'::jsonb,
    institutions jsonb not null default '[]'::jsonb,
    topics jsonb not null default '[]'::jsonb,
    categories jsonb not null default '[]'::jsonb,
    keywords jsonb not null default '[]'::jsonb,
    publication_year integer,
    published_at timestamptz,
    canonical_url text not null,
    landing_page_url text,
    readable_url text,
    pdf_url text,
    open_access_url text,
    license_name text,
    license_url text,
    rights_statement text,
    usage_constraints text,
    provenance jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    is_featured boolean not null default false,
    is_multilingual boolean not null default false,
    is_summary_ready boolean not null default false,
    is_audio_ready boolean not null default false,
    last_verified_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists open_access_sources_canonical_url_idx
    on public.open_access_sources(canonical_url);

create index if not exists open_access_sources_featured_idx
    on public.open_access_sources(is_featured, verification_status, last_verified_at desc);

create index if not exists open_access_sources_domain_idx
    on public.open_access_sources(source_domain, source_system, last_verified_at desc);

create table if not exists public.open_access_source_assets (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null references public.open_access_sources(id) on delete cascade,
    asset_type text not null default 'reference',
    label text,
    asset_url text not null,
    mime_type text,
    is_primary boolean not null default false,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists open_access_source_assets_source_url_idx
    on public.open_access_source_assets(source_id, asset_url);

create index if not exists open_access_source_assets_type_idx
    on public.open_access_source_assets(source_id, asset_type, created_at desc);

create table if not exists public.open_access_ingestion_runs (
    id uuid primary key default gen_random_uuid(),
    requested_by_clerk_user_id text,
    connector_name text not null,
    query text,
    requested_url text,
    source_domain text,
    source_type text,
    ingestion_method text not null default 'api',
    status text not null default 'pending',
    record_count integer not null default 0,
    warning_count integer not null default 0,
    warnings jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists open_access_ingestion_runs_connector_idx
    on public.open_access_ingestion_runs(connector_name, started_at desc);

create index if not exists open_access_ingestion_runs_status_idx
    on public.open_access_ingestion_runs(status, started_at desc);

create table if not exists public.admin_role_audit_events (
    id uuid primary key default gen_random_uuid(),
    actor_clerk_user_id text not null,
    target_clerk_user_id text not null,
    action text not null,
    admin_source text,
    previous_is_admin boolean not null default false,
    new_is_admin boolean not null default false,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists admin_role_audit_events_created_at_idx
    on public.admin_role_audit_events(created_at desc);

create index if not exists admin_role_audit_events_actor_idx
    on public.admin_role_audit_events(actor_clerk_user_id, created_at desc);

create index if not exists admin_role_audit_events_target_idx
    on public.admin_role_audit_events(target_clerk_user_id, created_at desc);

create table if not exists public.app_runtime_settings (
    key text primary key,
    value jsonb not null default '{}'::jsonb,
    updated_by_clerk_user_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

drop trigger if exists profile_paper_interests_set_updated_at on public.profile_paper_interests;
create trigger profile_paper_interests_set_updated_at
before update on public.profile_paper_interests
for each row
execute function public.set_updated_at();

drop trigger if exists profile_topic_interests_set_updated_at on public.profile_topic_interests;
create trigger profile_topic_interests_set_updated_at
before update on public.profile_topic_interests
for each row
execute function public.set_updated_at();

drop trigger if exists subscription_plans_set_updated_at on public.subscription_plans;
create trigger subscription_plans_set_updated_at
before update on public.subscription_plans
for each row
execute function public.set_updated_at();

drop trigger if exists billing_customers_set_updated_at on public.billing_customers;
create trigger billing_customers_set_updated_at
before update on public.billing_customers
for each row
execute function public.set_updated_at();

drop trigger if exists billing_subscriptions_set_updated_at on public.billing_subscriptions;
create trigger billing_subscriptions_set_updated_at
before update on public.billing_subscriptions
for each row
execute function public.set_updated_at();

drop trigger if exists profile_usage_daily_set_updated_at on public.profile_usage_daily;
create trigger profile_usage_daily_set_updated_at
before update on public.profile_usage_daily
for each row
execute function public.set_updated_at();

drop trigger if exists customer_sales_profiles_set_updated_at on public.customer_sales_profiles;
create trigger customer_sales_profiles_set_updated_at
before update on public.customer_sales_profiles
for each row
execute function public.set_updated_at();

drop trigger if exists team_members_set_updated_at on public.team_members;
create trigger team_members_set_updated_at
before update on public.team_members
for each row
execute function public.set_updated_at();

drop trigger if exists open_access_sources_set_updated_at on public.open_access_sources;
create trigger open_access_sources_set_updated_at
before update on public.open_access_sources
for each row
execute function public.set_updated_at();

drop trigger if exists open_access_source_assets_set_updated_at on public.open_access_source_assets;
create trigger open_access_source_assets_set_updated_at
before update on public.open_access_source_assets
for each row
execute function public.set_updated_at();

drop trigger if exists open_access_ingestion_runs_set_updated_at on public.open_access_ingestion_runs;
create trigger open_access_ingestion_runs_set_updated_at
before update on public.open_access_ingestion_runs
for each row
execute function public.set_updated_at();

drop trigger if exists app_runtime_settings_set_updated_at on public.app_runtime_settings;
create trigger app_runtime_settings_set_updated_at
before update on public.app_runtime_settings
for each row
execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.saved_papers enable row level security;
alter table public.reading_queue enable row level security;
alter table public.favorite_papers enable row level security;
alter table public.paper_notes enable row level security;
alter table public.paper_comparisons enable row level security;
alter table public.paper_activity_events enable row level security;
alter table public.profile_paper_interests enable row level security;
alter table public.profile_topic_interests enable row level security;
alter table public.subscription_plans enable row level security;
alter table public.billing_customers enable row level security;
alter table public.billing_subscriptions enable row level security;
alter table public.billing_transactions enable row level security;
alter table public.stripe_event_log enable row level security;
alter table public.profile_usage_daily enable row level security;
alter table public.customer_sales_profiles enable row level security;
alter table public.team_members enable row level security;
alter table public.open_access_sources enable row level security;
alter table public.open_access_source_assets enable row level security;
alter table public.open_access_ingestion_runs enable row level security;
alter table public.admin_role_audit_events enable row level security;
alter table public.app_runtime_settings enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'profiles' and policyname = 'service_role_profiles_all'
    ) then
        create policy service_role_profiles_all on public.profiles
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'saved_papers' and policyname = 'service_role_saved_papers_all'
    ) then
        create policy service_role_saved_papers_all on public.saved_papers
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'reading_queue' and policyname = 'service_role_reading_queue_all'
    ) then
        create policy service_role_reading_queue_all on public.reading_queue
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'favorite_papers' and policyname = 'service_role_favorite_papers_all'
    ) then
        create policy service_role_favorite_papers_all on public.favorite_papers
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'paper_notes' and policyname = 'service_role_paper_notes_all'
    ) then
        create policy service_role_paper_notes_all on public.paper_notes
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'paper_comparisons' and policyname = 'service_role_paper_comparisons_all'
    ) then
        create policy service_role_paper_comparisons_all on public.paper_comparisons
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'paper_activity_events' and policyname = 'service_role_paper_activity_events_all'
    ) then
        create policy service_role_paper_activity_events_all on public.paper_activity_events
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'profile_paper_interests' and policyname = 'service_role_profile_paper_interests_all'
    ) then
        create policy service_role_profile_paper_interests_all on public.profile_paper_interests
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'profile_topic_interests' and policyname = 'service_role_profile_topic_interests_all'
    ) then
        create policy service_role_profile_topic_interests_all on public.profile_topic_interests
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'subscription_plans' and policyname = 'service_role_subscription_plans_all'
    ) then
        create policy service_role_subscription_plans_all on public.subscription_plans
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'billing_customers' and policyname = 'service_role_billing_customers_all'
    ) then
        create policy service_role_billing_customers_all on public.billing_customers
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'billing_subscriptions' and policyname = 'service_role_billing_subscriptions_all'
    ) then
        create policy service_role_billing_subscriptions_all on public.billing_subscriptions
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'billing_transactions' and policyname = 'service_role_billing_transactions_all'
    ) then
        create policy service_role_billing_transactions_all on public.billing_transactions
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'stripe_event_log' and policyname = 'service_role_stripe_event_log_all'
    ) then
        create policy service_role_stripe_event_log_all on public.stripe_event_log
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'profile_usage_daily' and policyname = 'service_role_profile_usage_daily_all'
    ) then
        create policy service_role_profile_usage_daily_all on public.profile_usage_daily
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'customer_sales_profiles' and policyname = 'service_role_customer_sales_profiles_all'
    ) then
        create policy service_role_customer_sales_profiles_all on public.customer_sales_profiles
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'team_members' and policyname = 'service_role_team_members_all'
    ) then
        create policy service_role_team_members_all on public.team_members
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'open_access_sources' and policyname = 'service_role_open_access_sources_all'
    ) then
        create policy service_role_open_access_sources_all on public.open_access_sources
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'open_access_source_assets' and policyname = 'service_role_open_access_source_assets_all'
    ) then
        create policy service_role_open_access_source_assets_all on public.open_access_source_assets
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'open_access_ingestion_runs' and policyname = 'service_role_open_access_ingestion_runs_all'
    ) then
        create policy service_role_open_access_ingestion_runs_all on public.open_access_ingestion_runs
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'admin_role_audit_events' and policyname = 'service_role_admin_role_audit_events_all'
    ) then
        create policy service_role_admin_role_audit_events_all on public.admin_role_audit_events
        for all
        to service_role
        using (true)
        with check (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'app_runtime_settings' and policyname = 'service_role_app_runtime_settings_all'
    ) then
        create policy service_role_app_runtime_settings_all on public.app_runtime_settings
        for all
        to service_role
        using (true)
        with check (true);
    end if;
end $$;

insert into public.subscription_plans (
    code,
    name,
    billing_interval,
    price_monthly_cents,
    seats_included,
    usage_caps,
    metadata
)
values
    (
        'free',
        'Free',
        'month',
        0,
        1,
        '{"queries_per_month": 25, "arxiv_ingests": 2}'::jsonb,
        '{"positioning": "Top-of-funnel evaluation plan"}'::jsonb
    ),
    (
        'student',
        'Student',
        'month',
        299,
        1,
        '{"queries_per_month": 250, "arxiv_ingests": 25}'::jsonb,
        '{"positioning": "Budget-friendly plan for students"}'::jsonb
    ),
    (
        'pro',
        'Pro',
        'month',
        999,
        1,
        '{"queries_per_month": 1200, "arxiv_ingests": 150}'::jsonb,
        '{"positioning": "Primary paid plan for serious researchers"}'::jsonb
    ),
    (
        'enterprise',
        'Enterprise',
        'month',
        1499,
        5,
        '{"queries_per_month": 10000, "arxiv_ingests": 1000}'::jsonb,
        '{"positioning": "Team plan with expansion potential"}'::jsonb
    )
on conflict (code) do update
set
    name = excluded.name,
    billing_interval = excluded.billing_interval,
    price_monthly_cents = excluded.price_monthly_cents,
    seats_included = excluded.seats_included,
    usage_caps = excluded.usage_caps,
    metadata = excluded.metadata,
    is_active = true;
