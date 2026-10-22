# Homologação Adeus Pendrive — DELPI News (Etapa 1)

> **Status:** procedimento preparado; validação em aparelho **PENDENTE** até execução presencial.  
> Testes unitários **não** substituem esta homologação.

## Pré-requisitos

1. Bundle do `public-hub` com demonstração habilitada:
   - ambiente de desenvolvimento (`npm run dev`), **ou**
   - build/homologação com `VITE_DELPI_NEWS_DEMO=1` no rebuild do `public-hub`.
2. Em produção padrão (sem a flag), a rota de demo deve responder **indisponível** (404 do shell).

## Endereço autorizado da demonstração

```text
https://<host-autorizado>/p/delpi-news/board/demo
```

- Token de demonstração: `demo` (não é credencial de produção).
- Token legado `aberto`: deve permanecer sem conteúdo.

## Checklist de aparelho

| Item | Como verificar | Resultado |
|---|---|---|
| Resolução utilizada | Anotar (alvo 1920×1080 / 16:9) | PENDENTE |
| Tela cheia | Abrir URL no navegador do Adeus; F11 ou modo kiosk do app | PENDENTE |
| Alternância automática | Observar progresso e troca de manchete no intervalo do board | PENDENTE |
| Legibilidade | Título e resumo legíveis a ~2–3 m | PENDENTE |
| Após atualizar a página (F5) | Board reinicia sem erro; banner de demonstração permanece | PENDENTE |
| Barras de rolagem | Ideal: sem scroll no viewport 16:9; anotar se houver | PENDENTE |
| Navegador / equipamento | Modelo Adeus + versão do WebView/Chrome | PENDENTE |
| Identificação de demo | Banner «DEMONSTRAÇÃO — conteúdo fictício…» visível | PENDENTE |

## Evidência

Anexar capturas ou notas em `docs/12-roadmap-e-evolucao/delpi-news/evidence/` quando a sessão presencial for executada.

## Declaração

Compatibilidade real com Adeus Pendrive **não** está declarada nesta revisão. Estado: **HOMOLOGACAO_PENDENTE**.
