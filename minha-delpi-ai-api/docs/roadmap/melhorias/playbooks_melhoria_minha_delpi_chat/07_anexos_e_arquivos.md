# Playbook 07 — Anexos e arquivos

> **Status (31/05/2026):** [Parcial — ver STATUS](./STATUS_ROADMAP_MELHORIAS.md) — indexação PDF/XLSX/CSV no upload, welcome automático, preview de colunas, `attachmentSummaries`; backlog: imagens, comparação multi-arquivo, UI status no composer.


## Objetivo

Definir como o Minha DELPI Chat IA deve lidar com arquivos anexados: PDFs, Word, Excel, CSV, JSON, imagens, datasheets, relatórios, documentos administrativos e planilhas.

O chat deve transformar anexos em conhecimento útil, sem exigir que o usuário copie tudo manualmente.

---

## Tipos de arquivo

- PDF.
- DOC/DOCX.
- XLS/XLSX.
- CSV.
- TXT/MD.
- JSON.
- PNG/JPG/WebP.
- Datasheets.
- Relatórios.
- Atas.
- Pedidos.
- Tabelas exportadas.
- Documentação técnica.

---

## Princípio central

> Quando houver anexo, o chat deve perguntar ou sugerir o que pode fazer com ele.

Exemplo após upload:

> Arquivo recebido. Posso resumir, revisar, traduzir, extrair pendências ou transformar em checklist.

Chips:

- Resumir.
- Corrigir.
- Traduzir.
- Extrair pendências.
- Criar checklist.
- Gerar ata.
- Comparar.

---

## Ações por tipo

## PDF/DOC

- Resumir.
- Corrigir texto.
- Traduzir.
- Extrair pendências.
- Criar ata.
- Criar comunicado.
- Identificar pontos principais.
- Gerar checklist.
- Criar resumo executivo.
- Extrair tabela.

## Excel/CSV

- Resumir dados.
- Mostrar colunas.
- Calcular totais.
- Encontrar inconsistências.
- Gerar gráfico.
- Filtrar.
- Agrupar.
- Exportar resultado.
- Comparar planilhas.

## JSON

- Explicar estrutura.
- Validar formato.
- Gerar tabela.
- Resumir campos.
- Encontrar chaves importantes.
- Transformar em documentação.

## Imagem

- Descrever conteúdo.
- Extrair informações visuais.
- Interpretar gráfico ou tabela, quando possível.
- Gerar texto alternativo.
- Sugerir melhorias visuais.

---

## Fluxo recomendado

1. Usuário anexa arquivo.
2. Front mostra chip do arquivo.
3. Backend registra anexo na sessão.
4. Chat responde com opções.
5. Usuário escolhe ação.
6. Sistema processa o arquivo.
7. Resposta traz resumo e próximos passos.

---

## Resposta ao anexar

```md
Arquivo recebido.

Posso ajudar com:
- resumo;
- correção;
- tradução;
- extração de pendências;
- transformação em checklist;
- análise dos dados;
- criação de relatório.
```

---

## Perguntas típicas

- Resuma esse arquivo.
- Extraia pendências.
- Transforme em ata.
- Traduza para inglês.
- Corrija o texto.
- Faça um resumo executivo.
- Identifique erros.
- Mostre os principais números.
- Gere um gráfico.
- Compare os arquivos.

---

## Anexos grandes

Se o arquivo for grande:

> O arquivo é extenso. Posso começar por um resumo geral e depois detalhar por seção.

Chips:

- Resumo geral.
- Por seção.
- Extrair pendências.
- Procurar termo específico.
- Criar checklist.

---

## Planilhas

## Resposta inicial ideal

```md
Analisei a estrutura da planilha.

Colunas encontradas:
- Produto
- Descrição
- Quantidade
- Valor

O que deseja fazer?
```

Chips:

- Resumir.
- Gerar gráfico.
- Encontrar inconsistências.
- Agrupar por produto.
- Exportar resultado.

---

## Datasheets

Para datasheets técnicos:

- extrair especificações;
- identificar tensão, corrente, temperatura;
- gerar descrição técnica;
- comparar com norma DELPI;
- criar checklist de cadastro;
- traduzir termos técnicos.

---

## Arquivos administrativos

Para atas, comunicados e e-mails:

- revisar;
- melhorar tom;
- criar versão curta;
- extrair pendências;
- gerar comunicado;
- traduzir.

---

## Comparação de arquivos

Usuário:

> Compare esses dois documentos.

Resposta ideal:

```md
## Semelhanças

## Diferenças

## Pontos de atenção

## Recomendações
```

---

## Segurança

O chat deve:

- respeitar permissões;
- não expor arquivo para quem não deve;
- não inventar conteúdo não encontrado;
- avisar quando não conseguiu ler parte do arquivo;
- tratar dados sensíveis com cuidado.

---

## Metadata recomendada

```json
{
  "attachments": [
    {
      "id": "uuid",
      "filename": "relatorio.xlsx",
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "sizeBytes": 12345,
      "parsed": true,
      "summary": "Planilha com dados de vendas."
    }
  ]
}
```

---

## UI recomendada

## No input

Mostrar chips:

- nome;
- tamanho;
- remover;
- status de leitura.

## Após upload

Mostrar cards:

- Resumir.
- Corrigir.
- Traduzir.
- Extrair dados.
- Criar relatório.

## Na resposta

Mostrar:

- nome do arquivo usado;
- se foi usado integralmente ou parcialmente;
- próximos passos.

---

## Testes

- PDF pequeno.
- PDF grande.
- DOCX.
- XLSX.
- CSV com separador `;`.
- JSON inválido.
- Imagem.
- Dois arquivos para comparação.
- Arquivo com tabela.
- Arquivo com texto técnico.
- Arquivo anexado + pergunta operacional.

---

## Métricas

- Arquivos anexados por tipo.
- Taxa de leitura bem-sucedida.
- Ações mais usadas.
- Feedback por tipo de arquivo.
- Tempo de processamento.
- Erros de parsing.
- Uso de anexos em respostas.

---

## Resumo executivo

Anexos tornam o chat muito mais útil. A melhoria principal é tratar arquivo como fonte ativa da conversa e oferecer ações claras: resumir, revisar, traduzir, extrair pendências, gerar checklist, analisar dados e transformar em documento.
