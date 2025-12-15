# Générateur de Posts Reddit - Apprentissage du Français

Script Python pour générer des posts Reddit éducatifs au format HTML avec OCR automatique et traduction via OpenAI.

## Installation

1. Installer Tesseract OCR (nécessaire pour l'OCR) :
```bash
brew install tesseract tesseract-lang
```

2. Installer les dépendances Python :
```bash
pip3 install -r requirements.txt
```

3. Configurer la clé API OpenAI :
```bash
cp .env.example .env
# Édite le fichier .env et remplace par ta vraie clé API OpenAI
```

## Utilisation

```bash
python3 generate.py \
  --expression "en déplacement" \
  --image1 scene1.png \
  --image2 scene2.png
```

## Inputs requis

1. **--expression** : Le mot ou l'expression française à faire deviner
2. **--image1** : Chemin vers la première capture d'écran (avec sous-titres français incrustés)
3. **--image2** : Chemin vers la deuxième capture d'écran (avec sous-titres français incrustés)

## Output

Le script génère un fichier HTML nommé : `{expression-slug}-{date}.html`

Exemple : `en-deplacement-2025-12-12.html`

## Workflow

1. Place tes deux captures d'écran dans le dossier du projet
2. Lance le script avec l'expression et les chemins vers les images
3. Le script extrait automatiquement les sous-titres via OCR (Tesseract)
4. Les sous-titres sont traduits automatiquement en anglais via OpenAI
5. Ouvre le fichier HTML généré dans ton navigateur
6. Prends un screenshot de la page
7. Poste le screenshot sur Reddit

## Comment ça marche

Le script :
1. Extrait le texte français des images via OCR (Tesseract, langue française)
2. Traduit littéralement les sous-titres en anglais via l'API OpenAI (modèle GPT-4o-mini)
3. Génère un fichier HTML avec le layout prédéfini

## Structure du HTML généré

Le HTML contient :
- Titre avec l'expression à deviner (Fira Mono, 48px)
- Première image
- Traduction du premier sous-titre (Inter, 34px, fond noir #212121)
- Deuxième image
- Traduction du deuxième sous-titre (Inter, 34px, fond noir #212121)
- Footer "(Open the post to reveal the explanation)" (Fira Mono, 34px)

## Notes

- Les images sont référencées par leur chemin, elles doivent rester dans le même dossier que le HTML
- Le HTML est responsive avec une largeur maximale de 1124px
- Les images gardent leur ratio d'aspect original
- L'OCR et les traductions sont générés automatiquement
- Pour de meilleurs résultats OCR, assure-toi que les sous-titres sont clairs et lisibles
