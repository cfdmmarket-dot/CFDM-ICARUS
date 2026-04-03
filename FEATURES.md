# ICARUS — Lista de Features
> Intelligent Conversational Assistant for Research, Understanding & Strategy
> Fonte: Análise de planejamento SYNCTHING + Base de design CFDM Holding
> Versão: v1.0.0 | Atualizado: 2026-04-03

---

## LEGENDA
- ✅ Implementado
- 🔨 Em desenvolvimento
- ⬜ Pendente

---

## CATEGORIA 1 — CORE / CÉREBRO CENTRAL

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| C01 | Memória persistente curto/médio/longo prazo (JSON) | ✅ | Alta |
| C02 | Motor de processamento de linguagem natural (NLP) | ✅ | Alta |
| C03 | Context awareness — deque de 20 mensagens | ✅ | Alta |
| C04 | Skill router — detecção de intenção por regex | ✅ | Alta |
| C05 | Sistema de modos operacionais (30+ modos) | ⬜ | Alta |
| C06 | commands.json — sistema de comandos estruturado | ⬜ | Alta |
| C07 | Goal Manager — definição e rastreamento de objetivos | ⬜ | Alta |
| C08 | Planner — quebra de objetivos em tarefas | ⬜ | Alta |
| C09 | Loop Autônomo — execução contínua sem intervenção | ⬜ | Média |
| C10 | Monitor — avaliação de resultados + ajuste estratégia | ⬜ | Média |
| C11 | Auto-priorização de objetivos | ⬜ | Média |
| C12 | Sistema de reflexão / auto-análise | ⬜ | Baixa |
| C13 | Auto-correção de erros + aprendizado por tentativa | ⬜ | Baixa |
| C14 | Simulação de cenários antes de agir | ⬜ | Baixa |
| C15 | Registro completo de decisões (decision log) | ⬜ | Média |

---

## CATEGORIA 2 — MODOS OPERACIONAIS (30+)

> Comando: `ICARUS, ativar modo [MODO] (NÍVEL | ESTILO | FOCO | PRIORIDADE)`

### Camada 1 — Estratégico (Alta Liderança)
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M01 | MESTRE DOS MAGOS | Recebe problemas complexos, acha solução e resolve | ⬜ |
| M02 | VICE PRESIDENTE | Tomada de decisão macro, visão de crescimento | ⬜ |
| M03 | SUPERINTENDENTE / CONSELHEIRO | Supervisão + validação de decisões | ⬜ |
| M04 | MESTRE | Visão total + pensamento sistêmico | ⬜ |

### Camada 2 — Gestão e Execução
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M05 | GESTOR / PROJETOS / NEGÓCIOS | Planejar, organizar e executar projetos | ⬜ |
| M06 | PLANNER | Planejamento estratégico e tático | ⬜ |
| M07 | SECRETÁRIO ADMINISTRATIVO | Organização, agenda, documentos | ⬜ |
| M08 | PERSONAL ASSISTENTE | Execução de tarefas do dia a dia | ⬜ |

### Camada 3 — Controle & Segurança
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M09 | SENTINELA | Monitoramento contínuo (erros, riscos, alertas) | ⬜ |
| M10 | GUARDIÃO | Proteção de dados, decisões críticas | ⬜ |

### Camada 4 — Especializados
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M11 | FINANÇAS | Gestão financeira, análise, previsão | ⬜ |
| M12 | DOUTOR / HOME CARE | Saúde, bem-estar | ⬜ |
| M13 | PERSONAL TRAINING | Treino físico e rotina saudável | ⬜ |
| M14 | ESPECIALISTA | Conhecimento técnico específico sob demanda | ⬜ |

### Camada 5 — Inteligência & Criação
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M15 | IDEATOR | Geração de ideias e brainstorming | ⬜ |
| M16 | CRIATIVO | Criação de conteúdo, branding, copy | ⬜ |
| M17 | PESQUISADOR | Coleta e análise de dados | ⬜ |
| M18 | CIENTISTA | Análise profunda e validação | ⬜ |
| M19 | SAFO / TENDÊNCIAS | Monitoramento de novidades e tendências | ⬜ |

