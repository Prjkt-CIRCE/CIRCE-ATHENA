# CIRCE-ATHENA — PROJECT MASTER CONSOLIDADO

**Data de consolidação original:** 25/08/2026
**Data desta atualização:** 27/08/2026
**Status:** Baseline documental consolidada e atualizada após validação da AT-06B-CURATED-01
**Substitui:** `CIRCE-ATHENA-PROJECT-MASTER-CONSOLIDADO-2026-08-25.md`
**Projeto operacional atual:** CIRCE-ATHENA
**Unidade prioritária:** AT-06 — Workspace Investigativo & Construtor de Peças
**Método de desenvolvimento:** CIRCE — Metodologia Spec-Driven v1.0
**Natureza deste documento:** visão consolidada de produto, arquitetura, roadmap, SPECs, decisões vigentes, estado macro e próximos gates.

---

## 0. Finalidade

Este documento existe para permitir que um novo chat, uma nova sessão de implementação ou outro colaborador técnico compreenda o projeto CIRCE-ATHENA sem reconstruir dezenas de conversas e versões intermediárias.

Ele consolida:

- visão do produto;
- princípios não negociáveis;
- decisões arquiteturais vigentes;
- catálogo funcional;
- roadmap histórico e roadmap corrente;
- escopo da AT-06;
- principais SPECs e mini-SPECs;
- decisões recentes de workflow;
- estado macro de implementação;
- pendências estruturais;
- regras para continuidade.

O estado operacional detalhado, incluindo regressões e bloqueios atuais, está separado no documento:

`CIRCE-ATHENA-SNAPSHOT-ESTADO-ATUAL-2026-08-25.md`

---

# 1. Autoridade documental

A partir de 25/08/2026, a execução deve seguir a metodologia Spec-Driven do projeto.

Ordem recomendada de autoridade:

```text
PRINCÍPIOS / DECISÕES EXPLÍCITAS
        ↓
ADR
        ↓
PROJECT MASTER / SPEC MASTER
        ↓
ROADMAP
        ↓
SPECs
        ↓
PLANOS / SPRINTS / AUDITORIAS
        ↓
IMPLEMENTAÇÃO
        ↓
TESTES / VALIDAÇÃO
        ↓
STATUS / SNAPSHOT / HANDOFF
```

Para o AT-06, o pacote canônico consolidado de 23/08/2026 continua sendo referência histórica e funcional importante, mas deve ser lido junto com:

1. ADR-001 — Arquitetura Soberana e Híbrida;
2. ADR-002 — Organização Funcional em Ferramentas Investigativas;
3. ADR-003 — Safe Mode / Agent Mode;
4. decisões consolidadas de produto da AT-06;
5. SPEC AT-06 e mini-SPECs B3–B6.4;
6. HANDOVER STAB-01;
7. SPEC de Workflow Investigativo para Relatórios de Análise de Dispositivos, de 24/08/2026;
8. decisões posteriores de Design Lab/UX;
9. snapshot operacional mais recente.

Versões históricas não devem ser tratadas como normativas quando conflitarem com decisões posteriores.

---

# 2. Identidade do produto

## 2.1 Situação atual

O software em desenvolvimento e o repositório operacional continuam sendo tratados como **CIRCE-ATHENA**.

Entretanto, a arquitetura estratégica mais recente do ecossistema passou a tratar ATHENA como uma iniciativa preexistente cuja função futura, absorção ou eventual renomeação ainda poderá ser formalizada.

Portanto:

- **CIRCE-ATHENA** continua sendo o nome operacional válido do projeto atual;
- esse nome não deve ser usado para inferir automaticamente que ATHENA será para sempre o nome da plataforma principal do ecossistema;
- mudanças futuras de identidade deverão ocorrer por decisão explícita e sincronização documental.

## 2.2 Definição de produto atual

No recorte AT-06, o CIRCE-ATHENA é um:

> **Workspace Investigativo assistido para organizar evidências, raciocínio, contexto, análise e produção de peças policiais rastreáveis, reduzindo trabalho mecânico sem retirar do policial o julgamento, a autoria e o controle operacional.**

Ele não é simplesmente um “chat com IA” nem um “gerador automático de relatórios”.

---

# 3. Princípios centrais

## 3.1 Soberania

A plataforma é:

