# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.13  
**Data:** 2026-08-23  
**Status:** Baseline funcional após AT-06B6.3  
**Produto:** CIRCE-ATHENA

## 1. Fluxo consolidado

`Caso → Pool → Tópico → Bandeja da Mesa → mapa factual → contexto do analista → narrativa → confirmação → Produto`

O usuário fornece material e conhecimento. ATHENA organiza, extrai, estrutura e compõe, mantendo revisão humana e proveniência.

## 2. Pool e intake contínuo

O Pool volta a ter uma entrada global de material.

O usuário pode:

- clicar `+ Importar material`;
- arrastar arquivos para a área global de intake do Pool;
- importar diretamente em uma Bin específica.

Quando o material entra pelo intake global, ATHENA executa a triagem automática atualmente disponível por tipo técnico:

- documentos;
- imagens;
- áudios;
- vídeos.

Quando o usuário importa diretamente em uma Bin, essa escolha humana funciona como classificação explícita inicial.

A classificação semântica de OS, BO, laudo, ficha, pessoa, aparelho etc. continua condicionada a OCR/parsers/indexação.

## 3. Seleção e Bandeja

Mantém-se a arquitetura B6.2:

- Bin / Smart Bin = visão;
- seleção local = estado daquela visão;
- Bandeja da Mesa = seleção multibin preparada;
- proveniência = relação persistente com o Tópico.

## 4. Dos Fatos / Introdução

O Tópico `facts` deixa de usar um textarea genérico e ganha composição orientada.

### 4.1 Etapa 1 — fontes

OS, BO e outros PDFs são reunidos na Bandeja da Mesa.

### 4.2 Etapa 2 — mapa factual

ATHENA lê a camada textual dos PDFs e propõe um mapa estruturado:

- origem da apuração;
- natureza do fato;
- data/período;
- local;
- vítimas/alvos;
- pessoas mencionadas;
- síntese objetiva;
- delimitação da análise.

Cada item pode conter:

- valor;
- documento-fonte;
- página;
- trecho;
- confiança;
- observação de conflito/limitação.

Estados:

- proposto;
- confirmado;
- ignorado.

ATHENA não confirma os fatos automaticamente.

## 5. Contexto do analista

O policial pode registrar contexto humano complementar.

Nesta etapa o input é textual e já constitui o contrato futuro do Voice Note.

A origem humana é preservada. Inferência/opinião não vira fato documental automaticamente.

## 6. Narrativa em blocos

Após revisão do mapa factual, ATHENA compõe no máximo três blocos:

1. origem/contextualização;
2. síntese dos fatos;
3. delimitação/objetivo da análise.

Cada bloco é editável separadamente.

A composição usa somente:

- fatos confirmados;
- contexto humano autorizado.

Nada fora dessas fontes pode ser inventado.

## 7. Preview no Inspector

O Inspector passa a mostrar o tópico como página do relatório:

`1. DOS FATOS`

Os blocos editados na Mesa atualizam a prévia.

## 8. Confirmação do Tópico

`Confirmar Dos Fatos`:

- persiste a narrativa revisada;
- marca a composição como confirmada;
- conclui o Tópico;
- preserva fontes e fatos confirmados;
- sincroniza metadados no Acervo de Produção.

O botão genérico `Concluir tópico` não deve encerrar Dos Fatos sem passar por essa revisão.

## 9. Acervo de Produção

Fatos confirmados passam a integrar o índice do produto.

Exemplos de metadados pesquisáveis:

- natureza do fato;
- data/período;
- local;
- pessoas/vítimas mencionadas;
- origem da apuração;
- objetivo da análise.

O produto só é marcado como concluído no Acervo quando todos os Tópicos do roteiro estiverem concluídos.

## 10. Smart Bins

Permanecem:

- Relevante ao tópico;
- Usados no tópico;
- Ainda não usados;
- Notas assistidas.

As fontes persistidas na composição de Dos Fatos passam a alimentar `Usados no tópico` por proveniência.

## 11. Limites atuais

Não entram em B6.3:

- OCR de PDF-imagem;
- Voice Note real;
- extração semântica completa de entidades;
- Smart Bins semânticas;
- regeneração individual de bloco por comando natural;
- versionamento avançado de narrativa.

## 12. Banco

Nova migration:

`0013_at06b63_facts_topic_composition`
