# Blog Text Automation Process

Clear instructions on how the blog text automation process works.

## Initial Setup

1. Ensure you have keywords in the `content/keywords/keywords.txt` file (one per line)
2. Make sure you're logged into your Google account in Chrome

## Running the Automation

1. Activate your virtual environment:

   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the script:

   ```
   python src/main.py
   ```

3. When Playwright opens Chrome:

   - First time: Complete Google login if needed
   - The script will navigate to Claude.ai automatically
   - It will use the project URL: https://claude.ai/project/434990a3-f303-4f35-85cd-490c991139d4

4. For each keyword, the script will:
   - Take a keyword from keywords.txt
   - Navigate to Claude
   - Submit the following prompt template, replacing {Hauptstichwort} with the keyword:

```
THEMA/KEYWORD: {Hauptstichwort}

SCHREIBAUFTRAG: IMMOBILIEN-FACHTEXT

TEXTLÄNGE: nicht kürzer als 1500 Wörter und nicht länger als 1600 Wörter. GANZ WICHTIG.

SCHREIBSTIL:
• Formelle, fachkundige deutsche Immobiliensprache
• Menschlicher Schreibfluss mit natürlichen Variationen
• Regional geprägte Ausdrucksweise (norddeutsch/süddeutsch/Hochdeutsch)
• Bitte Strukturiert und informativ
• Hochdeutsch

STRUKTURVORGABEN:
• 1x H1-Überschrift (enthält Hauptstichwort)
• 3-7x H2-Überschriften (kann auch Hauptstichwort enthalten)
• 4-20x H3-Überschriften (kann auch Hauptstichwort enthalten)
• Absätze unterschiedlicher Länge (kurz, mittel, lang)
• Variierende Satzstrukturen (einfach, komplex, Fragen, Ausrufe)
• Einbau von Füllwörtern und Gedankensprüngen wie in natürlicher Sprache

INHALTLICHE ELEMENTE:
• Persönliche Anekdoten aus Maklererfahrungen einbauen
• Regionale Bezüge zu deutschen Städten/Bundesländern (immer verschiedene nutzen wenn möglich)
• Fachwissen mit subjektiven Einschätzungen mischen
• Aktuelle Markttrends mit historischen Entwicklungen verbinden
• Praktische Tipps aus direkter Erfahrung geben
• Perspektivwechsel einbauen wenn notwendig

TABELLENVORSCHLAG: Eine Vergleichstabelle zu verschiedenen Aspekten von {Hauptstichwort} (Lage, Vor-/Nachteile, preisliche Unterschiede, andere vergleiche, etc)

DIAGRAMMVORSCHLAG: Ein Faktendiagramm zur Preisentwicklung oder andere Entwicklungen von {Hauptstichwort} in verschiedenen Stadtlagen

KEYWORD-PLATZIERUNG:
• Hauptstichwort "" 12-20 mal natürlich im Text verteilen
• Verwandte Stichwörter einfließen lassen
• Hauptstichwort-Variationen durch Flexion und Komposita nutzen

WEITERE ANTI-KI-MERKMALE:
• Berufsspezifischen Fachjargon mit umgangssprachlichen Ausdrücken mischen
• Deutsche Sprichwörter oder regionale Redewendungen verwenden
• Persönliche Meinungen äußern

AUTOR-PERSONA: Ein erfahrener Immobilienmakler aus Deutschland mit mehreren Jahren Berufserfahrung, der für immobilienindernaehe.com schreibt. Hat eine Vorliebe für ältere Häuser und kennt sich besonders gut mit urbanem Wohnraum aus. Auch Neubau wird gerne gemocht.
```

5. The script will:
   - Wait for Claude to finish writing
   - Save the generated text as a markdown file in `content/completed/{keyword}/`
   - Mark the keyword as processed in processed_keywords.txt
   - Move to the next keyword

## Output Files

- Each generated blog post will be saved in its own directory under `content/completed/`
- The filename format is: `{keyword}.md`
- Keywords are tracked in `processed_keywords.txt` to avoid duplicates

## Troubleshooting

If the script encounters issues:

1. Check the screenshots/ folder for error state images
2. Ensure your Google login is still valid
3. Check that Claude.ai is accessible
4. Delete processed_keywords.txt to reprocess all keywords

## Notes

- The script maintains a persistent browser session to avoid frequent logins
- Screenshots are saved during the process for debugging
- Claude.ai may have maintenance windows or downtimes