> **soberana por padrão, híbrida por necessidade e auditável por princípio.**

Dados e funções sensíveis devem permanecer locais sempre que tecnicamente viável.

Integrações externas devem passar por uma fronteira controlada.

## 3.2 Controle humano

O sistema ajuda, organiza, sugere, analisa e executa tarefas permitidas, mas:

- não substitui a decisão investigativa;
- não transforma hipótese em fato;
- não afirma identidade sem validação;
- não inventa evidência;
- não cria fundamentação factual inexistente;
- não altera material original sem rastreabilidade;
- não executa ação sensível fora das permissões do operador.

## 3.3 Proveniência

Todo elemento relevante deve poder responder:

> **De onde saiu isso?**

A cadeia ideal é:

```text
fonte original
→ elemento extraído
→ validação
→ bloco investigativo
→ seção
→ texto produzido
→ produto final
```

## 3.4 Experiência operacional

O sistema deve reduzir trabalho burocrático, e não criar uma nova burocracia digital.

Quatro invariantes da AT-06:

1. Workspace não pode virar gerenciador de arquivos.
2. Report Builder não pode virar um Word piorado.
3. ATHENA não pode virar um gerador mágico de relatórios.
4. O policial não pode virar alimentador de formulários.

## 3.5 Liberdade operacional do usuário

Premissa de produto:

> **O sistema pode entregar o resultado, mas o usuário deve poder acompanhar, fazer junto, intervir, corrigir ou fazer do seu próprio jeito quando desejar.**

A automação não deve apagar a sensação de controle nem esconder o que está acontecendo.

---

# 4. Arquitetura estratégica vigente

## 4.1 Arquitetura soberana e híbrida

Decisão central:

- local por padrão;
- funcionamento offline das funções essenciais;
- serviços externos opcionais;
- IA desacoplada de fornecedor;
- BYOK possível quando autorizado;
- correlação sensível executada localmente;
- auditoria como requisito de primeira classe.

## 4.2 PÉGASO

PÉGASO é a camada de integração com:

- bancos;
- APIs;
- sistemas internos autorizados;
- serviços externos;
- Internet.

Nenhum módulo interno deve acessar Internet de forma direta e irrestrita.

Responsabilidades:

- autenticação;
- autorização;
- credenciais;
- políticas;
- sanitização;
- minimização de dados;
- logs;
- observabilidade;
- auditoria;
- timeout/retry/circuit breaker.

## 4.3 ÓRION

ÓRION é a ferramenta/módulo de OSINT.

Fluxo conceitual:

```text
Usuário
→ ÓRION
→ PÉGASO
→ fonte externa
→ PÉGASO
→ ÓRION
→ correlação local
```

## 4.4 IA intercambiável

A aplicação deve consumir uma interface abstrata de IA e permitir:

- modelos locais;
- modelos institucionais;
- APIs externas;
- fornecedores substituíveis;
- chaves do usuário quando autorizadas.

## 4.5 SAFE e AGENT

Permissão e autonomia são conceitos distintos.

> **Permissão define o que o operador pode fazer.
> Modo define quanto o assistente pode executar sem interrompê-lo.**

### SAFE

Padrão. Confirmações proporcionais ao risco.

### AGENT

Maior autonomia para executar uma solicitação já autorizada.

Agent Mode:

- não aumenta privilégio;
- não contorna PÉGASO;
- não elimina auditoria;
- não cria ações não suportadas;
- não autoriza iniciativa sem objetivo solicitado.

---

# 5. Catálogo funcional estratégico

A ADR-002 organiza a plataforma em oito ferramentas centrais.

## 5.1 Gestor de Investigações

Responsável por:

- casos;
- pessoas;
- organizações;
- documentos;
- evidências;
- vínculos;
- notas;
- cronologia;
- espaços de trabalho;
- incorporação de produtos de outras ferramentas.

É o ponto de convergência dos resultados.

## 5.2 Banco de Fotos

- cadastro;
- importação;
- busca;
- qualificação;
- comparação facial assistida;
- validação humana;
- auditoria.

## 5.3 Laboratório de Evidências

Três instrumentos principais:

- Extrator de Texto;
- Extrator de Frames;
- Transcritor.

Original e derivados devem permanecer separados.

## 5.4 Pesquisa em Fontes Abertas

