{#- Every model that is tagged `witness` or reads a `witness` source must carry the witness_aggregates_only
    test. Reads the dbt graph, so a new WITNESS model without the guard fails the build. -#}
{%- if execute -%}
    {%- set guarded = [] -%}
    {%- for n in graph.nodes.values() if n.resource_type == 'test' and n.test_metadata is defined and n.test_metadata.name == 'witness_aggregates_only' -%}
        {%- do guarded.append(n.attached_node) -%}
    {%- endfor -%}
    {%- set unguarded = [] -%}
    {%- for n in graph.nodes.values() if n.resource_type == 'model' -%}
        {%- set from_witness = 'witness' in n.tags or (n.sources | selectattr(0, 'equalto', 'witness') | list | length > 0) -%}
        {%- if from_witness and n.unique_id not in guarded -%}
            {%- do unguarded.append(n.name) -%}
        {%- endif -%}
    {%- endfor -%}
    {%- if unguarded | length > 0 %}
    select model_name from (values {% for u in unguarded %}('{{ u }}'){% if not loop.last %}, {% endif %}{% endfor %}) as t(model_name)
    {%- else %}
    select null as model_name where false
    {%- endif %}
{%- else -%}
    select null as model_name where false
{%- endif %}
