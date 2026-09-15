"""Ecran de combat facon JRPG : scene animee, panneaux d'etat, journal, actions."""

import math
import random

import pygame

from . import theme, sprites, widgets, decor, fx, bridge
from .app import Scene, ease_out, pulse

SOL = decor.SOL
POS_X = (352, 928)            # position au sol des deux combattants
ECHELLE = 7

PANNEAU_BAS = pygame.Rect(16, 440, theme.LARGEUR - 32, 266)
ZONE_JOURNAL = pygame.Rect(34, 452, 520, 240)
ZONE_ACTIONS = pygame.Rect(576, 452, 672, 240)
BOUTON_H = 44

MELEE = {"lame", "double", "hache", "charge", "carnage", "choc"}


class Combattant3D:
    """Etat d'affichage d'un combattant (position, secousse, teinte)."""

    def __init__(self, donnees, index):
        self.d = donnees
        self.index = index
        self.sens = 1 if index == 0 else -1
        self.x = POS_X[index]
        self.decalage = 0.0
        self.recul = 0.0
        self.flash = 0.0
        self.chute = 0.0
        self.pv = widgets.Barre(donnees.j.hp, donnees.pv_max)
        self.mana = widgets.Barre(donnees.j.mana, donnees.mana_max)
        self.armure = widgets.Barre(donnees.j.armure, max(donnees.armure_max, 1))

    def sync(self):
        self.d.rafraichir_maxima()
        self.pv.regler(max(self.d.j.hp, 0), self.d.pv_max)
        self.mana.regler(max(self.d.j.mana, 0), self.d.mana_max)
        self.armure.regler(max(self.d.j.armure, 0), max(self.d.armure_max, 1))

    def avancer(self, dt):
        self.pv.avancer(dt)
        self.mana.avancer(dt)
        self.armure.avancer(dt)
        self.recul *= max(0.0, 1 - dt * 7)
        self.flash = max(0.0, self.flash - dt * 4.0)

    @property
    def centre(self):
        sp = sprites.sprite(self.d.classe, ECHELLE)
        return (self.x + self.decalage + self.recul,
                SOL - sp.get_height() * 0.55)


