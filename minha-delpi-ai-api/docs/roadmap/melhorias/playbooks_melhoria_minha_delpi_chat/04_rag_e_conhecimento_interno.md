# Playbook 04 — RAG e conhecimento interno

> **Status (31/05/2026):** [Parcial — ver STATUS](./STATUS_ROADMAP_MELHORIAS.md).


## Objetivo

Melhorar a qualidade das respostas baseadas em documentos, conhecimento interno, anexos e fontes da DELPI.

O RAG deve ajudar o chat a responder com base em documentação autorizada, sem inventar informações e sem misturar documentos irrelevantes.

---

## Problemas que este playbook resolve

- O chat responde sem base documental.
- O RAG retorna trecho irrelevante.
- O usuário pergunta sobre um processo e o chat consulta API operacional.
- Documentos técnicos aparecem em perguntas de identidade.
- O chat não cita fonte.
- O documento anexado não é usado.
- Respostas ficam longas demais.
- Conteúdo antigo ou duplicado confunde a resposta.

---

## Princípio central

> RAG deve trazer poucos trechos relevantes, com escopo correto, fonte visível e resposta fiel ao documento.

---

## Fontes possíveis

- Documentos globais.
- Documentos por agente.
- Documentos por projeto.
- Arquivos anexados à sessão.
- Artefatos.
- Knowledge operacional.
- Normas técnicas.
- Documentação da plataforma.
- Manuais internos.

---

## Escopo de busca

A busca deve considerar:

| Contexto | Fonte |
|---|---|
| Chat comum | knowledge global + anexos |
| Agente | knowledge do agente + global permitido |
| Projeto | fontes do projeto |
| Mensagem com anexo | anexos do turno/sessão |
| Pergunta técnica | normas e documentação técnica |
| Pergunta operacional | actions antes de RAG, se for dado real |

---

## Quando usar RAG

Usar RAG quando o usuário pergunta:

- como funciona um processo;
- o que diz uma norma;
- como usar uma funcionalidade;
- qual orientação interna existe;
- explique esse documento;
- resuma este arquivo;
- compare estes documentos;
- crie checklist a partir do manual;
- responda com base no arquivo anexado.

---

## Quando não usar RAG

Não usar RAG em:

- small talk;
- data/hora;
- identidade simples do assistente;
- capacidades fixas;
- consulta operacional com action clara;
- correção textual pura;
- tradução pura;
- pergunta que pode ser respondida com toolCalls recentes.

---

## Qualidade da recuperação

Cada chunk deve ter:

- fonte;
- título;
- trecho;
- score;
- escopo;
- data de atualização, se existir;
- categoria;
- agente/projeto associado.

---

## Regras de relevância

### Aceitar chunk quando

- contém termos principais da pergunta;
- pertence ao escopo correto;
- tem score acima do mínimo;
- é documento autorizado;
- é recente ou estável;
- responde diretamente.

### Rejeitar chunk quando

- só contém palavra genérica;
- pertence a outro agente/projeto;
- é norma técnica, mas pergunta é identidade;
- é documento antigo sem validade;
- repete trecho já selecionado;
- não tem relação com a pergunta.

---

## Prompt com RAG

O prompt deve dizer:

```md
Responda usando apenas o contexto documental autorizado quando a pergunta depender de fonte interna.
Se o contexto não for suficiente, diga que não encontrou base suficiente.
Não invente procedimentos, políticas, prazos ou regras.
Cite ou mencione a fonte de forma clara.
```

---

## Resposta com RAG

Formato recomendado:

```md
Com base na documentação encontrada:

## Resumo
...

## Detalhes
...

## Fonte usada
- [nome do documento]
```

Se não houver contexto:

```md
Não encontrei documentação relevante para essa pergunta.

Posso tentar:
- buscar com outros termos;
- consultar outro agente;
- usar um arquivo anexado;
- responder de forma geral, sem afirmar como regra interna.
```

---

## Anexos

Quando o usuário anexar arquivo:

1. Confirmar que o arquivo foi recebido.
2. Informar que pode resumir, revisar, traduzir ou extrair pendências.
3. Usar o anexo como fonte principal.
4. Se for grande, trabalhar por partes.
5. Não misturar com knowledge global sem necessidade.

---

## Perguntas com anexos

### Exemplos

- Resuma esse PDF.
- Extraia pendências desse documento.
- Corrija o texto desse arquivo.
- Traduza esse documento.
- Transforme em checklist.
- Compare esses dois arquivos.
- Gere ata a partir desse anexo.

---

## Chunking recomendado

Documentos longos devem ser divididos por:

- título;
- seção;
- subtítulo;
- parágrafo;
- tabela;
- lista;
- item de procedimento.

Evitar chunks muito grandes ou cortados no meio de uma regra.

---

## Metadados de documento

Cada documento deve ter:

```json
{
  "title": "Normas Técnicas DELPI",
  "category": "norma_tecnica",
  "department": "engenharia",
  "language": "pt-BR",
  "version": "2026-05",
  "owner": "engenharia",
  "validFrom": "2026-05-01",
  "tags": ["produto", "cadastro", "cabos"]
}
```

---

## Governança de knowledge

Criar processo:

1. Submissão do documento.
2. Validação por responsável.
3. Classificação.
4. Ingestão.
5. Teste de busca.
6. Publicação.
7. Revisão periódica.
8. Desativação de documento obsoleto.

---

## Testes de RAG

Criar bateria:

- pergunta respondida por documento;
- pergunta sem documento;
- pergunta com documento irrelevante;
- pergunta sobre anexo;
- pergunta sobre norma técnica;
- pergunta de identidade;
- pergunta operacional que não deve usar RAG;
- pergunta textual que não deve usar RAG;
- documento duplicado;
- documento antigo.

---

## Feedback específico

Adicionar motivos:

- Fonte errada.
- Fonte ausente.
- Documento antigo.
- Não encontrou documento.
- Misturou assuntos.
- Resposta inventou regra.
- Resposta longa demais.

---

## Métricas

- Taxa de resposta com fonte.
- Score médio dos chunks usados.
- Taxa de RAG sem resultado.
- Feedback “faltou fonte”.
- Feedback “fonte errada”.
- Tempo de busca.
- Documentos mais usados.
- Perguntas sem cobertura documental.

---

## Resumo executivo

RAG deve ser usado para conhecimento interno, não para tudo. A melhoria principal é controlar escopo, qualidade dos chunks, fontes citadas e fallback quando não houver documento suficiente.
