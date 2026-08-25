# Terrain

`source/layers.cfg` e `source/QGIS/gtt_heightmap.asc` são entradas versionadas do terreno. As fontes GIS, imagens editáveis, shapefiles e o projeto Terrain Builder permanecem em NoronhaFiles.

## Estado da fonte de altura

Em 25/08/2026, o autor confirmou que a variante SHA-256 `72EC09E7934940EE8C69EF1B1C1620E533F655FE80385711D48FB090E7032322` contém as alterações recentes reais do terreno. Ela é a `TERRAIN_SOURCE_CURRENT` e `DEV_AUTHORITATIVE` a partir do commit que a promove para este caminho versionado.

O arquivo anterior SHA-256 `D40404363DB9B7B494CEE2F57F43BCDC5BCD4FAB72C097368CB5B425FD4BC68B` é preservado fora do checkout operacional como `TERRAIN_SOURCE_HISTORICAL`; não deve ser apagado nem usado como substituto silencioso. Ambos possuem a mesma malha ASCII (`1024 x 1024`, origem `200000, 0`, célula de `10 m`, `NODATA=-9999`).

O timestamp de filesystem observado na cópia promovida foi `2026-08-25T11:03:21-03:00`, embora o autor tenha atribuído a edição recente a aproximadamente 11:23. A classificação de autoridade segue a confirmação do autor, não uma inferência baseada somente no timestamp de cópia.

`data/layers/*.paa`, `*.png` e `*.rvmat` são outputs runtime aprovados. Os RVMAT referenciam os PNG das layers diretamente, então todos os três tipos pertencem ao mapa oficial.

O WRP é necessário para uma build jogável, mas a cópia correta não foi encontrada no inventário. Não gere ou adicione um WRP substituto sem confirmar que corresponde ao estado do projeto Terrain Builder.
