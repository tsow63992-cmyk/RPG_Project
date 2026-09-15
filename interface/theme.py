"""Palette, typographie et constantes visuelles de l'interface.

Aucune dépendance au jeu : ce module ne fait que décrire le style.
"""

import pygame

# ---------------------------------------------------------------- dimensions
LARGEUR = 1280
HAUTEUR = 720
FPS = 60

# ------------------------------------------------------------------ couleurs
NOIR        = (8, 7, 16)
ENCRE       = (13, 12, 28)
NUIT        = (18, 17, 38)
ARDOISE     = (30, 30, 58)
ARDOISE_CLR = (48, 48, 86)
BRUME       = (120, 126, 168)
TEXTE       = (226, 230, 248)
TEXTE_DOUX  = (156, 163, 200)
BLANC       = (255, 255, 255)

OR          = (255, 198, 88)
OR_SOMBRE   = (186, 132, 40)
CYAN        = (94, 226, 236)
VIOLET      = (167, 120, 255)
ROSE        = (255, 122, 182)
ROUGE       = (255, 86, 92)
ROUGE_SANG  = (196, 44, 52)
VERT        = (92, 224, 150)
VERT_POISON = (146, 226, 86)
ORANGE      = (255, 146, 62)
BLEU        = (94, 164, 255)
BLEU_GLACE  = (150, 226, 255)
JAUNE       = (255, 232, 110)

# barres
PV_HAUT     = (104, 228, 138)
PV_BAS      = (46, 168, 92)
PV_FANTOME  = (255, 96, 96)
MANA_HAUT   = (108, 178, 255)
MANA_BAS    = (58, 110, 220)
ARMURE_HAUT = (206, 214, 236)
ARMURE_BAS  = (128, 140, 176)

# ------------------------------------------------------------------- classes
# couleur d'accent + identité visuelle de chacune des 4 classes d'origine
CLASSES = {
    "Assassin": {
        "accent": (176, 122, 255),
        "accent2": (86, 244, 210),
        "titre": "ASSASSIN",
        "devise": "Rapide, poison, camouflage",
        "detail": "Frappe dans l'ombre et laisse le poison finir le travail.",
        "pv": 95, "mana": 70, "armure": 0,
        "atk": 2, "def": 1, "vit": 5, "mag": 2,
    },
    "Barbare": {
        "accent": (255, 128, 72),
        "accent2": (255, 208, 96),
        "titre": "BARBARE",
        "devise": "Puissance brute, mode rage",
        "detail": "Plus il souffre, plus il frappe fort. Aucune subtilite.",
        "pv": 150, "mana": 40, "armure": 0,
        "atk": 5, "def": 2, "vit": 2, "mag": 1,
    },
    "Chevalier": {
        "accent": (108, 196, 255),
        "accent2": (226, 236, 255),
        "titre": "CHEVALIER",
        "devise": "Tank, bouclier, contre-attaque",
        "detail": "Encaisse, provoque, riposte et restaure son armure.",
        "pv": 125, "mana": 50, "armure": 10,
        "atk": 2, "def": 5, "vit": 2, "mag": 2,
    },
    "Mage": {
        "accent": (128, 152, 255),
        "accent2": (168, 240, 255),
        "titre": "MAGE",
        "devise": "Feu, glace, foudre et drain",
        "detail": "Fragile mais devastateur : chaque sort le rend plus fort.",
        "pv": 85, "mana": 120, "armure": 0,
        "atk": 3, "def": 1, "vit": 3, "mag": 5,
    },
}

ORDRE_CLASSES = ["Assassin", "Barbare", "Chevalier", "Mage"]

# ---------------------------------------------------------------- typographie
# On evite scrupuleusement les emoji (ils s'affichent en carres vides sur
# beaucoup de systemes) : toutes les icones de l'interface sont dessinees.
_PREFERENCES = [
    "poppins", "montserrat", "raleway", "nunito", "quicksand",
    "segoeui", "ubuntu", "cantarell", "notosans", "dejavusans",
    "freesans", "liberationsans", "arial", "helvetica",
]
_PREFERENCES_TITRE = [
    "orbitron", "russoone", "bebasneue", "oswald", "anton",
    "poppins", "montserrat", "impact", "ubuntu", "dejavusans",
]

_cache = {}
_chemin_texte = None
_chemin_titre = None


def _trouver(preferences):
    for nom in preferences:
        try:
            chemin = pygame.font.match_font(nom, bold=False)
        except Exception:
            chemin = None
        if chemin:
            return chemin
    return None


def init_polices():
    """Resout une seule fois les fichiers de police disponibles."""
    global _chemin_texte, _chemin_titre
    if not pygame.font.get_init():
        pygame.font.init()
    _chemin_texte = _trouver(_PREFERENCES)
    _chemin_titre = _trouver(_PREFERENCES_TITRE) or _chemin_texte


def police(taille, gras=False, titre=False):
    """Retourne (et met en cache) une police a la taille demandee."""
    cle = (taille, gras, titre)
    if cle in _cache:
        return _cache[cle]
    chemin = _chemin_titre if titre else _chemin_texte
    if chemin:
        f = pygame.font.Font(chemin, taille)
        f.set_bold(gras)
    else:
        f = pygame.font.Font(None, int(taille * 1.15))
        f.set_bold(gras)
    _cache[cle] = f
    return f
