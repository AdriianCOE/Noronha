# Terrain

`source/layers.cfg` e `source/QGIS/gtt_heightmap.asc` são entradas versionadas do terreno. As fontes GIS, imagens editáveis, shapefiles e o projeto Terrain Builder permanecem em NoronhaFiles.

## Estado da fonte de altura

O commit autoral `a381902 map`, de 27/08/2026, atualizou o par de fontes do terreno. A variante SHA-256 `E2777418203F76EBC9CD12C7CF95D67F46C8C2758C86AFF329F05C44CF14C766` em `source/QGIS/gtt_heightmap.asc` é a `TERRAIN_SOURCE_CURRENT` e `DEV_AUTHORITATIVE` para a baseline vigente.

O arquivo anterior SHA-256 `D40404363DB9B7B494CEE2F57F43BCDC5BCD4FAB72C097368CB5B425FD4BC68B` é preservado fora do checkout operacional como `TERRAIN_SOURCE_HISTORICAL`; não deve ser apagado nem usado como substituto silencioso. Ambos possuem a mesma malha ASCII (`1024 x 1024`, origem `200000, 0`, célula de `10 m`, `NODATA=-9999`).

O timestamp de filesystem observado na cópia promovida foi `2026-08-25T11:03:21-03:00`, embora o autor tenha atribuído a edição recente a aproximadamente 11:23. A classificação de autoridade segue a confirmação do autor, não uma inferência baseada somente no timestamp de cópia.

`data/layers/*.paa`, `*.png` e `*.rvmat` são outputs runtime aprovados. Os RVMAT referenciam os PNG das layers diretamente, então todos os três tipos pertencem ao mapa oficial.

## WRP DEV atual

O mesmo commit `a381902 map` atualizou `world/Noronha.wrp` para SHA-256
`B75F5E940A7872F538EF672F6137683BCB09C57F02671EAD013C7B824D142C1B` e criou
`world/Noronha.hpp`. Esses artefatos, junto do heightmap atual, formam a
baseline `DEV_AUTHORITATIVE_RUNTIME` rastreada por Git LFS.

As referências de 25/08/2026 permanecem históricas; não devem ser restauradas
ou substituídas silenciosamente. A execução no DayZ continua sendo uma
validação runtime separada desta verificação de integridade.
