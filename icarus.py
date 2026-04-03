#!/usr/bin/env python3
"""
ICARUS — Assistente Pessoal de IA — CFDM Holding
Integrado ao ecossistema Cfdm Nexus + CfdmNote
"""

import sys
import os
from pathlib import Path

# Adiciona o Cfdm Nexus ao path
NEXUS_DIR = Path("/home/cfdm/Proj-Cfdm-NEXUS-AI-OS-(Triplex )_")
if NEXUS_DIR.exists():
    sys.path.insert(0, str(NEXUS_DIR))

from core.icarus_core import IcarusCore


def main():
    print("\n" + "═" * 60)
    print("  ✦ ICARUS — Assistente Pessoal CFDM Holding ✦")
    print("  Powered by Cfdm Nexus AI OS")
    print("═" * 60 + "\n")

    icarus = IcarusCore()

    # Modo CLI interativo
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = icarus.process(task)
        print(result)
    else:
        icarus.run_interactive()


if __name__ == "__main__":
    main()
