# Prompt para o Cursor — UI review, U10 (desempenho da BFF e testes por perfil)

```text
PROMPT CURSOR — UI REVIEW · U10 — /summary em 8,3 s (N+1 com conexão nova por consulta) e perfis HML

CONTEXTO
Revisão do Claude sobre U9 (15/11/2026): R4 aceito (página do usuário). R1 trouxe o carregamento
progressivo, mas /summary leva ≈8,3 s na análise 01–15/11 (315 notas, 159 ocorrências). R2 criou os
quatro usuários, mas o Playwright parou no consentimento LGPD do primeiro login. R3 deixou
color-contrast e button-name atribuídos ao host sem a lista de elementos.

CAUSA DO R1 (lida no código, HEAD 0182a1c6+)
1. N+1: application/entry_audit/service.py `_status()` (≈ linha 1237) chama
   `store.status_of(stable_key)` — uma consulta por linha. `summary()` chama `_status` duas vezes
   por ocorrência (pending e resolved); `_previous_kpis()` repete tudo para a análise anterior;
   `_filtered(..., status)` e a projeção pública das ocorrências também chamam por linha.
   São 7 chamadas de `_status(self._store` no serviço.
2. Conexão nova por consulta: infrastructure/entry_audit/postgres_store.py `_all()` (≈ linha 564)
   abre `plugins_db_connect()` a cada chamada. Resultado: centenas de conexões por requisição
   (≈ 2 × 159 + a análise anterior + rows/runs repetidos).
3. `_filtered()` chama `rows()` e `runs_of()` de novo em cada uso, dentro da mesma requisição.

R1 — corrigir
- `statuses_of(stable_keys)` em uma consulta (`WHERE stable_key = ANY(%s)`), ou LEFT JOIN do status
  na leitura das linhas; trocar todas as chamadas por linha pelo mapa.
- Dentro de uma requisição, ler `rows(kind)` e `runs_of` uma vez (memo local da chamada), sem cache
  entre requisições.
- `summary` calcula pending/resolved numa passada.
- Não trocar o gerenciamento de conexão da plataforma (`plugins_db_connect`) nesta etapa; se um pool
  for necessário, parar e propor (é decisão de plataforma).
- Teste que conta consultas por requisição (summary, breakdowns, occurrences) e trava o número
  (não cresce com a quantidade de linhas).
- Meta: /summary < 500 ms e KPIs visíveis < 1,5 s na análise 01–15/11 em HML; tabela antes/depois
  por requisição. Conferir as mesmas leituras pela CLARA (mesmo serviço).

R2 — perfis
O consentimento LGPD faz parte do primeiro acesso: o Playwright aceita o consentimento no primeiro
login de cada usuário de teste (passo do fluxo, uma vez) e segue. Se o aceite só puder ser feito por
API do Core, usar a API de HML com o próprio usuário. Depois rodar por perfil:
cf-access (sem Administração), cf-manage (com Administração; 403 some), cf-lnf (link do LNF),
cf-dre (experiência DRE), e um usuário sem LNF (sem o link).

R3 — acessibilidade
Listar os elementos de color-contrast e button-name (seletor, página, componente). Os que forem do
MFE: corrigir. Os do host/TopBar/plugin-ui: registrar com o componente dono, sem corrigir aqui.

REGRAS
As da trilha (main sem branch; git add só com caminhos explícitos; sem mudança de contrato, regra
ou permissão; HML antes de PROD; tag rollback-ui-review-u10-controllership-finance-api).
PROD: publicar a BFF e parar pedindo ao owner os prints (Início, entrada e análise 01–15/11 no
desktop e no celular) e o tempo que a análise levou para abrir.

REPORT
R1: causa confirmada, consultas por requisição antes/depois, tempos antes/depois. R2: resultado por
perfil. R3: lista e destino de cada violação. Atualizar track.md. Parar ao concluir.
```