### Camada 6 — Comportamental
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M20 | MORDOMO | Execução elegante + organização pessoal | ⬜ |
| M21 | ANJO | Suporte leve, positivo, encorajador | ⬜ |
| M22 | CONSELHEIRO ESPIRITUAL / MOTIVACIONAL | Mindset, motivação | ⬜ |
| M23 | HUMORISTA / ZUEIRA | Descontração e humor | ⬜ |
| M24 | ECLETICO | Adaptação geral a qualquer contexto | ⬜ |
| M25 | HELPER | Suporte simples e rápido | ⬜ |

### Camada 7 — Modos Operacionais Compostos
| ID | Modo | Função | Status |
|----|------|--------|--------|
| M26 | MODO HÍBRIDO | Combinação de múltiplos modos | ⬜ |
| M27 | DUAL (DUPLA) | Dois agentes com funções complementares | ⬜ |
| M28 | EQUIPE / TIME | Orquestração de múltiplos agentes | ⬜ |

---

## CATEGORIA 3 — INTERFACE (VOZ + TEXTO + MULTI-DEVICE)

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| I01 | Interface web 3 painéis (sidebar + chat + tasks) | ✅ | Alta |
| I02 | Botão de voz (Web Speech API, pt-BR) | ✅ | Alta |
| I03 | Wake word "ICARUS" — escuta contínua | ⬜ | Alta |
| I04 | Voz real TTS (pyttsx3 / ElevenLabs) — resposta em áudio | ⬜ | Alta |
| I05 | Interface mobile (PWA responsivo) | ⬜ | Média |
| I06 | Avatar visual animado (orbe central reativo) | ⬜ | Média |
| I07 | Tradução automática em tempo real | ⬜ | Média |
| I08 | Resposta com emoção (tom adaptável ao modo) | ⬜ | Média |
| I09 | Interface minimalista / avançada (toggle) | ⬜ | Baixa |
| I10 | Multi-idioma (PT, EN, ES) | ⬜ | Baixa |
| I11 | Dashboard React estilo JARVIS (multi-janelas) | ⬜ | Alta |
| I12 | WebSocket para controle em tempo real | ⬜ | Alta |
| I13 | Mapa visual de agentes (nós com status: ativo/processando/erro) | ⬜ | Média |
| I14 | Stream de pensamento — mostra raciocínio do ICARUS | ⬜ | Baixa |

---

## CATEGORIA 4 — ORQUESTRAÇÃO DE AGENTES

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| A01 | Integração com Cfdm Nexus via HTTP | ✅ | Alta |
| A02 | Invocar agente Nexus por setor | ✅ | Alta |
| A03 | Comando: `ICARUS, convocar [agente] do setor [setor] para [tarefa]` | ⬜ | Alta |
| A04 | Comando: `ICARUS, encontrar agente com [critérios]` | ⬜ | Alta |
| A05 | Comando: `ICARUS, montar equipe para [projeto]` | ⬜ | Alta |
| A06 | Hierarquia de agentes (CEO → Diretor → Executor) | ⬜ | Média |
| A07 | Delegação automática de tarefas | ⬜ | Média |
| A08 | Monitoramento de performance de agentes | ⬜ | Média |
| A09 | Execução paralela de tarefas | ⬜ | Baixa |
| A10 | Sistema de reputação interna de agentes | ⬜ | Baixa |
| A11 | Agentes temporários (on-demand) | ⬜ | Baixa |
| A12 | IA criando novas IAs (meta-agents) | ⬜ | Baixa |

---

## CATEGORIA 5 — SKILLS (DIÁRIAS E ESPECIALIZADAS)

| ID | Skill | Descrição | Status | Prioridade |
|----|-------|-----------|--------|-----------|
| S01 | tarefa_skill | Gestão de tarefas (criar/listar/completar) | ✅ | Alta |
| S02 | nexus_skill | Integração com Cfdm Nexus | ✅ | Alta |
| S03 | pesquisa_skill | Pesquisa na web / DuckDuckGo | ⬜ | Alta |
| S04 | financeiro_skill | Sentinela financeiro: contas, saldo, provisão | ⬜ | Alta |
| S05 | noticias_skill | Briefing de notícias matinal | ⬜ | Alta |
| S06 | email_skill | Leitura e resposta a e-mails | ⬜ | Alta |
| S07 | agenda_skill | Checar agenda do dia (Google Calendar) | ⬜ | Alta |
| S08 | saude_skill | Hidratação, pausas, treino, sono | ⬜ | Média |
| S09 | criacao_skill | Geração de conteúdo (YT/Instagram/TikTok) | ⬜ | Média |
| S10 | code_skill | Geração e revisão de código | ⬜ | Média |
| S11 | traducao_skill | Tradução de textos | ⬜ | Média |
| S12 | escrita_skill | Redação, copywriting, blog | ⬜ | Média |
| S13 | resumo_skill | Resumo de documentos longos | ⬜ | Média |
| S14 | nota_skill | Integração com CfdmNote | ⬜ | Alta |
| S15 | autocodificacao_skill | ICARUS cria/modifica scripts automaticamente | ⬜ | Baixa |

