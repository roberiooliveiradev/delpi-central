## Criar descrição técnica de um produto DELPI

> Usuário: **“Crie a descrição técnica do produto”**

### Diretriz mínima (AJUSTADA)

1. **Norma única**  
   Utilizar **exclusivamente** o arquivo `Normas_Tecnicas_DELPI.md` para determinar:
   - grupo técnico;
   - subtipo do item;
   - campos obrigatórios;
   - ordem dos campos;
   - prefixos, abreviações e vocabulário permitidos.
   
   ❌ É proibido usar datasheet como fonte estrutural. Datasheet serve **apenas** para preencher campos já existentes na norma.

2. **Identificação automática da norma**  
   O agente **deve identificar sozinho**:
   - o grupo DELPI correto (ex.: 1008);
   - o subtipo normativo aplicável (ex.: Terminal Olhal, Lingueta, Faston, etc.).

   ⚠️ Se **não existir** uma norma explícita para o item, o agente **deve parar** e informar:
   > “Não existe norma DELPI aplicável para este tipo de produto.”

3. **Dados externos (restrição absoluta)**  
   São permitidos **somente dados objetivos** provenientes de fabricante ou fornecedor que:
   - preencham **exatamente** campos previstos na norma;
   - estejam explicitamente disponíveis (sem inferência).

   ❌ É proibido:
   - estimar valores;
   - converter faixas;
   - deduzir medidas;
   - assumir equivalências.

4. **Construção da descrição**  
   A descrição deve ser montada:
   - seguindo **rigorosamente** a sequência definida na norma;
   - mantendo **prefixos fixos** (ex.: `TERM.`);
   - respeitando **pontuação, separadores e maiúsculas** dos exemplos normativos.

   ❌ É proibido:
   - alterar a ordem;
   - suprimir campos existentes;
   - adicionar campos não previstos.

5. **Restrições de comportamento do agente**  
   O agente **não pode**:
   - inventar dados;
   - completar lacunas;
   - extrapolar especificações;
   - adaptar a norma;
   - pedir confirmação ao usuário;
   - justificar escolhas;
   - explicar a descrição.

   ➜ Dado ausente = **descrição inválida**.

6. **Entrega**  
   A resposta **deve conter somente**:
   - a **descrição técnica final**, em uma única linha;
   - sem título;
   - sem comentários;
   - sem explicações;
   - sem formatação adicional.

---

### Regra-mãe

> **Descrição técnica DELPI é reprodução normativa, não interpretação.**