class EcranCombat(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.fx = fx.Systeme()
        self.journal = []
        self.tour = 1
        self.phase = "intro"
        self.chrono = 0.0
        self.index_sel = 0
        self.anim = None
        self.banniere = 0.0
        self.gagnant = None

        self.combattants = [
            bridge.Combattant(app.classes[0], app.noms[0], 1),
            bridge.Combattant(app.classes[1], app.noms[1], -1),
        ]
        self.vues = [Combattant3D(self.combattants[0], 0),
                     Combattant3D(self.combattants[1], 1)]
        self.actif = random.randint(0, 1)

    # ------------------------------------------------------------- utilitaires
    @property
    def vue_actif(self):
        return self.vues[self.actif]

    @property
    def vue_passif(self):
        return self.vues[1 - self.actif]

    def ajouter_journal(self, texte, couleur=None):
        if not texte:
            return
        if couleur is None:
            couleur = _couleur_ligne(texte)
        self.journal.append([texte, couleur, 0.0])
        if len(self.journal) > 40:
            self.journal.pop(0)

    def entrer(self):
        self.ajouter_journal("Le duel commence !", theme.OR)
        self.ajouter_journal("%s attaque en premier." %
                             self.combattants[self.actif].pseudo, theme.OR)
        self._demarrer_tour()

    # ----------------------------------------------------------------- tours
    def _demarrer_tour(self):
        self.phase = "intro"
        self.chrono = 0.0
        self.banniere = 0.0
        actif = self.combattants[self.actif]
        passif = self.combattants[1 - self.actif]
        av_pv = actif.j.hp
        res = bridge.debut_de_tour(actif, passif)
        for l in res["lignes"]:
            self.ajouter_journal(bridge._joli(l))
        perte = max(0, av_pv - actif.j.hp)
        if perte:
            v = self.vue_actif
            self.fx.texte(v.centre[0], v.centre[1] - 40, "-%d" % perte,
                          theme.VERT_POISON, 34)
            self.fx.gerbe(v.centre[0], v.centre[1], theme.VERT_POISON, 16, 160, .7, 5)
        self.index_sel = 0
        for v in self.vues:
            v.sync()
        if not actif.vivant:
            self._terminer(1 - self.actif)

    def _terminer(self, gagnant):
        self.gagnant = gagnant
        self.phase = "fin"
        self.chrono = 0.0
        self.vues[1 - gagnant].chute = 0.001
        self.ajouter_journal("%s remporte le duel !" %
                             self.combattants[gagnant].pseudo, theme.OR)

    def _competences_visibles(self):
        return self.combattants[self.actif].competences

    def _lancer(self, i):
        actif = self.combattants[self.actif]
        comps = actif.competences
        if not (0 <= i < len(comps)):
            return
        comp = comps[i]
        if actif.etat(comp) != "ok":
            self.fx.texte(theme.LARGEUR // 2, 400, "INDISPONIBLE", theme.ROUGE, 26,
                          40, 0.8)
            return
        self.phase = "anime"
        self.chrono = 0.0
        self.anim = {"comp": comp, "resultat": None, "impact": False,
                     "melee": comp["fx"] in MELEE}

    # ------------------------------------------------------------ evenements
    def evenement(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.quitter()
            return
        if self.phase == "intro":
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.chrono = max(self.chrono, 1.05)
            return
        if self.phase != "choix":
            return

        comps = self._competences_visibles()
        n = len(comps)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.index_sel = (self.index_sel + 1) % n
            elif e.key in (pygame.K_UP, pygame.K_z):
                self.index_sel = (self.index_sel - 1) % n
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.index_sel = (self.index_sel + 4) % n
            elif e.key in (pygame.K_LEFT, pygame.K_q):
                self.index_sel = (self.index_sel - 4) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._lancer(self.index_sel)
            elif pygame.K_1 <= e.key <= pygame.K_9:
                self._lancer(e.key - pygame.K_1)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for i in range(n):
                if self._rect_bouton(i).collidepoint(e.pos):
                    self.index_sel = i
                    self._lancer(i)
                    return
        elif e.type == pygame.MOUSEMOTION:
            for i in range(n):
                if self._rect_bouton(i).collidepoint(e.pos):
                    self.index_sel = i

    def _rect_bouton(self, i):
        col, lig = divmod(i, 4)
        w = (ZONE_ACTIONS.w - 14) // 2
        return pygame.Rect(ZONE_ACTIONS.x + col * (w + 14),
                           ZONE_ACTIONS.y + 30 + lig * (BOUTON_H + 5), w, BOUTON_H)

    # -------------------------------------------------------------- logique
    def avancer(self, dt, t):
        self.chrono += dt
        self.banniere = min(1.0, self.banniere + dt * 2.6)
        self.fx.avancer(dt)
        for v in self.vues:
            v.avancer(dt)
        for l in self.journal:
            l[2] = min(1.0, l[2] + dt * 5)

        if self.phase == "intro":
            if self.chrono > 1.1:
                self.phase = "choix"
                self.chrono = 0.0
        elif self.phase == "anime":
            self._avancer_animation(dt)
        elif self.phase == "fin":
            v = self.vues[1 - self.gagnant]
            v.chute = min(1.0, v.chute + dt * 1.6)
            if self.chrono > 2.4:
                from .ecran_victoire import EcranVictoire
                self.app.changer(EcranVictoire(
                    self.app, self.combattants, self.gagnant, self.tour))
                self.phase = "attente"

    def _avancer_animation(self, dt):
        a = self.anim
        va, vp = self.vue_actif, self.vue_passif
        comp = a["comp"]
        c = self.chrono

        # deplacement de l'attaquant
        if a["melee"]:
            if c < 0.18:
                va.decalage = -va.sens * 34 * ease_out(c / 0.18)
            elif c < 0.42:
                k = ease_out((c - 0.18) / 0.24)
                depart = -va.sens * 34
                arrivee = va.sens * (abs(POS_X[1] - POS_X[0]) - 190)
                va.decalage = depart + (arrivee - depart) * k
            elif c < 1.05:
                k = ease_out((c - 0.42) / 0.63)
                arrivee = va.sens * (abs(POS_X[1] - POS_X[0]) - 190)
                va.decalage = arrivee * (1 - k)
            else:
                va.decalage = 0.0
        else:
            if c < 0.42:
                va.decalage = -va.sens * 18 * math.sin(c / 0.42 * math.pi)
            else:
                va.decalage = 0.0

        # impact
        seuil = 0.42 if a["melee"] else 0.5
        if not a["impact"] and c >= seuil:
            a["impact"] = True
            self._impact(comp)

        if c > 1.25:
            self._fin_animation()

    def _impact(self, comp):
        actif = self.combattants[self.actif]
        passif = self.combattants[1 - self.actif]
        va, vp = self.vue_actif, self.vue_passif

        res = bridge.executer(actif, comp, passif)
        self.anim["resultat"] = res
        for l in res["lignes"]:
            self.ajouter_journal(l)

        cible_v = vp if comp["cible"] else va
        cx, cy = cible_v.centre

        fx.jouer(self.fx, comp["fx"], cx, cy, va.sens)

        if res["esquive"]:
            self.fx.texte(cx, cy - 50, "ESQUIVE", theme.VIOLET, 34)
        elif res["degats"] > 0:
            crit = res["critique"]
            self.fx.texte(cx, cy - 50, "-%d" % res["degats"],
                          theme.OR if crit else theme.ROUGE, 56 if crit else 44)
            if crit:
                self.fx.texte(cx, cy - 104, "CRITIQUE", theme.OR, 26, 60, 1.0)
            cible_v.recul = -va.sens * 34
            cible_v.flash = 1.0
            force = min(0.9, 0.22 + res["degats"] / 60.0)
            self.app.secouer(force)
            if crit:
                self.app.eclair(0.30, (255, 230, 180))
        if res["soin"] > 0:
            self.fx.texte(va.centre[0], va.centre[1] - 60, "+%d" % res["soin"],
                          theme.VERT, 40)
        if res["armure"] > 0:
            self.fx.texte(va.centre[0] + 40, va.centre[1] - 20,
                          "+%d ARM" % res["armure"], theme.ARMURE_HAUT, 26)
        if res["mana_vole"] > 0:
            self.fx.texte(vp.centre[0], vp.centre[1] - 20,
                          "-%d MP" % res["mana_vole"], theme.MANA_HAUT, 28)
            self.fx.texte(va.centre[0], va.centre[1] - 90,
                          "+%d MP" % res["mana_vole"], theme.MANA_HAUT, 28)
        if res["riposte"] > 0:
            self.fx.texte(va.centre[0], va.centre[1] - 70, "-%d" % res["riposte"],
                          theme.BLEU, 34)
            fx.jouer(self.fx, "bouclier", va.centre[0], va.centre[1], -va.sens)
            va.flash = 1.0
            va.recul = va.sens * 22

        for v in self.vues:
            v.sync()

    def _fin_animation(self):
        self.vue_actif.decalage = 0.0
        self.anim = None
        mort = [i for i, c in enumerate(self.combattants) if not c.vivant]
        if mort:
            perdant = mort[0]
            self._terminer(1 - perdant)
            return
        self.actif = 1 - self.actif
        self.tour += 1
        self._demarrer_tour()

    # ---------------------------------------------------------------- rendu
    def dessiner(self, ecran, t):
        self.app.arene.dessiner(ecran, t, 1 / 60.0)
        self._dessiner_combattants(ecran, t)
        self.fx.dessiner(ecran)
        self._dessiner_panneaux(ecran, t)
        self._dessiner_banniere(ecran, t)
        self._dessiner_bas(ecran, t)

    # ---- combattants
    def _dessiner_combattants(self, ecran, t):
        for i, v in enumerate(self.vues):
            d = v.d
            sp = sprites.sprite(d.classe, ECHELLE, vers_gauche=(i == 1))
            x = v.x + v.decalage + v.recul
            flotte = math.sin(t * 2.0 + i * 1.7) * 4
            if self.phase == "anime" and i == self.actif:
                flotte -= 6 * math.sin(min(self.chrono, 0.42) / 0.42 * math.pi)
            y = SOL - sp.get_height() + flotte

            # ombre portee
            ombre = pygame.Surface((sp.get_width(), 26), pygame.SRCALPHA)
            pygame.draw.ellipse(ombre, (0, 0, 0, 110),
                                (10, 6, sp.get_width() - 20, 16))
            ecran.blit(ombre, (x - sp.get_width() // 2, SOL - 12))

            img = sp
            # chute a la mort
            if v.chute > 0:
                k = ease_out(v.chute)
                img = pygame.transform.rotate(sp, -v.sens * 84 * k)
                img = img.copy()
                img.set_alpha(int(255 * (1 - k * 0.55)))
                y = SOL - img.get_height() + int(60 * k)

            # camouflage : le sprite devient translucide
            if getattr(d.j, "invisible", False):
                img = img.copy()
                img.set_alpha(135)
                h = decor.halo(90, (176, 122, 255), 70)
                ecran.blit(h, (x - 90, SOL - img.get_height() // 2 - 90))

            # aura du joueur actif
            if i == self.actif and self.phase in ("choix", "intro"):
                h = decor.halo(112, theme.CLASSES[d.classe]["accent"], 74)
                h.set_alpha(int(150 + 90 * pulse(t, 2.6)))
                ecran.blit(h, (x - 112, SOL - 112))

            ecran.blit(img, (x - img.get_width() // 2, y))

            # eclair blanc quand le personnage encaisse
            if v.flash > 0.02:
                blanc = sprites.silhouette(img, (255, 255, 255, 255))
                blanc.set_alpha(int(210 * v.flash))
                ecran.blit(blanc, (x - img.get_width() // 2, y))

            # curseur JRPG au-dessus du combattant actif
            if i == self.actif and self.phase == "choix":
                fleche = 8 + math.sin(t * 5) * 5
                pygame.draw.polygon(ecran, theme.OR, [
                    (x, y - 16 + fleche), (x - 12, y - 34 + fleche),
                    (x + 12, y - 34 + fleche)])

    # ---- panneaux d'etat
    def _dessiner_panneaux(self, ecran, t):
        for i, v in enumerate(self.vues):
            r = pygame.Rect(24 if i == 0 else theme.LARGEUR - 24 - 372, 22, 372, 144)
            d = v.d
            accent = theme.CLASSES[d.classe]["accent"]
            if i == self.actif and self.phase in ("choix", "intro"):
                widgets.lueur_rect(ecran, r, accent, 52, 18)
            widgets.panneau(ecran, r, 176,
                            accent if i == self.actif else (56, 58, 92),
                            16, theme.ENCRE, 2 if i == self.actif else 1)

            # portrait
            pr = pygame.Rect(r.x + 12, r.y + 12, 58, 58)
            widgets.panneau(ecran, pr, 150, accent, 12, theme.NUIT, 1, reflet=False)
            mini = sprites.sprite(d.classe, 2)
            ecran.blit(mini, (pr.centerx - mini.get_width() // 2,
                              pr.centery - mini.get_height() // 2 - 2))

            widgets.texte(ecran, d.pseudo, 21, theme.TEXTE, (r.x + 82, r.y + 14),
                          "topleft", gras=True)
            widgets.texte(ecran, d.classe.upper(), 12, accent,
                          (r.x + 82, r.y + 42), "topleft", gras=True, espacement=3,
                          ombre=False)

            # barres
            bx, bw = r.x + 12, r.w - 24
            y = r.y + 78
            self._barre(ecran, v.pv, (bx, y, bw, 15), "PV",
                        theme.PV_HAUT, theme.PV_BAS, d.j.hp)
            y += 22
            self._barre(ecran, v.mana, (bx, y, bw - 124, 9), "MP",
                        theme.MANA_HAUT, theme.MANA_BAS, d.j.mana, petit=True)
            widgets.texte(ecran, "ARM", 10, theme.BRUME,
                          (r.right - 118, y - 1), "topleft", gras=True, ombre=False)
            widgets.barre_simple(ecran, (r.right - 86, y, 44, 9),
                                 min(1.0, d.j.armure / max(d.armure_max, 1)),
                                 theme.ARMURE_HAUT, theme.ARMURE_BAS, (20, 20, 36), 4)
            widgets.texte(ecran, str(max(d.j.armure, 0)), 11, theme.ARMURE_HAUT,
                          (r.right - 12, y - 2), "topright", ombre=False)

            # pastilles d'etat
            ex = r.x + 12
            for icone, coul, libelle, tours in d.effets()[:5]:
                rr = widgets.puce_effet(ecran, (ex, r.y + 110), icone, coul,
                                        libelle, tours)
                ex += rr.w + 6

    def _barre(self, ecran, barre, rect, libelle, c1, c2, valeur, petit=False):
        r = pygame.Rect(rect)
        barre.dessiner(ecran, r, c1, c2)
        taille = 11 if petit else 13
        # le libelle reste lisible meme quand la barre est vide
        plein = barre.affiche / max(barre.maxi, 1) > 0.12
        widgets.texte(ecran, libelle, taille - 1,
                      (10, 10, 22) if plein else theme.BRUME,
                      (r.x + 7, r.centery), "midleft", gras=True, ombre=False)
        widgets.texte(ecran, str(max(int(valeur), 0)), taille, theme.TEXTE,
                      (r.right - 8, r.centery), "midright", gras=True)

    # ---- banniere de tour
    def _dessiner_banniere(self, ecran, t):
        k = ease_out(self.banniere)
        r = pygame.Rect(0, 0, 330, 66)
        r.center = (theme.LARGEUR // 2, int(48 + (1 - k) * -44))
        widgets.panneau(ecran, r, int(170 * k), theme.OR_SOMBRE, 16, theme.ENCRE, 1)
        widgets.texte(ecran, "TOUR %d" % self.tour, 23, theme.OR,
                      (r.centerx, r.y + 9), "midtop", gras=True, espacement=4,
                      alpha=int(255 * k), titre=True)
        nom = self.combattants[self.actif].pseudo
        widgets.texte(ecran, "au tour de %s" % nom, 13, theme.TEXTE_DOUX,
                      (r.centerx, r.bottom - 15), "center", alpha=int(255 * k),
                      ombre=False)

    # ---- bas de l'ecran
    def _dessiner_bas(self, ecran, t):
        widgets.panneau(ecran, PANNEAU_BAS, 196, (52, 54, 88), 20, theme.ENCRE, 1)

        # journal
        widgets.texte(ecran, "JOURNAL DU COMBAT", 12, theme.OR,
                      (ZONE_JOURNAL.x, ZONE_JOURNAL.y), "topleft", gras=True,
                      espacement=4, ombre=False)
        pygame.draw.line(ecran, (58, 60, 92), (ZONE_JOURNAL.x, ZONE_JOURNAL.y + 20),
                         (ZONE_JOURNAL.right, ZONE_JOURNAL.y + 20), 1)
        debut = ZONE_JOURNAL.y + 30
        pas = 21
        maxi = max(1, (ZONE_JOURNAL.bottom - debut) // pas)
        # on remplit depuis la ligne la plus recente vers le haut
        rendu = []
        for txt, coul, appar in reversed(self.journal):
            morceaux = widgets.envelopper(txt, 14, ZONE_JOURNAL.w - 16)[:2]
            for l in reversed(morceaux):
                rendu.append((l, coul, appar))
            if len(rendu) >= maxi:
                break
        rendu = list(reversed(rendu[:maxi]))
        n = len(rendu)
        for i, (l, coul, appar) in enumerate(rendu):
            alpha = int(255 * (0.4 + 0.6 * ((i + 1) / n)) * appar)
            widgets.texte(ecran, l, 14, coul, (ZONE_JOURNAL.x + 8, debut + i * pas),
                          "topleft", ombre=False, alpha=alpha)
        # actions
        actif = self.combattants[self.actif]
        accent = theme.CLASSES[actif.classe]["accent"]
        widgets.texte(ecran, "ACTIONS DE %s" % actif.pseudo.upper(), 12, accent,
                      (ZONE_ACTIONS.x, ZONE_ACTIONS.y), "topleft", gras=True,
                      espacement=4, ombre=False)
        pygame.draw.line(ecran, (58, 60, 92), (ZONE_ACTIONS.x, ZONE_ACTIONS.y + 20),
                         (ZONE_ACTIONS.right, ZONE_ACTIONS.y + 20), 1)

        choix_actif = self.phase == "choix"
        souris = pygame.mouse.get_pos()
        for i, comp in enumerate(actif.competences):
            etat = actif.etat(comp)
            c = dict(comp)
            c["_tours"] = actif.tours_restants(comp)
            r = self._rect_bouton(i)
            survol = r.collidepoint(souris) and choix_actif
            widgets.bouton_competence(ecran, r, c, etat, accent, survol,
                                      choix_actif and i == self.index_sel)
        if not choix_actif:
            voile = pygame.Surface((ZONE_ACTIONS.w, ZONE_ACTIONS.h - 26),
                                   pygame.SRCALPHA)
            voile.fill((10, 10, 22, 130))
            ecran.blit(voile, (ZONE_ACTIONS.x, ZONE_ACTIONS.y + 26))
        else:
            # description de la competence survolee
            comp = actif.competences[self.index_sel]
            widgets.texte(ecran, comp["desc"], 13, theme.TEXTE_DOUX,
                          (ZONE_ACTIONS.centerx, PANNEAU_BAS.bottom - 16),
                          "center", ombre=False)


_MOTS = [
    ("critique", theme.OR),
    ("poison", theme.VERT_POISON),
    ("brul", theme.ORANGE),
    ("brûl", theme.ORANGE),
    ("contre-attaque", theme.BLEU),
    ("camouflage", theme.VIOLET),
    ("intouchable", theme.VIOLET),
    ("rage", theme.ORANGE),
    ("recupere", theme.VERT),
    ("récup", theme.VERT),
    ("soin", theme.VERT),
    ("armure", theme.ARMURE_HAUT),
    ("degats infliges", theme.ROUGE),
    ("dégats infligés", theme.ROUGE),
    ("dégâts", theme.ROUGE),
    ("mana", theme.MANA_HAUT),
    ("froid", theme.BLEU_GLACE),
]


def _couleur_ligne(txt):
    bas = txt.lower()
    for mot, coul in _MOTS:
        if mot in bas:
            return coul
    return theme.TEXTE_DOUX
