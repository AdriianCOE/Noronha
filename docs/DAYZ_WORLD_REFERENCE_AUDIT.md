# Referência de mundos DayZ e toolchain

Data da leitura: 25/08/2026. Escopo: somente leitura em `P:\DZ\worlds` e
testes temporários. Os exemplos são configurações de mundos instalados (alguns
deRap) e são evidência descritiva, não um contrato de build para Noronha.

## Exemplos observados

| PATH EXAMPLE | PATTERN | RELEVANCE | CAN APPLY | NEEDS TEST | NOT APPLY |
| --- | --- | --- | --- | --- | --- |
| `Wickedisland/data/config.cpp` | `CfgPatches`; `units`, `weapons`, `requiredVersion`, `requiredAddons` | Referência de metadados explícitos para um PBO de data | Formatação/metadata somente como proposta | Sim: binário muda no teste controlado | Não copiar o nome ou dependências de Wickedisland |
| `Wickedisland/navmesh/config.cpp` | `CfgPatches` com metadata explícita | Referência de capitalização e estrutura | Apenas proposta de estilo | Sim: binário muda no teste controlado | Não alterar `Noronha_navmesh` ou sua dependência vazia por analogia |
| `sakhal/navmesh/config.cpp` | `requiredAddons[] = {}` também é usado por mundo oficial | Confirma que dependência vazia não é, por si, um erro de estilo | Nenhuma alteração necessária | Sim, se a dependência de Noronha for revista | Não inferir que todo navmesh deve depender de `DZ_Data` |
| `Wickedisland/ce/config.cpp` | addon CE declara `CfgPatches` e `requiredAddons` | A CE de Noronha já tem seu próprio contrato e dependência de Items | Nenhuma alteração necessária | Sim, somente se o load order da CE for alterado | Não copiar dependências de outro mundo |
| `Wickedisland/world/config.cpp` (895 linhas) | mundo monolítico; nenhum `#include` | O mundo de tamanho próximo não demonstra modularização por include | Nenhuma | Sim: exemplo real com include + PBO Project/Binarize do autor | Não dividir `world/config.cpp` agora |
| `enoch/world/config.cpp` (1065 linhas) e `chernarusplus/world/config.cpp` (2479 linhas) | mundos grandes também monolíticos; nenhum `#include` | Reforça que tamanho não justifica refactor de runtime | Nenhuma | Sim, antes de qualquer include | Não usar complexidade como motivo para mudar o config |
| `Wickedisland/world/config.cpp`, `enoch/world/config.cpp`, `chernarusplus/world/config.cpp` | `CfgWorlds` e classes de mundo próprios | Confirma a responsabilidade do config de mundo, mas não fornece um template intercambiável | Nenhuma | Sim, para qualquer mudança em herança/cenas/nomes | Não copiar blocos de `CfgWorlds` |
| toda a árvore `P:\DZ\worlds` | nenhum `$pboprefix$` encontrado | Os exemplos não esclarecem como os PBOs instalados derivam prefixo | Apenas manter o prefixo já explícito de `sounds` | Sim: inspeção do PBO Project do autor e de PBO empacotado | Não adicionar prefixes em `ce`, `data`, `navmesh` ou `world` |

Não foi encontrado exemplo real de `#include` em `*.cpp`, `*.hpp` ou `*.h`
dentro de `P:\DZ\worlds`. Portanto:

```text
WORLD_INCLUDE_TEST = UNPROVEN
```

## Teste temporário de estilo de config

O teste usou somente cópias em
`P:\Noronha_Builds\temp\code-organization-audit-20260825\config-style`.
Nenhum config de runtime foi alterado.

O `CfgConvert.exe` do DayZ Tools foi localizado em
`C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\CfgConvert\CfgConvert.exe`.
`CfgConvert -test` e `CfgConvert -bin` passaram para os quatro arquivos:

```powershell
CfgConvert.exe -test <copia-temporaria>\config.cpp
CfgConvert.exe -bin -dst <copia-temporaria>\config.bin <copia-temporaria>\config.cpp
```

Cada chamada retornou código 0 e não emitiu diagnóstico. A comparação abaixo
é a evidência de conversão, não prova de equivalência em runtime:

| Arquivo temporário | `-test` | SHA-256 do `.bin` | Tamanho |
| --- | --- | --- | --- |
| `before/data/config.cpp` | PASS | `AC38E020F55242EF0B89DBC17AB0EAA67466A10DC7727F0108F09F7EE9F8B5F4` | 89 B |
| `after/data/config.cpp` | PASS | `1FEEBEF39A79E59065AFAFA920C804F50DF5BC358BCF4E9E49D4C63DB7799BFC` | 129 B |
| `before/navmesh/config.cpp` | PASS | `3E3E6F922D3FB07CC01584FF2D9CA3933CB9072EA58F3D27240D59F87455747D` | 92 B |
| `after/navmesh/config.cpp` | PASS | `A5CBECAA54FA701B623687210549471EDDACD02BCD2BC57773AAB7978070AEA3` | 132 B |

`after` preservou exatamente os classnames públicos `Noronha_data` e
`Noronha_navmesh`, mas adicionou metadata e normalizou `cfgpatches` para
`CfgPatches`. Como o resultado binarizado mudou, o experimento não prova
equivalência de runtime. A decisão é:

```text
CONFIG_STYLE_TEST = PASS (sintaxe e conversão temporária)
SOURCE_APPLY = REQUIRES_AUTHOR_RUNTIME_TEST
```

Nenhum PBO, PBO Project, Addon Builder, FileBank ou DayZ foi executado.

## Prefixos

| Área | Situação |
| --- | --- |
| `sounds` | explícito: `sounds/$pboprefix$` contém `Noronha\sounds`; a referência do mundo e os OGG coincidem |
| `ce`, `data`, `navmesh`, `world` | `UNKNOWN` neste nível de source: não há `$pboprefix$` versionado |
| exemplos em `P:\DZ\worlds` | não há `$pboprefix$` para usar como prova |
| derivação do PBO Project do autor | `AUTHOR_PBO_PROJECT_TEST_REQUIRED`; não executar nesta auditoria |

Não se deve criar prefixos para os quatro diretórios `UNKNOWN` apenas para
uniformizar a árvore: isso pode mudar os caminhos virtuais do PBO.

## Toolchain localizado, não executado como build

| Ferramenta | Localização | Uso nesta auditoria |
| --- | --- | --- |
| `CfgConvert.exe` 1.2.0.1 | DayZ Tools `Bin\CfgConvert` | usado apenas para validar/converter cópias temporárias de config |
| `AddonBuilder.exe` 1.0.240.639 | DayZ Tools `Bin\AddonBuilder` | localizado; não executado |
| `binarize.exe` 1.29 | DayZ Tools `Bin\Binarize` | localizado; não executado |
| `Rapify.exe` 1.93.9.46 | Mikero DePboTools | localizado; não executado |
| `MakePbo.exe` 2.16.9.36 | Mikero DePboTools | localizado; não executado |
| `pboProject.exe` 4.31.10.04 | Mikero DePboTools | localizado; não executado |
| `DeRapify.exe` | caminhos pesquisados de DayZ Tools/Mikero | não localizado |

O fluxo oficial do autor continua: Terrain Builder exporta o WRP, PBO Project
faz o build manual, e o autor monta/testa/publica. Esta auditoria não substitui
nenhuma dessas etapas.
