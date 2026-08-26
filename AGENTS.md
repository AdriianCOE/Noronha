# Noronha agent rules

Estas regras valem para agentes de codigo trabalhando neste repositorio.

## Objetivo

Noronha e um mapa DayZ fortemente inspirado em Fernando de Noronha, mas nao e uma reproducao 1:1. Fidelidade visual, identidade tropical/brasileira, legibilidade e gameplay devem ser equilibrados. Nao adicione complexidade apenas porque existe na ilha real ou em outro mapa.

## Regras de engenharia

1. **Nao invente API DayZ.** Antes de escrever uma chamada Enforce Script, classe/config desconhecida, selection/memory point de P3D ou path vanilla, confirme no source vanilla local (`P:\scripts`, `P:\DZ`, ou outra arvore oficial disponivel) ou em uma referencia verificavel. Memoria e exemplos da internet sao pistas, nao prova.
2. **Separe autoria, build e runtime.** Terrain Builder/GIS/Python produzem fontes; RaG DayZ Tools constroi os PBOs; DayZ valida comportamento. Nao trate um resultado estatico como prova runtime.
3. **Seja explicito sobre verificacao.** Declare o que foi validado por parse/lint/hash/build e o que ainda exige DayZ. `CfgConvert passou` nao significa `funciona no jogo`.
4. **Evite ciclos de teste caros.** Faça primeiro checks offline, agrupe mudancas coerentes e planeje o smoke test antes de pedir rebuild.
5. **Preserve artefatos autoritativos.** Nao regenere ou substitua `world/Noronha.wrp`, `navmesh/navmesh.nm`, heightmap, satellite, mask ou layers gerados sem necessidade deliberada e revisao manual.
6. **Nao misture CE sem pedido explicito.** Mudancas de mapa/codigo fora de CE devem permanecer separadas de `ce/` quando a tarefa nao exigir economia/spawns.
7. **Main e a branch normal.** Mudancas pequenas e reversiveis podem ir direto para `main`. Use branch temporaria apenas para trabalho grande/arriscado; apos validar e integrar, remova a branch.
8. **RaG e o builder oficial atual.** Nao reintroduza Mikero/pboProject como workflow oficial. Ferramentas externas podem ser usadas para inspecao/preflight quando agregarem evidencia.
9. **Nao crie `Noronha_Scripts` por antecipacao.** Esgote primeiro `CfgWorlds`, configs, assets e sons. Um addon runtime so deve existir quando uma necessidade real nao puder ser resolvida de forma mais simples.
10. **Nao copie Nyheim ou outras referencias como arquitetura obrigatoria.** Extraia tecnicas e adapte ao tamanho/objetivo de Noronha.

## Referencias externas e como usa-las

- `kerkkoh/nyheim`: prior art de mapa completo, especialmente organizacao de world, weather, assets proprios, surfaces e autoria de terrain.
- `willy92wins/DayZ-Modding-Knowledge-Pack`: referencia tecnica e de processo. Priorize a disciplina de API verificada, client/server, preflight e validacao offline. O pack e MIT, mas prefira referenciar/consultar a copiar grandes blocos.
- `willy92wins/dayz-mcp`: ferramenta DEV/QA para observar e controlar DayZ em execucao. Deve permanecer separada do mod publicado e nunca virar dependencia runtime de Noronha.
- `TrueDolphin/references`: biblioteca de exemplos e ideias. Como nao foi observado `LICENSE` na raiz durante a auditoria de 2026-08-26, trate como **reference-only**: aprenda a tecnica e reimplemente quando util; nao copie arquivos inteiros para Noronha sem permissao/licenca clara.

Veja `docs/ENGINEERING_REFERENCES.md` para o papel de cada referencia e `docs/BUILD.md` para o workflow de build.

## Hierarquia de evidencia

Use esta ordem quando houver conflito:

1. comportamento medido no DayZ atual;
2. source/config vanilla atual;
3. source atual de Noronha;
4. referencias tecnicas verificadas;
5. exemplos comunitarios;
6. memoria/hipotese.

Uma referencia comunitaria nunca substitui um teste do engine quando os dois divergem.

## Antes de concluir uma mudanca

- revise `git diff` e paths runtime;
- rode validacao adequada ao tipo de arquivo (Python/JSON/CfgConvert/linter quando disponivel);
- confirme que WRP/navmesh/heightmap nao mudaram se nao faziam parte do escopo;
- marque qualquer mudanca visual como `RUNTIME_VISUAL_REVIEW` ate ser vista no DayZ;
- registre trabalho que depende de Terrain Builder/arte como `MANUAL_TB_REVIEW` ou `MANUAL_ASSET_REQUIRED`, em vez de inventar placeholder runtime.