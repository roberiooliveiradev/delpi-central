# Consulta de CEP — contrato compartilhado (INT-CEP-01)

## 1. Ownership

| Papel | Serviço |
|---|---|
| Owner da integração externa | `api-delpi` |
| Consumer autorizado | `supplies-api` (BFF Portal Suprimentos) |
| Futuros consumidores | outros BFFs via credencial S2S própria + allowlist |
| Providers externos | ViaCEP (primário) → BrasilAPI v1 (fallback) |

O MFE nunca chama a `api-delpi` diretamente — sempre via seu BFF.

## 2. Contrato HTTP

`GET /addresses/postal-codes/{postal_code}`

- Autenticação: S2S individual (`X-Delpi-Service-Authorization`), cliente
  em `allowed_clients`. Sem bearer de serviço → `401 S2S_TOKEN_*`; cliente
  fora da allowlist → `403 S2S_CLIENT_DENIED`. Não há caminho de usuário
  direto e o token legado compartilhado não autoriza.
- Entrada: CEP com ou sem máscara — normalizado para 8 dígitos; inválido
  → `400`.
- Saída (`data` do envelope):

```json
{
  "postal_code": "01310100",
  "found": true,
  "street": "Avenida Paulista",
  "district": "Bela Vista",
  "city": "São Paulo",
  "state": "SP",
  "ibge_city_code": "3550308",
  "source": "viacep",
  "result_type": "street"
}
```

CEP geral de município (sem logradouro próprio):

```json
{
  "postal_code": "89120000",
  "found": true,
  "street": null,
  "district": null,
  "city": "Timbó",
  "state": "SC",
  "ibge_city_code": "4218202",
  "source": "brasilapi",
  "result_type": "municipality"
}
```

- `found=true` não implica rua/bairro — `result_type` distingue
  `street` de `municipality`; campos ausentes vêm `null`, nunca
  fabricados.
- `found=false` somente quando **todos** os providers responderam
  definitivamente que o CEP não existe.
- Erros: provider inacessível/timeout → `504`; erro HTTP/JSON inválido
  → `502`; indisponibilidade nunca é reportada como `found=false`.

## 3. Providers

- Ordem contratada: **ViaCEP** (retorna logradouro/bairro quando há) →
  **BrasilAPI v1** (base open-cep cobre CEPs gerais que o ViaCEP não tem —
  ex.: `89120000` Timbó/SC). BrasilAPI exige `User-Agent` próprio (403 sem).
- Timeout 6s por provider; sem retry indiscriminado; redirects externos
  não são seguidos; URL montada de constante de config + dígitos
  validados (anti-SSRF).
- `source` identifica o provider que respondeu.

## 4. Segurança

- S2S com audience dedicada, fail-closed; sem credenciais de provider;
  sem persistência do retorno; logs sanitizados (nunca CEP+payload
  completo juntos com identidade do usuário).
- Dados: endereço público de CEP — não é dado pessoal por si, mas a
  resposta não deve ser logada em detalhe junto ao solicitante.

## 5. Consumidores

- `supplies-api`: `GET /suppliers/postal-codes/<cep>` (rota pública do
  Portal preservada) consome este contrato via `DelpiS2SApiGateway` e
  mantém AuthZ `supplies.access` no contexto do usuário.
- Novos consumidores: adicionar o client à `allowed_clients` do router
  e credenciar o serviço no Keycloak — sem nova permission de UI/Core.

## 6. Limites

- CEP não comprova existência/titularidade do endereço.
- `ibge_city_code` é o IBGE de 7 dígitos do provider — **não** é o código
  CC2 do Protheus; a conciliação (5 últimos dígitos + UF, comprovada em
  DELPI) é regra do consumidor TOTVS e fica fora deste contrato.

## 7. Evidências

- Causa raiz R4.1: `89120000` ausente no ViaCEP, presente na BrasilAPI
  (base open-cep) — fallback introduzido.
- Testes: `tests/test_postal_address_lookup.py` (23 casos — cadeia,
  adapters, classificação de erro, regressão 89120000).
- Runtime: verificado em container `delpi-api-delpi` — ver seção de
  smoke do relatório de execução.
