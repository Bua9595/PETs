# PET Agent Contract

## Projektziel

Dieses Projekt baut lokale Desktop-Pets.

Ein Pet ist nicht nur ein Sprite-Sheet.
Ein Pet besteht aus:

* Charakterkonzept
* sauberen Full-Body-Sprites
* Manifest
* Runtime-States
* Desktop-Verhalten
* QA-Artefakten
* später Multi-Pet-Interaktion

Das langfristige Ziel:

* Pets laufen eigenständig auf dem Desktop herum.
* Pets reagieren auf Maus/User-Aktionen.
* Pets können an Fenstern, Ordnern oder Desktop-Elementen visuell spielen.
* Pets manipulieren keine echten Dateien destruktiv.
* Mehrere Pets können später miteinander interagieren.

## Agentenrollen

### Cursor Agent

Cursor ist primär zuständig für:

* Repo-Struktur
* Code-Änderungen
* Ordnerstruktur
* Dokumentation
* Runtime-Architektur
* einfache QA-Skripte
* technische Integration
* Prüfung, welche Dateien wirklich verwendet werden

Cursor darf NICHT:

* Pfade erfinden
* alte Assets ungeprüft verwenden
* schlechte Sprites als final markieren
* große kreative Sprite-Sheets erzeugen
* README mit falschen Erfolgsmeldungen füllen

### Codex Agent

Codex ist primär zuständig für:

* technische Asset-Verarbeitung
* Sprites schneiden
* Atlas packen
* Manifest bauen
* GIF-Previews erzeugen
* QA-Berichte erzeugen
* Runtime mit konkreten finalen Assets testen

Codex darf NICHT:

* aus schlechten Rohbildern blind finale Pets bauen
* ungeprüfte Sheets verwenden
* `accepted=true` melden, wenn visuelle Qualität schlecht ist
* README als Werbetext schreiben
* neue Pfade erfinden

### Bild-/Video-Tools

Bild-/Video-Tools dienen nur für:

* Rohmaterial
* Referenzen
* Motion-Ideen
* neue Sprite-Kandidaten

Sie sind NICHT automatisch finale Asset-Quelle.

## Verbindliche Asset-Regel

Nur Dateien unter `assets/source_approved/` dürfen später als finale Sprite-Quelle verwendet werden.

Rohbilder liegen unter:

* `assets/source_raw/`

Verworfene oder fehlerhafte Kandidaten liegen unter:

* `assets/source_rejected/`

Contact-Sheets mit bekannten Fehlern dürfen NICHT aus `source_raw` direkt in Runtime-Assets übernommen werden.

## Full-Body-Regel

Jeder aktive Sprite muss Full-Body sein.

Full-Body bedeutet:

* Kopf sichtbar
* Haare / Hut sichtbar
* Oberkörper sichtbar
* beide Arme sichtbar
* beide Hände sichtbar
* beide Beine sichtbar
* beide Füße sichtbar
* Kleidung vollständig genug sichtbar
* Accessoires nicht unlogisch abgeschnitten
* keine falschen oder zusätzlichen Gliedmaßen
* keine verdrehten Arme/Beine
* keine fehlende Kleidung
* keine fremden Charaktere
* keine Textlabels
* keine Nummern
* keine Wasserzeichen

Ausnahme:
Ein Prop darf Körperteile teilweise verdecken, wenn das logisch ist, z. B. Laptop, Kissen, Controller.
Das muss in der QA-Note stehen.

## Qualitätsregel

Ein Sprite ist abzulehnen, wenn:

* Körperteile fehlen
* nur Oberkörper sichtbar ist
* Hände/Füße abgeschnitten sind
* Arm oder Bein falsch herum am Körper hängt
* Figur andere Identität/Stilrichtung annimmt
* Pose keinen State-Nutzen hat
* Sprite bereits nahezu identisch vorhanden ist
* Text/Zahlen/Labels enthalten sind
* Hintergrund das Ausschneiden erschwert
* Pose gegen Charakterlogik verstößt

## Ruffy / PET1 Charakterregel

PET1 ist ein Ruffy-inspirierter Rubber-Pirate-Desktop-Pet.

Kernmerkmale:

* schwarzes Haar
* Strohhut
* rote offene Weste / Jacke
* blaue Shorts
* Sandalen
* gelbe Schärpe
* energisch, mutig, verspielt
* Gummikörper
* Gear-States 2, 3, 4, 5

Wichtig:

* normale Form bleibt normale Form
* Gear2: Dampf/Steam, schneller/angespannter, aber normale Körperform
* Gear3: aufgeblasene einzelne Gliedmaßen durch in Daumen/Hand beißen und Luft einblasen; keine gegessene Hand, keine falschen Körperteile
* Gear4: kräftigere Form, dunkle/rote Haki-Arme, Steam, muskulöser
* Gear5: weiße Haare, weiße Kleidung, cartoonig/frei, Nika-artige Energie, aber keine kaputte Anatomie

## PET2 Charakterregel

PET2 ist ein Chibi-Girl-Desktop-Pet.

Kernmerkmale:

* lange braune Haare
* große blaue Augen
* violette Haaraccessoires
* schwarz/pinkes Outfit
* süß, freundlich, verspielt
* Streamer-/Gaming-/Social-Vibe
* Counter-Strike-/Competitive-Gaming darf als niedlicher State vorkommen

Keine Gewalt-/Shooter-Übertreibung.
Gaming-States sollen niedlich und pet-tauglich bleiben.

## Arbeitsprozess

Jeder Agent arbeitet nur in freigegebenen Schritten.

Standardprozess:

1. Reale Struktur prüfen
2. Status berichten
3. Nur freigegebene Dateien bearbeiten
4. Artefakte erzeugen
5. QA ausgeben
6. README/Doku aktualisieren
7. Ergebnisbericht liefern
8. Auf menschliche Abnahme warten

Kein Agent darf eigenständig in den nächsten Projektabschnitt springen.

## Abnahme

Ein Schritt ist erst fertig, wenn der Nutzer oder prüfende Assistant sagt:

* angenommen
* weiter
* passt
* fortfahren

Vorher keine Folgearbeiten starten.
