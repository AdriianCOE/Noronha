# Build

Pré-requisitos confirmados: DayZ Tools, PBO Project, checkout do mapa em
`P:\Noronha`, checkout de `Noronha_Items` em `P:\Noronha_Items`, e os dados
privados do Terrain Builder/CE Editor.

Ordem conhecida:

1. Terrain Builder/GIS no workspace privado exporta `Noronha.wrp`;
2. revisar WRP e navmesh e promover somente artefatos identificados e
   validados;
3. exportar CE para `Noronha/ce` e sincronizar a missão offline;
4. PBO Project é o workflow de build manual usado pelo autor para Noronha
   Items e para os PBOs do mapa;
5. o autor monta o mod, testa no DayZ e publica quando decidir.

Layout de PBO do mapa preparado em source: `ce -> ce.pbo`, `data -> data.pbo`,
`navmesh -> navmesh.pbo`, `world -> world.pbo` e `sounds -> sounds.pbo`.
O prefixo do addon de sons é `Noronha\sounds`.

Em 25/08/2026 foi construído um conjunto TEST separado (`Noronha_Items.pbo`,
`world.pbo`, `navmesh.pbo`, `ce.pbo` e `data.pbo`) exclusivamente como
diagnóstico com Addon Builder. Ele não representa a pipeline oficial, não deve
ser montado, assinado ou publicado e não substitui o build manual futuro em PBO
Project. A validação estática desse conjunto passou; ele continua apenas um
artefato diagnóstico e não substitui o workflow manual do autor.

Os comandos e as opções específicas de PBO Project ainda não foram comprovados
e não estão versionados; registrá-los após o workflow manual estabilizar é um
TODO explícito. O procedimento de publicação Workshop também permanece manual.
