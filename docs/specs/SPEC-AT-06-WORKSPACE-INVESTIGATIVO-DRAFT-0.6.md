# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.6  
**Data:** 2026-08-22  
**Status:** Baseline funcional para AT-06B4  
**Produto:** CIRCE-ATHENA  
**Escopo:** Pool Investigativo orientado por Bins/Smart Bins + Tópicos de Trabalho + Recortes/Achados + composição futura de peças

## 1. Visão

O Workspace Investigativo deve conduzir o policial pela atividade que ele está executando, sem exigir domínio interno da arquitetura da plataforma.

O fluxo de produto consolidado é:

`Caso → Pool → Tópico de Trabalho → seleção/recorte → nota do analista → Athena → Achado validado → Seção → Produto`

A pergunta permanente da Mesa é:

> **O que estou fazendo agora?**

O Tópico de Trabalho responde a essa pergunta e condiciona a forma como Athena e o Pool apresentam o material do caso.

## 2. Pool Investigativo

O Pool é o acervo operacional do caso. Não deve ser apresentado como formulário ou checklist.

A experiência principal deve ser semelhante a um explorador/media pool profissional:

- Bins para organização humana;
- Smart Bins para visões dinâmicas;
- busca global;
- seleção por clique;
- Ctrl/Cmd + clique para seleção múltipla;
- Shift + clique para intervalo;
- Ctrl/Cmd + A dentro da visão atual;
- drag and drop da seleção para a Mesa;
- preview rápido do elemento;
- preservação do original e da proveniência.

### 2.1 Bins

Bin é uma visão de organização humana.

Na AT-06B4, as Bins iniciais refletem as classes de material já disponíveis:

- Pessoas;
- Documentos;
- Vínculos;
- Anotações.

A evolução prevista inclui Bins como:

- Ordem de Serviço;
- Laudos e extrações;
- Conversações;
- Imagens;
- Áudios;
- Vídeos;
- Locais;
- Ocorrências;
- Achados;
- outras classes surgidas da ingestão/indexação.

Uma Bin não altera o conteúdo original.

### 2.2 Smart Bins

Smart Bin é uma visão calculada dinamicamente por regra.

Princípio:

> **A mesma fonte pode aparecer em várias Smart Bins sem ser duplicada ou movida.**

Tipos previstos:

1. **Determinísticas** — baseadas em metadados e regras objetivas.
2. **Sistêmicas** — fornecidas pelo ATHENA para estados do fluxo.
3. **Semânticas** — baseadas em busca vetorial/IA, somente após a infraestrutura de indexação.
4. **Context Bin** — Smart Bin dinâmica determinada pelo Tópico de Trabalho ativo.

### 2.3 Smart Bins da AT-06B4

A primeira vertical implementa:

- **Relevante ao tópico** — Context Bin que muda conforme o Tópico de Trabalho;
- **Seleção atual** — elementos selecionados no fluxo corrente;
- **Notas assistidas** — anotações originadas do fluxo da Athena.

A lógica inicial de relevância do Context Bin é determinística e conservadora. Ela não deve ser apresentada como conclusão semântica.

Exemplos:

- Cabeçalho → documentos e anotações;
- Dos Fatos / Introdução → documentos, vínculos e anotações;
- Objetos de análise → documentos;
- Qualificação → pessoas e documentos;
- Análise de imagens → documentos;
- Conversações → documentos e anotações;
- Considerações / Conclusão → visão ampla do material disponível.

Essa regra será substituída ou enriquecida pela indexação real quando OCR, parsers e embeddings estiverem disponíveis.

## 3. Navegação do Pool

O Pool possui dois níveis visuais.

### 3.1 Home

Exibe:

- Bins;
- Smart Bins;
- busca global.

O usuário escolhe uma visão sem precisar percorrer uma lista única extensa.

### 3.2 Conteúdo da visão

Ao abrir uma Bin ou Smart Bin:

- aparece a lista filtrada de elementos;
- o usuário pode selecionar por comportamento desktop;
- o preview mostra metadados e descrição já disponíveis;
- o material selecionado pode ser enviado/arrastado para o Tópico ativo.

O preview real de PDF, imagem, áudio, vídeo e conteúdo OCR depende da futura ingestão de artefatos. AT-06B4 entrega a superfície e o contrato visual, sem simular conteúdo inexistente.

## 4. Busca

A busca do Pool é global.

Na AT-06B4 ela opera sobre os textos/metadados já disponíveis na aplicação.

A evolução seguirá:

`busca textual → OCR/parsers → índice estruturado → busca híbrida exata + semântica`

Não deve existir “Smart Bin semântica” fictícia antes dessa infraestrutura.

## 5. Tópico de Trabalho e Pool

O Tópico ativo influencia o Pool, mas nunca esconde o restante do acervo.

Exemplo:

`Tópico: Objetos de análise`

O Context Bin deve favorecer fontes compatíveis com:

- laudos;
- documentos técnicos;
- informações de aparelho;
- IMEI/SIM/lacre/medida cautelar quando esses metadados estiverem indexados.

O usuário continua podendo abrir qualquer Bin manualmente.

## 6. Seleção e proveniência

Seleção no Pool é temporária.

Recorte é persistente.

Achado é conhecimento validado.

Nenhuma operação de seleção, Smart Bin ou drag and drop pode:

- duplicar a evidência original;
- alterar silenciosamente o artefato;
- apagar proveniência;
- transformar uma inferência em fato.

## 7. Preview e Inspector

O preview do Pool serve para reconhecimento rápido do material.

O Inspector/Athena serve para:

- orientar o Tópico ativo;
- inspecionar Recortes/Achados;
- revisar material;
- exibir o preview do Tópico quando concluído;
- receber comandos contextuais.

O preview de um Tópico concluído no Inspector permanece requisito do roadmap imediato.

## 8. Composer

O composer da Athena deve permanecer compacto.

Em painel destacado/tela cheia:

- largura máxima de leitura;
- altura inicial curta;
- crescimento limitado;
- scroll interno quando necessário.

Ele não deve ocupar espaço vertical simplesmente porque há área disponível.

## 9. Fora do escopo da AT-06B4

Não entram neste incremento:

- OCR;
- embeddings;
- busca semântica real;
- importador Cellebrite;
- preview binário real de PDF/imagem/áudio;
- editor persistente de regras de Smart Bin personalizadas;
- criação manual/persistente de novas Bins;
- presets institucionais de cabeçalho;
- sidebar colapsável;
- Voice Note real.

Esses itens permanecem previstos, mas não serão simulados.

## 10. Critérios de aceite AT-06B4

A vertical é aceita quando:

1. o Pool deixa de apresentar todos os itens como lista inicial;
2. Bins aparecem como objetos de navegação;
3. Smart Bins aparecem separadas e explicadas como visões;
4. `Relevante ao tópico` muda conforme o tópico ativo;
5. busca global abre uma visão de resultados;
6. clique/Ctrl/Shift/Ctrl+A funcionam na visão atual;
7. drag and drop continua funcional;
8. preview de metadados responde a hover/foco;
9. seleção não duplica material;
10. composer destacado permanece compacto;
11. AT-06B1/B2 continuam passando no smoke;
12. Alembic permanece em `0009_at06b2_work_topics`.
