# SPEC AT-06B6.2 — Seleção Local + Bandeja da Mesa

**Data:** 2026-08-23  
**Projeto:** CIRCE-ATHENA  
**Status:** Implementação incremental

## Problema

A seleção de Documentos permanecia marcada ao abrir Pessoas ou outras Bins, fazendo o rodapé do modal sugerir uso de itens que não pertenciam à visão aberta.

## Causa

O mesmo estado era usado para:

- seleção temporária da Bin;
- conjunto global de fontes destinado à Mesa.

## Solução

Separar explicitamente:

`seleção local da visão`  
de  
`Bandeja da Mesa`.

## Comportamento

### Dentro do modal

- seleção é local;
- contador diz `N selecionados nesta visão`;
- botão diz `Adicionar N à bandeja`;
- abrir outra Bin limpa a seleção local.

### Fora do modal

- Bandeja permanece;
- contador diz `N itens preparados`;
- botão diz `Usar N no tópico`;
- Desfazer e Limpar agem sobre a Bandeja.

## Multi-Bin

Exemplo:

1. Pessoas → João → Adicionar à bandeja;
2. Documentos → ficha.pdf → Adicionar à bandeja;
3. Imagens → foto.jpg → Adicionar à bandeja;
4. Bandeja = 3;
5. Usar 3 em Qualificação.

## Smart Bins

Não foram alteradas conceitualmente.

Elas continuam baseadas em:

- contexto;
- proveniência;
- workflow;
- origem assistida.

## Banco

Nenhuma migration.
