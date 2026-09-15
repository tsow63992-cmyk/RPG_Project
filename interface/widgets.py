"""Briques d'interface : panneaux de verre, barres animees, boutons, puces."""

import math

import pygame

from . import theme
from .decor import halo
from . import sprites


# ------------------------------------------------------------------- textes
def texte(ecran, txt, taille, couleur, pos, ancre="topleft", gras=False,
          titre=False, ombre=True, alpha=255, espacement=0):
    f = theme.police(taille, gras, titre)
    if espacement:
        img = _rendu_espace(f, txt, couleur, espacement)
    else:
        img = f.render(txt, True, couleur)
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    r = img.get_rect()
    setattr(r, ancre, pos)
    if ombre:
        if espacement:
            o = _rendu_espace(f, txt, (6, 5, 14), espacement)
        else:
            o = f.render(txt, True, (6, 5, 14))
        o.set_alpha(int(150 * alpha / 255))
        ecran.blit(o, (r.x + 2, r.y + 2))
    ecran.blit(img, r)
    return r


def _rendu_espace(f, txt, couleur, espacement):
    """Rendu avec interlettrage (pour les titres)."""
    images = [f.render(c, True, couleur) for c in txt]
    largeur = sum(i.get_width() for i in images) + espacement * max(len(txt) - 1, 0)
    h = f.get_height()
    s = pygame.Surface((max(largeur, 1), h), pygame.SRCALPHA)
    x = 0
    for i in images:
        s.blit(i, (x, 0))
        x += i.get_width() + espacement
    return s


def envelopper(txt, taille, largeur, gras=False):
    """Decoupe un texte en lignes qui tiennent dans `largeur` pixels."""
    f = theme.police(taille, gras)
    lignes, courante = [], ""
    for mot in txt.split():
        essai = (courante + " " + mot).strip()
        if f.size(essai)[0] <= largeur or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def paragraphe(ecran, txt, taille, couleur, x, y, largeur, interligne=None,
               gras=False, alpha=255):
    f = theme.police(taille, gras)
    pas = interligne or int(taille * 1.5)
    for i, l in enumerate(envelopper(txt, taille, largeur, gras)):
        texte(ecran, l, taille, couleur, (x, y + i * pas), "topleft", gras=gras,
              ombre=False, alpha=alpha)
    return y + len(envelopper(txt, taille, largeur, gras)) * pas


def texte_lumineux(ecran, txt, taille, couleur, pos, ancre="center",
                   titre=True, espacement=4, force=3, couleur_lueur=None):
    """Titre avec halo colore (superposition de copies decalees)."""
    f = theme.police(taille, True, titre)
    img = _rendu_espace(f, txt, couleur, espacement)
    r = img.get_rect()
    setattr(r, ancre, pos)
    lueur = _rendu_espace(f, txt, couleur_lueur or couleur, espacement)
    lueur.set_alpha(46)
    for d in range(1, force + 1):
        for dx, dy in ((d * 3, 0), (-d * 3, 0), (0, d * 3), (0, -d * 3),
                       (d * 2, d * 2), (-d * 2, -d * 2),
                       (d * 2, -d * 2), (-d * 2, d * 2)):
            ecran.blit(lueur, (r.x + dx, r.y + dy))
    ecran.blit(img, r)
    return r


# ------------------------------------------------------------------ panneaux
_cache_panneaux = {}


