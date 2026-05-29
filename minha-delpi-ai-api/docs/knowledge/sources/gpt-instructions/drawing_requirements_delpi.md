# 🧾 Requisitos Obrigatórios para Desenhos Técnicos DELPI

### _(Versão consolidada com base nas normas internas, análises de desenhos e integrações com API DELPI)_

---

## 🎯 **Objetivo**

Este documento define **tudo o que deve constar em um desenho técnico DELPI**, padronizando a **apresentação, formatação e conteúdo técnico** de acordo com:

-   As **Normas Técnicas DELPI**;
-   O **Drawing Analyser Instructions.md** (analisador de desenhos DELPI);
-   O documento **“Entendendo Código Intermediário no TOTVS e Desenhos”**;
-   As práticas consolidadas de análise via **API DELPI (SB1010, SG1010, SG2010, QP6–QP8)**.

O objetivo é garantir **coerência visual, técnica e documental** entre o desenho, o cadastro do produto e o fluxo produtivo no Protheus.

---

## 🧱 **1️⃣ Estrutura Geral do Desenho**

Cada desenho deve conter de forma obrigatória:

| Elemento                | Descrição                                              | Posição / Formato            |
| ----------------------- | ------------------------------------------------------ | ---------------------------- |
| **Formato da folha**    | A4 horizontal padrão                                   | Moldura com margens 10mm     |
| **Logotipo DELPI**      | Logotipo oficial no canto inferior direito             | Tamanho mínimo 30mm largura  |
| **Carimbo Técnico**     | Campos padronizados (ver seção 2)                      | Base inferior da folha       |
| **Tabela de Materiais** | Listagem de todos os componentes (BOM)                 | No canto inferior esquerdo   |
| **Vistas e projeções**  | Frontal, lateral, superior e isométrica (se aplicável) | Centralizadas e cotadas      |
| **Balões indicativos**  | Numeração dos componentes conforme BOM                 | Conectados por linhas finas  |
| **Escala**              | Escala real (1:1 ou 2:1) ou proporcional               | Indicar no carimbo           |
| **Unidade de medida**   | mm (milímetros)                                        | Indicar no carimbo           |
| **Revisão**             | Campo “REV.” no carimbo                                | Controlado via número e data |

---

## 🧾 **2️⃣ Carimbo Técnico Padrão DELPI**

O carimbo deve estar localizado na **base do desenho (lado direito)** e conter os seguintes campos obrigatórios:

| Campo                                 | Descrição                                   | Origem / Observação                                       |
| ------------------------------------- | ------------------------------------------- | --------------------------------------------------------- |
| **CÓDIGO DELPI**                      | Código do produto (ex.: 90264022, 50232155) | Deve existir no SB1010                                    |
| **DESCRIÇÃO**                         | Nome técnico completo                       | Conforme SB1010 ou estrutura intermediária                |
| **REVISÃO**                           | Nº da revisão e breve descrição             | Ex.: R01 – Ajuste de bitola                               |
| **CLIENTE**                           | Nome da empresa solicitante                 | Extraído do PDF ou cadastro SB1010                        |
| **CÓDIGO CLIENTE**                    | Código do cliente quando aplicável          | Campo complementar opcional                               |
| **EXECUTADO / VERIFICADO / LIBERADO** | Assinaturas ou iniciais responsáveis        | Padrão 3 níveis: desenhista / revisor / aprovação técnica |
| **DATA**                              | Data da revisão atual                       | dd/mm/aaaa                                                |
| **ESCALA**                            | Escala do desenho                           | Ex.: 1:1                                                  |
| **UNIDADE**                           | Unidade principal de medida                 | Sempre “mm”                                               |
| **LMP / LOCALIZAÇÃO**                 | Caminho interno (ex.: LMP-BUHLER/UL)        | Referência de origem                                      |

📘 _Referência: Drawing Analyser Instructions — seção “Verificação de Cabeçalho”._

---

## 🧩 **3️⃣ Tabela de Materiais (BOM)**

A tabela deve conter **todos os componentes estruturais** do produto, incluindo subconjuntos e itens de montagem, conforme a estrutura real (SG1010).

| Coluna                | Descrição                     | Exemplo                      |
| --------------------- | ----------------------------- | ---------------------------- |
| **Pos.**              | Posição de referência (balão) | 1, 2, 3…                     |
| **Código**            | Código interno DELPI          | 10080011                     |
| **Descrição Técnica** | Nome completo do item         | TERM. FASTON 6,3MM ESTANHADO |
| **Qtd.**              | Quantidade por montagem       | 2                            |
| **Unid.**             | Unidade de medida             | UN                           |
| **Obs.**              | Informação adicional          | Ex.: UL-ROHS, Compr. 255mm   |

📘 _Deve ser validada com a estrutura real via API: `/products/{code}/structure`_

---

## 📏 **4️⃣ Cotas, Dimensões e Tolerâncias**

Todos os desenhos devem apresentar **cotas legíveis e completas**, obedecendo os seguintes critérios:

| Item                         | Requisito                                                     | Observação                               |
| ---------------------------- | ------------------------------------------------------------- | ---------------------------------------- |
| **Cotas lineares**           | Todas as dimensões principais devem estar indicadas           | Comprimento total, decapes, espaçamentos |
| **Tolerâncias dimensionais** | Indicar conforme norma geral (±1mm ou conforme especificação) | Padrão DELPI                             |
| **Unidade padrão**           | Sempre “mm”                                                   | Declarar no carimbo                      |
| **Decape**                   | Medir e cotar ambos os lados (E/D)                            | Ex.: 06/06 mm                            |
| **Identificação de cabos**   | Cotas adicionais se houver múltiplas seções                   | Ex.: ramificações, derivações            |

