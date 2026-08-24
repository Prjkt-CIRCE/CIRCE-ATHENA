# SPEC AT-06B5.2 — Pool Preview + Cabeçalho Estruturado

**Data:** 2026-08-22  
**Status:** Implementação incremental  
**Projeto:** CIRCE-ATHENA

## Objetivo

1. reduzir e resolver melhor o Pool Browser;
2. dar preview real dos originais nativos;
3. tornar a seleção do modal efetivamente material da Mesa;
4. implementar o Cabeçalho como primeiro componente real do produto final.

## Pool Browser

- modal menor, central e deliberadamente não full-screen;
- lista à esquerda;
- preview real à direita;
- PDF em iframe;
- imagem em `img`;
- áudio em player;
- vídeo em player;
- seleção múltipla;
- botão `Usar na Mesa`;
- materiais escolhidos aparecem explicitamente na Mesa como fontes do Tópico.

## Cabeçalho

Template inicial reproduz o padrão institucional fornecido pelo usuário, incluindo os dois elementos gráficos do cabeçalho:

- brasão do Estado de Mato Grosso;
- emblema da Polícia Civil de Mato Grosso;
- ESTADO DE MATO GROSSO
- SECRETARIA DE ESTADO DE SEGURANÇA PÚBLICA
- POLÍCIA CIVIL
- DIRETORIA METROPOLITANA
- DELEGACIA ESPECIALIZADA EM REPRESSÃO A ROUBOS E FURTOS DE CUIABÁ
- NÚCLEO DE INTELIGÊNCIA
- RELATÓRIO TÉCNICO Nº

Campos:

- data;
- assunto;
- origem;
- difusão;
- difusão anterior;
- referências;
- anexos.

Todos são editáveis.

## Templates

O usuário pode modificar a estrutura institucional e salvar como novo template.

AT-06B5.2 não implementa ainda gestão completa de templates em Configurações.

## Inspector

Quando `Cabeçalho` é o Tópico ativo, o Inspector exibe uma prévia branca do documento, atualizada ao editar os campos.

## Proveniência

As fontes selecionadas no Pool são persistidas no Cabeçalho.

## Banco

Migration:

`0011_at06b52_report_header`

Tabelas:

- `report_header_templates`;
- `workspace_report_headers`;
- `workspace_report_header_sources`.

A migration também normaliza materiais nativos legados ainda marcados como `inbox` para `documents`.

## Limite deliberado

Não existe extração automática da OS/BO neste incremento.

O objetivo é fechar o contrato estrutural e visual do Cabeçalho antes de ligar OCR/extração.
