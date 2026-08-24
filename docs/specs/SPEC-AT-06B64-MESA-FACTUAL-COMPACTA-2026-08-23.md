# SPEC AT-06B6.4 — Mesa Factual Compacta

**Data:** 2026-08-23  
**Projeto:** CIRCE-ATHENA  
**Status:** Implementação incremental

## Problema observado

O Mapa Factual funcionou com material real, porém cada informação ocupava um card alto contendo simultaneamente:

- label;
- status;
- textarea;
- documento;
- página;
- trecho.

Isso produzia rolagem excessiva e leitura lenta.

## Solução

### Linha compacta

Estado recolhido:

`Natureza | FURTO (CONSUMADO) | PROPOSTO | BO.pdf · p.1`

Clique expande o item.

### Detalhe expandido

- textarea editável;
- estado;
- Ver fonte;
- Ver trecho usado;
- notas.

### Grupos

- Dados estruturados;
- Síntese documental;
- Contexto e delimitação do analista;
- Narrativa.

## Confirmação

`Confirmar mapa factual`:

- confirma itens não vazios e não ignorados;
- salva o mapa;
- preserva campos vazios como não confirmados.

## Proveniência

O trecho completo fica recolhido por padrão.

A fonte abre em nova aba, com fragmento de página quando disponível.

## Limpeza da Mesa

O bloco técnico AT-06A deixa de ser exibido em Cabeçalho e Dos Fatos.

## Banco

Nenhuma migration.

Alembic:

`0013_at06b63_facts_topic_composition`
