# 🧭 Normas de Representação e Regras Gráficas de Desenhos DELPI

### _(drawing_rules_DELPI.md – versão inicial consolidada com base em amostras reais e documentos técnicos)_

---

## 🎯 **Objetivo**

Este documento define as **regras de representação gráfica e simbologia** aplicáveis a todos os **desenhos técnicos DELPI**. Ele padroniza a forma como cabos, conectores, dimensões, notas técnicas, vistas e tabelas devem ser representados, garantindo **uniformidade visual e compatibilidade com os sistemas do Protheus (API DELPI)**.

Fontes de base:

-   _Requisitos Desenho DELPI.md_
-   _Drawing Analyser Instructions.md_
-   _Entendendo Código Intermediário no TOTVS e Desenhos.md_
-   Amostras de desenhos reais analisados (90264130, 90480106, 90263902, 90264116, 70260048, 90263188, etc.)

---

## 🧱 **1️⃣ Estrutura Gráfica Geral do Desenho**

| Item                 | Regra                                                                | Observações                                                            |
| -------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Formato de folha** | Padrão A4 horizontal ou vertical (210x297mm)                         | Margens: 10mm em todos os lados                                        |
| **Moldura**          | Deve conter letras (A–F) e números (1–8) para referência             | Exigido em todas as folhas                                             |
| **Logo DELPI**       | Inserido no canto inferior direito                                   | Tamanho ≥ 30mm largura                                                 |
| **Carimbo Técnico**  | Sempre localizado na base direita                                    | Campos: Código, Descrição, Cliente, Revisão, Execução, Liberação, Data |
| **Título principal** | Centralizado na parte superior                                       | Formato: “CHICOTE DE LIGAÇÃO / XXXXX”                                  |
| **Tabelas**          | Devem manter linhas visíveis, texto legível e altura mínima de 2,5mm | A fonte padrão é Arial Narrow                                          |

---

## 🧾 **2️⃣ Regras de Carimbo Técnico**

Campos obrigatórios e padrões de preenchimento:

| Campo                       | Padrão de Preenchimento                 | Observação                                   |
| --------------------------- | --------------------------------------- | -------------------------------------------- |
| **CÓDIGO DELPI**            | Ex.: 90264130                           | Código deve existir em SB1010                |
| **DESCRIÇÃO**               | Nome técnico completo do produto        | Evitar abreviações desnecessárias            |
| **CLIENTE**                 | Nome completo da empresa                | Ex.: “WEG INDÚSTRIA S.A. – LINHARES”         |
| **REV.**                    | Numeração sequencial (00, 01, 02...)    | “CRIAÇÃO DO DESENHO” na REV.00               |
| **EXECUTADO / LIBERADO**    | Assinaturas ou iniciais de responsáveis | Ex.: “GABRIELA / WILLIAM”                    |
| **LMP**                     | Código de projeto (ex.: 099/25)         | Campo obrigatório para rastreio              |
| **DATA**                    | dd/mm/aaaa                              | Deve refletir data da revisão                |
| **RESUMO DAS MODIFICAÇÕES** | Breve descrição (máx. 3 linhas)         | Ex.: “ALTERADO TERM. 10081073 PARA 10081585” |

---

## 🧩 **3️⃣ Tabela de Materiais (BOM)**

| Campo         | Regra                            | Exemplo                                  |
| ------------- | -------------------------------- | ---------------------------------------- |
| **Item**      | Numeração sequencial (A1, A2...) | Padrão alfanumérico conforme AutoCAD     |
| **Código**    | Código interno DELPI             | 10081073                                 |
| **Descrição** | Nome completo                    | TERM. TUBULAR 0,34MM² COMP 8MM ESTANHADO |
| **QTD.**      | Quantidade por montagem          | 2                                        |
| **Obs.**      | Incluir observações técnicas     | “UL-ROHS”, “Cabo PVC 105°C 750V”         |

---

## 📏 **4️⃣ Regras de Cotas e Dimensões**

| Regra           | Padrão                                               | Observação                                               |
| --------------- | ---------------------------------------------------- | -------------------------------------------------------- |
| **Unidade**     | Sempre milímetros (mm)                               | Indicar no canto inferior direito “MEDIDAS EM MILÍMETRO” |
| **Precisão**    | Usar ±1 ou ±2 mm conforme produto                    | Exemplo: “300±3”                                         |
| **Decape**      | Indicar ambos os lados: “10±1”                       | Usar setas e linhas finas vermelhas                      |
| **Comprimento** | Cota total principal destacada                       | Cor vermelha e setas simétricas                          |
| **Alinhamento** | Todas as cotas devem ser paralelas à vista principal | Evitar sobreposição de textos                            |
| **Simbolismo**  | Símbolos e letras de cota (A1, A2, etc.) em magenta  | Devem corresponder aos balões                            |

