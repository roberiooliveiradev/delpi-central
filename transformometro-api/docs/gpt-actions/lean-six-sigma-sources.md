# Lean Six Sigma — fontes e limites

Consulta em 2026-11-06. Este arquivo registra a origem do vocabulário.
Não reproduz normas, handbooks ou corpos de conhecimento protegidos.
O runtime canônico é `tm_app/application/methodology/lean_six_sigma.py`,
projetado em `teo-method-playbooks-v2`. A versão v1 não muda.

TÉO não certifica pessoas e não declara conformidade com ISO 13053-1
nem com ISO 18404.

| Fonte | O que foi usado | Limite |
|---|---|---|
| ASQ, “DMAIC”, https://asq.org/quality-resources/dmaic | Fases Define, Measure, Analyze, Improve, Control; charter, VOC, mapa, capability, Pareto, causa, FMEA, DOE, plano de controle, CEP, 5S, poka-yoke. DMAIC para processo existente; DMADV só como contraste, não implementado. | Página pública. Sem copiar o handbook citado na página. |
| ASQ, “Six Sigma Tools & Techniques”, https://asq.org/quality-resources/sixsigma/tools | DMAIC também como procedimento avulso; 5S; sete desperdícios; VSM em dois desenhos (atual e futuro); VOC. | Os sete desperdícios da página não incluem o oitavo (talento). O playbook Lean já existente não foi reescrito. |
| ISO 13053-1:2011, ficha https://www.iso.org/standard/52901.html | Nome das cinco fases e o fato de a norma cobrir manufatura e serviço. Edição 1, 2011-09, confirmada em 2022. 32 páginas. Texto não adquirido. | Nenhuma frase da norma foi copiada. Sem alegação de conformidade. |
| ISO 18404:2015, ficha https://www.iso.org/standard/62405.html | Existe um vocabulário de competências Six Sigma e Lean. Não consultado além da existência do título. | Sem certificação e sem cópia de requisitos de competência. |
| IASSC Yellow Belt Body of Knowledge, https://www.iassc.org/wp-content/uploads/2011/06/IASSC-Yellow-Belt-Body-of-Knowledge1.pdf | Só a decisão de tratar Yellow Belt como escopo de participação, não como método. | PDF de corpo de conhecimento não foi reproduzido. |
| IASSC Green Belt Body of Knowledge, https://iassc.org/body-of-knowledge/green-belt-body-of-knowledge/ | Só a decisão de tratar Green Belt como escopo de projeto DMAIC com julgamento estatístico básico. | Sem reproduzir o outline. |
| NIST/SEMATECH Engineering Statistics Handbook, https://www.nist.gov/programs-projects/nistsematech-engineering-statistics-handbook | Lembrete de que estabilidade, capacidade e análise de sistema de medição são assuntos distintos e exigem dados. | O handbook não foi copiado. Não há motor estatístico. |

Ferramentas novas consultáveis só em `guide_version=teo-method-playbooks-v2`:
`yellow_belt`, `green_belt`, `black_belt`, `dmaic`, `pdca`, `voc_ctq`,
`project_charter`, `vsm`, `pareto`, `five_s`, `defect_metrics`,
`descriptive_statistics`, `msa`, `process_capability`, `control_chart`,
`fmea`, `hypothesis_test`, `doe_intro`, `control_plan`.

SIPOC, Lean, Ishikawa, 5 Porquês, AS-IS, TO-BE, KPI e ponta a ponta
continuam sendo os playbooks v1. A família não cria processo, diagnóstico
nem medição paralelos: o registro segue as capabilities já autorizadas.
