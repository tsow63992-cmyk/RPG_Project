"""Decor de bataille genere proceduralement : nuit, lune, foret, riviere.

Le fond statique est calcule une seule fois puis anime par-dessus
(scintillement des etoiles, lucioles, petales, reflets sur l'eau).
"""

import math
import random

import pygame

from . import theme

LARGEUR = theme.LARGEUR
HAUTEUR = theme.HAUTEUR
SOL = 430          # ligne de sol : les pieds des combattants reposent ici


def _degrade_vertical(surface, haut, bas, y0, y1):
    """Degrade lineaire, dessine en bandes de 2px (rapide et sans artefact)."""
    n = max(int(y1 - y0), 1)
    for i in range(0, n, 2):
        t = i / n
        c = (int(haut[0] + (bas[0] - haut[0]) * t),
             int(haut[1] + (bas[1] - haut[1]) * t),
             int(haut[2] + (bas[2] - haut[2]) * t))
        surface.fill(c, (0, int(y0 + i), surface.get_width(), 2))


_CACHE_HALOS = {}


def _halo(rayon, couleur, force=90):
    """Disque lumineux doux (utilise partout : lune, orbes, impacts).

    Le resultat est mis en cache : ces surfaces sont couteuses a construire
    et servent a chaque image.
    """
    cle = (int(rayon), tuple(couleur[:3]), int(force))
    cache = _CACHE_HALOS.get(cle)
    if cache is not None:
        cache.set_alpha(None)
        return cache
    s = _halo_brut(rayon, couleur, force)
    if len(_CACHE_HALOS) < 260:
        _CACHE_HALOS[cle] = s
    return s


def _halo_brut(rayon, couleur, force=90):
    # Construit un degrade radial pixel par pixel sur une petite surface,
    # puis l'agrandit : rendu identique et sans anneaux visibles.
    n = 48
    petit = pygame.Surface((n, n), pygame.SRCALPHA)
    c = (couleur[0], couleur[1], couleur[2])
    for j in range(n):
        for i in range(n):
            dx = (i + 0.5) / n * 2 - 1
            dy = (j + 0.5) / n * 2 - 1
            d = math.sqrt(dx * dx + dy * dy)
            if d >= 1.0:
                continue
            a = int(force * (1 - d) ** 2.0)
            if a > 0:
                petit.fill(c + (a,), (i, j, 1, 1))
    taille = max(int(rayon) * 2, 2)
    return pygame.transform.smoothscale(petit, (taille, taille))


halo = _halo


def _vignette(surface, marge=170, force=96):
    """Assombrit les quatre bords en douceur (pas d'anneaux concentriques)."""
    w, h = surface.get_size()
    v = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(0, marge, 2):
        a = int(force * (1 - i / marge) ** 1.8)
        if a <= 0:
            continue
        col = (0, 0, 8, a)
        v.fill(col, (0, i, w, 2))
        v.fill(col, (0, h - i - 2, w, 2))
        v.fill(col, (i, 0, 2, h))
        v.fill(col, (w - i - 2, 0, 2, h))
    surface.blit(v, (0, 0))


