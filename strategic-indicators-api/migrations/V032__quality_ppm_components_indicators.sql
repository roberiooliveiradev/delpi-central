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
    'quality-ppm-internal-components',
    'quality',
    'PPM Interno Chicotes',
    0.00,
    'per_unit',
    'lower_is_better',
    'PPM interno para chicotes (produtos acabados com código iniciado em 9026).',
    'quality_ppm_internal_components',
    'ppm',
    NULL,
    'PPM',
    2,
    TRUE,
    8
),
(
    'quality-ppm-external-components',
    'quality',
    'PPM Externo Chicotes',
    0.00,
    'per_unit',
    'lower_is_better',
    'PPM externo chicotes (produtos acabados com código iniciado em 9026).',
    'quality_ppm_external_components',
    'ppm',
    NULL,
    'PPM',
    2,
    TRUE,
    9
)
ON CONFLICT (indicator_id) DO NOTHING;

COMMIT;
