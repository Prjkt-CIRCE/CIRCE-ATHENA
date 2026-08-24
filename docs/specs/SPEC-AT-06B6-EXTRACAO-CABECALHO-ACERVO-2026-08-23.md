# SPEC AT-06B6 — Extração Assistida do Cabeçalho + Acervo de Produção

**Data:** 2026-08-23  
**Status:** Implementação incremental  
**Projeto:** CIRCE-ATHENA

## Objetivos

1. Ler PDFs locais já vinculados ao Tópico Cabeçalho.
2. Propor automaticamente campos operacionais.
3. Mostrar proveniência por campo.
4. Exigir confirmação humana.
5. Criar a fundação do acervo pessoal de produção.
6. Permitir que a Athena recupere relatórios por metadados mesmo fora do Workspace ativo.

## Extração

Campos:

- assunto;
- origem;
- difusão;
- difusão anterior;
- referências;
- anexos.

Não extrair:

- data do relatório;
- número oficial do relatório.

## PDF

AT-06B6 usa `pypdf` para PDFs com camada textual.

Limites do piloto:

- até 14 páginas por documento para a tarefa Cabeçalho;
- contexto total limitado;
- PDF sem texto gera aviso de OCR necessário.

## Proveniência

Cada campo proposto recebe:

`documento + página + trecho + confiança + método`

A interface não substitui silenciosamente um valor humano já digitado: mostra a proposta e oferece **Usar proposta**.

## Confirmação

`Salvar rascunho` não conclui o Cabeçalho.

`Confirmar cabeçalho`:

- salva a versão revisada;
- registra o operador;
- registra timestamp;
- conclui o Tópico;
- sincroniza o produto no acervo.

## Acervo

Tabelas conceituais:

- `report_products`;
- `report_metadata_index`.

O produto possui chave estável `RPT-...`.

Busca inicial suporta metadados textuais/numerados, incluindo:

- IP/inquérito;
- BO;
- OS;
- processo;
- número do relatório;
- nome de parte;
- CPF;
- RG.

## Athena

Consultas fora de caso ativo passam a consultar o acervo do próprio operador.

O resultado é anexado ao contexto local como `REPORT:<product_key>`.

## Migration

`0012_at06b6_header_extraction_archive`

## Dependência

`pypdf` é necessária para extração textual de PDF.

O instalador verifica a dependência e instala somente se ausente.
