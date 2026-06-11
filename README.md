# Anki Lookup

Anki Lookup is a desktop Anki add-on for looking up text directly while reviewing
cards.

It is designed to provide:

- Hold-to-scan word lookup with a configurable modifier key.
- Local Yomitan-compatible dictionaries for multiple languages.
- Google Translate and DeepL translation actions.
- A configurable popup with themes, fonts, sizing, and layout controls.
- Direct creation of new Anki notes from lookup results.

> **Development status:** Pre-alpha. Hold-to-scan, local Yomitan term dictionary
> imports, and real dictionary results are available. Translation providers are still
> being implemented.

## Current Preview

While reviewing a card, hold **Shift** and move the pointer across text. Anki Lookup
will detect the word under the pointer and open the lookup popup. Press **Escape** to
close it. You can also select text and press **Ctrl+Shift+L**.

Import dictionaries from **Tools > Anki Lookup: Manage Dictionaries...**. The current
version supports Yomitan format-3 term dictionaries. Kanji-only and pitch
metadata-only archives are detected but are not searchable yet.

## Installation

1. Download the latest `.ankiaddon` file from the GitHub Releases page.
2. Open Anki Desktop.
3. Select **Tools > Add-ons**.
4. Choose **Install from file** and select the downloaded `.ankiaddon` file.
5. Restart Anki.

Anki Lookup supports Anki Desktop. AnkiMobile and AnkiDroid do not load desktop
add-ons.

## Dictionary Files

Dictionary files are not bundled. Users must provide dictionaries they are permitted
to use and import them through the add-on's dictionary manager.
