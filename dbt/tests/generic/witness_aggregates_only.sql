{#- Guard for docs/adr/0003-witness-aggregates-only.md.
    Attach to every WITNESS-sourced model. Fails (returns one row per offending column) when the model has any
    column outside var('witness_allowed_columns'). Columns that look like voter or ballot identifiers are
    reported with a clearer reason. -#}
{% test witness_aggregates_only(model) %}
{%- set allowed = var('witness_allowed_columns') -%}
{%- set suspicious = '(voter|ballot|participat|elector|member|user|session|receipt|token|credential|passkey|email|ip_?addr)' -%}
{%- if execute -%}
    {%- set cols = adapter.get_columns_in_relation(model) -%}
    {%- set bad = [] -%}
    {%- for c in cols if c.name | lower not in allowed -%}
        {%- do bad.append(c.name) -%}
    {%- endfor -%}
    {%- if bad | length > 0 %}
    select column_name,
           case when regexp_matches(lower(column_name), '{{ suspicious }}')
                then 'resembles a voter or ballot identifier'
                else 'not in witness_allowed_columns' end as reason
    from (values {% for b in bad %}('{{ b }}'){% if not loop.last %}, {% endif %}{% endfor %}) as t(column_name)
    {%- else %}
    select null as column_name, null as reason where false
    {%- endif %}
{%- else -%}
    select null as column_name, null as reason where false
{%- endif %}
{% endtest %}
