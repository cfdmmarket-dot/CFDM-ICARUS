# ICARUS — Development Log
> Intelligent Conversational Assistant for Research, Understanding & Strategy
> CFDM Holding | Versão atual: v1.1.0

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
