# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.9  
**Data:** 2026-08-22  
**Status:** Baseline funcional após AT-06B5.2  
**Produto:** CIRCE-ATHENA

## 1. Princípios consolidados

O Workspace deve responder continuamente:

> **O que estou fazendo agora?**

Fluxo:

`Caso → Pool → Tópico de Trabalho → Recortes/Achados → Seção → Produto`

O usuário não precisa conhecer a arquitetura interna da plataforma para trabalhar.

## 2. Pool

O Pool é o acervo operacional do caso.

### 2.1 Bins e Smart Bins

Bins são visões organizacionais.

Smart Bins são visões calculadas por regra.

Um artefato existe uma vez e pode aparecer em várias visões sem duplicação física.

### 2.2 Pool Browser

Bins e Smart Bins não devem despejar seu conteúdo na coluna estreita do Workspace.

Clique em uma Bin abre o **Pool Browser** em modal central de tamanho controlado.

Estrutura:

`Lista / seleção | Preview`

O Browser é uma superfície de triagem para a Mesa de Trabalho.

Interações:

- clique;
- Ctrl/Cmd;
- Shift;
- hover/foco para preview;
- `Usar na Mesa`;
- materiais enviados passam a aparecer explicitamente na Mesa como fontes do Tópico;
- drag and drop quando apropriado.

### 2.3 Preview real

Para material nativo preservado localmente:

- PDF → preview embutido;
- imagem → preview visual;
- áudio → player;
- vídeo → player.

OCR e extração textual permanecem etapa posterior.

## 3. Tópico Cabeçalho

O Cabeçalho é um objeto estruturado e persistente.

### 3.1 Template inicial PJC-MT

O primeiro template reproduz o padrão visual fornecido para a Polícia Civil de Mato Grosso, incluindo o brasão estadual e o emblema institucional no preview.

Estrutura institucional:

1. Estado;
2. Secretaria;
3. Órgão;
4. Diretoria;
5. Delegacia;
6. Seção / Núcleo / Cartório.

Depois:

- tipo do relatório;
- número oficial;
- data;
- assunto;
- origem;
- difusão;
- difusão anterior;
- referências;
- anexos.

O número oficial pode permanecer em branco até ser obtido no numerador institucional.

### 3.2 Template editável

Todos os campos institucionais podem ser editados no Workspace.

O usuário pode salvar o enquadramento institucional atual como **novo template**.

Um template aplicado ao relatório é copiado para o cabeçalho do caso; alterações futuras no template não devem reescrever silenciosamente relatórios já existentes.

### 3.3 Fontes

Documentos selecionados no Pool podem ser vinculados ao Cabeçalho como fontes.

AT-06B5.2 registra a proveniência dessas fontes, mas ainda não extrai automaticamente os campos da OS/BO.

A próxima vertical fará:

`OS/BO → extração de campos → proposta → confirmação humana`.

### 3.4 Preview no Inspector

Enquanto o Tópico Cabeçalho estiver ativo, o Inspector mostra a aparência do cabeçalho do relatório em tempo real.

Editar a Mesa atualiza a prévia.

Ao concluir o Tópico, o preview permanece disponível.

## 4. Composer Athena

O composer permanece compacto, centralizado e com crescimento limitado, independentemente de o Inspector estar encaixado ou destacado.

## 5. Editabilidade

Premissa transversal:

> Tudo que o usuário inseriu ou corrigiu deve poder ser posteriormente editado, complementado, reclassificado ou removido, preservando auditoria.

O Workspace é a superfície preferencial, sem impedir CRUD contextual em outras telas.

## 6. Fora do escopo AT-06B5.2

- OCR;
- extração automática de OS/BO;
- embeddings;
- Smart Bins semânticas;
- upload/configuração visual dos brasões;
- DOCX/PDF final;
- Voice Note real.

## 7. Próxima vertical

`OS + BO reais → extração automática do Cabeçalho → revisão humana → conclusão → início de Dos Fatos`.
