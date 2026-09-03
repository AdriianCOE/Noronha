# TerrainSatGen — Terrain Builder Ground Truth

Fase 2.6 — Terrain Builder compatibility e surface tile audit
Data: 2026-09-03
Readiness: **READY_FOR_REAL_PREVIEW = YES** (`SPATIAL_REGISTRATION = CONFIRMED`)

`READY_FOR_TB_REGEN / PROMOTION = NO` permanece um gate separado: ele exige
regularização consciente dos paths persistidos e resolução manual dos segmentos
com mais de quatro surfaces. Esses itens não bloqueiam o renderer real
estritamente read-only.

## Contrato e baseline

Esta fase leu os inputs e executou apenas o inspector read-only. Não abriu,
salvou, atualizou ou reexportou o TV4P; não alterou WRP, navmesh, heightmap,
satellite, mask, layers.cfg, Terrain Builder ou Noronha_Workspace.

| Artefato autoritativo | SHA-256 baseline |
| --- | --- |
| world/Noronha.wrp | 110C4BC4BEEA4AD87A1E20D756FBD700A363D9D748D44D58FFE009713FC81AA6 |
| navmesh/navmesh.nm | 87FF7F33FDB9CC958BF3879EE2BEDAB5682590887D951E426269DF9035654803 |
| source/QGIS/gtt_heightmap.asc | 832EC370CD9871688E25E0F1D7BF78E44E10F976D97739147B874FC441AA8A9E |
| P:/Noronha_Workspace/assets-src/terrain/gtt_satmap.bmp | 1D2D37109DB1A6BFC825D1126FAB2F077CC93A5F5EA9E6E8BD0E54DFFCCB8107 |
| P:/Noronha_Workspace/assets-src/terrain/gtt_mask_osm.bmp | DF3516A6C527BC5574DC0D2FF96BEC02AB9CED7BE8112BDB283FD15A09DFDC7B |

## Evidência manual do Terrain Builder

Os valores abaixo foram copiados manualmente da UI real do projeto Noronha.

| Domínio | Valor confirmado |
| --- | --- |
| Mapframe | UTM 31N; left-bottom Easting 200000.000, Northing 0.000; output root P:/Noronha |
| Terrain | grid 1024 x 1024; cell 10.000 m; tamanho 10240.000 m |
| Satellite/surface source | 10240 x 10240 px; 1.000000 m/px |
| Satellite tile texture | 512 x 512 px |
| Overlap | desired 16 px por lado; actual shared overlap 32 px; overlapped area 12.109% |
| Segmento útil | stride 480 px; final sat grid 48 terrain cells; satellite segment 12 |
| Grid | 22 tiles por linha; landgrid 256 m; wanted sat grid 49.600 cells |
| Texture layer | 40.00 x 40.00 m |
| Processing | export satellite texture, normal map e surface mask habilitados; modo 4 materials per cell |
| layers.cfg ativo | P:/Noronha/source/layers.cfg |

O left-bottom coincide com o ASC: xllcorner 200000 e yllcorner 0. UTM 31N é
parte do contrato atual do projeto e não deve ser corrigido nesta fase.

Os campos UV observados abaixo são evidência, não semântica inferida:

~~~text
gridInWSize=0.046875       wSegmentExtent=480.000000
wSegment=480               wSegTex=512
satTexU=0.937500           satGrid=480.000000
satUA=0.001953             xOffset=16
satOffU=0.031250           xBeg=0.000000
satUB=0.031250             rangeZ=10240.000000
zBeg=10240.000000          satVB=20.031250
~~~

## Paths persistidos e reimportação

Layers Manager apresenta o ASC em P:/Noronha/source/QGIS/gtt_heightmap.asc e
os BMP antigos em P:/Noronha/source/QGIS/gtt_mask_osm.bmp,
gtt_terrain_normals.bmp e gtt_satmap.bmp. Os BMP autoritativos atuais vivem em
P:/Noronha_Workspace/assets-src/terrain.

O projeto exibe raster persistido/cacheado apesar dos paths legados.
RUNTIME/REIMPORT REPRODUCIBILITY = MANUAL_TB_REVIEW. Não reapontar esses paths
nem salvar o projeto nesta fase.

## Registro espacial

As capturas de 2026-09-03 fornecem evidência manual para Aeroporto:

- o marcador cai na região esperada;
- mata, vias, clareiras e construções vizinhas são coerentes no satellite;
- o footprint de aeroporto aparece na mask;
- a pista foi removida deliberadamente do satellite para não competir com
  terrain/mask/objetos e não é mismatch.

