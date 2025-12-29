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
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


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


def generate_html(expression, image1_path, translation1, image2_path, translation2, explanation):
    """Génère le HTML complet avec le template CSS"""

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
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1124px;
            width: 100%;
            background-color: #ffffff;
        }}

        .title {{
            background-color: #e0e0e0;
            padding: 40px;
            text-align: center;
            font-family: 'Fira Mono', monospace;
            font-size: 48px;
            font-weight: 400;
            color: #000000;
        }}

        .screenshot {{
            width: 100%;
            max-width: 1124px;
            height: auto;
            display: block;
        }}

        .translation-box {{
            background-color: #212121;
            padding: 32px;
            text-align: center;
            font-family: 'Inter', sans-serif;
            font-size: 34px;
            font-weight: 400;
            color: #FFFFFF;
        }}

        .footer {{
            background-color: #e0e0e0;
            padding: 20px;
            text-align: center;
            font-family: 'Fira Mono', monospace;
            font-size: 34px;
            font-weight: 400;
            color: #000000;
        }}

        .explanation {{
            background-color: #ffffff;
            padding: 40px;
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
    <div class="container">
        <div class="title">What does "{expression}" mean here?</div>

        <img src="{image1_path}" alt="Screenshot 1" class="screenshot">

        <div class="translation-box">{translation1}</div>

        <img src="{image2_path}" alt="Screenshot 2" class="screenshot">

        <div class="translation-box">{translation2}</div>

        <div class="footer">(Open the post to reveal the explanation)</div>

        <div class="explanation">{explanation}</div>
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

    # Générer l'explication
    print(f"⏳ Génération de l'explication ({text_type})...")
    explanation = generate_explanation(text, is_expression=is_expression)
    print("✓ Explication générée")

    # Générer le nom du fichier
    text_slug = slugify(text)
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_filename = f"{text_slug}-{date_str}.html"

    # Générer le HTML
    html_content = generate_html(
        text,
        args.image1,
        translation1,
        args.image2,
        translation2,
        explanation
    )

    # Sauvegarder le fichier
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Fichier HTML généré : {output_filename}")
    print(f"  Ouvre-le dans ton navigateur pour faire le screenshot!")


if __name__ == '__main__':
    main()
