# TerrainSatGen - auditoria e proposta inicial

Data da auditoria: 2026-09-03

Escopo desta etapa: auditoria read-only dos assets de terreno e proposta de
engenharia. Nenhum renderer foi implementado e nenhum asset autoritativo foi
regenerado, promovido ou substituido.

## A. CURRENT STATE

Noronha tem um mundo quadrado de `10240 x 10240 m`, comprovado por
`world/config.cpp` (`mapSize=10240`) e por
`Noronha_Workspace/ce-editor/Noronha.xml` (`world size="10240"`).

As fontes estao separadas por autoridade:

- `P:\Noronha` contem o checkout operacional e os inputs versionados
  `source/layers.cfg` e `source/QGIS/gtt_heightmap.asc`;
- `P:\Noronha_Workspace/terrain` contem o projeto Terrain Builder autoritativo;
- `P:\Noronha_Workspace/assets-src/terrain` contem os rasters editaveis
  autoritativos de satellite, mask e normals;
- `P:\Noronha/data/layers` contem outputs runtime gerados: 1452 PAA, 1452 PNG e
  1059 RVMAT no momento desta auditoria.

O projeto Terrain Builder `terrain/noronha.tv4p` existe e tem 497444 bytes. Sua
varredura read-only encontrou referencias persistidas aos caminhos antigos:

- `P:\Noronha\source\QGIS\gtt_heightmap.asc` (existe);
- `P:\Noronha\source\QGIS\gtt_satmap.bmp` (nao existe);
- `P:\Noronha\source\QGIS\gtt_mask_osm.bmp` (nao existe);
- `P:\Noronha\source\QGIS\gtt_terrain_normals.bmp` (nao existe).

As tres imagens existem hoje em
`P:\Noronha_Workspace\assets-src\terrain`. O TV4P tambem contem tres referencias
legadas `meusassets\e_estradas_parts`; elas pertencem ao problema ja conhecido
das bibliotecas de roads e nao devem ser corrigidas como efeito colateral deste
projeto.

O checkout `P:\Noronha` estava limpo em `main` no inicio da auditoria. O
workspace privado ja estava sujo, com `terrain/Dialogs_new.vdat` modificado e
backups `terrain/*.v4d.bakN` removidos. Essas mudancas preexistentes foram
preservadas.

## B. VERIFIED INPUTS

### Geometria e imagens

| Input | Evidencia | Resultado |
| --- | --- | --- |
| Mundo | `world/config.cpp`, CE XML | `10240 x 10240 m` |
| Satellite fonte | `assets-src/terrain/gtt_satmap.bmp` | BMP RGB, sem compressao, `10240 x 10240`, 314572854 bytes |
| Surface mask fonte | `assets-src/terrain/gtt_mask_osm.bmp` | BMP RGB, sem compressao, `10240 x 10240`, 314572854 bytes |
| Normals fonte | `assets-src/terrain/gtt_terrain_normals.bmp` | BMP RGB, sem compressao, `1024 x 1024` |
| Heightmap | `source/QGIS/gtt_heightmap.asc` | ESRI ASCII, `1024 x 1024`, celula `10 m`, sem NODATA usado |
| Legend | `source/LayerColours.png` | PNG RGBA, `378 x 850` |
| Legend completa | `source/LayerLegendComplete_v2.png` | PNG RGB, `6500 x 6209` |

O satellite e a mask cobrem a mesma grade de pixels. Com um mundo de 10240 m,
isso implica `1.0 m/px`. O heightmap cobre 10240 m por eixo e declara:

```text
xllcorner = 200000
yllcorner = 0
cellsize  = 10
extent X  = [200000, 210240]
extent Y  = [0, 10240]
```

As dimensoes sao coerentes. A orientacao, o pixel origin e o registro exato
entre ASC/BMP nao foram provados somente por esses metadados; isso requer uma
sobreposicao com landmarks conhecidos no QGIS/Terrain Builder.

Estatisticas do heightmap atual:

- 1024 linhas, todas com 1024 valores;
- minimo `-27.61 m`, maximo `242.99 m`, media `2.4633 m`;
- nenhum valor `-9999`.