Aeroporto = SPATIAL_ALIGNMENT_STRONGLY_CONFIRMED.

Porto é o segundo landmark independente confirmado pelas capturas de
2026-09-03: píer curvo, curva da costa, estrada diagonal de chegada, massa
rochosa e marcador coincidem no satellite; a mask apresenta a mesma costa,
orientação e eixo principal. Portanto:

~~~text
AEROPORTO = CONFIRMED
PORTO = CONFIRMED
SECOND_LANDMARK_REQUIRED = NO
SPATIAL_REGISTRATION = CONFIRMED
~~~

Isso é evidência suficiente para preview regional estritamente read-only. Não
infere pixel-center subpixel, nem autoriza qualquer ação no Terrain Builder.
O preview recebe `y` em coordenada de mundo lower-left e o converte para a
origem top-down do raster; essa conversão é parte do registro confirmado.

## Cores da mask e compatibilidade TB

A mask possui seis RGB usados. Em STRICT_RGB, quatro não são igualdade byte a
byte com a Legend. Em TB_COMPAT, somente aliases declarados no preset são
ativados; não há nearest-color automático e nenhum pixel é reescrito.

| RGB mask | Surface Legend | Estado TB_COMPAT | Evidência |
| --- | --- | --- | --- |
| (255,175,23) | cp_gravel (255,175,22) | explicit_alias | delta de um canal, candidato único |
| (254,29,191) | en_soil (254,28,191) | explicit_alias | delta de um canal, candidato único |
| (251,227,38) | en_stubble (250,227,38) | explicit_alias | delta de um canal, candidato único |
| (87,86,86) | cp_concrete2 (86,86,86) | explicit_alias | MANUAL_SEMANTIC_CONFIRMATION = YES no aeroporto |

A confirmação visual do concrete veio da captura de mask no aeroporto: a área
cinza escura representa o material concreto usado ali. Isso confirma a intenção
semântica do alias, não uma necessidade de corrigir a mask.

Comportamento do inspector:

| Modo | Resolução |
| --- | --- |
| STRICT_RGB, default | exact ou unknown; mantém os quatro unknown e falha pela política atual |
| TB_COMPAT, opt-in | exact, explicit_alias ou unknown; aceita somente aliases do preset |
| nearest | diagnóstico para unknown; nunca vira alias automático |

Aliases que apontam para surface inexistente, sombreiam RGB exato da Legend ou
são duplicados/conflitantes são rejeitados. Contagem de materiais usa nomes de
surface resolvidos, não RGB bruto.

## TB_SEGMENT_WINDOW_MODEL

O audit usa os samplers reais acima, com limites de pixel half-open:

1. core start = n x 480;
2. core end = min(start + 480, 10240);
3. window = core expandido por 16 px em cada lado;
4. window é recortada em 0..10240 somente na borda exterior.

Portanto, 10240 / 480 resulta em 22 segmentos por eixo e 484 segmentos totais.
O último core é parcial. Um tile interior mede 512 px por 512 px; bordas
externas são menores por clipping. A área compartilhada de 32 px participa da
contagem.

## Resultado da auditoria real

Comando executado:

~~~text
python -m terrainsat inspect --preset presets/noronha.toml --tb-compat --surface-segment-audit
~~~

| Modo | Segmentos | PASS | FAIL | UNKNOWN | Máximo |
| --- | ---: | ---: | ---: | ---: | ---: |
| STRICT_RGB | 484 | 0 | 0 | 484 | 2 materiais resolvidos |
| TB_COMPAT | 484 | 481 | 3 | 0 | 5 materiais |

Tempo da auditoria TB_COMPAT: aproximadamente 4.02 s. A leitura é tiled por
janela e não cria uma cópia integral adicional da mask de 10240 x 10240.

Os três failures TB_COMPAT são reais sob o modelo confirmado:

| Tile X,Y | Core bounds | Window bounds | Surfaces com overlap |
| --- | --- | --- | --- |
| 11,7 | [5280,3360,5760,3840) | [5264,3344,5776,3856) | cp_gravel, en_forest_con, en_grass2, en_soil, en_stubble |
| 9,8 | [4320,3840,4800,4320) | [4304,3824,4816,4336) | cp_gravel, en_forest_con, en_grass2, en_soil, en_stubble |
| 12,11 | [5760,5280,6240,5760) | [5744,5264,6256,5776) | cp_gravel, en_forest_con, en_grass2, en_soil, en_stubble |

