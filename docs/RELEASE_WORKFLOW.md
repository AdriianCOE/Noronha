# DEV, TEST e LIVE

Ha uma unica fonte por repositorio. DEV, TEST e LIVE sao estados de Git, builds e Workshop; nao sao copias de diretorios nem variantes paralelas do mapa.

```text
Terrain Builder / GIS / Python
            |
            v
       source/runtime
            |
            v
    validacao estatica
            |
            v
      RaG DayZ Tools
            |
            v
   P:\Noronha_Builds
            |
            v
      teste no DayZ
            |
            v
   publicacao manual
```

## Convencao Git

- `main`: branch normal e fonte canonica do estado atual do projeto.
- mudancas pequenas e reversiveis podem ir direto para `main` com commits estreitos.
- `feature/*`: branch **temporaria**, usada apenas para trabalho grande/arriscado que precise de isolamento. Apos validar e integrar, deve ser removida.
- nao manter `develop` permanente apenas para duplicar o estado de `main`.

Tags tecnicas podem congelar checkpoints importantes, mas uma tag nao representa automaticamente uma versao publica ou publicacao Workshop.

## Outputs

- `P:\Noronha_Builds`: builds locais, logs, manifests e referencias; fora de qualquer repo.
- referencias de PBOs da Workshop podem ser preservadas para diagnostico, mas nunca viram fonte DEV.
- nao criar `Noronha_FINAL`, `Noronha_REAL`, `Noronha_TEST2` ou copias manuais equivalentes como fonte concorrente.

A fonte oficial de cada artefato deve continuar unica.

## Toolchain

O builder oficial atual de Noronha e **RaG DayZ Tools**. Mikero/pboProject nao faz parte do workflow oficial atual.

Ordem logica dos addons do mapa:

```text
ce
data
navmesh
sounds
world   <- por ultimo
```

O autor executa o build final, monta a combinacao de mods, testa no DayZ, assina quando necessario e publica no Workshop quando decidir.

## Tres niveis de verificacao

### STATIC

Exemplos: CfgConvert, JSON/XML parse, Python tests, hashes, paths, LFS e linters opcionais.

STATIC limpo significa que o source passou os checks executados; nao prova comportamento no engine.

### BUILD

Validar que RaG produziu os PBOs esperados e que o artefato final e plausivel. A automacao futura deve conferir, no minimo:

- `ce.pbo`;
- `data.pbo`;
- `navmesh.pbo`;
- `sounds.pbo`;
- `world.pbo`;
- tamanho/estrutura plausiveis;
- hashes e log/manifest.

### RUNTIME

Somente o DayZ confirma comportamento real. Mudancas de lighting, weather, fog, sons, surfaces e outros efeitos visuais continuam `RUNTIME_VISUAL_REVIEW` ate serem observadas no jogo.

O DayZ-MCP pode ser usado futuramente como ferramenta DEV para repetir fixtures de runtime, mas nunca deve virar dependencia do release de Noronha.

## Promocao

O fluxo normal e:

```text
main/source
   -> validacao estatica
   -> build RaG
   -> smoke test DayZ
   -> KEEP / ADJUST / REVERT
   -> tag/release quando fizer sentido
   -> Workshop manual
```

Uma feature branch so existe enquanto o risco justifica isolamento. Depois do merge, apagar a branch mantem o repositorio simples sem apagar o historico Git.