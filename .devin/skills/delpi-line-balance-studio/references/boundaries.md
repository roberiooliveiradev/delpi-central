# Fronteiras — DELPI Line Balance Studio

**GREENFIELD obrigatório.** O Studio será código novo sob `plugins/delpi-line-balance-studio/`. A solução de Balanceamento/Yamazumi em `plugins/engineering` fica isolada, sem extrair, importar, copiar, adaptar ou modelar o novo produto a partir de seus internals.

**Reuso permitido:** `@delpi/plugin-ui` público e genérico; contratos oficiais independentes de API/domínio; autenticação/autorização governada pelo Core; padrões de infraestrutura e qualidade. O Studio deve ter API pública testável sem Portal Engenharia.

| Responsabilidade | Owner |
|---|---|
| Studio/workspace e estudo em rascunho | Produto DELPI Line Balance Studio |
| Controles, tabelas, chart, export genéricos | Plugin UI |
| Cálculo determinístico, métodos e restrições | Domain API Engenharia/EVA |
| Fonte oficial de produto/roteiro/BOM | API-DELPI |
| Identidade/SSO | Keycloak |
| RBAC/manifest/rotas | Core |
| Host / navegação | Portal de origem |
| Aprovação e publicação técnica | Owners Engenharia |

**M1–M6:** M1 capacidade e takt, M2 FFD/LCR, M3 RPW, M4 Kilbridge-Wester, M5 Yamazumi **visual**, M6 dimensionamento de recursos. Status e contrato por método. `Yamazumi != solver`; `CT != posto != operador != máquina`; tempos e precedências desconhecidos não podem ser inventados. Um manual sem SKU não pode chamar endpoint por produto com código falso.

**Governança:** agentes, instruções, MCP, JWT, UI e adapters não são autoridades; decisões de novo owner/source of truth/bounded context/authority exigem Coordination.
