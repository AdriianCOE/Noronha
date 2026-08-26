# Build

Pré-requisitos confirmados: DayZ Tools, RaG DayZ Tools, checkout do mapa em
`P:\Noronha`, checkout de `Noronha_Items` em `P:\Noronha_Items` e os dados
privados de autoria em `P:\Noronha_Workspace`.

## Workflow atual

1. Terrain Builder/GIS no workspace privado exporta `Noronha.wrp`;
2. WRP, navmesh e demais artefatos gerados são revisados antes de substituir o
   baseline validado;
3. CE é exportada para `Noronha/ce` e a missão de teste pode ser sincronizada
   pelo workspace;
4. **RaG DayZ Tools / RaG PBO Builder** é o builder atualmente validado para os
   PBOs do mapa;
5. o autor monta o mod final, testa no DayZ, assina quando necessário e publica
   no Workshop quando decidir.

Layout runtime esperado:

- `ce -> ce.pbo`
- `data -> data.pbo`
- `navmesh -> navmesh.pbo`
- `sounds -> sounds.pbo`
- `world -> world.pbo`

O `world` deve ser construído depois das dependências que referencia. O prefixo
do addon de sons permanece `Noronha\sounds`.

## Decisão de toolchain

Em 25/08/2026 o workflow baseado em Mikero pboProject passou a não ser confiável
para o WRP atual de Noronha: o programa reconhecia e inspecionava
`Noronha.wrp`, reportava sucesso, mas produzia um `world.pbo` de cerca de 22 KB
sem o WRP dentro. A lista de exclusões não continha `*.wrp` e limpar o temp não
alterou o resultado.

Após remover Mikero Tools e construir com RaG DayZ Tools, o WRP foi empacotado e
o mapa voltou a carregar corretamente. Por isso pboProject/MakePbo não fazem
mais parte do workflow oficial de build de Noronha. Utilitários externos de
inspeção só devem ser usados quando houver um motivo específico e sem alterar o
source.

## Automação

RaG PBO Builder possui CLI, mas a receita automatizada de Noronha ainda não está
congelada. Antes de criar `build-noronha.ps1`, registrar os valores do build RaG
que já funcionou (source, output, temp, exclusões, Binarize, CfgConvert e
assinatura). A automação futura deve preservar builds anteriores, produzir logs
e hashes, validar os cinco PBOs e nunca apagar um output conhecido como bom.

A chave `.biprivatekey` não deve ser versionada nem distribuída. O procedimento
de teste runtime e publicação Workshop permanece manual.
