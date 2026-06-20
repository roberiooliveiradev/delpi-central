# Minha DELPI — Plugin `strategic-indicators`

> **Arquivo:** `docs/08-plugins/strategic-indicators.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** plugin/microfrontend `strategic-indicators`

---

## 1. Objetivo

Este documento registra o estado conhecido do plugin **`strategic-indicators`** dentro da Minha DELPI.

A documentação considera somente informações confirmadas nos arquivos enviados e padrões oficiais do Plugin System. Detalhes funcionais devem ser complementados após análise do código real do plugin.

---

## 2. Identidade conhecida

Identificador do plugin:

```text
strategic-indicators
```

Container:

```text
delpi-strategic-indicators
```

Serviço Docker:

```text
strategic-indicators
```

Pasta esperada:

```text
plugins/strategic-indicators
```

---

## 3. Papel arquitetural

O `strategic-indicators` é tratado na stack como plugin frontend/microfrontend.

Build no Compose:

```yaml
build:
  context: ../plugins/strategic-indicators
  dockerfile: Dockerfile
```

Volumes usados:

```yaml
volumes:
  - ../plugins/strategic-indicators:/app
  - /app/node_modules
```

No Compose informado, ele participa da rede:

```text
delpi-network
```

e também aparece como dependência do Gateway.

---

## 4. Tipo de plugin

Tipo esperado:

```text
microfrontend
```

Essa classificação deve ser confirmada no manifesto real.

O padrão oficial para microfrontends federados usa:

```text
/apps/<plugin>/assets/remoteEntry.js
```

Logo, o entry esperado para este plugin seria:

```text
/apps/strategic-indicators/assets/remoteEntry.js
```

---

## 5. Manifesto esperado

Manifesto esperado:

```text
plugins/strategic-indicators/delpi.manifest.json
```

Modelo mínimo de referência:

```json
{
  "schemaVersion": "1.0.0",
  "id": "strategic-indicators",
  "name": "Indicadores Estratégicos",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/apps/strategic-indicators",
  "entry": "/apps/strategic-indicators/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "strategic-indicators.access",
      "name": "Acessar Indicadores Estratégicos",
      "module": "strategic-indicators"
    }
  ],
  "routes": [
    {
      "path": "/apps/strategic-indicators",
      "label": "Indicadores Estratégicos",
      "permission": "strategic-indicators.access",
      "showInMenu": true,
      "order": 10
    }
  ],
  "ui": {
    "renderMode": "federated"
  }
}
```

> Esse modelo não substitui o manifesto real. Ele apenas registra o contrato esperado para o plugin.

---

## 6. Permissões

Permissão mínima esperada:

```text
strategic-indicators.access
```

Possíveis permissões futuras, se o plugin possuir múltiplas visões:

```text
strategic-indicators.view
strategic-indicators.admin
strategic-indicators.export
```

Essas permissões só devem ser adicionadas se existirem telas/ações reais que justifiquem granularidade.

---

## 7. Rotas

Rota principal esperada:

```text
/apps/strategic-indicators
```

O Plugin System exige que rotas estejam coerentes com `basePath`.

A rota só aparece no menu se a Core API retorná-la em `/me/apps`.

---

## 8. Integração com Portal

Fluxo esperado:

```text
Portal chama /me/apps
  ↓
Core API retorna strategic-indicators se usuário autorizado
  ↓
Portal exibe menu
  ↓
Usuário acessa rota
  ↓
Portal carrega entryUrl do plugin
```

O plugin não deve ser hardcoded no Portal.

---

## 9. Backend e dados

Não há arquivo de código real analisado que confirme quais APIs este plugin consome.

Possibilidades a confirmar:

- Core API;
- API DELPI;
- endpoints de indicadores;
- dados estáticos;
- fontes externas.

Nenhuma dessas fontes deve ser assumida sem confirmação no código.

---

## 10. Checklist técnico

- [ ] Confirmar manifesto real.
- [ ] Confirmar `id=strategic-indicators`.
- [ ] Confirmar `basePath`.
- [ ] Confirmar `entry`.
- [ ] Confirmar rotas.
- [ ] Confirmar permissões.
- [ ] Confirmar APIs consumidas.
- [ ] Confirmar tela principal e KPIs.
- [ ] Confirmar Gateway.
- [ ] Confirmar carregamento no Portal.

---

## 11. Pendências

Ainda dependem dos arquivos reais do plugin:

- descrição funcional;
- KPIs exibidos;
- chamadas HTTP;
- camada de estado;
- componentes principais;
- permissões finais;
- manifesto final;
- contratos de API consumidos.

---

## 12. Pontos de atenção

1. O plugin aparece no Compose e no Gateway.
2. A documentação funcional precisa do código real.
3. O entry deve seguir o padrão atual `/apps/<plugin>/assets/remoteEntry.js`.
4. O Portal deve consumir o plugin via `/me/apps`.
5. Permissões devem ser registradas via manifesto.
6. APIs operacionais devem validar JWT/permissões no backend.

---

## Referências internas

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
