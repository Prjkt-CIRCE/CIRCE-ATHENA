# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.11  
**Data:** 2026-08-23  
**Status:** Baseline funcional após AT-06B6.1  
**Produto:** CIRCE-ATHENA

## 1. Princípio operacional

O usuário não organiza o ATHENA para poder investigar.

> **O ATHENA organiza o material para que o usuário possa investigar.**

O Pool é um acervo operacional, não um formulário nem um gerenciador de arquivos genérico.

## 2. Bins

Bins são visões de organização explícita do acervo.

Bins atuais:

- Pessoas;
- Documentos;
- Imagens;
- Áudios;
- Vídeos;
- Vínculos;
- Anotações.

### 2.1 Importação direta

O botão global `Adicionar material` não deve existir no Pool.

O fluxo preferencial é:

1. clicar na Bin desejada;
2. usar `Importar arquivos nesta Bin`;

ou:

1. arrastar arquivos do sistema operacional;
2. soltar diretamente sobre a Bin desejada.

A escolha explícita de uma Bin pelo policial é uma ação humana deliberada e prevalece sobre a classificação automática inicial.

Na criação do caso, quando não há Bin explicitamente indicada, ATHENA continua executando classificação determinística por tipo.

### 2.2 Pessoas

Enquanto a extração semântica ainda não estiver ativa, um PDF/foto colocado deliberadamente em `Pessoas` é tratado como material associado àquela classe, sem afirmar automaticamente que uma entidade Pessoa foi extraída.

A futura indexação deverá transformar ficha + foto + dados estruturados em entidade Pessoa sem duplicar os originais.

## 3. Smart Bins

Smart Bin é uma **visão calculada**, não uma pasta física.

Regras:

- nunca move o original;
- nunca cria cópia do original;
- pode mostrar a mesma fonte em várias visões;
- deve deixar clara a diferença entre regra determinística e resultado semântico/IA.

### 3.1 Revisão conceitual AT-06B6.1

`Seleção atual` deixa de ser Smart Bin.

Seleção é estado transitório da interface e não uma visão de conhecimento do caso.

Smart Bins atuais:

### Relevante ao tópico

Context Bin determinística.

A regra muda conforme o Tópico de Trabalho ativo.

Exemplos atuais:

- Cabeçalho → documentos e anotações;
- Dos Fatos → documentos, pessoas, vínculos e anotações;
- Objetos de análise → documentos e imagens;
- Qualificação → pessoas, documentos e imagens;
- Análise de imagens → imagens;
- Conversações → documentos, áudios e anotações;
- Considerações/Conclusão → visão ampla.

Essas regras são conservadoras e não equivalem a análise semântica.

### Usados no tópico

Mostra fontes que já possuem relação de proveniência com o Tópico ativo.

No Cabeçalho, deriva das fontes persistidas no cabeçalho.

Nos Tópicos analíticos, deriva das fontes de Recortes/Achados vinculados ao Tópico.

### Ainda não usados

Mostra material do caso que ainda não possui relação de proveniência com o Tópico ativo.

É uma visão de workflow, não uma inferência investigativa.

### Notas assistidas

Filtra anotações produzidas pelo fluxo assistido da Athena.

## 4. Seleção no Pool Browser

A seleção mostrada no rodapé do modal deve ser **da visão atualmente aberta**.

Exemplo:

- Documentos possui 2 elementos selecionados;
- usuário abre Pessoas vazia;
- rodapé de Pessoas deve mostrar `0 itens selecionados nesta Bin`;
- jamais `Usar 2 na Mesa`.

A seleção global pode existir tecnicamente no Workspace, mas não deve “vazar” visualmente entre Bins.

## 5. Pool Browser

Cada Bin/Smart Bin abre o mesmo Browser modal:

`Lista | Preview`

O preview usa:

- PDF incorporado quando disponível;
- imagem;
- áudio;
- vídeo;
- metadados quando não houver renderização especializada.

O Browser é a superfície de seleção e envio para a Mesa.

## 6. Mesa

`Usar N na Mesa` deve considerar apenas os itens selecionados na visão atual.

No Tópico Cabeçalho, as fontes efetivamente persistidas aparecem separadamente como:

`Materiais usados neste cabeçalho`

Assim:

- seleção transitória;
- fonte persistida;
- Smart Bin `Usados no tópico`

não são confundidas.

## 7. Cabeçalho

Permanece o primeiro Tópico estruturado completo.

A extração B6 continua baseada em PDF textual, com:

- proposta Athena;
- proveniência documento/página/trecho;
- revisão humana;
- confirmação;
- indexação no Acervo de Produção.

## 8. Smart Bins futuras

Quando a infraestrutura suportar:

### Determinísticas

- adicionados recentemente;
- OCR pendente;
- indexação pendente;
- conflitos de metadados;
- não analisados;
- utilizados no produto;
- não utilizados no produto;
- por pessoa;
- por dispositivo;
- por período;
- por interlocutor.

### Semânticas

Devem ser identificadas visualmente como resultados assistidos por IA.

Exemplos:

- material relacionado ao planejamento do roubo;
- menções compatíveis com arma de fogo;
- conversações sobre divisão de valores.

Nenhuma Smart Bin semântica será simulada antes da indexação real.

## 9. Premissa de proveniência

A força das Smart Bins depende de bons metadados.

Todo produto produzido deve preservar metadados suficientes para:

- recuperação futura;
- pesquisa por caso/BO/IP/processo;
- pesquisa por pessoa/CPF/RG;
- pesquisa por assunto;
- briefing posterior para audiência.

## 10. Banco

AT-06B6.1 não requer migration.

Alembic permanece em:

`0012_at06b6_header_extraction_archive`
