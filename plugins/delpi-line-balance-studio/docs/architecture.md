# Arquitetura — Studio reutilizável

**Status:** TARGET / APPROVED_PRODUCT_DIRECTION / NOT_IMPLEMENTED. **Owner da composição da ferramenta:** DELPI Line Balance Studio; **owner de domínio:** Engenharia/EVA; **owner de componentes genéricos:** Plugin UI.

## Diagrama de dependências alvo
```text
Portal Engenharia (primeiro consumidor)  Outros consumidores futuros
           |                                      |
           +------------ API pública Studio -------+
                               |
                   DELPI Line Balance Studio
         workflow / study state / método / editores / Yamazumi
                 |               |             |
             Ports de dados  Port de análise  Port de armazenamento
                 |               |             |
      Adapter do host      Engineering domain   session adapter
      (API autorizada)    / contratos oficiais   do consumidor
                               |
                     @delpi/plugin-ui (componentes visuais)
```

**Importante:** Plugin UI **não fica abaixo do domínio**; é dependência exclusiva da apresentação. Domínio/Application não dependem de React, Recharts, SDKs, HTTP, MFE ou banco.

## Bounded ownership
| Item | Owner | Pode fazer | Não pode fazer |
|---|---|---|---|
| Studio | Produto ferramenta reutilizável | Orquestrar workflow e estado local do estudo | Publicar roteiro oficial, autorizar ERP |
| Plugin UI | Kit UI corporativo | Expor controles e gráficos agnósticos | Regras de takt, precedência ou viabilidade |
| Engenharia/EVA domínio | Motor determinístico | Cálculos, restrições, metadados de método | Alterar cadastro alheio sem workflow governado |
| API-DELPI | Dados oficiais | Roteiro/BOM/tempo autorizado | Ser substituída por cache ou prompt |
| Core/Keycloak | RBAC/SSO | Decidir acesso vivo | Confiar em campo de frontend como autorização |
| Portal Engenharia | Consumer inicial | Adaptar origem oficial e navegar | Ser importado como runtime pelo Studio |

## Abstraction Gate da primeira implementação
- **Consumidores reais?** Portal Engenharia PROVEN, demais TARGET.
- **Equivalente existente?** `LineBalancingPage.tsx`, `yamazumi.ts`, `methodCatalog.ts`, `PostConfigurator`, `@delpi/plugin-ui`: inventariar, **extrair** em vez de copiar.
- **Escopo do novo pacote?** Composição de ferramenta, não novo owner de algoritmo.
- **Modo de distribuição?** A selecionar após inventariar `plugins/shared-libraries.manifest.json`, federated remotes e build. Não adicionar entrada especulativa ao manifest.
- **Contrato público?** Tipado, com versão e compatibilidade, evitando import em internals.
- **Rollback?** Portal Engenharia continua funcional antes/depois da troca por integração reversível.

## Invariantes
1. Oficial `OBSERVED` é imutável na fonte; manual `PROVIDED/DRAFT_LOCAL`; resultados `CALCULATED`; hipóteses `SIMULATION`.
2. `POST /v1/products/{code}/line-balance` atual **não** calcula alocação validada de operadores/postos avançados.
3. `CT != posto != operador != equipamento`; precedências requerem grafo definido.
4. Leitura tem live AuthZ; Studio não interpreta JWT nem mantém tokens.
5. Sem import relativo de `plugins/engineering/src/features/products` dentro do Studio.
6. Plugin UI recebe extensão apenas quando o comportamento é realmente genérico.
7. Mudança de owner, source of truth, bounded context ou authority permanece `ARCHITECTURE_DECISION_REQUIRED`.

## Modo não-produto
Processos criados do zero não possuem SKU oficial e não podem invocar endpoint `products/{code}` com código falso. Análise determinística desses estudos requer contrato próprio no owner de domínio; UI pode montar e visualizar um rascunho com limitações explícitas sem prometer cálculo oficial.
