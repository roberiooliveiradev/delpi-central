# Página 03 — Formulário Público para Responder Pesquisa

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: \`plugins/public-hub/README.md\`, \`src/shell/PublicShell.tsx\`, \`src/shell/types.ts\`, \`src/apps/customer-experience/{pages.tsx,FormPage.tsx,api.ts}\`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Responsabilidade e localização

**Uma página pública** em `plugins/public-hub`, caminho candidato **`/p/commercial/form/{token}`**, sem login do Portal/Keycloak e sem novos serviços ou MFE. Já existe `PublicShell`, roteamento por token e registro `publicRegistry`. A nova página será registrada em `src/shell/registry.ts` como `commercial.form` e consumirá **somente** os endpoints da `commercial-api` `GET /public/satisfaction-surveys/{token}` e `POST /public/satisfaction-surveys/{token}/response`. O gateway já encaminha `/p/` ao public-hub conforme README (validar no HEAD/deploy da execução).

**Não usar o formulário de Customer Experience como contrato de dados:** sua implementação atual em `FormPage.tsx` exige nome do respondente e usa tipos de formulário personalizável; a pesquisa DELPI é fixa, vinculada somente à **empresa convidada**. Reusar padrões visuais, shell e estados, **sem** importar lógica/endpoint/identificação pessoal indevidos.

## 2. Wireframe — abertura e formulário, desktop

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ DELPI                                                                     │
│ Pesquisa de Satisfação do Cliente                                         │
│ Sua avaliação ajuda a melhorar nossos produtos e serviços.               │
│ Prazo da pesquisa: [período quando permitido pela API]                    │
│ Aviso de finalidade/privacidade aprovado                                 │
│                                          [Iniciar pesquisa]                │
├───────────────────────────────────────────────────────────────────────────┤
│ AVALIAÇÃO DOS SERVIÇOS — 10 DIMENSÕES                                    │
│ Qualidade           [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Prazo de entrega    [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Atendimento         [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Agilidade           [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Comunicação         [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Suporte técnico     [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Suporte comercial   [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Flexibilidade       [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Confiabilidade      [1] [2] [3] [4] [5] [Não se aplica]                   │
│ Parceria            [1] [2] [3] [4] [5] [Não se aplica]                   │
├───────────────────────────────────────────────────────────────────────────┤
│ SATISFAÇÃO GERAL*                   [1] [2] [3] [4] [5]                  │
│ RECOMENDAÇÃO (NPS)*                [0] [1] [2] ... [9] [10]             │
├───────────────────────────────────────────────────────────────────────────┤
│ COMENTÁRIOS — opcionais                                                  │
│ Pontos fortes                [____________________________________]      │
│ O que melhorar               [____________________________________]      │
│ Necessidades não atendidas   [____________________________________]      │
│                                           [Revisar respostas]             │
└───────────────────────────────────────────────────────────────────────────┘
* Obrigatório. Texto integral e ordem vêm do plano/contrato oficial.
```

**A escolha de uma pergunta por página ou bloco único** deve favorecer legibilidade e menor custo de navegação. Recomendação atual: blocos de assunto na mesma página, com seção de revisão final, como acima; não forçar quinze etapas individuais porque a biblioteca suporta wizard.

## 3. Wireframe — revisão, envio e estados

```text
┌─ Revisar respostas ───────────────────────────────────────────────────────┐
│ 10 dimensões: notas/N.A. | Satisfação geral: 4 | NPS: 9                 │
│ Pontos fortes: ...  Melhorias: ...  Necessidades: ...                   │
│ Após confirmar, esta resposta NÃO poderá ser editada.                    │
│ [Voltar e corrigir]                     [Confirmar e enviar]            │
└───────────────────────────────────────────────────────────────────────────┘
                    ↓ POST atômico autorizado por token
┌─ Confirmação ─────────────────────────────────────────────────────────────┐
│ ✓ Obrigado por participar! Sua pesquisa foi registrada.                  │
│ Não há segunda resposta para a empresa nesta campanha.                   │
└───────────────────────────────────────────────────────────────────────────┘

Estados alternativos via backend:
[Campanha ainda não aberta] [Campanha encerrada]
[Resposta já registrada] [Link inválido/indisponível]
[Erro de conexão — tentar novamente com dados locais mantidos na sessão]
```

## 4. Inventário e escolha dos componentes visuais

