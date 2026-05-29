# ✅ Regras de Validação e Critérios de Conformidade de Desenhos DELPI
### _(validation_rules_DELPI.md – critérios automáticos de verificação e aprovação de desenhos técnicos DELPI)_

---

## 🎯 **Objetivo**

Definir as **regras automáticas de validação** aplicáveis a todos os desenhos técnicos DELPI, com base nas normas internas e na integração com o **sistema Protheus via API DELPI**.  

Essas regras são utilizadas pelo **Agente de Análise de Desenhos** para classificar cada item do desenho como:
- ✅ **Conforme**  → Atende ao padrão técnico e normativo;
- ⚠️ **Pendente** → Informação ausente, ilegível ou incompleta;
- ❌ **Não conforme** → Divergente das normas DELPI ou dos dados reais do Protheus.

---

## 🧾 **1️⃣ Estrutura de Validação Geral**

| Categoria | Descrição | Método de Verificação | Critério de Conformidade |
|------------|------------|------------------------|---------------------------|
| **Produto (SB1010)** | Confirma se o código do produto existe e está ativo | API `/products/{code}` | ✅ Cadastrado e ativo / ❌ Inexistente ou inativo |
| **Estrutura (SG1010)** | Confirma se todos os componentes estão no desenho | API `/products/{code}/structure` | ✅ Todos presentes / ⚠️ Componentes faltantes |
| **Roteiro (SG2010)** | Verifica se o roteiro existe e possui operação CT-99 | API `/products/{code}/guide` | ✅ Operações completas / ⚠️ CT-99 ausente |
| **Inspeções (QP6–QP8)** | Confere existência de inspeções vinculadas | API `/products/{code}/inspection` | ✅ Inspeções cadastradas / ⚠️ Ausentes |
| **Normas Técnicas** | Confere aderência ao grupo técnico correto | Base `Normas_Tecnicas_DELPI.md` | ✅ Grupo correto / ❌ Divergente |

---

## 🧱 **2️⃣ Cabeçalho e Carimbo Técnico**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Código DELPI** | Deve existir em SB1010 | ✅ Válido / ❌ Inexistente |
| **Descrição** | Deve ser idêntica à do sistema | ✅ Igual / ⚠️ Parcialmente divergente |
| **Cliente** | Nome completo e correto | ✅ Completo / ⚠️ Abreviado / ❌ Errado |
| **Revisão** | Sequencial e registrada | ✅ Numérica crescente / ❌ Falta ou fora de ordem |
| **Assinaturas** | Todos os campos preenchidos | ✅ 3 níveis preenchidos / ⚠️ Campo vazio |
| **Data** | Presente e válida | ✅ Formato dd/mm/aaaa / ⚠️ Faltante |
| **Resumo de modificações** | Descrição concisa da alteração | ✅ Presente / ⚠️ Ausente |

📘 *Referência: Requisitos Desenho DELPI.md – seção 2; Drawing Rules DELPI – seção 2.*

---

## 🧩 **3️⃣ Tabela de Materiais (BOM)**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Todos os itens da SG1010** | Devem constar na tabela | ✅ 100% conferentes / ⚠️ Itens faltantes |
| **Quantidades** | Dentro de ±10% da SG1010 | ✅ Dentro da tolerância / ❌ Divergente |
| **Descrição técnica** | Conforme normas e SB1010 | ✅ Corretas / ⚠️ Parcialmente divergentes |
| **Código e posição (balão)** | Correspondem ao desenho | ✅ Alinhados / ⚠️ Inconsistentes |

📘 *Base: Drawing Analyser Instructions – seção 3; Drawing Rules DELPI – seção 3.*

---

## 📏 **4️⃣ Cotas, Dimensões e Escala**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Cotas principais** | Presentes (comprimento, decape, espaçamentos) | ✅ Todas visíveis / ⚠️ Faltantes |
| **Tolerâncias** | Informadas no desenho | ✅ ±1mm ou conforme norma / ⚠️ Ausente |
| **Escala** | Indicada no carimbo | ✅ 1:1 / ⚠️ Não informada |
| **Unidade** | Sempre “mm” | ✅ Correta / ❌ Errada |
| **Legibilidade** | Texto ≥ 2,5mm | ✅ Ok / ⚠️ Ilegível |

