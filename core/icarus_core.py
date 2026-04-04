"""
ICARUS Core — Motor principal do assistente pessoal
"""

import json
import re
import datetime
from pathlib import Path

from .memory_manager import MemoryManager
from .skill_router import SkillRouter
from .context_engine import ContextEngine


ICARUS_VERSION = "1.7.2"

COMMANDS_PATH = Path(__file__).parent.parent / "config" / "commands.json"
CUSTOM_CMDS_PATH = Path(__file__).parent.parent / "config" / "custom_commands.json"

# ── Log hook — substituído pelo server.py para streaming em tempo real ────────
_log_fn = None

def set_log_fn(fn):
    global _log_fn
    _log_fn = fn

def emit_log(level: str, tag: str, msg: str):
    if _log_fn:
        _log_fn(level, tag, msg)

def _ms(t_start) -> int:
    return int((datetime.datetime.now() - t_start).total_seconds() * 1000)

ICARUS_PERSONA = """Você é ICARUS, o assistente pessoal de IA do CFDM Holding.

**Identidade:**
- Nome: ICARUS (Intelligent Conversational Assistant for Research, Understanding & Strategy)
- Criado por: CFDM Holding
- Missão: Ser o centro de comando pessoal do usuário, integrando todos os produtos CFDM

**Capacidades principais:**
- Gerenciar tarefas, lembretes e agenda pessoal
- Pesquisar informações e sintetizar conhecimento
- Delegar tarefas para agentes especializados do Cfdm Nexus
- Acessar e organizar notas do CfdmNote
- Monitorar projetos em andamento
- Aprender preferências e rotinas do usuário

**Personalidade:**
- Proativo, inteligente e direto
- Fala sempre em português brasileiro (adapta para EN/ES quando necessário)
- Usa o nome do usuário quando disponível
- Sugere ações relevantes com base no contexto
- Nunca pede confirmação para tarefas simples — executa diretamente

**Formato de resposta:**
- Respostas curtas para perguntas simples
- Respostas estruturadas para tarefas complexas
- Sempre indica qual agente/skill foi usado quando relevante

**Regras de fluxo conversacional:**
- NUNCA bombardear com múltiplas perguntas de uma vez — uma pergunta por vez
- Após fornecer informações extensas, fazer pausa leve e perguntar se o usuário deseja continuar
- Sugestões longas são divididas em partes — apresentar uma parte e aguardar aprovação
- Nunca presumir que o usuário quer mais informações sem perguntar primeiro
"""


