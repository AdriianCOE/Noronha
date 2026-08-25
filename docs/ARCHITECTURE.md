# Arquitetura

## Fontes de verdade

| Conteúdo | Fonte oficial | Papel das cópias |
| --- | --- | --- |
| Configuração/world/CE exportada/sons | `Noronha` | checkout de trabalho em `P:\Noronha` |
| Itens e PAA runtime | `Noronha_Items` | checkout em `P:\Noronha_Items` |
| Terrain Builder, CE Editor, GIS e PNG fonte | `NoronhaFiles` | workspace privado, não uma cópia concorrente do mapa |
| CE da missão offline | `Noronha/ce` | cópia gerada por `P:\Noronha_Workspace\tools\sync-ce.ps1` |

`P:\Noronha_Workspace\ce-editor` é o projeto fonte do DayZ CE Editor. Seus exports são revisados e publicados em `Noronha/ce`; `P:\Noronha_Workspace\mission-test` não é um terceiro editor de balanceamento.

Os PAA/PNG/RVMAT em `data/layers/` e `navmesh/navmesh.nm` são artefatos runtime necessários ao mapa e estão versionados. Os RVMAT referenciam os PNG diretamente; por isso esses PNG não podem ser tratados como intermediários descartáveis. GIS e imagens editáveis ficam no workspace privado.

`world/Noronha.wrp` é `DEV_AUTHORITATIVE_RUNTIME`, rastreado por Git LFS e documentado em [TERRAIN.md](TERRAIN.md). Ele não é automaticamente equivalente a uma versão LIVE da Workshop.
