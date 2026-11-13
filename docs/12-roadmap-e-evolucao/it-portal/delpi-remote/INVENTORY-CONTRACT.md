# Delpi Remote | Contrato G1 de inventario de estacoes (planejado)

**Status em 13/11/2026:** G1-API e G1-UI implementados em codigo, AMBOS EM REVISAO e NAO implantados. A migration V009, rotas, tela e testes estao versionados, sem homologacao com Postgres real nem avaliacao de producao.

**Objetivo:** entregar primeiro cadastro e consultas sem qualquer controle de tela, shell, mouse, teclado, clipboard ou arquivos.

## Entidade nova, separada de servidores

`workstations` com `id UUID`, `seq BIGINT`, `name`, `hostname`, `unit_code`, `device_kind` (`desktop|notebook|mini_pc|workstation`), `ip_address` **opcional e nao identificador**, `department`, `location`, `responsible`, `operating_system`, `administrative_status`, `description`, `revision`, `archived_at/by`, `created_at/by`, `updated_at/by`.

- Codigo publico calculado a partir da sequencia: `PC-0001` (exemplo).
- Unicidade de cadastro ativo por `(unit_code, lower(hostname))` para evitar duplicidade operacional inicial; mudancas de hostname e colisao tratadas por revisao, nunca por merge automatico.
- Identidade S2S do **agente** fica em estrutura separada, vinculada ao UUID; IP/MAC/serial observado nao autorizam uma conexao.
- Observacoes tecnicas e inventario de hardware ficam em tabela(s) separada(s), com `observed_at`, `source`, `run_id` e protecao contra replays/futuros falsos.
- Setor/responsavel podem conter dados pessoais: acesso por perfis minimos, mascaramento e retencao a definir.
- Nunca persistir senha, token, chave privada, clipboard, shell history nem conteudo de arquivo.

## API v1 planejadada
- `GET /workstations`: busca, filtros unidade/tipo/status, `page/page_size` e ordenacao allowlisted, exige `computers.view`.
- `POST /workstations`: cadastro curado, exige `computers.view + computers.manage` e RBAC fresh.
- `GET /workstations/{id}`: detalhe, exige `computers.view`.
- `PUT /workstations/{id}`: edicao com `revision` otimista, RBAC fresh.
- `POST /workstations/{id}/archive` e `/restore`: preserva historico, RBAC fresh.
- Endpoint de coleta S2S apenas em G2, com scope proprio e binding por identidade. **Nenhuma rota de controle remoto no G1.**

## Frontend v1
- Menu `Computadores` so aparece com `can_view_computers`.
- Pagina de lista com busca, unidade, filtros, criacao/edicao se autorizado; detalhe com dados curados e situacao de observacoes quando G2 existir.
- Estados de carregamento/vazio/offline/erro e acessibilidade padrao do `plugin-ui`.
- Nao mostrar botao `Conectar` funcional nesta etapa.

## Gates de testes
1. Sem `computers.view`, API responde 403 e UI nao mostra inventario.
2. `computers.manage` sem `computers.view` nao permite gravar.
3. Revogacao no Core antes da escrita gera 403; Core indisponivel gera 503 sem gravacao.
4. Hostname normalizado e nao duplicado; IP invalido e secrets em texto livre sao rejeitados.
5. Concorrencia otimista e historico nao permitem perda silenciosa.
6. Leitura de servidores, agentes e SCM existentes continuam intactos.
7. Migration e rollback operacional documentados; nao editar V001...V008.

**Nota:** especificacao e contrato propostos; ainda nao corresponde a rotas disponiveis no backend.

## Proxima evolucao planejada: G1-OWNER (vinculo ao usuario do Core)

O campo `responsible` atual e texto livre. Depois de homologar o G1, desenvolver um campo de busca e selecao de **colaborador usuario da Minha DELPI**, persistindo referencia estavel ao usuario no Core (ID, nao o nome digitado).

- Ver [G1-OWNER.md](G1-OWNER.md) para regras, migracao futura, tratamento de contas inativas, seguranca, API e criterios de aceite.
- O **responsavel de uso** do ativo (colaborador a quem o computador foi atribuido) e diferente do **administrador de TI** com permissao para gerenciar/assistir a maquina. O vinculo de propriedade nao outorga acesso remoto.
- Nenhuma mudanca na tabela, na API ou nas permissoes foi executada neste pedido de roadmap.
