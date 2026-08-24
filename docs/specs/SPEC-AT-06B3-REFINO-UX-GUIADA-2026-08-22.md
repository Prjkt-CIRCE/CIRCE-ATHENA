# SPEC AT-06B3 — Refino de UX Guiada do Workspace

**Data:** 2026-08-22  
**Projeto:** CIRCE-ATHENA  
**Unidade técnica:** AT-06B3  
**Status:** Pronto para implementação  
**Base:** AT-06B2 / Alembic `0009_at06b2_work_topics`

## 1. Problema observado

O AT-06B2 provou o modelo de Tópicos de Trabalho, seleção desktop do Pool e panes destacáveis, mas o teste de uso revelou que a interface ainda exige conhecimento excessivo da arquitetura interna.

O usuário deve ser conduzido sem infantilização. A experiência deve reduzir ambiguidade operacional e responder continuamente:

1. em qual caso estou;
2. o que estou fazendo agora;
3. qual é a próxima ação útil.

Também foram observados dois defeitos visuais concretos:

- comandos dos panes sobrepostos após colapso;
- scrollbars nativas claras destoando do tema escuro.

## 2. Princípio de UX

> A plataforma deve orientar o fluxo sem transformar o trabalho em um wizard rígido.

O usuário pode circular livremente entre Pool, Mesa e Inspector/Athena, mas o sistema deve tornar evidente o objeto de trabalho ativo e a próxima ação esperada.

## 3. Alterações AT-06B3

### 3.1 Indicador global “AGORA”

O cabeçalho do Workspace deve exibir o Tópico de Trabalho ativo. Na ausência de tópico, deve orientar o usuário a escolher um na Mesa.

### 3.2 Entrada guiada na Mesa

Antes de existir roteiro, a Mesa deve apresentar uma entrada explícita:

- “Comece por aqui”;
- pergunta “O que você vai produzir?”;
- explicação curta do fluxo em três passos;
- ação primária para iniciar o roteiro piloto de análise de celular.

### 3.3 Roteiro como eixo visual

Após iniciar o roteiro, a Mesa deve indicar claramente que os cartões horizontais representam o roteiro do relatório e que o usuário deve escolher o que está fazendo agora.

### 3.4 Próxima ação no Tópico

O cartão do Tópico ativo deve conter uma orientação contextual conforme o estado:

- `pending`: começar o tópico;
- `in_progress`: selecionar fontes do Pool e usá-las no tópico;
- `review`: revisar e concluir ou retornar à elaboração;
- `completed`: reabrir apenas para complementar/corrigir.

### 3.5 Pool orientado ao destino

A seleção permanece no paradigma desktop (clique/Ctrl/Shift/drag-and-drop), mas a barra inferior deve informar o destino atual e a ação primária deve ser contextual:

- sem tópico: escolher um tópico;
- tópico pendente: começar o tópico;
- tópico em elaboração/revisão: usar no tópico.

O botão não deve habilitar análise quando o tópico não estiver apto a receber fontes.

### 3.6 Inspector / Athena contextual

O painel direito passa a se identificar como `Inspector / Athena` e sua mensagem inicial deve explicar o contexto operacional conforme o Tópico ativo.

### 3.7 Controles dos panes

Os comandos de `Destacar` e `Recolher` devem possuir rótulos visíveis em larguras normais.

Ao colapsar um pane:

- `Destacar` desaparece;
- apenas o comando de reabrir permanece no topo;
- o título vertical não pode sobrepor os controles;
- nenhuma ação pode ficar inacessível por sobreposição.

### 3.8 Scrollbars

Todas as áreas do Workspace devem adotar scrollbars discretas e escuras, compatíveis com o design do ATHENA, incluindo o roteiro horizontal de tópicos.

## 4. Fora do escopo

AT-06B3 não altera:

- banco de dados;
- modelos de domínio;
- migrations;
- OCR;
- Voice Note real;
- importador Cellebrite;
- compositor DOCX/PDF;
- snap físico nativo de janelas.

## 5. Critérios de aceite

1. usuário identifica o Tópico atual sem procurar na tela;
2. a tela inicial da Mesa apresenta uma ação de entrada inequívoca;
3. Tópico ativo apresenta uma “Próxima ação” contextual;
4. Pool deixa claro para onde irá a seleção;
5. ação do Pool permanece desabilitada enquanto o Tópico não estiver apto;
6. controles de pane não se sobrepõem ao colapsar;
7. scrollbars claras deixam de aparecer no Workspace;
8. panes destacáveis continuam funcionais;
9. seleção desktop e BroadcastChannel permanecem preservados;
10. smoke AT-06B2 continua passando.
