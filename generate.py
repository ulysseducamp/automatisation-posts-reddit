#!/usr/bin/env python3
"""
Script pour générer des posts Reddit HTML pour l'apprentissage du français.
Usage: python generate.py --expression "..." --image1 ... --image2 ...
"""

import argparse
from datetime import datetime
import json
import re
import os
import sys
import base64
import random
import requests
import shutil
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

# Charger les variables d'environnement depuis .env
load_dotenv()

# Variations de post-scriptum promotionnel (choisi aléatoirement)
PS_VARIATIONS = [
    "PS: If you watch Netflix on your computer and want to support this post, you can check [this tool] that I made.    ",
    "PS: If you like watching Netflix and sometimes hesitate between putting the subtitles in French or in your native language, I made a [little tool] that solves this problem",
    "PS: if you like watching French content on Netflix and sometimes hesitate between putting the subtitles in French or in your native language, I made a little tool called Subly that adjusts the subtitles to your level. If you want to support this post and if you think that this tool could be useful, feel free give it a try by [clicking here] ;)",
    "PS: if you like watching French content on Netflix and sometimes hesitate between putting the subtitles in French or in your native language, I made a little tool called Subly that I would recommend to use. This extension adjusts the subtitles to your level (if a subtitle is adapted to your level, it displays it in French, if a subtitle is too hard, it displays it in your native language). I use it to learn Portuguese, it provides a good balance between practicing your target language and enjoying the show. Here is [the link to try it].",
    "How to support these posts: check out [this tool] that I made to learn French with Netflix.",
    "If you want to improve your French while watching Netflix, here is a [simple tool] I made that decides if a subtitle should be displayed in French or in your Native language based on your level.",
    "Quick note: If you watch Netflix on your computer, I built a [simple tool] that shows subtitles in French only when the words are familiar to you, otherwise it switches to your native language.",
    "PS: If you're a Netflix user, I made a [simple tool] that automatically chooses between French and native subtitles depending on the vocabulary you know.",
    "PS: If you want to learn dozens of new words every time you watch a Netflix show, you can [try my tool called Subly]."
]


def slugify(text):
    """Convertit un texte en slug (minuscules, espaces -> tirets)"""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def extract_subtitle_from_image(image_path):
    """Extrait le texte d'une image via OpenAI Vision API"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    try:
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            print(f"❌ Erreur : Image introuvable : {image_path}")
            sys.exit(1)

        # Encoder l'image en base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Appel API OpenAI avec vision
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extrait UNIQUEMENT le texte français des sous-titres visibles dans cette image. Réponds uniquement avec le texte extrait, sans aucun commentaire ni explication."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )

        text = response.choices[0].message.content.strip()

        # Nettoyer les guillemets si présents
        text = text.strip('"').strip("'")

        # Vérifier que du texte a été détecté
        if not text:
            print(f"❌ Erreur : Aucun texte détecté dans l'image {image_path}")
            print("   Vérifie que l'image contient des sous-titres lisibles.")
            sys.exit(1)

        return text

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction du texte de {image_path} : {e}")
        sys.exit(1)


def extract_movie_title(image_path):
    """Extrait le titre du film visible en bas de l'image via OpenAI Vision API"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    try:
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            print(f"❌ Erreur : Image introuvable : {image_path}")
            sys.exit(1)

        # Encoder l'image en base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Appel API OpenAI avec vision
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract ONLY the movie title visible in the bottom right corner of this image. The format should be: Movie Name (Year). Respond only with the title, without any comments or explanation."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )

        title = response.choices[0].message.content.strip()

        # Nettoyer les guillemets si présents
        title = title.strip('"').strip("'")

        # Vérifier qu'un titre a été détecté
        if not title:
            print(f"⚠️  Attention : Aucun titre de film détecté dans {image_path}")
            return "Unknown Movie"

        return title

    except Exception as e:
        print(f"⚠️  Attention : Erreur lors de l'extraction du titre de {image_path} : {e}")
        return "Unknown Movie"


def crop_image_bottom(image_path, output_path, pixels_to_remove=50):
    """Rogne une image en enlevant les pixels du bas"""
    try:
        # Ouvrir l'image
        img = Image.open(image_path)
        width, height = img.size

        # Vérifier que le rognage est possible
        if pixels_to_remove >= height:
            print(f"⚠️  Attention : Impossible de rogner {pixels_to_remove}px sur une image de {height}px de hauteur")
            # Copier l'image telle quelle
            shutil.copy(image_path, output_path)
            return

        # Rogner l'image (enlever du bas)
        cropped = img.crop((0, 0, width, height - pixels_to_remove))

        # Sauvegarder l'image rognée
        cropped.save(output_path)

    except Exception as e:
        print(f"❌ Erreur lors du rognage de {image_path} : {e}")
        # En cas d'erreur, copier l'image telle quelle
        shutil.copy(image_path, output_path)