O SHA-256 atual do heightmap e
`832EC370CD9871688E25E0F1D7BF78E44E10F976D97739147B874FC441AA8A9E`.
Ele foi commitado em `644ff1a` em 2026-09-02. O hash anterior ainda escrito em
`docs/TERRAIN.md` e no default de `validate-noronha.ps1` esta desatualizado; nao
se trata de uma alteracao local desta auditoria.

Estatisticas RGB do satellite, medidas em tiles:

- media: `(25.3391, 36.0032, 39.5677)`;
- desvio padrao: `(18.9793, 17.1377, 13.1001)`;
- minimo: `(0, 5, 6)`; maximo: `(253, 253, 252)`;
- nenhum canal possui pixels em 255; clipping em zero aparece apenas no canal R
  (`0.000221%`).

### Layers e Legend

`source/layers.cfg` declara 26 surfaces e 26 cores, sem nomes, materiais ou
cores duplicados:

```text
cp_grass                   cp_dirt
cp_rock                    cp_concrete1
cp_concrete2               cp_broadleaf_dense1
cp_broadleaf_dense2        cp_broadleaf_sparse1
cp_broadleaf_sparse2       cp_conifer_common1
cp_conifer_common2         cp_conifer_moss1
cp_conifer_moss2           cp_grass_tall
cp_gravel                  en_flowers1
en_flowers2                en_flowers3
en_forest_con              en_forest_dec
en_grass1                  en_grass2
en_soil                    en_stones
en_stubble                 en_tarmac_old
```

Todos os 52 paths de textura/material referenciados pelo arquivo existem em
`P:\DZ\surfaces` (Chernarus) ou `P:\DZ\surfaces_bliss` (Livonia).

A mask usa apenas seis cores. Duas casam exatamente com o Legend e quatro tem
um canal deslocado em uma unidade:

| Cor observada | Pixels | Area | Cor/nome mais proximo no Legend | Estado |
| --- | ---: | ---: | --- | --- |
| `(255,175,23)` | 88775026 | 84.662462% | `cp_gravel (255,175,22)` | mismatch |
| `(193,116,167)` | 9083698 | 8.662889% | `en_grass2` | exata |
| `(28,255,207)` | 5189364 | 4.948963% | `en_forest_con` | exata |
| `(254,29,191)` | 1522009 | 1.451501% | `en_soil (254,28,191)` | mismatch |
| `(251,227,38)` | 284945 | 0.271745% | `en_stubble (250,227,38)` | mismatch |
| `(87,86,86)` | 2558 | 0.002439% | `cp_concrete2 (86,86,86)` | mismatch |

Portanto, `unknown mask colors = 4` e `unknown pixels = 90584538` sob igualdade
RGB exata. O futuro `inspect` deve reportar isso como falha, mostrar o candidato
mais proximo, mas nunca remapear ou regravar a mask silenciosamente. Um alias
explicito no preset so pode ser adicionado depois de confirmar no Terrain Builder
que essas quatro cores representam de fato as surfaces indicadas.

O auditor existente tambem encontrou
`DZ\surfaces_bliss\data\terrain\en_deforested.rvmat` em `UsedTerrainMaterials`,
mas nao em `layers.cfg`. Esse achado e independente da mask e permanece
`MANUAL_TB_REVIEW`.

### Referencias vanilla

As arvores locais `P:\DZ` e `P:\scripts` existem. As 15 surfaces `cp_*` usadas
por Noronha resolvem em `P:\DZ\surfaces`; as 11 `en_*` resolvem em
`P:\DZ\surfaces_bliss`. Isso permite estudar Chernarus e Livonia sem copiar
assets para o repositorio.

Os assets sao PAA/RVMAT. Pillow nao decodifica PAA, e nenhum decoder PAA ->
imagem foi comprovado nesta auditoria. O DayZ Tools local possui
`ImageToPAA.exe`, que converte na direcao oposta. `analyze-style` deve ficar
bloqueado ate existir uma conversao read-only comprovada para um diretorio
temporario ou um decoder licenciado e verificavel.

