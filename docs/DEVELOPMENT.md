# Desenvolvimento

`main` e a branch normal de desenvolvimento de Noronha. Mudancas pequenas, reversiveis e bem delimitadas podem ser commitadas diretamente nela. Use uma branch temporaria somente para trabalho grande, arriscado ou que precise ser isolado; depois de validar e integrar, remova a branch.

Revise conteudo normalizado para CRLF/LF antes de concluir que dois arquivos divergem. Nunca remova uma fonte unica so porque parece cache.

## Disciplina DayZ

As regras para agentes e automacao estao em [`../AGENTS.md`](../AGENTS.md). Em especial:

- nao inventar API/config/path DayZ;
- confirmar comportamento no source vanilla quando possivel;
- separar validacao STATIC, BUILD e RUNTIME;
- nao regenerar WRP/navmesh/heightmap/layers sem escopo deliberado;
- manter `DayZ_MCP` e outras ferramentas de QA fora das dependencias runtime do mapa.

As referencias externas e seus papeis estao em [ENGINEERING_REFERENCES.md](ENGINEERING_REFERENCES.md).

## DEV / TEST / LIVE

DEV, TEST e LIVE sao estados do projeto e de builds, nao copias manuais de source. O fluxo esta em [RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md). Builds locais pertencem a `P:\Noronha_Builds`, nunca ao checkout de source.

O builder oficial atual e RaG DayZ Tools. O autor controla montagem final, smoke test no DayZ, assinatura e publicacao.

## Placement costeiro

O generator em `source/scripts/coastal_placement.py` e uma ferramenta OFFLINE de autoria; ele nao roda dentro do DayZ.

Exemplo:

```powershell
python source/scripts/coastal_placement.py --heightmap source/QGIS/gtt_heightmap.asc --surfacemap <caminho-para-gtt_mask_osm.bmp> --output source/scripts/generated_coastal_objects
```

Instale as dependencias com:

```powershell
python -m pip install -r source/scripts/requirements.txt
```

Os arquivos `generated_coastal_objects_*_tb.txt` sao outputs rastreados historicos; so atualize quando a geracao for intencional e revisada. Profiles, seed, dry-run e estatisticas devem ser preferidos a ajustes hardcoded quando a ferramenta oferecer essas opcoes.

## Antes de pedir um teste in-game

1. esgotar parse/lint/hash/preflight offline;
2. agrupar apenas mudancas coerentes;
3. definir exatamente o que observar;
4. construir com RaG;
5. registrar `KEEP / ADJUST / REVERT` depois do teste.

Quando o DayZ-MCP for configurado como ferramenta DEV, ele deve servir para tornar fixtures de runtime reproduziveis, nao para substituir julgamento visual humano ou virar dependencia de release.