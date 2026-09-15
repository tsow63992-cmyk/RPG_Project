"""Pixel-art genere par code : combattants, icones de competences, lune, arbres.

Tout est dessine a la main sur une petite grille de pixels puis agrandi,
ce qui donne un rendu "jeu 16 bits" net, sans aucun fichier d'image externe.
"""

import math
import pygame

from . import theme


# =========================================================== toile de pixels
class Toile:
    """Petite grille de pixels avec des primitives de dessin."""

    def __init__(self, largeur, hauteur):
        self.l = largeur
        self.h = hauteur
        self.g = [[None] * largeur for _ in range(hauteur)]

    # -- primitives -------------------------------------------------------
    def px(self, x, y, c):
        if 0 <= x < self.l and 0 <= y < self.h and c is not None:
            self.g[int(y)][int(x)] = c

    def rect(self, x, y, w, h, c):
        for j in range(int(y), int(y + h)):
            for i in range(int(x), int(x + w)):
                self.px(i, j, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for j in range(int(cy - ry), int(cy + ry) + 1):
            for i in range(int(cx - rx), int(cx + rx) + 1):
                dx = (i - cx) / max(rx, 0.001)
                dy = (j - cy) / max(ry, 0.001)
                if dx * dx + dy * dy <= 1.05:
                    self.px(i, j, c)

    def ligne(self, x0, y0, x1, y1, c, epaisseur=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / max(n, 1)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if epaisseur <= 1:
                self.px(round(x), round(y), c)
            else:
                r = epaisseur / 2
                self.ellipse(round(x), round(y), r, r, c)

    def triangle(self, p0, p1, p2, c):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        for j in range(int(min(ys)), int(max(ys)) + 1):
            for i in range(int(min(xs)), int(max(xs)) + 1):
                if _dans_triangle(i + 0.5, j + 0.5, p0, p1, p2):
                    self.px(i, j, c)

    # -- post-traitement --------------------------------------------------
    def contour(self, couleur):
        """Ajoute un liser sombre autour de la silhouette (style pixel-art)."""
        ajout = []
        for y in range(self.h):
            for x in range(self.l):
                if self.g[y][x] is not None:
                    continue
                voisin = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    i, j = x + dx, y + dy
                    if 0 <= i < self.l and 0 <= j < self.h and self.g[j][i] is not None:
                        voisin = True
                        break
                if voisin:
                    ajout.append((x, y))
        for x, y in ajout:
            self.g[y][x] = couleur

    def surface(self, echelle=1):
        s = pygame.Surface((self.l * echelle, self.h * echelle), pygame.SRCALPHA)
        for y in range(self.h):
            for x in range(self.l):
                c = self.g[y][x]
                if c is not None:
                    s.fill(c, (x * echelle, y * echelle, echelle, echelle))
        return s


def _signe(px, py, ax, ay, bx, by):
    return (px - bx) * (ay - by) - (ax - bx) * (py - by)


def _dans_triangle(px, py, a, b, c):
    d1 = _signe(px, py, a[0], a[1], b[0], b[1])
    d2 = _signe(px, py, b[0], b[1], c[0], c[1])
    d3 = _signe(px, py, c[0], c[1], a[0], a[1])
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def _melange(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ====================================================== combattants 22 x 28
L_SPR, H_SPR = 22, 28
_CONTOUR = (14, 10, 24)


def _jambes(t, sombre, clair, bottes):
    t.rect(8, 20, 3, 5, sombre)
    t.rect(12, 20, 3, 5, sombre)
    t.px(8, 20, clair)
    t.px(12, 20, clair)
    t.rect(7, 25, 5, 2, bottes)
    t.rect(11, 25, 5, 2, bottes)


def _assassin():
    t = Toile(L_SPR, H_SPR)
    cape = (58, 30, 96)
    cape_c = (86, 48, 134)
    corps = (36, 24, 56)
    corps_c = (58, 40, 84)
    capuche = (108, 62, 182)
    capuche_c = (146, 98, 224)
    peau = (28, 20, 40)
    oeil = (128, 250, 240)
    acier = (214, 230, 255)
    acier_s = (132, 156, 196)
    cuir = (74, 48, 40)

    # cape derriere (le personnage regarde vers la droite)
    t.triangle((4, 11), (10, 11), (3, 26), cape)
    t.triangle((4, 11), (8, 11), (4, 24), cape_c)
    # jambes + torse
    _jambes(t, corps, corps_c, cuir)
    t.rect(7, 12, 8, 9, corps)
    t.rect(7, 12, 3, 9, corps_c)
    t.rect(7, 16, 8, 1, cuir)          # ceinture
    t.px(11, 16, (226, 196, 120))
    # tete + capuche
    t.ellipse(11, 7, 4, 4.5, peau)
    t.ellipse(11, 6, 5, 5, capuche)
    t.ellipse(11, 5, 4, 3.6, capuche_c)
    t.rect(11, 5, 5, 5, capuche)       # bec de la capuche vers l'avant
    t.triangle((14, 4), (17, 8), (13, 10), capuche)
    t.rect(11, 7, 4, 3, peau)          # visage dans l'ombre
    t.px(14, 8, oeil)
    t.px(13, 8, oeil)
    t.px(14, 9, _melange(oeil, peau, 0.5))
    # echarpe
    t.rect(8, 11, 7, 2, cape_c)
    t.triangle((6, 11), (9, 11), (2, 17), cape_c)
    # bras + dagues
    t.rect(15, 13, 3, 2, corps_c)      # bras avant
    t.rect(5, 14, 3, 2, corps_c)       # bras arriere
    t.rect(17, 12, 2, 2, cuir)         # poignee avant
    t.ligne(18, 12, 21, 8, acier)      # dague avant
    t.ligne(19, 13, 21, 10, acier_s)
    t.rect(3, 15, 2, 2, cuir)          # poignee arriere
    t.ligne(4, 16, 1, 20, acier)       # dague arriere
    t.ligne(5, 17, 2, 21, acier_s)
    t.contour(_CONTOUR)
    return t.surface()


def _barbare():
    t = Toile(L_SPR, H_SPR)
    peau = (218, 152, 108)
    peau_c = (240, 186, 140)
    peau_s = (168, 106, 74)
    cheveux = (198, 74, 40)
    cheveux_c = (238, 122, 62)
    fourrure = (94, 58, 40)
    fourrure_c = (134, 88, 58)
    casque = (176, 150, 96)
    corne = (236, 226, 198)
    acier = (206, 216, 232)
    acier_s = (120, 132, 156)
    bois = (108, 70, 42)

    _jambes(t, fourrure, fourrure_c, (70, 44, 30))
    # torse large et muscle
    t.rect(6, 12, 10, 9, peau)
    t.rect(6, 12, 3, 9, peau_s)
    t.rect(13, 12, 3, 9, peau_c)
    t.px(10, 15, peau_s)
    t.px(11, 15, peau_s)
    t.rect(6, 19, 10, 2, fourrure)     # pagne
    t.rect(6, 11, 10, 2, fourrure_c)   # fourrure d'epaule
    # tete
    t.ellipse(11, 8, 4, 4.2, peau)
    t.rect(7, 6, 2, 4, cheveux)        # meches sous le casque
    t.rect(14, 6, 2, 4, cheveux)
    t.px(12, 9, (46, 26, 18))          # yeux
    t.px(14, 9, (46, 26, 18))
    t.px(13, 10, peau_s)
    t.rect(8, 11, 7, 2, cheveux)       # barbe
    t.triangle((8, 12), (15, 12), (11, 16), cheveux)
    t.triangle((9, 13), (14, 13), (11, 15), cheveux_c)
    # casque a cornes
    t.rect(7, 4, 9, 3, casque)
    t.ellipse(11, 4.5, 4.8, 2.2, casque)
    t.rect(7, 6, 9, 1, (232, 208, 140))
    t.triangle((7, 5), (8, 2), (4, 0), corne)
    t.triangle((15, 5), (14, 2), (18, 0), corne)
    # bras
    t.rect(16, 13, 3, 3, peau_c)
    t.rect(3, 13, 3, 3, peau_s)
    # hache immense
    t.rect(18, 4, 1, 19, bois)
    t.rect(19, 4, 1, 19, (78, 50, 30))
    t.triangle((13, 4), (20, 0), (20, 10), acier)
    t.triangle((15, 5), (19, 2), (19, 8), acier_s)
    t.triangle((20, 1), (22, 5), (20, 9), acier)
    t.contour(_CONTOUR)
    return t.surface()


def _chevalier():
    t = Toile(L_SPR, H_SPR)
    acier = (176, 190, 214)
    acier_c = (224, 234, 250)
    acier_s = (106, 122, 152)
    bleu = (60, 110, 200)
    bleu_c = (108, 168, 255)
    plume = (236, 90, 110)
    or_ = (248, 206, 110)
    visiere = (24, 30, 48)

    _jambes(t, acier_s, acier, (58, 68, 90))
    # cuirasse
    t.rect(6, 12, 10, 9, acier)
    t.rect(6, 12, 3, 9, acier_s)
    t.rect(13, 12, 2, 9, acier_c)
    t.rect(6, 11, 10, 2, acier_c)      # spallieres
    t.triangle((9, 13), (13, 13), (11, 19), bleu)
    t.triangle((9, 13), (12, 13), (11, 17), bleu_c)
    t.rect(6, 19, 10, 2, or_)
    # heaume
    t.ellipse(11, 7, 4.2, 4.6, acier)
    t.ellipse(10, 6, 3.4, 3.4, acier_c)
    t.rect(11, 6, 5, 4, acier)
    t.rect(12, 7, 4, 2, visiere)       # fente de visiere
    t.px(13, 7, (120, 200, 255))
    t.px(15, 7, (120, 200, 255))
    t.rect(8, 2, 6, 2, plume)          # plumet
    t.ellipse(10, 2, 3, 2, plume)
    t.ellipse(8, 1, 2, 1.6, (255, 138, 152))
    # bras + epee
    t.rect(16, 13, 3, 2, acier_c)
    t.rect(19, 4, 2, 9, acier_c)       # lame
    t.rect(20, 4, 1, 9, acier_s)
    t.triangle((19, 4), (21, 4), (20, 1), acier_c)
    t.rect(17, 13, 6, 1, or_)          # garde
    t.rect(19, 14, 2, 3, (92, 62, 40))  # poignee
    t.px(19, 17, or_)
    t.px(20, 17, or_)
    # bouclier
    t.rect(3, 12, 5, 6, bleu)
    t.triangle((3, 18), (8, 18), (5, 22), bleu)
    t.rect(3, 12, 5, 1, acier_c)
    t.rect(5, 13, 1, 7, or_)
    t.rect(3, 15, 5, 1, or_)
    t.contour(_CONTOUR)
    return t.surface()


def _mage():
    t = Toile(L_SPR, H_SPR)
    robe = (56, 72, 168)
    robe_c = (86, 112, 224)
    robe_s = (34, 44, 112)
    chapeau = (44, 56, 140)
    chapeau_c = (72, 92, 200)
    peau = (226, 186, 152)
    barbe = (226, 232, 248)
    barbe_s = (170, 182, 212)
    bois = (118, 78, 46)
    orbe = (150, 238, 255)
    or_ = (250, 214, 120)

    # robe evasee
    t.triangle((5, 26), (17, 26), (11, 11), robe)
    t.triangle((6, 26), (11, 26), (11, 12), robe_s)
    t.rect(5, 25, 12, 2, robe_s)
    t.rect(8, 12, 6, 6, robe_c)
    t.rect(7, 17, 8, 1, or_)
    t.rect(6, 25, 4, 2, (58, 40, 30))
    t.rect(12, 25, 4, 2, (58, 40, 30))
    # tete
    t.ellipse(11, 8, 3.6, 3.8, peau)
    t.px(12, 8, (46, 40, 70))          # yeux
    t.px(14, 8, (46, 40, 70))
    t.rect(8, 10, 7, 2, barbe)         # barbe
    t.triangle((8, 11), (15, 11), (11, 16), barbe)
    t.triangle((9, 12), (14, 12), (11, 15), barbe_s)
    # chapeau pointu
    t.rect(6, 4, 10, 2, chapeau)
    t.ellipse(11, 5, 6, 1.6, chapeau_c)
    t.triangle((7, 5), (15, 5), (15, -4), chapeau)
    t.triangle((9, 4), (14, 4), (14, -2), chapeau_c)
    t.px(14, 0, or_)
    t.px(13, 1, or_)
    # bras + baton
    t.rect(15, 13, 3, 2, robe_c)
    t.rect(18, 6, 1, 19, bois)
    t.rect(19, 6, 1, 19, (92, 60, 36))
    t.ellipse(18.5, 4, 2.8, 2.8, orbe)
    t.ellipse(18, 3.4, 1.3, 1.3, (255, 255, 255))
    t.contour(_CONTOUR)
    return t.surface()


_FABRIQUES = {
    "Assassin": _assassin,
    "Barbare": _barbare,
    "Chevalier": _chevalier,
    "Mage": _mage,
}

_cache_sprites = {}


def sprite(nom_classe, echelle=6, vers_gauche=False):
    """Retourne le sprite d'une classe, mis en cache."""
    cle = (nom_classe, echelle, vers_gauche)
    if cle in _cache_sprites:
        return _cache_sprites[cle]
    base = _FABRIQUES[nom_classe]()
    s = pygame.transform.scale(
        base, (base.get_width() * echelle, base.get_height() * echelle))
    if vers_gauche:
        s = pygame.transform.flip(s, True, False)
    _cache_sprites[cle] = s
    return s


def silhouette(surface, couleur):
    """Copie coloree uniforme d'un sprite (pour les lueurs et le camouflage)."""
    s = surface.copy()
    teinte = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    teinte.fill(couleur)
    s.blit(teinte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


_cache_silhouettes = {}


def silhouette_classe(nom_classe, echelle, vers_gauche, couleur):
    """Silhouette d'un sprite de classe, mise en cache (appelee a chaque image)."""
    cle = (nom_classe, echelle, vers_gauche, tuple(couleur))
    s = _cache_silhouettes.get(cle)
    if s is None:
        s = silhouette(sprite(nom_classe, echelle, vers_gauche), couleur)
        if len(_cache_silhouettes) < 120:
            _cache_silhouettes[cle] = s
    s.set_alpha(None)
    return s


# ============================================================ icones vectorielles
def _poly(s, pts, c):
    pygame.draw.polygon(s, c, pts)


def icone(nom, taille=28, couleur=theme.BLANC):
    """Dessine une petite icone de competence (aucun emoji, tout est vectoriel)."""
    s = pygame.Surface((taille, taille), pygame.SRCALPHA)
    u = taille / 28.0
    c = couleur
    sombre = (max(c[0] - 70, 0), max(c[1] - 70, 0), max(c[2] - 70, 0))

    def U(v):
        return v * u

    if nom == "lame":
        _poly(s, [(U(20), U(3)), (U(24), U(7)), (U(11), U(21)), (U(8), U(18))], c)
        pygame.draw.line(s, sombre, (U(9), U(19)), (U(21), U(6)), max(1, int(U(1))))
        _poly(s, [(U(4), U(24)), (U(9), U(19)), (U(11), U(21)), (U(6), U(26))], sombre)
    elif nom == "double":
        for dx in (-4, 4):
            _poly(s, [(U(16 + dx), U(4)), (U(20 + dx), U(8)), (U(10 + dx), U(22)),
                      (U(7 + dx), U(19))], c if dx > 0 else sombre)
    elif nom == "poison":
        _poly(s, [(U(14), U(4)), (U(22), U(17)), (U(6), U(17))], c)
        pygame.draw.circle(s, c, (U(14), U(18)), U(6))
        pygame.draw.circle(s, sombre, (U(12), U(17)), U(1.8))
        pygame.draw.circle(s, sombre, (U(16), U(20)), U(1.4))
    elif nom == "ombre":
        pygame.draw.ellipse(s, c, (U(3), U(6), U(22), U(16)), max(1, int(U(2))))
        pygame.draw.circle(s, c, (U(14), U(14)), U(4))
        pygame.draw.circle(s, sombre, (U(14), U(14)), U(2))
    elif nom == "soin":
        pygame.draw.rect(s, c, (U(11), U(4), U(6), U(20)), border_radius=int(U(2)))
        pygame.draw.rect(s, c, (U(4), U(11), U(20), U(6)), border_radius=int(U(2)))
    elif nom == "hache":
        pygame.draw.line(s, sombre, (U(16), U(4)), (U(11), U(25)), max(2, int(U(2.4))))
        _poly(s, [(U(9), U(4)), (U(22), U(2)), (U(22), U(13)), (U(11), U(11))], c)
    elif nom == "choc":
        for r, a in ((10, 255), (6, 190), (3, 130)):
            col = (c[0], c[1], c[2], a)
            pygame.draw.circle(s, col, (U(14), U(19)), U(r), max(1, int(U(2))))
        pygame.draw.line(s, c, (U(14), U(19)), (U(14), U(5)), max(2, int(U(2))))
    elif nom == "crane":
        pygame.draw.circle(s, c, (U(14), U(12)), U(9))
        pygame.draw.rect(s, c, (U(10), U(18), U(8), U(6)), border_radius=int(U(2)))
        pygame.draw.circle(s, sombre, (U(10.5), U(12)), U(2.6))
        pygame.draw.circle(s, sombre, (U(17.5), U(12)), U(2.6))
        pygame.draw.rect(s, sombre, (U(13), U(19), U(2), U(5)))
    elif nom == "rage":
        _poly(s, [(U(14), U(2)), (U(21), U(12)), (U(17), U(11)), (U(19), U(22)),
                  (U(14), U(26)), (U(9), U(22)), (U(11), U(11)), (U(7), U(12))], c)
        _poly(s, [(U(14), U(10)), (U(17), U(18)), (U(14), U(23)), (U(11), U(18))], sombre)
    elif nom == "bouclier":
        _poly(s, [(U(14), U(3)), (U(24), U(7)), (U(24), U(15)), (U(14), U(25)),
                  (U(4), U(15)), (U(4), U(7))], c)
        _poly(s, [(U(14), U(7)), (U(20), U(9)), (U(20), U(15)), (U(14), U(21)),
                  (U(8), U(15)), (U(8), U(9))], sombre)
    elif nom == "epee_bouclier":
        _poly(s, [(U(10), U(4)), (U(18), U(7)), (U(18), U(14)), (U(10), U(22)),
                  (U(2), U(14)), (U(2), U(7))], sombre)
        _poly(s, [(U(23), U(2)), (U(26), U(5)), (U(15), U(18)), (U(12), U(15))], c)
    elif nom == "charge":
        _poly(s, [(U(3), U(14)), (U(16), U(4)), (U(16), U(10)), (U(26), U(10)),
                  (U(26), U(18)), (U(16), U(18)), (U(16), U(24))], c)
    elif nom == "armure":
        _poly(s, [(U(14), U(3)), (U(24), U(7)), (U(24), U(15)), (U(14), U(25)),
                  (U(4), U(15)), (U(4), U(7))], c)
        pygame.draw.rect(s, sombre, (U(12), U(8), U(4), U(12)))
        pygame.draw.rect(s, sombre, (U(8), U(12), U(12), U(4)))
    elif nom == "feu":
        _poly(s, [(U(14), U(2)), (U(21), U(12)), (U(21), U(19)), (U(14), U(26)),
                  (U(7), U(19)), (U(7), U(12))], c)
        _poly(s, [(U(14), U(11)), (U(18), U(18)), (U(14), U(24)), (U(10), U(18))], sombre)
    elif nom == "glace":
        for ang in range(0, 180, 60):
            a = math.radians(ang)
            dx, dy = math.cos(a) * U(11), math.sin(a) * U(11)
            pygame.draw.line(s, c, (U(14) - dx, U(14) - dy), (U(14) + dx, U(14) + dy),
                             max(2, int(U(2.2))))
        pygame.draw.circle(s, sombre, (U(14), U(14)), U(3))
    elif nom == "foudre":
        _poly(s, [(U(16), U(2)), (U(8), U(15)), (U(13), U(15)), (U(10), U(26)),
                  (U(20), U(11)), (U(15), U(11))], c)
    elif nom == "bulle":
        pygame.draw.circle(s, c, (U(14), U(14)), U(11), max(2, int(U(2.4))))
        pygame.draw.circle(s, c, (U(10), U(10)), U(2.4))
        pygame.draw.arc(s, c, (U(5), U(5), U(18), U(18)), 0.7, 2.0, max(1, int(U(2))))
    elif nom == "drain":
        pygame.draw.arc(s, c, (U(3), U(3), U(22), U(22)), 0.4, 4.6, max(2, int(U(2.6))))
        _poly(s, [(U(22), U(2)), (U(26), U(10)), (U(18), U(9))], c)
        pygame.draw.circle(s, c, (U(14), U(14)), U(3))
    elif nom == "eclair_petit":
        _poly(s, [(U(16), U(4)), (U(9), U(15)), (U(13), U(15)), (U(11), U(24)),
                  (U(19), U(12)), (U(15), U(12))], c)
    elif nom == "coeur":
        pygame.draw.circle(s, c, (U(10), U(11)), U(6))
        pygame.draw.circle(s, c, (U(18), U(11)), U(6))
        _poly(s, [(U(4), U(13)), (U(24), U(13)), (U(14), U(25))], c)
    elif nom == "goutte":
        pygame.draw.circle(s, c, (U(14), U(17)), U(7))
        _poly(s, [(U(14), U(3)), (U(21), U(17)), (U(7), U(17))], c)
    elif nom == "etoile":
        pts = []
        for k in range(10):
            r = U(12) if k % 2 == 0 else U(5)
            a = math.radians(-90 + k * 36)
            pts.append((U(14) + math.cos(a) * r, U(14) + math.sin(a) * r))
        _poly(s, pts, c)
    else:
        pygame.draw.circle(s, c, (U(14), U(14)), U(9), max(2, int(U(2))))
    return s


_cache_icones = {}


def icone_cache(nom, taille, couleur):
    cle = (nom, taille, couleur)
    if cle not in _cache_icones:
        _cache_icones[cle] = icone(nom, taille, couleur)
    return _cache_icones[cle]
