-- Auditra integrated plant-water model: DRAFT v0.1 for PostgreSQL (not yet run against a database).
-- Principles: one shared plant model (nodes + typed streams), time-series readings in UTC with a quality flag,
-- Gregorian/UTC storage and Jalali/Gregorian display, bilingual names, user-extensible reference tables.
-- Reference tables are filled from knowledge/vocab and knowledge/*.yaml; a user can add rows (code prefix 'USR-').

create table organization (id bigserial primary key, name_fa text, name_en text);
create table site (id bigserial primary key, org_id bigint references organization, name_fa text, name_en text,
  industry_group text, status text, climate_zone text, lat numeric, lon numeric,
  calendar_pref text default 'jalali' check (calendar_pref in ('jalali','gregorian')), lang_pref text default 'fa');
create table unit (id bigserial primary key, site_id bigint not null references site, parent_id bigint references unit,
  name_fa text, name_en text, unit_type text);                       -- process unit or service area (accounting level 2)

-- reference tables (extensible)
create table ref_stream_type (code text primary key, name_fa text, name_en text, is_user boolean default false);
create table ref_equipment (code text primary key, name_fa text, name_en text, system_code text, roles text[], in_streams text[], out_streams text[],
  params text[], review_status text, is_user boolean default false, owner_site_id bigint references site);
create table ref_parameter (code text primary key, name_fa text, name_en text, unit text);

-- plant model: nodes (accounting level 1-3) and typed streams (edges)
create table node (id bigserial primary key, site_id bigint not null references site, unit_id bigint references unit,
  kind text not null check (kind in ('source','storage','equipment','junction','boundary')), equipment_code text references ref_equipment,
  name text, consumption_class text, required_basis text);          -- class/basis feed 'beneficial use' (FRM-03-013)
create table stream (id bigserial primary key, site_id bigint not null references site, from_node bigint references node, to_node bigint references node,
  stream_type text not null references ref_stream_type, permitted_use text[], recycle_status text, origin_note text,
  check (from_node is not null or to_node is not null));

-- measurement points and time series
create table meter (id bigserial primary key, site_id bigint not null references site, node_id bigint references node, stream_id bigint references stream,
  parameter text not null references ref_parameter, accuracy_rel numeric, measure_method text,   -- accuracy feeds uncertainty (FRM-01-010)
  check (node_id is not null or stream_id is not null));
create table import_batch (id bigserial primary key, site_id bigint references site, channel text check (channel in ('manual','file','api','gateway')),
  created_at timestamptz default now(), created_by bigint, status text default 'staged');
create table reading (meter_id bigint not null references meter, ts_utc timestamptz not null, value double precision,
  quality text not null default 'valid' check (quality in ('valid','estimated','suspect','invalid','missing')),
  batch_id bigint references import_batch, primary key (meter_id, ts_utc));  -- partition by time for daily data later

-- binding of formula variables to the plant model, and engine results
create table formula_binding (id bigserial primary key, site_id bigint not null references site, formula_id text not null, var_symbol text not null,
  meter_id bigint references meter, node_id bigint references node, constant_value numeric, note text);
create table calc_result (id bigserial primary key, site_id bigint not null references site, formula_id text not null, node_id bigint references node, stream_id bigint references stream,
  period_start timestamptz, period_end timestamptz, value double precision, uncertainty double precision, data_quality text, calc_version text, created_at timestamptz default now());
create table kpi_setting (site_id bigint references site, kpi_id text, node_id bigint references node, target numeric, warning numeric, critical numeric,
  primary key (site_id, kpi_id, node_id));                          -- thresholds live per plant, never in the shared bank

-- management cycle: diagnose -> opportunity -> evaluate -> implement -> verify
create table case_file (id bigserial primary key, site_id bigint not null references site, node_id bigint references node,
  kind text check (kind in ('alert','inspection','opportunity','project','verification')), status text default 'open', title text,
  opened_at timestamptz default now(), source_result_id bigint references calc_result, parent_case bigint references case_file);
create table economic_run (id bigserial primary key, case_id bigint references case_file, inputs jsonb, results jsonb, sensitivity jsonb, monte_carlo jsonb);

-- governance
create table app_user (id bigserial primary key, org_id bigint references organization, name text, role text check (role in ('operator','expert','manager','admin')));
create table audit_log (id bigserial primary key, at timestamptz default now(), user_id bigint, entity text, entity_id text, action text, detail jsonb);
create index on reading (ts_utc);
create index on stream (from_node); create index on stream (to_node);
create index on calc_result (site_id, formula_id, period_start);