def translate_subtitle(subtitle_french):
    """Traduit un sous-titre français en anglais littéralement via OpenAI API"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "user", "content": f"""traduis cette phrase en anglais (littéralement)

dans ta réponse, écris uniquement la traduction, rien d'autre, pas d'explication, juste la traduction. Ne mets pas de guillemets autour de la traduction.

Pour "Ça vous dérange pas la fumée"

une bonne traduction littérale est "It doesn't bother you the smoke."

L'idée c'est d'avoir une structure de phrase similaire avec à peu près les mêmes mots.

Phrase à traduire : {subtitle_french}"""}
            ]
        )
        translation = response.choices[0].message.content.strip()
        # Nettoyer les guillemets si présents
        translation = translation.strip('"').strip("'")
        return translation

    except Exception as e:
        print(f"❌ Erreur lors de l'appel API OpenAI : {e}")
        sys.exit(1)


def translate_subtitle_natural(subtitle_french):
    """Traduit un sous-titre français en anglais naturellement via OpenAI API"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "user", "content": f"""Traduis cette phrase en anglais de manière naturelle et correcte.

Réponds uniquement avec la traduction, sans guillemets ni explication.

Phrase à traduire : {subtitle_french}"""}
            ]
        )
        translation = response.choices[0].message.content.strip()
        # Nettoyer les guillemets si présents
        translation = translation.strip('"').strip("'")
        return translation

    except Exception as e:
        print(f"❌ Erreur lors de l'appel API OpenAI : {e}")
        sys.exit(1)


def hide_text_in_translation(translation_english, subtitle_french, text_to_hide, is_expression):
    """Cache le mot/expression dans la traduction anglaise via OpenAI API (GPT-4o)"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    # Déterminer le type (Expression ou Mot)
    text_type = "Expression" if is_expression else "Mot"

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "user", "content": f"""Tu as un sous-titre français qui a été traduit en anglais.

Dans la traduction anglaise, tu dois cacher la partie qui correspond au {text_type.lower()} français que je te fournis, en remplaçant chaque lettre et espace par un underscore "_".

Exemples :

Exemple 1:
Sous-titre français: "Vous faites fausse route."
Traduction anglaise: "You are making false way"
Expression française à cacher: "faire fausse route"
Partie anglaise correspondante: "making false way" (16 caractères)
Résultat: "You are ________________"

Exemple 2:
Sous-titre français: "C'est un objectif réalisable."
Traduction anglaise: "It's an objective achievable."
Mot français à cacher: "objectif"
Partie anglaise correspondante: "objective" (9 caractères)
Résultat: "It's an _________ achievable."

Exemple 3:
Sous-titre français: "Et puis c'est pas gagné."
Traduction anglaise: "And then it's not won."
Expression française à cacher: "c'est pas gagné"
Partie anglaise correspondante: "it's not won" (12 caractères)
Résultat: "And then ____________."

IMPORTANT: Renvoie UNIQUEMENT la traduction avec les underscores, rien d'autre.

Sous-titre français: {subtitle_french}
Traduction anglaise: {translation_english}
{text_type} français à cacher: "{text_to_hide}"
"""}
            ]
        )
        translation_hidden = response.choices[0].message.content.strip()
        # Nettoyer les guillemets si présents
        translation_hidden = translation_hidden.strip('"').strip("'")
        return translation_hidden

    except Exception as e:
        print(f"❌ Erreur lors du cachage de la traduction : {e}")
        sys.exit(1)


def generate_explanation(text, is_expression=True):
    """Génère une explication via OpenAI API (expression ou mot)"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)

        # Prompt différent selon expression ou mot
        if is_expression:
            user_prompt = f"""Explique en anglais ce que signifie cette expression française.

Donne la traduction des mots rares de l'expression.

S'il n'existe pas de traduction satisfaisante pour un mot, donne uniquement sa définition, n'essaie pas de le traduire. Par exemple, pour le mot "Déplacement", il faut donner sa définition et ne pas essayer de le traduire.
-> ne pas écrire :
"Déplacement" means "movement" or "travel."
et à la place, écrire :
"Déplacement" = movement from one place to another, especially the act of changing position or location.

ne donne pas la traduction des mots qui font partie des 100 les plus utilisés en français.

Donne 2 exemples qui montrent les différents usages.

Sois synthétique.

L'explication doit suivre cette structure : d'abord expliquer ce que signifie l'expression ensuite traduire ou définir les mots rare de l'expression. enfin montrer les exemples d'usages. (d'abord la phrase en français puis sa traduction pour que l'utilisateur puisse comprendre l'exemple).

