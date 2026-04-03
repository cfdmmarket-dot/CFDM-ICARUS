# ICARUS — Contexto para o Claude Code
> Intelligent Conversational Assistant for Research, Understanding & Strategy
> CFDM Holding | v1.1.0

---

## ⚡ Regras de Ouro do Projeto (SEMPRE aplicar)

1. **Proceed = sempre SIM** — nunca perguntar "posso prosseguir?", "quer que eu faça?", "confirma?". Se o próximo passo for claro, executar diretamente.
2. **DEVLOG.md atualizado a cada sessão** — sem exceção. Commit separado no final.
3. **FEATURES.md sempre atualizado** — marcar ✅ quando implementado, 🔨 quando em progresso.
4. **SEMPRE bump de versão** em `icarus.py` e `web/server.py` a cada feature confirmada.
5. **Formato de versão: X.Y.Z** — commit com mensagem `feat(vX.Y.Z): descrição`.

---

## Regra de Ouro (Escalável · Automatizável · Monetizável · Replicável)
> Tudo que for criado precisa ser escalável, automatizável, monetizável e replicável.

## Regra de Prata (Nada Manual)
> Nada pode depender de intervenção manual. Tudo vira sistema, agente ou automação.

## Regra Ouro Rosa (Estética Absurda)
> Tudo precisa ter estética premium, experiência fluida e inteligência percebida (efeito "wow").

---

## O que é este projeto

ICARUS = Intelligent Conversational Assistant for Research, Understanding & Strategy.
Assistente pessoal de IA integrado ao ecossistema CFDM Holding:
- **Cfdm Nexus** — 286+ agentes de IA (porta 8000)
- **CfdmNote** — gerenciador de notas + cofre (C++17/Qt5)

### Papel do ICARUS no Ecossistema
```
[Usuário]
    ↓ voz/texto
[ICARUS Core] ← sistema de modos (30+ personalidades)
    ↓
[Skill Router] → [Skills: financeiro, tarefas, voz, nexus...]
    ↓
[Orquestrador] → [Cfdm Nexus (286+ agentes)]
    ↓
[CfdmNote] ← integração via WebSocket (futuro)
```

---

## Stack

- **Python 3.10+** + FastAPI (porta 8001)
- JSON puro para persistência (memory/)
- Web Speech API (STT browser-native)
- pyttsx3 (TTS local, offline)
- Whisper (STT avançado, opcional)
- Modular por skills em `skills/`

---

## Regras Absolutas

- SEMPRE Python 3.10+ — nunca C/C++ neste projeto
- SEMPRE FastAPI — nunca Flask, Django
- NUNCA dependências desnecessárias
- Skills são SEMPRE plugáveis (arquivo independente em `skills/`)
- Modos são SEMPRE carregados de `config/commands.json`
- Memória SEMPRE em JSON em `memory/`
- **SEMPRE atualizar DEVLOG.md ao final de cada sessão**
- **SEMPRE marcar features em FEATURES.md**

---

## Versão Atual: v1.2.0

### Features Confirmadas
- [x] v1.0.0 — Motor principal (IcarusCore), SkillRouter, MemoryManager, ContextEngine
- [x] v1.0.0 — Skill de tarefas (tarefa_skill.py)
- [x] v1.0.0 — Skill de integração Nexus (nexus_skill.py)
- [x] v1.0.0 — Servidor FastAPI porta 8001 (web/server.py)
- [x] v1.0.0 — Interface web 3 painéis: sidebar + chat + tasks (dark navy)
- [x] v1.0.0 — Botão de voz (Web Speech API, pt-BR, auto-send)
- [x] v1.0.0 — Atalho desktop (.desktop) + launcher script
- [x] v1.0.0 — CLI interativo (icarus.py)
- [x] v1.1.0 — Sistema de 28 modos operacionais em 7 camadas
- [x] v1.1.0 — config/commands.json — sistema central de comandos
- [x] v1.1.0 — Skill Financeiro (financeiro_skill.py) — sentinela financeiro
- [x] v1.1.0 — memory/finance.json — banco financeiro persistente
- [x] v1.1.0 — API: GET /modes, POST /modes/activate, POST /modes/deactivate, GET /agents
- [x] v1.1.0 — core/voice_engine.py — TTS (pyttsx3) + STT (Whisper)
- [x] v1.1.0 — skills/voz_skill.py — controle de voz via texto
- [x] v1.1.0 — FEATURES.md — 120+ features catalogadas em 8 categorias
- [x] v1.1.0 — _Planejamento_/ — 23 arquivos SYNCTHING como referência

