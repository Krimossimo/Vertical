# Vertical — Shorts automatiques depuis tes VOD Twitch

Vertical analyse une VOD (même 2 h), repère les meilleurs moments et les transforme en Shorts
9:16 prêts à publier sur YouTube Shorts, TikTok et Instagram Reels. **Tout tourne en local sur ton PC,
gratuitement** : aucun abonnement, aucune API payante.

## Lancer

| Quoi | Comment |
|---|---|
| Première installation | Double-clic sur **`Installer.bat`** (vérifie ce qui est déjà présent, installe le reste dans ce dossier) |
| Utilisation quotidienne | **`Vertical.exe`** ou le raccourci **Vertical** sur le Bureau |
| Dépannage (avec console) | **`Lancer Vertical.bat`** |
| Ouvrir dans le navigateur | `Lancer Vertical.bat --browser` |
| Diagnostic | `Lancer Vertical.bat --check` |

## Utilisation

1. **Choisir une VOD** (MP4, MKV, MOV, TS, FLV…).
2. **Analyse** : choisis le jeu (ou « Détection automatique »), la durée des Shorts et leur nombre (5 à 10),
   puis « Lancer l'analyse ». Compte 10 à 20 min pour 2 h de VOD sur une RTX 3060.
3. **Moments** : pour chaque passage proposé tu vois le score, la raison du choix, la transcription.
   Lis le passage, ajuste le début/la fin (poignées vertes, boutons ±1 s, « ici »), choisis le cadrage,
   vérifie l'**Aperçu 9:16**, puis **Valider** ou **Rejeter**. Tu peux aussi ajouter un passage oublié.
4. **Export** : règle les sous-titres (police, taille, couleurs, mot surligné, position) et la qualité,
   puis « Exporter ». Un dossier `<nom de la VOD> - Shorts` est créé à côté de la VOD (modifiable) avec :
   - `01 - Titre.mp4` … (1080×1920, H.264 NVENC, AAC 192 kb/s, volume normalisé -14 LUFS)
   - `01 - Titre.txt` : titre, variantes, description et hashtags pour YouTube / TikTok / Instagram
   - `PUBLICATION.md` et `shorts.json` : récapitulatif

## Comment les moments sont choisis

| Signal | Outil local |
|---|---|
| Paroles + timestamps au mot | faster-whisper `large-v3-turbo` sur GPU (repli : medium → small CPU) |
| Cris, pics de volume, montées soudaines | analyse audio (volume relatif à ton niveau habituel, brillance de la voix) |
| Rires | modulation de l'enveloppe sonore + « mdr/ptdr/haha » + IA audio AST |
| Exclamations, jurons, répétitions | dictionnaire FR/EN (« non non non », « c'est pas possible », « let's go »…) |
| Événements de jeu | mots-clés du profil de jeu + CLIP (combat de boss, écran de mort, victoire, parade, combo…) |
| Intensité visuelle | mouvement, flashs, teinte rouge (dégâts), fondu au noir (mort) |
| Sons de jeu | IA audio AST (explosions, impacts, acclamations) |

Les signaux sont fusionnés en une courbe d'intérêt seconde par seconde, les pics sont analysés en
profondeur, puis chaque passage est découpé avec du contexte avant l'action et des coupes calées sur
les pauses de parole (jamais au milieu d'un mot).

**Profils de jeux** (`vertical/profiles/*.json`) : Phantom Blade Zero, Action/Souls-like, FPS/Battle royale,
MOBA, Combat, Horreur, Course, Sport, Sandbox, Générique. Le jeu est détecté via le nom du fichier, sinon
par l'image (CLIP). Pour ajouter un jeu, copie `phantom_blade_zero.json` et adapte mots-clés et descriptions.

## Cadrages 9:16

- **Facecam en haut + jeu** : la webcam est détectée automatiquement (bouton « 📷 Facecam » pour ajuster).
- **Recadrage intelligent** : la fenêtre 9:16 suit l'action à l'écran, avec un lissage pour éviter les à-coups.
- **Recadrage centré** et **Image entière + fond flou**.

## Analyse Claude avec ton abonnement (sans API)

Onglet Moments → **✦ Analyse Claude (manuel)** : copie le prompt généré, colle-le dans claude.ai (tu peux
glisser les miniatures du dossier proposé), puis recolle la réponse JSON dans Vertical. Titres, descriptions,
hashtags, bornes et avis sont mis à jour. Aucun frais API.

## Options gratuites

- **Ollama** (local) : s'il est installé et lancé (`ollama pull qwen2.5:7b`), Vertical l'utilise pour rédiger
  les titres. Sinon, un générateur intégré prend le relais.

## Solutions de secours

| Si… | alors… |
|---|---|
| CUDA indisponible pour Whisper | transcription CPU (modèle `small`) |
| PyTorch / modèles IA absents | analyse audio/vidéo classique (mode « Rapide ») |
| NVENC indisponible | encodage libx264 (même qualité, plus lent) |
| Format non lisible dans l'aperçu (ex. .ts) | bouton « Créer une version de prévisualisation » |
| Fenêtre native (WebView2) indisponible | ouverture dans le navigateur |
| Pas de transcription | pas de sous-titres, le reste fonctionne |

## Dossiers

- `data/` : projets (cache d'analyse, miniatures, aperçus), réglages, `vertical.log`
- `models/` : modèles IA téléchargés (≈ 3 Go)
- `tools/` : FFmpeg, uv et Python portables
- `.venv/` : environnement Python

Supprimer un projet dans l'accueil n'efface ni la VOD ni les Shorts exportés.

Polices incluses : Anton, Bebas Neue, Bangers, Poppins, Archivo Black (SIL OFL) et Luckiest Guy (Apache 2.0).