voici un exemples du genre de résultat que j'attends : " "Lâcher prise" means to let go or to release control over something, often referring to emotional or psychological burdens. It suggests the idea of accepting a situation rather than trying to control or change it.

"Lâcher" means "to let go"
"Prise" means "grip" or "hold"

Examples :
- "Il est temps de lâcher prise et d'accepter ce qui est." -> "It's time to let go and accept what is."
- "Après des mois de stress, elle a finalement décidé de lâcher prise." -> "After months of stress, she finally decided to let go." "

Expression à expliquer : "{text}" """
        else:
            user_prompt = f"""Explique en anglais ce que signifie ce mot français

Donne 2 exemples qui montrent les différents usages.

Sois synthétique.

L'explication doit suivre cette structure : d'abord expliquer ce que signifie le mot ensuite montrer les exemples d'usages. (d'abord la phrase en français puis sa traduction pour que l'utilisateur puisse comprendre l'exemple).

exemple du genre de rendu que j'attends : " "efficacement" means "effectively" or "efficiently." It refers to doing something in a way that produces the desired result with minimal waste of time or resources.

Examples:
- "Il a réussi à terminer le projet efficacement." -> "He managed to complete the project effectively."
- "Nous devons travailler ensemble pour résoudre ce problème efficacement." -> "We need to work together to solve this problem efficiently." "