class Decor:
    def __init__(self, graine=7):
        self.rng = random.Random(graine)
        self.etoiles = []
        self.lucioles = []
        self.petales = []
        self.reflets = []
        self._construire_statique()
        self._peupler()

    # ------------------------------------------------------------- statique
    def _construire_statique(self):
        rng = self.rng
        s = pygame.Surface((LARGEUR, HAUTEUR))
        # --- ciel
        _degrade_vertical(s, (9, 8, 28), (46, 28, 74), 0, 200)
        _degrade_vertical(s, (46, 28, 74), (96, 56, 102), 200, 300)

        # --- nebuleuse diffuse
        for _ in range(16):
            x = rng.randint(0, LARGEUR)
            y = rng.randint(0, 240)
            r = rng.randint(90, 220)
            col = rng.choice([(96, 60, 160), (60, 70, 170), (150, 70, 140)])
            s.blit(_halo(r, col, 16), (x - r, y - r))

        # --- lune + halo
        lx, ly, lr = 762, 132, 40
        s.blit(_halo(190, (210, 220, 255), 46), (lx - 190, ly - 190))
        pygame.draw.circle(s, (246, 244, 226), (lx, ly), lr)
        pygame.draw.circle(s, (224, 222, 208), (lx - 9, ly + 8), 7)
        pygame.draw.circle(s, (228, 226, 212), (lx + 12, ly - 11), 5)
        pygame.draw.circle(s, (230, 228, 214), (lx + 6, ly + 16), 4)

        # --- montagnes lointaines (deux plans)
        self._montagnes(s, 318, 128, (38, 30, 74), 3)
        self._montagnes(s, 344, 86, (26, 21, 54), 11)

        # --- brume au pied des montagnes
        brume = pygame.Surface((LARGEUR, 90), pygame.SRCALPHA)
        for i in range(90):
            a = int(46 * math.sin(math.pi * i / 90))
            brume.fill((150, 170, 220, a), (0, i, LARGEUR, 1))
        s.blit(brume, (0, 296))

        # --- ligne de foret
        self._foret(s, 372, (18, 16, 42), 30, 26, 58)
        self._foret(s, 396, (12, 12, 32), 40, 34, 74)

        # --- riviere lumineuse
        _degrade_vertical(s, (30, 52, 96), (44, 92, 140), 398, 424)
        for _ in range(70):
            x = rng.randint(0, LARGEUR)
            y = rng.randint(400, 422)
            w = rng.randint(8, 46)
            a = rng.randint(30, 90)
            bande = pygame.Surface((w, 2), pygame.SRCALPHA)
            bande.fill((160, 230, 255, a))
            s.blit(bande, (x, y))

        # --- berge et sol
        _degrade_vertical(s, (30, 54, 46), (18, 30, 30), 422, 520)
        _degrade_vertical(s, (18, 30, 30), (10, 14, 22), 520, HAUTEUR)
        # touffes d'herbe
        for _ in range(900):
            x = rng.randint(0, LARGEUR)
            y = rng.randint(424, 560)
            prof = (y - 424) / 136
            h = rng.randint(3, 8)
            c = (int(52 + 40 * (1 - prof) + rng.randint(-10, 10)),
                 int(96 + 46 * (1 - prof) + rng.randint(-10, 10)),
                 int(66 + 20 * (1 - prof)))
            c = tuple(max(0, min(255, v)) for v in c)
            pygame.draw.line(s, c, (x, y), (x + rng.randint(-1, 1), y - h), 1)
        # petites fleurs
        for _ in range(60):
            x = rng.randint(0, LARGEUR)
            y = rng.randint(430, 545)
            pygame.draw.circle(s, rng.choice([(236, 214, 120), (238, 160, 200),
                                              (200, 226, 250)]), (x, y), 2)

        # --- grands cerisiers qui encadrent la scene
        self._cerisier(s, 118, SOL + 24, 1.25, (58, 34, 46))
        self._cerisier(s, 1176, SOL + 18, 1.05, (52, 30, 42))
        self._arbre_sombre(s, 330, 404, 0.7)
        self._arbre_sombre(s, 980, 400, 0.62)

        # --- vignette (degrades sur les quatre bords, sans anneaux)
        _vignette(s, 170, 96)
        self.statique = s

    def _montagnes(self, s, base, hauteur, couleur, seed):
        rng = random.Random(seed)
        sommets = []
        pts = [(-40, base + 40)]
        x = -40
        while x < LARGEUR + 60:
            largeur = rng.randint(150, 280)
            h = rng.randint(int(hauteur * 0.55), hauteur)
            sx = x + largeur // 2
            sy = base - h
            # flanc gauche legerement brise
            pts.append((sx - largeur * 0.28, sy + h * 0.42))
            pts.append((sx, sy))
            pts.append((sx + largeur * 0.30, sy + h * 0.38))
            sommets.append((sx, sy, largeur))
            x += largeur
        pts.append((LARGEUR + 60, base + 40))
        pts.append((LARGEUR + 60, base + 160))
        pts.append((-40, base + 160))
        pygame.draw.polygon(s, couleur, pts)
        # cimes enneigees eclairees par la lune
        clair = tuple(min(255, c + 52) for c in couleur)
        for sx, sy, largeur in sommets:
            w = largeur * 0.13
            pygame.draw.polygon(s, clair, [
                (sx, sy), (sx + w, sy + w * 1.5), (sx + w * 0.45, sy + w * 1.1),
                (sx + w * 0.15, sy + w * 1.9), (sx - w * 0.3, sy + w * 1.0),
                (sx - w * 0.7, sy + w * 1.6), (sx - w, sy + w * 1.5)])

    def _foret(self, s, base, couleur, nb, hmin, hmax):
        rng = random.Random(base)
        pas = LARGEUR / nb
        for i in range(nb + 1):
            x = i * pas + rng.randint(-14, 14)
            h = rng.randint(hmin, hmax)
            w = h * 0.52
            pygame.draw.polygon(s, couleur, [(x, base - h), (x - w, base + 8),
                                             (x + w, base + 8)])
            pygame.draw.polygon(s, couleur, [(x, base - h * 0.6), (x - w * 1.25, base + 14),
                                             (x + w * 1.25, base + 14)])
        pygame.draw.rect(s, couleur, (0, base + 6, LARGEUR, 14))

    def _arbre_sombre(self, s, x, base, ech):
        c = (14, 14, 34)
        pygame.draw.rect(s, c, (x - 4 * ech, base - 60 * ech, 8 * ech, 62 * ech))
        for dx, dy, r in ((0, -70, 30), (-22, -54, 22), (24, -56, 24), (-12, -84, 20)):
            pygame.draw.circle(s, c, (int(x + dx * ech), int(base + dy * ech)),
                               int(r * ech))

    def _cerisier(self, s, x, base, ech, tronc):
        rng = random.Random(int(x))
        # tronc
        pygame.draw.polygon(s, tronc, [
            (x - 13 * ech, base), (x + 13 * ech, base),
            (x + 7 * ech, base - 150 * ech), (x - 8 * ech, base - 150 * ech)])
        for ang, lg in ((-0.9, 80), (0.85, 92), (-0.35, 64)):
            x2 = x + math.sin(ang) * lg * ech
            y2 = base - 150 * ech - math.cos(ang) * lg * ech * 0.6
            pygame.draw.line(s, tronc, (x, base - 140 * ech), (x2, y2), int(9 * ech))
        # feuillage : amas de cercles roses assombris par la nuit
        centres = [(0, -210), (-58, -178), (62, -184), (-104, -140), (108, -146),
                   (-26, -244), (34, -238), (-150, -108), (152, -112)]
        for cx, cy in centres:
            for _ in range(16):
                rr = rng.randint(16, 34)
                px = x + (cx + rng.randint(-24, 24)) * ech
                py = base + (cy + rng.randint(-18, 18)) * ech
                t = rng.random()
                col = (int(96 + 70 * t), int(46 + 34 * t), int(86 + 50 * t))
                pygame.draw.circle(s, col, (int(px), int(py)), int(rr * ech))
        # quelques petales eclaires par la lune
        for cx, cy in centres:
            for _ in range(7):
                px = x + (cx + rng.randint(-26, 26)) * ech
                py = base + (cy + rng.randint(-20, 20)) * ech
                pygame.draw.circle(s, (214, 148, 190), (int(px), int(py)),
                                   int(rng.randint(5, 10) * ech))

    # -------------------------------------------------------------- animation
    def _peupler(self):
        rng = self.rng
        for _ in range(210):
            self.etoiles.append([
                rng.randint(0, LARGEUR), rng.randint(0, 320),
                rng.uniform(0.8, 2.2), rng.uniform(0, 6.28), rng.uniform(1.0, 3.0)])
        for _ in range(34):
            self.lucioles.append([
                rng.uniform(0, LARGEUR), rng.uniform(300, 520),
                rng.uniform(0, 6.28), rng.uniform(0.3, 0.9),
                rng.uniform(14, 42), rng.choice([(180, 255, 170), (255, 236, 150)])])
        for _ in range(26):
            self.petales.append([
                rng.uniform(0, LARGEUR), rng.uniform(-200, 460),
                rng.uniform(10, 26), rng.uniform(0, 6.28), rng.uniform(4, 8)])
        self._halo_luciole = {}

    def _luciole_halo(self, couleur):
        if couleur not in self._halo_luciole:
            self._halo_luciole[couleur] = _halo(13, couleur, 120)
        return self._halo_luciole[couleur]

    def dessiner(self, ecran, t, dt):
        ecran.blit(self.statique, (0, 0))

        # etoiles scintillantes
        for e in self.etoiles:
            a = 0.5 + 0.5 * math.sin(t * e[4] + e[3])
            c = int(150 + 105 * a)
            r = e[2]
            if r < 1.2:
                ecran.fill((c, c, min(255, c + 16)), (int(e[0]), int(e[1]), 1, 1))
            else:
                pygame.draw.circle(ecran, (c, c, min(255, c + 16)),
                                   (int(e[0]), int(e[1])), int(r))

        # reflets mouvants sur la riviere
        for i in range(24):
            x = (i * 73 + t * 22) % (LARGEUR + 80) - 40
            y = 402 + (i % 6) * 3
            w = 26 + 14 * math.sin(t * 1.6 + i)
            a = int(60 + 50 * math.sin(t * 2.1 + i * 0.7))
            if a > 0:
                bande = pygame.Surface((int(max(w, 2)), 2), pygame.SRCALPHA)
                bande.fill((170, 235, 255, a))
                ecran.blit(bande, (int(x), int(y)))

        # petales de cerisier
        for p in self.petales:
            p[1] += (12 + p[4]) * dt
            p[0] += math.sin(t * 1.4 + p[3]) * 22 * dt
            if p[1] > 470:
                p[1] = -20
                p[0] = random.uniform(0, LARGEUR)
            ang = t * 2 + p[3]
            w = max(2, int(p[4] * abs(math.cos(ang))))
            pygame.draw.ellipse(ecran, (226, 158, 198),
                                (int(p[0]), int(p[1]), w, int(p[4] * 0.8)))

        # lucioles
        for f in self.lucioles:
            f[0] += math.cos(t * f[3] + f[2]) * 16 * dt
            f[1] += math.sin(t * f[3] * 1.3 + f[2]) * 11 * dt
            pulsation = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 3 + f[2]))
            h = self._luciole_halo(f[5])
            h.set_alpha(int(190 * pulsation))
            ecran.blit(h, (int(f[0]) - 13, int(f[1]) - 13))
            pygame.draw.circle(ecran, f[5], (int(f[0]), int(f[1])), 2)


