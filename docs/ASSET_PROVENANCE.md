# Asset provenance

Este arquivo registra origem e status de procedencia dos assets usados ou planejados em Noronha. Nao atribua licenca sem evidencia.

## Status

- `VANILLA_REFERENCE`: asset fornecido pelo DayZ e apenas referenciado pelo config/mapa.
- `OWNED`: criado especificamente para Noronha pelo autor/projeto.
- `DERIVED`: modificado a partir de uma fonte cuja licenca permite derivacao; registrar fonte/licenca.
- `EXTERNAL_LICENSED`: asset externo com permissao/licenca comprovada.
- `REVIEW_REQUIRED`: origem/licenca ainda precisa ser confirmada.
- `PLANNED`: asset ainda nao existe.

## Runtime atual

| Area | Asset/fonte | Status | Observacao |
|---|---|---|---|
| world/data | texturas e materials vanilla referenciados pelo world | `VANILLA_REFERENCE` | revisar gradualmente dependencia visual de Enoch/Livonia |
| sounds | `birds_seagull.ogg` | `REVIEW_REQUIRED` | registrar autor/origem/licenca antes de redistribuicao publica do source |
| sounds | `birds-bemtevi.ogg` | `REVIEW_REQUIRED` | registrar autor/origem/licenca |
| sounds | `birds-gralhas.ogg` | `REVIEW_REQUIRED` | registrar autor/origem/licenca |
| sounds | `cigarra-sound.ogg` | `REVIEW_REQUIRED` | registrar autor/origem/licenca |
| items | addon `Noronha_Items` | `REVIEW_REQUIRED` por asset | repo separado; revisar PAA/modelos/logos individualmente antes de publicacao de source |
| terrain | `world/Noronha.wrp` | `OWNED`/projeto | artefato autoral do mapa; fontes pesadas ficam no workspace privado |
| navmesh | `navmesh/navmesh.nm` | `OWNED`/gerado | gerado para Noronha; nao editar manualmente |

## Assets planejados

| Asset | Status | Requisito antes de ativar |
|---|---|---|
| mapa de mao aberto/fechado/legenda | `PLANNED` | criar arte propria e documentar fonte de qualquer elemento externo |
| `envTexture` tropical | `PLANNED` | criar asset e testar no DayZ |
| `global_nohq` proprio | `PLANNED` | gerar a partir do terrain de Noronha e validar visualmente |
| `middle_mco` proprio | `PLANNED` | produzir asset especifico do mapa |
| `outside_sat_co` proprio | `PLANNED` | criar horizonte/oceano coerente com ilha |
| surfaces Noronha | `PLANNED` | texturas/materials com procedencia registrada |
| vegetacao tropical custom | `PLANNED` | confirmar licenca/permissao de cada pack/modelo antes de repack |
| objetos costeiros/brasileiros | `PLANNED` | registrar autor, URL, licenca e mudancas |

## Mods e referencias externas

Nao confundir referencia tecnica com permissao de redistribuicao.

- `willy92wins/DayZ-Modding-Knowledge-Pack`: MIT; usar principalmente como conhecimento/tooling.
- `willy92wins/dayz-mcp`: MIT; ferramenta DEV/QA externa, nao asset runtime de Noronha.
- `TrueDolphin/references`: durante a auditoria de 2026-08-26 nao foi observado `LICENSE` na raiz; tratar como reference-only.
- mods Workshop candidatos a vegetacao/fauna/objetos: **nao repackar** ate obter permissao explicita ou licenca que permita redistribuicao/repack.

## Registro para novo asset

Ao introduzir asset externo, registrar:

```text
Nome:
Tipo:
Autor:
Fonte/URL:
Licenca/permissao:
Data de verificacao:
Arquivo(s) usados:
Modificacoes realizadas:
Pode redistribuir?: sim/nao/incerto
Pode repackar?: sim/nao/incerto
Credito exigido:
Notas:
```

Se qualquer campo necessario estiver incerto, usar `REVIEW_REQUIRED` e nao publicar/repackar ate resolver.