# Documentation Projet - Générateur de Posts Reddit

## Vue d'ensemble

Ce projet génère automatiquement des posts Reddit éducatifs pour l'apprentissage du français :
- **Vocabulaire** (`generate.py`) : Posts avec captures d'écran de films/séries
- **Grammaire** (`generate_grammar.py`) : Quiz grammaticaux générés par IA
- **Humour** (`generate_humor.py`) : Mèmes français avec explications pédagogiques

## Architecture

### Workflow complet

```
1. Input utilisateur
   ├─ Expression française OU mot français (ex: "en déplacement" ou "manger")
   ├─ Image 1 (capture d'écran avec sous-titres + titre film)
   └─ Image 2 (capture d'écran avec sous-titres + titre film)

2. Extraction titres films (GPT-4o-mini Vision) - 1 fois
   ├─ Image 1 → Titre film extrait (ex: "La cage dorée (2013)")
   └─ Image 2 → Titre film extrait

3. Extraction sous-titres OCR (GPT-4o-mini) - 1 fois
   ├─ Image 1 → Texte français extrait
   └─ Image 2 → Texte français extrait

4. Traduction (GPT-4o-mini) - 1 fois
   ├─ Texte 1 → Traduction anglaise naturelle
   └─ Texte 2 → Traduction anglaise naturelle

5. Cachage (GPT-4o) - 1 fois
   ├─ Traduction 1 → Version cachée avec underscores
   └─ Traduction 2 → Version cachée avec underscores

6. Génération explication (GPT-4o-mini) - 1 fois
   └─ Expression OU Mot → Explication pédagogique en anglais

7. Rognage images - 1 fois
   ├─ Image 1 → Rognage 40px du bas (enlève titre + "Download video")
   └─ Image 2 → Rognage 40px du bas

8. Génération fichier unique dynamique - 1 fois
   ├─ Sélection de 4 PS aléatoires différents
   ├─ Création de 4 liens Ablink uniques (API)
   ├─ Conversion PS en Markdown links [texte](url)
   └─ Génération de 1 fichier HTML avec JavaScript pour gestion multi-subreddit

9. Output
   └─ 1 fichier HTML dans posts/ : {expression}-{date}.html
      - Interface dynamique avec localStorage (état + selectedSubredditIndex)
      - Sélection manuelle subreddit (clic label → surlignage + change PS)
      - Checkboxes indépendantes (tracking visuel, togglables)
      - 2 sections (visible + cachée) éditables inline
      - Images rognées et stockées dans img/
      - Overlays titre film (coin haut-droit, 8px Fira Mono, 5px padding, fond #212121)
```

## Fichiers du projet

### `generate.py` (Vocabulaire)
Script posts vocabulaire avec captures d'écran :

**Fonctions principales :**
- `slugify(text)` : Convertit texte en slug pour noms de fichiers
- `extract_movie_title(image_path)` : Extrait titre film en bas-droit via OpenAI Vision (GPT-4o-mini)
- `extract_subtitle_from_image(image_path)` : OCR sous-titres via OpenAI Vision (GPT-4o-mini)
- `crop_image_bottom(image_path, output_path, pixels_to_remove=40)` : Rogne image (Pillow)
- `translate_subtitle(subtitle_french)` : Traduction FR → EN littérale (GPT-4o-mini) [obsolète, conservée]
- `translate_subtitle_natural(subtitle_french)` : Traduction FR → EN naturelle (GPT-4o-mini) [utilisée]
- `hide_text_in_translation(translation_en, subtitle_fr, text, is_expression)` : Cache mot/expression avec underscores (GPT-4o)
- `generate_explanation(text, is_expression=True)` : Génère explication pédagogique (GPT-4o-mini)
- `bold_first_sentence(text)` : Met en gras première phrase de l'explication
- `convert_ps_to_markdown_link(ps_text, link_url)` : Convertit [texte] en [texte](url) Markdown
- `create_short_link(title)` : Crée lien raccourci via API Ablink
- `generate_html(...)` : Crée HTML dynamique avec overlays titres films, JavaScript, localStorage
- `main()` : Orchestration complète (génère 1 fichier unique)

