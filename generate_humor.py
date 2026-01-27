#!/usr/bin/env python3
"""
Script pour générer des posts Reddit HTML avec mèmes humoristiques en français.
Chat interactif avec LLM pour analyser l'image et générer la description.
"""

import os
import sys
import re
import json
import random
import shutil
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Variations de post-scriptum promotionnel (réutilisées des autres scripts)
PS_VARIATIONS = [
    "PS: If you watch Netflix on your computer and want to support this post, you can check [this tool] that I made.",
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


def get_openai_client():
    """Crée et retourne un client OpenAI"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Erreur : La clé API OpenAI n'est pas configurée.")
        print("   Crée un fichier .env avec : OPENAI_API_KEY=ta-clé-api")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def encode_image_to_base64(image_path):
    """Encode une image en base64 pour l'API OpenAI"""
    import base64
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_meme(image_path):
    """Analyse le mème et génère la description complète avec GPT-4o Vision"""
    client = get_openai_client()

    print("⏳ Analyse de l'image et génération de la description...\n")

    # Encoder l'image en base64
    base64_image = encode_image_to_base64(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in French humor and language pedagogy. You analyze French memes and create educational content for English-speaking learners."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this French meme and create an educational post for English speakers learning French.

Your response MUST follow this EXACT format:

**Translation:**
[Translate all French text visible in the meme to English. If there are multiple speakers/panels, use emojis or labels to identify them clearly]

**Why is this funny:**
[Explain the joke in 2-4 sentences. Focus on cultural context, wordplay, or situational humor]

**Vocabulary:**
[List key French words/expressions with English definitions. Format: "• word = definition". ONLY include this section if there are interesting vocabulary points worth teaching. If not, completely OMIT this section - do NOT write "**Vocabulary:**" at all]

**Context:**
[Add cultural/historical context if needed to understand the humor. ONLY include this section if culturally significant. If not needed, completely OMIT this section - do NOT write "**Context:**" at all]

IMPORTANT:
- Use **bold** markdown for section titles (Translation, Why is this funny, Vocabulary, Context)
- Do NOT use ALL CAPS for section titles
- Do NOT include "(if relevant)" or any similar notes in your response
- Simply omit the Vocabulary or Context sections entirely if they are not needed

Keep it concise, educational, and engaging. Use simple English."""
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

    return response.choices[0].message.content.strip()


def modify_description(current_description, user_instruction):
    """Modifie la description selon les instructions de l'utilisateur"""
    client = get_openai_client()

    print("⏳ Modification de la description...\n")

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in French humor and language pedagogy who adapts content based on feedback."
            },
            {
                "role": "user",
                "content": f"""Here is the current description:

{current_description}

The user requests: "{user_instruction}"

Generate a new version incorporating this feedback.
Keep the same format (TRANSLATION, WHY IS THIS FUNNY, etc.) and structure.
DO NOT use markdown formatting (no bold, no headers with #)."""
            }
        ]
    )

    return response.choices[0].message.content.strip()


def create_short_link(title, test_mode=False):
    """Crée un lien raccourci via l'API Ablink"""
    import requests

    # En mode test, retourner un lien factice
    if test_mode:
        return "https://ablink.io/test-link"

    api_key = os.getenv('ABLINK_API_KEY')
    if not api_key:
        print("⚠️  Attention : La clé API Ablink n'est pas configurée.")
        return "Error: Unable to generate link (missing API key)"

    try:
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

        if response.status_code in [200, 201]:
            data = response.json()
            slug = data.get('slug')
            if slug:
                return f"https://ablink.io/{slug}"

        return "Error: Unable to generate link (API error)"

    except Exception as e:
        print(f"⚠️  Erreur création lien : {e}")
        return "Error: Unable to generate link"


def convert_ps_to_markdown_link(ps_text, link_url):
    """Convertit [texte] en [texte](lien) dans le texte du PS"""
    pattern = r'\[([^\]]+)\]'
    markdown_text = re.sub(pattern, r'[\1](' + link_url + ')', ps_text)
    return markdown_text


