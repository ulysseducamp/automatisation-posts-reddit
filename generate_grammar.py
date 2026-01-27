#!/usr/bin/env python3
"""
Script pour générer des posts Reddit HTML pour l'apprentissage de la grammaire française.
Chat interactif avec LLM pour proposer des règles de grammaire et générer le contenu.
"""

import os
import sys
import re
import json
import random
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Variations de post-scriptum promotionnel (identiques au vocab)
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


def propose_grammar_rule():
    """Propose une règle de grammaire aléatoire avec 3 exemples"""
    client = get_openai_client()

    print("⏳ Génération d'une proposition de règle de grammaire...\n")

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=1.2,  # Créatif pour varier les propositions
        messages=[
            {"role": "system", "content": "Tu es un expert en grammaire française qui crée du contenu pédagogique pour des apprenants anglophones. Tu dois proposer des règles VARIÉES à chaque fois."},
            {"role": "user", "content": """Propose UNE règle de grammaire française intéressante pour des apprenants de niveau intermédiaire.

La règle doit :
- Être claire et spécifique (ex: "il faut que + subjonctif", "si + imparfait", "ne...que", agreement rules, etc.)
- Être une difficulté commune pour les anglophones
- Permettre de créer 3 exemples de phrases similaires

Ensuite, génère EXACTEMENT 3 phrases en français qui testent cette règle :
- 1 phrase CORRECTE
- 2 phrases INCORRECTES avec des erreurs ÉVIDENTES et CLAIREMENT fausses

IMPORTANT :
- Les 3 phrases doivent utiliser le même contexte/vocabulaire
- Elles doivent différer UNIQUEMENT par l'élément grammatical testé (verbe, accord, préposition, structure, etc.)
- Les phrases incorrectes doivent avoir des erreurs que PERSONNE ne ferait en français correct
- Il doit y avoir EXACTEMENT UNE SEULE option correcte (pas d'ambiguïté)
- Sois créatif et varie les règles de grammaire !

Format de réponse (STRICT) :
RULE: [nom de la règle en anglais, court]
CONTEXT: [description du contexte si nécessaire]
OPTION1: [version complète de la phrase]
OPTION2: [version complète de la phrase]
OPTION3: [version complète de la phrase]
CORRECT: [numéro de l'option correcte : 1, 2 ou 3]"""}
        ]
    )

    content = response.choices[0].message.content.strip()

    # Parser la réponse
    rule_match = re.search(r'RULE:\s*(.+)', content)
    context_match = re.search(r'CONTEXT:\s*(.+)', content)
    option1_match = re.search(r'OPTION1:\s*(.+)', content)
    option2_match = re.search(r'OPTION2:\s*(.+)', content)
    option3_match = re.search(r'OPTION3:\s*(.+)', content)
    correct_match = re.search(r'CORRECT:\s*(\d)', content)

    if not all([rule_match, context_match, option1_match, option2_match, option3_match, correct_match]):
        print("⚠️  Erreur de parsing, nouvelle tentative...\n")
        return propose_grammar_rule()  # Retry

    return {
        'rule': rule_match.group(1).strip(),
        'context': context_match.group(1).strip(),
        'option1': option1_match.group(1).strip(),
        'option2': option2_match.group(1).strip(),
        'option3': option3_match.group(1).strip(),
        'correct': int(correct_match.group(1))
    }


def generate_explanation(rule_data):
    """Génère l'explication pédagogique"""
    client = get_openai_client()

    print("⏳ Génération de l'explication...\n")

    correct_option = rule_data[f'option{rule_data["correct"]}']

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Tu es un expert en grammaire française qui explique les règles de manière claire et concise en anglais."},
            {"role": "user", "content": f"""Écris une explication pédagogique EN ANGLAIS pour cette règle de grammaire française.

Règle : {rule_data['rule']}
Phrase correcte : {correct_option}
Options incorrectes : {[opt for i, opt in enumerate([rule_data['option1'], rule_data['option2'], rule_data['option3']], 1) if i != rule_data['correct']]}

L'explication doit :
1. Commencer par : "The correct version is option {rule_data['correct']}: '{correct_option}'"
2. Expliquer POURQUOI cette règle existe (en 2-3 phrases maximum)
3. Expliquer POURQUOI les autres options sont incorrectes (1 phrase par option)
4. Être concise (maximum 150 mots)
5. Utiliser un ton pédagogique et encourageant

Format :
The correct version is option X: "phrase"

[Explication de la règle]

[Pourquoi option X est correcte]
[Pourquoi les autres sont incorrectes]

NE METS PAS de titres, de sections, juste du texte continu."""}
        ]
    )

    return response.choices[0].message.content.strip()


