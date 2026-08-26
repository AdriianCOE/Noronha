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
class IDs, coordenadas, tipos e raios atuais. O `world/config.cpp` agora o
inclui diretamente; `CfgConvert -test` validou o include relativo, padrão também
usado pelo source local de Nyheim para partes de configuração do mundo.

### Ambiência runtime conservadora

| Área | Antes | Depois | Estado |
| --- | --- | --- | --- |
| Costa | `river_close_loop` | `ambients\\coast` vanilla | RUNTIME_VISUAL_REVIEW |
| Pólen sem vento | custo fixo, inclusive chuva/mar | suprimido por chuva e mar | RUNTIME_VISUAL_REVIEW |

Não houve ajuste de Weather, Lighting, fog, clutter ou ILS: os valores existem,
mas uma leitura de config não prova efeito visual, custo ou orientação no WRP.
Nyheim, Chernarus, Livonia e Sakhal servem como referências de arquitetura e
faixas de configuração; nenhum valor foi copiado para Noronha.

### Placement profiles

O profile preserva o comportamento de geração legado e declara os biomas
conceituais `beach`, `rocky_coast`, `dry_coast`, `dry_shrub`, `green_shrub`,
`wetland` e `urban_edge`. Eles reutilizam exclusivamente as quatro cores de
surface mask existentes e são validados contra nomes de surfaces conhecidos;
nenhuma nova cor, máscara ou output foi gerado.

### Build

`docs/BUILD.md` registra RaG DayZ Tools como builder validado e pboProject como
retirado do workflow oficial após omitir `Noronha.wrp` do `world.pbo` apesar de
reportar sucesso.

## Próximo código runtime

Próximos passos runtime:

1. testar `names.hpp`, costa e pollen em build RaG/DayZ;
2. revisar fog, céu e Lighting/Weather em experiências pequenas e reversíveis;
3. revisar clutter e parâmetros visuais que não exigem regenerar o WRP;
4. fazer `MANUAL_TB_REVIEW` de ILS contra objetos do aeroporto no WRP;
5. avaliar `Noronha_Scripts` somente se `CfgWorlds` não conseguir expressar um
   comportamento que realmente melhore o mapa.

## Backlog manual separado

Não ativar paths para arquivos inexistentes. Ficam para passes manuais futuros:
mapa turístico próprio, `envTexture`, global normal, middle texture, outside
satellite, surface palette/mask v2, vegetação, objetos costeiros e revisão final
de navmesh.
