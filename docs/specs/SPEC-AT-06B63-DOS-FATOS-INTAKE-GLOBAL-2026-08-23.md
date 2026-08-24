# SPEC AT-06B6.3 — Dos Fatos Orientado + Intake Global

**Data:** 2026-08-23  
**Projeto:** CIRCE-ATHENA  
**Status:** Implementação incremental

## Objetivos

1. restaurar o intake global do Pool;
2. manter importação/drag-and-drop direto nas Bins;
3. transformar `Dos fatos / introdução` em fluxo orientado e persistente.

## Intake global

`+ Importar material` retorna ao Pool.

Também é possível arrastar arquivos para a área de intake global.

Sem Bin explícita, a triagem inicial usa o classificador determinístico por tipo.

## Dos Fatos

Fluxo:

`Bandeja → Extrair mapa factual → revisar/confirmar → contexto do analista → Compor narrativa → editar blocos → Confirmar Dos Fatos`

## Mapa factual

Campos iniciais:

- Origem da apuração;
- Natureza do fato;
- Data / período do fato;
- Local;
- Vítima(s) / alvo(s);
- Pessoas mencionadas;
- Síntese objetiva;
- Delimitação desta análise.

Cada campo preserva proveniência.

## Narrativa

Blocos v1:

- Origem da apuração;
- Síntese dos fatos;
- Delimitação da análise.

O usuário pode editar cada bloco.

## Inspector

Mostra preview do capítulo `1. DOS FATOS`.

## Acervo

Fatos confirmados alimentam os metadados do produto.

## Migration

`0013_at06b63_facts_topic_composition`
