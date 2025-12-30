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

2. Extraction OCR (OpenAI Vision API - GPT-4o-mini) - 1 fois
   ├─ Image 1 → Texte français extrait
   └─ Image 2 → Texte français extrait

3. Traduction (OpenAI - GPT-4o-mini) - 1 fois
   ├─ Texte 1 → Traduction anglaise littérale
   └─ Texte 2 → Traduction anglaise littérale

4. Génération explication (OpenAI - GPT-4o-mini) - 1 fois
   └─ Expression OU Mot → Explication pédagogique en anglais
      (prompt adapté selon le type)

5. Génération multi-subreddit - 3 fois
   ├─ Sélection de 3 PS aléatoires différents
   ├─ Création de 3 liens Ablink uniques (API)
   └─ Génération de 3 fichiers HTML (1 par subreddit)

6. Output
   └─ 3 fichiers HTML : {expression}-{date}-r-{subreddit}.html
```

## Fichiers du projet

### `generate.py`
Script principal contenant toute la logique :

**Fonctions principales :**
- `slugify(text)` : Convertit texte en slug pour noms de fichiers
- `extract_subtitle_from_image(image_path)` : OCR via OpenAI Vision
- `translate_subtitle(subtitle_french)` : Traduction FR → EN
- `generate_explanation(text, is_expression=True)` : Génère explication pédagogique (adapte le prompt selon le type)
- `create_short_link(title)` : Crée lien raccourci via API Ablink
- `generate_html(...)` : Crée le HTML final avec CSS
- `main()` : Orchestration du workflow complet (génère 3 fichiers par exécution)

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

### Modèle utilisé
**GPT-4o-mini** pour toutes les opérations :
- OCR (extraction de texte)
- Traduction
- Génération d'explications

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

## Structure HTML générée

### Layout
1. **Titre** (Fira Mono 48px, fond gris #e0e0e0)
   - Format : "What does "{expression}" mean here?"

2. **Image 1** (max-width: 1124px)

3. **Traduction 1** (Inter 34px, fond noir #212121, texte blanc)

4. **Image 2** (max-width: 1124px)

5. **Traduction 2** (Inter 34px, fond noir #212121, texte blanc)

6. **Footer** (Fira Mono 34px, fond gris #e0e0e0)
   - Texte : "(Open the post to reveal the explanation)"

7. **Explication + PS + Lien + Subreddit** (Inter 16px, fond blanc, texte noir, aligné à gauche)
   - Explication pédagogique
   - PS promotionnel (choisi aléatoirement, différent pour chaque subreddit)
   - Lien raccourci Ablink unique
   - Nom du subreddit (pour identification)

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
**3 fichiers HTML** générés par commande, format : `{text-slug}-{date}-r-{subreddit}.html`

Exemples pour `--expression "en déplacement"` :
- `en-deplacement-2025-12-30-r-frenchimmersion.html`
- `en-deplacement-2025-12-30-r-learningfrench.html`
- `en-deplacement-2025-12-30-r-learnfrench.html`

Chaque fichier contient :
- Même explication/traductions/OCR
- PS différent (3 PS aléatoires sans répétition)
- Lien Ablink unique (titre: "{expression} - r/{subreddit}")

## Gestion d'erreurs

Le script s'arrête proprement avec des messages clairs dans ces cas :
- Clé API OpenAI manquante ou invalide
- Image introuvable ou corrompue
- Échec de l'API OpenAI (rate limit, erreur réseau, etc.)
- Aucun texte détecté par l'OCR

**Gestion gracieuse pour API Ablink :** Si l'API échoue, affiche "Error: Unable to generate link" au lieu du lien, mais continue la génération du HTML.

## Coûts estimés

**Par génération (3 fichiers HTML) :**
- 2 appels Vision API (OCR) : ~$0.0003
- 2 appels traduction : ~$0.0001
- 1 appel explication : ~$0.0001
- 3 appels API Ablink : gratuit

**Total : ~$0.0005** (moins d'un centime pour 3 posts)

## Fichiers exclus du repo (.gitignore)

- `.env` : Contient les clés API (OpenAI + Ablink)
- `*.html` : Fichiers HTML générés
- `test_*.png` : Images de test
- `__pycache__/` : Cache Python
- `.DS_Store` : Fichiers macOS

## Subreddits cibles

3 subreddits configurés (génération automatique de 3 fichiers HTML) :
- `r/FrenchImmersion`
- `r/learningfrench`
- `r/learnfrench`

## Évolutions futures possibles

### Idées
- [ ] Mode batch : traiter plusieurs expressions d'un coup
- [ ] Export direct en PNG (screenshot automatique du HTML)
- [ ] Support de plusieurs langues cibles
- [ ] Interface CLI interactive
- [ ] Validation automatique de la qualité de l'OCR

## Notes de développement

### Historique des versions
- **V1** : Génération HTML manuelle avec traductions manuelles
- **V2** : Ajout traduction automatique via OpenAI
- **V3** : Remplacement Tesseract par OpenAI Vision
- **V3.1** : Génération automatique des explications
- **V4** : Temperature=0 + différenciation expressions/mots + prompts optimisés
- **V5** : Génération multi-subreddit (3 fichiers) + intégration API Ablink pour liens uniques + PS aléatoires

### Choix techniques importants
- **OpenAI Vision plutôt que Tesseract** : Meilleure gestion des sous-titres stylisés
- **GPT-4o-mini plutôt que GPT-4o** : 100x moins cher, qualité suffisante
- **Temperature=0** : Résultats déterministes et consistants
- **3 fichiers HTML par génération** : Anti-ban Reddit (liens + PS différents par subreddit)
- **API Ablink** : Tracking des performances + liens uniques
- **9 variations de PS** : Sélection aléatoire de 3 différents pour maximiser la variété
- **Gestion d'erreur gracieuse pour Ablink** : Continue sans lien si API échoue

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