def generate_html(description, image_filename, date_str, title_slug, title_display, test_mode=False):
    """Génère le HTML avec image + description éditable + tracker 3 subreddits"""

    # Sélectionner 3 PS aléatoires différents
    ps_list = random.sample(PS_VARIATIONS, 3)

    # Subreddits pour humor (sans FrenchVocab)
    subreddits = [
        ("r/FrenchImmersion", "r-frenchimmersion", "https://www.reddit.com/r/FrenchImmersion/"),
        ("r/learnfrench", "r-learnfrench", "https://www.reddit.com/r/learnfrench/"),
        ("r/learningfrench", "r-learningfrench", "https://www.reddit.com/r/learningfrench/")
    ]

    # Créer 3 liens raccourcis
    if test_mode:
        print(f"\n🧪 Mode test : liens Ablink non créés (liens factices)")
        short_links = ["https://ablink.io/test-link"] * 3
    else:
        print(f"\n⏳ Création des liens raccourcis...")
        short_links = []
        for i, (subreddit_display, _, __) in enumerate(subreddits):
            link_title = f"Humor {title_slug} - {subreddit_display}"
            short_link = create_short_link(link_title, test_mode=False)

            if short_link.startswith("Error:"):
                print(f"⚠️  {subreddit_display}: {short_link}")
            else:
                print(f"✓ {subreddit_display}: {short_link}")

            short_links.append(short_link)

    # Convertir PS en Markdown avec liens
    ps_list_with_links = [
        convert_ps_to_markdown_link(ps_list[i], short_links[i])
        for i in range(3)
    ]

    # Convertir en JSON pour JavaScript
    ps_json = json.dumps(ps_list_with_links)
    subreddits_json = json.dumps([name for name, _, __ in subreddits])
    subreddits_urls_json = json.dumps([url for _, __, url in subreddits])

    # Chemin relatif de l'image (posts/humor/ vers img/humor/)
    image_relative_path = f"../../img/humor/{image_filename}"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learn French with humor</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400&family=Inter:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }}

        .wrapper {{
            max-width: 700px;
            margin: 0 auto;
        }}

        /* LIEN SUBREDDIT */
        .subreddit-container {{
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            background-color: white;
            border-radius: 8px;
            margin-bottom: 10px;
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
        }}

        .copy-link-btn:hover {{
            background-color: #1565C0;
        }}

        .copy-link-btn.copied {{
            background-color: #4CAF50;
        }}

        /* TITRE DU POST */
        .post-title {{
            background-color: white;
            padding: 20px;
            text-align: left;
            font-family: 'Inter', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: #000000;
            margin-bottom: 10px;
            border-radius: 8px;
        }}

        .editable-part {{
            color: #1976D2;
            border-bottom: 2px dashed #1976D2;
            padding: 2px 4px;
            transition: background-color 0.2s;
        }}

        .editable-part:focus {{
            outline: none;
            background-color: #FFF9C4;
        }}

        .copy-title-btn {{
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 20px 20px 0;
        }}

        .copy-title-btn:hover {{
            background-color: #45a049;
        }}

        .copy-title-btn.copied {{
            background-color: #2196F3;
        }}

        /* IMAGE DU MÈME */
        .meme-container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}

        .meme-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}

        /* DESCRIPTION */
        .description {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
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
            margin-bottom: 20px;
        }}

        .copy-btn:hover {{
            background-color: #45a049;
        }}

        .copy-btn.copied {{
            background-color: #2196F3;
        }}

        /* TRACKER */
        .tracker {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
        }}

        .tracker h3 {{
            font-family: 'Inter', sans-serif;
            font-size: 18px;
            margin-bottom: 15px;
        }}

        .tracker-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px;
        }}

        .tracker-item input[type="checkbox"] {{
            width: 18px;
            height: 18px;
            cursor: pointer;
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
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- LIEN SUBREDDIT -->
        <div class="subreddit-container">
            <a href="#" class="subreddit-link" id="current-subreddit-link" target="_blank"></a>
            <button class="copy-link-btn" id="copy-subreddit-link-btn">📋 Copier le lien</button>
        </div>

        <!-- TITRE DU POST (partie éditable) -->
        <div class="post-title">
            Learn French with humor: <span class="editable-part" contenteditable="true" id="editable-title">{title_display}</span> (Joke explained in description)
        </div>
        <button class="copy-title-btn" id="copy-title-btn">📋 Copier le titre</button>

        <!-- IMAGE DU MÈME -->
        <div class="meme-container">
            <img src="{image_relative_path}" alt="French meme">
        </div>

        <!-- DESCRIPTION -->
        <div class="description" contenteditable="true" id="description">{description}</div>

        <!-- PS (dynamique) -->
        <div class="description" id="ps-text"></div>

        <!-- SIGNATURE -->
        <div class="description">Happy learning!</div>

        <!-- BOUTON COPIER -->
        <button class="copy-btn" id="copy-btn">📋 Copier Description + PS</button>

        <!-- TRACKER -->
        <div class="tracker">
            <h3>Publication tracker:</h3>
            <div id="tracker-list"></div>
        </div>
    </div>

    <script>
        // Configuration
        const TITLE_SLUG = "{title_slug}";
        const DATE = "{date_str}";
        const SUBREDDITS = {subreddits_json};
        const SUBREDDITS_URLS = {subreddits_urls_json};
        const PS_VARIATIONS = {ps_json};
        const STORAGE_KEY = `reddit-post-humor-${{TITLE_SLUG}}-${{DATE}}`;

        // État par défaut
        const DEFAULT_STATE = {{
            published: [false, false, false],
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
            document.getElementById('ps-text').textContent = PS_VARIATIONS[selectedIndex];

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

                const labelContainer = document.createElement('div');
                labelContainer.className = 'label-container';

                const labelText = document.createElement('span');
                labelText.id = `tracker-label-${{index}}`;
                labelText.className = 'label-text';
                labelText.contentEditable = 'true';

                if (state.editedContent && state.editedContent[`tracker-label-${{index}}`]) {{
                    labelText.textContent = state.editedContent[`tracker-label-${{index}}`];
                }} else {{
                    labelText.textContent = subreddit;
                }}

                if (index === selectedIndex) {{
                    labelText.classList.add('selected');
                }}

                labelText.addEventListener('click', (e) => {{
                    if (document.activeElement === labelText) {{
                        return;
                    }}
                    e.preventDefault();
                    selectSubreddit(index);
                }});

                labelText.addEventListener('focus', (e) => {{
                    if (!labelText.dataset.editing) {{
                        labelText.blur();
                    }}
                }});

                labelText.addEventListener('blur', () => {{
                    delete labelText.dataset.editing;
                    const state = loadState();
                    if (!state.editedContent) {{
                        state.editedContent = {{}};
                    }}
                    state.editedContent[`tracker-label-${{index}}`] = labelText.textContent;
                    saveState(state);
                }});

                labelText.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter') {{
                        e.preventDefault();
                        labelText.blur();
                    }}
                }});

                const editBtn = document.createElement('button');
                editBtn.className = 'edit-btn';
                editBtn.textContent = '✏️';
                editBtn.title = 'Éditer';

                editBtn.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    labelText.dataset.editing = 'true';
                    labelText.focus();
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

        // Gérer le changement de checkbox
        function handleCheckboxChange(index) {{
            const state = loadState();
            state.published[index] = !state.published[index];

            if (state.published[index] && index === state.selectedSubredditIndex) {{
                state.selectedSubredditIndex = findNextUnpublishedIndex(state);
            }}

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

        // Copier description + PS
        function setupCopyButton() {{
            const copyBtn = document.getElementById('copy-btn');
            copyBtn.addEventListener('click', async () => {{
                const description = document.getElementById('description').textContent;
                const ps = document.getElementById('ps-text').textContent;
                const textToCopy = description + '\\n\\n' + ps + '\\n\\nHappy learning!';

                try {{
                    await navigator.clipboard.writeText(textToCopy);
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
                        copyBtn.textContent = '📋 Copier Description + PS';
                    }}, 2000);
                }}
            }});
        }}

        // Copier le titre
        function setupCopyTitleButton() {{
            const copyTitleBtn = document.getElementById('copy-title-btn');
            copyTitleBtn.addEventListener('click', async () => {{
                const staticPart = 'Learn French with humor: ';
                const editablePart = document.getElementById('editable-title').textContent;
                const suffix = ' (Joke explained in description)';
                const fullTitle = staticPart + editablePart + suffix;

                try {{
                    await navigator.clipboard.writeText(fullTitle);
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

        // Copier le lien du subreddit
        function setupCopySubredditLinkButton() {{
            const copySubredditLinkBtn = document.getElementById('copy-subreddit-link-btn');
            copySubredditLinkBtn.addEventListener('click', async () => {{
                const state = loadState();
                const selectedIndex = state.selectedSubredditIndex;
                const subredditUrl = SUBREDDITS_URLS[selectedIndex];

                try {{
                    await navigator.clipboard.writeText(subredditUrl);
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

        // Initialisation
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


def main(test_mode=False):
    """Workflow interactif principal"""

    print("=" * 60)
    print("😄 GÉNÉRATEUR DE POSTS HUMOUR FRANÇAIS")
    if test_mode:
        print("🧪 MODE TEST (pas de liens Ablink)")
    print("=" * 60)
    print()

    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("❌ Erreur : Aucune image fournie")
        print("Usage : python3 generate_humor.py --image <chemin_image> [--test]")
        sys.exit(1)

    # Parser les arguments
    image_path = None
    for i, arg in enumerate(sys.argv):
        if arg == '--image' and i + 1 < len(sys.argv):
            image_path = sys.argv[i + 1]
            break

    if not image_path:
        print("❌ Erreur : Vous devez spécifier une image avec --image")
        print("Usage : python3 generate_humor.py --image <chemin_image> [--test]")
        sys.exit(1)

    # Vérifier que l'image existe
    if not os.path.exists(image_path):
        print(f"❌ Erreur : L'image '{image_path}' n'existe pas")
        sys.exit(1)

    # Étape 1 : Analyser l'image et générer la description
    description = analyze_meme(image_path)

    # Boucle de modification de la description
    while True:
        print("\n" + "─" * 60)
        print("📝 DESCRIPTION GÉNÉRÉE :\n")
        print(description)
        print("─" * 60)

        modify_choice = input("\nC'est bon ? (oui/modifier/régénérer) : ").strip().lower()

        if modify_choice == 'oui':
            break
        elif modify_choice == 'régénérer':
            description = analyze_meme(image_path)
        elif modify_choice == 'modifier':
            instruction = input("\nQu'est-ce que tu veux changer ? : ").strip()
            if instruction:
                description = modify_description(description, instruction)
        else:
            print("⚠️  Réponse invalide. Tapez 'oui', 'modifier' ou 'régénérer'.")

    # Étape 2 : Demander un titre pour le slug
    print("\n" + "─" * 60)
    title_input = input("Donne un titre court pour le fichier (ex: 'la-pilule', 'monument', etc.) : ").strip()
    title_slug = slugify(title_input) if title_input else "humor-post"

    # Étape 3 : Générer le fichier HTML
    print("\n⏳ Génération du fichier HTML...")

    date_str = datetime.now().strftime('%Y-%m-%d')

    # Créer les dossiers si nécessaire
    os.makedirs('posts/humor', exist_ok=True)
    os.makedirs('img/humor', exist_ok=True)

    # Copier l'image dans img/humor/
    image_extension = os.path.splitext(image_path)[1]
    image_filename = f"{title_slug}-{date_str}{image_extension}"
    image_destination = f"img/humor/{image_filename}"
    shutil.copy(image_path, image_destination)
    print(f"✓ Image copiée : {image_destination}")

    # Générer le HTML
    html_content = generate_html(description, image_filename, date_str, title_slug, title_input, test_mode=test_mode)
    output_filename = f"posts/humor/{title_slug}-{date_str}.html"

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ Fichier HTML créé : {output_filename}")
    print(f"   Tu peux maintenant l'ouvrir dans ton navigateur pour éditer le titre et publier !")

    print("\n👋 À bientôt !")


if __name__ == '__main__':
    import sys
    # Vérifier si --test est passé en argument
    test_mode = '--test' in sys.argv
    main(test_mode=test_mode)
