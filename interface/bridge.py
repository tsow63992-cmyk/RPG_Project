"""Pont entre l'interface et le moteur de jeu d'origine.

IMPORTANT : aucun fichier du jeu n'est modifie. On importe les classes
telles quelles (player.py, assassin.py, barbare.py, chevalier.py, mage.py)
et on se contente de les piloter. Les `print()` d'origine sont captures
et reaffiches dans le journal de combat de l'interface.
"""

import contextlib
import io


from assassin import Assassin
from barbare import Barbare
from chevalier import Chevalier
from mage import Mage


# ----------------------------------------------------------------- catalogue
# Couts et temps de recharge repris a l'identique de combat_manager.py.
COMPETENCES = {
    "Assassin": [
        dict(nom="Lame sonique", methode="lame_sonique", cout=0, cd=None,
             cible=True, icone="lame", fx="lame", touche=1,
             desc="Attaque rapide. Degats legers mais gratuits."),
        dict(nom="Double attaque", methode="attaque_double", cout=15,
             cd="double_cooldown", cible=True, icone="double", fx="double", touche=2,
             desc="Deux frappes enchainees. Recharge : 2 tours."),
        dict(nom="Lame toxique", methode="lame_toxique", cout=10,
             cd="poison_cooldown", cible=True, icone="poison", fx="poison", touche=3,
             desc="Degats moyens et applique Poison (3 tours)."),
        dict(nom="Camouflage", methode="camouflage", cout=20,
             cd="camouflage_cooldown", cible=False, icone="ombre", fx="ombre", touche=4,
             desc="Devient intouchable, prochaine attaque critique."),
        dict(nom="Soin", methode="soin", cout=25, cd="soin_cooldown",
             cible=False, icone="soin", fx="soin", touche=5,
             desc="Recupere 23 points de vie."),
    ],
    "Barbare": [
        dict(nom="Coup brutal", methode="coup_brutal", cout=0, cd=None,
             cible=True, icone="hache", fx="hache", touche=1,
             desc="Gros degats bruts, sans cout de mana."),
        dict(nom="Choc tellurique", methode="choc_tellurique", cout=10,
             cd="choc_countdown", cible=True, icone="choc", fx="choc", touche=2,
             desc="Frappe le sol : degats et reduction des degats subis."),
        dict(nom="Carnage", methode="carnage", cout=40, cd="carnage_countdown",
             cible=True, icone="crane", fx="carnage", touche=3,
             desc="Attaque ultime, degats extremes."),
        dict(nom="Mode rage", methode="mode_rage", cout=5, cd="rage_countdown",
             cible=False, icone="rage", fx="rage", touche=4,
             desc="+50% de degats sur la prochaine attaque."),
        dict(nom="Soin", methode="soin", cout=30, cd="soin_countdown",
             cible=False, icone="soin", fx="soin", touche=5,
             desc="Recupere 37 points de vie."),
    ],
    "Chevalier": [
        dict(nom="Escrime de Camelot", methode="escrime_de_camelot", cout=0,
             cd=None, cible=True, icone="epee_bouclier", fx="lame", touche=1,
             desc="Attaque de base a l'epee."),
        dict(nom="Provocation", methode="provocation", cout=15,
             cd="provocation_countdown", cible=False, icone="bouclier",
             fx="bouclier", touche=2,
             desc="Reduit les degats ennemis de 30% et prepare un contre."),
        dict(nom="Charge", methode="charge", cout=30, cd="charge_countdown",
             cible=True, icone="charge", fx="charge", touche=3,
             desc="Charge de bouclier : lourds degats."),
        dict(nom="Restauration", methode="restauration", cout=15,
             cd="res_countdown", cible=False, icone="armure", fx="bouclier", touche=4,
             desc="Regagne 10 points d'armure."),
        dict(nom="Soin", methode="soin", cout=25, cd="soin_countdown",
             cible=False, icone="soin", fx="soin", touche=5,
             desc="Recupere 31 points de vie."),
    ],
    "Mage": [
        dict(nom="Sort de base", methode="atk_basique", cout=0, cd=None,
             cible=True, icone="etoile", fx="magie", touche=1,
             desc="Petite attaque magique gratuite."),
        dict(nom="Boule de feu", methode="boule_de_feu", cout=15,
             cd="feu_countdown", cible=True, icone="feu", fx="feu", touche=2,
             desc="Degats de feu et applique Brulure (2 tours)."),
        dict(nom="Rayon de glace", methode="rayon_de_glace", cout=20,
             cd="glace_countdown", cible=True, icone="glace", fx="glace", touche=3,
             desc="Degats de glace et applique Froid."),
        dict(nom="Coup de tonnerre", methode="tonnerre", cout=50,
             cd="tonnerre_countdown", cible=True, icone="foudre", fx="foudre", touche=4,
             desc="Attaque ultime : critique garanti."),
        dict(nom="Bouclier magique", methode="bouclier_magique", cout=25,
             cd="armor_countdown", cible=False, icone="bulle", fx="bouclier", touche=5,
             desc="+6 d'armure, disparait au premier coup encaisse."),
        dict(nom="Drain", methode="drain", cout=20, cd="drain_countdown",
             cible=True, icone="drain", fx="drain", touche=6,
             desc="Vole 15 de mana a l'adversaire et rend 2 PV."),
        dict(nom="Soin", methode="soin", cout=35, cd="soin_countdown",
             cible=False, icone="soin", fx="soin", touche=7,
             desc="Recupere 21 points de vie."),
    ],
}

