# ICARUS — Development Log
> Intelligent Conversational Assistant for Research, Understanding & Strategy
> CFDM Holding | Versão atual: v1.3.1

---

## [v1.3.1] — 2026-04-03

### Adicionado — Cfdm Nexus Integrado ao Painel ICARUS
- **Tab ⚡ Nexus** no right panel — Nexus agora vive dentro do ICARUS (sem abrir nova aba)
- **Status em tempo real** — indicador online/offline com dot verde/vermelho e contador de agentes
- **Lista de agentes pesquisável** — busca em tempo real, seleção com clique
- **Execução direta** — campo de tarefa + botão ▶ Executar roda o agente via ICARUS chat
- **Alternativa Chat** — botão 💬 envia o comando pelo chat visível (transparente)
- **API: GET /nexus/status** — proxy para Nexus /status (sem CORS no frontend)
- **API: POST /nexus/run** — executa agente via nexus_skill do ICARUS
- **Launcher unificado** — `icarus-launcher.sh` agora inicia Nexus (:8000) antes do ICARUS (:8001)
- Sidebar "Ecossistema": clique em Nexus abre o painel integrado (não nova aba)
- `checkNexus()` migrado para `/nexus/status` proxy (elimina chamadas CORS diretas)

### Decisão Arquitetural
```
Nexus DENTRO do ICARUS (não o contrário):
- ICARUS = interface (assistente pessoal, front-end)
- Nexus  = motor (286+ agentes, back-end invisível)
- Um launcher abre tudo; usuário usa apenas ICARUS (:8001)
```

---

## [v1.3.0] — 2026-04-03

### Adicionado — JARVIS HUD + Voice Mode
- **UI JARVIS/Iron Man** — paleta cyan `#00d4ff`, fundo `#020c14`, grade HUD, scanlines, Orbitron font
- **Voice Orb** — overlay fullscreen com anéis rotativos, estado wake/escuta/pensando
- **Wake word** — detecção de "ICARUS/ICARO/ÍCARUS" em loop contínuo (Web Speech API)
- **Push-to-Talk (PTT)** — MediaRecorder → POST /voice/transcribe → Whisper local → texto
- **TTS** — SpeechSynthesis pt-BR, limpa markdown, fala respostas automaticamente
- **API: POST /voice/transcribe** — faster-whisper → openai-whisper fallback (offline)
- **API: GET /voice/status** — informa engines disponíveis
- **API: GET /system** — CPU/RAM/disco via psutil
- **API: GET /logs** — últimas N entradas do buffer de log
- **API: GET /scripts** — lista scripts/*.py
- Modais: Agentes, Comandos, Logs, Sistema, Ferramentas, Config, Manual
- Animação de boot na tela de boas-vindas
- Fix: erro de rede no microfone — mensagem amigável + fallback Whisper

---

## [v1.2.0] — 2026-04-03

### Adicionado
- **Skill de Notícias** (`skills/noticias_skill.py`) — RSS nativo sem dependências externas
- **Skill de Agenda** (`skills/agenda_skill.py`) — agenda local em `memory/agenda.json`
- `skill_router.py` — intents noticias + agenda com padrões em PT-BR

---

## [v1.1.0] — 2026-04-03

### Adicionado
- **Sistema de modos operacionais** — 30+ modos em 7 camadas funcionais (Estratégico, Gestão, Controle, Especializados, Inteligência, Comportamental, Operacionais Compostos)
- **commands.json** — Arquivo de configuração central com modos, agentes e padrões de comandos (`config/commands.json`)
- **Skill Financeiro** (`skills/financeiro_skill.py`) — Sentinela financeiro: verifica contas vencendo, calcula saldo, provisiona montantes, gera relatórios
- **memory/finance.json** — Banco de dados financeiro persistente
- **API: GET /modes** — Lista todos os modos disponíveis com metadados
- **API: POST /modes/activate** — Ativa modo operacional via HTTP
- **API: POST /modes/deactivate** — Desativa modo atual
- **API: GET /agents** — Lista agentes do sistema de comandos
- **FEATURES.md** — Lista completa de 120+ features organizadas em 8 categorias
- **_Planejamento_/** — 18 arquivos de planejamento copiados do SYNCTHING como referência
- **Comandos de texto**: `ativar modo [MODO]`, `convocar agente`, `montar equipe`, `encontrar agente`
- **/modos** e **/modo** — Novos comandos CLI para listar e ver modo ativo

### Melhorado
- `icarus_core.py` — Integra modos, agentes, skill financeira; bump para v1.1.0
- `skill_router.py` — Padrões financeiros adicionados; skills builtins carregadas diretamente
- `web/server.py` — Novos endpoints de modos e agentes; versão 1.1.0

### Arquitetura de Modos
```
ICARUS, ativar modo [MODO] (NÍVEL | ESTILO | FOCO | PRIORIDADE)

Camada 1 — Estratégico: MESTRE_DOS_MAGOS, VICE_PRESIDENTE, SUPERINTENDENTE, MESTRE
Camada 2 — Gestão: GESTOR, PLANNER, SECRETARIO, PERSONAL_ASSISTENTE
Camada 3 — Controle: SENTINELA, GUARDIAO
Camada 4 — Especializados: FINANCAS, DOUTOR, PERSONAL_TRAINING, ESPECIALISTA
Camada 5 — Inteligência: IDEATOR, CRIATIVO, PESQUISADOR, CIENTISTA, TENDENCIAS
Camada 6 — Comportamental: MORDOMO, ANJO, MOTIVACIONAL, HUMORISTA, ECLETICO, HELPER
Camada 7 — Compostos: HIBRIDO, DUAL, EQUIPE
```

---

## [v1.0.0] — 2026-04-03

### Lançamento inicial
- Motor principal `core/icarus_core.py` com persona ICARUS
- Memória persistente JSON (`memory_manager.py`)
- Context engine com deque de 20 mensagens (`context_engine.py`)
- Skill router com detecção de intenção por regex (`skill_router.py`)
- Skill de tarefas (`skills/tarefa_skill.py`)
- Skill de integração Nexus (`skills/nexus_skill.py`)
- Servidor FastAPI na porta 8001 (`web/server.py`)
- Interface web 3 painéis: sidebar + chat + painel de tarefas
- Botão de voz (Web Speech API, pt-BR)
- Atalho de desktop (`.desktop`) + launcher script
- CLI interativo (`icarus.py`)