---

## 🎨 **5️⃣ Balões, Etiquetas e Conexões**

| Elemento                      | Regra                                                       | Exemplo                                 |
| ----------------------------- | ----------------------------------------------------------- | --------------------------------------- |
| **Balões indicativos**        | Letras maiúsculas + números (A1, A2...)                     | Cor magenta, linha de chamada fina      |
| **Etiquetas de fios**         | Devem estar **alinhadas aos terminais**                     | Ver exemplo: 90263188 – página 1        |
| **Cores de cabos**            | Nomeadas conforme código de cor (VERD, PRET, AZUL, AMAR)    | Ver Entendendo Código Intermediário p.6 |
| **Setas de referência**       | Usar traço contínuo e ponta fechada                         | Direção do fluxo do circuito            |
| **Identificação de lado A/B** | Inserir legenda textual “Lado A / Lado B”                   | Exemplo: 90480106                       |
| **Etiquetas múltiplas**       | Inserir nota: “Deixar etiquetas alinhadas com os terminais” | Exemplo: 90263188                       |

---

## 🧰 **6️⃣ Vistas, Cortes e Representações Especiais**

| Tipo de vista               | Requisitos                                                | Exemplo                     |
| --------------------------- | --------------------------------------------------------- | --------------------------- |
| **Principal**               | Exibir todo o conjunto em projeção ortogonal              |
| **Lateral / Detalhe**       | Usar escala ampliada (2:1 ou 4:1) para terminais pequenos |
| **Vista “X”**               | Identificar com texto “VISTA X” em vermelho               | Exemplo: 90264124           |
| **Cortes parciais**         | Hachura a 45° e legenda “CORTE AA” ou “BB”                |
| **Instruções fotográficas** | Podem ser adicionadas (formato JPG) na lateral direita    | Exemplo: 70260048, 70260033 |

---

## 🧠 **7️⃣ Notas Técnicas e Observações**

Regras para notas técnicas:

| Tipo                       | Padrão                                                                         | Exemplo           |
| -------------------------- | ------------------------------------------------------------------------------ | ----------------- |
| **Nota de montagem**       | Caixa de texto vermelha: “CONFERIR A ÚLTIMA PÁGINA PARA INSTRUÇÃO DE MONTAGEM” | Exemplo: 70260048 |
| **Nota de produção**       | Texto azul: “PRODUTO NOVO – FAVOR INFORMAR ENGENHARIA AO INICIAR PRODUÇÃO”     | Exemplo: 90264130 |
| **Nota de segurança / UL** | “COLAR ETIQUETA UL NA EMBALAGEM”                                               | Exemplo: 90264019 |
| **Nota de processo**       | “INSERIR ETIQUETAS ANTES DE CRIMPAR OS TERMINAIS”                              | Exemplo: 90263188 |

---

## 🧮 **8️⃣ Escalas e Textos**

| Elemento                 | Regra                                                                     |
| ------------------------ | ------------------------------------------------------------------------- |
| **Escala principal**     | 1:1 sempre que possível                                                   |
| **Fontes**               | Arial Narrow / Calibri, altura mínima 2,5mm                               |
| **Espessura de linha**   | 0,25mm padrão, 0,5mm contornos principais                                 |
| **Cor de texto técnico** | Preta (descrições), vermelha (cotas), magenta (referências), azul (notas) |
| **Caixa de texto**       | Bordas arredondadas para notas especiais                                  |

---

## 📚 **9️⃣ Referências e Cruzamentos Internos**

| Elemento                   | Regra                                              | Exemplo                         |
| -------------------------- | -------------------------------------------------- | ------------------------------- |
| **Contra Peça**            | Sempre indicar código da contraparte               | Ex.: “CONTRA PEÇA 90263713”     |
| **LMP**                    | Inserir referência cruzada com projeto             | Ex.: “LMP 099/25”               |
| **Referência de montagem** | Sempre que houver mais de um conector, identificar | Ex.: “CONECTOR 1/16” (90263902) |

---

## ✅ **🔟 Conclusão**

Estas regras formam a **base do padrão visual DELPI** e devem ser aplicadas em todos os desenhos, garantindo:

-   Clareza e legibilidade técnica;
-   Padronização entre clientes e produtos;
-   Alinhamento com as informações da API DELPI (Protheus);
-   Aderência às normas internas e externas (UL, NBR, IEC).

📘 _Atualização validada com base em amostras reais e normas internas até Novembro/2025._
