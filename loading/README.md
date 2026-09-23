# Noronha loading screen

Client-side DayZ UI addon for the Fernando de Noronha loading, login queue, and login-time screens.

## Runtime contract

- Package prefix: `Noronha\loading`
- PBO source root: `P:\Noronha\loading`
- Background: `set:noronha_loading image:loading1`
- Map signature: `noronha_logo_ui.edds`, rendered directly by dedicated non-interactive layouts in the loading workspace and PC main menu.
- Main loading uses the native `loading_screen_3_mask.edds` reveal mask and leaves the vanilla lower hint/progress layout in place.
- The DayZ logo remains the vanilla `ImageLogoMid` / `dayz_logo` widget. The Noronha signature is an additional top-right widget, so it is not affected by the background reveal mask.
- Queue and login-time layouts retain their native static backgrounds because those vanilla layouts do not use the progress reveal mask.
- The addon has no map-config dependency, so it can be tested alone in DayZDiag and loaded beside the official map.

## Rebuild

The editable sources and master provenance are recorded in `data/ASSET_PROVENANCE.md`. Build only this source folder with RaG:

```powershell
python P:\Noronha_Workspace\tools\RaG-DayZ-Tools-20260825\rag_pbo_builder_gui.py build --source P:\Noronha --addons loading --project-root P: --output P:\Noronha_Builds\test\@FernandoDeNoronha-loading-20260923 --pbo-name Noronha_Loading --cfgconvert "C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\CfgConvert\CfgConvert.exe" --exclude-extensions .md --force --no-binarize --convert-config --no-sign --preflight
```

The output is intentionally unsigned and isolated for DayZDiag testing. The approved logo source and its transparent UI derivative are documented in `data/ASSET_PROVENANCE.md`.