**Format** : Message promo subreddit automatique r/FrenchVocab (PS/PS-2)

### `generate_grammar.py` (Grammaire)
Script posts grammaire avec quiz interactif :

**Workflow** :
1. Propose règle de grammaire aléatoire (GPT-4o, temp=1.2)
2. Génère 3 options (1 correcte, 2 incorrectes)
3. Chat interactif : validation/modification de la description
4. Génère HTML avec image quiz unique (540x540px)

**Fonctions principales** :
- `propose_grammar_rule()` : Génère règle + 3 options via GPT-4o
- `generate_explanation(rule_data)` : Explication pédagogique (GPT-4o-mini)
- `modify_explanation(explanation, instruction)` : Itération sur description
- `create_short_link(title, test_mode)` : Liens Ablink (skip si --test)
- `generate_html(rule_data, explanation, test_mode)` : HTML avec tracker 4 subreddits

**Commandes** :
```bash
python3 generate_grammar.py          # Mode normal (crée liens Ablink)
python3 generate_grammar.py --test   # Mode test (liens factices)
```

**Subreddits** : FrenchImmersion, FrenchGrammar, learnfrench, learningfrench

**Format** : max-width 700px, message promo subreddit automatique (PS/PS-2)

### `generate_humor.py` (Humour)
Script posts humour avec mèmes français :

**Workflow** :
1. Analyse image mème (GPT-4o Vision)
2. Génère description : Translation, Why is this funny, Vocabulary (optionnel), Context (optionnel)
3. Chat interactif : validation/modification
4. Génère HTML avec image + description éditable

**Fonctions principales** :
- `analyze_meme(image_path)` : Analyse mème via GPT-4o Vision
- `modify_description(description, instruction)` : Modification interactive
- `create_short_link(title, test_mode)` : Liens Ablink (skip si --test)
- `generate_html(description, image_filename, date_str, title_slug, title_display, test_mode)` : HTML tracker 4 subreddits

**Commandes** :
```bash
python3 generate_humor.py --image meme.png          # Mode normal
python3 generate_humor.py --image meme.png --test   # Mode test
```

**Subreddits** : FrenchImmersion, learnfrench, learningfrench, LearnFrenchWithHumor

**Format** : Titres en **gras** (markdown), max-width 700px, titre auto-rempli, message promo subreddit automatique (PS/PS-2)

### `requirements.txt`
Dépendances Python :
- `openai>=1.0.0` : SDK OpenAI pour Vision API et traductions
- `python-dotenv>=1.0.0` : Gestion des variables d'environnement
- `requests>=2.31.0` : Appels HTTP pour API Ablink
- `Pillow>=10.0.0` : Traitement d'images (rognage)

### `.env` (non versionné)
Contient les clés API :
```
OPENAI_API_KEY=sk-proj-...
ABLINK_API_KEY=...
```

### `.env.example`
Template pour la configuration. À copier en `.env` et remplir avec les vraies clés API.

### `README.md`
Documentation utilisateur avec instructions d'installation et d'utilisation.

## Configuration OpenAI

### Modèles utilisés
**Vocabulaire (`generate.py`)** :
- **GPT-4o-mini** : OCR, traduction, explication (économique)
- **GPT-4o** : Cachage des traductions (précision requise)

**Grammaire (`generate_grammar.py`)** :
- **GPT-4o** : Génération règles (variété + créativité, temp=1.2)
- **GPT-4o-mini** : Explications pédagogiques (temp=0)

**Humour (`generate_humor.py`)** :
- **GPT-4o** : Analyse mème Vision + génération description (temp=0)

### Prompts système

**Extraction titre film :**
```
"Extract ONLY the movie title visible in the bottom right corner of this image.
The format should be: Movie Name (Year). Respond only with the title, without any comments or explanation."
```

