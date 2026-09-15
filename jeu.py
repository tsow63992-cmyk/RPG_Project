#!/usr/bin/env python3
"""Lance le jeu de combat avec son interface graphique.

    python3 jeu.py

Le moteur d'origine (player.py, assassin.py, barbare.py, chevalier.py,
mage.py) est utilise tel quel, sans la moindre modification.
La version console reste disponible via `python3 combat_manager.py`.
"""

import os
import sys

# le dossier du jeu doit etre importable meme si on lance depuis ailleurs
RACINE = os.path.dirname(os.path.abspath(__file__))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("pygame n'est pas installe.")
        print("Installez-le avec :  pip install pygame")
        print("  (ou, sous Ubuntu/Debian :  sudo apt install python3-pygame)")
        return 1

    from interface.app import Application
    from interface.ecran_titre import EcranTitre

    plein_ecran = "--plein-ecran" in sys.argv or "-f" in sys.argv
    app = Application(plein_ecran=plein_ecran)
    app.lancer(EcranTitre(app))
    return 0


if __name__ == "__main__":
    sys.exit(main())
