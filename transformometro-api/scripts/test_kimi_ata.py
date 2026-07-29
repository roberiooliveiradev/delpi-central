#!/usr/bin/env python3
"""
Script isolado — teste de geração de seções de ata via Kimi K3 (OpenAI-compatible).

Não altera rotas, banco nem serviços de produção.
Uso (a partir de transformometro-api/):

  cp .env.example .env   # preencha KIMI_API_KEY
  python scripts/test_kimi_ata.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # ambiente sem python-dotenv (ex.: apt só com python3-requests)
    def load_dotenv(dotenv_path: str | Path | None = None, **_: object) -> bool:
        path = Path(dotenv_path or ".env")
        if not path.is_file():
            return False
        parsed: dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key:
                parsed[key] = value  # última ocorrência no arquivo vence
        for key, value in parsed.items():
            if key not in os.environ:
                os.environ[key] = value
        return True

# Raiz do pacote transformometro-api (pai de scripts/)
_API_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_API_ROOT / ".env")

REQUIRED_KEYS = (
    "agenda_html",
    "body_html",
    "decisions_html",
    "pending_html",
    "observations_html",
)

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "moonshotai/kimi-k3"

SAMPLE_TRANSCRIPT = """
Reunião Transforma+ — Acompanhamento semanal de melhorias
Data: 28/07/2026 · Unidade 01 · Sala de projetos · 09:00–09:45

Participantes: Ana (facilitação), Bruno (produção), Carla (qualidade), Diego (engenharia).

Pauta:
1. Status das ações da semana anterior
2. Gargalo na linha de embalagem
3. Próximos passos e responsáveis

Discussão:
Ana abriu a reunião pedindo um resumo das ações abertas. Bruno informou que a ação
de calibração do sensor de temperatura foi concluída na sexta-feira e já está
operando em modo estável. Carla comentou que o indicador de retrabalho caiu 8%
na última semana, mas ainda há variação no turno da noite.

Sobre o gargalo na embalagem, Diego apresentou o diagnóstico preliminar: o tempo
de setup entre SKUs diferentes está em média 22 minutos, acima da meta de 12.
Bruno sugeriu padronizar o checklist de troca e treinar dois operadores-chave.
Carla pediu que o novo checklist seja validado pela qualidade antes do go-live.
O grupo concordou em pilotar a mudança na linha 2 por duas semanas.

Decisões:
- Aprovar piloto do checklist de troca de SKU na linha 2, com início na próxima segunda.
- Diego elabora a primeira versão do checklist até quarta-feira.
- Carla valida o documento até sexta-feira.
- Bruno agenda o treinamento dos operadores-chave para a semana seguinte.

Pendências:
- Diego: checklist de setup (prazo: quarta).
- Carla: validação qualidade (prazo: sexta).
- Bruno: agendar treinamento (após validação).
- Ana: incluir o piloto no dashboard Transforma+ na próxima reunião.

Observações:
Não houve discussão de investimento novo. Próxima reunião marcada para 04/08/2026
no mesmo horário. Ata a ser enviada para assinatura de Ana, Bruno, Carla e Diego.
""".strip()

SYSTEM_PROMPT = """
Você é um assistente que gera atas de reunião formais a partir de transcrições
do projeto Transforma+ / Transformômetro (Delpi).

Regras obrigatórias:
1. Responda APENAS com um único objeto JSON válido (sem markdown, sem texto fora do JSON).
2. O JSON deve conter EXATAMENTE estas chaves (todas strings HTML):
   - agenda_html
   - body_html
   - decisions_html
   - pending_html
   - observations_html
3. Use HTML simples adequado a um editor rich-text: <p>, <ul>, <ol>, <li>, <strong>, <em>, <br>.
   Não use scripts, estilos inline complexos, tabelas nem imagens.
4. agenda_html: pauta / assuntos tratados.
5. body_html: narrativa do andamento da reunião (discussão).
6. decisions_html: decisões tomadas.
7. pending_html: pendências e responsáveis/prazos quando houver.
8. observations_html: observações finais, próximos encontros, etc.
9. Se a transcrição não trouxer material para uma seção, use um parágrafo curto
   indicando que não houve itens relevantes (ainda assim a chave deve existir).
10. Escreva em português do Brasil, tom formal e objetivo.
""".strip()


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _print_section(title: str, html: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("-" * 72)
    print(html.strip() or "(vazio)")


def main() -> int:
    api_key = _env("KIMI_API_KEY")
    base_url = (_env("KIMI_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL).rstrip("/")
    model = _env("KIMI_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL

    if not api_key:
        print(
            "Erro: KIMI_API_KEY não definida.\n"
            f"Crie {_API_ROOT / '.env'} a partir de .env.example e preencha a chave.",
            file=sys.stderr,
        )
        return 1

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Gere a ata em JSON a partir da transcrição abaixo.\n\n"
                    f"{SAMPLE_TRANSCRIPT}"
                ),
            },
        ],
        "temperature": 0.2,
        "stream": False,
        # OpenAI-compatible / OpenRouter: força objeto JSON quando suportado
        "response_format": {"type": "json_object"},
    }

    print(f"POST {url}")
    print(f"model={model}")
    print("Enviando transcrição de exemplo…")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
    except requests.RequestException as exc:
        print(f"Erro de rede ao chamar o provedor: {exc}", file=sys.stderr)
        return 1

    if response.status_code >= 400:
        print(
            f"Chamada falhou: HTTP {response.status_code}\n"
            f"Corpo:\n{response.text}",
            file=sys.stderr,
        )
        return 1

    try:
        data = response.json()
    except ValueError:
        print(f"Resposta não é JSON válido:\n{response.text}", file=sys.stderr)
        return 1

    choices = data.get("choices") or []
    if not choices:
        print(f"Resposta sem choices:\n{json.dumps(data, ensure_ascii=False, indent=2)}", file=sys.stderr)
        return 1

    content = str((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        print("message.content vazio na resposta do modelo.", file=sys.stderr)
        return 1

    # Alguns provedores envolvem o JSON em fences ```json
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        sections = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"Falha ao parsear JSON do modelo: {exc}\nConteúdo:\n{content}", file=sys.stderr)
        return 1

    if not isinstance(sections, dict):
        print(f"JSON raiz não é objeto: {type(sections).__name__}", file=sys.stderr)
        return 1

    missing = [key for key in REQUIRED_KEYS if key not in sections]
    if missing:
        print(
            f"JSON incompleto — faltam chaves: {', '.join(missing)}\n"
            f"Recebido: {list(sections.keys())}",
            file=sys.stderr,
        )
        return 1

    print("\nOK — JSON com as 5 seções da ata.")
    for key in REQUIRED_KEYS:
        value = sections[key]
        if not isinstance(value, str):
            print(f"Aviso: {key} não é string (tipo={type(value).__name__}); convertendo.", file=sys.stderr)
            value = str(value)
        _print_section(key, value)

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
