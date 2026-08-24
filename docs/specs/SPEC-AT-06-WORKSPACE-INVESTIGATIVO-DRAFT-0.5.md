# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.5
**Data:** 2026-08-22
**Status:** Baseline funcional para AT-06B3
**Produto:** CIRCE-ATHENA
**Escopo:** Pool indexado + Recortes Investigativos + Achados validados + composição futura de peças
**Relacionadas:** ADR-001, ADR-002, ADR-003; AT-06 — Decisões Consolidadas de Produto — 2026-08-21

## 1. Visão revisada

O Workspace Investigativo é o ambiente operacional do caso.

A experiência deixa de ser centrada em formulários e em “criar blocos” e passa a ser centrada no ciclo real de análise:

`Pool → Indexação/Extração → Elementos → Recorte → Resumo → Achado → Seção → Produto`

O policial não deve preencher o relatório como tarefa principal. Ele alimenta o caso, seleciona material relevante, registra sua percepção e valida interpretações. A plataforma reduz o trabalho mecânico de extração, organização, busca, formatação e projeção documental.

## 2. Evidência empírica da revisão

A revisão foi orientada pela engenharia reversa de um relatório técnico real de análise de aparelho celular de média complexidade, com 93 páginas.

O documento evidencia um padrão recorrente de trabalho:

1. metadados institucionais e referências do procedimento;
2. contextualização dos fatos;
3. identificação dos objetos analisados e cadeia de custódia;
4. qualificação de envolvidos;
5. análise temática de imagens, conversas e outros conteúdos;
6. seleção de trechos relevantes;
7. sínteses intermediárias por sequência/interlocutores;
8. reorganização cronológica ou temática dos achados;
9. considerações finais e conclusão;
10. extensa carga mecânica de inserção de imagens, transcrições, fichas, legendas e paginação.

A SPEC passa a tratar esse fluxo como referência concreta de produto para análise de dispositivo móvel, sem assumir que um único relatório representa toda a produção policial.

## 3. Princípio central

> **O policial alimenta e interpreta o caso; Athena e a plataforma estruturam, relacionam e projetam esse trabalho em produtos rastreáveis.**

A plataforma pode:

- extrair;
- indexar;
- pesquisar;
- organizar;
- sugerir;
- sintetizar;
- redigir;
- diagramar;
- montar projeções documentais;
- apontar lacunas e conflitos.

A plataforma não pode:

- transformar interpretação em fato sem validação humana;
- inventar conteúdo ausente;
- ocultar divergência entre fontes;
- perder proveniência;
- substituir decisão investigativa;
- atribuir ao policial conclusão que ele não validou.

## 4. Modelo operacional revisado

### 4.1 Caso

Identidade da investigação.

O número institucional de relatório/produto pode permanecer pendente no início. O sistema utiliza identidade técnica própria e recebe o número oficial quando disponível.

### 4.2 Workspace

Ambiente operacional do Caso.

Na fase atual:

`1 Caso → 1 Workspace`

### 4.3 Pool do Caso

Repositório lógico de tudo que ingressa ou é produzido no caso.

Exemplos:

- ordem de serviço;
- boletins de ocorrência;
- laudos;
- decisões/medidas judiciais;
- fichas de qualificação;
- documentos;
- imagens;
- áudios;
- extrações forenses;
- pessoas;
- vínculos;
- locais;
- anotações;
- recortes;
- achados.

O Pool não é apenas uma lista de arquivos. Cada artefato deverá evoluir para:

`Original preservado → extração/metadados → indexação → entidades/campos candidatos → elementos citáveis`

### 4.4 Elemento

Unidade pesquisável e selecionável no Workspace.

Pode representar:

- pessoa;
- documento;
- mensagem;
- áudio;
- imagem;
- arquivo;
- local;
- coordenada;
- ocorrência;
- objeto;
- vínculo;
- anotação;
- outro registro estruturado.

### 4.5 Recorte Investigativo

Conjunto contextual de elementos selecionados pelo policial para analisar uma sequência, relação, evento ou ponto relevante.

Exemplo:

`10 mensagens + 2 áudios + 1 imagem → Recorte “Planejamento do roubo”`

O Recorte preserva:

- fontes selecionadas;
- snapshots mínimos;
- nota literal do analista;
- proposta estruturada da Athena;
- lacunas/limites detectados;
- estado de validação.