---

## CATEGORIA 6 — AUTOMAÇÃO FINANCEIRA

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| F01 | Verificar contas vencendo | ⬜ | Alta |
| F02 | Provisionar montante necessário | ⬜ | Alta |
| F03 | Alertas de fluxo de caixa | ⬜ | Alta |
| F04 | Integração com CFDMNote (contas via WebSocket C++) | ⬜ | Alta |
| F05 | Relatório financeiro em áudio (Modo Parça) | ⬜ | Média |
| F06 | Projeção de lucro/prejuízo | ⬜ | Média |
| F07 | Regra de reinvestimento: 80% → hardware/software | ⬜ | Baixa |
| F08 | Sugestão automática de oportunidades | ⬜ | Baixa |

---

## CATEGORIA 7 — SEGURANÇA & INFRAESTRUTURA

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| SEC01 | Criptografia de memória sensível | ⬜ | Alta |
| SEC02 | Modo Parça Incondicional — silêncio em caso de intrusão | ⬜ | Alta |
| SEC03 | Logs auditáveis imutáveis | ⬜ | Média |
| SEC04 | Controle de permissões por skill | ⬜ | Média |
| SEC05 | Backup automático de memória | ⬜ | Média |
| SEC06 | Comunicação ICARUS ↔ CFDMNote via WebSocket local | ⬜ | Alta |

---

## CATEGORIA 8 — EXPANSÃO / ECOSSISTEMA

| ID | Feature | Status | Prioridade |
|----|---------|--------|-----------|
| E01 | SDK ICARUS (API pública) | ⬜ | Baixa |
| E02 | Marketplace de skills plugáveis | ⬜ | Baixa |
| E03 | Integração com Docker/VMs | ⬜ | Baixa |
| E04 | Deploy em Raspberry Pi (núcleo local) | ⬜ | Média |
| E05 | Agente Scouter — monitoramento de tendências 24/7 | ⬜ | Média |
| E06 | Agente Prospector — identificação de oportunidades | ⬜ | Média |
| E07 | Agente DevOps Sentinel — saúde do sistema | ⬜ | Média |
| E08 | Agente Destilador — resume whitepapers/feeds → CFDMNote | ⬜ | Média |

---

## ROADMAP (10 FASES — Padrão CFDM com Regras Ouro/Prata/Ouro Rosa)

| Fase | Nome | Status | Regra |
|------|------|--------|-------|
| 1 | FUNDAÇÃO — Core + arquitetura modular | ✅ | Ouro |
| 2 | UI BASE — Interface 3 painéis + dark theme | ✅ | Ouro Rosa |
| 3 | CORE INTELIGENTE — Skills + modos + commands.json | 🔨 | Ouro |
| 4 | AGENTES — Orquestração de agentes Nexus | ⬜ | Ouro |
| 5 | AUTOMAÇÃO — Loop autônomo + scheduler | ⬜ | Prata |
| 6 | MONETIZAÇÃO — Skills financeiras + sentinela | ⬜ | Ouro |
| 7 | EXPANSÃO — Conteúdo digital + redes sociais | ⬜ | Ouro Rosa |
| 8 | INTELIGÊNCIA — Auto-melhoria + feedback loops | ⬜ | Ouro |
| 9 | ECOSSISTEMA — Integração total NEXUS + CFDMNote | ⬜ | Ouro |
| 10 | AUTONOMIA REAL — Sistema operando 24/7 | ⬜ | Ouro Rosa |

---

## REGRAS DE DESENVOLVIMENTO

### Regra de Ouro
> Tudo que for criado precisa ser: **Escalável · Automatizável · Monetizável · Replicável**

### Regra de Prata
> Nada pode depender de intervenção manual: **Rodar → Testar → Validar → Avançar**

### Regra Ouro Rosa
> Tudo precisa ter: **Estética absurda · Experiência fluida · Inteligência percebida ("wow")**
