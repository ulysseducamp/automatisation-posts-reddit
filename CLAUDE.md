# Documentation Projet - Générateur de Posts Reddit

## Vue d'ensemble

Ce projet génère automatiquement des posts Reddit éducatifs pour l'apprentissage du français. Il utilise l'API OpenAI pour extraire le texte des images (OCR), traduire les sous-titres et générer des explications pédagogiques.

## Architecture

### Workflow complet

```
1. Input utilisateur
   ├─ Expression française OU mot français (ex: "en déplacement" ou "manger")
   ├─ Image 1 (capture d'écran avec sous-titres)
   └─ Image 2 (capture d'écran avec sous-titres)

2. Extraction OCR (GPT-4o-mini) - 1 fois
   ├─ Image 1 → Texte français extrait
   └─ Image 2 → Texte français extrait

3. Traduction (GPT-4o-mini) - 1 fois
   ├─ Texte 1 → Traduction anglaise littérale
   └─ Texte 2 → Traduction anglaise littérale

4. Cachage (GPT-4o) - 1 fois
   ├─ Traduction 1 → Version cachée avec underscores
   └─ Traduction 2 → Version cachée avec underscores

5. Génération explication (GPT-4o-mini) - 1 fois
   └─ Expression OU Mot → Explication pédagogique en anglais

6. Génération multi-subreddit - 4 fois
   ├─ Sélection de 4 PS aléatoires différents
   ├─ Création de 4 liens Ablink uniques (API)
   ├─ Conversion PS en Markdown links [texte](url)
   └─ Génération de 4 fichiers HTML (1 par subreddit, 2 sections par fichier)

7. Output
   └─ 4 fichiers HTML dans posts/ : {expression}-{date}-r-{subreddit}.html
      - Chaque fichier : 2 sections (visible + cachée) avec titres séparés
      - Images renommées et stockées dans img/
```

## Fichiers du projet

### `generate.py`
Script principal contenant toute la logique :

**Fonctions principales :**
- `slugify(text)` : Convertit texte en slug pour noms de fichiers
- `extract_subtitle_from_image(image_path)` : OCR via OpenAI Vision (GPT-4o-mini)
- `translate_subtitle(subtitle_french)` : Traduction FR → EN littérale (GPT-4o-mini)
- `hide_text_in_translation(translation_en, subtitle_fr, text, is_expression)` : Cache mot/expression avec underscores (GPT-4o)
- `generate_explanation(text, is_expression=True)` : Génère explication pédagogique (GPT-4o-mini)
- `bold_first_sentence(text)` : Met en gras première phrase de l'explication
- `convert_ps_to_markdown_link(ps_text, link_url)` : Convertit [texte] en [texte](url) Markdown
- `create_short_link(title)` : Crée lien raccourci via API Ablink
- `generate_html(...)` : Crée HTML avec 2 sections (visible + cachée)
- `main()` : Orchestration complète (génère 4 fichiers × 2 sections)

### `requirements.txt`
Dépendances Python :
- `openai>=1.0.0` : SDK OpenAI pour Vision API et traductions
- `python-dotenv>=1.0.0` : Gestion des variables d'environnement
- `requests>=2.31.0` : Appels HTTP pour API Ablink

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
- **GPT-4o-mini** : OCR, traduction, explication (économique)
- **GPT-4o** : Cachage des traductions (précision requise)

### Prompts système

**Extraction OCR :**
```
"Extrait UNIQUEMENT le texte français des sous-titres visibles dans cette image.
Réponds uniquement avec le texte extrait, sans aucun commentaire ni explication."
```

**Traduction (avec temperature=0) :**
```
User: "traduis cette phrase en anglais (littéralement)

dans ta réponse, écris uniquement la traduction, rien d'autre, pas d'explication,
juste la traduction. Ne mets pas de guillemets autour de la traduction.

Pour "Ça vous dérange pas la fumée"
une bonne traduction littérale est "It doesn't bother you the smoke."

L'idée c'est d'avoir une structure de phrase similaire avec à peu près les mêmes mots.

Phrase à traduire : {texte}"
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

**Ordre workflow-friendly :**
1. Nom subreddit (Inter 16px) - Pour savoir où publier
2. Titre post "Your daily vocab' workout 🏋️ #" (Inter 32px gras)
3. Section 1 - Version visible (avec titre propre)
4. Section 2 - Version cachée (avec titre propre)
5. Explication + PS + signature

**Chaque section (autonome pour screenshots) :**
- Titre "What does '{mot}' mean here?" (Fira Mono 24px, #e0e0e0)
- Images 1 & 2 (max-width: 562px, chemins relatifs ../img/)
- Traductions (Inter 17px, #212121, fond blanc)
- Footer "(Open...)" (Fira Mono 17px)

**Partie textuelle :**
- Explication (première phrase en gras via Markdown **)
- PS avec lien Markdown intégré [texte](url)
- Signature "Happy learning!"

### Polices utilisées
- **Fira Mono** (Regular 400) : Titre et footer
- **Inter** (Regular 400) : Traductions et explication

Chargées via Google Fonts.

## Utilisation

### Installation
```bash
# Installer les dépendances
pip3 install -r requirements.txt