Nao foram encontrados projetos `.qgs`/`.qgz` nos dois repositorios. Existem o
ASC versionado, shapefiles no workspace e o projeto Terrain Builder; a ausencia
do projeto QGIS deve ser confirmada pelo autor antes de planejar uma integracao
QGIS.

## C. RISKS / UNKNOWNS

1. **Cores da mask:** quatro cores cobrem 86.388147% da imagem e nao casam
   exatamente com `layers.cfg`. Nenhum renderer material-aware deve prosseguir
   com remapeamento implicito.
2. **Paths antigos no TV4P:** satellite, mask e normals apontam para paths que
   nao existem mais. O projeto pode reter dados importados em cache, mas isso
   nao prova que uma reimportacao seja reproduzivel.
3. **Registro espacial:** tamanho e escala passam; orientacao, pixel center,
   origem e alinhamento de landmarks ainda nao foram verificados visualmente.
4. **Baseline documental:** `docs/TERRAIN.md` e o parametro default do validator
   ainda citam um heightmap anterior.
5. **Surface nao declarada:** `en_deforested.rvmat` aparece no mundo sem entrada
   correspondente no `layers.cfg` atual.
6. **Limite por tile do engine:** a documentacao oficial da Bohemia descreve
   limite de quatro surface types por quadrado da mask, incluindo overlap. O
   MVP deve medir isso quando os parametros reais de satellite grid/overlap
   forem confirmados no Terrain Builder.
7. **PNG 10K/20K:** Pillow consegue ler crops, mas nao oferece um writer PNG
   aleatorio realmente streaming. O formato de trabalho do MVP deve continuar
   BMP, compativel com os inputs atuais, ou usar um writer separado so depois de
   benchmark.
8. **PAA style analysis:** nao ha decoder read-only comprovado no ambiente.
9. **Validacao visual:** estatisticas nao provam qualidade, continuidade visual
   ou resultado dentro do DayZ.

Referencias oficiais consultadas:

