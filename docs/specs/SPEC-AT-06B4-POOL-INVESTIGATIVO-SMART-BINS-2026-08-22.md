# SPEC AT-06B4 — Pool Investigativo com Bins e Smart Bins

**Data:** 2026-08-22  
**Status:** Implementação incremental  
**Projeto:** CIRCE-ATHENA  
**Unidade:** AT-06B4

## Objetivo

Substituir o paradigma visual de “lista/checklist de elementos” por um Pool investigativo navegável, inspirado na lógica de Media Pool/Smart Bins, mas adaptado ao trabalho policial.

## Problema observado

O protótipo anterior provou seleção, drag and drop e Tópicos de Trabalho, porém o Pool ainda parecia uma lista técnica. Em casos reais, especialmente extrações de dispositivos móveis, o volume de elementos torna essa representação inadequada.

## Decisão

Implementar dois níveis:

`Home do Pool → Conteúdo da Bin/Smart Bin + Preview`

### Bins v1

- Pessoas
- Documentos
- Vínculos
- Anotações

### Smart Bins v1

- Relevante ao tópico
- Seleção atual
- Notas assistidas

### Context Bin

A Smart Bin `Relevante ao tópico` recebe regra determinística baseada no Tópico de Trabalho ativo.

Ela é ajuda de navegação, não classificação probatória.

## Interações

- clique: seleção única;
- Ctrl/Cmd + clique: adiciona/remove;
- Shift + clique: intervalo dentro da visão atual;
- Ctrl/Cmd + A: seleciona elementos visíveis;
- Escape: limpa seleção;
- hover/foco: preview;
- drag: leva a seleção para a Mesa;
- busca: abre visão global de resultados.

## Preview

AT-06B4 exibe metadados e descrição existentes.

A superfície é preparada para receber posteriormente:

- imagem;
- PDF;
- OCR;
- áudio;
- vídeo;
- conversação estruturada.

Não será criado preview fictício.

## Smart Bins futuras

Após indexação:

- não analisados;
- OCR pendente;
- conflitos de metadados;
- já utilizados / não utilizados;
- por pessoa;
- por período;
- por aparelho;
- por interlocutores;
- regras personalizadas;
- Smart Bins semânticas.

## Composer

O painel Athena destacado recebe composer compacto com largura máxima e altura limitada.

## Banco

Nenhuma migration.

Alembic permanece em:

`0009_at06b2_work_topics`

## Critério de conclusão

A navegação pelo Pool deve se parecer com exploração de acervo, não com preenchimento de formulário.