### 4.6 Resumo

Descrição condensada do que ocorre no Recorte.

Resumo não é automaticamente conclusão.

Deve privilegiar conteúdo diretamente registrado e separar o que é descrição daquilo que é interpretação.

### 4.7 Achado Investigativo

Objeto validado pelo policial que representa significado investigativo reutilizável.

Tipos iniciais:

- fato;
- declaração;
- anotação;
- inferência;
- hipótese;
- pendência.

Um Achado deve responder:

- o que foi identificado;
- quais fontes sustentam;
- qual é a descrição objetiva;
- qual é a interpretação, se houver;
- qual é o estatuto epistemológico;
- quem validou;
- onde é utilizado.

### 4.8 Bloco Investigativo

Permanece como infraestrutura técnica da AT-06A e possível unidade agregadora futura.

A UX não deve obrigar o policial a pensar em “blocos” para realizar tarefas comuns. O paradigma visível passa a ser:

`Fonte → Recorte → Achado → Produto`

### 4.9 Produto e Seção

Produto é a peça documental final ou intermediária.

`Produto → Seções → Achados/Recortes/Elementos utilizados`

O Produto é projeção do trabalho investigativo, não sua fonte de verdade.

## 5. Voice Note contextual

Voice Note é ferramenta de captura do raciocínio investigativo no momento em que ele ocorre, não mero ditado de relatório.

Fluxo normativo:

`Áudio original → transcrição literal → estrutura proposta → validação humana → Recorte/Achado/Anotação`

A fala do policial deve permanecer preservada como entrada humana.

Athena pode:

- reorganizar;
- limpar redundância oral;
- separar descrição e interpretação;
- sugerir resumo;
- sugerir classificação epistemológica;
- apontar lacunas.

Athena não pode transformar silenciosamente a fala em fato.

### 5.1 AT-06B1

O primeiro incremento valida a arquitetura usando **texto digitado como substituto da futura transcrição de voz**.

O áudio real entra depois sem alterar o modelo conceitual.

## 6. Indexação e busca

A indexação é pilar do Workspace.

### 6.1 Busca exata

Deve localizar, quando os dados existirem:

- nomes;
- telefones;
- CPF/RG;
- IMEI;
- placas;
- datas;
- valores;
- expressões literais;
- números de BO, IP, processo, laudo ou lacre.

### 6.2 Busca semântica

Deve permitir consultas como:

- “conversas sobre venda da arma”;
- “onde falam de carro ou moto próximos ao planejamento”;
- “menções à presença policial”;
- “trechos relacionados à entrega do objeto”.

### 6.3 Filtros

Previstos:

- pessoa/interlocutor;
- aplicativo;
- dispositivo;
- período;
- tipo de conteúdo;
- status de análise;
- recorte;
- achado;
- uso no produto.

## 7. Extração multimodal

Princípio:

> **Use a representação original estruturada quando ela existir; use OCR quando não houver camada textual confiável.**

Pipeline previsto:

- texto estruturado → parser direto;
- PDF textual → extração textual;
- PDF/imagem escaneada → OCR;
- imagem → OCR/metadados/descrição assistida quando aplicável;
- áudio → transcrição;
- vídeo → áudio, frames e metadados conforme ferramenta específica.

Todo derivado deve manter referência ao original.

## 8. Três níveis de automação

### 8.1 Determinística

Pode ocorrer automaticamente quando configurada:

- data;
- cabeçalho institucional;
- rodapé;
- paginação;
- estilos;
- numeração;
- fichas e tabelas a partir de dados estruturados;
- posicionamento e dimensionamento padronizado de mídia.

### 8.2 Extração assistida

Athena pode propor dados com origem explícita:

- nomes;
- BO/IP/processo;
- medida cautelar;
- lacres;
- IMEI;
- telefones;
- datas;
- locais;
- pessoas;
- objetos.

Conflitos entre fontes devem ser exibidos, não resolvidos silenciosamente.

### 8.3 Análise

Sempre sob controle humano:

- relevância;
- significado de jargão;
- vínculo;
- inferência;
- hipótese;
- conclusão;
- atribuição de autoria/participação.

## 9. Esqueleto inicial — Relatório de análise de dispositivo móvel

O primeiro template de domínio deverá distinguir seções estruturais, condicionais e livres.

### 9.1 Estruturais