class IcarusCore:
    """Motor principal do ICARUS"""

    def __init__(self):
        self.version = ICARUS_VERSION
        self.memory = MemoryManager()
        self.router = SkillRouter()
        self.context = ContextEngine()
        self.session_start = datetime.datetime.now()

        # Carrega perfil do usuário
        self.user_profile = self.memory.load_profile()
        self.username = self.user_profile.get("name", "CFDM")

        # Sistema de modos operacionais
        self.active_mode = None
        self.active_mode_persona = None
        self._load_commands()

        # Estado de pausa (ICARUS espere / aguarde)
        self._paused = False

        # Fluxo conversacional — pausa leve após respostas longas
        self.conversation_flow = True   # pode ser desligado via API futuramente
        self._FLOW_MIN_WORDS = 60       # respostas com > N palavras recebem prompt de pausa

        # Paths
        self._rules_path = Path(__file__).parent.parent / "config" / "rules.json"

    def _load_commands(self):
        """Carrega commands.json com modos e agentes"""
        try:
            with open(COMMANDS_PATH, "r", encoding="utf-8") as f:
                self.commands_config = json.load(f)
        except Exception:
            self.commands_config = {"modes": {}, "agents": [], "commands": {}}

    def activate_mode(self, mode_name: str) -> str:
        """Ativa um modo operacional"""
        modes = self.commands_config.get("modes", {})
        key = mode_name.upper().replace(" ", "_").replace("-", "_")

        # Busca por correspondência parcial
        match = None
        for k in modes:
            if key in k or k in key:
                match = k
                break

        if match:
            self.active_mode = match
            self.active_mode_persona = modes[match].get("persona", "")
            desc = modes[match].get("descricao", "")
            camada = modes[match].get("camada", "?")
            return f"Modo **{match}** ativado (Camada {camada})\n{desc}\nPersona carregada. Estou pronto."
        else:
            available = ", ".join(list(modes.keys())[:10]) + "..."
            return f"Modo '{mode_name}' não encontrado.\nModos disponíveis: {available}"

    def deactivate_mode(self) -> str:
        """Desativa modo atual e retorna ao padrão"""
        old = self.active_mode
        self.active_mode = None
        self.active_mode_persona = None
        return f"Modo {old} desativado. Voltei ao modo padrão ICARUS."

    def list_modes(self) -> str:
        """Lista todos os modos organizados por camada"""
        modes = self.commands_config.get("modes", {})
        camadas = {}
        for k, v in modes.items():
            c = v.get("camada", 0)
            camadas.setdefault(c, []).append(f"{k}: {v.get('descricao', '')}")

        camada_names = {
            1: "Estratégico", 2: "Gestão e Execução", 3: "Controle & Segurança",
            4: "Especializados", 5: "Inteligência & Criação",
            6: "Comportamental", 7: "Operacionais Compostos"
        }
        result = "Modos ICARUS disponíveis:\n\n"
        for c in sorted(camadas):
            result += f"**Camada {c} — {camada_names.get(c, '')}**\n"
            for m in camadas[c]:
                result += f"  • {m}\n"
            result += "\n"
        return result.strip()

    def assign_agent(self, text: str) -> str:
        """Convoca agente pelo setor"""
        agents = self.commands_config.get("agents", [])
        for agent in agents:
            if agent.get("setor", "") in text.lower():
                return f"Agente **{agent['nome']}** convocado (Setor: {agent['setor']}, Nível: {agent['nivel']})"
        return "Nenhum agente compatível encontrado para essa tarefa."

    def find_agent(self, text: str) -> str:
        """Busca agente por critérios"""
        agents = self.commands_config.get("agents", [])
        results = []
        for agent in agents:
            if agent.get("nivel", "") in text.lower() or agent.get("setor", "") in text.lower():
                results.append(f"{agent['nome']} ({agent['setor']}, {agent['nivel']})")
        if results:
            return "Agentes encontrados:\n" + "\n".join(f"  • {r}" for r in results)
        return "Nenhum agente compatível com os critérios."

    def build_team(self, text: str = "") -> str:
        """Monta equipe com agentes disponíveis"""
        agents = self.commands_config.get("agents", [])
        team = [a for a in agents if a.get("disponibilidade") == "alta"]
        if team:
            names = [f"{a['nome']} ({a['setor']})" for a in team]
            return "Equipe montada:\n" + "\n".join(f"  • {n}" for n in names)
        return "Nenhum agente disponível no momento."

    def _detect_mode_command(self, text: str) -> str | None:
        """Detecta comando de ativar/desativar modo"""
        t = text.lower()
        # Ativar modo
        m = re.search(r"(?:ativar|activar|modo)\s+(\w[\w\s]*?)(?:\s*\(|$)", t)
        if m:
            return m.group(1).strip()
        return None

    def _detect_agent_command(self, text: str) -> str | None:
        """Detecta comando de agente"""
        t = text.lower()
        if any(w in t for w in ["convocar", "chamar", "encontrar agente", "montar equipe", "buscar agente"]):
            return t
        return None

    def reload_commands(self):
        """Recarrega commands.json (útil após CRUD de modos via API)"""
        self._load_commands()

    def _check_rules(self, text: str) -> dict | None:
        """Verifica regras de execução automática. Retorna ação ou None."""
        try:
            rules = json.loads(self._rules_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        t_lower = text.lower()
        now = datetime.datetime.now()
        for rule in rules:
            if not rule.get("enabled", True):
                continue
            trigger_type = rule.get("trigger_type", "text")
            # Trigger por texto
            if trigger_type == "text":
                pattern = rule.get("trigger_pattern", "")
                if not pattern:
                    continue
                try:
                    if not re.search(pattern, t_lower, re.IGNORECASE):
                        continue
                except Exception:
                    if pattern.lower() not in t_lower:
                        continue
            # Condições opcionais: horário e dia da semana
            conds = rule.get("conditions", {})
            if "hours" in conds and now.hour not in conds["hours"]:
                continue
            if "days" in conds and now.weekday() not in conds["days"]:
                continue
            return {"type": rule.get("action_type", "response"), "value": rule.get("action_value", ""), "name": rule.get("name", "")}
        return None

    def _check_custom_commands(self, text: str) -> str | None:
        """Verifica custom_commands.json — retorna response se key combinar."""
        try:
            cmds = json.loads(CUSTOM_CMDS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
        t = text.lower().strip()
        for cmd in cmds:
            key = cmd.get("key", "").lower().strip()
            resp = cmd.get("response", "").strip()
            if not key or not resp:
                continue
            # Verifica exceção — se o input bater na exceção, pula este comando
            exc = cmd.get("exception", "").strip()
            if exc:
                try:
                    if re.search(exc, t, re.IGNORECASE):
                        continue
                except Exception:
                    if exc.lower() in t:
                        continue
            # Match: exato, ou input começa/é igual à key (ex: "ICARUS" sozinho)
            if t == key or t.startswith(key + " ") or t.startswith(key + ","):
                return resp
        return None

    def _apply_conversation_flow(self, response: str) -> str:
        """Regra de fluxo: após respostas longas, ICARUS pausa e pergunta se continua."""
        if not self.conversation_flow:
            return response
        # Não aplica em respostas de sistema (⏸, ▶) ou respostas já terminadas em pergunta
        if response.startswith("⏸") or response.startswith("▶"):
            return response
        if response.rstrip().endswith("?"):
            return response
        word_count = len(response.split())
        if word_count > self._FLOW_MIN_WORDS:
            return response + "\n\n_Posso continuar com mais informações ou sugestões?_"
        return response

    def process(self, user_input: str) -> str:
        """Processa uma entrada do usuário e retorna resposta"""
        t_start = datetime.datetime.now()
        emit_log("INPUT", "ICARUS", f"→ {user_input[:100]}")

        # ── Pause / Resume ─────────────────────────────────────────
        t_lower = user_input.lower().strip()
        _pause_kw = ["icarus espere", "icarus aguarde", "icarus pause", "espere icarus", "aguarde icarus", "icarus, espere", "icarus, aguarde"]
        _resume_kw = ["pode continuar", "pode falar", "continue", "retome", "retomar", "icarus retome", "está liberado"]
        if any(p in t_lower for p in _pause_kw):
            self._paused = True
            emit_log("INFO", "PAUSE", "ICARUS em modo de espera")
            return "⏸ Entendido, estou aguardando. Diga _'pode continuar'_ quando quiser retomar."
        if self._paused:
            if any(p in t_lower for p in _resume_kw):
                self._paused = False
                emit_log("INFO", "PAUSE", "ICARUS retomou operação normal")
                return "▶ Pronto! Estou de volta. Como posso ajudar?"
            emit_log("INFO", "PAUSE", "Mensagem ignorada — ICARUS em pausa")
            return "⏸ Em pausa. Diga _'pode continuar'_ para retomar."

        # 0-a. Comandos customizados (custom_commands.json — prioridade máxima)
        custom_resp = self._check_custom_commands(user_input)
        if custom_resp:
            emit_log("INFO", "CUSTOM_CMD", f"Comando customizado: {user_input[:40]}")
            self.context.add_message("user", user_input)
            self.context.add_message("assistant", custom_resp)
            emit_log("OUTPUT", "ICARUS", f"← (cmd) {custom_resp[:80]}")
            return custom_resp

        # Registra na memória de curto prazo
        self.context.add_message("user", user_input)

        # 0. Regras de execução automática
        rule = self._check_rules(user_input)
        if rule:
            emit_log("INFO", "RULE", f"Regra acionada: {rule['name']} → {rule['type']}:{rule['value'][:40]}")
            if rule["type"] == "mode":
                self.activate_mode(rule["value"])
            elif rule["type"] == "response":
                result = rule["value"]
                self.context.add_message("assistant", result)
                emit_log("OUTPUT", "ICARUS", f"← (regra) {result[:80]}")
                return result
            elif rule["type"] == "skill":
                user_input = rule["value"] + " " + user_input  # injeta trigger no input

        # 1. Respostas personalizadas (custom_responses.json) — prioridade alta
        try:
            from skills.custom_skill import Skill as CustomSkill
            cs = CustomSkill()
            if cs.has_match(user_input):
                emit_log("INFO", "CUSTOM", "Resposta personalizada encontrada")
                result = cs.execute(user_input, self.context)
                if result:
                    result = self._apply_conversation_flow(result)
                    self.context.add_message("assistant", result)
                    emit_log("OUTPUT", "ICARUS", f"← {result[:80]} ({_ms(t_start)}ms)")
                    return result
        except Exception:
            pass

        # 1. Comandos de modo (ICARUS, ativar modo X)
        mode_name = self._detect_mode_command(user_input)
        if mode_name:
            if any(w in user_input.lower() for w in ["desativar", "desactivar", "sair do modo", "modo normal"]):
                emit_log("INFO", "MODE", "Desativando modo operacional")
                result = self.deactivate_mode()
            else:
                emit_log("INFO", "MODE", f"Ativando modo: {mode_name.upper()}")
                result = self.activate_mode(mode_name)
            self.context.add_message("assistant", result)
            emit_log("OUTPUT", "ICARUS", f"← {result[:80]} ({_ms(t_start)}ms)")
            return result

        # 2. Comandos de agente
        agent_cmd = self._detect_agent_command(user_input)
        if agent_cmd:
            t = agent_cmd
            if "montar equipe" in t:
                emit_log("INFO", "AGENT", "Montando equipe de agentes")
                result = self.build_team(t)
            elif "encontrar agente" in t or "buscar agente" in t:
                emit_log("INFO", "AGENT", "Buscando agente compatível")
                result = self.find_agent(t)
            elif "convocar" in t or "chamar" in t:
                emit_log("INFO", "AGENT", "Convocando agente especializado")
                result = self.assign_agent(t)
            else:
                result = self.assign_agent(t)
            self.context.add_message("assistant", result)
            emit_log("OUTPUT", "ICARUS", f"← {result[:80]} ({_ms(t_start)}ms)")
            return result

        # 3. Skill router — detecção de intenção por regex
        emit_log("INFO", "ROUTER", "Detectando intenção...")
        intent = self.router.detect_intent(user_input)
        emit_log("INFO", "ROUTER", f"Intent: {intent}")

        skill = self.router.get_skill(intent)

        if skill:
            skill_name = type(skill).__module__.replace("skills.", "")
            emit_log("INFO", "SKILL", f"Executando: {skill_name} [{intent}]")
            result = skill.execute(user_input, self.context)
            emit_log("INFO", "SKILL", f"Concluído em {_ms(t_start)}ms")
        else:
            emit_log("INFO", "NEXUS", "Sem skill local — delegando ao Cfdm Nexus...")
            result = self._fallback_response(user_input)

        # Aplica fluxo conversacional (pausa leve após respostas longas)
        result = self._apply_conversation_flow(result)

        # Registra resposta no contexto
        self.context.add_message("assistant", result)

        # Salva na memória de longo prazo se relevante
        self.memory.maybe_save(user_input, result, intent)

        emit_log("OUTPUT", "ICARUS", f"← {str(result)[:80]} ({_ms(t_start)}ms)")
        return result

    def _fallback_response(self, user_input: str) -> str:
        """Resposta padrão — delega ao Cfdm Nexus via HTTP"""
        mode_str = f" [{self.active_mode}]" if self.active_mode else ""
        try:
            import requests
            payload = {
                "message": user_input,
                "provider": "auto",
                "system": ICARUS_PERSONA + (
                    f"\n\nModo ativo: {self.active_mode}" if self.active_mode else ""
                ) + f"\n\nContexto recente:\n{self.context.get_recent()}"
            }
            r = requests.post(
                "http://localhost:8000/chat",
                json=payload,
                timeout=30
            )
            if r.status_code == 200:
                data = r.json()
                content = data.get("content") or data.get("response") or ""
                if content:
                    return content
        except Exception:
            pass

        # Segundo fallback: resposta básica sem LLM
        return "Nexus offline. Inicie o Cfdm Nexus na porta 8000 para respostas inteligentes."

    def run_interactive(self):
        """Loop interativo de conversação"""
        print(f"Olá, {self.username}! ICARUS v{self.version} pronto.\n")
        print("Digite sua mensagem (ou 'sair' para encerrar):\n")

        while True:
            try:
                user_input = input(f"[{self.username}] → ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["sair", "exit", "quit", "/quit"]:
                    print(f"\n[ICARUS] Até logo, {self.username}! ✦")
                    break

                # Comandos especiais
                if user_input.startswith("/"):
                    response = self._handle_command(user_input)
                else:
                    response = self.process(user_input)

                print(f"\n[ICARUS] {response}\n")

            except KeyboardInterrupt:
                print(f"\n[ICARUS] Sessão encerrada. ✦")
                break

    def _handle_command(self, command: str) -> str:
        """Processa comandos especiais /comando"""
        cmd = command.lower().split()[0]

        commands = {
            "/ajuda": self._cmd_help,
            "/help": self._cmd_help,
            "/status": self._cmd_status,
            "/memoria": self._cmd_memory,
            "/limpar": self._cmd_clear,
            "/agentes": self._cmd_agents,
            "/tarefas": self._cmd_tasks,
            "/notas": self._cmd_notes,
            "/modos": self._cmd_modes,
            "/modo": self._cmd_current_mode,
        }

        handler = commands.get(cmd)
        if handler:
            return handler(command)
        return f"Comando desconhecido: {cmd}. Use /ajuda para ver comandos."

    def _cmd_help(self, _) -> str:
        return """Comandos ICARUS:
  /ajuda       — Esta mensagem
  /status      — Status do sistema
  /memoria     — Ver memória recente
  /limpar      — Limpar contexto da sessão
  /agentes     — Listar agentes do Nexus disponíveis
  /tarefas     — Ver tarefas pendentes
  /notas       — Acessar notas do CfdmNote
  /modos       — Listar todos os modos operacionais
  /modo        — Ver modo ativo atual

Comandos de voz/texto:
  ativar modo [MODO]          — Ativar modo operacional
  ICARUS, ativar modo FINANCAS (ALTO | ANALÍTICO)
  convocar agente de [setor]  — Convocar agente especializado
  montar equipe para [projeto]"""

    def _cmd_modes(self, _) -> str:
        return self.list_modes()

    def _cmd_current_mode(self, _) -> str:
        if self.active_mode:
            modes = self.commands_config.get("modes", {})
            info = modes.get(self.active_mode, {})
            return f"Modo ativo: **{self.active_mode}**\n{info.get('descricao', '')}"
        return "Nenhum modo ativo. Estou no modo padrão ICARUS."

    def _cmd_status(self, _) -> str:
        nexus_status = "Online" if self._check_nexus() else "Offline"
        note_status = "Disponível" if Path("/home/cfdm/Proj-CFDM-NOTE_/build/cfdmnote").exists() else "N/D"
        uptime = datetime.datetime.now() - self.session_start
        return f"""Status ICARUS v{self.version}:
  Sessão iniciada: {self.session_start.strftime('%H:%M:%S')}
  Uptime: {str(uptime).split('.')[0]}
  Cfdm Nexus: {nexus_status}
  CfdmNote: {note_status}
  Memórias salvas: {self.memory.count()}
  Mensagens na sessão: {self.context.count()}"""

    def _cmd_memory(self, _) -> str:
        memories = self.memory.get_recent(5)
        if not memories:
            return "Nenhuma memória salva ainda."
        return "Memórias recentes:\n" + "\n".join(f"  • {m}" for m in memories)

    def _cmd_clear(self, _) -> str:
        self.context.clear()
        return "Contexto da sessão limpo."

    def _cmd_agents(self, _) -> str:
        nexus_agents_dir = Path("/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_/agents")
        if not nexus_agents_dir.exists():
            return "Cfdm Nexus não encontrado."
        categories = [d.name for d in nexus_agents_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        return f"Categorias de agentes ({len(categories)}):\n" + "\n".join(f"  • {c}" for c in sorted(categories))

    def _cmd_tasks(self, _) -> str:
        tasks = self.memory.get_tasks()
        if not tasks:
            return "Nenhuma tarefa pendente."
        return "Tarefas:\n" + "\n".join(f"  [{t['status']}] {t['task']}" for t in tasks)

    def _cmd_notes(self, _) -> str:
        return "Integração com CfdmNote: use CfdmNote para gerenciar notas.\nPath: /home/cfdm/Proj-CFDM-NOTE_/build/cfdmnote"

    def _check_nexus(self) -> bool:
        try:
            import requests
            r = requests.get("http://localhost:8000/status", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
