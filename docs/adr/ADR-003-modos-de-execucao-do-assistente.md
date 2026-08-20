# ADR-003 — Modos de Execução do Assistente: Safe Mode e Agent Mode

- **Status:** Aceita
- **Data:** 2026-08-20
- **Decisores:** Equipe do projeto
- **Escopo:** Assistente de Inteligência / autonomia operacional / interação humano-IA
- **Categoria:** Produto / Segurança / Experiência Operacional
- **Relacionadas:** ADR-001 — Arquitetura Soberana e Híbrida; ADR-002 — Organização Funcional em Ferramentas Investigativas

## 1. Contexto

O Assistente de Inteligência deve operar em ambiente policial, no qual segurança, rastreabilidade e controle humano são requisitos fundamentais. Ao mesmo tempo, o uso operacional é sensível a tempo: excesso de confirmações, diálogos intermediários e comandos rígidos pode aumentar a fricção, reduzir a adoção e fazer o analista perder oportunidades.

A plataforma também adota como princípio que o sistema deve apoiar a decisão do usuário autorizado, e não substituir sua autonomia operacional.

Uma única política de confirmação não atende adequadamente a todos os operadores e contextos. Alguns usuários preferirão proteção proporcional ao risco; outros, devidamente autorizados, poderão optar por maior autonomia de execução.

## 2. Decisão

O Assistente de Inteligência oferecerá dois modos de execução selecionáveis pelo operador:

### 2.1 Safe Mode

Modo padrão.

Ações serão tratadas de forma proporcional ao risco:

- leitura, consulta e análise: livres dentro das permissões do operador;
- ações de baixo risco e claramente solicitadas: execução direta;
- ações reversíveis de risco intermediário: execução direta quando houver mecanismo adequado de rastreabilidade/reversão;
- ações de alto risco, destrutivas, irreversíveis ou com exposição relevante: confirmação contextual antes da execução;
- pedidos ambíguos: esclarecimento mínimo necessário.

### 2.2 Agent Mode

Modo de autonomia máxima de execução.

Quando o operador solicita uma ação suportada, a solicitação constitui autorização operacional suficiente para executar as etapas necessárias sem confirmações intermediárias.

Agent Mode:

- não concede novas permissões;
- não contorna controles de acesso;
- não habilita ações tecnicamente não suportadas;
- não elimina auditoria;
- não autoriza iniciativa autônoma sem objetivo ou solicitação do usuário;
- não contorna políticas de comunicação externa definidas pela ADR-001.

## 3. Separação entre permissão e modo de execução

A arquitetura adotará a seguinte distinção:

> **Permissão determina o que o operador pode fazer.**
>
> **Modo de execução determina quanto o Assistente pode executar sem interromper o operador.**

A troca para Agent Mode não eleva privilégios.

## 4. Auditoria

Ambos os modos são auditáveis.

Deverão ser registrados, quando aplicável:

- operador;
- modo de execução vigente;
- ação executada;
- entidade/caso afetado;
- horário;
- resultado;
- confirmação contextual quando exigida pelo Safe Mode;
- mudança de modo de execução.

O conteúdo sensível não deverá ser duplicado desnecessariamente nos logs.

## 5. Persistência

A preferência será armazenada por operador.

- padrão para operador sem preferência registrada: `safe`;
- valores válidos: `safe`, `agent`;
- a preferência independe do modelo de IA utilizado;
- a preferência poderá ser alterada na interface do Assistente.

## 6. Classificação de risco

A política de risco será centralizada e extensível.

Categorias iniciais:

- `low`
- `medium`
- `high`
- `critical`

A classificação pertence à ação estruturada, não ao texto livre produzido pelo LLM.

A primeira escrita implementada — adicionar anotação humana a um caso sem alterar o payload sincronizado — é classificada como **low**.

## 7. Guardrails invariantes

Mesmo em Agent Mode permanecem obrigatórios:

1. autenticação;
2. autorização por perfil/permissão;
3. allowlist de ações suportadas;
4. validação estrutural dos argumentos;
5. auditoria;
6. separação entre fatos, inferências e anotações humanas;
7. preservação de proveniência;
8. fronteira PÉGASO para comunicação externa quando aplicável.

## 8. Consequências

### Positivas

- reduz fricção operacional;
- preserva autonomia do usuário;
- permite perfis de tolerância a risco diferentes;
- mantém segurança proporcional no modo padrão;
- cria base clara para futura execução multi-etapas;
- desacopla política de execução do provedor/modelo de IA.

### Negativas

- aumenta a responsabilidade de classificação correta de risco;
- Agent Mode exige maior maturidade de auditoria e permissões;
- erros de interpretação podem produzir ação mais rápida;
- exige testes específicos por modo.

## 9. Requisitos derivados

1. criar preferência persistente de modo por operador;
2. exibir toggle SAFE/AGENT no Assistente;
3. registrar mudança de modo na auditoria;
4. criar política central de risco por ação;
5. remover confirmação obrigatória de ações low-risk no Safe Mode;
6. manter confirmação contextual para high/critical no Safe Mode;
7. Agent Mode não poderá ampliar permissões nem ações suportadas;
8. toda nova ação do Assistente deverá declarar risco e requisitos de confirmação;
9. SPEC do Assistente deverá incorporar estes modos.

## 10. Critério de revisão

Revisar esta ADR caso:

- a plataforma implemente execução autônoma iniciada sem solicitação do usuário;
- sejam introduzidas ações externas de alto impacto;
- política institucional exija restrições adicionais;
- auditoria ou controle de permissões se mostrem insuficientes para Agent Mode.
