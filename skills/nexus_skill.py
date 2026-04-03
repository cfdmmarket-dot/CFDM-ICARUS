"""
ICARUS Skill — Integração com Cfdm Nexus
"""

SKILL_NAME = "nexus"


class Skill:
    """Delega tarefas para agentes do Cfdm Nexus"""

    def execute(self, user_input: str, context) -> str:
        try:
            import requests

            # Tenta via API do Nexus
            response = requests.post(
                "http://localhost:8000/chat",
                json={"message": user_input, "provider": "auto"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                agent = data.get("agent", "Nexus")
                content = data.get("response", data.get("content", ""))
                return f"[{agent}] {content}"

        except Exception as e:
            pass

        return f"[ICARUS→Nexus] Nexus offline. Inicie o servidor: http://localhost:8000\nComando: cd '/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_' && python3 -m uvicorn web.server:app --port 8000"
