# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.8  
**Data:** 2026-08-22  
**Status:** Baseline funcional após AT-06B5.1  
**Produto:** CIRCE-ATHENA

## 1. Fluxo consolidado

`Caso → Pool → Tópico de Trabalho → Recorte → Nota do Analista → Athena → Achado validado → Seção → Produto`

O sistema deve conduzir o usuário pela atividade atual sem exigir conhecimento da arquitetura interna.

## 2. Caso nativo

ATHENA deve criar e gerir casos sem dependência do Intel Desk ou outra origem externa.

O caso possui identidade técnica própria e pode receber materiais:

- no momento da criação;
- posteriormente pelo Workspace;
- por futuras integrações autorizadas.

Integrações externas podem enriquecer um caso, mas não são requisito para sua existência.

## 3. Intake e organização automática

Princípio de produto:

> **O usuário não organiza o ATHENA para poder investigar. O ATHENA organiza o material para que o usuário possa investigar.**

Não existe Bin `Entrada` na experiência normal.

O processamento técnico pode ter estados internos, mas o material deve aparecer diretamente em visões úteis do Pool.

### 3.1 Classificação AT-06B5.1

Enquanto OCR/indexação semântica ainda não estão implementados, o intake nativo executa classificação determinística mínima:

- documentos;
- imagens;
- áudios;
- vídeos.

PDFs, DOCX, planilhas e arquivos não reconhecidos entram em Documentos.

Imagens entram em Imagens.

Áudios entram em Áudios.

Vídeos entram em Vídeos.

### 3.2 Evolução

Com OCR, parsers e indexação:

- Ordem de Serviço;
- BO;
- Laudo;
- ficha de qualificação;
- conversação;
- pessoa;
- local;
- aparelho;
- ocorrência;
- outros subtipos

serão identificados automaticamente.

Uma ficha de pessoa poderá aparecer em Documentos, Pessoas e Smart Bins sem duplicação física do original.

## 4. Bins e Smart Bins

Bin é uma visão organizacional.

Smart Bin é uma visão calculada por regra.

Nenhuma Bin/Smart Bin duplica nem move o artefato original.

### Bins atuais

- Pessoas;
- Documentos;
- Imagens;
- Áudios;
- Vídeos;
- Vínculos;
- Anotações.

### Smart Bins atuais

- Relevante ao tópico;
- Seleção atual;
- Notas assistidas.

Smart Bins semânticas permanecem condicionadas à indexação real.

## 5. Pool Browser modal

A coluna do Pool deve permanecer enxuta.

Ao clicar em uma Bin ou Smart Bin, abre-se um **Pool Browser modal** grande, reutilizável para qualquer visão.

O Browser contém:

- identificação da Bin/Smart Bin;
- lista de elementos;
- preview;
- seleção múltipla;
- destino atual;
- ação `Usar no tópico`.

Comportamento:

- clique: seleção única;
- Ctrl/Cmd + clique: múltipla seleção;
- Shift + clique: intervalo;
- Ctrl/Cmd + A: seleção da visão;
- hover/foco: preview rápido;
- Escape/clique no backdrop: fecha Browser;
- drag permanece disponível quando fizer sentido.

O Browser modal evita tentar operar grandes volumes de evidência numa coluna estreita.

## 6. Composer Athena

O composer deve seguir uma proporção semelhante a ferramentas conversacionais modernas:

- largura máxima controlada;
- centralizado;
- altura inicial compacta;
- crescimento automático conforme o texto;
- máximo de altura;
- scroll interno depois do limite;
- não cresce apenas porque Inspector ou janela ficaram maiores.

Em painel estreito ele ocupa a largura disponível.

Em painel destacado/tela cheia permanece compacto.

## 7. Tópicos

A progressão horizontal continua como mapa do relatório.

Exemplo:

`Cabeçalho → Dos Fatos → Objetos → Qualificação → Análises → Considerações → Conclusão`

O Tópico ativo responde:

> **O que estou fazendo agora?**

Pool, Mesa e Inspector devem refletir esse contexto.

## 8. Inspector

Durante elaboração:

- contexto;
- apoio Athena;
- revisão;
- pendências.

Após conclusão:

- preview do Tópico/Seção deve ocupar o Inspector.

Esse preview permanece requisito do próximo ciclo de composição.

## 9. Editabilidade e controle do usuário

Premissa transversal:

> Dados inseridos, corrigidos ou produzidos pelo usuário devem poder ser posteriormente editados, complementados, removidos ou reclassificados, respeitando auditoria e preservação de origem.

O Workspace é a superfície preferencial, mas outras telas podem fornecer CRUD contextual quando útil.

Exclusão de informação ou artefato não deve apagar silenciosamente seu histórico auditável.

## 10. Fora do escopo AT-06B5.1

- OCR;
- embeddings;
- classificação semântica;
- reconhecimento automático de ficha Vinculum;
- preview binário real de PDF/imagem/áudio/vídeo;
- editor de Smart Bins;
- cabeçalho institucional estruturado;
- sidebar colapsável;
- Voice Note real.

## 11. Próxima vertical sugerida

`OS + BO reais → extração do Cabeçalho → confirmação humana → concluir Tópico → preview institucional no Inspector`.
