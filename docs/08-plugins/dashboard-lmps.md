# Minha DELPI — Plugin `dashboard-lmps`

> **Arquivo:** `docs/08-plugins/dashboard-lmps.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** plugin/microfrontend `dashboard-lmps`

---

## 1. Objetivo

Este documento descreve o plugin **`dashboard-lmps`** dentro da Minha DELPI.

O `dashboard-lmps` é um microfrontend de dashboard operacional relacionado ao acompanhamento de LMPs e dados operacionais de engenharia/fluxo.

---

## 2. Identidade conhecida

Identificador:

```text
dashboard-lmps
```

Container:

```text
delpi-dashboard-lmps
```

Serviço Docker:

```text
dashboard-lmps
```

Pasta esperada:

```text
plugins/dashboard-lmps
```

---

## 3. Papel arquitetural

O `dashboard-lmps` é um plugin frontend/microfrontend.

Ele é construído no Compose a partir de:

```yaml
build:
  context: ../plugins/dashboard-lmps
  dockerfile: Dockerfile
```

Em desenvolvimento, o Compose monta:

```yaml
volumes:
  - ../plugins/dashboard-lmps:/app
  - /app/node_modules
```

O Gateway depende desse serviço no Compose informado.

---

## 4. Tipo de plugin

Tipo esperado:

```text
microfrontend
```

Renderização esperada:

```text
federated
```

O padrão oficial para microfrontends federados usa:

```text
/apps/<plugin>/assets/remoteEntry.js
```

Logo, o entry esperado é:

```text
/apps/dashboard-lmps/assets/remoteEntry.js
```

---

## 5. Manifesto de referência

Exemplo de manifesto documentado para `dashboard-lmps`:

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "description": "Dashboard analítico de LMPs",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/apps/dashboard-lmps",
  "entry": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "dashboard-lmps.view",
      "name": "Acesso ao dashboard LMPs",
      "module": "dashboard-lmps"
    }
  ],
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.view",
      "order": 1,
      "showInMenu": true
    }
  ],
  "ui": {
    "renderMode": "federated"
  }
}
```

> Há documentos antigos com variações de `basePath`, `entry` e permission code. O padrão atual recomendado para microfrontends federados é `/apps/<plugin>/assets/remoteEntry.js`.

---

## 6. Permissões

Permissões documentadas em exemplos:

```text
dashboard-lmps.view
dashboard-lmps.access
dashboard-lmps.read
```

Ponto de atenção:

> Antes de registrar ou atualizar o plugin, escolher e padronizar o permission code final no manifesto real. Evitar manter permissões equivalentes duplicadas para o mesmo acesso.

Sugestão de padronização:

```text
dashboard-lmps.access
```

ou:

```text
dashboard-lmps.view
```

A escolha deve refletir o padrão adotado nos manifests reais já registrados.

---

## 7. Rota principal

Rota pública esperada:

```text
/apps/dashboard-lmps
```

Essa rota deve estar alinhada com:

```text
basePath
routes[].path
Gateway
Portal
```

---

## 8. Integração com dados LMP

A documentação da rota LMP indica evolução na modelagem de dados de LMP, especialmente:

- LMP definida por processo + estágio;
- AC2010 como tabela de verdade para interpretar stages;
- histórico AIJ010 lido com revisão e processo;
- status atual baseado na última revisão;
- tempo em andamento contado até o momento atual;
- separação entre estágio definidor de LMP e apoio de engenharia.

Esses pontos indicam que o dashboard deve consumir dados operacionais preparados pela API DELPI ou rota operacional equivalente, e não recriar a regra no frontend.

---

## 9. Responsabilidade do frontend

O plugin deve:

- exibir indicadores;
- consumir APIs documentadas;
- renderizar filtros e gráficos;
- respeitar estado de loading/erro;
- receber contexto do Portal quando necessário.

O plugin não deve:

- conter regra de negócio crítica de LMP;
- consultar banco diretamente;
- calcular autorização final;
- hardcodar token;
- duplicar lógica de status que pertence ao backend.

---

## 10. Responsabilidade do backend operacional

A API consumida pelo dashboard deve:

- calcular regra de LMP;
- consultar TOTVS ou datasource operacional;
- aplicar filtros;
- fornecer dados agregados;
- validar JWT/permissões se protegido;
- paginar quando necessário;
- documentar resposta.

---

## 11. Testes essenciais do microfrontend

Testes obrigatórios:

```text
GET http://localhost/apps/dashboard-lmps/assets/remoteEntry.js
```

Resultado esperado:

```text
JavaScript
```

Não deve retornar HTML.

Também validar:

- mount/unmount;
- base pública do Vite;
- cache do `remoteEntry.js`;
- assets hashados;
- menu dinâmico via `/me/apps`.

---

## 12. Checklist técnico

- [ ] Confirmar manifesto real.
- [ ] Confirmar permission code final.
- [ ] Confirmar `basePath=/apps/dashboard-lmps`.
- [ ] Confirmar `entry=/apps/dashboard-lmps/assets/remoteEntry.js`.
- [ ] Confirmar rota principal.
- [ ] Confirmar APIs consumidas.
- [ ] Confirmar regra LMP no backend, não no frontend.
- [ ] Confirmar Gateway.
- [ ] Confirmar build Module Federation.
- [ ] Confirmar carregamento no Portal.

---

## 13. Pendências

Dependem de leitura dos arquivos reais do plugin:

- telas atuais;
- componentes;
- filtros disponíveis;
- gráficos/KPIs;
- chamadas HTTP;
- contrato de resposta da API;
- manifesto final usado no registro.

---

## 14. Pontos de atenção

1. Há variações antigas de manifesto nos documentos.
2. O padrão atual de entry deve ser `/apps/dashboard-lmps/assets/remoteEntry.js`.
3. Regra de LMP deve ficar no backend operacional.
4. O frontend deve apenas consumir e apresentar dados.
5. Permissões devem ser padronizadas antes do registro final.
6. O Gateway deve servir corretamente `remoteEntry.js`.

---

## Referências internas

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
