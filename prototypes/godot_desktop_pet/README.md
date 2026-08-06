# Godot Desktop Pet Shell Prototype

Isolierter Godot-4-Windows-Prototyp zur Prüfung von transparentem, rahmenlosem
Always-on-top-Fenster, polygonalem Maus-Passthrough, Dragging und Esc. Die helle
`Polygon2D`-Silhouette ist direkt in `main.tscn` definiert und dient zugleich als
Mausregion. Er enthält keine PET-Assets, keine Python-Runtime-Anbindung und kein Rig.

## Im Godot-Editor starten

1. Godot 4 öffnen.
2. **Import** wählen und `project.godot` aus diesem Ordner auswählen.
3. Die Szene `main.tscn` öffnen und mit **F6** oder über **Run Project / F5** starten.

## Über PowerShell starten

Wenn Godot in `PATH` liegt:

```powershell
godot --path .
```

Alternativ den vollständigen Pfad zur Godot-4-EXE verwenden:

```powershell
& "C:\Path\To\Godot_v4.x-stable_win64.exe" --path .
```

Für einen Parse-/Start-Check ohne sichtbares Fenster:

```powershell
godot --headless --path . --editor --quit
```

## Manuelle Windows-Prüfliste

- Hintergrund ist außerhalb der violetten Figur transparent.
- Fenster ist rahmenlos und bleibt vor anderen Fenstern.
- Klicks außerhalb der Figur erreichen das darunterliegende Programm.
- Linksklick auf die Figur zieht das gesamte Fenster.
- `Esc` beendet den Prototyp.
- Die Figur ist beim Start vollständig sichtbar und nicht abgeschnitten.
- Die Godot-Ausgabe enthält `transparency_available=true`, die aktiven
  Fenster-/Viewport-Flags und `passthrough_polygon_points=25`.
