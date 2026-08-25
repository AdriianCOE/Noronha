# Sons customizados

`world/config.cpp` referencia os quatro caminhos abaixo, todos existentes como
fonte no diretório `sounds/`:

- `Noronha\sounds\birds_seagull`
- `Noronha\sounds\birds-bemtevi`
- `Noronha\sounds\birds-gralhas`
- `Noronha\sounds\cigarra-sound`

## Estado LIVE observado em 25/08/2026

A instalação da Workshop `3682451894` contém apenas `ce.pbo`, `data.pbo`,
`navmesh.pbo` e `world.pbo`. Os inventários completos já capturados desses
quatro PBOs não contêm `.ogg` nem nenhum dos quatro nomes acima; também não há
OGG solto no diretório da Workshop. Portanto:

`LIVE_SOUND_PACKAGING = MISSING_FROM_LIVE`

Não há PBO, prefixo ou path virtual LIVE a registrar para esses sons. Isso é um
risco conhecido: os sons customizados provavelmente não funcionam corretamente
na versão pública atual, sujeito à confirmação pelo teste runtime do autor.

## Source preparado para o próximo build manual

O source agora prepara um addon independente `sounds -> sounds.pbo`, com prefixo
`Noronha\sounds`:

```text
sounds/
  $pboprefix$             # Noronha\sounds
  birds_seagull.ogg
  birds-bemtevi.ogg
  birds-gralhas.ogg
  cigarra-sound.ogg
```

O `$pboprefix$` contém exatamente `Noronha\sounds`. O `config.cpp` contém
somente `CfgPatches/Noronha_Sounds`, com dependência `DZ_Data`; não há
`CfgSounds` adicional. O world declara `Noronha_Sounds` em seu
`requiredAddons[]`.

O path virtual final permanece `Noronha\sounds\...`, sem alteração das
referências corretas do world. Esta preparação não gerou PBO, não prova o
empacotamento runtime e não substitui o build manual futuro em PBO Project.
