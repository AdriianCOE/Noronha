# Central Economy

`ce/` é a versão oficial exportada usada pelo mapa. `NoronhaFiles/Noronha2` é o projeto do CE Editor; `NoronhaFiles/dayzOffline.Noronha` é somente a missão de teste.

Depois de aprovar uma exportação do CE Editor, atualize `ce/`, revise o diff e execute:

```powershell
P:\tools\sync-ce.ps1 -Source C:\Users\drioj\Documents\GitHub\Noronha\ce -Destination P:\dayzOffline.Noronha
```

Use `-WhatIf` antes de uma sincronização sensível. O script preserva arquivos exclusivos da missão, como `areaflags.map`, e sobrescreve apenas os arquivos existentes na CE oficial.
