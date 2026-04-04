# ICARUS — Development Log
> Intelligent Conversational Assistant for Research, Understanding & Strategy
> CFDM Holding | Versão atual: v1.7.2

---

## [v1.7.2] — 2026-04-04

### Comandos customizados executáveis + Fluxo conversacional

#### Comandos customizados (custom_commands.json)
- **`_check_custom_commands()`** em `icarus_core.py` — verifica `custom_commands.json` antes de qualquer skill
- Campo **`response`** no comando: texto exato que o ICARUS responde quando a `key` é detectada
- Campo **`exception`** (regex): se o input bater nessa expressão, o comando não dispara
- Campo **`observation`**: nota interna do usuário, não processada pelo motor
- Match por: exato (`t == key`), começo (`startswith key + " "`) ou com vírgula
- Comando "ICARUS" → responde "Estou Aqui Senhor... Posso ajudá-lo com algo ou alguma coisa?"

#### Regra de fluxo conversacional
- **`_apply_conversation_flow()`** — aplicada após TODA resposta não-pausada
- Respostas com > 60 palavras recebem: `_"Posso continuar com mais informações ou sugestões?"_`
- `ICARUS_PERSONA` atualizado: proibido múltiplas perguntas simultâneas, sugestões longas divididas em partes
- Flag `conversation_flow` (padrão: `True`) — preparado para toggle via API

#### Modal Comandos — campos expandidos
- Formulário de criação/edição agora inclui: Resposta, Exceção e Observação
- Cards de comandos custom exibem preview colorido: resposta (azul), exceção (vermelho), observação (cinza)
- `server.py` endpoints POST/PUT `/commands` salvam/atualizam os novos campos

#### Versão
- `ICARUS_VERSION = "1.7.2"` em `icarus_core.py`
- `app = FastAPI(..., version="1.7.2")` em `web/server.py`

---

## [v1.7.1] — 2026-04-04

### Fix — Ecossistema status + launch funcional

#### Bug fixes críticos
- **`NameError: ICARUS_VERSION`** — variável não existia no escopo de `server.py`; corrigido para `icarus.version` (instância do core)
- **`async def ecosystem_status()` com `requests` síncrono** — bloqueava o event loop do uvicorn e retornava 500; convertido para `def` (FastAPI executa em thread pool automaticamente)
- **`pkill cfdmnote` muito genérico** — padrão atualizado para `build/cfdmnote` (evita matar processos errados)
- **DISPLAY não propagado para CfdmNote** — launcher agora lê `os.environ.get("DISPLAY", ":1")` e injeta no subprocesso
- **Versão hardcoded `v1.3.0` no HTML** — corrigida para `v1.7.1` em logo e painel Info

#### Resultado verificado
```json
GET /ecosystem/status →
{
  "icarus":   { "online": true, "version": "1.7.1" },
  "nexus":    { "online": true, "agents": 21 },
  "cfdmnote": { "running": true, "pid": 9741 }
}
```

---

## [v1.7.0] — 2026-04-04

### Adicionado — Modal Comandos CRUD + Regras de Execução + Pause + Ecossistema

#### ⌨ Modal Comandos — Redesign Completo (4 tabs)

**Tab: Comandos**
- Lista de 27 comandos builtin (read-only) com badge BUILTIN
- Comandos custom (CRUD completo): criar, editar, apagar
- Filtros: Todos / Builtin / Custom + busca em tempo real
- Formulário inline (sem modal extra): abre no topo, não cobre a lista
- `config/custom_commands.json` — persistência dos comandos do usuário
- Endpoint `GET/POST /commands`, `PUT/DELETE /commands/{id}`

**Tab: Modos**
- Grid de favoritos + lista completa (todos os 31 modos)
- Busca em tempo real por nome/descrição
- Criar novo modo: nome (KEY), descrição, camada (1-7), persona
- Editar modo existente: formulário pré-preenchido inline
- Apagar modo: remove do `commands.json` e recarrega core
- Endpoints: `POST /modes/create`, `PUT /modes/{key}`, `DELETE /modes/{key}`
- `icarus.reload_commands()` chamado após cada CRUD → core atualizado sem restart