# Configurer la clé API
cp .env.example .env
# Éditer .env et ajouter la vraie clé OpenAI
```

### Commande

**Pour une expression :**
```bash
python3 generate.py \
  --expression "en déplacement" \
  --image1 scene1.png \
  --image2 scene2.png
```

**Pour un mot :**
```bash
python3 generate.py \
  --mot "manger" \
  --image1 scene1.png \
  --image2 scene2.png
```

**Note :** Les arguments `--expression` et `--mot` sont mutuellement exclusifs (il faut utiliser l'un OU l'autre).

### Output
**4 fichiers HTML** dans `posts/`, format : `posts/{text-slug}-{date}-r-{subreddit}.html`

Exemples pour `--expression "en déplacement"` :
- `posts/en-deplacement-2026-01-03-r-frenchimmersion.html`
- `posts/en-deplacement-2026-01-03-r-learningfrench.html`
- `posts/en-deplacement-2026-01-03-r-learnfrench.html`
- `posts/en-deplacement-2026-01-03-r-frenchvocab.html`

**Images renommées** dans `img/` :
- `img/en-deplacement-2026-01-03-scene1.png`
- `img/en-deplacement-2026-01-03-scene2.png`

Chaque HTML contient :
- Nom subreddit + titre post (en haut pour workflow)
- Section 1 : Traductions complètes (avec titre)
- Section 2 : Traductions cachées (avec titre)
- Explication (1ère phrase gras) + PS Markdown + signature

## Gestion d'erreurs

Le script s'arrête proprement avec des messages clairs dans ces cas :
- Clé API OpenAI manquante ou invalide
- Image introuvable ou corrompue
- Échec de l'API OpenAI (rate limit, erreur réseau, etc.)
- Aucun texte détecté par l'OCR

**Gestion gracieuse pour API Ablink :** Si l'API échoue, affiche "Error: Unable to generate link" au lieu du lien, mais continue la génération du HTML.

## Coûts estimés

**Par génération (4 fichiers HTML × 2 sections) :**
- 2 OCR (GPT-4o-mini) : ~$0.0003
- 2 traductions (GPT-4o-mini) : ~$0.0001
- 2 cachages (GPT-4o) : ~$0.001
- 1 explication (GPT-4o-mini) : ~$0.0001
- 4 liens Ablink : gratuit

**Total : ~$0.0015** (moins de 2 centimes pour 4 posts)

## Fichiers exclus du repo (.gitignore)

- `.env` : Contient les clés API (OpenAI + Ablink)
- `*.html` : Fichiers HTML générés
- `test_*.png` : Images de test
- `__pycache__/` : Cache Python
- `.DS_Store` : Fichiers macOS

## Subreddits cibles

4 subreddits configurés (génération automatique de 4 fichiers HTML) :
- `r/FrenchImmersion`
- `r/learningfrench`
- `r/learnfrench`
- `r/FrenchVocab`

## Évolutions futures possibles

### Idées
- [ ] Mode batch : traiter plusieurs expressions d'un coup
- [ ] Export direct en PNG (screenshot automatique du HTML)
- [ ] Support de plusieurs langues cibles
- [ ] Interface CLI interactive
- [ ] Validation automatique de la qualité de l'OCR

## Notes de développement

### Historique des versions
- **V1-V6** : Versions initiales (traductions, OCR, cachage, multi-subreddit)
- **V7** : Images auto-renommées et organisées dans img/
- **V8** : Titre post Reddit ajouté au HTML
- **V9** : Réduction largeur HTML (562px) pour screenshots
- **V10** : Liens Markdown intégrés [texte](url) dans PS
- **V11** : Signature "Happy learning!" pour espacement
- **V12** : Première phrase en gras + cleanup imports
- **V13** : 4ème subreddit r/FrenchVocab ajouté
- **V14** : Organisation posts/ + ordre workflow-friendly
- **V15** : Titres dupliqués pour sections autonomes

### Choix techniques importants
- **OpenAI Vision (GPT-4o-mini)** : OCR précis vs Tesseract
- **GPT-4o** : Cachage uniquement (précision 80%)
- **Temperature=0** : Résultats déterministes
- **2 sections autonomes** : Chaque section a son titre pour screenshots séparés
- **4 fichiers/génération** : Anti-ban Reddit (4 subreddits, liens + PS uniques)
- **Markdown links** : [texte](url) intégré dans PS pour copier-coller direct
- **Organisation dossiers** : posts/ (HTML) + img/ (images renommées)
- **Workflow-friendly** : Ordre HTML = ordre workflow (subreddit → titre → images → explication)
- **9 variations PS** : Sélection aléatoire de 4 différents
- **Première phrase gras** : Améliore lisibilité explication

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
