BEGIN;

INSERT INTO strategic_indicators.department_indicators (
    indicator_id,
    department_id,
    indicator_name,
    weight_pct,
    scope_type,
    performance_direction,
    strategic_description,
    source_key,
    value_unit,
    value_prefix,
    value_suffix,
    value_decimals,
    is_active,
    display_order
)
VALUES
(
    'quality-ppm-internal-plugs',
    'quality',
    'PPM Interno Plugues',
    0.00,
    'per_unit',
    'lower_is_better',
    'PPM interno para plugues (produtos acabados com código iniciado em 9048).',
    'quality_ppm_internal_plugs',
    'ppm',
    NULL,
    'PPM',
    2,
    TRUE,
    6
),
(
    'quality-ppm-external-plugs',
    'quality',
    'PPM Externo Plugues',
    0.00,
    'per_unit',
    'lower_is_better',
    'PPM externo plugues (produtos acabados com código iniciado em 9048).',
    'quality_ppm_external_plugs',
    'ppm',
    NULL,
    'PPM',
    2,
    TRUE,
    7
)
ON CONFLICT (indicator_id) DO NOTHING;

COMMIT;
