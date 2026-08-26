# Code Fidelity Pass

Objetivo: melhorar Noronha pelo que pode ser feito em código antes de trabalho
manual de Terrain Builder/arte, preservando a liberdade de adaptar Fernando de
Noronha ao gameplay de DayZ.

## Regras

- Noronha é inspirada fortemente no arquipélago real, não uma obrigação 1:1.
- Gameplay, legibilidade e atmosfera podem justificar nomes, distâncias e
  densidades adaptadas.
- Não regenerar WRP, layers ou navmesh como efeito colateral de refactor.
- Mudança de código e mudança manual de terreno devem ser testadas separadamente.
- Assets autorais só entram depois de origem/licença e teste visual.

## Implementado nesta branch

### Authoring placement

`source/scripts/coastal_placement.py` foi convertido em ferramenta configurável e
determinística. Parâmetros e model pools ficam em
`source/scripts/placement_profiles.json`; o script oferece seleção de categorias,
seed, dry-run e relatório JSON de rejeições/placements.

Os filtros costeiros duplicados do script antigo foram removidos. No código
antigo eles faziam reeds, stones e shrubs passarem por regras amplas e depois
serem forçados novamente ao `COASTAL_COLOR`, anulando parte das regras anteriores.
Os arquivos de placement já gerados não foram alterados automaticamente.

Os modelos atuais de junco, pedras com musgo e arbustos continuam como
**placeholders de autoria** até uma seleção manual de assets tropicais/plausíveis.

### Nomes do mapa

`world/names.hpp` contém uma proposta de labels menores para o jogador, mantendo
class IDs, coordenadas, tipos e raios atuais. O arquivo ainda não está incluído
no `world/config.cpp` porque o checkout Git remoto não contém o último estado
local validado com RaG. Ele é deliberadamente staged/inativo até essa base ser
sincronizada.

### Build

`docs/BUILD.md` registra RaG DayZ Tools como builder validado e pboProject como
retirado do workflow oficial após omitir `Noronha.wrp` do `world.pbo` apesar de
reportar sucesso.

## Próximo código runtime

Depois de sincronizar o `world/config.cpp` local que carregou com RaG:

1. ativar `names.hpp` e validar com CfgConvert/RaG;
2. revisar `Sounds` e `Ambient` sem adicionar um PBO de scripts ainda;
3. revisar fog, céu e Lighting/Weather em experiências pequenas e reversíveis;
4. revisar clutter e parâmetros visuais que não exigem regenerar o WRP;
5. avaliar `Noronha_Scripts` somente se `CfgWorlds` não conseguir expressar um
   comportamento que realmente melhore o mapa.

## Backlog manual separado

Não ativar paths para arquivos inexistentes. Ficam para passes manuais futuros:
mapa turístico próprio, `envTexture`, global normal, middle texture, outside
satellite, surface palette/mask v2, vegetação, objetos costeiros e revisão final
de navmesh.
