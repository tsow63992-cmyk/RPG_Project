"""Effets visuels : particules, nombres flottants, ondes de choc, tremblement.

Chaque competence du jeu declenche un effet different (feu, glace, foudre,
poison, soin, bouclier, entaille...).
"""

import math
import random

import pygame

from . import theme
from .decor import halo


# ------------------------------------------------------------------ particule
class Particule:
    __slots__ = ("x", "y", "vx", "vy", "grav", "vie", "vie_max", "taille",
                 "couleur", "forme", "lueur", "rot", "vrot", "frein")

    def __init__(self, x, y, vx, vy, vie, taille, couleur,
                 grav=380.0, forme="rond", lueur=True, frein=0.99):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.grav = grav
        self.vie = self.vie_max = vie
        self.taille = taille
        self.couleur = couleur
        self.forme = forme
        self.lueur = lueur
        self.frein = frein
        self.rot = random.uniform(0, 6.28)
        self.vrot = random.uniform(-8, 8)

    def avancer(self, dt):
        self.vie -= dt
        self.vx *= self.frein
        self.vy = self.vy * self.frein + self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.vrot * dt
        return self.vie > 0


class Systeme:
    """Conteneur unique pour toutes les particules et textes flottants."""

    def __init__(self):
        self.particules = []
        self.textes = []
        self.ondes = []
        self.eclairs = []
        self.entailles = []
        self._halos = {}

    # ------------------------------------------------------------- creation
    def ajouter(self, p):
        self.particules.append(p)

    def gerbe(self, x, y, couleur, nb=26, vitesse=260, vie=0.7, taille=5,
              grav=420, forme="rond", etalement=6.283, angle=0.0):
        for _ in range(nb):
            a = angle + random.uniform(-etalement / 2, etalement / 2)
            v = vitesse * random.uniform(0.35, 1.0)
            self.particules.append(Particule(
                x, y, math.cos(a) * v, math.sin(a) * v,
                vie * random.uniform(0.6, 1.25),
                taille * random.uniform(0.6, 1.4), couleur, grav, forme))

    def texte(self, x, y, txt, couleur, taille=44, monte=90, vie=1.25,
              contour=(8, 6, 16)):
        self.textes.append({"x": x, "y": y, "t": txt, "c": couleur, "s": taille,
                            "monte": monte, "vie": vie, "vie_max": vie,
                            "contour": contour, "dx": random.uniform(-14, 14)})

    def onde(self, x, y, couleur, rayon=170, vie=0.55, epaisseur=6):
        self.ondes.append({"x": x, "y": y, "c": couleur, "r": rayon,
                           "vie": vie, "vie_max": vie, "e": epaisseur})

    def eclair(self, x0, y0, x1, y1, couleur, vie=0.35, segments=13, ecart=34):
        pts = []
        for i in range(segments + 1):
            t = i / segments
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if 0 < i < segments:
                x += random.uniform(-ecart, ecart)
                y += random.uniform(-ecart * 0.35, ecart * 0.35)
            pts.append((x, y))
        self.eclairs.append({"pts": pts, "c": couleur, "vie": vie, "vie_max": vie})

    def entaille(self, x, y, couleur, sens=1, vie=0.3, taille=150):
        self.entailles.append({"x": x, "y": y, "c": couleur, "sens": sens,
                               "vie": vie, "vie_max": vie, "s": taille})

    # ------------------------------------------------------------ simulation
    def avancer(self, dt):
        self.particules = [p for p in self.particules if p.avancer(dt)]
        for liste in (self.textes, self.ondes, self.eclairs, self.entailles):
            for e in liste:
                e["vie"] -= dt
            liste[:] = [e for e in liste if e["vie"] > 0]

    def vide(self):
        return not (self.particules or self.textes or self.ondes
                    or self.eclairs or self.entailles)

    # --------------------------------------------------------------- rendu
    def _halo(self, r, c):
        cle = (r, c)
        if cle not in self._halos:
            self._halos[cle] = halo(r, c, 150)
        return self._halos[cle]

    def dessiner(self, ecran):
        # ondes de choc
        for o in self.ondes:
            t = 1 - o["vie"] / o["vie_max"]
            r = int(o["r"] * (0.2 + 0.8 * t))
            a = int(210 * (1 - t) ** 1.5)
            if r > 1 and a > 0:
                s = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(s, (o["c"][0], o["c"][1], o["c"][2], a),
                                   (r + 4, r + 4), r, max(1, int(o["e"] * (1 - t) + 1)))
                ecran.blit(s, (o["x"] - r - 4, o["y"] - r - 4))

        # entailles (arcs d'epee)
        for e in self.entailles:
            t = 1 - e["vie"] / e["vie_max"]
            a = int(255 * (1 - t) ** 1.2)
            taille = e["s"]
            s = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
            for k in range(3):
                dec = k * 9
                rect = (dec, dec, taille * 2 - dec * 2, taille * 2 - dec * 2)
                col = (e["c"][0], e["c"][1], e["c"][2], max(a - k * 60, 0))
                debut = -0.9 + t * 1.5
                pygame.draw.arc(s, col, rect, debut, debut + 1.5, max(2, 9 - k * 3))
            if e["sens"] < 0:
                s = pygame.transform.flip(s, True, False)
            ecran.blit(s, (e["x"] - taille, e["y"] - taille))

        # eclairs (dessines sur une surface de la taille du trace seulement)
        for e in self.eclairs:
            t = 1 - e["vie"] / e["vie_max"]
            a = int(255 * (1 - t))
            c = e["c"]
            pts = e["pts"]
            marge = 20
            x0 = min(p[0] for p in pts) - marge
            y0 = min(p[1] for p in pts) - marge
            w = int(max(p[0] for p in pts) - x0 + marge)
            h = int(max(p[1] for p in pts) - y0 + marge)
            s = pygame.Surface((max(w, 2), max(h, 2)), pygame.SRCALPHA)
            locaux = [(p[0] - x0, p[1] - y0) for p in pts]
            pygame.draw.lines(s, (c[0], c[1], c[2], max(a // 3, 0)), False, locaux, 16)
            pygame.draw.lines(s, (c[0], c[1], c[2], a), False, locaux, 6)
            pygame.draw.lines(s, (255, 255, 255, a), False, locaux, 2)
            ecran.blit(s, (int(x0), int(y0)))

        # particules
        for p in self.particules:
            t = max(p.vie / p.vie_max, 0)
            taille = max(1, int(p.taille * (0.35 + 0.65 * t)))
            a = int(255 * min(1.0, t * 1.6))
            c = p.couleur
            if p.lueur and taille >= 3:
                h = self._halo(taille * 3, c)
                h.set_alpha(int(a * 0.5))
                ecran.blit(h, (int(p.x - taille * 3), int(p.y - taille * 3)))
            col = (c[0], c[1], c[2], a)
            if p.forme == "carre":
                s = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
                s.fill(col)
                s = pygame.transform.rotate(s, math.degrees(p.rot))
                ecran.blit(s, (int(p.x - s.get_width() / 2),
                               int(p.y - s.get_height() / 2)))
            elif p.forme == "etincelle":
                dx = math.cos(p.rot) * taille * 3
                dy = math.sin(p.rot) * taille * 3
                s = pygame.Surface((abs(dx) * 2 + 6, abs(dy) * 2 + 6), pygame.SRCALPHA)
                cx, cy = s.get_width() / 2, s.get_height() / 2
                pygame.draw.line(s, col, (cx - dx, cy - dy), (cx + dx, cy + dy),
                                 max(1, taille // 2))
                ecran.blit(s, (int(p.x - cx), int(p.y - cy)))
            else:
                s = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, col, (taille, taille), taille)
                ecran.blit(s, (int(p.x - taille), int(p.y - taille)))

        # nombres flottants
        for e in self.textes:
            t = 1 - e["vie"] / e["vie_max"]
            y = e["y"] - e["monte"] * (1 - (1 - t) ** 2)
            x = e["x"] + e["dx"] * t
            ech = 1.0 + 0.35 * max(0.0, 1 - t * 6)
            a = int(255 * min(1.0, (1 - t) * 3))
            f = theme.police(max(10, int(e["s"] * ech)), True, titre=True)
            img = f.render(e["t"], True, e["c"])
            om = f.render(e["t"], True, e["contour"])
            img.set_alpha(a)
            om.set_alpha(a)
            px, py = int(x - img.get_width() / 2), int(y)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, -2)):
                ecran.blit(om, (px + dx, py + dy))
            ecran.blit(img, (px, py))


# --------------------------------------------------------- effets par famille
def jouer(sys_, famille, x, y, sens=1, couleur=None):
    """Declenche l'effet visuel associe a une famille de competence."""
    if famille == "lame":
        sys_.entaille(x, y, (235, 245, 255), sens, 0.28, 130)
        sys_.gerbe(x, y, (220, 236, 255), 18, 300, 0.45, 4, forme="etincelle")
        sys_.gerbe(x, y, (255, 120, 120), 10, 210, 0.5, 4)
    elif famille == "double":
        sys_.entaille(x - 18, y - 16, (220, 200, 255), sens, 0.26, 120)
        sys_.entaille(x + 18, y + 14, (255, 235, 255), -sens, 0.3, 120)
        sys_.gerbe(x, y, (214, 180, 255), 26, 340, 0.5, 4, forme="etincelle")
    elif famille == "poison":
        sys_.onde(x, y, theme.VERT_POISON, 120, 0.5, 5)
        for _ in range(24):
            sys_.ajouter(Particule(
                x + random.uniform(-26, 26), y + random.uniform(-16, 30),
                random.uniform(-30, 30), random.uniform(-90, -30),
                random.uniform(0.7, 1.4), random.uniform(3, 8),
                random.choice([(150, 230, 80), (96, 200, 90), (196, 246, 120)]),
                grav=-40))
    elif famille == "ombre":
        sys_.onde(x, y, (176, 122, 255), 140, 0.55, 6)
        sys_.gerbe(x, y, (150, 90, 230), 30, 170, 1.0, 6, grav=-70)
    elif famille == "soin":
        for _ in range(28):
            sys_.ajouter(Particule(
                x + random.uniform(-40, 40), y + random.uniform(0, 60),
                random.uniform(-16, 16), random.uniform(-130, -60),
                random.uniform(0.8, 1.5), random.uniform(3, 7),
                random.choice([(120, 250, 170), (210, 255, 220), (255, 240, 160)]),
                grav=-20))
        sys_.onde(x, y, theme.VERT, 130, 0.6, 5)
    elif famille == "hache":
        sys_.entaille(x, y, (255, 190, 120), sens, 0.3, 160)
        sys_.gerbe(x, y, (255, 150, 90), 24, 330, 0.55, 6)
        sys_.gerbe(x, y, (200, 40, 50), 14, 250, 0.6, 5)
    elif famille == "choc":
        sys_.onde(x, y + 70, (255, 190, 110), 260, 0.6, 9)
        sys_.gerbe(x, y + 80, (176, 130, 90), 34, 380, 0.8, 7, etalement=2.4,
                   angle=-1.57)
    elif famille == "carnage":
        sys_.onde(x, y, (255, 90, 80), 300, 0.7, 12)
        sys_.entaille(x, y, (255, 120, 100), sens, 0.35, 190)
        sys_.gerbe(x, y, (255, 70, 70), 46, 480, 0.9, 8)
        sys_.gerbe(x, y, (255, 210, 120), 20, 300, 0.7, 6, forme="etincelle")
    elif famille == "rage":
        for _ in range(34):
            sys_.ajouter(Particule(
                x + random.uniform(-36, 36), y + random.uniform(-20, 70),
                random.uniform(-40, 40), random.uniform(-190, -70),
                random.uniform(0.6, 1.2), random.uniform(4, 9),
                random.choice([(255, 110, 50), (255, 190, 70), (210, 40, 40)]),
                grav=-90))
        sys_.onde(x, y, (255, 140, 60), 150, 0.5, 7)
    elif famille == "bouclier":
        sys_.onde(x, y, (150, 210, 255), 150, 0.6, 7)
        sys_.gerbe(x, y, (190, 230, 255), 22, 150, 0.9, 5, grav=-30)
    elif famille == "charge":
        sys_.entaille(x, y, (190, 226, 255), sens, 0.3, 170)
        sys_.gerbe(x, y, (150, 200, 255), 30, 400, 0.6, 6, etalement=2.0,
                   angle=0.0 if sens > 0 else 3.14)
        sys_.onde(x, y, (140, 200, 255), 200, 0.5, 8)
    elif famille == "feu":
        for _ in range(38):
            sys_.ajouter(Particule(
                x + random.uniform(-30, 30), y + random.uniform(-20, 40),
                random.uniform(-90, 90), random.uniform(-160, -30),
                random.uniform(0.5, 1.1), random.uniform(4, 11),
                random.choice([(255, 90, 30), (255, 160, 50), (255, 226, 120)]),
                grav=-110))
        sys_.onde(x, y, (255, 150, 60), 180, 0.5, 8)
    elif famille == "glace":
        sys_.onde(x, y, theme.BLEU_GLACE, 170, 0.55, 6)
        sys_.gerbe(x, y, (180, 240, 255), 30, 300, 0.8, 6, forme="carre", grav=180)
        sys_.gerbe(x, y, (255, 255, 255), 14, 200, 0.7, 4, forme="etincelle")
    elif famille == "foudre":
        sys_.eclair(x + random.uniform(-40, 40), -20, x, y, (255, 240, 130), 0.4)
        sys_.eclair(x + random.uniform(-90, 90), -20, x, y, (170, 220, 255), 0.3, 9, 46)
        sys_.onde(x, y, (255, 240, 140), 280, 0.55, 10)
        sys_.gerbe(x, y, (255, 250, 190), 40, 420, 0.7, 6, forme="etincelle")
    elif famille == "drain":
        for k in range(30):
            a = k / 30 * 6.283
            r = 70
            sys_.ajouter(Particule(
                x + math.cos(a) * r, y + math.sin(a) * r * 0.6,
                -math.cos(a) * 150, -math.sin(a) * 110,
                0.7, random.uniform(3, 6), (168, 130, 255), grav=0))
        sys_.onde(x, y, (168, 130, 255), 120, 0.5, 5)
    elif famille == "magie":
        sys_.onde(x, y, (150, 180, 255), 140, 0.5, 5)
        sys_.gerbe(x, y, (170, 200, 255), 24, 260, 0.6, 5)
    else:
        sys_.gerbe(x, y, couleur or theme.BLANC, 20, 260, 0.6, 5)
