-- Sequência de códigos PAC e registro no catálogo quality.submodules

INSERT INTO quality.document_sequences (
    sequence_key,
    prefix,
    current_value,
    padding_length,
    active
)
VALUES
    ('quality_action_plan', 'PAC', 0, 4, TRUE)
ON CONFLICT (sequence_key) DO NOTHING;

INSERT INTO quality.submodules (code, name, description, sort_order)
VALUES
    (
        'action_plans',
        'Planos de Ação PAC',
        'Planos de ação central de qualidade (PAC Qualidade DELPI).',
        50
    )
ON CONFLICT (code) DO NOTHING;
