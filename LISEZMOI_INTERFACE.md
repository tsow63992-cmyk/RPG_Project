# Interface graphique 2D (pygame)

Une interface façon JRPG 16 bits posée par-dessus le jeu de combat existant.

## Lancer

```bash
pip install pygame        # une seule fois
python3 jeu.py            # ou : python3 jeu.py --plein-ecran
```

La version console d'origine reste intacte et fonctionne toujours :

```bash
python3 combat_manager.py
```

## Le moteur d'origine n'a pas été touché

`player.py`, `assassin.py`, `barbare.py`, `chevalier.py`, `mage.py` et
`combat_manager.py` sont **exactement** les fichiers du dépôt. L'interface les
importe et appelle leurs méthodes telles quelles :

- les dégâts, soins, cooldowns et effets viennent uniquement du code d'origine ;
- les `print()` du jeu sont capturés (`contextlib.redirect_stdout`) et
  réaffichés dans le journal de combat, avec une couleur selon le contenu ;
- les coûts en mana et les temps de recharge affichés sont ceux de
  `combat_manager.py` ;
- les nombres de dégâts affichés à l'écran sont mesurés sur les PV et l'armure
  réellement perdus, donc ils tiennent compte des passifs (peau endurcie du
  barbare, provocation du chevalier, froid du mage...).

La seule logique ajoutée est celle que `combat_manager.py` déléguait au joueur :
l'enchaînement des tours, la condition de victoire, et le fait qu'une compétence
gratuite reste utilisable même si le Drain du mage a rendu le mana négatif.

## Ce que contient l'interface

| Fichier | Rôle |
|---|---|
| `jeu.py` | point d'entrée |
| `interface/theme.py` | palette, polices, fiches des 4 classes |
| `interface/sprites.py` | pixel-art des combattants et icônes, dessinés en code |
| `interface/decor.py` | décor nocturne procédural (lune, montagnes, forêt, rivière, lucioles) |
| `interface/fx.py` | particules, nombres flottants, ondes, éclairs, entailles |
| `interface/widgets.py` | panneaux de verre, barres animées, boutons |
| `interface/bridge.py` | pont vers le moteur de jeu d'origine |
| `interface/ecran_*.py` | écran titre, choix des classes, combat, victoire |

Aucun fichier image ou son n'est nécessaire : tout est généré par le code, donc
le dossier reste léger et rien ne peut manquer à l'exécution.

## Commandes

| Écran | Touches |
|---|---|
| Titre | n'importe quelle touche pour commencer |
| Pseudo | taper, `Entrée` pour valider (vide = pseudo par défaut) |
| Classes | `←` `→` ou la souris, `Entrée` pour confirmer |
| Combat | `1`–`7` pour lancer une compétence, flèches + `Entrée`, ou la souris |
| Victoire | `Entrée` pour un nouveau duel, `Échap` pour quitter |
| Partout | `F11` plein écran, `Échap` quitter |

## Détails d'affichage

- Barre de vie avec traînée rouge qui rattrape les dégâts, pastilles d'état
  (poison, brûlure, froid, rage, camouflage, contre, armure magique, affinité).
- Une animation différente par famille de compétence : entaille d'épée, bulles
  de poison, gerbe de feu, éclats de glace, éclair qui tombe du ciel, spirale
  de drain, étincelles de soin, bouclier.
- Coups critiques : nombre doré agrandi, flash d'écran et secousse de caméra.
- Camouflage : le sprite devient translucide ; à la mort, le perdant bascule au sol.
- Aucun emoji n'est utilisé : toutes les icônes sont dessinées, donc pas de
  carrés vides selon la police du système.
