# Mockup — Painel e navegação global

> **Último passo** — só fechar após mockups 01–10.

## Objetivo

Definir se (e como) substituir as **10 abas planas** por seções agrupadas, sem repetir os erros da implementação revertida.

## Wireframe — visão alvo (referência do Playbook 11)

```
┌─────────────────────────────────────────────────────────────┐
│ Administração — Minha DELPI Chat          [Atualizar] [Voltar]│
├─────────────────────────────────────────────────────────────┤
│ [Painel] [Curadoria ▼] [Agentes ▼] [Operação ▼] [Plataforma]│
├─────────────────────────────────────────────────────────────┤
│ Sub-abas (quando aplicável)                                  │
├─────────────────────────────────────────────────────────────┤
│ Conteúdo da aba ativa                                        │
└─────────────────────────────────────────────────────────────┘
```

## Regras obrigatórias na implementação futura

1. **Uma barra de navegação** — sem «Acesso direto» duplicando 10 pills.
2. **Deep link** estável por seção/sub-aba.
3. **RBAC** e **inteligência** em lugar único e previsível.
4. **Mobile:** sub-abas colapsáveis ou select, não duas barras horizontais.

## Critérios de aceite (global)

- [ ] Todas as funções das 10 abas legadas acessíveis.
- [ ] `npm run build` + smoke manual por seção.
- [ ] Redirects de URLs antigas documentados.

## Status

- [ ] Aguardando aprovação dos mockups 01–10.