# statistiques de depart, identiques a combat_manager.py
_STATS = {
    "Assassin": (Assassin, 95, 70, 0),
    "Barbare": (Barbare, 150, 40, 0),
    "Chevalier": (Chevalier, 125, 50, 10),
    "Mage": (Mage, 85, 120, 0),
}

_REGEN = {"Assassin": "regen_assassin", "Barbare": "regen_barbare",
          "Chevalier": "regen_chevalier", "Mage": "regen_mage"}
_RESET = {"Assassin": "reset_assassin", "Barbare": "reset_barbare",
          "Chevalier": "reset_chevalier", "Mage": "reset_mage"}

_PASSIFS = {
    "Assassin": ["Poison : -4 a -6 PV par tour", "Camouflage : intouchable un tour"],
    "Barbare": ["Peau endurcie : -1 a -2 degats subis",
                "Esprit combatif : +1 degat par tranche de 10 PV perdus"],
    "Chevalier": ["Contre : riposte automatique apres une provocation"],
    "Mage": ["Affinite magique : +1 puissance par sort (max 5)",
             "Froid : -20% degats ennemis / Brulure : -3 PV par tour"],
}


def passifs(classe):
    return _PASSIFS[classe]


def _capturer(fn, *a, **kw):
    """Execute une methode du jeu en recuperant ses print()."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        try:
            fn(*a, **kw)
        except Exception as err:          # securite : l'interface ne doit jamais tomber
            print("Erreur interne : %s" % err)
    lignes = [l.strip() for l in tampon.getvalue().splitlines()]
    return [l for l in lignes if l]


# --------------------------------------------------------------- combattant
class Combattant:
    """Enveloppe legere autour d'un personnage du jeu d'origine."""

    def __init__(self, classe, pseudo, cote):
        cls, pv, mana, armure = _STATS[classe]
        self.classe = classe
        self.pseudo = pseudo
        self.cote = cote                       # 1 = gauche, -1 = droite
        self.j = cls(pseudo, pv, mana, armure)
        self.pv_max = pv
        self.mana_max = max(mana, 1)
        self.armure_max = max(armure, 10)
        self.competences = COMPETENCES[classe]
        self.degats_infliges = 0
        self.soins = 0

    # -- suivi des maxima (les soins peuvent depasser la valeur de depart)
    def rafraichir_maxima(self):
        self.pv_max = max(self.pv_max, self.j.hp)
        self.mana_max = max(self.mana_max, self.j.mana)
        self.armure_max = max(self.armure_max, self.j.armure)

    @property
    def vivant(self):
        return self.j.hp > 0

    def instantane(self):
        return (self.j.hp, self.j.mana, self.j.armure)

    # -- etat d'une competence : "ok", "mana" ou "recharge"
    def etat(self, comp):
        if comp["cd"] and getattr(self.j, comp["cd"], 0) > 0:
            return "recharge"
        # comme dans combat_manager.py, l'attaque de base ne coute rien et
        # reste utilisable meme si le Drain du mage a rendu le mana negatif
        if comp["cout"] > 0 and self.j.mana < comp["cout"]:
            return "mana"
        return "ok"

    def tours_restants(self, comp):
        return getattr(self.j, comp["cd"], 0) if comp["cd"] else 0

    def effets(self):
        """Liste des etats actifs a afficher sous forme de pastilles."""
        res = []
        j = self.j
        if getattr(j, "poison", 0) > 0:
            res.append(("poison", (150, 230, 90), "Poison", j.poison))
        if getattr(j, "brulure", 0) > 0:
            res.append(("feu", (255, 150, 70), "Brulure", j.brulure))
        if getattr(j, "froid", 0) > 0:
            res.append(("glace", (150, 226, 255), "Froid", j.froid))
        if getattr(j, "invisible", False):
            res.append(("ombre", (186, 140, 255), "Camouflage", None))
        if getattr(j, "rage", False):
            res.append(("rage", (255, 140, 60), "Rage", None))
        if getattr(j, "choc", False):
            res.append(("choc", (255, 200, 120), "Garde", None))
        if getattr(j, "contre_active", False):
            res.append(("bouclier", (140, 200, 255), "Contre", None))
        if getattr(j, "dgt_reduit", 0) > 0:
            res.append(("armure", (190, 220, 255), "Provocation", j.dgt_reduit))
        if getattr(j, "magic_armor", False):
            res.append(("bulle", (170, 210, 255), "Armure magique", None))
        if getattr(j, "magic_aff", 0) > 0:
            res.append(("etoile", (200, 180, 255), "Affinite", j.magic_aff))
        return res


# ----------------------------------------------------------------- deroule
def debut_de_tour(actif, passif):
    """Effets de debut de tour : poison/brulure, regeneration, cooldowns."""
    avant = actif.instantane()
    lignes = _capturer(actif.j.subir_degats, passif.j, 0)
    lignes += _capturer(getattr(actif.j, _REGEN[actif.classe]))
    # les cooldowns sont affiches visuellement : on ignore ce texte-la
    _capturer(getattr(actif.j, _RESET[actif.classe]))
    apres = actif.instantane()
    actif.rafraichir_maxima()
    return {
        "lignes": lignes,
        "degats_subis": max(0, avant[0] - apres[0]),
        "mana_gagne": max(0, apres[1] - avant[1]),
    }


def executer(actif, comp, cible):
    """Lance la competence choisie et resume ce qui s'est passe."""
    avant_a = actif.instantane()
    avant_c = cible.instantane()

    methode = getattr(actif.j, comp["methode"])
    if comp["cible"]:
        lignes = _capturer(methode, cible.j)
    else:
        lignes = _capturer(methode)

    apres_a = actif.instantane()
    apres_c = cible.instantane()
    actif.rafraichir_maxima()
    cible.rafraichir_maxima()

    degats = (avant_c[0] - apres_c[0]) + (avant_c[2] - apres_c[2])
    riposte = (avant_a[0] - apres_a[0])
    soin = max(0, apres_a[0] - avant_a[0])
    armure = max(0, apres_a[2] - avant_a[2])
    mana_vole = max(0, avant_c[1] - apres_c[1])
    critique = any("critique" in l.lower() for l in lignes)
    esquive = any("intouchable" in l.lower() for l in lignes)
    contre = any("contre-attaque" in l.lower() for l in lignes)

    actif.degats_infliges += max(0, degats)
    actif.soins += soin

    return {
        "lignes": [_joli(l) for l in lignes],
        "degats": max(0, degats),
        "riposte": max(0, riposte),
        "soin": soin,
        "armure": armure,
        "mana_vole": mana_vole,
        "critique": critique,
        "esquive": esquive,
        "contre": contre,
    }


_REMPLACEMENTS = [
    ("⚔", ""), ("\U0001f4a5", ""), ("☠", ""), ("\U0001f6e1", ""),
    ("⚡", ""), ("\U0001f525", ""),
]


def _joli(ligne):
    """Nettoie les emoji du texte d'origine (ils s'affichent mal en jeu)."""
    for a, b in _REMPLACEMENTS:
        ligne = ligne.replace(a, b)
    return " ".join(ligne.split())