**Extraction sous-titres OCR :**
```
"Extrait UNIQUEMENT le texte français des sous-titres visibles dans cette image.
Réponds uniquement avec le texte extrait, sans aucun commentaire ni explication."
```

**Traduction naturelle (avec temperature=0) :**
```
User: "Traduis cette phrase en anglais de manière naturelle et correcte.

Réponds uniquement avec la traduction, sans guillemets ni explication.

Phrase à traduire : {texte}"
```

**Traduction littérale [obsolète, conservée dans le code] :**
```
Prompt mot-à-mot avec structure similaire. Non utilisé actuellement.
```

**Explication - EXPRESSION (avec temperature=0) :**
```
System: "Ne fais pas de mise en forme dans ta réponse."
User: Prompt détaillé incluant :
- Traduction des mots rares
- Définition plutôt que traduction pour certains mots
- 2 exemples d'usage
- Structure imposée : signification → mots rares → exemples
```

**Explication - MOT (avec temperature=0) :**
```
System: "Ne fais pas de mise en forme dans ta réponse."
User: Prompt simplifié incluant :
- Définition du mot
- 2 exemples d'usage
- Structure imposée : signification → exemples
```

**Cachage (GPT-4o, temperature=0) :**
```
Prompt en 2 étapes :
1. Reçoit : sous-titre FR + traduction EN + texte à cacher
2. Identifie la partie EN correspondante au texte FR
3. Remplace chaque lettre/espace par underscore "_"
4. Renvoie uniquement la traduction avec underscores

Exemples intégrés au prompt pour guidance (80% taux de succès)
```

## Structure HTML générée

### Layout (ordre d'affichage)

**Interface dynamique avec état persistant (localStorage) :**
1. Lien subreddit cliquable (URL complète) + bouton "📋 Copier le lien"
2. Titre post dynamique "Learn French: what does "[expression/mot]" mean here?" (Inter 32px gras)
3. Bouton "📋 Copier le titre" pour copie rapide du titre Reddit
4. Section 1 - Version visible (traductions éditables inline)
5. Section 2 - Version cachée (traductions éditables inline)
6. Explication éditable + PS dynamique + "Happy learning!" + bouton copier
7. Tracker publication : 4 labels cliquables + 4 checkboxes togglables

**Zones éditables (contenteditable="true") :**
- 4 traductions (2 visibles + 2 cachées) avec feedback visuel (bleu au focus)
- Explication complète
- Modifications auto-sauvegardées dans localStorage

**Fonctionnalités JavaScript :**
- Clé localStorage : `reddit-post-{expression}-{date}` (state: published[], selectedSubredditIndex, editedContent)
- Clic label subreddit → Sélectionne (surlignage bleu) + Change lien + PS
- Checkbox → Toggle tracking visuel (indépendant de sélection)
- Auto-sélection prochain non-coché si subreddit sélectionné coché
- Bouton "📋 Copier le lien" copie URL subreddit (workflow fluide vers Reddit)
- Bouton "📋 Copier le titre" copie le titre pour Reddit
- Bouton "📋 Copier Explication + PS" copie : Explication + PS + "Happy learning!" avec feedback
- Ordre subreddits fixe : FrenchImmersion → FrenchVocab → learnfrench → learningfrench

### Polices utilisées
- **Fira Mono** (Regular 400) : Titre et footer
- **Inter** (Regular 400) : Traductions et explication

Chargées via Google Fonts.

## Utilisation

### Installation
```bash
pip3 install -r requirements.txt
cp .env.example .env
# Éditer .env : OPENAI_API_KEY + ABLINK_API_KEY
```

### Vocabulaire (generate.py)

**Expression :**
```bash
python3 generate.py --expression "en déplacement" --image1 scene1.png --image2 scene2.png
```

**Mot :**
```bash
python3 generate.py --mot "manger" --image1 scene1.png --image2 scene2.png
```

### Grammaire (generate_grammar.py)

**Mode normal :**
```bash
python3 generate_grammar.py
# Chat interactif : propose règles → valide → génère HTML
# Output : posts/grammar/{rule}-{date}.html
```

