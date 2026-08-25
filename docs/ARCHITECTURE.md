# Arquitetura

## Fontes de verdade

| Conteúdo | Fonte oficial | Papel das cópias |
| --- | --- | --- |
| Configuração/world/CE exportada/sons | `Noronha` | checkout de trabalho em `P:\Noronha` |
| Itens e PAA runtime | `Noronha_Items` | checkout em `P:\Noronha_Items` |
| Terrain Builder, CE Editor, GIS e PNG fonte | `NoronhaFiles` | workspace privado, não uma cópia concorrente do mapa |
| CE da missão offline | `Noronha/ce` | cópia gerada por `P:\tools\sync-ce.ps1` |

`Noronha2` é o projeto fonte do DayZ CE Editor. Seus exports são revisados e publicados em `Noronha/ce`; a missão offline não é um terceiro editor de balanceamento.

Os PAA/RVMAT em `data/layers/` e `navmesh/navmesh.nm` são artefatos runtime necessários ao mapa e estão versionados. Os PNG intermediários de layers, GIS e imagens editáveis ficam no workspace privado.

O WRP não foi localizado durante esta reorganização. `world/config.cpp` continua apontando para `world/Noronha.wrp`; a origem e a versão correta desse arquivo precisam ser recuperadas antes de uma build pública completa.
