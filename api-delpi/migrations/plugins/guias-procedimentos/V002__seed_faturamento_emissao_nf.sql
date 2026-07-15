-- Guias e Procedimentos — seed Faturamento + emissão de NF (V002)
-- IDs estáveis para preservar slugs públicos atuais do MFE.

INSERT INTO guias_procedimentos.departments (
    id,
    name,
    slug,
    description,
    icon,
    active,
    order_index,
    created_by_name,
    updated_by_name
)
VALUES (
    '11111111-1111-4111-8111-111111111101',
    'Faturamento',
    'faturamento',
    'Procedimentos e orientações do setor de Faturamento.',
    'receipt',
    TRUE,
    1,
    'seed',
    'seed'
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO guias_procedimentos.procedures (
    id,
    department_id,
    title,
    slug,
    summary,
    content_html,
    status,
    reading_time_minutes,
    order_index,
    published_at,
    created_by_name,
    updated_by_name
)
VALUES (
    '11111111-1111-4111-8111-111111111102',
    '11111111-1111-4111-8111-111111111101',
    'Informações necessárias para solicitação de emissão de nota fiscal',
    'emissao-nota-fiscal',
    'O que reunir antes de solicitar a emissão: destinatário, itens, tipo de NF, transporte e pedido de compra.',
    $html$<p>Antes de solicitar a emissão de uma nota fiscal, reúna e confira todas as informações necessárias. Isso reduz correções, atrasos e devoluções da solicitação.</p>
<h2>Dados do destinatário</h2>
<ul>
<li>Se já estiver cadastrado, informar o código do cliente ou fornecedor.</li>
<li><strong>Se não estiver cadastrado, providenciar o cadastro antes da solicitação.</strong></li>
</ul>
<h2>Dados dos produtos ou serviços</h2>
<ul>
<li>Código do item.</li>
<li>Quantidade.</li>
<li>Valor unitário.</li>
<li><strong>Informar se haverá baixa de estoque.</strong></li>
<li><strong>Caso haja baixa de estoque, o material precisa estar no almoxarifado 01.</strong></li>
</ul>
<h2>Tipo de nota fiscal</h2>
<ul>
<li>Venda.</li>
<li>Devolução.</li>
<li>Amostra.</li>
<li>Remessa ou retorno de conserto.</li>
<li>Outros.</li>
</ul>
<h2>Transporte</h2>
<ul>
<li><strong>Informar a modalidade de transporte (CIF ou FOB).</strong></li>
<li>Transportadora.</li>
<li>Peso e volumes.</li>
</ul>
<h2>Informações adicionais</h2>
<ul>
<li><strong>Pedido de compra, quando existir.</strong></li>
</ul>
<h2>Checklist de conferência</h2>
<ul>
<li>Destinatário identificado ou cadastrado.</li>
<li>Código dos itens informado.</li>
<li>Quantidade e valor unitário conferidos.</li>
<li>Baixa de estoque definida.</li>
<li>Tipo de nota fiscal selecionado.</li>
<li>Modalidade de transporte informada.</li>
<li>Peso e volumes informados.</li>
<li>Pedido de compra anexado ou informado, quando existir.</li>
</ul>
<p>Em caso de dúvida sobre um caso específico, confirme as informações com o setor de Faturamento antes de enviar a solicitação.</p>$html$,
    'published',
    4,
    1,
    NOW(),
    'seed',
    'seed'
)
ON CONFLICT (slug) DO NOTHING;