def panneau(ecran, rect, alpha=168, bordure=None, rayon=18, fond=theme.ENCRE,
            trait=1, reflet=True):
    """Panneau translucide facon verre depoli."""
    r = pygame.Rect(rect)
    cle = (r.w, r.h, alpha, bordure, rayon, fond, trait, reflet)
    s = _cache_panneaux.get(cle)
    if s is None:
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (fond[0], fond[1], fond[2], alpha),
                         (0, 0, r.w, r.h), border_radius=rayon)
        if reflet:
            haut = pygame.Surface((r.w, max(r.h // 2, 2)), pygame.SRCALPHA)
            for i in range(0, haut.get_height(), 2):
                a = int(26 * (1 - i / haut.get_height()) ** 1.5)
                haut.fill((255, 255, 255, a), (0, i, r.w, 2))
            masque = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(masque, (255, 255, 255, 255), (0, 0, r.w, r.h),
                             border_radius=rayon)
            haut2 = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            haut2.blit(haut, (0, 0))
            haut2.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(haut2, (0, 0))
        if bordure:
            pygame.draw.rect(s, bordure, (0, 0, r.w, r.h), trait, border_radius=rayon)
        if len(_cache_panneaux) < 220:
            _cache_panneaux[cle] = s
    ecran.blit(s, r.topleft)
    return r


def lueur_rect(ecran, rect, couleur, force=70, marge=26):
    """Halo doux derriere un element selectionne."""
    r = pygame.Rect(rect)
    s = pygame.Surface((r.w + marge * 2, r.h + marge * 2), pygame.SRCALPHA)
    etapes = 9
    for i in range(etapes, 0, -1):
        t = i / etapes
        a = int(force * (1 - t) ** 1.6)
        d = int(marge * t)
        pygame.draw.rect(s, (couleur[0], couleur[1], couleur[2], a),
                         (marge - d, marge - d, r.w + d * 2, r.h + d * 2),
                         border_radius=20 + d)
    ecran.blit(s, (r.x - marge, r.y - marge))


# -------------------------------------------------------------------- barres
class Barre:
    """Barre de statistique avec interpolation douce et trainee de degats."""

    def __init__(self, valeur, maxi):
        self.cible = float(valeur)
        self.affiche = float(valeur)
        self.fantome = float(valeur)
        self.maxi = float(max(maxi, 1))

    def regler(self, valeur, maxi=None):
        if maxi:
            self.maxi = float(max(maxi, 1))
        self.cible = float(valeur)

    def avancer(self, dt):
        self.affiche += (self.cible - self.affiche) * min(1.0, dt * 9)
        if abs(self.affiche - self.cible) < 0.4:
            self.affiche = self.cible
        if self.fantome > self.affiche:
            self.fantome += (self.affiche - self.fantome) * min(1.0, dt * 2.4)
        else:
            self.fantome = self.affiche

    def dessiner(self, ecran, rect, c_haut, c_bas, fond=(16, 16, 32),
                 fantome=theme.PV_FANTOME, rayon=6, brillance=True):
        r = pygame.Rect(rect)
        pygame.draw.rect(ecran, fond, r, border_radius=rayon)
        pygame.draw.rect(ecran, (0, 0, 0, 90), r, 1, border_radius=rayon)
        ratio_f = max(0.0, min(1.0, self.fantome / self.maxi))
        ratio = max(0.0, min(1.0, self.affiche / self.maxi))
        if ratio_f > ratio + 0.001:
            w = int(r.w * ratio_f)
            if w > 2:
                pygame.draw.rect(ecran, fantome, (r.x, r.y, w, r.h),
                                 border_radius=rayon)
        w = int(r.w * ratio)
        if w > 1:
            barre = pygame.Surface((w, r.h), pygame.SRCALPHA)
            for i in range(r.h):
                t = i / max(r.h - 1, 1)
                c = (int(c_haut[0] + (c_bas[0] - c_haut[0]) * t),
                     int(c_haut[1] + (c_bas[1] - c_haut[1]) * t),
                     int(c_haut[2] + (c_bas[2] - c_haut[2]) * t))
                barre.fill(c, (0, i, w, 1))
            masque = pygame.Surface((w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(masque, (255, 255, 255, 255), (0, 0, w, r.h),
                             border_radius=rayon)
            barre.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            ecran.blit(barre, r.topleft)
            if brillance and r.h >= 8:
                eclat = pygame.Surface((w, max(r.h // 3, 2)), pygame.SRCALPHA)
                eclat.fill((255, 255, 255, 40))
                ecran.blit(eclat, (r.x, r.y + 2))


def barre_simple(ecran, rect, ratio, c_haut, c_bas, fond=(16, 16, 32), rayon=5):
    r = pygame.Rect(rect)
    pygame.draw.rect(ecran, fond, r, border_radius=rayon)
    w = int(r.w * max(0.0, min(1.0, ratio)))
    if w > 1:
        barre = pygame.Surface((w, r.h), pygame.SRCALPHA)
        for i in range(r.h):
            t = i / max(r.h - 1, 1)
            c = (int(c_haut[0] + (c_bas[0] - c_haut[0]) * t),
                 int(c_haut[1] + (c_bas[1] - c_haut[1]) * t),
                 int(c_haut[2] + (c_bas[2] - c_haut[2]) * t))
            barre.fill(c, (0, i, w, 1))
        masque = pygame.Surface((w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(masque, (255, 255, 255, 255), (0, 0, w, r.h),
                         border_radius=rayon)
        barre.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        ecran.blit(barre, r.topleft)


# --------------------------------------------------------------------- puces
def puce_effet(ecran, pos, nom_icone, couleur, libelle, tours=None):
    """Petite pastille d'etat (poison, rage, camouflage...)."""
    larg = 30 + (18 if tours else 0)
    r = pygame.Rect(pos[0], pos[1], larg, 26)
    s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (couleur[0], couleur[1], couleur[2], 56),
                     (0, 0, r.w, r.h), border_radius=13)
    pygame.draw.rect(s, couleur, (0, 0, r.w, r.h), 1, border_radius=13)
    ecran.blit(s, r.topleft)
    ic = sprites.icone_cache(nom_icone, 18, couleur)
    ecran.blit(ic, (r.x + 6, r.y + 4))
    if tours:
        texte(ecran, str(tours), 14, couleur, (r.x + 27, r.y + 13), "midleft",
              gras=True, ombre=False)
    return r


# ------------------------------------------------------------------- boutons
def bouton_competence(ecran, rect, comp, etat, accent, survol=False,
                      selectionne=False, pulsation=0.0):
    """Dessine un bouton de competence.

    etat : "ok", "mana", "recharge"
    """
    r = pygame.Rect(rect)
    dispo = etat == "ok"
    if selectionne and dispo:
        lueur_rect(ecran, r, accent, 80, 18)
    fond = theme.ARDOISE if dispo else (26, 26, 42)
    alpha = 220 if dispo else 150
    bordure = accent if (selectionne or survol) and dispo else (60, 62, 96)
    panneau(ecran, r, alpha, bordure, 12, fond, 2 if selectionne else 1,
            reflet=dispo)

    if dispo and (survol or selectionne):
        bande = pygame.Surface((5, r.h - 10), pygame.SRCALPHA)
        bande.fill(accent)
        ecran.blit(bande, (r.x + 4, r.y + 5))

    c_icone = accent if dispo else (92, 94, 122)
    c_texte = theme.TEXTE if dispo else (120, 122, 150)
    ic = sprites.icone_cache(comp["icone"], 26, c_icone)
    ecran.blit(ic, (r.x + 16, r.centery - 13))

    texte(ecran, comp["nom"], 17, c_texte, (r.x + 52, r.centery - 10), "topleft",
          gras=True, ombre=False)

    # cout / statut a droite
    if etat == "recharge":
        texte(ecran, "Recharge %d" % comp["_tours"], 13, theme.ROUGE,
              (r.right - 14, r.centery), "midright", gras=True, ombre=False)
    elif etat == "mana":
        texte(ecran, "%d MP" % comp["cout"], 13, theme.ROUGE,
              (r.right - 14, r.centery), "midright", gras=True, ombre=False)
    elif comp["cout"] > 0:
        texte(ecran, "%d MP" % comp["cout"], 13, theme.MANA_HAUT,
              (r.right - 14, r.centery), "midright", gras=True, ombre=False)
    else:
        texte(ecran, "libre", 13, theme.TEXTE_DOUX,
              (r.right - 14, r.centery), "midright", ombre=False)

    # raccourci clavier
    texte(ecran, str(comp["touche"]), 12, (110, 114, 150),
          (r.x + 52, r.centery + 8), "topleft", ombre=False)
    return r


def curseur_triangle(ecran, x, y, couleur, t):
    """Petit curseur clignotant facon JRPG."""
    d = math.sin(t * 6) * 4
    pygame.draw.polygon(ecran, couleur, [
        (x + d, y - 8), (x + d + 13, y), (x + d, y + 8)])
