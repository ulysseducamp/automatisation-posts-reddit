#!/usr/bin/env python3
"""
Script pour générer des posts Reddit HTML pour l'apprentissage du français.
Usage: python generate.py --expression "..." --image1 ... --image2 ...
"""

import argparse
from datetime import datetime
import re
import os
import sys
import base64
import random
import requests
import shutil
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Variations de post-scriptum promotionnel (choisi aléatoirement)
PS_VARIATIONS = [
    "PS: If you watch Netflix on your computer and want to support this post, you can check [this tool] that I made.",
    "PS: If you like watching Netflix and you sometimes hesitate between putting the subtitles in French or in your native language, I made a [little tool] that solves this problem",
    "PS: if you like to watch French content on Netflix and if you sometimes hesitate between puting the subtitles in French or in your native language, I made a little tool called Subly that adjusts the subtitles to your level. If you want to support this post and if you think that this tool could be useful, feel free give it a try by [clicking here] ;)",
    "PS: if you like to watch French content on Netflix and if you sometime hesitate between puting the subtitles in French or in your native language, I made a little tool called Subly that I would recommend to use. This extension adjusts the subtitles to your level (if a subtitle is adapted to your level, it displays it in French, if a subtitle is too hard, it displays it in your native language). I use it to learn Portuguese, it provides a good balance between practicing your target language and enjoying the show. Here is [the link to try it].",
    "How to support these posts: check out [this tool] that I made to learn French with Netflix.",
    "If you want to improve your French while watching Netflix, here is a [simple tool] I made that decide if a subtitle should be displayed in French or in your Native language based on your level.",
    "Quick note: If you watch Netflix on your computer, I built a [simple tool] that shows subtitles in French only when the words are familiar to you, otherwise it switches to your native language.",
    "PS: If you're a Netflix user, I made a [simple tool] that automatically chooses between French and native subtitles depending on the vocabulary you know."
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


def generate_html(expression, image1_path, translation1_visible, translation1_hidden, image2_path, translation2_visible, translation2_hidden, explanation, ps_text, short_link, subreddit_name):
    """Génère le HTML complet avec 2 sections (visible + cachée)"""

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
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="title">What does "{expression}" mean here?</div>

        <!-- SECTION 1: VERSION VISIBLE -->
        <div class="container">
            <img src="{image1_path}" alt="Screenshot 1" class="screenshot">
            <div class="translation-box">{translation1_visible}</div>
            <img src="{image2_path}" alt="Screenshot 2" class="screenshot">
            <div class="translation-box">{translation2_visible}</div>
            <div class="footer">(Open the post to reveal the explanation)</div>
        </div>

        <!-- SECTION 2: VERSION CACHÉE -->
        <div class="container">
            <img src="{image1_path}" alt="Screenshot 1" class="screenshot">
            <div class="translation-box">{translation1_hidden}</div>
            <img src="{image2_path}" alt="Screenshot 2" class="screenshot">
            <div class="translation-box">{translation2_hidden}</div>
            <div class="footer">(Open the post to reveal the explanation)</div>
        </div>

        <!-- PARTIE TEXTUELLE (une seule fois) -->
        <div class="post-title">Your daily vocab' workout 🏋️ #</div>
        <div class="explanation">{explanation}

{ps_text}

Happy learning!

{subreddit_name}</div>
    </div>
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

    # Extraire les sous-titres via OpenAI Vision
    print("⏳ Extraction texte image 1...")
    subtitle1 = extract_subtitle_from_image(args.image1)
    print(f"✓ Texte extrait : \"{subtitle1}\"")

    print("⏳ Extraction texte image 2...")
    subtitle2 = extract_subtitle_from_image(args.image2)
    print(f"✓ Texte extrait : \"{subtitle2}\"")

    # Traduire les sous-titres via OpenAI
    print("⏳ Traduction du sous-titre 1...")
    translation1 = translate_subtitle(subtitle1)
    print(f"✓ Traduction : \"{translation1}\"")

    print("⏳ Traduction du sous-titre 2...")
    translation2 = translate_subtitle(subtitle2)
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

    # Sélectionner 3 post-scriptum aléatoires différents
    ps_list = random.sample(PS_VARIATIONS, 3)

    # Liste des subreddits
    subreddits = [
        ("r/FrenchImmersion", "r-frenchimmersion"),
        ("r/learningfrench", "r-learningfrench"),
        ("r/learnfrench", "r-learnfrench")
    ]

    # Générer le slug et la date pour les noms de fichiers
    text_slug = slugify(text)
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Renommer les images avec des noms uniques et les déplacer dans img/
    image1_new_name = f"img/{text_slug}-{date_str}-scene1.png"
    image2_new_name = f"img/{text_slug}-{date_str}-scene2.png"

    print(f"⏳ Renommage des images...")
    shutil.move(args.image1, image1_new_name)
    shutil.move(args.image2, image2_new_name)
    print(f"✓ Images renommées et déplacées dans img/")

    # Générer 3 fichiers HTML (un par subreddit)
    generated_files = []

    for i, (subreddit_display, subreddit_slug) in enumerate(subreddits):
        # Créer un lien raccourci unique pour ce subreddit
        link_title = f"{text} - {subreddit_display}"
        print(f"⏳ Création du lien pour {subreddit_display}...")
        short_link = create_short_link(link_title)

        if short_link.startswith("Error:"):
            print(f"⚠️  {short_link}")
        else:
            print(f"✓ Lien créé : {short_link}")

        # Nom du fichier pour ce subreddit
        output_filename = f"{text_slug}-{date_str}-{subreddit_slug}.html"

        # Convertir le PS en format Markdown avec lien intégré
        ps_with_link = convert_ps_to_markdown_link(ps_list[i], short_link)

        # Générer le HTML avec les 2 sections (visible + cachée)
        html_content = generate_html(
            text,
            image1_new_name,
            translation1,  # traduction visible
            translation1_hidden,  # traduction cachée
            image2_new_name,
            translation2,  # traduction visible
            translation2_hidden,  # traduction cachée
            explanation,
            ps_with_link,  # PS avec lien Markdown intégré
            short_link,
            subreddit_display  # Nom du subreddit (avec r/)
        )

        # Sauvegarder le fichier
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        generated_files.append(output_filename)

    # Message de confirmation
    print(f"\n✓ 3 fichiers HTML générés :")
    for filename in generated_files:
        print(f"  - {filename}")
    print(f"\n  Ouvre-les dans ton navigateur pour faire les screenshots!")


if __name__ == '__main__':
    main()