**Mode test (sans liens Ablink) :**
```bash
python3 generate_grammar.py --test
```

### Humour (generate_humor.py)

**Mode normal :**
```bash
python3 generate_humor.py --image meme.png
# Analyse image → valide/modifie → saisit titre → génère HTML
# Output : posts/humor/{titre}-{date}.html + img/humor/{titre}-{date}.png
```

**Mode test :**
```bash
python3 generate_humor.py --image meme.png --test
```

### Output

**Vocabulaire** :
- `posts/{expression}-{date}.html`
- `img/{expression}-{date}-scene1.png` (40px enlevés)
- Interface : 2 sections (visible/cachée), tracker 4 subreddits, promo r/FrenchVocab

**Grammaire** :
- `posts/grammar/{rule}-{date}.html`
- Interface : 1 image quiz (540x540px, 3 options centrées), tracker 4 subreddits, promo r/FrenchGrammar, max-width 700px

**Humour** :
- `posts/humor/{titre}-{date}.html`
- `img/humor/{titre}-{date}.png`
- Interface : 1 image mème, description éditable, tracker 4 subreddits, promo r/LearnFrenchWithHumor, max-width 700px

## Gestion d'erreurs

Le script s'arrête proprement avec des messages clairs dans ces cas :
- Clé API OpenAI manquante ou invalide
- Image introuvable ou corrompue
- Échec de l'API OpenAI (rate limit, erreur réseau, etc.)
- Aucun texte détecté par l'OCR

**Gestion gracieuse pour API Ablink :** Si l'API échoue, affiche "Error: Unable to generate link" au lieu du lien, mais continue la génération du HTML.

## Coûts estimés

**Par génération (1 fichier HTML pour 4 subreddits) :**
- 2 OCR titres films (GPT-4o-mini) : ~$0.0003
- 2 OCR sous-titres (GPT-4o-mini) : ~$0.0003
- 2 traductions (GPT-4o-mini) : ~$0.0001
- 2 cachages (GPT-4o) : ~$0.001
- 1 explication (GPT-4o-mini) : ~$0.0001
- 4 liens Ablink : gratuit

**Total : ~$0.0018** (moins de 2 centimes par expression)

## Fichiers exclus du repo (.gitignore)

- `.env` : Contient les clés API (OpenAI + Ablink)
- `*.html` : Fichiers HTML générés
- `test_*.png` : Images de test
- `__pycache__/` : Cache Python
- `.DS_Store` : Fichiers macOS

## Subreddits cibles