### Features Pendentes (próximas)
- [x] v1.2.0 — Skill de notícias matinal (RSS nativo, sem dependências)
- [x] v1.2.0 — Skill de agenda local (memory/agenda.json)
- [ ] v1.2.0 — Wake word "ICARUS" (escuta contínua via Whisper)
- [ ] v1.3.0 — Skill de agenda Google Calendar API
- [ ] v1.3.0 — Dashboard React estilo JARVIS (WebSocket)
- [ ] v1.3.0 — Mapa visual de agentes (nós com status)
- [ ] v1.4.0 — Integração CFDMNote via WebSocket local
- [ ] v1.5.0 — Loop autônomo (Goal Manager + Planner)

---

## Workflow de Versionamento (OBRIGATÓRIO)

```
Feature implementada
       ↓
Testar localmente
       ↓
Bump ICARUS_VERSION em icarus.py e web/server.py
       ↓
Atualizar CLAUDE.md (features confirmadas)
       ↓
Atualizar FEATURES.md (✅ na feature)
       ↓
Atualizar DEVLOG.md
       ↓
git add -p (seletivo)
       ↓
git commit -m "feat(vX.Y.Z): descrição"
       ↓
git push origin main
```

---

## Arquitetura Atual

```
Proj-CFDM-ICARUS_/
├── CLAUDE.md          ← este arquivo
├── DEVLOG.md          ← histórico de desenvolvimento
├── FEATURES.md        ← lista de 120+ features
├── icarus.py          ← entry point CLI (ICARUS_VERSION aqui)
├── config/
│   └── commands.json  ← modos, agentes, padrões de comando
├── core/
│   ├── icarus_core.py ← motor principal + sistema de modos
│   ├── memory_manager.py
│   ├── skill_router.py
│   ├── context_engine.py
│   └── voice_engine.py ← TTS (pyttsx3) + STT (Whisper)
├── skills/
│   ├── tarefa_skill.py
│   ├── nexus_skill.py
│   ├── financeiro_skill.py
│   └── voz_skill.py
├── web/
│   ├── server.py       ← FastAPI porta 8001
│   └── templates/
│       └── index.html  ← UI 3 painéis dark navy
├── memory/
│   ├── user_profile.json
│   ├── memories.json
│   ├── tasks.json
│   └── finance.json
├── integrations/
├── logs/
└── _Planejamento_/    ← 23 arquivos SYNCTHING de referência
```

---

## Comandos do Sistema de Modos

```bash
# Ativar modo
ativar modo FINANCAS
ICARUS, ativar modo CRIATIVO (ALTO | CONTEÚDO | INSTAGRAM)
ativar modo MESTRE DOS MAGOS

# Agentes
convocar agente de marketing
montar equipe para projeto X
encontrar agente sênior de dev

# CLI
/modos       — listar todos os modos
/modo        — ver modo ativo
/status      — status do sistema
/tarefas     — tarefas pendentes
```

---

## Como Rodar

```bash
# CLI
python3 /home/cfdm/Proj-CFDM-ICARUS_/icarus.py

# Web (porta 8001)
cd /home/cfdm/Proj-CFDM-ICARUS_
python3 -m uvicorn web.server:app --port 8001 --reload

# Instalar dependências de voz (opcional)
pip install pyttsx3 openai-whisper pyaudio
```

---

## Git Identity

```
user.name: Cfdm-GitH
user.email: cfdm@users.noreply.github.com
```

## Repositório GitHub

- GitHub: https://github.com/cfdmmarket-dot/CFDM-ICARUS
- Branch: main
- Diretório: /home/cfdm/Proj-CFDM-ICARUS_/
