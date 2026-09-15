"""Ecran de victoire : vainqueur mis en scene et resume du duel."""

import math
import random

import pygame

from . import theme, sprites, widgets, decor, fx
from .app import Scene, ease_out, pulse


class EcranVictoire(Scene):
    def __init__(self, app, combattants, gagnant, tours):
        super().__init__(app)
        self.combattants = combattants
        self.gagnant = gagnant
        self.tours = tours
        self.fx = fx.Systeme()
        self.temps = 0.0
        self.confettis = 0.0

    def entrer(self):
        self.temps = 0.0
        v = self.combattants[self.gagnant]
        self.app.eclair(0.4, (255, 230, 170))
        for _ in range(3):
            self.fx.onde(theme.LARGEUR // 2, 300, theme.OR, 420, 1.0, 8)

    def evenement(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.quitter()
            elif e.key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER):
                from .ecran_classes import EcranClasses
                self.app.changer(EcranClasses(self.app))
        elif e.type == pygame.MOUSEBUTTONDOWN:
            from .ecran_classes import EcranClasses
            self.app.changer(EcranClasses(self.app))

    def avancer(self, dt, t):
        self.temps += dt
        self.fx.avancer(dt)
        self.confettis += dt
        if self.confettis > 0.08 and self.temps < 6:
            self.confettis = 0.0
            x = random.uniform(0, theme.LARGEUR)
            self.fx.ajouter(fx.Particule(
                x, -10, random.uniform(-40, 40), random.uniform(20, 90),
                random.uniform(3.0, 5.0), random.uniform(4, 8),
                random.choice([theme.OR, theme.ROSE, theme.CYAN, theme.VERT,
                               (255, 255, 255)]),
                grav=40, forme="carre", lueur=False, frein=0.999))

    def dessiner(self, ecran, t):
        self.app.fond_menu.dessiner(ecran, t, 1 / 60.0)
        gag = self.combattants[self.gagnant]
        perd = self.combattants[1 - self.gagnant]
        accent = theme.CLASSES[gag.classe]["accent"]
        a = ease_out(min(1.0, self.temps * 1.3))

        # rayons de lumiere derriere le vainqueur
        centre = (theme.LARGEUR // 2, 322)
        rayons = pygame.Surface((theme.LARGEUR, theme.HAUTEUR), pygame.SRCALPHA)
        for i in range(16):
            ang = t * 0.25 + i * math.pi / 8
            lg = 560
            p1 = (centre[0] + math.cos(ang) * 40, centre[1] + math.sin(ang) * 40)
            p2 = (centre[0] + math.cos(ang) * lg, centre[1] + math.sin(ang) * lg)
            p3 = (centre[0] + math.cos(ang + 0.12) * lg,
                  centre[1] + math.sin(ang + 0.12) * lg)
            pygame.draw.polygon(rayons, (accent[0], accent[1], accent[2], 13),
                                [p1, p2, p3])
        ecran.blit(rayons, (0, 0))
        h = decor.halo(300, accent, 74)
        ecran.blit(h, (centre[0] - 300, centre[1] - 300))

        # vainqueur
        sp = sprites.sprite(gag.classe, 9)
        flotte = math.sin(t * 1.8) * 8
        ecran.blit(sp, (centre[0] - sp.get_width() // 2,
                        centre[1] - sp.get_height() // 2 + flotte))

        self.fx.dessiner(ecran)

        widgets.texte(ecran, "VICTOIRE", 20, theme.OR, (theme.LARGEUR // 2, 62),
                      "center", gras=True, espacement=12, alpha=int(255 * a))
        widgets.texte_lumineux(ecran, gag.pseudo.upper(), 64, theme.TEXTE,
                               (theme.LARGEUR // 2, 118), espacement=5, force=4)
        widgets.texte(ecran, "%s  -  vainqueur en %d tours" %
                      (gag.classe, self.tours), 17, accent,
                      (theme.LARGEUR // 2, 166), "center", espacement=2)

        # resume chiffre
        r = pygame.Rect(0, 0, 720, 130)
        r.center = (theme.LARGEUR // 2, 528)
        widgets.panneau(ecran, r, 176, (58, 60, 94), 18, theme.ENCRE, 1)
        colonnes = [
            ("TOURS", str(self.tours), theme.OR),
            ("DEGATS INFLIGES", str(gag.degats_infliges), theme.ROUGE),
            ("PV RESTANTS", str(max(gag.j.hp, 0)), theme.PV_HAUT),
            ("SOINS", str(gag.soins), theme.VERT),
        ]
        for i, (lib, val, coul) in enumerate(colonnes):
            cx = r.x + 90 + i * 180
            widgets.texte(ecran, val, 36, coul, (cx, r.y + 30), "center", gras=True,
                          titre=True)
            widgets.texte(ecran, lib, 11, theme.BRUME, (cx, r.y + 84), "center",
                          gras=True, espacement=2, ombre=False)

        widgets.texte(ecran, "%s (%s) tombe au combat." %
                      (perd.pseudo, perd.classe), 15, theme.TEXTE_DOUX,
                      (theme.LARGEUR // 2, 612), "center")

        p = pulse(t, 3.0)
        widgets.texte(ecran, "ENTREE : nouveau duel        ECHAP : quitter", 18,
                      (255, int(200 + 50 * p), int(140 + 60 * p)),
                      (theme.LARGEUR // 2, 662), "center", gras=True, espacement=2)