# ------------------------------------------------------------ fond des menus
class FondStellaire:
    """Fond sobre et anime pour les ecrans de menu."""

    def __init__(self, graine=3):
        rng = random.Random(graine)
        s = pygame.Surface((LARGEUR, HAUTEUR))
        _degrade_vertical(s, (10, 9, 26), (26, 20, 52), 0, HAUTEUR // 2)
        _degrade_vertical(s, (26, 20, 52), (14, 12, 30), HAUTEUR // 2, HAUTEUR)
        for _ in range(14):
            x, y = rng.randint(0, LARGEUR), rng.randint(0, HAUTEUR)
            r = rng.randint(140, 300)
            col = rng.choice([(92, 58, 168), (48, 66, 168), (150, 62, 132)])
            s.blit(_halo(r, col, 20), (x - r, y - r))
        self.statique = s
        self.etoiles = [[rng.randint(0, LARGEUR), rng.randint(0, HAUTEUR),
                         rng.uniform(0.7, 2.0), rng.uniform(0, 6.28),
                         rng.uniform(0.8, 2.6)] for _ in range(240)]
        self.poussiere = [[rng.uniform(0, LARGEUR), rng.uniform(0, HAUTEUR),
                           rng.uniform(6, 22), rng.uniform(0, 6.28)]
                          for _ in range(40)]

    def dessiner(self, ecran, t, dt):
        ecran.blit(self.statique, (0, 0))
        for e in self.etoiles:
            a = 0.5 + 0.5 * math.sin(t * e[4] + e[3])
            c = int(130 + 120 * a)
            if e[2] < 1.2:
                ecran.fill((c, c, min(255, c + 20)), (int(e[0]), int(e[1]), 1, 1))
            else:
                pygame.draw.circle(ecran, (c, c, min(255, c + 20)),
                                   (int(e[0]), int(e[1])), int(e[2]))
        for p in self.poussiere:
            p[1] -= p[2] * dt
            if p[1] < -10:
                p[1] = HAUTEUR + 10
                p[0] = random.uniform(0, LARGEUR)
            k = 0.5 + 0.5 * math.sin(t * 2 + p[3])
            c = (int(52 + 76 * k), int(60 + 86 * k), int(96 + 130 * k))
            pygame.draw.circle(ecran, c, (int(p[0]), int(p[1])), 2)