- consultas públicas;
- preservação de fonte/data/hora;
- coleta orientada;
- enriquecimento;
- integração via PÉGASO;
- correlação local.

## 5.5 Analisador Financeiro

- importação de dados;
- consolidação de transações;
- fluxos financeiros;
- totais;
- recorrências;
- vínculos;
- tipologias e anomalias para avaliação humana.

## 5.6 Diagrama Investigativo

- pessoas;
- organizações;
- telefones;
- veículos;
- endereços;
- eventos;
- relações;
- filtros;
- proveniência;
- exportação.

## 5.7 Assistente de Inteligência

- consulta em linguagem natural;
- busca;
- síntese;
- comparação;
- convergências/divergências;
- apoio à correlação;
- fontes explícitas.

## 5.8 Assistente de Relatórios

- seleção de informações;
- estruturação de peças;
- redação;
- padronização;
- referências;
- versões;
- exportação;
- aprovação humana.

## 5.9 Evolução condicionada

Análise Territorial somente entra quando houver:

- dados georreferenciados suficientes;
- caso de uso operacional real;
- qualidade de endereço/coordenadas;
- política de acesso;
- possibilidade de validação em operação.

---

# 6. Roadmap histórico ATHENA — AT-01 a AT-05

O roadmap inicial de 02/08/2026 organizou o produto assim:

| ID | Unidade | Objetivo original |
|---|---|---|
| AT-01 | Fundação do servidor | servidor, autenticação, interface base |
| AT-02 | Banco de Fotos | acervo + comparação assistida |
| AT-03 | Platea | conhecimento compartilhado / sincronização |
| AT-04 | Assistente IA | RAG + consulta em linguagem natural |
| AT-05 | Assistente de Relatório | rascunho assistido e aprovação |

Esse roadmap foi importante para iniciar o ATHENA, mas **não descreve sozinho o projeto atual**.

Desde então:

- a arquitetura do ecossistema foi revista;
- Platea deixou de ser conceito de produto obrigatório;
- o Workspace Investigativo tornou-se a unidade central de evolução;
- a construção de relatórios deixou de ser tratada apenas como geração linear de rascunho;
- o roadmap efetivo passou a ser detalhado pela AT-06.

Portanto, AT-01–AT-05 deve ser preservado como **roadmap fundacional/histórico**, não como única sequência normativa vigente.

---

# 7. Roadmap corrente — AT-06

## 7.1 AT-06A — Núcleo do Workspace

**Objetivo:** criar o ambiente operacional real do caso.

Escopo:

- Workspace ligado ao caso;
- contexto do caso;
- materiais;
- pessoas;
- blocos investigativos;
- associação rastreável de fontes;
- ATHENA contextual;
- reversibilidade básica;
- layout/panes;
- fundação para Pool/Bins.

**Estado macro:** fundação implementada e utilizada como base das revisões posteriores.

## 7.2 AT-06B — Intake e Pool do Caso

**Objetivo:** reduzir o esforço para colocar e organizar material dentro do caso.

Escopo previsto:

- upload/intake;
- preservação de original;
- hash;
- metadados;
- Pool;
- Bins;
- Smart Bins;
- seleção;
- Bandeja da Mesa;
- drag and drop;
- proveniência inicial;
- extração assistida;
- mapa factual.

### Implementações documentadas dentro da AT-06B

- B3 — Refino de UX Guiada;
- B4;
- B5;
- B5.1;
- B5.2;
- B6;
- B6.1 — Smart Bins e seleção por visão;
- B6.2 — seleção local + Bandeja da Mesa;
- B6.3 — Dos Fatos + Intake Global;
- B6.4 — Mesa Factual Compacta.

**Estado macro atualizado em 27/08/2026:** a fundação histórica da AT-06B permanece relevante, e a unidade curada `AT-06B-CURATED-01 — Intake Físico e Armazenamento Canônico` foi concluída e validada em runtime real. O backend de intake físico passa a ser considerado **congelado** até decisão arquitetural explícita. A apresentação visual do intake pode ser substituída pelo redesign do Workspace, desde que os contratos de domínio sejam preservados.

## 7.3 AT-06C — Organização Analítica

Escopo:

- fatos;
- declarações;
- inferências;
- hipóteses;
- pendências;
- vínculos;
- cronologia;
- validação;
- correlações;
- estados analíticos.

