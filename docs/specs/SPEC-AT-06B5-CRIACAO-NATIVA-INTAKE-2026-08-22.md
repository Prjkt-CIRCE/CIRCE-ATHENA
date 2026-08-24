# SPEC AT-06B5 — Criação Nativa de Caso & Intake Inicial

**Data:** 2026-08-22  
**Status:** Implementação incremental  
**Projeto:** CIRCE-ATHENA

## Objetivo

Eliminar a dependência operacional de casos provenientes do legado/Intel Desk e permitir que o ATHENA seja o ponto de nascimento de uma investigação.

## Entrega

- `+ Novo caso` no Gestor de Investigações;
- formulário mínimo;
- UUID e referência técnica gerados pelo ATHENA;
- origem nativa registrada;
- anexos iniciais opcionais;
- SHA-256 e preservação local;
- Bin `Entrada`;
- criação automática do Workspace;
- roteiro móvel opcional na criação;
- `+ Adicionar material` no Pool para evolução do caso;
- auditoria;
- deduplicação por hash no mesmo caso.

## Não implementar nesta etapa

- OCR;
- leitura automática da OS;
- classificação inteligente de arquivo;
- cabeçalho institucional estruturado;
- número oficial do relatório;
- edição de regras de Bins.

## Critério de aceite

Um policial deve conseguir, sem qualquer integração externa:

1. abrir o Gestor;
2. clicar `+ Novo caso`;
3. informar título;
4. anexar OS/BO/fotos;
5. criar;
6. chegar ao Workspace com os arquivos em `Entrada`;
7. adicionar novo material depois;
8. manter hash, origem e auditoria.
