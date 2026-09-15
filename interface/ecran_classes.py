"""Saisie des pseudos puis choix des classes, joueur apres joueur."""

import math

import pygame

from . import theme, sprites, widgets, bridge
from .app import Scene, pulse, ease_out

CARTE_L, CARTE_H = 252, 322
ECART = 26
TOTAL = 4 * CARTE_L + 3 * ECART
X0 = (theme.LARGEUR - TOTAL) // 2
Y0 = 146

COULEUR_JOUEUR = [(120, 200, 255), (255, 150, 190)]


class EcranClasses(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.etape = "nom"          # "nom" puis "classe"
        self.joueur = 0
        self.saisie = ""
        self.index = 0
        self.apparition = 0.0
        self.caret = 0.0

    def entrer(self):
        self.apparition = 0.0

    # ------------------------------------------------------------ evenements
    def evenement(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.quitter()
            return
        if self.etape == "nom":
            self._evenement_nom(e)
        else:
            self._evenement_classe(e)

    def _evenement_nom(self, e):
        if e.type != pygame.KEYDOWN:
            if e.type == pygame.MOUSEBUTTONDOWN:
                self._valider_nom()
            return
        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._valider_nom()
        elif e.key == pygame.K_BACKSPACE:
            self.saisie = self.saisie[:-1]
        else:
            c = getattr(e, "unicode", "")
            if c and c.isprintable() and len(self.saisie) < 14:
                self.saisie += c

    def _valider_nom(self):
        nom = self.saisie.strip() or ("Joueur %d" % (self.joueur + 1))
        self.app.noms[self.joueur] = nom
        self.etape = "classe"
        self.apparition = 0.0
        self.index = 0 if self.joueur == 0 else 1

    def _evenement_classe(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_q):
                self.index = (self.index - 1) % 4
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % 4
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._valider_classe()
            elif pygame.K_1 <= e.key <= pygame.K_4:
                self.index = e.key - pygame.K_1
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for i in range(4):
                if self._rect_carte(i).collidepoint(e.pos):
                    if i == self.index:
                        self._valider_classe()
                    else:
                        self.index = i
                    return
            if self._rect_bouton().collidepoint(e.pos):
                self._valider_classe()
        elif e.type == pygame.MOUSEMOTION:
            for i in range(4):
                if self._rect_carte(i).collidepoint(e.pos):
                    self.index = i

    def _valider_classe(self):
        self.app.classes[self.joueur] = theme.ORDRE_CLASSES[self.index]
        if self.joueur == 0:
            self.joueur = 1
            self.etape = "nom"
            self.saisie = ""
            self.apparition = 0.0
        else:
            from .ecran_combat import EcranCombat
            self.app.changer(EcranCombat(self.app))

    # ---------------------------------------------------------------- rendu
    def _rect_carte(self, i):
        return pygame.Rect(X0 + i * (CARTE_L + ECART), Y0, CARTE_L, CARTE_H)

    def _rect_bouton(self):
        r = pygame.Rect(0, 0, 340, 54)
        r.center = (theme.LARGEUR // 2, 680)
        return r

    def avancer(self, dt, t):
        self.apparition = min(1.0, self.apparition + dt * 2.6)
        self.caret += dt

    def dessiner(self, ecran, t):
        self.app.fond_menu.dessiner(ecran, t, 1 / 60.0)
        if self.etape == "nom":
            self._dessiner_nom(ecran, t)
        else:
            self._dessiner_classes(ecran, t)

    # ---- saisie du pseudo
    def _dessiner_nom(self, ecran, t):
        accent = COULEUR_JOUEUR[self.joueur]
        a = ease_out(self.apparition)
        cy = 300 + (1 - a) * 24

        widgets.texte(ecran, "JOUEUR %d" % (self.joueur + 1), 20, accent,
                      (theme.LARGEUR // 2, int(cy - 108)), "center", gras=True,
                      espacement=8)
        widgets.texte_lumineux(ecran, "ENTREZ VOTRE PSEUDO", 46, theme.TEXTE,
                               (theme.LARGEUR // 2, int(cy - 50)), espacement=3,
                               force=2, couleur_lueur=accent)

        champ = pygame.Rect(0, 0, 620, 84)
        champ.center = (theme.LARGEUR // 2, int(cy + 40))
        widgets.lueur_rect(ecran, champ, accent, 52, 24)
        widgets.panneau(ecran, champ, 196, accent, 18, theme.NUIT, 2)

        affiche = self.saisie if self.saisie else ""
        couleur = theme.TEXTE if affiche else theme.BRUME
        montre = affiche or "Joueur %d" % (self.joueur + 1)
        r = widgets.texte(ecran, montre, 34, couleur, champ.center, "center",
                          gras=True)
        if math.sin(self.caret * 6) > 0:
            pygame.draw.rect(ecran, accent, (r.right + 8, r.centery - 19, 3, 38))

        widgets.texte(ecran, "Entree pour valider   -   le pseudo par defaut "
                             "est utilise si vous laissez vide", 15,
                      theme.TEXTE_DOUX, (theme.LARGEUR // 2, int(cy + 116)),
                      "center")

        # galerie des quatre classes, en veille
        widgets.texte(ecran, "LES QUATRE VOIES", 12, theme.BRUME,
                      (theme.LARGEUR // 2, 476), "center", gras=True,
                      espacement=6, ombre=False)
        for i, cls in enumerate(theme.ORDRE_CLASSES):
            cx = theme.LARGEUR // 2 + (i - 1.5) * 190
            sp = sprites.sprite(cls, 4)
            flotte = math.sin(t * 1.6 + i * 1.2) * 4
            img = sprites.silhouette_classe(cls, 4, False, (120, 116, 168, 255))
            img.set_alpha(150)
            ecran.blit(img, (cx - sp.get_width() // 2, 508 + flotte))
            widgets.texte(ecran, cls.upper(), 12, theme.BRUME, (cx, 632), "center",
                          gras=True, espacement=3, ombre=False)

        # rappel du choix du joueur 1
        if self.joueur == 1:
            info = "Joueur 1 : %s  -  %s" % (self.app.noms[0], self.app.classes[0])
            widgets.texte(ecran, info, 17, COULEUR_JOUEUR[0],
                          (theme.LARGEUR // 2, 672), "center", gras=True)

    # ---- choix de la classe
    def _dessiner_classes(self, ecran, t):
        accent_j = COULEUR_JOUEUR[self.joueur]
        nom = self.app.noms[self.joueur]
        widgets.texte(ecran, "JOUEUR %d" % (self.joueur + 1), 16, accent_j,
                      (theme.LARGEUR // 2, 44), "center", gras=True, espacement=8)
        widgets.texte_lumineux(ecran, nom.upper(), 40, theme.TEXTE,
                               (theme.LARGEUR // 2, 82), espacement=3, force=2,
                               couleur_lueur=accent_j)
        widgets.texte(ecran, "Choisissez votre classe   -   fleches ou clic pour "
                             "naviguer", 15, theme.TEXTE_DOUX,
                      (theme.LARGEUR // 2, 118), "center", espacement=1)

        for i, cls in enumerate(theme.ORDRE_CLASSES):
            self._carte(ecran, i, cls, i == self.index, t)

        self._detail(ecran, theme.ORDRE_CLASSES[self.index], t)

        # bouton de confirmation
        r = self._rect_bouton()
        accent = theme.CLASSES[theme.ORDRE_CLASSES[self.index]]["accent"]
        p = pulse(t, 3.2)
        widgets.lueur_rect(ecran, r, accent, int(30 + 34 * p), 20)
        widgets.panneau(ecran, r, 170, accent, 16, theme.NUIT, 2)
        widgets.texte(ecran, "CONFIRMER  -  ENTREE", 19, theme.TEXTE, r.center,
                      "center", gras=True, espacement=3)

    def _carte(self, ecran, i, cls, choisi, t):
        info = theme.CLASSES[cls]
        accent = info["accent"]
        r = self._rect_carte(i)
        decalage = ease_out(min(1.0, max(0.0, self.apparition * 1.6 - i * 0.12)))
        r = r.move(0, int((1 - decalage) * 40))
        if decalage <= 0.01:
            return

        if choisi:
            r = r.inflate(16, 18)
            widgets.lueur_rect(ecran, r, accent, 74, 26)
        widgets.panneau(ecran, r, 205 if choisi else 150,
                        accent if choisi else (58, 60, 92),
                        18, theme.NUIT if choisi else theme.ENCRE,
                        2 if choisi else 1)

        # sprite
        ech = 5 if choisi else 4
        sp = sprites.sprite(cls, ech)
        flotte = math.sin(t * 2.2 + i) * 4 if choisi else 0
        ecran.blit(sp, (r.centerx - sp.get_width() // 2,
                        r.y + (16 if choisi else 26) + flotte))

        haut = r.y + (172 if choisi else 160)
        widgets.texte(ecran, info["titre"], 24 if choisi else 21,
                      accent if choisi else theme.TEXTE,
                      (r.centerx, haut), "center", gras=True, espacement=2)
        widgets.texte(ecran, info["devise"], 13, theme.TEXTE_DOUX,
                      (r.centerx, haut + 30), "center", ombre=False)

        # statistiques
        y = haut + 54
        for libelle, cle, c1, c2, maxi in (
                ("PV", "pv", theme.PV_HAUT, theme.PV_BAS, 150),
                ("MANA", "mana", theme.MANA_HAUT, theme.MANA_BAS, 120),
                ("ATK", "atk", theme.ORANGE, (168, 78, 40), 5),
                ("DEF", "def", theme.ARMURE_HAUT, theme.ARMURE_BAS, 5)):
            widgets.texte(ecran, libelle, 11, theme.BRUME, (r.x + 22, y), "topleft",
                          gras=True, ombre=False)
            widgets.barre_simple(ecran, (r.x + 62, y + 2, r.w - 116, 8),
                                 info[cle] / maxi, c1, c2, (22, 22, 40), 4)
            widgets.texte(ecran, str(info[cle]), 11, theme.TEXTE_DOUX,
                          (r.right - 22, y), "topright", ombre=False)
            y += 18

        widgets.texte(ecran, "%d competences" % len(bridge.COMPETENCES[cls]), 12,
                      accent, (r.centerx, r.bottom - 26), "center", ombre=False)

    def _detail(self, ecran, cls, t):
        info = theme.CLASSES[cls]
        accent = info["accent"]
        r = pygame.Rect(X0, 490, TOTAL, 150)
        widgets.panneau(ecran, r, 168, (52, 54, 86), 18, theme.ENCRE, 1)
        pygame.draw.rect(ecran, accent, (r.x, r.y + 18, 4, r.h - 36))

        widgets.texte(ecran, "PROFIL", 12, accent, (r.x + 22, r.y + 18), "topleft",
                      gras=True, espacement=4, ombre=False)
        widgets.paragraphe(ecran, info["detail"], 15, theme.TEXTE,
                           r.x + 22, r.y + 42, 430, 22)
        y = r.y + 92
        for p in bridge.passifs(cls):
            pygame.draw.circle(ecran, accent, (r.x + 27, y + 8), 3)
            widgets.texte(ecran, p, 13, theme.TEXTE_DOUX, (r.x + 38, y), "topleft",
                          ombre=False)
            y += 21

        # liste des competences, sur deux colonnes
        cx = r.x + 500
        widgets.texte(ecran, "COMPETENCES", 12, accent, (cx, r.y + 18), "topleft",
                      gras=True, espacement=4, ombre=False)
        comps = bridge.COMPETENCES[cls]
        for i, c in enumerate(comps):
            col, lig = divmod(i, 4)
            x = cx + col * 290
            y = r.y + 42 + lig * 26
            ic = sprites.icone_cache(c["icone"], 18, accent)
            ecran.blit(ic, (x, y + 1))
            widgets.texte(ecran, c["nom"], 14, theme.TEXTE, (x + 24, y), "topleft",
                          ombre=False)
            cout = "%d MP" % c["cout"] if c["cout"] else "libre"
            widgets.texte(ecran, cout, 12,
                          theme.MANA_HAUT if c["cout"] else theme.TEXTE_DOUX,
                          (x + 268, y + 2), "topright", ombre=False)

