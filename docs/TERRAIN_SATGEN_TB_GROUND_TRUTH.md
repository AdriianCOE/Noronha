# TerrainSatGen — Terrain Builder Ground Truth

Fase 2.5 — auditoria e coleta manual pendente
Data: 2026-09-03
Decisão: **NÃO PRONTO** para renderer real, aliases de mask ou Fase 3.

## Escopo e regra de evidência

Este é o contrato de coleta para P:/Noronha_Workspace/terrain/noronha.tv4p.
A inspeção foi somente de leitura: não abriu, salvou, atualizou ou reexportou o
projeto Terrain Builder e não alterou WRP, navmesh, heightmap, mask, satellite
nem outros rasters.

Texto legível do binário TV4P prova somente que uma configuração existe. Sem
parser confiável, não prova valores, unidades, grid, tile, overlap, orientação
ou origem. Todo campo MANUAL_TB_REQUIRED precisa ser copiado na UI do Terrain
Builder, acompanhado de captura de tela.

## Baseline preservado

| Artefato autoritativo | SHA-256 baseline |
| --- | --- |
| world/Noronha.wrp | 110C4BC4BEEA4AD87A1E20D756FBD700A363D9D748D44D58FFE009713FC81AA6 |
| navmesh/navmesh.nm | 87FF7F33FDB9CC958BF3879EE2BEDAB5682590887D951E426269DF9035654803 |
| source/QGIS/gtt_heightmap.asc | 832EC370CD9871688E25E0F1D7BF78E44E10F976D97739147B874FC441AA8A9E |
| P:/Noronha_Workspace/assets-src/terrain/gtt_satmap.bmp | 1D2D37109DB1A6BFC825D1126FAB2F077CC93A5F5EA9E6E8BD0E54DFFCCB8107 |
| P:/Noronha_Workspace/assets-src/terrain/gtt_mask_osm.bmp | DF3516A6C527BC5574DC0D2FF96BEC02AB9CED7BE8112BDB283FD15A09DFDC7B |

O repositório começou em main...origin/main [ahead 2], após os checkpoints
locais 4c9a8ba Add TerrainSatGen inspect MVP e
5ef2022 Add synthetic TerrainSatGen preview core. O Noronha_Workspace já
possuía alterações não relacionadas; elas estão fora deste escopo.

## Quatro RGB sem ground truth

gtt_mask_osm.bmp é RGB, 10240 x 10240. Isso é coerente com mundo de
10240 m x 10240 m e escala derivada de 1 m/pixel, mas não prova origem de
pixel, direção de Y nem registro visual.

| RGB observado | Pixels | Layer vizinho em source/layers.cfg | Delta RGB | Estado |
| --- | ---: | --- | --- | --- |
| (255,175,23) | 88,775,026 | cp_gravel (255,175,22) | 1 no B | LIKELY_BUT_MANUAL_TB_REQUIRED |
| (254,29,191) | 1,522,009 | en_soil (254,28,191) | 1 no G | LIKELY_BUT_MANUAL_TB_REQUIRED |
| (251,227,38) | 284,945 | en_stubble (250,227,38) | 1 no R | LIKELY_BUT_MANUAL_TB_REQUIRED |
| (87,86,86) | 2,558 | cp_concrete2 (86,86,86) | 1 no R | LIKELY_BUT_MANUAL_TB_REQUIRED |

Há 90,584,538 pixels sem igualdade exata. A proximidade de um canal é uma
hipótese forte de quantização/exportação, mas não foi encontrado alias ativo,
log de importação ou exportador que prove equivalência. Não criar aliases, não
normalizar a mask e não aceitar o vizinho como mapeamento confirmado.

## Projeto Terrain Builder e sampler

Evidência segura:

- Projeto: P:/Noronha_Workspace/terrain/noronha.tv4p, 497,444 bytes; última
  gravação observada em 2026-09-02 20:46:58.
- O arquivo persiste paths antigos para P:/Noronha/source/QGIS/gtt_satmap.bmp,
  gtt_mask_osm.bmp e gtt_terrain_normals.bmp; não são os bitmaps de origem
  atuais.
- Há rótulos binários como imageryResolution, satGridCellSize, texcell,
  texoverlap e texture layer, sem parser confiável para associar bytes a
  valores e unidades.

| Campo | Valor offline | Estado |
| --- | --- | --- |
| Resolução de imagery/satellite | — | MANUAL_TB_REQUIRED |
| Satellite grid: dimensão e célula | — | MANUAL_TB_REQUIRED |
| Segmento/tile | — | MANUAL_TB_REQUIRED |
| Overlap horizontal e vertical | — | MANUAL_TB_REQUIRED |
| Texture layer size | — | MANUAL_TB_REQUIRED |
| Origem, Y e pixel-center | — | MANUAL_TB_REQUIRED |
| Raster satellite efetivamente associado | path antigo persistido | MANUAL_TB_REQUIRED |
| Raster mask efetivamente associado | path antigo persistido | MANUAL_TB_REQUIRED |

Não reapontar paths na coleta. Registrar se o Terrain Builder resolve arquivo
por cache, path alternativo ou reporta ausência; capturar a mensagem.

## Registro espacial

