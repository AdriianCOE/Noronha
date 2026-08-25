# Auditoria de organização de código

Data: 25/08/2026. Base: `baseline-2026-08-25`. Esta auditoria preserva o
comportamento de gameplay, CE, heightmap, WRP e navmesh.

## Matriz de classificação

| Path | Tipo | Owner | Seguro para refactor | Risco | Observações |
| --- | --- | --- | --- | --- | --- |
| `world/config.cpp` | RUNTIME_MANUAL | Noronha | Parcial | alto | configuração efetiva do mundo; 688 linhas e sem modularização comprovada pelo toolchain |
| `world/Noronha.wrp` | BINARY_RUNTIME | Noronha | não | alto | `DEV_AUTHORITATIVE_RUNTIME`, LFS |
| `data/config.cpp`, `data/layers/**` | RUNTIME_MANUAL / BINARY_RUNTIME | Noronha | config: parcial; layers: não | alto | layers são runtime aprovado; não reformatar binários |
| `sounds/config.cpp`, `sounds/*.ogg`, `$pboprefix$` | RUNTIME_MANUAL / BINARY_RUNTIME | Noronha | config: parcial | médio | prefixo virtual `Noronha\\sounds` validado |
| `navmesh/config.cpp`, `navmesh/navmesh.nm` | RUNTIME_MANUAL / BINARY_RUNTIME | Noronha | config: parcial; NM: não | alto | navmesh é LFS e imutável nesta auditoria |
| `ce/config.cpp`, `ce/init.c` | RUNTIME_MANUAL | Noronha | init: parcial | alto | `init.c` contém starter kit e regra de data |
| `ce/db/**`, `ce/env/**`, `ce/map*.xml`, `ce/cfg*.xml/json` | GENERATED_CE | CE Editor / Noronha | não | alto | validar, mas não reformatar ou rebalancear |
| `source/QGIS/**`, `source/layers.cfg` | AUTHORING_SOURCE | Noronha / workspace | limitado | alto | heightmap é fonte DEV autoritativa |
| `source/scripts/coastal_placement.py` | AUTHORING_SCRIPT | Noronha | parcial | médio | script determinístico com seed fixa; saída muda conteúdo do mundo |
| `docs/**`, `README.md` | DOCUMENTATION | Noronha | sim | baixo | deve refletir paths e workflow atuais |
| `.gitattributes`, `.gitignore` | DOCUMENTATION / Git policy | Noronha | parcial | médio | LFS define artefatos runtime versionados |

## Grafo de addons observado

```text
DZ_Data, DZ_Surfaces, DZ_Surfaces_Bliss
 ├─ Noronha_Sounds
 ├─ Noronha_data            (sem dependência declarada)
 └─ Noronha_navmesh         (sem dependência declarada)

Noronha (world) ───────────> Noronha_Sounds
Noronha_CE ────────────────> Noronha_Items
```

`Noronha` não depende de `Noronha_Items`: a referência a classnames de itens
ocorre na CE. Não alterar esse load order sem teste de montagem.

## Refactors seguros aplicados

- `source/scripts/coastal_placement2.0.py` foi renomeado para
  `coastal_placement.py`; a versão passa a ser responsabilidade do Git.
- O import explícito de `sys` foi adicionado porque o logger usa `sys.stdout`.
- `world/Noronha.hpp`, vazio e sem referências rastreadas, foi removido.
- A documentação foi alinhada aos paths de `P:\Noronha_Workspace` e ao estado
  atual de baseline/WRP.

## Itens mantidos sem mudança

### B — melhoria técnica que requer teste

- Padronizar `data/config.cpp` e `navmesh/config.cpp`: `CfgPatches`, campos e
  line endings divergem dos exemplos em `P:\DZ\worlds`. Os classnames públicos
  `Noronha_data` e `Noronha_navmesh` não foram renomeados.
- Adicionar/ajustar dependências de `Noronha_data` ou `Noronha_navmesh`: os
  exemplos oficiais declaram addons base, mas alterar a ordem de carregamento
  sem build/mount test é risco técnico.
- Modularizar `world/config.cpp`: `#include`/preprocessamento não foi provado
  com o PBO Project/Binarize do autor. Manter monolito até teste comparativo.
- Criar prefixes explícitos para PBOs sem `$pboprefix$`: depende da configuração
  real do PBO Project; não adicionar apenas por estética.

### C — revisão semântica obrigatória

- `ce/init.c`: a lógica de data não fixa todos os dias de janeiro/fevereiro;
  mudar isso altera o comportamento atual. O starter kit, RNG, saúde, camisa,
  comida, faca e quickbar não foram tocados.
- `coastal_placement.py`: filtros repetidos que exigem `COASTAL_COLOR` após
  aceitarem outras cores podem ser intencionais ou um erro histórico. Removê-los
  altera placement geográfico e exige revisão de conteúdo.
- Weather, iluminação, CE XML/JSON, tiers, fauna, spawns e materiais de terreno.

### D — não mudar

- `world/Noronha.wrp`, `navmesh/navmesh.nm`, heightmap e `data/layers/**`.
- XML/JSON exportados do CE Editor apenas para reformatar.

## Validações desta auditoria

- XML CE: 37 bem formados; JSON CE: 3 válidos.
- Python: compilação, import, setup do logger e `--help` do script aprovados.
- Os quatro OGG de sons e a dependência `Noronha_Sounds` permanecem presentes.
- Heightmap, WRP e navmesh devem manter os hashes registrados na baseline.
- `CfgConvert` não está presente nesta instalação do DayZ Tools; configs foram
  revisados estaticamente, mas alterações de config requerem validação pelo
  toolchain antes de serem aplicadas.