Nos tiles 11,7 e 9,8 as cinco surfaces já existem no core. No tile 12,11,
en_stubble aparece por causa da janela com overlap: são 137 px (0,05226% da
janela), fora do core. Ele é um `MANUAL_SIMPLIFICATION_CANDIDATE`, não uma
autorização para editar a mask. Nos tiles 11,7 e 9,8, `cp_gravel` existe no
core em área relevante e pode ser estrada, pátio ou geometria intencional; não
removê-lo automaticamente. Os três locais exigem decisão de autoria/revisão
manual posterior.

## en_deforested

en_deforested.rvmat = LEGACY_BUT_PRESENT e é não bloqueante para este preview.
Ele existe em UsedTerrainMaterials e como RVMAT, mas não em source/layers.cfg e
não há associação de mask comprovada. Não adicionar layer, inventar surface ou
alterar a configuração nesta fase.

## Readiness

| Gate | Estado |
| --- | --- |
| Geometria terrain/satellite/mask e origem ASC | Resolvido |
| Sampler TB, tile, overlap, texture layer e 4-material mode | Resolvido |
| Paths legados/cache | `PRE_TB_PROMOTION_GATE`; regularizar conscientemente antes de reimportar/salvar no TB; não bloqueia preview read-only |
| Aliases TB explícitos | Resolvido para TB_COMPAT; STRICT permanece disponível |
| Airport alignment | CONFIRMED |
| Porto alignment | CONFIRMED |
| Registro espacial para preview read-only | SPATIAL_REGISTRATION = CONFIRMED |
| 4 materiais por segmento | `PRE_TB_PROMOTION_GATE`: 3 segmentos TB_COMPAT com 5 materiais; não bloqueia preview read-only |
| en_deforested | LEGACY_BUT_PRESENT, não bloqueante |

READY_FOR_REAL_PREVIEW = **YES**. O renderer real pode ler regionalmente os
inputs atuais e escrever somente em `tools/terrain_satgen/out/`; ele não pode
modificar os inputs, gerar o satmap completo ou interagir com Terrain Builder.

READY_FOR_TB_REGEN / PROMOTION permanece **NO** pelos três segmentos acima do
limite de quatro materiais e pelos paths persistidos/cacheados. Não gerar
satellite, não alterar mask e não operar/salvar o Terrain Builder até revisão
explícita desses gates de promoção.

## Fase 3.1 — contexto visual read-only

A calibração do preview não altera este ground truth nem amplia permissão no
Terrain Builder. O renderer usa o Mapframe confirmado (`x=200000`, `y=0`) e a
convenção ASC padrão de linhas north-to-south para amostrar altura em world
coordinates: a coluna é `floor((200000 + world_x - xllcorner) / 10)` e a linha
é `1023 - floor((world_y - yllcorner) / 10)`.

O ASC medido possui mar dominante em aproximadamente `-10 m` e uma faixa de
valores perto de zero. Para o preview, somente, o preset declara:

~~~text
WATER             height <= -2 m
COAST_TRANSITION  -2 m < height < 2 m
LAND              height >= 2 m
~~~

Isso não reclassifica a mask. Ele resolve o finding visual em que `cp_gravel`
também ocorre no oceano: pixels `WATER` preservam fortemente o satellite e a
modulação terrestre é limitada; `cp_gravel + LAND` conserva sua receita
terrestre relativa. As transições entre surfaces recebem feather local limitado
por recipe e por halo; a mask de entrada permanece byte-exata.

`READY_FOR_TB_REGEN / PROMOTION = NO` continua inalterado.

## Fase 3.2 — calibração meso read-only

A Fase 3.2 não altera os dados acima nem amplia os gates de Terrain Builder.
Ela separa localmente o crop do satellite em macro, meso e micro por dois
low-passes com halo e preserva o componente meso do satellite original com mais
força no preview `balanced`. Os diagnósticos macro/meso/micro e as métricas de
Chernarus/Livonia são somente artefatos em `tools/terrain_satgen/out/`; as
referências locais e eventuais ROIs não entram no Git e não fornecem pixels,
paleta ou geometria para Noronha.

Assim, qualquer resultado desta fase continua `READ_ONLY_REGIONAL_PREVIEW` e
`RUNTIME_VISUAL_REVIEW`; não constitui promoção para Terrain Builder, alteração
de mask/satellite, ou autorização para Generate Layers.