**Estado:** não iniciada como unidade completa. Existem primitivas já construídas no AT-06B, especialmente mapa factual, contexto e proveniência.

## 7.4 AT-06D — Compositor da Peça / Report Builder

Escopo:

- objeto Produto;
- seções;
- composição não linear;
- blocos;
- Viewer/Inspector;
- redação assistida contextual;
- revisão;
- rastreabilidade seção → bloco → fonte.

**Estado:** não concluída. Existem protótipos/preparação de narrativa, mas o compositor completo não deve ser considerado entregue.

## 7.5 AT-06E — Exportação

Escopo:

- DOCX;
- PDF;
- estilos;
- modelos;
- cabeçalho/rodapé;
- tabelas;
- imagens.

**Estado:** pendente.

## 7.6 AT-06F — Refinamentos

Escopo futuro:

- versionamento;
- comparação;
- aprovação;
- histórico;
- colaboração;
- templates institucionais;
- produtividade.

**Estado:** pendente.

---

# 8. Modelo operacional consolidado do Workspace

## 8.1 Caso

Identidade canônica da investigação.

## 8.2 Workspace

Ambiente operacional daquele caso.

Baseline atual:

```text
1 Caso → 1 Workspace
```

Sem bloquear multiplicidade futura.

## 8.3 Artefato

Material original ou derivado incorporado ao caso.

## 8.4 Pool

Acervo navegável de elementos.

## 8.5 Bin

Visão/classificação operacional do Pool.

## 8.6 Smart Bin

Visão calculada por contexto, proveniência ou regra.

## 8.7 Seleção local

Seleção temporária dentro da visão atual.

## 8.8 Bandeja da Mesa

Conjunto acumulado de fontes selecionadas de várias Bins para utilização em um tópico.

## 8.9 Bloco Investigativo

Unidade de informação/argumentação rastreável.

Não é sinônimo de parágrafo.

Um bloco pode originar:

- parágrafo;
- quadro;
- tabela;
- cronologia;
- seção;
- capítulo.

## 8.10 Tópico de Trabalho

Objeto operacional dentro da composição do relatório/análise.

## 8.11 Mesa

Área principal de construção e validação do raciocínio.

## 8.12 Inspector / Viewer

Mostra o produto resultante, e não a mecânica interna de extração.

## 8.13 ATHENA contextual

Deve compreender:

- caso ativo;
- seleção;
- tópico;
- bloco;
- artefato;
- fontes;
- contexto recente.

---

# 9. Semântica epistemológica

O sistema deve distinguir:

### FATO
Elemento sustentado por fonte/registro.

### DECLARAÇÃO
Informação atribuída a pessoa ou fonte.

### EVIDÊNCIA
Artefato/registro utilizado para sustentar análise.

### ANOTAÇÃO
Manifestação humana ou texto assistido.

### INFERÊNCIA
Conclusão derivada dos elementos disponíveis.

### HIPÓTESE
Possibilidade ainda insuficientemente demonstrada.

### PENDÊNCIA
Questão que requer verificação.

A classificação deve existir no modelo sem transformar a interface em formulário burocrático.

---

# 10. SPEC de Workflow de Relatórios de Análise de Dispositivos — 24/08/2026

Essa SPEC introduz uma decisão importante e deve orientar o próximo ciclo funcional.

## 10.1 Premissa

> **Analisar primeiro, relatar depois.**

O usuário normalmente já examinou previamente o aparelho/material antes de escrever o relatório.

O Workspace não deve obrigá-lo a “refazer a investigação” para conseguir relatar.

## 10.2 Papel do sistema

O usuário deve pensar em:

- fato;
- evidência;
- relevância;
- interpretação;
- conclusão limitada.

O sistema deve cuidar de:

- estrutura;
- organização;
- preenchimento;
- formatação;
- assistência de redação;
- referências;
- consistência.

## 10.3 Tela em branco como exceção

Se documentos/metadados permitirem, o capítulo deve começar com esqueleto parcial ou preenchido.

## 10.4 Capítulos guiados, não engessados

A interface deve orientar, mas o analista deve poder:

- aceitar;
- editar;
- excluir;
- reordenar;
- fazer manualmente;
- pedir assistência;
- acompanhar como o resultado foi construído.

