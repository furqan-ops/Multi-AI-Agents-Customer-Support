-- Project 3 schema - run in Supabase SQL Editor

create table if not exists token_usage (
  id bigserial primary key,
  request_id text,
  agent text,
  model text,
  prompt_tokens int default 0,
  completion_tokens int default 0,
  total_tokens int generated always as (prompt_tokens + completion_tokens) stored,
  cost_usd numeric(10,6) default 0,
  created_at timestamptz default now()
);
create index if not exists idx_token_usage_created_at on token_usage(created_at desc);
create index if not exists idx_token_usage_agent on token_usage(agent);

create table if not exists guardrail_events (
  id bigserial primary key,
  request_id text,
  agent text,
  event_type text not null,
  severity text default 'warning',
  details jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_guardrail_events_created_at on guardrail_events(created_at desc);

create table if not exists budget_config (
  id int primary key default 1,
  daily_budget_usd numeric(10,2) default 5.00,
  monthly_budget_usd numeric(10,2) default 100.00,
  max_escalation_rate numeric(4,3) default 0.30,
  min_avg_confidence numeric(4,3) default 0.60,
  updated_at timestamptz default now(),
  constraint single_row check (id = 1)
);
insert into budget_config (id) values (1) on conflict do nothing;

create table if not exists alerts (
  id bigserial primary key,
  alert_type text not null,
  severity text default 'warning',
  message text,
  value numeric(12,4),
  threshold numeric(12,4),
  acknowledged boolean default false,
  created_at timestamptz default now()
);
create index if not exists idx_alerts_created_at on alerts(created_at desc);