**Tab: Regras de Execução**
- Sistema de automação: trigger → ação
- Tipos de gatilho: `text` (padrão regex) | `always` (toda mensagem)
- Tipos de ação: `mode` (ativa modo) | `response` (resposta fixa) | `skill` (injeta no input)
- Toggle on/off individual por regra (sem apagar)
- Formulário inline com preview do padrão
- `config/rules.json` — persistência
- Endpoints: `GET/POST /rules`, `PUT/DELETE /rules/{id}`
- `icarus_core._check_rules()` — avalia regras em toda mensagem antes do skill router

**Tab: Criar**
- 3 cards de tipo: Comando / Modo / Regra
- Formulário dinâmico conforme seleção
- Output de resultado inline (sucesso/erro)

#### ⏸ Pause / Resume (icarus_core)
- `"ICARUS espere"` / `"ICARUS aguarde"` → `_paused = True`, retorna "⏸ Estou aguardando"
- `"pode continuar"` / `"está liberado"` → `_paused = False`, retorna "▶ Pronto!"
- Enquanto pausado: toda mensagem retorna aviso de pausa sem processar
- Adicionado aos comandos builtin no modal (visible + clickable)

#### 🌐 Painel Ecossistema (substituiu tab "Nexus")
- Tab "Nexus" → "🌐 Apps" no painel direito
- Cards de status para cada app com dot colorido:
  - ⚡ ICARUS — sempre ● Online, mostra versão
  - 🤖 Cfdm Nexus — ● Online/Offline, conta agentes, botão Iniciar/Parar
  - 📓 CfdmNote — ● Ativo/Fechado, PID do processo, botão Abrir/Fechar
- Auto-refresh de status a cada 30 segundos
- Seção Nexus: lista de agentes + campo de tarefa + executar/chat (mantida)
- Seção CfdmNote: Abrir processo / Ver notas no chat / Abrir cofre
- `GET /ecosystem/status` — polling unificado (ICARUS + Nexus + CfdmNote)
- `POST /ecosystem/launch` — inicia Nexus ou CfdmNote com DISPLAY correto
- `POST /ecosystem/stop` — encerra serviço via pkill
- Botão toolbar: "⚡ Nexus" → "🌐 Apps"

#### 🔧 Desktop shortcuts corrigidos
- `ICARUS.desktop`: path `Proj-CFDM-ICARUS_` → `Proj-Cfdm-ICARUS_` (case-sensitive Linux)
- `CfdmNote.desktop`: `Proj-CFDM-NOTE_/build_asan` → `Proj-Cfdm-Note_/build` (binary correto)
- `icarus-launcher.sh`: `ICARUS_DIR` corrigido + versão atualizada para v1.7.0
- Ambos marcados como executáveis (`chmod +x`)

#### 🎨 Modal Skills — fix layout
- `max-height: 82vh` → `height: 82vh` (flex:1 nos filhos não funciona com max-height)
- `min-height: 0` adicionado em skPageList e skList (padrão correto para flex scroll)

---

## [v1.6.0] — 2026-04-04

### Adicionado — Memória de Projetos + Scroll Universal + Contraste UI

#### 📁 Memória Viva de Projetos (projeto_skill)
- **`memory/projects.json`** — fonte de verdade dos projetos CFDM Holding:
  - ICARUS, CfdmNote, Cfdm Nexus, Keepsidian com histórico completo
  - Últimas mudanças, próximos passos, stack, portas, regras absolutas por projeto
  - Histórico de sessões de desenvolvimento com arquivos modificados