## 10.5 Fluxo vertical

A prioridade não deve ser implementar todos os capítulos simultaneamente.

Primeiro validar:

> **um fluxo vertical completo, compreensível e útil para um caso real.**

## 10.6 Questões ainda abertas dessa SPEC

Antes de implementação ampla ainda precisam de desenho específico:

1. ficha de qualificação;
2. card/bloco de objeto de análise;
3. núcleo visual de conversação;
4. importação em lote de prints;
5. extração de dados de telas de ferramentas externas;
6. vínculo entre consideração e evidências;
7. estados original / IA / validado;
8. entrada por voz;
9. política de transcrição derivada;
10. citação interna de prints;
11. sugestão automática de evidências;
12. revisão final contra afirmações não ancoradas.

---

# 11. Decisões de UX vigentes

## 11.1 Progressão orientada, não wizard rígido

A interface deve deixar claro:

- onde estou;
- o que estou fazendo;
- o que já foi concluído;
- qual é a próxima ação.

Mas etapas já alcançadas devem poder ser revisitadas.

## 11.2 Feedback perceptível

Toda ação precisa dar resposta visível.

Exemplos:

- material adicionado;
- item salvo;
- estado alterado;
- tópico avançado;
- fonte vinculada;
- processamento iniciado;
- processamento concluído;
- erro ocorrido.

Uma ação sem percepção de resultado é tratada como problema de UX, mesmo que tecnicamente tenha funcionado.

## 11.3 Sistema faz sozinho, junto ou sob comando

Automação deve possuir gradação.

O usuário pode:

- aceitar um resultado pronto;
- acompanhar etapas;
- intervir;
- editar;
- substituir;
- executar manualmente.

## 11.4 Layout profissional

A referência conceitual é um editor não linear profissional:

- Pool/acervo;
- área de composição;
- Viewer/Inspector;
- panes redimensionáveis;
- foco no objeto atual.

Não copiar literalmente softwares existentes.

---

# 12. Baseline técnica conhecida

Último checkpoint documental explicitamente validado antes dos relatos mais recentes de regressão:

```text
Branch: feat/at-06a-workspace-core
Commit: d3e9715
Mensagem: feat(AT-06): checkpoint workspace UX-02 stabilized
Alembic: 0013_at06b63_facts_topic_composition
Working tree no checkpoint: limpo
```

No STAB-01 foram validados:

- foco/edição;
- persistência;
- retorno entre estágios;
- Contexto → Narrativa → F5 → Contexto com conteúdo preservado;
- Contexto → Mapa factual → Contexto.

Isso é a **última baseline boa comprovada pela documentação disponível**.

O HEAD atual posterior a novas alterações deve ser confirmado no repositório antes de qualquer correção.

---

# 13. Riscos técnicos atuais

## 13.1 Acoplamento da superfície do Workspace

O Workspace acumulou múltiplas rodadas de:

- estrutura;
- estados;
- navegação;
- persistência;
- eventos;
- seleção;
- panes;
- UX.

O padrão recente de regressões indica risco elevado de acoplamento entre controladores de interface.

Isso deve ser comprovado por auditoria antes de qualquer refatoração.

## 13.2 Regressão silenciosa

Mudanças de UX não podem quebrar:

- foco;
- persistência;
- seleção;
- navegação;
- proveniência;
- salvamento;
- DnD.

Cada contrato já validado precisa de smoke/regression test.

## 13.3 Divergência entre UX e produto

A interface já chegou a estados em que:

- o mecanismo existe;
- a intenção é boa;
- mas o usuário não sente controle nem clareza.

Esse é um risco de produto, não apenas de CSS.

## 13.4 Crescimento prematuro

AT-06C/D/E não devem avançar enquanto a base AT-06A/B estiver instável.

---

# 14. Decisões estruturais ainda pendentes

Fora da AT-06 imediata, permanecem decisões estratégicas:

- identidade definitiva da plataforma principal do ecossistema;
- destino/posição final do nome ATHENA;
- papel definitivo de ANDRÔMEDA;
- posição final do NEXUS;
- detalhamento interno do PÉGASO;
- política formal de classificação de dados;
- cofre de segredos;
- retenção e proteção de auditoria;
- estratégia de migração do Intel Desk/Dash;
- modelo de implantação institucional;
- critérios formais de paridade/descontinuação do legado;
- SPECs próprias das demais ferramentas da ADR-002.