Mot à expliquer : "{text}" """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "Ne fais pas de mise en forme dans ta réponse."},
                {"role": "user", "content": user_prompt}
            ]
        )
        explanation = response.choices[0].message.content.strip()
        return explanation

    except Exception as e:
        print(f"❌ Erreur lors de la génération de l'explication : {e}")
        sys.exit(1)


def bold_first_sentence(text):
    """Met en gras la première phrase (jusqu'au premier point) du texte"""
    first_dot = text.find('.')
    if first_dot != -1:
        # Ajouter ** autour de la première phrase (incluant le point)
        return f"**{text[:first_dot+1]}**{text[first_dot+1:]}"
    return text  # Si pas de point trouvé, renvoyer le texte tel quel


def convert_ps_to_markdown_link(ps_text, link_url):
    """Convertit [texte] en [texte](lien) dans le texte du PS"""
    # Remplacer [texte] par [texte](lien)
    pattern = r'\[([^\]]+)\]'
    markdown_text = re.sub(pattern, r'[\1](' + link_url + ')', ps_text)
    return markdown_text


def create_short_link(title):
    """Crée un lien raccourci via l'API Ablink"""
    # Vérifier que la clé API est configurée
    api_key = os.getenv('ABLINK_API_KEY')
    if not api_key:
        print("⚠️  Attention : La clé API Ablink n'est pas configurée.")
        print("   Le lien raccourci ne sera pas généré.")
        return "Error: Unable to generate link (missing API key)"

    try:
        # Appeler l'API Ablink pour créer un lien raccourci
        response = requests.post(
            "https://ablink.io/api/links",
            json={
                "url": "https://subly-extension.vercel.app/landing",
                "title": title
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            timeout=10
        )

        # Vérifier le status code
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            slug = data.get('slug')
            if slug:
                short_url = f"https://ablink.io/{slug}"
                return short_url
            else:
                print("⚠️  Attention : Réponse API Ablink invalide (slug manquant)")
                return "Error: Unable to generate link (invalid API response)"
        else:
            print(f"⚠️  Attention : Erreur API Ablink (status {response.status_code})")
            return "Error: Unable to generate link (API error)"

    except requests.exceptions.Timeout:
        print("⚠️  Attention : Timeout lors de l'appel à l'API Ablink")
        return "Error: Unable to generate link (timeout)"
    except Exception as e:
        print(f"⚠️  Attention : Erreur lors de la création du lien raccourci : {e}")
        return "Error: Unable to generate link"


def generate_html(expression, date_str, image1_path, translation1_visible, translation1_hidden, image2_path, translation2_visible, translation2_hidden, explanation, ps_list, subreddits, movie_title1, movie_title2):
    """Génère le HTML complet avec JavaScript pour gestion dynamique des subreddits"""

    # Convertir les listes Python en JSON pour JavaScript
    ps_json = json.dumps(ps_list)
    subreddits_json = json.dumps([name for name, _, __ in subreddits])
    subreddits_urls_json = json.dumps([url for _, __, url in subreddits])

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>What does "{expression}" mean here?</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400&family=Inter:wght@400&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Arial, sans-serif;
            background-color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 10px;
        }}

        .wrapper {{
            max-width: 562px;
            width: 100%;
        }}

        .container {{
            max-width: 562px;
            width: 100%;
            background-color: #ffffff;
            margin-bottom: 40px;
        }}

        .title {{
            background-color: #e0e0e0;
            padding: 20px;
            text-align: center;
            font-family: 'Fira Mono', monospace;
            font-size: 24px;
            font-weight: 400;
            color: #000000;
        }}

        .screenshot {{
            width: 100%;
            max-width: 562px;
            height: auto;
            display: block;
        }}

        .translation-box {{
            background-color: #212121;
            padding: 16px;
            text-align: center;
            font-family: 'Inter', sans-serif;
            font-size: 17px;
            font-weight: 400;
            color: #FFFFFF;
        }}

        .footer {{
            background-color: #e0e0e0;
            padding: 10px;
            text-align: center;
            font-family: 'Fira Mono', monospace;
            font-size: 17px;
            font-weight: 400;
            color: #000000;
        }}

        .post-title {{
            background-color: #ffffff;
            padding: 20px 20px 10px 20px;
            text-align: left;
            font-family: 'Inter', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #000000;
            margin-bottom: 10px;
        }}

        .explanation {{
            background-color: #ffffff;
            padding: 0 20px 20px 20px;
            text-align: left;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 400;
            color: #000000;
            line-height: 1.6;
            white-space: pre-wrap;
        }}

        .subreddit-container {{
            padding: 0 20px 10px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .subreddit-link {{
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            color: #1976D2;
            text-decoration: none;
            flex-grow: 1;
        }}

        .subreddit-link:hover {{
            text-decoration: underline;
        }}

        .copy-link-btn {{
            background-color: #1976D2;
            color: white;
            padding: 6px 12px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
            white-space: nowrap;
        }}

        .copy-link-btn:hover {{
            background-color: #1565C0;
        }}

        .copy-link-btn.copied {{
            background-color: #4CAF50;
        }}

        .tracker {{
            background-color: #f5f5f5;
            padding: 20px;
            margin-top: 20px;
            border-radius: 8px;
        }}

        .tracker h3 {{
            font-family: 'Inter', sans-serif;
            font-size: 18px;
            margin-bottom: 15px;
            color: #000000;
        }}

        .tracker-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            gap: 10px;
        }}

        .tracker-item input[type="checkbox"] {{
            margin-right: 0;
            width: 18px;
            height: 18px;
            cursor: pointer;
            flex-shrink: 0;
        }}

        .tracker-item .label-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-grow: 1;
        }}

        .tracker-item .label-text {{
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 4px solid transparent;
            transition: all 0.2s ease;
            flex-grow: 1;
            outline: 2px dashed transparent;
        }}

        .tracker-item .label-text:hover {{
            background-color: #f5f5f5;
        }}

        .tracker-item .label-text.selected {{
            background-color: #E3F2FD;
            border-left-color: #1976D2;
            color: #1976D2;
            font-weight: 500;
        }}

        .tracker-item .label-text[contenteditable="true"]:focus {{
            outline: 2px dashed #1976D2;
            background-color: #FFF9C4;
            cursor: text;
        }}

        .tracker-item .edit-btn {{
            background: none;
            border: none;
            font-size: 16px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background-color 0.2s;
            flex-shrink: 0;
            opacity: 0.6;
        }}

        .tracker-item .edit-btn:hover {{
            background-color: #e0e0e0;
            opacity: 1;
        }}

        [contenteditable="true"] {{
            outline: 2px dashed transparent;
            transition: outline 0.2s;
        }}

        [contenteditable="true"]:hover {{
            outline-color: #2196F3;
        }}

        [contenteditable="true"]:focus {{
            outline-color: #1976D2;
            background-color: #f0f8ff;
            color: #000000;
        }}

        .translation-box[contenteditable="true"]:focus {{
            background-color: #f0f8ff;
            color: #000000;
        }}

        .copy-btn {{
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin: 20px 20px 10px 20px;
            transition: background-color 0.3s, transform 0.1s;
            display: inline-block;
        }}

        .copy-btn:hover {{
            background-color: #45a049;
            transform: translateY(-2px);
        }}

        .copy-btn:active {{
            transform: translateY(0);
        }}

        .copy-btn.copied {{
            background-color: #2196F3;
        }}

        .image-container {{
            position: relative;
            width: 100%;
            display: block;
        }}

        .movie-title-overlay {{
            position: absolute;
            top: 0;
            right: 0;
            background-color: #212121;
            color: #ffffff;
            padding: 5px;
            font-family: 'Fira Mono', monospace;
            font-size: 8px;
            font-weight: 400;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- LIEN DU SUBREDDIT EN PREMIER -->
        <div class="subreddit-container">
            <a href="#" class="subreddit-link" id="current-subreddit-link" target="_blank"></a>
            <button class="copy-link-btn" id="copy-subreddit-link-btn">📋 Copier le lien</button>
        </div>

        <!-- TITRE DU POST EN DEUXIÈME -->
        <div class="post-title" id="main-title">Learn French: what does "{expression}" mean here?</div>

        <!-- BOUTON COPIER LE TITRE -->
        <button class="copy-btn" id="copy-title-btn" style="margin: 0 20px 20px 20px;">📋 Copier le titre</button>

        <!-- SECTION 1: VERSION VISIBLE -->
        <div class="title">What does "{expression}" mean here?</div>
        <div class="container">
            <div class="image-container">
                <img src="{image1_path}" alt="Screenshot 1" class="screenshot">
                <div class="movie-title-overlay">{movie_title1}</div>
            </div>
            <div class="translation-box" contenteditable="true" id="translation1-visible">{translation1_visible}</div>
            <div class="image-container">
                <img src="{image2_path}" alt="Screenshot 2" class="screenshot">
                <div class="movie-title-overlay">{movie_title2}</div>
            </div>
            <div class="translation-box" contenteditable="true" id="translation2-visible">{translation2_visible}</div>
            <div class="footer">(Open the post to reveal the explanation)</div>
        </div>

        <!-- SECTION 2: VERSION CACHÉE -->
        <div class="title">What does "{expression}" mean here?</div>
        <div class="container">
            <div class="image-container">
                <img src="{image1_path}" alt="Screenshot 1" class="screenshot">
                <div class="movie-title-overlay">{movie_title1}</div>
            </div>
            <div class="translation-box" contenteditable="true" id="translation1-hidden">{translation1_hidden}</div>
            <div class="image-container">
                <img src="{image2_path}" alt="Screenshot 2" class="screenshot">
                <div class="movie-title-overlay">{movie_title2}</div>
            </div>
            <div class="translation-box" contenteditable="true" id="translation2-hidden">{translation2_hidden}</div>
            <div class="footer">(Open the post to reveal the explanation)</div>
        </div>

        <!-- EXPLICATION -->
        <div class="explanation" contenteditable="true" id="explanation">{explanation}</div>

        <!-- PS (dynamique) -->
        <div class="explanation" id="ps-text"></div>

        <!-- PROMO SUBREDDIT -->
        <div class="explanation" id="ps-subreddit"></div>

        <!-- SIGNATURE -->
        <div class="explanation">Happy learning!</div>

        <!-- BOUTON COPIER -->
        <button class="copy-btn" id="copy-btn">📋 Copier Explication + PS</button>

        <!-- TRACKER DE PUBLICATION -->
        <div class="tracker">
            <h3>Publication tracker:</h3>
            <div id="tracker-list"></div>
        </div>
    </div>

    <script>
        // Configuration
        const EXPRESSION = "{expression}";
        const DATE = "{date_str}";
        const SUBREDDITS = {subreddits_json};
        const SUBREDDITS_URLS = {subreddits_urls_json};
        const PS_VARIATIONS = {ps_json};
        const STORAGE_KEY = `reddit-post-${{EXPRESSION}}-${{DATE}}`;

        // État par défaut
        const DEFAULT_STATE = {{
            published: [false, false, false, false],
            selectedSubredditIndex: 0,
            editedContent: {{}}
        }};

        // Charger l'état depuis localStorage
        function loadState() {{
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : DEFAULT_STATE;
        }}

        // Sauvegarder l'état dans localStorage
        function saveState(state) {{
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }}

        // Trouver le prochain subreddit non publié
        function findNextUnpublishedIndex(state) {{
            const index = state.published.findIndex(pub => pub === false);
            return index !== -1 ? index : SUBREDDITS.length - 1;
        }}

        // Sélectionner un subreddit
        function selectSubreddit(index) {{
            const state = loadState();
            state.selectedSubredditIndex = index;
            saveState(state);
            updateDisplay(state);
        }}

        // Mettre à jour l'affichage
        function updateDisplay(state) {{
            // Vérifier si le subreddit sélectionné est coché
            // Si oui, auto-sélectionner le prochain non-coché
            if (state.published[state.selectedSubredditIndex]) {{
                state.selectedSubredditIndex = findNextUnpublishedIndex(state);
                saveState(state);
            }}

            const selectedIndex = state.selectedSubredditIndex;

            // Mettre à jour le lien du subreddit
            const subredditLink = document.getElementById('current-subreddit-link');
            subredditLink.textContent = SUBREDDITS_URLS[selectedIndex];
            subredditLink.href = SUBREDDITS_URLS[selectedIndex];

            // Mettre à jour le PS
            const psText = PS_VARIATIONS[selectedIndex];
            document.getElementById('ps-text').textContent = psText;

            // Mettre à jour le PS promo subreddit
            const psPrefix = psText.startsWith('PS:') ? 'PS-2:' : 'PS:';
            document.getElementById('ps-subreddit').textContent = `${{psPrefix}} More posts like this on r/FrenchVocab`;

            // Créer/mettre à jour les checkboxes
            const trackerList = document.getElementById('tracker-list');
            trackerList.innerHTML = '';

            SUBREDDITS.forEach((subreddit, index) => {{
                const item = document.createElement('div');
                item.className = 'tracker-item';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `checkbox-${{index}}`;
                checkbox.checked = state.published[index];
                checkbox.addEventListener('change', () => handleCheckboxChange(index));

                // Conteneur pour le label et le bouton d'édition
                const labelContainer = document.createElement('div');
                labelContainer.className = 'label-container';

                // Texte du label (span au lieu de label)
                const labelText = document.createElement('span');
                labelText.id = `tracker-label-${{index}}`;
                labelText.className = 'label-text';
                labelText.contentEditable = 'true';

                // Restaurer le texte édité ou utiliser le nom du subreddit par défaut
                if (state.editedContent && state.editedContent[`tracker-label-${{index}}`]) {{
                    labelText.textContent = state.editedContent[`tracker-label-${{index}}`];
                }} else {{
                    labelText.textContent = subreddit;
                }}

                // Ajouter la classe selected si c'est le subreddit actuellement sélectionné
                if (index === selectedIndex) {{
                    labelText.classList.add('selected');
                }}

                // Clic sur le texte = sélection du subreddit
                labelText.addEventListener('click', (e) => {{
                    // Ne pas sélectionner si on est en train d'éditer
                    if (document.activeElement === labelText) {{
                        return;
                    }}
                    e.preventDefault();
                    selectSubreddit(index);
                }});

                // Désactiver l'édition par défaut (on utilisera le bouton crayon)
                labelText.addEventListener('focus', (e) => {{
                    // Si focus sans avoir cliqué sur le bouton édition, annuler
                    if (!labelText.dataset.editing) {{
                        labelText.blur();
                    }}
                }});

                // Sauvegarder les modifications quand on quitte l'édition
                labelText.addEventListener('blur', () => {{
                    delete labelText.dataset.editing;
                    const state = loadState();
                    if (!state.editedContent) {{
                        state.editedContent = {{}};
                    }}
                    state.editedContent[`tracker-label-${{index}}`] = labelText.textContent;
                    saveState(state);
                }});

                // Entrée = terminer l'édition
                labelText.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter') {{
                        e.preventDefault();
                        labelText.blur();
                    }}
                }});

                // Bouton d'édition (crayon)
                const editBtn = document.createElement('button');
                editBtn.className = 'edit-btn';
                editBtn.textContent = '✏️';
                editBtn.title = 'Éditer';

                // Clic sur le crayon = activer l'édition
                editBtn.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    labelText.dataset.editing = 'true';
                    labelText.focus();
                    // Sélectionner tout le texte
                    const range = document.createRange();
                    range.selectNodeContents(labelText);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                }});

                labelContainer.appendChild(labelText);
                labelContainer.appendChild(editBtn);

                item.appendChild(checkbox);
                item.appendChild(labelContainer);
                trackerList.appendChild(item);
            }});

            // Restaurer le contenu édité
            if (state.editedContent) {{
                Object.keys(state.editedContent).forEach(id => {{
                    const element = document.getElementById(id);
                    if (element) {{
                        element.textContent = state.editedContent[id];
                    }}
                }});
            }}
        }}

        // Gérer le changement de checkbox (tracking seulement)
        function handleCheckboxChange(index) {{
            const state = loadState();
            // Toggle l'état (permettre de décocher)
            state.published[index] = !state.published[index];

            // Si on coche le subreddit actuellement sélectionné,
            // auto-sélectionner le prochain non-coché
            if (state.published[index] && index === state.selectedSubredditIndex) {{
                state.selectedSubredditIndex = findNextUnpublishedIndex(state);
            }}

            // Sauvegarder et mettre à jour
            saveState(state);
            updateDisplay(state);
        }}

        // Sauvegarder les modifications de contenu éditable
        function setupContentEditableSaving() {{
            const editableElements = document.querySelectorAll('[contenteditable="true"]');
            editableElements.forEach(element => {{
                element.addEventListener('blur', () => {{
                    const state = loadState();
                    if (!state.editedContent) {{
                        state.editedContent = {{}};
                    }}
                    state.editedContent[element.id] = element.textContent;
                    saveState(state);
                }});
            }});
        }}

        // Copier l'explication + PS + Happy learning! dans le presse-papiers
        function setupCopyButton() {{
            const copyBtn = document.getElementById('copy-btn');
            copyBtn.addEventListener('click', async () => {{
                const explanation = document.getElementById('explanation').textContent;
                const ps = document.getElementById('ps-text').textContent;
                const psSubreddit = document.getElementById('ps-subreddit').textContent;
                const textToCopy = explanation + '\\n\\n' + ps + '\\n\\n' + psSubreddit + '\\n\\nHappy learning!';

                try {{
                    await navigator.clipboard.writeText(textToCopy);

                    // Feedback visuel
                    const originalText = copyBtn.textContent;
                    copyBtn.textContent = '✅ Copié !';
                    copyBtn.classList.add('copied');

                    setTimeout(() => {{
                        copyBtn.textContent = originalText;
                        copyBtn.classList.remove('copied');
                    }}, 2000);
                }} catch (err) {{
                    console.error('Erreur lors de la copie:', err);
                    copyBtn.textContent = '❌ Erreur';
                    setTimeout(() => {{
                        copyBtn.textContent = '📋 Copier Explication + PS';
                    }}, 2000);
                }}
            }});
        }}

        // Copier le titre dans le presse-papiers
        function setupCopyTitleButton() {{
            const copyTitleBtn = document.getElementById('copy-title-btn');
            copyTitleBtn.addEventListener('click', async () => {{
                const title = document.getElementById('main-title').textContent;

                try {{
                    await navigator.clipboard.writeText(title);

                    // Feedback visuel
                    const originalText = copyTitleBtn.textContent;
                    copyTitleBtn.textContent = '✅ Copié !';
                    copyTitleBtn.classList.add('copied');

                    setTimeout(() => {{
                        copyTitleBtn.textContent = originalText;
                        copyTitleBtn.classList.remove('copied');
                    }}, 2000);
                }} catch (err) {{
                    console.error('Erreur lors de la copie:', err);
                    copyTitleBtn.textContent = '❌ Erreur';
                    setTimeout(() => {{
                        copyTitleBtn.textContent = '📋 Copier le titre';
                    }}, 2000);
                }}
            }});
        }}

        // Copier le lien du subreddit dans le presse-papiers
        function setupCopySubredditLinkButton() {{
            const copySubredditLinkBtn = document.getElementById('copy-subreddit-link-btn');
            copySubredditLinkBtn.addEventListener('click', async () => {{
                const state = loadState();
                const selectedIndex = state.selectedSubredditIndex;
                const subredditUrl = SUBREDDITS_URLS[selectedIndex];

                try {{
                    await navigator.clipboard.writeText(subredditUrl);

                    // Feedback visuel
                    const originalText = copySubredditLinkBtn.textContent;
                    copySubredditLinkBtn.textContent = '✅ Copié !';
                    copySubredditLinkBtn.classList.add('copied');

                    setTimeout(() => {{
                        copySubredditLinkBtn.textContent = originalText;
                        copySubredditLinkBtn.classList.remove('copied');
                    }}, 2000);
                }} catch (err) {{
                    console.error('Erreur lors de la copie:', err);
                    copySubredditLinkBtn.textContent = '❌ Erreur';
                    setTimeout(() => {{
                        copySubredditLinkBtn.textContent = '📋 Copier le lien';
                    }}, 2000);
                }}
            }});
        }}

        // Initialisation au chargement de la page
        document.addEventListener('DOMContentLoaded', () => {{
            const state = loadState();
            updateDisplay(state);
            setupContentEditableSaving();
            setupCopyButton();
            setupCopyTitleButton();
            setupCopySubredditLinkButton();
        }});
    </script>
