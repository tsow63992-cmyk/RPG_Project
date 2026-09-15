"""Boucle principale : gestion des scenes, des transitions et du tremblement."""

import math
import random
import sys

import pygame

from . import theme
from . import decor


class Scene:
    """Interface commune a toutes les scenes."""

    def __init__(self, app):
        self.app = app

    def entrer(self):
        pass

    def evenement(self, e):
        pass

    def avancer(self, dt, t):
        pass

    def dessiner(self, ecran, t):
        pass


class Application:
    def __init__(self, plein_ecran=False):
        pygame.init()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        theme.init_polices()
        drapeaux = pygame.FULLSCREEN if plein_ecran else 0
        self.ecran = pygame.display.set_mode((theme.LARGEUR, theme.HAUTEUR), drapeaux)
        pygame.display.set_caption("RPG Combat - Jeu de combat au tour par tour")
        self.tampon = pygame.Surface((theme.LARGEUR, theme.HAUTEUR))
        self.horloge = pygame.time.Clock()
        self.actif = True
        self.t = 0.0

        # decors partages entre les scenes
        self.fond_menu = decor.FondStellaire()
        self.arene = decor.Decor()

        # etat partage : pseudos et classes choisies
        self.noms = ["Joueur 1", "Joueur 2"]
        self.classes = ["Assassin", "Barbare"]

        # transition et secousse
        self.scene = None
        self._scene_suivante = None
        self._fondu = 0.0
        self._sens_fondu = 0
        self.secousse = 0.0
        self.flash = 0.0
        self.flash_couleur = (255, 255, 255)

    # ---------------------------------------------------------------- outils
    def changer(self, scene, immediat=False):
        if immediat:
            self.scene = scene
            scene.entrer()
        else:
            self._scene_suivante = scene
            self._sens_fondu = 1

    def secouer(self, force):
        self.secousse = max(self.secousse, force)

    def eclair(self, force=0.5, couleur=(255, 255, 255)):
        self.flash = max(self.flash, force)
        self.flash_couleur = couleur

    def quitter(self):
        self.actif = False

    # ------------------------------------------------------------ boucle jeu
    def lancer(self, scene_depart):
        self.changer(scene_depart, immediat=True)
        while self.actif:
            dt = min(self.horloge.tick(theme.FPS) / 1000.0, 0.05)
            self.t += dt

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.actif = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif self._sens_fondu == 0:
                    self.scene.evenement(e)

            # transition
            if self._sens_fondu == 1:
                self._fondu = min(1.0, self._fondu + dt * 3.6)
                if self._fondu >= 1.0:
                    self.scene = self._scene_suivante
                    self._scene_suivante = None
                    self.scene.entrer()
                    self._sens_fondu = -1
            elif self._sens_fondu == -1:
                self._fondu = max(0.0, self._fondu - dt * 3.0)
                if self._fondu <= 0.0:
                    self._sens_fondu = 0

            self.scene.avancer(dt, self.t)
            self.secousse = max(0.0, self.secousse - dt * 3.2)
            self.flash = max(0.0, self.flash - dt * 2.6)

            self.tampon.fill(theme.NOIR)
            self.scene.dessiner(self.tampon, self.t)

            if self.flash > 0.01:
                voile = pygame.Surface((theme.LARGEUR, theme.HAUTEUR))
                voile.fill(self.flash_couleur)
                voile.set_alpha(int(200 * self.flash))
                self.tampon.blit(voile, (0, 0))

            dx = dy = 0
            if self.secousse > 0.01:
                amp = self.secousse * 16
                dx = int(random.uniform(-amp, amp))
                dy = int(random.uniform(-amp, amp))
            self.ecran.fill(theme.NOIR)
            self.ecran.blit(self.tampon, (dx, dy))

            if self._fondu > 0.001:
                voile = pygame.Surface((theme.LARGEUR, theme.HAUTEUR))
                voile.fill((0, 0, 0))
                voile.set_alpha(int(255 * min(1.0, self._fondu)))
                self.ecran.blit(voile, (0, 0))

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def souris_dans(rect, pos):
    return pygame.Rect(rect).collidepoint(pos)


def ease(t):
    """Adoucissement classique (lent - rapide - lent)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def pulse(t, vitesse=3.0):
    return 0.5 + 0.5 * math.sin(t * vitesse)
