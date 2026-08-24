# SPEC AT-06B6.1 — Smart Bins, Seleção por Visão e Importação Direta

**Data:** 2026-08-23  
**Projeto:** CIRCE-ATHENA  
**Status:** Implementação incremental

## Objetivo

Corrigir o comportamento do Pool após o primeiro uso real do Cabeçalho.

## Correções

### Vazamento de seleção

O rodapé do Pool Browser passa a contar apenas itens selecionados na Bin/Smart Bin aberta.

Uma Bin vazia sempre mostra zero itens selecionados, mesmo que exista seleção em outra visão.

### Importação

Remove o botão global `Adicionar material`.

Bins importáveis:

- Pessoas;
- Documentos;
- Imagens;
- Áudios;
- Vídeos.

Fluxos:

- abrir Bin → `Importar arquivos nesta Bin`;
- arrastar arquivos diretamente sobre o card da Bin.

A Bin escolhida funciona como classificação humana explícita.

### Smart Bins

Remove `Seleção atual`.

Inclui:

- Relevante ao tópico;
- Usados no tópico;
- Ainda não usados;
- Notas assistidas.

## Proveniência

`Usados no tópico` é calculada com base em relações persistidas:

- fontes do Cabeçalho;
- fontes de Recortes;
- fontes de Achados.

Não é calculada pela seleção momentânea da interface.

## Context Bin

A lógica foi refinada para considerar classe da fonte e Bin.

Exemplo: em `Análise de imagens`, um PDF comum não aparece apenas por possuir `poolKind=document`; a regra privilegia a Bin Imagens.

## Banco

Nenhuma migration.

Alembic:

`0012_at06b6_header_extraction_archive`
