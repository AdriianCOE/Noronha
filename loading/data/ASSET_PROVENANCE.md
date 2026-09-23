# Loading-screen asset provenance

- Active approved original master: `C:\Users\drioj\Downloads\image.jpg`
  - Resolution: `3840 x 2160` (`16:9`)
  - Size: `2,112,902` bytes
  - SHA-256: `552562E85BA399297AAE87AE8B9F583F47511565CB9DB5DE208F3872372E690D`
- Source archive copy: `P:\Noronha_Workspace\assets-src\loading\source\noronha_map_capture.jpg` (byte-identical to the approved master)
- Active visual-treatment source: `P:\Noronha_Workspace\assets-src\loading\derived\noronha_loading_official_v3_map_capture.png`
  - Resolution: `1672 x 941`; SHA-256: `16022BE8779F5E0F8318F9CB6879D63627029AFD5FA8CC5DED642CFF3D1EBE5D`
  - Non-destructive v3 edit of the actual in-map capture: muted olive/charcoal palette, green-gray shadows, broad humid haze, overcast sky, fine restrained grain, and a gentle vignette. The composition, characters, vehicles, road, tower, buildings, and subject placement remain the same.
- Active runtime derivative: `P:\Noronha_Workspace\assets-src\loading\derived\noronha_loading_1_co.png`
  - Resolution: `1920 x 1080`; SHA-256: `2A6DE35698D595C27165BBA9AAC10E502AA70C9AF9F2C9E4E7D3B5862B58956F`
- Active runtime atlas: `P:\Noronha_Workspace\assets-src\loading\derived\noronha_loading_atlas.png`
  - Resolution: `2048 x 2048`; SHA-256: `C00F912D933D370CE9203DBC9ACA30B738062E5020718D4CA89D633E9160761D`
- Runtime asset in this PBO: `noronha_loading.edds` (SHA-256 `019AEB11B5B4DC8717162963FD1E7C6FDDDE7389E0835E3B86D1A34DC5D08DB3`), registered through `noronha_loading.imageset` as `set:noronha_loading image:loading1`.

The approved capture is not edited, resized, or overwritten. The v3 treatment is a separate source, then normalized to the existing `1920 x 1080` Imageset region and placed in the existing `2048 x 2048` atlas. It adds no text, logo, UI, objects, crop, or heavy visual effect. Earlier visual-treatment sources are not referenced by the active derivative, atlas, EDDS, or Imageset.

## Noronha UI logo

- Approved source (preserved unchanged): `P:\Noronha_Workspace\3742535229\logo.png`
  - Resolution: `2172 x 724` (`3:1`); format: RGB PNG
  - Size: `1,373,433` bytes
  - SHA-256: `E71548FBCC17A9A9F08A37A60DF079AAF100D5EB2F579EBF2D64AB4EDD1B772A`
- UI derivative: `P:\Noronha_Workspace\assets-src\loading\derived\noronha_logo_ui.png`
  - Resolution: `1024 x 244`; format: RGBA PNG
  - Derived without redrawing: crop `232,154 1710 x 407`, with the solid-black source canvas converted to alpha and a 8-level alpha floor before proportional resampling.
  - SHA-256: `9F70A451EA5DA3DCC24BD0451D7B8BF9141D601F741B8B9E2FF572B43A265029`
- UI atlas source: `P:\Noronha_Workspace\assets-src\loading\derived\noronha_logo_ui_atlas.png`
  - Resolution: `1024 x 512`; SHA-256: `CAB6315FAF996CDCFFC22B955A2F3F1653CAD90F253B04288F4A7D5777829EF5`
- Runtime asset in this PBO: `noronha_logo_ui.edds` (SHA-256 `686713EFC4496F68CE794B0DF4D6E2A0066AD4AC77002D7EA45721AD26D6486A`), loaded directly by the two logo layouts through `imageTexture "{A1AB393B3727546D}Noronha/loading/data/noronha_logo_ui.edds"`.

The transparent derivative has no backing panel, outline, shadow, added text, or logo redesign. It is used as a secondary map signature in the upper-right loading workspace and below the upper-right main-menu controls. The vanilla DayZ logo remains untouched.