- [Making Satellite Texture and Mask](https://community.bohemia.net/wiki/Making_Satellite_Texture_and_Mask)
- [Common Terrain Creation Problems](https://community.bohemia.net/wiki/Arma_3%3A_Common_Terrain_Creation_Problems)
- [Terrain Processor sample project](https://community.bohemia.net/wiki/Terrain_Processor%3A_Tutorial_Sample_project)

Essas paginas sao referencias de toolchain Bohemia/Arma; qualquer diferenca
observada no DayZ Tools atual ou no projeto Noronha tem precedencia.

## D. TERRAIN SATELLITE PIPELINE

Fluxo proposto, sempre com promocao manual:

```text
inputs read-only
  layers.cfg + mask + satellite + optional heightmap
        |
        v
inspect / validate / manifest with input hashes
        |
        v
regional preview in world coordinates
        |
        v
tiled full render to out/temporary
        |
        v
compare + diagnostics + atomic finalize in out/
        |
        v
MANUAL_TB_REVIEW
        |
        v
manual import/promotion by the author
        |
        v
RUNTIME_VISUAL_REVIEW in DayZ
```

Invariantes:

- inputs sao abertos read-only;
- o destino resolvido deve estar dentro do `out/` da ferramenta;
- o destino nao pode resolver para o mesmo arquivo de nenhum input;
- arquivos finais sao publicados atomicamente apenas depois de concluir o tile
  final e os diagnosticos;
- nenhum comando chama Terrain Builder, RaG, Binarize ou altera o checkout por
  conta propria;
- cada output registra seed, preset, coordenadas, resolucao e hashes dos inputs.

## E. PROPOSED TOOL ARCHITECTURE

Arquitetura logica futura, nao scaffold a ser criado agora:

```text
CLI
  inspect | preview | generate | compare | analyze-style
        |
        +-- input readers: layers.cfg, ASC, raster windows
        +-- spatial model: bounds, orientation, m/px, world <-> pixel
        +-- material model: exact RGB -> surface, explicit aliases
        +-- procedural fields: deterministic multiscale world-space signals
        +-- modifiers: grade, slope, curvature, neighbors, coast
        +-- tiled compositor: tile + halo -> atomic writer
        +-- diagnostics: hashes, dimensions, per-surface stats, clipping, seams
```

O MVP nao deve criar modulos vazios para renderer, noise, distance ou styles.
Eles entram somente na fase que os usa.

Dependencias propostas para o primeiro codigo:

- Python `>=3.11`;
- NumPy para varredura vetorizada e janelas;
- Pillow para metadata/crops BMP/PNG;
- `tomllib` da biblioteca padrao para preset TOML;
- `argparse`, `hashlib`, `pathlib`, `json` e `unittest` da biblioteca padrao.

Nao adicionar no MVP: PyYAML, OpenCV, Rasterio, SciPy obrigatorio, pyvips ou uma
biblioteca de noise. NumPy e Pillow ja fazem parte de
`source/scripts/requirements.txt`; o pacote `noise` esta listado ali, mas nao
esta instalado no ambiente atual e nao deve virar acoplamento automatico.

SciPy pode ser avaliado na fase de distance fields. `pyvips` ou outro writer
streaming so deve ser considerado se BMP deixar de atender ou um benchmark 20K
mostrar necessidade real.

## F. DATA MODEL / PRESET FORMAT

Usar TOML inicialmente evita uma dependencia YAML e continua legivel no
Windows. Exemplo de contrato, sem afirmar valores finais de arte:

```toml
[world]
size_m = 10240
seed = 1987
origin = "southwest"

[inputs]
layers = "P:/Noronha/source/layers.cfg"
height = "P:/Noronha/source/QGIS/gtt_heightmap.asc"
satellite = "P:/Noronha_Workspace/assets-src/terrain/gtt_satmap.bmp"
mask = "P:/Noronha_Workspace/assets-src/terrain/gtt_mask_osm.bmp"

[output]
directory = "out"
tile_px = 1024

[mask]
unknown_color_policy = "error"

# Somente apos MANUAL_TB_REVIEW:
# [mask.color_aliases]
# "255,175,23" = "cp_gravel"

[surfaces.cp_grass]
source = "original_satellite"
strength = 0.45

[[surfaces.cp_grass.variation]]
name = "macro"
scale_m = 350.0
strength = 0.08
```

Regras de validacao:

- `world.size_m`, dimensoes e `meters_per_pixel` devem fechar exatamente;
- todas as scales usam metros, nunca pixels;
- surface configurada deve existir no `layers.cfg`;
- alias RGB precisa ser explicito, unico e apontar para surface existente;
- paths de input existem e sao arquivos;
- output resolvido fica dentro de `out/` e nunca coincide com input;
- campos desconhecidos no preset geram erro para evitar typo silencioso.

## G. RENDERING / TILING STRATEGY

Custos brutos:

| Resolucao | RGB uint8 | Um campo float32 | Dez campos float32 | RGB float32 |
| --- | ---: | ---: | ---: | ---: |
| 10240² | 300 MiB | 400 MiB | 3.91 GiB | 1.17 GiB |
| 20480² | 1.17 GiB | 1.56 GiB | 15.63 GiB | 4.69 GiB |

E proibido manter satellite, mask e varios campos float32 completos ao mesmo
tempo. Estrategia:

1. ler metadata e validar tudo antes do primeiro output;
2. iterar tiles de `1024 x 1024`;
3. calcular coordenadas absolutas pelo centro do pixel em metros;
4. ler somente satellite/mask/height necessario ao tile;
5. expandir com halo igual ao maior suporte espacial usado naquele passe;
6. compor em float32 e converter/clamp uma unica vez;
7. escrever apenas o miolo, descartando halo;
8. finalizar o arquivo temporario e fazer rename atomico dentro de `out/`.

Para zero seams, o procedural nao pode depender do indice local do tile. Cada
amostra usa coordenada mundial absoluta. Seeds de camadas devem ser derivadas
com hash estavel, por exemplo BLAKE2 sobre `seed + surface + band`; nunca usar
`hash()` do Python. A grade procedural e interpolacao precisam ser identicas em
preview e generate.

Noise multiescala deve combinar bandas configuraveis em metros (macro, medium e
local), com curvas e strengths independentes por surface. Nao usar um unico
Perlin global multiplicado pela imagem.

Slope precisa de halo minimo de uma celula do heightmap. Filtros com kernel
precisam do raio do kernel. Distance fields globais nao devem ser fingidos com
um halo pequeno: na fase 2, ou o efeito declara um `max_distance_m` e usa halo
correspondente, ou adota um algoritmo multipasse/out-of-core comprovado.

BMP 24-bit sem compressao permite leitura e escrita por offset/memmap com baixo
overhead. O primeiro generate completo deve usar BMP em `out/`. Conversao para
outro formato e uma etapa separada, tambem dentro de `out/`.

## H. MVP

O primeiro MVP implementavel deve conter somente `terrainsat inspect`:

- parser read-only de `layers.cfg`;
- parser streaming do header e linhas ASC;
- leitura de metadata de satellite/mask;
- contagem tiled de cores da mask;
- verificacao de dimensoes, world size e escala inferida;
- validacao exata Legend -> mask, com nearest-color apenas diagnostico;
- existencia dos paths PAA/RVMAT locais;
- manifest JSON opcional em `out/inspect/`;
- protecao contra qualquer escrita fora de `out/`.

Nao fazem parte do primeiro MVP: renderer, alteracao de cor, noise, preview,
generate, compare, distance fields, slope, curvature, coast ou analyze-style.
Os nomes futuros podem constar no README, mas nao devem existir como comandos
falsos ou modulos vazios.

## I. TEST PLAN

### MVP inspect

- parseia 26 classes/cores do fixture e rejeita duplicatas;
- ignora comentarios em `layers.cfg` sem engolir blocos validos;
- valida ASC retangular e detecta linha curta, NODATA e header invalido;
- preserva os bytes e hashes de todos os inputs;
- conta cores BMP em tiles e reporta unknown RGB exato;
- sugere nearest RGB sem promover alias;
- falha quando sat/mask diferem em dimensao;
- infere `m/px` somente quando world size e dimensao sao consistentes;
- rejeita output fora de `out/`, symlink escape e output igual a input;
- nao cria arquivo quando `inspect` roda sem `--json-out`.

### Renderer futuro

- determinismo byte-a-byte para mesma seed/preset/input;
- seeds diferentes alteram o campo;
- render completo e mosaico de tiles produzem pixels identicos;
- teste explicito da fronteira horizontal e vertical entre tiles;
- preview de uma janela coincide com o recorte do full render;
- estruturas amostradas a `1.0` e `0.5 m/px` coincidem em coordenadas mundiais;
- dimensoes e extensao fisica permanecem iguais;
- mask e inputs mantem hashes antes/depois;
- clipping fica abaixo de limiar declarado e e reportado, nunca oculto;
- falha injetada no meio do render nao publica arquivo final parcial.

### Distance/terrain futuros

- distance fields coincidem entre tiled e referencia pequena in-memory;
- slope/aspect respeitam orientacao ASC comprovada;
- effects zerados sao identidade;
- surface vizinha nunca altera a mask, apenas a aparencia do satellite.

## J. IMPLEMENTATION PHASES

1. **Contrato e inspect:** implementar apenas o MVP acima e rodar em fixtures e
   nos inputs reais read-only.
2. **Resolver gates manuais:** confirmar os quatro aliases RGB, atualizar paths
   do TV4P pela interface quando o autor decidir, e comprovar orientacao/registro.
3. **Preview sintetico:** implementar campos deterministas multiescala em
   world-space e testar invariancia/seams com imagens pequenas sinteticas.
4. **Preview Noronha:** integrar inputs reais read-only e produzir tres regioes
   A/B em `out/previews`, sem full render.
5. **Compare:** dimensoes, medias globais/per-surface, clipping, hashes e diff.
6. **Generate tiled:** BMP completo, output atomico, benchmark 10K e limite de
   memoria documentado; 20K somente depois do 10K.
7. **Neighbors:** distance-to-surface com alcance limitado ou algoritmo
   out-of-core comprovado.
8. **Heightmap:** slope/aspect/curvature sutis, depois de registro validado.
9. **Coast:** efeito especifico de Noronha, calibrado em previews.
10. **Analyze-style:** somente apos comprovar decoder/conversao local PAA
    read-only e licenca/redistribuicao; salvar apenas estatisticas derivadas.
11. **Promocao:** manual no Terrain Builder, seguida de build separado e
    `RUNTIME_VISUAL_REVIEW` no DayZ.

## K. EXACT FILES/DIRECTORIES THAT THE NEXT TASK SHOULD CREATE

Somente para a proxima tarefa (`scaffold + inspect`):

```text
P:\Noronha\tools\terrain_satgen\
|-- .gitignore
|-- README.md
|-- pyproject.toml
|-- presets\
|   `-- noronha.toml
|-- src\terrainsat\
|   |-- __init__.py
|   |-- __main__.py
|   |-- cli.py
|   `-- inspect.py
`-- tests\
    |-- test_inspect.py
    `-- fixtures\
        |-- heightmap.asc
        `-- layers.cfg
```

O teste deve criar imagens pequenas no diretorio temporario; nao versionar BMPs
fixture se Pillow puder gera-los durante o teste. O `.gitignore` local deve
ignorar pelo menos `/out/`, `/.venv/`, `/build/`, `/dist/` e `*.egg-info/`.

Nao criar ainda `renderer.py`, `noise.py`, `distance.py`, `styles.py`,
`diagnostics.py`, examples ou assets copiados. Cada arquivo entra junto da fase
que realmente o exige.

## L. ITEMS REQUIRING MANUAL TERRAIN BUILDER OR DAYZ VALIDATION

### MANUAL_TB_REVIEW

- confirmar que as quatro cores off-by-one da mask significam `cp_gravel`,
  `en_soil`, `en_stubble` e `cp_concrete2`;
- confirmar o comportamento atual da importacao dessas cores;
- abrir o projeto e conferir/reapontar os tres paths raster antigos;
- registrar Samplers reais: imagery resolution, satellite grid, tile size,
  overlap e texture layer size;
- verificar orientacao e alinhamento ASC/mask/satellite com landmarks;
- revisar `en_deforested.rvmat` ausente de `layers.cfg`;
- verificar o limite de quatro surfaces por tile usando os parametros reais;
- revisar visualmente cada preview e qualquer eventual promocao.

### RUNTIME_VISUAL_REVIEW

- aparencia macro/medium/local e ausencia de repeticao artificial;
- transicoes entre surfaces e ausencia de seams;
- leitura da costa, vegetacao, solo, rocha e areas urbanas;
- cor/exposicao sob lighting e weather reais de Noronha;
- mipmaps e transicao satellite/detail em diferentes distancias;
- resultado do WRP exportado no DayZ apos promocao manual.

Nenhuma verificacao estatica, teste Python, import do Terrain Builder ou build
RaG substitui essa revisao runtime.

## Baseline de integridade desta auditoria

Hashes observados antes de criar este documento:

```text
world/Noronha.wrp
  110C4BC4BEEA4AD87A1E20D756FBD700A363D9D748D44D58FFE009713FC81AA6
navmesh/navmesh.nm
  87FF7F33FDB9CC958BF3879EE2BEDAB5682590887D951E426269DF9035654803
source/QGIS/gtt_heightmap.asc
  832EC370CD9871688E25E0F1D7BF78E44E10F976D97739147B874FC441AA8A9E
Noronha_Workspace/assets-src/terrain/gtt_satmap.bmp
  1D2D37109DB1A6BFC825D1126FAB2F077CC93A5F5EA9E6E8BD0E54DFFCCB8107
Noronha_Workspace/assets-src/terrain/gtt_mask_osm.bmp
  DF3516A6C527BC5574DC0D2FF96BEC02AB9CED7BE8112BDB283FD15A09DFDC7B
```

Esses hashes devem ser repetidos ao encerrar a tarefa e em toda futura execucao
do `inspect` sobre os inputs reais.