- **`skills/projeto_skill.py`** — skill completa de gestão de projetos:
  - `"status dos projetos"` → overview de todos com badges de status
  - `"como está o CfdmNote"` → detalhes completos com stack e roadmap
  - `"próximos passos do ICARUS"` → backlog organizado
  - `"o que foi feito recentemente"` → sessões de desenvolvimento
  - `"analisa o projeto X"` → delega ao Nexus LLM com contexto do projeto
  - `"delegar ao Nexus: refatora Y"` → convoca agentes Nexus com contexto
  - `registrar mudança no projeto X: descrição` → atualiza memória
- **`core/skill_router.py`** — 13 novos padrões de intent `"projeto"`
- **Endpoints REST:**
  - `GET /projects` — memória completa JSON
  - `POST /projects/{key}/log` — registra sessão (Claude Code usa automaticamente)
  - `PATCH /projects/{key}/steps` — atualiza próximos passos
- **Modal 📁 Projetos** na toolbar (ao lado de Agentes):
  - Tab **Projetos** — cards com status 🟢/🟡/🔴, mudanças, próximos passos, botões 💬/🤖
  - Tab **Sessões** — histórico completo com scroll
  - Tab **✏ Registrar** — formulário para registrar sessão manual

#### 🖥 Terminal Flutuante com SSE Real-Time
- **`web/server.py`** — `/logs/stream` SSE endpoint (substitui polling 2s por push <150ms)
- **`core/icarus_core.py`** — `set_log_fn()` + `emit_log()` + `_ms()`: hook de log global
- Logs ricos em cada etapa: INPUT, ROUTER (intent), SKILL (nome + ms), NEXUS, OUTPUT
- **Terminal drawer** fixo na base, abre/fecha com `Ctrl+\`` ou botão 🖥 Terminal
- Filtros: TUDO / ENTRADA / ROTEADOR / SKILL / NEXUS / ERROS
- Redimensionável por arrasto, auto-scroll inteligente
- Campo de comando direto no rodapé (envia ao ICARUS sem abrir chat)
- Auto-abre quando usuário envia mensagem (mostra processamento em tempo real)

#### 🔌 Modal Skills
- **`GET /skills`** — endpoint que lista todas as skills com metadados (icon, desc, patterns, loaded)
- **Modal 🔌 Skills** na toolbar ao lado de 📊 Sistema:
  - Tab **Todas** — cards com BUILTIN/CRIADA badge, status ativa, padrões, KB
  - Botões: ▶ Testar, 👁 Código, 🗑 Deletar (dinâmicas)
  - Filtros: Todas / Builtin / Criadas + busca
  - Tab **+ Adicionar** — formulário com sugestões + campo 🎤 + opções avançadas (nome, padrões)

#### 🎭 Menu Modos
- **4 novos modos** em `config/commands.json`:
  - `ARQUITETO` — design de sistemas, soluções técnicas de alto nível
  - `ENGENHEIRO` — implementação técnica, código, debugging
  - `PARCA` — parceiro informal, casual e direto
  - `MORDOMO` — persona expandida com mais detalhe
- **Tab 🎭 Modos** no modal Comandos (ao lado de ⌨ Comandos):
  - Cards favoritos: Mordomo, Arquiteto, Engenheiro, Parça (1 clique ativa)
  - Grid com todos os 31 modos organizados por camada com ícone
  - Modo ativo exibido no rodapé do painel
- Atalho no POWER: "🎭 Ver todos os modos…"

#### 🤖 Agente Architect (Auto-Codificação)
- **`skills/autocode_skill.py`** — cria skills Python em linguagem natural:
  - Envia ao Nexus LLM com prompt-template padronizado
  - Valida sintaxe via `ast.parse()`, extrai `SKILL_NAME` e `TRIGGER_PATTERNS`
  - Hot-load via importlib + injeção no `_global_router`
  - Listar, deletar skills dinâmicas por chat
