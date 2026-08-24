# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.10  
**Data:** 2026-08-23  
**Status:** Baseline funcional para AT-06B6  
**Produto:** CIRCE-ATHENA

## 1. Fluxo consolidado

`Caso → Pool → Tópico de Trabalho → Recorte → Nota do Analista → Athena → Achado validado → Seção → Produto → Acervo de Produção`

O relatório não termina na exportação. O produto final e seus metadados devem permanecer pesquisáveis no acervo do próprio policial.

## 2. Cabeçalho estruturado

O Cabeçalho é um objeto editável e auditável.

Campos institucionais vêm de template/preset:

- Estado;
- Secretaria;
- Órgão;
- Diretoria;
- Delegacia;
- Seção / Núcleo / Cartório;
- rótulo do produto.

Campos operacionais:

- número oficial;
- data do relatório;
- assunto;
- origem;
- difusão;
- difusão anterior;
- referências;
- anexos.

Número oficial pode permanecer em branco até obtenção no numerador institucional.

## 3. Extração assistida do Cabeçalho

AT-06B6 implementa a primeira automação documental real.

### 3.1 Fontes

O policial seleciona no Pool os PDFs que devem sustentar o Cabeçalho, por exemplo:

- Ordem de Serviço;
- Boletim de Ocorrência;
- laudo;
- medida judicial;
- outros documentos pertinentes.

### 3.2 Processo

`PDF original → extração da camada textual → Athena → proposta estruturada → revisão humana → confirmação`

Nesta etapa não há OCR. PDF sem camada textual deve ser sinalizado explicitamente como dependente de OCR futuro.

### 3.3 Campos propostos pela Athena

- assunto;
- origem;
- difusão;
- difusão anterior;
- referências;
- anexos.

A data do relatório e o número oficial não são inferidos dos documentos.

### 3.4 Proveniência por campo

Cada proposta registra:

- campo;
- valor extraído;
- documento-fonte;
- página;
- trecho de suporte;
- confiança declarada pelo extrator;
- método de extração;
- estado da proposta.

Athena não confirma um valor automaticamente.

### 3.5 Estados

`draft → proposed → confirmed`

Se o usuário editar um cabeçalho já confirmado, ele retorna ao estado de revisão.

O Tópico Cabeçalho só deve ser considerado concluído pelo comando explícito **Confirmar cabeçalho**.

## 4. Acervo de Produção

Premissa:

> **Cada relatório produzido pelo policial passa a integrar seu acervo de produção e deve continuar recuperável por seus metadados anos depois.**

O acervo é parte estrutural do produto, não um histórico secundário.

### 4.1 Produto persistente

O relatório recebe identidade própria antes mesmo da exportação DOCX/PDF.

Metadados iniciais:

- chave interna do produto;
- caso;
- workspace;
- proprietário/autor;
- tipo do produto;
- título;
- status;
- número do relatório;
- data;
- assunto;
- timestamps de criação/atualização/conclusão.

### 4.2 Índice de metadados

O índice deve aceitar enriquecimento incremental ao longo do relatório.

AT-06B6 indexa inicialmente:

- referência interna do caso;
- título do caso;
- classificação;
- unidade;
- número do relatório;
- data;
- assunto;
- origem;
- difusão;
- difusão anterior;
- referências documentais;
- anexos;
- nomes das pessoas do caso;
- CPF;
- RG;
- aliases disponíveis.

Futuras seções devem acrescentar locais, coordenadas, aparelhos, telefones, veículos, contas, eventos, achados e demais entidades estruturadas.

### 4.3 Recuperação pela Athena

Fora de um Workspace ativo, a Athena pode consultar o acervo do operador por metadados.

Exemplos de intenção:

- “Que relatório eu fiz referente ao IP 212.4.2025.1440?”
- “Qual relatório meu menciona Fulano de Tal?”
- “Eu produzi algum relatório envolvendo o CPF 123.456.789-00?”

Resultados do acervo entram no contexto com fonte `REPORT:<product_key>`.

### 4.4 Cenário de audiência

Objetivo futuro suportado pela arquitetura:

`consulta por metadado → localizar relatório → abrir produto preservado → resumir → gerar briefing para audiência`

A geração do briefing deverá usar somente o relatório e os dados vinculados ao produto localizado, preservando proveniência.

## 5. Pool

O Pool continua sendo fonte de verdade documental do caso.

Artefatos são preservados uma vez; Bins e Smart Bins são visões e não cópias.

## 6. Editabilidade

Dados inseridos pelo usuário permanecem editáveis, complementáveis, reclassificáveis e removíveis sob auditoria.

Edição após confirmação deve alterar o estado de revisão correspondente.

## 7. Segurança epistemológica

- extração não equivale a fato investigativo;
- proposta da Athena não equivale a confirmação;
- ausência de campo deve permanecer ausência;
- conflito entre documentos não deve ser resolvido silenciosamente;
- OCR futuro deve preservar ligação com original/página;
- metadado de acervo serve para recuperação, não para produzir conclusão investigativa por si só.

## 8. Fora do escopo da AT-06B6

- OCR de PDF digitalizado;
- extração de imagem/foto de qualificação;
- importação Cellebrite;
- exportação DOCX/PDF final;
- UI dedicada “Meu Acervo”;
- briefing de audiência pronto;
- busca semântica vetorial do acervo;
- indexação do texto completo do produto.

## 9. Próximo passo após validação

Se a extração do Cabeçalho funcionar satisfatoriamente com OS/BO/laudo reais:

`Cabeçalho confirmado → Dos Fatos / Introdução → proposta assistida com as mesmas fontes → preview no Inspector`
