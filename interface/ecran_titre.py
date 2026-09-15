"""Ecran titre : la scene de bataille en fond, le titre qui pulse devant."""

import math

import pygame

from . import theme, sprites, widgets, decor
from .app import Scene, pulse, ease_out


class EcranTitre(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.apparition = 0.0

    def entrer(self):
        self.apparition = 0.0

    def evenement(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.quitter()
            else:
                self._demarrer()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            self._demarrer()

    def _demarrer(self):
        from .ecran_classes import EcranClasses
        self.app.changer(EcranClasses(self.app))

    def avancer(self, dt, t):
        self.apparition = min(1.0, self.apparition + dt * 0.8)

    def dessiner(self, ecran, t):
        self.app.arene.dessiner(ecran, t, 1 / 60.0)

        # duel en ombre chinoise, avec une lueur derriere chaque combattant
        for nom, x, gauche, teinte in (("Chevalier", 360, False, (110, 180, 255)),
                                       ("Assassin", 920, True, (176, 122, 255))):
            sp = sprites.sprite(nom, 7, gauche)
            flotte = math.sin(t * 1.5 + x) * 4
            y = decor.SOL - sp.get_height() + flotte
            h = decor.halo(140, teinte, 58)
            ecran.blit(h, (x - 140, decor.SOL - 150))
            ombre = sprites.silhouette_classe(nom, 7, gauche, (52, 46, 84, 255))
            ecran.blit(ombre, (x - sp.get_width() // 2, y))
            # lisere colore pour detacher la silhouette du fond
            rim = sprites.silhouette_classe(nom, 7, gauche, teinte + (255,))
            rim.set_alpha(70)
            ecran.blit(rim, (x - sp.get_width() // 2 - 3, y - 3))

        # voile sombre pour faire ressortir le titre
        voile = pygame.Surface((theme.LARGEUR, theme.HAUTEUR), pygame.SRCALPHA)
        for i in range(0, 400, 2):
            a = int(118 * (1 - abs(i - 170) / 250.0))
            if a > 0:
                voile.fill((6, 5, 18, a), (0, i, theme.LARGEUR, 2))
        ecran.blit(voile, (0, 0))

        a = ease_out(self.apparition)
        cy = 168 + (1 - a) * 30

        # bandeau superieur
        widgets.texte(ecran, "DUEL AU TOUR PAR TOUR", 17, theme.OR,
                      (theme.LARGEUR // 2, int(cy - 58)), "center", gras=True,
                      espacement=7, alpha=int(230 * a))

        widgets.texte_lumineux(ecran, "RPG COMBAT", 92, theme.TEXTE,
                               (theme.LARGEUR // 2, int(cy + 18)),
                               espacement=8, force=4, couleur_lueur=theme.OR)

        # filet dore avec losange central
        larg = int(430 * a)
        y = int(cy + 78)
        pygame.draw.line(ecran, theme.OR_SOMBRE,
                         (theme.LARGEUR // 2 - larg, y),
                         (theme.LARGEUR // 2 - 22, y), 2)
        pygame.draw.line(ecran, theme.OR_SOMBRE,
                         (theme.LARGEUR // 2 + 22, y),
                         (theme.LARGEUR // 2 + larg, y), 2)
        pygame.draw.polygon(ecran, theme.OR, [
            (theme.LARGEUR // 2, y - 9), (theme.LARGEUR // 2 + 10, y),
            (theme.LARGEUR // 2, y + 9), (theme.LARGEUR // 2 - 10, y)])

        widgets.texte(ecran, "Assassin  -  Barbare  -  Chevalier  -  Mage", 20,
                      theme.TEXTE_DOUX, (theme.LARGEUR // 2, y + 36), "center",
                      espacement=2, alpha=int(255 * a))

        # invite clignotante
        if self.apparition > 0.7:
            p = pulse(t, 3.4)
            r = pygame.Rect(0, 0, 420, 62)
            r.center = (theme.LARGEUR // 2, 560)
            widgets.lueur_rect(ecran, r, theme.OR, int(26 + 30 * p), 22)
            widgets.panneau(ecran, r, 150, theme.OR_SOMBRE, 18, theme.ENCRE, 1)
            widgets.texte(ecran, "APPUYEZ SUR ENTREE", 24,
                          (255, int(210 + 40 * p), int(140 + 60 * p)),
                          r.center, "center", gras=True, espacement=4)

        widgets.texte(ecran, "Entree : commencer     F11 : plein ecran     "
                             "Echap : quitter", 15, theme.BRUME,
                      (theme.LARGEUR // 2, 636), "center")
        widgets.texte(ecran, "Moteur de jeu : Bah Ibrahima Sory   |   "
                             "Interface pygame", 14, (104, 108, 142),
                      (theme.LARGEUR // 2, 676), "center")
