# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.12  
**Data:** 2026-08-23  
**Status:** Baseline funcional após AT-06B6.2  
**Produto:** CIRCE-ATHENA

## 1. Princípio central do Pool

O Pool distingue quatro conceitos:

1. **Bin / Smart Bin** — visão sobre o acervo;
2. **seleção local** — itens marcados na visão aberta naquele momento;
3. **Bandeja da Mesa** — conjunto acumulado de fontes de várias visões;
4. **proveniência** — vínculo persistente entre fonte e trabalho produzido.

Esses conceitos não devem ser confundidos visual ou tecnicamente.

## 2. Seleção local

A seleção dentro de uma Bin ou Smart Bin é temporária e pertence somente à visão aberta.

Regras:

- abrir outra Bin zera a seleção local;
- uma Bin vazia sempre mostra `0 selecionados nesta visão`;
- Ctrl/Cmd + clique adiciona/remove;
- Shift + clique seleciona intervalo;
- Ctrl/Cmd + A seleciona somente os elementos visíveis daquela visão;
- a seleção local não é Smart Bin;
- a seleção local não altera proveniência.

## 3. Bandeja da Mesa

A Bandeja é o mecanismo explícito para reunir fontes de várias Bins.

Fluxo:

`Bin A → selecionar → Adicionar à bandeja → Bin B → selecionar → Adicionar à bandeja → Usar no tópico`

A Bandeja:

- pode acumular fontes de várias visões;
- permanece ao trocar de Bin;
- possui contador próprio;
- pode ser limpa;
- suporta desfazer;
- é sincronizada entre panes/janelas do mesmo Workspace;
- alimenta Cabeçalho, Recortes, Achados e demais trabalhos do Tópico.

## 4. Smart Bins

A revisão B6.1 permanece válida.

Smart Bins atuais:

- Relevante ao tópico;
- Usados no tópico;
- Ainda não usados;
- Notas assistidas.

Nenhuma delas depende da seleção momentânea do usuário.

### Relevante ao tópico

Context Bin determinística condicionada ao Tópico ativo.

### Usados no tópico

Calculada por proveniência persistente.

### Ainda não usados

Material do caso sem relação persistida com o Tópico ativo.

### Notas assistidas

Anotações originadas do fluxo assistido.

Smart Bins semânticas continuam condicionadas a OCR/indexação/embeddings reais.

## 5. Estados visuais

Um item pode estar simultaneamente:

- visível na Bin atual;
- selecionado localmente;
- já presente na Bandeja;
- já utilizado no Tópico.

Esses estados devem ter indicadores independentes.

## 6. Regra de não vazamento

Contadores e comandos do Pool Browser devem refletir somente a seleção local da visão atual.

É proibido exibir, por exemplo:

`Pessoas — nenhum elemento nesta visão — Usar 2 na Mesa`

quando os dois itens foram selecionados em Documentos.

O contador da Bandeja pode continuar mostrando dois, mas deve ser rotulado explicitamente como Bandeja.

## 7. Cabeçalho e análise

A Bandeja fornece os `source_tokens` usados pelos fluxos estruturados.

No Cabeçalho:

- OS e BO podem ser reunidos pela Bandeja;
- extração B6 lê os PDFs;
- confirmação humana persiste as fontes;
- Smart Bin `Usados no tópico` passa então a refletir a proveniência persistida.

## 8. Banco

AT-06B6.2 não requer migration.

Alembic permanece em:

`0012_at06b6_header_extraction_archive`
