{# dlt creates a table only when it has rows. Until the first release exists, fall back to a typed empty relation. #}
{% macro source_or_empty(source_name, table_name, empty_select) %}
    {%- set rel = adapter.get_relation(database=target.database, schema=source(source_name, table_name).schema, identifier=table_name) -%}
    {%- if rel is not none -%}
        select * from {{ source(source_name, table_name) }}
    {%- else -%}
        {{ empty_select }}
    {%- endif -%}
{% endmacro %}