Essas pendências não bloqueiam a estabilização do Workspace.

---

# 15. Próximo roadmap de execução recomendado

A prioridade continua não sendo acumular novas features. Após a conclusão da `AT-06B-CURATED-01`, o foco passa a ser **fechar documentação, preservar contratos e alinhar o redesign antes da próxima expansão funcional**.

## Unidade 0 — FECHAMENTO-AT06B-CURATED-01

**Estado em 27/08/2026:** concluída tecnicamente; fechamento documental em execução.

Resultado consolidado:

- intake físico real validado;
- storage governado validado;
- SHA-256 e deduplicação validados;
- original recuperável após restart;
- banco real migrado para `0009_at06b_curated_intake_storage`;
- ponte de compatibilidade legada validada;
- smokes AT-06B verdes;
- branch `feat/at06b-curated-01-intake-storage` publicada;
- HEAD remoto de fechamento técnico: `b7e294a`.

Próximo gate:

```text
atualização documental
→ commit documental
→ PR
→ merge
```

## Unidade 1 — REVIEW-DESIGN-WORKSPACE-01

Antes de implementar o redesign produzido no laboratório de UX/UI, revisar a proposta contra os contratos já congelados.

A revisão deve classificar cada mudança como:

- somente apresentação;
- composição/layout;
- microinteração;
- fluxo operacional;
- alteração de contrato;
- nova funcionalidade.

Regra:

> Design pode substituir a forma. Não pode redefinir silenciosamente storage, intake, proveniência, auditoria, identidade do material ou propriedade pelo Caso.

Saída esperada:

- aprovação;
- aprovação com correções;
- ou retorno ao Design Lab.

## Unidade 2 — ELEIÇÃO DA PRÓXIMA SPEC

Após aprovação do redesign, escolher explicitamente a próxima unidade. A escolha **não é automática**.

Candidatas atuais:

### Opção A — AT-06B-CURATED-02 — Intake Visual / Pool mínimo

Adequada se a prioridade for consolidar a experiência de entrada e organização visual de materiais sem expandir o backend já validado.

### Opção B — VERTICAL-SLICE-REPORT-01

Adequada se a prioridade for provar ponta a ponta um fluxo real:

```text
material
→ extração
→ fato/proveniência
→ intervenção humana
→ bloco/seção
→ narrativa
→ preview
```

## Unidade 3 — Próxima implementação aprovada

Somente depois das unidades anteriores.

Não iniciar AT-06C/D/E por inércia de roadmap enquanto o redesign e o próximo slice não estiverem explicitamente aprovados.

---

# 16. Critério macro de sucesso do AT-06

A AT-06 será considerada materialmente bem-sucedida quando um policial conseguir:

1. criar/abrir um caso;
2. inserir documentos, prints, imagens, evidências e notas;
3. organizar material;
4. validar fatos e contexto;
5. conversar com ATHENA sobre o caso;
6. construir seções a partir de elementos rastreáveis;
7. ajustar redação e ordem;
8. entender de onde cada afirmação saiu;
9. exportar um DOCX coerente;
10. fazer tudo isso sem reconstruir manualmente o conteúdo.

---

# 17. Critérios de não sucesso

Não considerar o produto maduro se:

- a interface exigir conhecimento da arquitetura interna;
- cliques não produzirem feedback;
- o usuário não souber o que aconteceu;
- voltar de etapa quebrar estado;
- persistência não for confiável;
- IA produzir texto não ancorado;
- automação esconder fontes;
- o usuário ficar preso a um fluxo rígido;
- a construção do relatório exigir mais trabalho que o processo manual;
- recursos sejam adicionados apenas porque são tecnicamente interessantes.

---

# 18. Regra de continuidade

A partir do fechamento técnico de 27/08/2026:

> **O backend de intake físico da AT-06B-CURATED-01 é baseline congelada. Mudanças de apresentação são livres dentro do Design System; mudanças de contrato exigem nova SPEC/ADR.**

Toda próxima unidade deve terminar com:

- testes;
- resultado observável;
- decisão;
- atualização de status;
- handoff;
- sincronização documental;
- orientação explícita sobre qual documento novo substitui ou não uma fonte anterior.