def modify_explanation(current_explanation, user_instruction):
    """Modifie l'explication selon les instructions de l'utilisateur"""
    client = get_openai_client()

    print("⏳ Modification de l'explication...\n")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Tu es un expert en grammaire française qui adapte les explications selon les retours."},
            {"role": "user", "content": f"""Voici l'explication actuelle :

{current_explanation}

L'utilisateur demande : "{user_instruction}"

Génère une nouvelle version en tenant compte de cette demande.
Garde le même format et la même structure (commence toujours par "The correct version is option X...").
Ne mets pas de titres ni de sections."""}
        ]
    )

    return response.choices[0].message.content.strip()


def create_short_link(title, test_mode=False):
    """Crée un lien raccourci via l'API Ablink (copié du vocab)"""
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


def generate_html(rule_data, explanation, date_str, test_mode=False):
    """Génère le HTML avec 3 slides carrées + tracker subreddits"""

    rule_slug = slugify(rule_data['rule'])

    # Sélectionner 4 PS aléatoires différents
    ps_list = random.sample(PS_VARIATIONS, 4)

    # Subreddits pour grammar
    subreddits = [
        ("r/FrenchImmersion", "r-frenchimmersion", "https://www.reddit.com/r/FrenchImmersion/"),
        ("r/FrenchGrammar", "r-frenchgrammar", "https://www.reddit.com/r/FrenchGrammar/"),
        ("r/learnfrench", "r-learnfrench", "https://www.reddit.com/r/learnfrench/"),
        ("r/learningfrench", "r-learningfrench", "https://www.reddit.com/r/learningfrench/")
    ]

    # Créer 4 liens raccourcis
    if test_mode:
        print(f"\n🧪 Mode test : liens Ablink non créés (liens factices)")
        short_links = ["https://ablink.io/test-link"] * 4
    else:
        print(f"\n⏳ Création des liens raccourcis...")
        short_links = []
        for i, (subreddit_display, _, __) in enumerate(subreddits):
            link_title = f"{rule_data['rule']} - {subreddit_display}"
            short_link = create_short_link(link_title, test_mode=False)

            if short_link.startswith("Error:"):
                print(f"⚠️  {subreddit_display}: {short_link}")
            else:
                print(f"✓ {subreddit_display}: {short_link}")

            short_links.append(short_link)

    # Convertir PS en Markdown avec liens
    ps_list_with_links = [
        convert_ps_to_markdown_link(ps_list[i], short_links[i])
        for i in range(4)
    ]

    # Convertir en JSON pour JavaScript
    ps_json = json.dumps(ps_list_with_links)
    subreddits_json = json.dumps([name for name, _, __ in subreddits])
    subreddits_urls_json = json.dumps([url for _, __, url in subreddits])

    # Déterminer quelle slide est correcte (mettre checkmark)
    correct_index = rule_data['correct']

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grammar: {rule_data['rule']}</title>
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
            max-width: 1200px;
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

        /* SLIDES CARRÉES */
        .slides-container {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}

        .slide {{
            width: 540px;
            min-height: 540px;
            background-color: #2b2b2b;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 40px;
            border-radius: 8px;
            position: relative;
        }}

        .slide-header {{
            background-color: #c62828;
            color: white;
            padding: 10px 20px;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 40px;
        }}

        .options-list {{
            width: 100%;
            text-align: center;
            margin-bottom: 40px;
        }}

        .option-item {{
            font-size: 20px;
            font-weight: 400;
            margin-bottom: 25px;
            line-height: 1.5;
        }}

        .slide-footer {{
            font-size: 14px;
            color: #bdbdbd;
        }}

        /* EXPLICATION */
        .explanation {{
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

        <!-- TITRE DU POST (éditable) -->
        <div class="post-title" contenteditable="true" id="main-title">Grammar: [complete this]</div>
        <button class="copy-title-btn" id="copy-title-btn">📋 Copier le titre</button>

        <!-- SLIDE UNIQUE AVEC LES 3 OPTIONS -->
        <div class="slides-container">
            <div class="slide">
                <div class="slide-header">Which version is correct?</div>
                <div class="options-list">
                    <div class="option-item">1. {rule_data['option1']}</div>
                    <div class="option-item">2. {rule_data['option2']}</div>
                    <div class="option-item">3. {rule_data['option3']}</div>
                </div>
                <div class="slide-footer">(Answer + explanation in description)</div>
            </div>
        </div>

        <!-- EXPLICATION -->
        <div class="explanation" contenteditable="true" id="explanation">{explanation}</div>

        <!-- PS (dynamique) -->
        <div class="explanation" id="ps-text"></div>

        <!-- SIGNATURE -->
        <div class="explanation">Happy learning!</div>

        <!-- BOUTON COPIER -->
        <button class="copy-btn" id="copy-btn">📋 Copier Explication + PS</button>

        <!-- TRACKER -->
        <div class="tracker">
            <h3>Publication tracker:</h3>
            <div id="tracker-list"></div>
        </div>
    </div>

    <script>
        // Configuration
        const RULE = "{rule_slug}";
        const DATE = "{date_str}";
        const SUBREDDITS = {subreddits_json};
        const SUBREDDITS_URLS = {subreddits_urls_json};
        const PS_VARIATIONS = {ps_json};
        const STORAGE_KEY = `reddit-post-grammar-${{RULE}}-${{DATE}}`;

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

        // Copier l'explication + PS
        function setupCopyButton() {{
            const copyBtn = document.getElementById('copy-btn');
            copyBtn.addEventListener('click', async () => {{
                const explanation = document.getElementById('explanation').textContent;
                const ps = document.getElementById('ps-text').textContent;
                const textToCopy = explanation + '\\n\\n' + ps + '\\n\\nHappy learning!';

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
                        copyBtn.textContent = '📋 Copier Explication + PS';
                    }}, 2000);
                }}
            }});
        }}

        // Copier le titre
        function setupCopyTitleButton() {{
            const copyTitleBtn = document.getElementById('copy-title-btn');
            copyTitleBtn.addEventListener('click', async () => {{
                const title = document.getElementById('main-title').textContent;

                try {{
                    await navigator.clipboard.writeText(title);
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
    print("🎓 GÉNÉRATEUR DE POSTS GRAMMAIRE FRANÇAISE")
    if test_mode:
        print("🧪 MODE TEST (pas de liens Ablink)")
    print("=" * 60)
    print()

    # Boucle principale
    while True:
        # Étape 1 : Proposer une règle
        rule_data = propose_grammar_rule()

        print("💡 PROPOSITION DE RÈGLE DE GRAMMAIRE\n")
        print(f"Règle : {rule_data['rule']}\n")
        print("Exemples :")
        print(f"1. {rule_data['option1']}")
        print(f"2. {rule_data['option2']}")
        print(f"3. {rule_data['option3']}")
        print(f"\n✓ Option correcte : {rule_data['correct']}\n")

        # Demander validation
        choice = input("Est-ce que cette règle mérite un post ? (oui/non/autre) : ").strip().lower()

        if choice == 'non':
            print("\n🔄 Nouvelle proposition...\n")
            continue
        elif choice == 'autre':
            print("\n🔄 Nouvelle proposition...\n")
            continue
        elif choice != 'oui':
            print("⚠️  Réponse invalide. Tapez 'oui', 'non' ou 'autre'.")
            continue

        # Étape 2 : Générer l'explication
        explanation = generate_explanation(rule_data)

        # Boucle de modification de l'explication
        while True:
            print("\n" + "─" * 60)
            print("📝 DESCRIPTION GÉNÉRÉE :\n")
            print(explanation)
            print("─" * 60)

            modify_choice = input("\nC'est bon ? (oui/modifier/régénérer) : ").strip().lower()

            if modify_choice == 'oui':
                break
            elif modify_choice == 'régénérer':
                explanation = generate_explanation(rule_data)
            elif modify_choice == 'modifier':
                instruction = input("\nQu'est-ce que tu veux changer ? : ").strip()
                if instruction:
                    explanation = modify_explanation(explanation, instruction)
            else:
                print("⚠️  Réponse invalide. Tapez 'oui', 'modifier' ou 'régénérer'.")

        # Étape 3 : Générer le fichier HTML
        print("\n⏳ Génération du fichier HTML...")

        date_str = datetime.now().strftime('%Y-%m-%d')
        rule_slug = slugify(rule_data['rule'])

        # Créer le dossier posts/grammar/ si nécessaire
        os.makedirs('posts/grammar', exist_ok=True)

        html_content = generate_html(rule_data, explanation, date_str, test_mode=test_mode)
        output_filename = f"posts/grammar/{rule_slug}-{date_str}.html"

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ Fichier HTML créé : {output_filename}")
        print(f"   Tu peux maintenant l'ouvrir dans Chrome pour faire les captures d'écran !")

        # Demander si on continue
        again = input("\nGénérer un autre post ? (oui/non) : ").strip().lower()
        if again != 'oui':
            print("\n👋 À bientôt !")
            break

        print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    import sys
    # Vérifier si --test est passé en argument
    test_mode = '--test' in sys.argv
    main(test_mode=test_mode)
