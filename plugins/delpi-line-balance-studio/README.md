# DELPI Line Balance Studio

**Decisão do Product Owner:** 2026-11-17 — ferramenta corporativa **greenfield**, independente e reutilizável no ecossistema Minha DELPI.  
**Status:** `AUTHORIZED / DESIGN_DOCUMENTED / IMPLEMENTATION_NOT_STARTED`. Este commit cria apenas documentação; não cria aplicação executável nem altera runtime.  
**Primeiro consumidor futuro:** Portal Engenharia > Processos > Balanceamento de Linha. Outros portais poderão importar a API pública futura.  
**Regra vinculante:** **NÃO** copiar, adaptar, extrair, portar, refatorar ou importar código, tipos, hooks, componentes específicos, algoritmos de UI, estado ou fluxo já desenvolvidos em `plugins/engineering` (inclusive páginas de Produto/Roteiro e Yamazumi V3). Essa implementação é legado isolado, deve permanecer intacta e **não** servir como blueprint nem fonte para prompts da implementação nova.

## Produto
Uma única ferramenta clean que permita escolher o método, criar estudos a partir de produto oficial (por adapter) **ou sem produto cadastrado**, editar operações, horários e pausas, atribuir operações a postos, visualizar gráficos Yamazumi, comparar cenários e exportar resultados explicitamente rotulados.

## Os seis métodos
| ID | Capacidade | Situação no Studio greenfield |
|---|---|---|
| M1 | Diagnóstico de capacidade e takt | TARGET; cálculo autorizado deve vir do domínio competente |
| M2 | FFD / Largest Candidate Rule | TARGET |
| M3 | Ranked Positional Weight (RPW) | TARGET |
| M4 | Kilbridge-Wester | TARGET |
| M5 | Yamazumi interativo | **PRIMEIRA IMPLEMENTAÇÃO** / TARGET |
| M6 | Dimensionamento de recursos e cenários | TARGET |

M5 é um instrumento visual, não um solver; M6 é família de análises, não um algoritmo único. O catálogo deve expor honestamente o estado de cada capacidade.

## Ownership e dependências permitidas
- **Studio:** experiência, editores, cenários, estados e API pública reutilizável. Sem import do Portal Engenharia.
- **`@delpi/plugin-ui`:** somente componentes genéricos públicos, design system, gráficos, tabelas, controles e exportações; não receber regras de balanceamento.
- **Domínio Engenharia/EVA:** owner dos cálculos, restrições de precedência, viabilidade e métodos matemáticos; sem algoritmos fabris dentro do kit UI.
- **API-DELPI/Domain APIs:** dados oficiais (routing/BOM/tempos) e contratos. O Studio não consulta banco nem internals de outro MFE.
- **Core/Keycloak/Portal:** autenticação, autorização e host; o Studio não guarda tokens e não define RBAC.
- **Engenharia:** aprovação/publicação de alterações técnicas. Todo cenário do Studio é `DRAFT/SIMULATION` até workflow governado.

O uso de contratos **oficiais externos** é permitido e necessário; a proibição diz respeito a reutilização da **implementação antiga**. Nenhuma biblioteca gráfica paralela a Plugin UI.

## Estrutura e documentos
- [docs/INDEX.md](docs/INDEX.md) — navegação dos contratos e especificações.
- `src/app/` — composição original do Studio;
- `src/model/` — estado e invariantes, sem framework;
- `src/ports/` — interfaces agnósticas de fontes, análise, storage e export;
- `src/methods/catalog/` e `src/methods/yamazumi/` — catálogo e primeira capacidade;
- `src/features/study-origin/`, `operation-editor/`, `shift-editor/`, `station-editor/`, `scenario-comparison/` — recursos separados;
- `src/ui/` — composição do Studio com Plugin UI;
- `tests/` — unit/contract/component/E2E.

As pastas de código acima são **layout alvo**, sem scaffold fictício. Pasta só passa a ter código quando houver implementação e testes.

## Primeira entrega técnica proposta
1. Criar modelo e API pública **do zero** no Studio.
2. Implementar origem manual e a origem oficial por adapter neutro, sem inferir autorização.
3. Editar operações/elementos de trabalho pela tabela e visualização sincronizadas.
4. Editar turnos por horários ou minutos e múltiplas pausas.
5. Implementar Yamazumi original com postos, atribuições, takt e cenários.
6. Integrar Portal Engenharia via API pública quando o Studio estiver isoladamente testado; manter tela antiga intacta até substituição governada, sem reutilizar seu código.
7. Validar e implantar conforme `AGENTS.md`, com Verify independente, HML→PROD e rollback.

**Status de evidência:** `DOCUMENTED / TEST_NOT_RUN`. Aprovação do produto não equivale aprovação de mudança de source of truth/owner/authority. Se isso ocorrer, devolver à Coordination.
