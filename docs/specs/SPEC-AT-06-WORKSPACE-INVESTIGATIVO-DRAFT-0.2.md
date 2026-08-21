# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.2
**Data:** 2026-08-21
**Status:** Em implementação incremental
**Produto:** CIRCE-ATHENA
**Escopo:** Workspace por caso + composição investigativa não linear + construção assistida de peças policiais
**Relacionadas:** ADR-001, ADR-002, ADR-003; AT-06 — Decisões Consolidadas de Produto — 2026-08-21

## 1. Visão

O Workspace Investigativo é o ambiente operacional de um caso.

Seu objetivo é permitir que o policial reúna, organize, relacione, analise e utilize informações e evidências com o mínimo possível de trabalho mecânico.

A experiência adotará um modelo de **composição investigativa não linear**, inspirado na gramática de editores profissionais: um Pool do Caso organiza os elementos disponíveis; Blocos Investigativos estruturam o raciocínio; um Compositor organiza o produto; Viewer/Inspector e Athena atuam contextualmente sobre o objeto selecionado.

O usuário não deve trabalhar a partir de página em branco nem de formulários extensos.

## 2. Princípio central

> **O policial constrói a lógica investigativa; Athena e a plataforma reduzem o esforço de organizá-la e transformá-la em produto documental.**

A plataforma poderá organizar, sugerir, comparar, sintetizar, redigir, revisar e estruturar.

Não poderá:

- substituir decisão investigativa;
- transformar hipótese em fato;
- inventar base factual;
- perder origem dos elementos;
- atribuir ao operador conteúdo não fornecido ou não solicitado;
- ocultar autoria assistida.

## 3. Modelo de domínio

### 3.1 Caso

Identidade da investigação.

### 3.2 Workspace

Ambiente operacional ligado ao Caso.

AT-06A: `1 Caso → 1 Workspace`.

### 3.3 Artefato

Original preservado: arquivo, documento, imagem, áudio, vídeo, planilha ou material equivalente.

### 3.4 Evidência

Unidade citável ou delimitada derivada ou referenciada de artefato/registro.

### 3.5 Elemento Investigativo

Tipos semânticos previstos:

- Fato;
- Declaração;
- Anotação;
- Inferência;
- Hipótese;
- Pendência.

Evidência permanece conceitualmente separada.

### 3.6 Bloco Investigativo

Unidade de raciocínio que referencia fontes e elementos.

Blocos são reutilizáveis e independentes do produto documental.

### 3.7 Produto e Seção

`Produto → Seções → Blocos utilizados`

A narrativa documental é projeção da investigação, não sua fonte de verdade.

## 4. Pool do Caso

A área atualmente chamada Elementos do Caso evoluirá para **Pool do Caso**.

O Pool não representa pastas físicas.

Bins virtuais iniciais:

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

Evolução prevista: Smart Bins derivados por filtros e estado.

## 5. Manipulação direta e drag and drop

Drag and drop será interação estrutural.

O usuário deverá poder:

- arrastar elemento para bloco;
- arrastar múltiplos elementos;
- criar bloco por drop em área vazia;
- remover associação sem apagar origem;
- reordenar blocos;
- futuramente arrastar blocos para seções do Produto.

## 6. Workspace

Áreas funcionais:

1. Pool / Elementos do Caso;
2. Blocos / Composição Investigativa;
3. Athena / Viewer / Inspector.

O layout deverá:

- ser redimensionável;
- permitir colapso de painéis;
- persistir preferências localmente;
- permitir restauração rápida;
- preservar o estado dos objetos durante alterações de layout.

## 7. Athena contextual

Prioridade:

1. seleção atual;
2. bloco ativo;
3. Workspace;
4. Caso;
5. histórico recente.

Quando um bloco estiver ativo, Athena deve trabalhar prioritariamente com suas fontes.

Ampliação de contexto não deve ser silenciosa.

## 8. Proveniência

Cada objeto relevante deve responder “de onde saiu isso?”.

Associações do Workspace deverão usar:

- referência estável quando disponível;
- snapshot mínimo de identificação;
- autoria/origem;
- data;
- relação com bloco/produto.

Proveniência nova usa nomenclatura neutra `CASE:<referência>`.

Marcadores legados podem ser lidos durante transição, mas não devem ser gerados por novos fluxos.

## 9. Autoria

Modos:

- `literal`;
- `assisted_drafting`.

Texto produzido por Athena não se torna automaticamente fato, declaração ou evidência.

Mudanças de estatuto exigem ação explícita e rastreável.

## 10. SAFE / AGENT

A ADR-003 permanece normativa.

Modo de execução:

- não amplia permissão;
- não remove auditoria;
- não contorna allowlists;
- não contorna fronteira de comunicação externa;
- não elimina validação estrutural.

Toda nova ação persistente deverá declarar risco.

## 11. Reversibilidade

O Workspace deverá evitar destruição silenciosa.

AT-06A inclui:

- desfazer seleção;
- limpar seleção;
- remover fonte de bloco;
- descarte lógico de bloco;
- auditoria das alterações persistentes.

## 12. Nomenclatura

Nome visível da ferramenta: **Gestor de Investigações**.

“Platea” é tratado como nomenclatura interna/legada durante transição e não como identidade futura do produto.

Rotas e modelos internos podem ser regularizados em incremento próprio.

## 13. Incrementos

### AT-06A — Núcleo do Workspace

Inclui:

- Workspace por Caso;
- Bloco Investigativo;
- fontes rastreáveis;
- Athena contextual;
- reversibilidade;
- tiling;
- painéis colapsáveis;
- fundação para Pool/Bins e drag and drop.

### AT-06B — Intake e Pool

Inclui:

- upload;
- preservação;
- hash;
- metadados;
- Pool;
- bins;
- drag and drop;
- evidências iniciais.

### AT-06C — Organização Analítica

Inclui:

- Fato;
- Declaração;
- Inferência;
- Hipótese;
- Pendência;
- cronologia;
- Smart Bins;
- validação.

### AT-06D — Compositor

Inclui:

- Produto;
- Seções;
- composição vertical;
- drag and drop de blocos;
- Viewer/Inspector;
- Athena contextual à seção;
- rastreabilidade seção → bloco → fonte.

### AT-06E — Exportação

Inclui:

- DOCX;
- PDF;
- estilos;
- templates;
- imagens;
- tabelas.

### AT-06F — Refinamentos

Inclui:

- versionamento;
- comparação;
- aprovação;
- colaboração;
- templates institucionais;
- produtividade avançada.

## 14. Critérios de aceite do núcleo

AT-06A será considerada funcional quando:

1. um caso abrir seu Workspace;
2. o Workspace não duplicar a base canônica desnecessariamente;
3. blocos puderem ser criados e descartados;
4. fontes puderem ser associadas/removidas sem alterar originais;
5. Athena receber o Caso e o Bloco ativos;
6. o bloco preservar proveniência;
7. seleção e layout forem reversíveis;
8. migrations forem explícitas e reproduzíveis;
9. smoke tests passarem;
10. o fluxo demonstrar ganho operacional real.

## 15. Critérios de produto

A evolução deverá provar que:

- casos grandes continuam manejáveis;
- o policial encontra material rapidamente;
- o número de cliques diminui;
- drag and drop é previsível;
- o sistema não vira gerenciador de arquivos;
- o compositor não vira editor de texto genérico;
- Athena respeita contexto e proveniência;
- a peça final continua sob autoria e validação humana.