4 subreddits configurés (ordre fixe dans l'interface) :
1. `r/FrenchImmersion`
2. `r/FrenchVocab`
3. `r/learnfrench`
4. `r/learningfrench`

## Évolutions futures possibles

### Idées
- [ ] Mode batch : traiter plusieurs expressions d'un coup
- [ ] Export direct en PNG (screenshot automatique du HTML)
- [ ] Support de plusieurs langues cibles
- [ ] Interface CLI interactive
- [ ] Validation automatique de la qualité de l'OCR

## Notes de développement

### Historique des versions
- **V1-V15** : Système multi-fichiers (4 HTML par génération)
- **V16** : Refonte complète - fichier HTML unique dynamique
  - Interface avec localStorage pour gérer 4 publications
  - Zones éditables inline (contenteditable) pour traductions + explication
  - Bouton "Copier Explication + PS" avec feedback visuel
  - Checkboxes désactivées après cochage
  - Mise à jour automatique subreddit + PS selon état
  - Clé localStorage : `reddit-post-{expression}-{date}`
- **V17** : Traductions naturelles par défaut
  - Ajout `translate_subtitle_natural()` pour traductions correctes en anglais
  - Fonction littérale conservée pour faciliter retour arrière si besoin
- **V18** : Repositionnement "Happy learning!"
  - "Happy learning!" placé après PS et avant bouton (meilleur format Reddit)
  - Bouton copie inclut maintenant : Explication + PS + "Happy learning!"
- **V19** : Sélection manuelle de subreddit + tracking indépendant
  - Clic sur nom subreddit → Sélection + surlignage (fond bleu #E3F2FD + bordure #1976D2)
  - Checkbox découplée → Tracking visuel uniquement, cochable/décochable librement
  - Persistance selectedSubredditIndex dans localStorage
  - Auto-sélection prochain non-coché si subreddit sélectionné est coché
  - Évite spam detection Reddit (rotation manuelle vs 4 posts simultanés/subreddit)
- **V20** : Crédits films automatiques avec overlays
  - Extraction automatique titres films via OCR (GPT-4o-mini Vision)
  - Rognage automatique images (40px du bas, enlève titre source + "Download video")
  - Overlays CSS : coin haut-droit, Fira Mono 8px, padding 5px, fond #212121 opaque
  - Crédits respectent droits d'auteur + intérêt pédagogique utilisateurs
  - Ajout dépendance Pillow pour traitement images
  - Fix espaces blancs : display block sur .image-container
- **V21** : Titre dynamique SEO-friendly
  - Nouveau format : "Learn French: what does "[expression/mot]" mean here?"
  - Remplace ancien "Your daily vocab' workout 🏋️ #" (répétitif, non SEO)
  - Bouton "📋 Copier le titre" pour copie rapide vers Reddit
  - Améliore trouvabilité Google et référencement naturel des posts
- **V22** : Workflow optimisé vers Reddit
  - Lien subreddit cliquable (URL complète) au lieu du nom seul
  - Bouton "📋 Copier le lien" pour copie directe de l'URL
  - Suppression automatique des images sources après rognage (racine propre)
  - Accès direct au subreddit sans manipulation manuelle d'URL

### Choix techniques importants
- **OpenAI Vision (GPT-4o-mini)** : OCR précis vs Tesseract (sous-titres + titres films)
- **GPT-4o** : Cachage uniquement (précision 80%)
- **Pillow** : Rognage images (40px, enlève titre source avant sauvegarde)
- **Traductions naturelles** : Anglais correct vs littéral (meilleure réception utilisateurs)
- **Temperature=0** : Résultats déterministes
- **Fichier unique dynamique** : Réduit duplication, facilite éditions
- **localStorage** : Persistance état sans serveur, clé unique expression+date
- **contenteditable** : Édition inline native, UX simple
- **Titre dynamique SEO** : Unique par expression/mot → indexation Google + trouvabilité
- **Lien subreddit cliquable** : URL complète affichée + bouton copie → accès direct Reddit
- **Bouton copie titre** : Un clic pour titre Reddit (évite sélection manuelle)
- **Bouton copie** : Un clic pour Explication + PS + "Happy learning!" (évite sélection manuelle)
- **Suppression auto images** : Images sources supprimées après rognage (racine propre)
- **"Happy learning!" après PS** : Format optimal pour post Reddit commentaire
- **Sélection manuelle subreddit** : Clic sur label → change PS, checkbox = tracking only
- **Checkboxes togglables** : Correction erreurs possible (cochable/décochable)
- **Markdown links** : [texte](url) pré-intégrés dans PS
- **9 variations PS** : Sélection aléatoire de 4 différents par génération
- **Ordre subreddits fixe** : FrenchImmersion → FrenchVocab → learnfrench → learningfrench
- **Rotation posts** : Évite spam Reddit (répartir publications sur différents subreddits)
- **Overlays films** : Crédits automatiques (droits d'auteur + engagement utilisateurs)
- **display: block** : Élimine espaces blancs entre images et blocs (vs inline-block)

## Support et maintenance

Pour toute modification du code :
1. Tester localement d'abord
2. Créer un commit Git avec message descriptif
3. Pousser sur GitHub pour backup

En cas de régression, utiliser Git pour revenir en arrière :
```bash
git log  # Voir l'historique
git checkout <commit-hash>  # Revenir à un commit précédent
```