- **`config/dynamic_skills.json`** — criado na primeira skill gerada
- **`core/skill_router.py`** — `_global_router` global, `_load_dynamic_patterns()`, intent `autocode`
- **Tab 🤖 Architect** no POWER ICARUS: campo + 🎤 + sugestões rápidas + lista de criadas

#### 🎨 Contraste e Legibilidade (UI Fix)
- `--text-faint: #1e4a5a` → `#5a8fa8` (era quase invisível)
- `--text-dim: #5a90a8` → `#90bdd0`
- `--text: #c8ecf8` → `#d8f0fa`
- `--bg-input: #030a12` → `#071320`
- `--border: #0a2535` → `#0f2f42`
- CSS global: `modal [style*="text-faint"] → text-dim`, labels uppercase legíveis
- `.pwr-menu-label` → `rgba(255,255,255,0.45)` (era 0.25)
- `.modal-section-title` → `var(--text-dim)` (era text-faint)
- Placeholders, timestamps terminal, botões pwr-cmd todos corrigidos

#### 📜 Scroll Universal nos Modais
- `.modal-body` → `overflow-y: auto; max-height: 65vh` (regra global)
- Scrollbar fina estilizada (4px, cor accent)
- Modal Agentes → `max-height: 85vh` + contador de agentes visível
- Modal Projetos, Skills, Comandos/Modos todos com scroll correto

#### Fix: Menu POWER não expandia
- `.toolbar` separado de `.app-body` com `z-index: 200` vs `z-index: 1`
- `.app-body` vinha depois no DOM e cobria o dropdown

---

## [v1.5.0] — 2026-04-04

### Adicionado — Agente Architect (Auto-Codificação de Skills)

- **`skills/autocode_skill.py`** — Skill completa do Agente Architect:
  - Aceita comandos em linguagem natural ("criar skill para X")
  - Envia descrição ao Nexus LLM com prompt-template padronizado
  - Extrai bloco `python` da resposta, valida sintaxe via `ast.parse()`
  - Escreve arquivo `skills/<nome>_skill.py` automaticamente
  - Registra padrões de trigger em `config/dynamic_skills.json`
  - Hot-load via importlib + injeção no `_global_router` em memória
  - Listar skills dinâmicas: "listar skills criadas"
  - Deletar skill: "deletar skill <nome>"

- **`core/skill_router.py`** atualizado:
  - Intent `"autocode"` com 11 padrões regex
  - `_global_router` — referência global para hot-reload
  - `_load_dynamic_patterns()` — carrega padrões de `dynamic_skills.json` em cada `detect_intent()`
  - Skills dinâmicas ganham intent routing automático após criação
  - `SkillRouter.__init__` expõe `_global_router = self`

- **`web/server.py`** — 4 novos endpoints:
  - `GET /autocode/skills` — lista skills dinâmicas com metadados
  - `POST /autocode/create` — cria skill via API REST
  - `DELETE /autocode/skills/{name}` — deleta skill dinâmica
  - `GET /autocode/preview/{name}` — retorna código-fonte da skill
  - Versão bumped: 1.4.0 → **1.5.0**

- **`web/templates/index.html`** — Tab 🤖 Architect no POWER ICARUS:
  - Campo de descrição + botão 🎤 ditar + botão ⚡ Criar
  - Sugestões rápidas: Clima, CEP, Moedas, Senhas, Motivação, Timer
  - Lista de skills dinâmicas com preview 👁, recriar 🔄, deletar 🗑
  - Output em tempo real com status da criação
  - `architectCreate()`, `architectLoadSkills()`, `architectPreview()`, `architectDelete()`

- **`config/dynamic_skills.json`** — criado automaticamente na primeira skill gerada

### Decisão Arquitetural
```
Architect = Agente autônomo de criação de skills
Input: linguagem natural ("criar skill para verificar clima")
Pipeline: Nexus LLM → extração de código → validação → escrita → hot-load
Output: nova skill Python funcionando no ICARUS sem reinicialização
```

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