- identificação institucional;
- metadados do produto;
- contextualização/fatos;
- objetos de análise;
- origem/autorização/cadeia de custódia quando aplicável;
- considerações/conclusão.

### 9.2 Condicionais

- qualificação de envolvidos;
- imagens;
- conversações;
- áudios;
- chamadas;
- contatos;
- arquivos;
- geolocalização;
- ocorrências relacionadas;
- cronologia;
- diagramas/tabelas/mapas.

### 9.3 Livres

Seções criadas pelo policial de acordo com a necessidade investigativa.

## 10. Workspace revisado

Três zonas principais:

1. **Pool** — acervo, busca, filtros e seleção;
2. **Mesa de Análise / Produto** — Recortes, Achados e composição;
3. **Inspector / Athena** — objeto em foco, contexto, assistência e proveniência.

O painel central deve evoluir entre dois modos:

- **Analisar** — produzir Recortes/Achados;
- **Compor** — organizar Achados/elementos em Seções do Produto.

## 11. AT-06B1 — Núcleo de Análise Investigativa

### 11.1 Objetivo

Provar uma fatia vertical completa:

`seleção no Pool → nota do analista → estruturação Athena → revisão → validação → Achado persistente`

### 11.2 Inclui

- modelo persistente de Recorte;
- fontes many-to-many por referência/snapshot;
- nota literal do analista;
- proposta de resumo e interpretação pela Athena local;
- classificação epistemológica sugerida;
- lacunas/limites da proposta;
- revisão editável;
- validação explícita humana;
- Achado persistente;
- descarte lógico de Recorte em rascunho;
- auditoria;
- Mesa de Análise na interface;
- preservação do protótipo de Blocos como infraestrutura técnica.

### 11.3 Não inclui ainda

- captura real de microfone;
- transcrição automática;
- OCR operacional completo;
- importador Cellebrite;
- indexação semântica de massa;
- Smart Bins;
- compositor de relatório;
- DOCX/PDF;
- fichas Vinculum automáticas;
- mapas/diagramas automáticos.

### 11.4 Critérios de aceite

AT-06B1 é considerada funcional quando:

1. o policial seleciona uma ou mais fontes do Pool;
2. registra uma nota de análise;
3. Athena retorna proposta separando resumo objetivo e interpretação;
4. a proposta permanece explicitamente não validada;
5. o policial pode editar os campos;
6. o policial escolhe/classifica o estatuto epistemológico;
7. somente ação explícita cria o Achado validado;
8. o Achado preserva vínculo com o Recorte e suas fontes;
9. o Recorte pode ser descartado sem alterar fontes originais;
10. todas as persistências relevantes são auditáveis.

## 12. Diretriz de produto

> **Indexar tudo. Permitir selecionar qualquer conjunto relevante. Capturar o raciocínio humano no contexto. Transformar esse raciocínio em estrutura reutilizável e rastreável.**

Essa diretriz passa a orientar os próximos incrementos da AT-06.


## 13. AT-06B3 — UX guiada sem rigidez

O teste operacional do AT-06B2 estabeleceu que funcionalidade disponível não equivale a funcionalidade descobrível. O Workspace deve orientar sem obrigar o usuário a conhecer a arquitetura interna.

### 13.1 Perguntas permanentes da interface

A experiência deve responder continuamente:

1. em qual caso estou;
2. o que estou fazendo agora;
3. qual é a próxima ação útil.

### 13.2 Tópico como contexto operacional visível

O Tópico ativo deve aparecer no cabeçalho e na Mesa. A Mesa deve apresentar orientação contextual baseada em seu ciclo de vida.

### 13.3 Pool contextual

A seleção desktop permanece, mas a ação principal deve indicar o destino da seleção e somente habilitar o envio quando o Tópico estiver em elaboração ou revisão.

### 13.4 Panes

Controles de destacar/recolher devem ser legíveis, não se sobrepor em estado colapsado e preservar a possibilidade de destacamento multijanela.

### 13.5 Acabamento visual

Scrollbars e elementos nativos visíveis devem ser harmonizados com o tema escuro para evitar quebra de identidade visual.

---

**Atualização 2026-08-22 — Draft 0.5:** incorporado AT-06B3 com condução contextual, indicador “AGORA”, próxima ação por Tópico, Pool orientado ao destino, correção de panes colapsados e scrollbars escuras.
