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


ICARUS_VERSION = "1.1.0"

COMMANDS_PATH = Path(__file__).parent.parent / "config" / "commands.json"

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

    def process(self, user_input: str) -> str:
        """Processa uma entrada do usuário e retorna resposta"""
        # Registra na memória de curto prazo
        self.context.add_message("user", user_input)

        # 1. Comandos de modo (ICARUS, ativar modo X)
        mode_name = self._detect_mode_command(user_input)
        if mode_name:
            if any(w in user_input.lower() for w in ["desativar", "desactivar", "sair do modo", "modo normal"]):
                result = self.deactivate_mode()
            else:
                result = self.activate_mode(mode_name)
            self.context.add_message("assistant", result)
            return result

        # 2. Comandos de agente
        agent_cmd = self._detect_agent_command(user_input)
        if agent_cmd:
            t = agent_cmd
            if "montar equipe" in t:
                result = self.build_team(t)
            elif "encontrar agente" in t or "buscar agente" in t:
                result = self.find_agent(t)
            elif "convocar" in t or "chamar" in t:
                result = self.assign_agent(t)
            else:
                result = self.assign_agent(t)
            self.context.add_message("assistant", result)
            return result

        # 3. Skill router — detecção de intenção por regex
        intent = self.router.detect_intent(user_input)
        skill = self.router.get_skill(intent)

        if skill:
            result = skill.execute(user_input, self.context)
        else:
            result = self._fallback_response(user_input)

        # Registra resposta no contexto
        self.context.add_message("assistant", result)

        # Salva na memória de longo prazo se relevante
        self.memory.maybe_save(user_input, result, intent)

        return result

    def _fallback_response(self, user_input: str) -> str:
        """Resposta padrão — usa persona do modo ativo ou padrão ICARUS"""
        persona = ICARUS_PERSONA
        if self.active_mode and self.active_mode_persona:
            persona = f"{self.active_mode_persona}\n\n{ICARUS_PERSONA}"
        try:
            from triplex import TRIPLEX
            triplex = TRIPLEX()
            response = triplex.chat(
                user_input,
                system=persona + f"\n\nContexto recente:\n{self.context.get_recent()}"
            )
            return response.content
        except Exception as e:
            mode_str = f" [{self.active_mode}]" if self.active_mode else ""
            return f"[ICARUS{mode_str}] Recebi: {user_input}\n(Nexus offline: {e})"

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