📘 _Fontes: Drawing Analyser Instructions — seção “Análise Gráfica e Técnica” e Entendendo Código Intermediário (p.8–9)._

---

## 🎨 **5️⃣ Balões Indicativos e Identificação de Componentes**

-   Cada componente listado na BOM deve possuir **um balão numerado** no desenho;
-   Balões conectados por **linhas finas contínuas**, sem sobreposição;
-   Numeração deve coincidir com a **coluna “Pos.” da tabela**;
-   Em conjuntos elétricos, indicar **lado A e lado B**, conforme montagem;
-   Em cabos intermediários, indicar visualmente **decape e terminal isolado**.

📘 _Baseado em práticas de análise de chicotes e normas internas DELPI._

---

## 🧠 **6️⃣ Identificação do Produto e Código Intermediário (50xx)**

Todo desenho deve conter o **código completo do produto** e, quando aplicável, o **código do intermediário** (família 50xx) no corpo do desenho.

| Campo                            | Exemplo                                                                         | Observação                                  |
| -------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------- |
| **Código principal (SB1010)**    | 90264022                                                                        | Produto acabado ou conjunto                 |
| **Código intermediário (50xx)**  | 50232155 CB1,50VERD-00255/06/06–6314–0111                                       | Subconjunto de cabo com terminal e isolador |
| **Descrição técnica automática** | Gerada conforme documento “Entendendo Código Intermediário no TOTVS e Desenhos” | Deve constar na legenda lateral             |

📘 _Fundamentado no documento de intermediários (p.3–14) e Drawing Analyser Instructions._

---

## ⚙️ **7️⃣ Revisões e Histórico de Alterações**

-   Cada atualização de desenho deve gerar **nova revisão (R00 → R01 → R02...);**
-   Alterações devem ser descritas brevemente no campo “Descrição da Revisão”;
-   O histórico deve permanecer visível no rodapé ou legenda lateral;
-   Em revisões de adequação técnica, indicar **“REV. TÉCNICA – sem alteração dimensional”**.

📘 _Base: Normas Técnicas DELPI e Drawing Analyser Instructions — seção “Cabeçalho”._

---

## 🧰 **8️⃣ Simbologia, Textos e Legendas**

| Elemento                   | Requisito                                                       |
| -------------------------- | --------------------------------------------------------------- |
| **Fonte**                  | Arial Narrow ou Calibri, 2,5mm altura mínima                    |
| **Espessura de linha**     | 0,25mm (corpo) / 0,5mm (contorno)                               |
| **Setas e linhas de cota** | Padrão ISO 128, espaçamento 2mm                                 |
| **Notas técnicas**         | Inserir abaixo da tabela ou à direita da vista principal        |
| **Símbolos elétricos**     | Conforme padrão IEC / DELPI                                     |
| **Cores dos fios**         | Representar graficamente ou por legenda (VERD, AZUL, MARR etc.) |
| **Materiais UL / RoHS**    | Indicar na legenda quando aplicável                             |

📘 _Baseado em: Normas Técnicas DELPI — seção de formatação gráfica._

---

## 🔍 **9️⃣ Itens Complementares Obrigatórios**

| Item                   | Descrição                                                                |
| ---------------------- | ------------------------------------------------------------------------ |
| **Etiqueta UL ou QR**  | Indicação de rastreabilidade no desenho (campo técnico)                  |
| **Referência cruzada** | Número do arquivo LMP ou documento do cliente (quando aplicável)         |
| **Versão digital**     | Arquivo PDF em alta resolução e nome padronizado (ex.: 90264022_R01.pdf) |
| **Assinatura digital** | Campo de verificação no PDF final                                        |
| **Notas ambientais**   | Quando exigidas (RoHS, REACH, UL94)                                      |

📘 _Práticas derivadas de análises de produtos BUHLER, WEG e WANKE._

---

## 🧾 **🔟 Checklist Final de Conformidade do Desenho DELPI**

| Categoria                | Verificação                              | Status Esperado   |
| ------------------------ | ---------------------------------------- | ----------------- |
| **Cabeçalho**            | Código, revisão, cliente, assinatura     | ✅ Preenchido     |
| **Tabela BOM**           | Todos os componentes conferem com SG1010 | ✅ Coerente       |
| **Cotas e Decapes**      | Medidas legíveis e tolerâncias definidas | ✅ Corretas       |
| **Balões**               | Correspondência com tabela de materiais  | ✅ Correspondente |
| **Código Intermediário** | Formatação e descrição conforme norma    | ✅ Padronizado    |
| **Normas Técnicas**      | Referência às normas aplicáveis          | ✅ Citadas        |
| **Revisão**              | Campo e histórico atualizados            | ✅ Atualizado     |
| **Formato A4 e carimbo** | Conforme padrão DELPI                    | ✅ Ok             |
| **Legibilidade geral**   | Texto e dimensões legíveis               | ✅ Ok             |

---

## 📚 **Fontes de Referência**

-   **Drawing Analyser Instructions.md** — Análise técnica automatizada e integração API DELPI.
-   **Entendendo Código Intermediário no TOTVS e Desenhos.md** — Estrutura e formatação de produtos intermediários.
-   **Normas Técnicas DELPI.md** — Padrões gráficos, simbologia e conformidade de materiais.
-   **Checklist Revisão de Desenhos DELPI.xlsx** — Campos e validações obrigatórias.

---

### ✅ **Conclusão**

Este guia define o **modelo oficial para desenvolvimento, revisão e padronização dos desenhos DELPI**.  
Seu uso é **obrigatório** em todas as áreas de engenharia e controle de documentos, garantindo **padronização, rastreabilidade e integração completa com o Protheus (API DELPI)**.