📘 *Fonte: Drawing Rules DELPI – seção 4.*

---

## 🎨 **5️⃣ Balões, Vistas e Identificações**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Balões correspondem à BOM** | Conferir posições | ✅ Ok / ⚠️ Divergente |
| **Vista principal presente** | Verificar projeção ortogonal | ✅ Presente / ❌ Ausente |
| **Vistas auxiliares ou cortes** | Usadas quando necessário | ✅ Presentes / ⚠️ Incompletas |
| **Vistas especiais (Vista X)** | Identificadas e cotadas | ✅ Corretas / ⚠️ Não identificadas |
| **Lado A / B** | Identificação textual | ✅ Presente / ⚠️ Omitido |

📘 *Exemplos: 90264124, 90263790, 90480106.*

---

## ⚙️ **6️⃣ Notas Técnicas e Observações**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Nota de produto novo** | Quando REV.00 | ✅ Presente / ⚠️ Ausente |
| **Nota de processo** | Instruções operacionais | ✅ Correta / ⚠️ Genérica |
| **Nota de inspeção** | Vincular à operação CT-99 | ✅ Citada / ⚠️ Ausente |
| **Nota de segurança / UL** | Quando exigido pelo cliente | ✅ Presente / ⚠️ Faltante |

📘 *Fontes: Drawing Rules DELPI – seção 7; Normas Técnicas DELPI.*

---

## 🧠 **7️⃣ Códigos Intermediários (Família 50xx)**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Formato do código** | `50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx` | ✅ Correto / ❌ Incompleto |
| **Descrição técnica** | Compatível com o código | ✅ Ok / ⚠️ Incompleta |
| **Cor e bitola** | Devem corresponder ao código | ✅ Ok / ❌ Divergente |
| **Terminais e isoladores** | Devem existir no código | ✅ Ok / ⚠️ Faltantes |

📘 *Referência: Entendendo Código Intermediário no TOTVS e Desenhos.md (p.3–14).*  

---

## 🧰 **8️⃣ Revisões e Histórico**

| Item | Verificação | Critério |
|------|--------------|----------|
| **Revisão atual** | Corresponde à última versão salva | ✅ Ok / ⚠️ Desatualizada |
| **Descrição da revisão** | Informada no carimbo | ✅ Ok / ⚠️ Ausente |
| **Versão digital (PDF)** | Nome padrão `XXXXXX_RYY.pdf` | ✅ Ok / ❌ Fora do padrão |
| **Assinatura digital** | Presente no PDF final | ✅ Ok / ⚠️ Ausente |

📘 *Base: Requisitos Desenho DELPI – seção 7.*

---

## 🔍 **9️⃣ Classificação Automática Final**

Após a validação de todas as seções, o agente classifica o desenho conforme o resultado consolidado:

| Classificação | Critério | Ação Requerida |
|---------------|----------|----------------|
| ✅ **Conforme** | 95–100% dos itens validados como OK | Liberar produção e arquivar revisão |
| ⚠️ **Pendente** | 70–94% dos itens conformes | Solicitar correção e reenvio |
| ❌ **Não Conforme** | <70% conformidade | Reprovar e devolver à engenharia |

📘 *Percentuais baseados em média ponderada de campos críticos (cabeçalho, BOM, cotas, notas e revisão).*  

---

## 📚 **Fontes Oficiais de Validação**

- **Drawing Rules DELPI.md** — Regras gráficas e simbologia.  
- **Requisitos Desenho DELPI.md** — Estrutura e obrigatoriedades.  
- **Entendendo Código Intermediário.md** — Padrões de formatação e descrição.  
- **Normas Técnicas DELPI.md** — Materiais e conformidade.  
- **Checklist Revisão DELPI.xlsx** — Itens de auditoria e pesos de conformidade.  

---

### ✅ **Conclusão**

As regras aqui definidas permitem que o **Agente de Análise DELPI** realize auditorias automáticas e documentadas, garantindo:
- Rastreabilidade entre desenho e produto real (Protheus);
- Uniformidade visual e técnica;
- Aderência às normas internas e externas (UL / NBR / IEC);
- Redução de falhas humanas e ganho de eficiência nas revisões técnicas.