| Relação | Evidência atual | Estado | Checagem manual |
| --- | --- | --- | --- |
| Mundo | 10240 m x 10240 m | CONFIRMED_OFFLINE | Confirmar na UI. |
| ASC | 1024 x 1024; xllcorner 200000, yllcorner 0, cellsize 10; X [200000,210240], Y [0,10240] | CONFIRMED_OFFLINE | Confirmar import/grid e origem. |
| Satellite e mask | BMP RGB 10240 x 10240; 1 m/px derivado | dimensão confirmada; registro UNKNOWN | Confirmar escala, origem, Y e associação ativa. |
| ASC contra BMP | dimensões físicas coerentes | LIKELY_BUT_MANUAL_TB_REQUIRED | Sobrepor e validar landmarks. |
| Pixel center, borda e Y | não determinado | UNKNOWN_MANUAL_TB_REQUIRED | Registrar convenção efetiva. |

Usar três landmarks e salvar uma captura por ponto que mostre coincidência de
terreno, satellite e referência de posição:

| Landmark | Posição X,Y | Critério |
| --- | --- | --- |
| Aeroporto | 5845.81, 5907.83 | Instalação/pista coincide com feição do satellite. |
| Porto | 9021.95, 8296.21 | Costa/porto coincide com feição do satellite. |
| Pico (Rocha Nega) | 6594.60, 7163.40 | Pico/relevo coincide entre heightmap e referência visual. |

Aprovar somente quando os três coincidirem sem deslocamento sistemático. Se
houver deslocamento, registrar magnitude, eixo e direção; não compensar por
edição nesta fase.

## en_deforested.rvmat

**Classificação: LEGACY_BUT_PRESENT.**

world/config.cpp inclui
DZ\surfaces_bliss\data\terrain\en_deforested.rvmat em UsedTerrainMaterials; o
arquivo existe em P:/DZ/surfaces_bliss/data/terrain/en_deforested.rvmat; porém
não há entrada correspondente em source/layers.cfg, nem prova offline de cor da
mask, layer do Terrain Builder ou tile atual que o use. Auditorias anteriores o
descrevem como declaração legada a revisar no Terrain Builder.

1. Localizar en_deforested.rvmat na lista funcional de materiais/surfaces usados
   pelo projeto e capturar a lista completa.
2. Verificar se uma layer ou associação de mask o seleciona; registrar nome, RGB
   e área/tile, se a UI disponibilizar.
3. Se não houver associação, registrar a ausência. Não removê-lo de
   UsedTerrainMaterials e não adicioná-lo a layers.cfg nesta fase.

## Checklist humano no Terrain Builder

Nomes de painéis variam por versão; as ações são funcionais, não alegações sobre
rótulos de UI.

1. Abrir manualmente noronha.tv4p. Se houver prompt de migração, atualização ou
   salvamento, cancelar e não gravar o projeto.
2. Abrir propriedades de terreno/projeto e capturar tamanho, grade, célula e
   parâmetros de importação do heightmap.
3. Localizar imagery/satellite e copiar com captura: raster associado,
   resolução, satellite grid, segmento/tile, overlap e texture layer size.
   Anotar unidade e versão do Terrain Builder.
4. Localizar mask/surfaces e capturar associações de cores e materiais. Registrar
   a surface efetiva de (255,175,23), (254,29,191), (251,227,38) e (87,86,86).
5. Capturar materiais usados e executar o checklist de en_deforested.
6. Validar e capturar os três landmarks. Anotar deslocamento, inversão ou
   espelhamento observado.
7. Registrar tile e overlap reais no bloco abaixo; somente então executar o
   gate de quatro surfaces.

### Bloco de coleta

~~~text
Terrain Builder version:
Imagery/satellite source actually resolved:
Mask source actually resolved:
Imagery resolution:
Satellite grid dimensions / cell size:
Segment/tile size:
Overlap X / Y:
Texture layer size:
Origin / Y direction / pixel-center convention:
RGB (255,175,23) ->
RGB (254,29,191) ->
RGB (251,227,38) ->
RGB (87,86,86) ->
en_deforested active association ->
Landmark result (Aeroporto / Porto / Pico):
Capture paths or identifiers:
~~~

## Gate: quatro surface types por tile

Este é plano, não implementação. Executar somente após parâmetros reais e todos
os mapeamentos de cor estarem confirmados.

1. Converter cada pixel da mask para a surface confirmada pelo Terrain Builder;
   cor sem confirmação é UNKNOWN e bloqueia o resultado.
2. Derivar janela nuclear de cada tile do grid/tile size real e expandi-la pelo
   overlap real, usando origem e convenção de bordas confirmadas pela UI.
3. Para cada janela expandida, contar o conjunto de surface types distintos. O
   overlap integra a janela e não pode ser ignorado.
4. Emitir por tile: índice, caixa em coordenadas de mask/mundo, surfaces,
   contagem e pixels UNKNOWN.
5. Falhar se algum tile tiver mais de quatro types, algum pixel UNKNOWN ou
   faltar parâmetro real do sampler.

O relatório incluirá tiles de borda, cantos, os tiles dos três landmarks e o
máximo global. Nenhuma correção da mask é parte deste gate.

## Readiness gate

| Critério para renderer real/Fase 3 | Situação |
| --- | --- |
| Quatro RGB comprovados no Terrain Builder | Pendente |
| Sampler real: grid, tile, overlap, layer | Pendente |
| Paths de raster efetivamente resolvidos comprovados | Pendente |
| Registro espacial aprovado por três landmarks | Pendente |
| en_deforested classificado por associação real | Pendente |
| Gate de quatro surfaces executável com parâmetros reais | Pendente |

**Resultado: NÃO PRONTO.** A próxima atividade permitida é a coleta humana
acima, sem salvar o TV4P nem modificar asset autoritativo. Depois da coleta,
reavaliar a Fase 2.5 antes de renderer real ou Fase 3.