| Região | Componente/fonte existente | Aplicação |
|---|---|---|
| Shell, branding, responsividade e estado de load | `PublicShell`, `PublicLoadingSplash`, `PublicFallback` | `plugins/public-hub/src/shell/*` já implementados; **não duplicar** |
| Página fullpage | `PublicPageDefinition` com `chrome: "fullpage"` | Registro em `src/shell/registry.ts` seguindo `customer-experience/pages.tsx` |
| Blocos/organização | Padrões visuais do `public-hub/src/apps/customer-experience/FormPage.tsx`/`form.css`; `SectionCard` do PluginUI **se compatível com o shell público** | Reusar estrutura/estilo existente; evitar importar CSS Comercial autenticado |
| Escalas e escolhas 1–5, N.A., NPS 0–10 | Componentes de controles de formulário **do PluginUI a confirmar no pacote exportado**; referência de comportamento de rating em `FormPage.tsx` | **TO_INVENTORY** para nomes exatos dos controles; não declarar que existe `RatingGroup` sem verificar |
| Três comentários | Campo de texto longo do kit PluginUI existente, **a conferir exports/uso público** | Não construir textarea estilizado novo |
| Ações e revisão | `ActionButton` do PluginUI se compatível; padrões de botões/confirm do formulário público existente | Componentes oficiais, sem modal próprio |
| Ilustrações ícones | `LucideIconByName` exportado por PluginUI | Já usado no formulário público do Customer Experience |
| Confirmação/erros | `PublicFallback` para falha inicial; feedback da view adaptado ao kit/padrão público | Diferenciar inválido, encerrado, enviado e conflito; não substituir tudo por 404 |

**Verificação importante:** o formulário público de referência usa JSX/HTML e CSS próprios; isso **não autoriza copiar seus elementos nativos estilizados** como componentes novos. Na implementação verificar as exportações e compatibilidade do PluginUI para cada campo, botão e grupo de escolha. Se faltar uma primitiva, registrar gap e aplicar Abstraction Gate, em vez de criar componentes exclusivos dentro da página. A semântica `form`, `label`, `fieldset` e `input` acessível pode ser usada como infraestrutura quando a biblioteca não fornecer encapsulamento, mas o visual deve vir da biblioteca/padrões existentes.

## 5. Regras de UX e validações

- **15 perguntas, mesma ordem/texto oficial do Word**: 10 dimensões 1–5 ou `Não se aplica`; satisfação geral 1–5 obrigatória; NPS 0–10 obrigatório; três abertas opcionais. O rascunho está **somente na memória do navegador** até o envio, sem API de salvar parcial.
- **Nunca perguntar nome, e-mail ou CPF do respondente.** A associação é à empresa pelo token gerado na campanha. Não expor código/loja, carteira, outros clientes nem dados internos.
- Revisão obrigatória antes do envio final; usuário pode voltar e corrigir antes de confirmar; após sucesso, imutável.
- Desabilitar múltiplos cliques enquanto POST estiver pendente, mas **não usar disable como única garantia**: banco/servidor controlam unicidade e janela. Resposta concorrente retorna estado “já registrada”, sem duplicar.
- Controles acessíveis pelo teclado, foco visível, legendas da escala, rótulos por dimensão, alternativa `Não se aplica` explícita, contraste e zoom. No celular, opções se acomodam sem rolagem horizontal excessiva; NPS deve ter alvos táteis adequados.
- Texto de privacidade/finalidade deve ser validado pelo responsável LGPD; não publicar uma declaração jurídica inventada. Sem analytics de terceiros ou propagação de token em logs/referer.
- Erro de rede mantém estado local para tentativa explícita, sem prometer que a resposta foi salva antes do commit.
- Sem edição das quinze perguntas no Portal e sem fluxo de envio de convites nesta página.

## 6. Contrato de rede / segurança

| Momento | Endpoint da commercial-api | Retorno seguro |
|---|---|---|
| Abrir link | `GET /public/satisfaction-surveys/{token}` | Perguntas oficiais/versionamento, estado da janela e informações mínimas necessárias |
| Confirmar envio | `POST /public/satisfaction-surveys/{token}/response` | Confirmação depois de persistir; conflito `already_submitted` sem vazar identidade |

`fetch` sem bearer/cookie interno; classe/cliente HTTP isolado em `plugins/public-hub/src/apps/commercial/api.ts`. A exceção pública no middleware da `commercial-api` deve ser delimitada estritamente a métodos/paths e validação de token, e o gateway precisa encaminhar os endpoints corretamente.

## 7. Critérios de aceite

1. Link gerado por Marketing abre via `/p/commercial/form/{token}` fora do Portal autenticado.
2. Textos, ordem e escalas exatas da fonte Word; revisão antes do POST.
3. Sem pedido de identificação pessoal; uma única resposta por empresa/campanha e estado “já respondido”.
4. Fuso/data no backend; link expirado/antes do período apresenta mensagem apropriada.
5. Erros de rede, formulário inválido e indisponibilidade de API não causam confirmação falsa.
6. Layout mobile/tablet/desktop, teclado, zoom, foco e leitores de tela; componentes e estilos do kit público reutilizados, sem componentes visuais nativos novos.
7. Token protegido, sem terceiros/telemetria/log e sem acesso de cliente a rotas internas.
8. Testes de frontend, backend público e concorrência; **nenhuma capability de submissão externa via CAIO**.

**Referências de execução:** `plugins/public-hub/src/shell/{routing.ts,registry.ts,PublicShell.tsx,types.ts}`, `src/apps/customer-experience/{pages.tsx,FormPage.tsx,api.ts}`, `commercial-api/commercial_app/middleware/auth_middleware.py`, `SURVEY-FIRST-RELEASE-CONTRACT.md`.