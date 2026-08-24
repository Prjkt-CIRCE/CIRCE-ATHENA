# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.14  
**Data:** 2026-08-23  
**Status:** Baseline funcional após AT-06B6.4  
**Produto:** CIRCE-ATHENA

## 1. Objetivo desta revisão

A extração factual de `Dos fatos / introdução` foi validada com documentos reais.

O problema observado deixou de ser primariamente de extração e passou a ser de **leitura, revisão e ergonomia da Mesa**.

A Mesa não deve expor o mecanismo interno como uma sequência longa de formulários.

## 2. Estrutura do tópico Dos Fatos

A Mesa passa a organizar o trabalho em quatro camadas:

1. Fontes;
2. Dados estruturados;
3. Síntese documental;
4. Contexto/delimitação do analista;
5. Narrativa.

Fluxo:

`fontes → mapa factual compacto → confirmação → contexto humano → narrativa → preview → confirmação do tópico`

## 3. Dados estruturados

Dados como:

- origem da apuração;
- natureza;
- data/período;
- local;
- vítimas/alvos;
- pessoas mencionadas

devem ser visíveis em **linhas compactas**.

Estado normal:

`Campo | valor | estado | fonte/página`

O detalhe completo fica recolhido.

Ao expandir:

- editar valor;
- alterar estado;
- abrir fonte;
- visualizar trecho usado;
- ler notas/limitações.

## 4. Estados factuais

Estados atuais:

- proposto;
- confirmado;
- ignorado.

Visualmente devem aparecer como badges, não como selects permanentes.

O select continua disponível apenas quando o item é expandido.

A arquitetura permanece preparada para um futuro estado `conflito`.

## 5. Proveniência

A proveniência continua obrigatória, mas deixa de ocupar espaço permanente.

Visão compacta:

`B.O. nº ... · p.1`

Ação:

`Ver fonte`

Detalhe opcional:

`Ver trecho usado`

Sempre que possível o PDF deve abrir já na página referenciada.

## 6. Síntese documental

`Síntese objetiva do fato` não deve competir visualmente com campos atômicos.

Ela passa a uma seção própria: **Síntese documental**.

É matéria-prima narrativa derivada de fonte documental e permanece sujeita à revisão humana.

## 7. Delimitação da análise

`Delimitação desta análise` é tratada de forma diferenciada.

Mesmo quando houver referência documental, seu significado depende da finalidade do relatório e do recorte deliberado pelo policial.

Ela passa para a área:

**Contexto e delimitação do analista**

junto da nota/contexto humano.

Isso não altera a proveniência existente.

## 8. Confirmação do mapa factual

O comando `Confirmar itens preenchidos` é substituído por:

`Confirmar mapa factual`

Ao confirmar:

- itens preenchidos e não ignorados tornam-se confirmados;
- itens vazios permanecem não confirmados;
- o mapa é persistido;
- o sistema informa quantos itens foram confirmados e quantos permanecem vazios.

## 9. Infraestrutura técnica

O protótipo `Infraestrutura técnica AT-06A — blocos` deixa de aparecer nos Tópicos estruturados:

- Cabeçalho;
- Dos fatos / introdução.

A infraestrutura permanece no código, sem competir com a tarefa operacional.

## 10. Contexto do analista

A área humana permanece distinta do mapa documental.

Futura entrada por Voice Note utiliza a mesma camada de dados.

Opinião, inferência e dúvida não são convertidas automaticamente em fato documental.

## 11. Narrativa

A narrativa continua sendo composta somente depois da revisão do mapa.

Permanece editável bloco a bloco.

O Inspector continua mostrando o produto, não o mecanismo de extração.

## 12. Banco

AT-06B6.4 é uma revisão de superfície e interação.

**Nenhuma migration.**

Alembic permanece em:

`0013_at06b63_facts_topic_composition`
