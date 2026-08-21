# AT-06 — Decisões Consolidadas de Produto

**Data:** 2026-08-21
**Status:** Decisão de produto consolidada
**Projeto:** CIRCE-ATHENA
**Unidade técnica:** AT-06 — Workspace Investigativo & Construtor de Peças
**Branch de trabalho:** `feat/at-06a-workspace-core`

## 1. Objetivo deste documento

Este documento consolida as decisões de produto e arquitetura funcional tomadas durante a implementação e validação inicial da AT-06.

Ele substitui interpretações anteriores que tratavam o Workspace principalmente como uma tela de caso com listas e formulários e estabelece uma linguagem de interação mais próxima de um **editor não linear profissional aplicado ao trabalho investigativo**.

A referência conceitual de interação é a aba **Edit** de softwares como DaVinci Resolve: não para copiar sua interface literalmente, mas para adotar sua lógica de organização de material, composição, inspeção contextual e manipulação direta.

A decisão central é:

> **A investigação e a peça policial serão construídas como uma composição não linear de elementos rastreáveis, manipulados visualmente pelo policial, com Athena atuando de forma contextual sobre o objeto em foco.**

## 2. Princípios invariantes de produto

A AT-06 deve continuar obedecendo aos seguintes princípios:

1. O Workspace não pode virar gerenciador de arquivos.
2. O Construtor de Peças não pode virar um Word piorado.
3. Athena não pode virar um gerador mágico de relatórios.
4. O policial não pode virar alimentador de formulários.
5. Toda funcionalidade deve justificar sua existência por ganho operacional real.
6. A autoria, a decisão e a validação final permanecem humanas.
7. Proveniência e rastreabilidade não são opcionais.
8. Fato, declaração, evidência, anotação, inferência, hipótese e pendência não podem ser misturados semanticamente.
9. A interface deve reduzir trabalho mecânico e preservar o raciocínio investigativo.
10. O sistema deve privilegiar manipulação direta, contexto e reutilização em vez de duplicação.

## 3. Modelo conceitual consolidado

A sequência original:

`Caso → Artefato → Evidência → Bloco Investigativo → Seção → Produto`

é mantida apenas como **fluxo de compreensão**, não como árvore rígida de banco de dados.

O modelo real é relacional e muitos-para-muitos.

### 3.1 Caso

Identidade canônica da investigação.

O Caso agrega as entidades e materiais pertinentes à investigação, mas não deve absorver o estado operacional específico do trabalho do analista.

### 3.2 Workspace

Ambiente operacional do Caso.

Na AT-06A adota-se:

`1 Caso → 1 Workspace`

A arquitetura não deve bloquear multiplicidade futura, mas não haverá complexidade adicional sem necessidade operacional demonstrada.

### 3.3 Artefato

Material preservado que ingressa no caso: documento, imagem, print, planilha, áudio, vídeo ou outro arquivo.

O original deve permanecer distinguível de qualquer derivado.

### 3.4 Evidência

Unidade citável ou delimitada utilizada como suporte.

Exemplo:

- não apenas `extrato.pdf`;
- mas “transação de R$ 12.500, página 8, data X”.

Evidência responde:

> **Qual é o suporte?**

### 3.5 Elemento Investigativo

Objeto que expressa o significado atribuído ou registrado no processo investigativo.

Categorias previstas:

- Fato;
- Declaração;
- Anotação;
- Inferência;
- Hipótese;
- Pendência.

Evidência não deve ser apenas mais um valor desse enum, porque ela exerce função diferente: sustenta afirmações, mas não é a afirmação em si.

### 3.6 Bloco Investigativo

Unidade de raciocínio investigativo.

Um bloco agrega, por referência:

- pessoas;
- documentos;
- evidências;
- vínculos;
- anotações;
- fatos;
- inferências;
- hipóteses;
- pendências;
- demais elementos relevantes.

O bloco não copia seus elementos.

Ele representa:

> **“Estou analisando esta questão com estas fontes e estes elementos.”**

Um mesmo elemento pode participar de vários blocos.

### 3.7 Produto e Seção

Produto é a peça documental: relatório, informação, análise ou outro produto policial.

A organização correta é:

`Produto → Seções → Blocos utilizados`

Um bloco pode alimentar mais de um produto ou seção sem duplicar sua base investigativa.

## 4. Composição Investigativa Não Linear

A linguagem de interação escolhida para a evolução da AT-06 é a **Composição Investigativa Não Linear**.

A interface não deverá ser orientada por páginas de formulário, mas por áreas de trabalho especializadas e manipuláveis.

O paradigma é:

`Pool do Caso → Blocos Investigativos → Compositor da Peça → Viewer/Inspector → Produto`

### 4.1 Pool do Caso

A atual coluna **Elementos do caso** evoluirá para um **Pool do Caso**.

O Pool é inspirado no Media Pool de editores não lineares.

Ele não representa diretórios físicos.