</body>
</html>"""

    return html_template


def main():
    parser = argparse.ArgumentParser(
        description='Génère un post Reddit HTML pour l\'apprentissage du français'
    )

    # Groupe mutuellement exclusif pour expression ou mot
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--expression',
                       help='Expression française à expliquer (ex: "c\'est pas gagné")')
    group.add_argument('--mot',
                       help='Mot français à expliquer (ex: "manger")')

    parser.add_argument('--image1', required=True,
                        help='Chemin vers la première capture d\'écran')
    parser.add_argument('--image2', required=True,
                        help='Chemin vers la deuxième capture d\'écran')

    args = parser.parse_args()

    # Déterminer si c'est une expression ou un mot
    if args.expression:
        text = args.expression
        is_expression = True
        text_type = "expression"
    else:
        text = args.mot
        is_expression = False
        text_type = "mot"

    # ÉTAPE 1: Extraire les titres des films (depuis images sources)
    print("⏳ Extraction titre du film (image 1)...")
    movie_title1 = extract_movie_title(args.image1)
    print(f"✓ Titre extrait : \"{movie_title1}\"")

    print("⏳ Extraction titre du film (image 2)...")
    movie_title2 = extract_movie_title(args.image2)
    print(f"✓ Titre extrait : \"{movie_title2}\"")

    # ÉTAPE 2: Extraire les sous-titres via OpenAI Vision
    print("⏳ Extraction texte image 1...")
    subtitle1 = extract_subtitle_from_image(args.image1)
    print(f"✓ Texte extrait : \"{subtitle1}\"")

    print("⏳ Extraction texte image 2...")
    subtitle2 = extract_subtitle_from_image(args.image2)
    print(f"✓ Texte extrait : \"{subtitle2}\"")

    # Traduire les sous-titres via OpenAI
    print("⏳ Traduction du sous-titre 1...")
    translation1 = translate_subtitle_natural(subtitle1)
    print(f"✓ Traduction : \"{translation1}\"")

    print("⏳ Traduction du sous-titre 2...")
    translation2 = translate_subtitle_natural(subtitle2)
    print(f"✓ Traduction : \"{translation2}\"")

    # Cacher le mot/expression dans les traductions (une seule fois)
    print(f"⏳ Cachage du {text_type.lower()} dans les traductions...")
    translation1_hidden = hide_text_in_translation(translation1, subtitle1, text, is_expression)
    translation2_hidden = hide_text_in_translation(translation2, subtitle2, text, is_expression)
    print(f"✓ Traductions cachées générées")

    # Générer l'explication
    print(f"⏳ Génération de l'explication ({text_type})...")
    explanation = generate_explanation(text, is_expression=is_expression)
    # Mettre la première phrase en gras
    explanation = bold_first_sentence(explanation)
    print("✓ Explication générée")

    # Sélectionner 4 post-scriptum aléatoires différents
    ps_list = random.sample(PS_VARIATIONS, 4)

    # Liste des subreddits (ordre fixe comme demandé)
    subreddits = [
        ("r/FrenchImmersion", "r-frenchimmersion", "https://www.reddit.com/r/FrenchImmersion/"),
        ("r/FrenchVocab", "r-frenchvocab", "https://www.reddit.com/r/FrenchVocab/"),
        ("r/learnfrench", "r-learnfrench", "https://www.reddit.com/r/learnfrench/"),
        ("r/learningfrench", "r-learningfrench", "https://www.reddit.com/r/learningfrench/")
    ]

    # Générer le slug et la date pour les noms de fichiers
    text_slug = slugify(text)
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Rogner les images (enlever 50px du bas) et les sauvegarder dans img/
    image1_new_name = f"img/{text_slug}-{date_str}-scene1.png"
    image2_new_name = f"img/{text_slug}-{date_str}-scene2.png"

    print(f"⏳ Rognage et sauvegarde des images...")
    crop_image_bottom(args.image1, image1_new_name, pixels_to_remove=40)
    crop_image_bottom(args.image2, image2_new_name, pixels_to_remove=40)
    print(f"✓ Images rognées et sauvegardées dans img/")

    # Supprimer les images sources (plus nécessaires)
    print(f"⏳ Suppression des images sources...")
    os.remove(args.image1)
    os.remove(args.image2)
    print(f"✓ Images sources supprimées")

    # Créer 4 liens raccourcis (un par subreddit)
    print(f"⏳ Création des liens raccourcis...")
    short_links = []
    for i, (subreddit_display, _, __) in enumerate(subreddits):
        link_title = f"{text} - {subreddit_display}"
        short_link = create_short_link(link_title)

        if short_link.startswith("Error:"):
            print(f"⚠️  {subreddit_display}: {short_link}")
        else:
            print(f"✓ {subreddit_display}: {short_link}")

        short_links.append(short_link)

    # Convertir les PS en format Markdown avec liens intégrés
    ps_list_with_links = [
        convert_ps_to_markdown_link(ps_list[i], short_links[i])
        for i in range(4)
    ]

    # Adapter les chemins des images pour le dossier posts/ (ajouter ../)
    image1_path_for_html = f"../{image1_new_name}"
    image2_path_for_html = f"../{image2_new_name}"

    # Générer UN SEUL fichier HTML avec gestion dynamique
    output_filename = f"posts/{text_slug}-{date_str}.html"

    html_content = generate_html(
        text,
        date_str,
        image1_path_for_html,
        translation1,  # traduction visible
        translation1_hidden,  # traduction cachée
        image2_path_for_html,
        translation2,  # traduction visible
        translation2_hidden,  # traduction cachée
        explanation,
        ps_list_with_links,  # Liste des 4 PS avec liens Markdown
        subreddits,
        movie_title1,  # Titre du film (image 1)
        movie_title2   # Titre du film (image 2)
    )

    # Sauvegarder le fichier
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Message de confirmation
    print(f"\n✓ Fichier HTML généré : {output_filename}")
    print(f"  Ouvre-le dans ton navigateur pour commencer le workflow de publication!")


if __name__ == '__main__':
    main()