Documentos atualizados devem declarar no cabeçalho uma destas relações:

```text
SUBSTITUI / SUPERSEDE
ou
COMPLEMENTA / NÃO SUBSTITUI
```

Isso passa a ser requisito de higiene documental do projeto.

---

# 19. Fontes consolidadas utilizadas

Documentos centrais:

- ADR-001 — Arquitetura Soberana e Híbrida da Plataforma Operacional — 19/08/2026;
- ADR-002 — Organização Funcional em Ferramentas Investigativas — 19/08/2026;
- ADR-003 — Modos de Execução SAFE / AGENT — 20/08/2026;
- ROADMAP CIRCE Athena — AT-01 a AT-05 — 02/08/2026;
- AT-06 — Decisões Consolidadas de Produto — 21/08/2026;
- SPEC AT-06 — Workspace Investigativo & Construtor de Peças;
- mini-SPECs AT-06B3 a B6.4;
- STATUS Canônico AT-06 — 23/08/2026;
- HANDOVER AT-06 / STAB-01 — 23/08/2026;
- SPEC Workflow Investigativo para Relatórios de Análise de Dispositivos — 24/08/2026;
- CIRCE — Metodologia Spec-Driven v1.0 — 25/08/2026;
- decisões e validações posteriores do Design Lab de UX/UI.

---

# 20. Síntese executiva

O CIRCE-ATHENA continua definido como um Workspace Investigativo que transforma material, evidência, contexto e raciocínio em produto policial rastreável.

Em 27/08/2026 ocorreu uma mudança importante de estado: a unidade `AT-06B-CURATED-01 — Intake Físico e Armazenamento Canônico` deixou de ser proposta e passou a **baseline implementada e validada**.

O sistema já demonstrou, em runtime real:

```text
Caso
→ incorporar material físico
→ preservar original
→ registrar hash/metadados
→ bloquear duplicidade no mesmo Caso
→ recuperar Original
→ reiniciar aplicação
→ recuperar novamente
```

O banco real foi migrado de uma linhagem legada para `0009_at06b_curated_intake_storage` sem fabricar metadados físicos para documentos antigos. A compatibilidade foi validada também sobre cópia do backup legado.

O problema atual, portanto, mudou. Não é mais “como guardar um arquivo corretamente”. Esse contrato está congelado.

A prioridade passa a ser:

1. encerrar documentalmente a unidade;
2. revisar a proposta de redesign do Workspace contra os contratos congelados;
3. escolher explicitamente a próxima SPEC;
4. provar o próximo slice sem reabrir decisões já validadas.

### Snapshot técnico de 27/08/2026

```text
REPO: C:\Projetos\CIRCE_ATHENA
REMOTE: https://github.com/Prjkt-CIRCE/CIRCE-ATHENA.git
BRANCH: feat/at06b-curated-01-intake-storage
HEAD: b7e294a2e73aa2c0fa94cd2498f9a40197362b3
LOCAL == ORIGIN: sim, validado
WORKING TREE: limpa no checkpoint
ALEMBIC: 0009_at06b_curated_intake_storage (head)
PYTHON BASELINE VALIDADA: 3.11.9 em .venv local
```

Últimos checkpoints relevantes:

```text
b7e294a  fix(dev): restore audited localhost auth bypass
2f5c1e2  fix(runtime): lazy-load optional facial recognition stack
35ad3fb  test(AT-06B): decouple workspace smoke from visual wording
c366db8  fix(AT-06B): bridge legacy Alembic lineage for curated intake
4b7e644  feat(AT-06B): integrate case document intake into workspace
dc48a88  feat(AT-06B): expose governed document intake and retrieval
```

### Pendência técnica deliberadamente aberta

InsightFace/ONNX/CUDA ainda não foi validado end-to-end. O commit de runtime garante apenas que a indisponibilidade desse subsistema opcional não impeça o ATHENA de iniciar.

### Próxima decisão de produto

A próxima implementação será escolhida somente após revisão do redesign do Workspace. As candidatas mais prováveis permanecem `AT-06B-CURATED-02 — Intake Visual / Pool mínimo` e `VERTICAL-SLICE-REPORT-01`.

A direção segue sendo:

> **estabilizar, provar, congelar; depois expandir.**
