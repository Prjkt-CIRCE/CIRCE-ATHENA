# SPEC AT-06B5.1 — Pool Browser Modal + Composer Compacto

**Data:** 2026-08-22  
**Status:** Implementação incremental  
**Projeto:** CIRCE-ATHENA

## Objetivo

Corrigir dois problemas de superfície observados no piloto real:

1. conteúdo de Bins/Smart Bins não deve ser navegado dentro da coluna estreita do Pool;
2. composer da Athena não deve aumentar proporcionalmente quando o Inspector ocupa grande área.

O incremento também elimina da experiência visível a Bin `Entrada`.

## Pool Browser

Clique em qualquer Bin/Smart Bin abre Browser modal central.

Estrutura:

`Lista de elementos | Preview`

Rodapé:

`seleção atual | destino | Usar no tópico`

Fechamento:

- botão `Fechar`;
- Escape;
- clique no backdrop.

## Intake

Novos arquivos passam diretamente para classificação determinística:

- Documento;
- Imagem;
- Áudio;
- Vídeo.

Não existe Bin Entrada para o usuário.

Classificação semântica virá com OCR/indexação.

## Composer

- shell central;
- max-width 760 px;
- altura mínima aproximada de uma linha;
- auto-grow até 160 px;
- sem resize manual;
- comportamento idêntico no Inspector encaixado ou destacado, respeitando apenas a largura disponível.

## Banco

Nenhuma migration.

Alembic permanece em:

`0010_at06b5_native_case_intake`

## Critérios de aceite

- não aparece Bin Entrada;
- três PDFs existentes aparecem em Documentos;
- novo JPG entra em Imagens;
- novo áudio entra em Áudios;
- novo vídeo entra em Vídeos;
- Bin/Smart Bin abre modal;
- modal exibe conteúdo e preview;
- seleção do modal pode ser usada no Tópico;
- composer permanece compacto em tela cheia;
- smoke B5 continua válido;
- smoke B5.1 passa.
