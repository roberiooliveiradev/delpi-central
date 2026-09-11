# Portal de Engenharia — Design de Arquitetura de Informação e UX

> **Status:** contrato de experiência para implementação.  
> **Referências internas:** Portais Comercial e Suprimentos + `@delpi/plugin-ui`.

## 1. Objetivo

O Portal deve reduzir a fragmentação da Engenharia sem transformar a navegação em uma lista de todos os sistemas existentes. A IA separa **jornadas principais** de **ferramentas especializadas**.

## 2. Navegação principal

Ordem travada:

```text
Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda
```

### Semântica

- **Início:** atenção, atalhos, atividades e descoberta.
- **Visão geral:** placar da área e indicadores.
- **Sala de interação:** colaboração entre pessoas/contextos.
- **Minhas tarefas:** itens acionáveis atribuídos ao usuário.
- **LMPs:** jornada operacional central.
- **Ajuda:** orientação permanente.

Nenhuma ferramenta deve entrar na TopBar sem decisão explícita do Product Owner e revisão da arquitetura de informação.

## 3. Ferramentas

Ferramentas são acessadas pelo Início, Ctrl+K, Favoritos e deep links.

Grupos propostos:

```text
Ferramentas
├── Produto e estrutura
│   ├── Produtos
│   └── Biblioteca de desenhos
├── Processos de Engenharia
│   ├── Controle de MP
│   └── Não conformidades
├── Documentos
│   └── Documentos técnicos
└── Melhoria contínua
    └── TRANSFORMA+
```

O agrupamento pode evoluir, mas não deve alterar ownership nem permissions.

## 4. Shell

O shell deve usar o TopBar canônico do kit, com:

```text
[Portal de Engenharia]
Início | Visão geral | Sala | Minhas tarefas | LMPs | Ajuda
                    [Ferramentas] [Buscar] [Favoritos] [Perfil]
```

Se a API vigente do TopBar não comportar exatamente essa distribuição, estudar primeiro o `plugin-ui` e os portais maduros. Não criar uma segunda barra fixa apenas para contornar limitação local.

## 5. Início

Hierarquia de informação:

1. saudação/contexto;
2. atenção do usuário;
3. tarefas;
4. LMPs críticas/recentes;
5. menções/salas;
6. ferramentas;
7. atividade recente.

Home não replica todos os gráficos da Visão geral.

### Cards de ferramenta

Cada card deve conter no máximo:

- nome;
- descrição curta;
- estado/contador quando existe contrato confiável;
- CTA;
- favorito quando suportado.

Não exibir card desabilitado por falta de permission se o padrão do Portal for omissão. Seguir comportamento canônico do shell.

## 6. Visão geral

Deve ser um placar gerencial, não uma cópia do dashboard legado pixel a pixel.

P0:

- score/indicadores oficiais;
- tendência temporal quando houver contrato;
- resumo de LMPs;
- resumo TRANSFORMA+;
- atenções/gargalos;
- drills para LMPs ou owner correspondente.

Filtros só entram no chrome global quando afetam de forma coerente todos os blocos. Filtro pertencente a uma ferramenta fica naquela ferramenta.

## 7. Sala de interação

### Inbox

- Todas / Não lidas / Minhas, somente se o modelo real suportar;
- busca;
- título/contexto;
- preview da última mensagem;
- horário;
- badge de não lida;
- criação de sala conforme policy.

### Thread

- header com título/contexto/participantes;
- um scroller de mensagens;
- mensagens com autor/avatar/hora;
- menções/reactions/anexos;
- composer fixo no final da área de conversa;
- painel contextual opcional sem competir com a conversa.

### Mobile

Inbox e thread viram navegação drill-in. Não comprimir duas colunas em viewport estreito. Voltar preserva busca/filtro da inbox.

## 8. Minhas tarefas

A worklist deve priorizar ação e compreensão rápida.

Campos visuais candidatos:

- prioridade;
- origem;
- título;
- contexto;
- prazo;
- estado;
- ação principal.

Desktop: DataTable do kit quando apropriado. Mobile: card/record pattern equivalente com a mesma semântica.

## 9. LMPs

### Lista

- resumo/KPIs;
- filtros e busca;
- tabela/lista;
- status, lead, responsável, última movimentação;
- deep link da LMP.

### Detalhe

PageHero com identidade e estado, depois seções/tabs:

```text
Resumo | Produtos | Histórico | Gantt | Não conformidades
```

Não duplicar a ficha completa de Produto dentro da LMP; usar resumo + CTA para a ferramenta Produtos.

## 10. Produtos

Ferramenta orientada a descoberta técnica.

Pesquisa deve aceitar os identificadores reais disponíveis no backend: código, descrição, referência/part number quando comprovados.

Ficha 360°:

```text
Visão geral | Estrutura | Onde é usado | Desenho | Estoque | Fornecedores | Custos*
```

`Custos*` só aparece com autorização adequada.

## 11. Documentos e desenhos

### Biblioteca de desenhos

Filtros por metadados reais; preview PDF com ações contextualizadas.

### Documentos técnicos

Bibliotecas lógicas, nunca árvore arbitrária do FILESERVER. Office pode iniciar com download controlado se preview seguro não existir.

## 12. Ajuda contextual

Padrão vigente: quando houver label/título semântico, o próprio texto é o alvo do help; evitar ícone `?` separado.

Usar:

- `FieldLabel`;
- `TitleWithHelp`/equivalente;
- `SectionHintLabel`;
- helpers/factories do kit.

Help deve funcionar em hover e teclado/focus conforme componente canônico.

## 13. Estados

Toda superfície assíncrona deve projetar explicitamente:

```text
loading
success
empty
partial (quando semanticamente seguro)
error
forbidden
not-found
```

Loading não usa banner de erro. Vazio deve orientar o usuário. 403 não oferece CTA que continuaria proibido.

## 14. Responsividade

- desktop: densidade informacional com hierarquia clara;
- tablet: preservar ações primárias;
- mobile: coluna única/drill-in quando necessário;
- touch target mínimo conforme kit;
- tabelas grandes devem ter estratégia mobile explícita;
- sem scroll horizontal global por layout mal dimensionado.

## 15. Tema e tokens

O MFE mapeia tokens locais para `--delpi-ui-*`. Não definir tema paralelo, `body`, `:root` global ou override `.delpi-ui-*`.

## 16. Acessibilidade

- foco visível;
- navegação por teclado;
- headings em ordem;
- aria labels em controles icônicos;
- contraste pelo design system;
- tooltip não pode ser única fonte de informação crítica;
- estados e erros devem ser anunciáveis quando o kit suportar.

## 17. Busca Ctrl+K

Indexar rotas autorizadas, áreas principais e ferramentas. Resultado deve apresentar label amigável e grupo, nunca operationId/path técnico.

Exemplos:

```text
“desenho” → Biblioteca de desenhos
“estrutura” → Produtos
“lmp” → LMPs
“matéria-prima” → Controle de MP
“transforma” → TRANSFORMA+
```

## 18. Favoritos

Favoritos são atalhos de navegação, não cópia de dados. Devem preservar route target estável e respeitar RBAC atual; item que perdeu acesso deixa de ser executável/visível conforme padrão canônico.

## 19. Critério de excelência

A página só fecha quando o usuário consegue entender onde está, o que pode fazer, o que aconteceu em erro/vazio, como voltar, como compartilhar a URL e onde encontrar ajuda — em desktop, mobile e teclado.
