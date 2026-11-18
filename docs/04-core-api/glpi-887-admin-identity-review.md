# GLPI #887 - Etapa 2B: previa administrativa de identidade (somente leitura)

## Por que esta etapa existe

Auditoria do Portal RH em 18/11/2026 para o gestor de matricula textual `20001`:
- 63 colaboradores na hierarquia completa, ativos;
- 9 com `UserProfile.collaborator` unico e conta RH ativa (candidatos RH, **nao** Core confirmados);
- 54 sem associacao entre conta Django RH e colaborador;
- 0 vinculacoes RH -> Core executadas pela auditoria.

Nao concluir que os 54 colaboradores estao sem conta Minha Delpi. O modelo
`CollaboratorProfile` tem `personal_email`, mas e-mail pessoal **nao deve** ser
utilizado para inferir conta corporativa. O modelo `epi.Collaborator` recebe
`MATRICULA, NOME, FILIAL, ATIVO` da view Protheus; nao expõe `sub` do Keycloak.
A Core pode carregar um `users.id` historico diferente de `sub` por fallback
de email no middleware; nao pressupor igualdade para todas as contas.

## O que o endpoint faz

`GET /admin/organization/managers/{registration}/identity-review`

Paramêtros: `include_indirect=true|false` (padrao true) e
`details=true|false` (padrao false).

Exige **JWT do usuario + permissoes `rbac.manage` e `users.manage`** ou
superadmin. O token S2S genérico **nao** autoriza esta API. Retornos sem
credencial = 401; sem permissoes = 403; limite de 500 membros = 422.
A consulta é rate-limited, usa a hierarquia oficial RH via gateway S2S
ja existente e consulta somente as contas Core ativas.
Nao replica a hierarquia, nao faz migracoes e nao acessa Keycloak diretamente.

Padrao `details=false`: somente contagens, sem lista de colaboradores.
`details=true`: matricula textual exata, nome, filial, relacao e estado por
colaborador, com UUID Core vinculado ou UUID candidato quando apropriado.
Acesso **somente administrativo**, evitar colar a resposta detalhada em tickets.

Categorias:
- `verified_mapping`: matricula ja associada pelo `user_hr_registrations` a
  usuario Core ativo. Essa contagem reflete a verificacao administrativa
  registrada, nao uma nova confirmacao.
- `suggestion_by_name`: **sugestao fraca para revisao humana**, nunca associacao.
  Exige nome identico após normalizacao conservadora de espacos/case,
  somente uma ocorrencia RH e uma Core ativa, e Core ainda sem matricula.
- `ambiguous_rh_name`: mais de um membro nao vinculado com nome igual.
- `ambiguous_core_name`: mais de uma conta Core ativa com o mesmo nome.
- `already_assigned_to_other_registration`: Core com vinculo existente;
  bloqueado para evitar cruzamento.
- `no_exact_name_suggestion`: sem sugestao por nome; **nao significa sem conta**.

Nenhum resultado isolado, nem mesmo `suggestion_by_name`, autoriza gravar
uma identidade. Nome, e-mail e Protheus `SYS_USR` nao sao provas suficientes.
As nove contas vinculadas no RH ainda exigem confirmacao de identidade
com Core/Keycloak. A falta de `UserProfile.collaborator` em 54 pessoas
nao impede a gestao da hierarquia nem deve gerar cadastros em massa.

## Contrato de exemplo (dados ficticios)

```http
GET /admin/organization/managers/20001/identity-review?include_indirect=true
Authorization: Bearer <JWT_ADMIN>
```

Resposta reduzida exemplificativa:

```json
{
  "source": "portal-rh+core",
  "managerRegistration": "20001",
  "includeIndirect": true,
  "teamCount": 63,
  "statusCounts": {
    "verified_mapping": 0,
    "suggestion_by_name": 0,
    "ambiguous_rh_name": 0,
    "ambiguous_core_name": 0,
    "already_assigned_to_other_registration": 0,
    "no_exact_name_suggestion": 63
  },
  "verifiedCount": 0,
  "suggestionCount": 0,
  "readOnly": true,
  "automaticMappingsCreated": 0
}
```

Valores acima sao apenas ilustrativos e **nao** representam dados atuais
de producao Core. A previa nunca grava ou aprova vinculacoes.

## Processo de revisao e continuidade

1. Consultar agregados, verificar contas Core e revisar ambiguidades.
2. Apenas TI/RH autorizados consultam `details=true` e validam identidade
   com evidencias oficiais adicionais. Nao usar simples igualdade de nome/e-mail.
3. Vinculos aprovados individualmente usam o contrato admin existente
   `PUT /admin/organization/users/{uuid}/hr-registration` com
   `confirmIdentity=true`, auditado. **Este endpoint novo nao chama PUT.**
4. Depois, implementar agregacao semanal e acesso estritamente limitado
   pela propria hierarquia do gestor com a revisao LGPD concluida.
5. Nenhum relatorio nominal ou envio automatico e criado nesta PR.

## CI e publicacao

Testar no repositorio `delpi-central`:

```bash
cd core-api
pytest app/tests/test_portal_rh_organization.py app/tests/test_glpi_887_identity_review.py -q
```

Nao precisa de migration nem credenciais novas. **Nao aplicar deploy** nem
`git reset/clean/stash` no Portal RH de producao. As alteracoes locais do
Portal RH sao trabalho de desenvolvimento em uso e devem ser preservadas.
Para eventual deploy Core, verificar primeiro alteracoes locais e
usar somente o servico `core-api` conforme o playbook da stack.