Os “bins” serão organizações virtuais de objetos investigativos.

Bins iniciais previstos:

- Pessoas;
- Organizações;
- Documentos;
- Imagens;
- Evidências;
- Vínculos;
- Anotações;
- Declarações;
- Fatos;
- Inferências;
- Hipóteses;
- Pendências.

Um objeto não deve ser duplicado ao aparecer em um bin.

### 4.2 Smart Bins

A arquitetura deverá permitir evolução para Smart Bins, por exemplo:

- Evidências ainda não utilizadas;
- Pendências abertas;
- Elementos relacionados a determinada pessoa;
- Elementos de determinado período;
- Inferências não validadas;
- Material utilizado no produto atual;
- Elementos adicionados recentemente;
- Fontes sem proveniência suficiente.

Smart Bins são visões derivadas, não armazenamento paralelo.

### 4.3 Drag and Drop

Drag and drop passa a ser interação estrutural do produto.

Fluxos desejados:

- arrastar um elemento do Pool para um bloco;
- selecionar múltiplos elementos e arrastá-los em conjunto;
- soltar elementos em área vazia para iniciar novo bloco;
- reordenar blocos;
- futuramente arrastar blocos para seções do produto;
- futuramente reordenar seções e componentes do produto.

A manipulação direta deve reduzir cliques e formulários.

### 4.4 Blocos como área de composição investigativa

A atual área **Blocos Investigativos** é o equivalente funcional à área de composição de um editor.

Ela não deve ser uma timeline horizontal de vídeo.

A investigação e a produção documental são predominantemente estruturais, não temporais.

A área deve privilegiar organização visual, ordem, agrupamento e contexto.

## 5. Compositor da Peça

A AT-06D deverá evoluir para um compositor documental estruturado.

A analogia com timeline será aplicada como **composição vertical**, adequada a documentos.

Exemplo:

- 01 — Identificação;
- 02 — Contexto;
- 03 — Diligências;
- 04 — Análise;
- 05 — Conclusão.

Cada seção poderá consumir:

- blocos investigativos;
- evidências;
- imagens;
- tabelas;
- elementos selecionados;
- textos humanos;
- textos assistidos.

O usuário organiza a estrutura.

O sistema cuida da transformação documental.

## 6. Viewer / Inspector

A área atualmente utilizada por Athena evoluirá conceitualmente para uma zona de **Viewer / Inspector contextual**.

Ela deverá exibir o objeto atualmente em foco e permitir ações pertinentes.

### 6.1 Exemplo: Evidência

O Inspector poderá mostrar:

- origem;
- artefato original;
- localização no artefato;
- hash;
- operador;
- data;
- blocos em que é utilizada;
- seções/produtos em que é citada.

### 6.2 Exemplo: Bloco

Poderá mostrar:

- fontes;
- resumo;
- estado;
- autoria;
- inferências relacionadas;
- pendências;
- produtos/seções em que foi utilizado.

### 6.3 Exemplo: Seção

Poderá mostrar:

- blocos-base;
- autoria;
- última revisão;
- elementos de suporte;
- ações de revisão e redação assistida.

## 7. Athena contextual

Athena não deverá ser tratada como um chat paralelo desconectado.

A prioridade contextual será:

1. objeto ou seleção atual;
2. bloco ativo;
3. Workspace ativo;
4. Caso ativo;
5. histórico recente.

Exemplos:

- selecionou uma evidência → Athena atua sobre a evidência;
- selecionou um bloco → Athena atua sobre o bloco;
- selecionou uma seção → Athena atua sobre a seção;
- nenhuma seleção → Athena atua sobre o Caso.

O usuário não deve precisar repetir identificadores que a própria interface já conhece.

### 7.1 Regra de isolamento

Quando Athena estiver operando sobre um bloco, não deverá utilizar silenciosamente elementos externos ao bloco para sustentar conclusões sobre aquele bloco.

Se ampliar o contexto for necessário, isso deverá ser explícito.

### 7.2 Autoria

Permanecem os modos:

- `literal`;
- `assisted_drafting`.

Nenhum texto produzido por Athena se torna automaticamente fato ou evidência.

## 8. Proveniência e estabilidade de referência

A proveniência deve responder continuamente:

> **“De onde saiu isso?”**

A AT-06A adotou como regra:

- chave estável da fonte quando disponível;
- snapshot mínimo de identificação no momento da associação.

Essa proteção é necessária porque fontes sincronizadas podem ser atualizadas ou recriadas internamente.

A proveniência nova deve utilizar nomenclatura neutra, por exemplo:

`CASE:<referência>`

O marcador legado `PLATEA:` não deve ser produzido por novos fluxos.

Compatibilidade de leitura com dados legados pode ser mantida enquanto necessário.

## 9. Nomenclatura de produto

**Platea** deixa de ser nome de produto ou conceito obrigatório da arquitetura futura.

A interface visível usa:

- Gestor de Investigações;
- Caso;
- Workspace Investigativo;
- Blocos Investigativos;
- Athena.

Rotas, tabelas e classes internas legadas podem permanecer temporariamente durante migração controlada.

Não se deve realizar refatoração massiva de nomenclatura interna no meio da AT-06A apenas por estética.

## 10. Gestão do espaço de trabalho

A AT-06A validou que larguras fixas são inadequadas.

O Workspace deve possuir:

- tiling redimensionável;
- divisores arrastáveis;
- persistência das larguras;
- painéis colapsáveis;
- restauração rápida do layout;
- preservação do estado dos elementos durante colapso.

As áreas principais são:

- Pool/Elementos do Caso;
- Blocos/Composição;
- Athena / Viewer / Inspector.

O layout deve adaptar-se ao trabalho em curso.

## 11. Reversibilidade operacional

O sistema deve permitir correção de ações sem apagar rastros.

Implementado/projetado:

- desfazer última seleção;
- limpar seleção;
- remover fonte de um bloco sem apagar a fonte original;
- desfazer criação de bloco por descarte lógico;
- auditoria das alterações persistentes.

Desfazer não significa destruição silenciosa.

## 12. Modos SAFE e AGENT

A ADR-003 permanece válida.

Modo de execução não altera permissão.

Ações persistentes do Workspace deverão declarar risco.

Operações reversíveis e de baixo risco poderão ser executadas diretamente conforme política central.

Ações destrutivas, irreversíveis ou de alto impacto permanecem sujeitas aos guardrails definidos.

## 13. Fronteiras revisadas AT-06A–AT-06F

### AT-06A — Núcleo do Workspace

Entrega:

- Workspace ligado ao Caso;
- contexto do caso;
- Blocos Investigativos;
- associação rastreável de fontes;
- Athena contextual ao Caso/Bloco;
- reversibilidade básica;
- tiling;
- colapso de painéis;
- fundação para Pool/Bins e drag and drop.

Não entrega:

- intake completo;
- OCR;
- produto documental;
- DOCX/PDF;
- motor epistemológico completo.

### AT-06B — Intake e Pool do Caso

Entrega:

- ingresso de novos materiais;
- preservação de original;
- hash;
- metadados;
- Pool do Caso;
- bins virtuais;
- drag and drop de elementos;
- início da delimitação de evidências.

### AT-06C — Organização Analítica

Entrega:

- fatos;
- declarações;
- inferências;
- hipóteses;
- pendências;
- validação;
- cronologia;
- smart bins;
- correlações e estados analíticos.

### AT-06D — Compositor da Peça

Entrega:

- Produto;
- Seções;
- composição vertical;
- drag and drop de blocos;
- Viewer / Inspector;
- redação assistida contextual;
- revisão;
- rastreabilidade seção → bloco → fonte.

### AT-06E — Exportação

Entrega:

- DOCX;
- PDF;
- estilos;
- cabeçalhos;
- rodapés;
- tabelas;
- imagens;
- templates documentais.

### AT-06F — Refinamentos

Entrega futura:

- versionamento;
- comparação de versões;
- aprovação;
- templates institucionais;
- colaboração;
- refinamentos de produtividade.

## 14. Decisão sobre o protótipo atual

O protótipo AT-06A não será descartado.

Ele é a fundação da nova linguagem de interação.

Evolução prevista:

- lista com checkboxes → Pool/Bins;
- associação por clique → drag and drop;
- Blocos atuais → área de composição investigativa;
- Athena atual → Athena contextual integrada ao Viewer/Inspector;
- tiling/colapso atual → infraestrutura permanente de layout.

## 15. Critérios de sucesso do paradigma

A direção será considerada bem-sucedida quando:

1. casos grandes continuarem navegáveis;
2. o analista puder localizar e reutilizar material sem duplicação;
3. criar ou enriquecer um bloco exigir poucas ações;
4. drag and drop reduzir trabalho mecânico real;
5. Athena respeitar o contexto selecionado;
6. toda conclusão relevante puder retornar às suas fontes;
7. a peça puder ser reorganizada sem alterar a base investigativa;
8. o policial puder construir um relatório sem trabalhar como diagramador de Word;
9. a interface continuar compreensível sem treinamento excessivo;
10. o ganho operacional for percebido em investigação real.

## 16. Decisão final

A AT-06 deixa de ser concebida apenas como “Workspace + editor de relatório”.

Ela passa a ser concebida como uma **plataforma de composição investigativa não linear orientada a evidências**, na qual:

- o Caso fornece o universo investigativo;
- o Pool organiza os elementos;
- os Blocos estruturam o raciocínio;
- o Compositor estrutura a peça;
- o Viewer/Inspector expõe contexto e propriedades;
- Athena atua sobre o foco atual;
- o motor documental transforma a composição em DOCX/PDF;
- proveniência, autoria e auditoria atravessam toda a cadeia.
