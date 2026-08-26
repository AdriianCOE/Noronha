# Referencias de engenharia

Este documento define como Noronha usa referencias externas sem transformar o projeto em uma copia de outro mapa ou framework.

## Principio

Cada referencia tem um papel diferente. A pergunta nao e "qual repo devemos copiar?", mas "qual fonte e mais forte para este tipo de decisao?".

## Matriz de uso

| Fonte | Usar para | Nao usar como |
|---|---|---|
| DayZ vanilla / DayZ Tools | APIs, configs, paths, comportamento engine, exemplos oficiais | prova de que um valor visual e ideal para Noronha |
| `kerkkoh/nyheim` | arquitetura de mapa, world/weather modular, assets proprios, surfaces, prior art de terrain | template que precisa ser replicado 1:1 |
| `willy92wins/DayZ-Modding-Knowledge-Pack` | playbooks, preflight, anti-confabulacao, client/server, sons, P3D, texturas, validacao | substituto do source vanilla ou do teste in-game |
| `willy92wins/dayz-mcp` | QA runtime, logs, tempo/clima, teleport, raycast, surface query, screenshots e telemetria | dependencia do mapa publicado |
| `TrueDolphin/references` | exemplos pequenos, ideias de scripts e tooling | fonte de codigo para copiar sem revisar licenca |

## DayZ Modding Knowledge Pack

Repositorio: <https://github.com/willy92wins/DayZ-Modding-Knowledge-Pack/>

Uso recomendado em Noronha:

- consultar o playbook relevante sob demanda, sem carregar o pack inteiro;
- validar toda API Enforce/config importante contra source vanilla atual;
- usar o material de som para revisar `CfgWorlds::Sounds`, SoundSets/Shaders e controllers ambientais;
- avaliar `dayz-script-validator` como camada opcional do preflight de Noronha;
- usar P3D/texture/model tooling quando Noronha ganhar assets proprios;
- manter as afirmacoes de verificacao separadas em STATIC / BUILD / RUNTIME.

O repo e MIT. Mesmo assim, Noronha deve preferir links, referencias e adaptacoes pequenas a importar grandes blocos do pack para dentro do mapa.

### Regra de evidencia adotada

Antes de escrever uma API DayZ desconhecida:

1. localizar no source vanilla atual;
2. confirmar assinatura e modulo/lado de execucao;
3. somente entao implementar;
4. registrar o que foi verificado e o que ainda depende de runtime.

## DayZ-MCP

Repositorio: <https://github.com/willy92wins/dayz-mcp>

Papel planejado: **ferramenta DEV/QA externa**.

Nunca adicionar `DayZ_MCP` a `requiredAddons[]`, nunca empacotar no release de Noronha e nunca exigir o addon para jogadores.

Casos de uso prioritarios para o mapa:

- comparar Lighting/Weather/Fog em cameras e horarios fixos;
- teleportar para POIs de teste;
- aplicar estados de tempo reproduziveis;
- consultar `surface_query` e raycasts ao revisar surfaces/materials;
- capturar logs depois de uma build;
- produzir fixtures de smoke test repetiveis para Remedios, Sancho, Sueste, Aeroporto, Porto e Pico.

### Matriz inicial de QA runtime

| Fixture | Hora | Clima | Objetivo |
|---|---:|---|---|
| Remedios noon | 12:00 | clear | exposicao, clutter, leitura urbana |
| Sancho golden | 17:30 | clear | low sun/golden hour e costa |
| Sueste wet | 15:00 | overcast/rain | fog, chuva, vegetacao e contraste |
| Porto storm | 16:00 | storm | mar, vento, visibilidade e audio |
| Pico night | 00:00 | clear | ceu, estrelas, escuridao e horizonte |
| Aeroporto dawn | 05:30 | clear | transicao de amanhecer e leitura de pista |

As coordenadas/cameras devem ser capturadas do mapa real de Noronha apenas quando o harness for configurado. Nao inventar coordenadas neste documento.

## TrueDolphin references

Repositorio: <https://github.com/TrueDolphin/references/tree/main>

Foi observado como uma colecao de exemplos (`Math`, `bat files`, `init.c files`, `python scripts`, etc.), nao como framework de mapa.

Ideias uteis:

- ferramentas pequenas de analise de terreno/heightmap;
- scripts temporarios de ambiente de build;
- harness de servidor/teste;
- exemplos de Enforce/Expansion para pesquisa pontual.

Durante a auditoria de 2026-08-26 nao foi observado um arquivo `LICENSE` na raiz. Portanto, a politica de Noronha e **reference-only** ate haver permissao/licenca clara. Reimplementar a ideia com codigo proprio quando util.

## Nyheim

Repositorio: <https://github.com/kerkkoh/nyheim>

Continua sendo a melhor referencia entre estas para mapa completo. Aprendizados prioritarios:

- identidade visual propria em vez de textures globais herdadas de outro mapa;
- weather/world configuration separavel por responsabilidade;
- surfaces e assets intencionais;
- source de autoria organizado;
- modularidade apenas quando justificada pelo conteudo.

Noronha nao deve copiar a quantidade de PBOs ou assets de Nyheim. O projeto e menor e deve continuar enxuto.

## Pipeline de verdade de Noronha

```text
AUTHORING
Terrain Builder / GIS / Python
        |
        v
SOURCE
Noronha + Noronha_Workspace
        |
        v
STATIC VALIDATION
Noronha validator + CfgConvert + linters opcionais
        |
        v
BUILD
RaG DayZ Tools
        |
        v
ARTIFACT VALIDATION
PBOs / paths / tamanho / hashes / manifest
        |
        v
RUNTIME QA
DayZ manual e, futuramente, DayZ-MCP
        |
        v
KEEP / ADJUST / REVERT
```

## Prioridade de integracao

1. aplicar as regras do `AGENTS.md` imediatamente;
2. usar Knowledge Pack durante o Code Fidelity Pass, especialmente sons/configs;
3. manter RaG como builder e acrescentar preflight/manifest, sem substituir a toolchain;
4. preparar DayZ-MCP apenas como ambiente DEV quando chegar a fase de tuning visual repetitivo;
5. criar tooling proprio de terrain no Workspace quando uma ideia de TrueDolphin resolver um problema real;
6. introduzir P3D/texture tooling quando os primeiros assets proprios relevantes forem criados.