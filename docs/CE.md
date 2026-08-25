# Central Economy

`ce/` é a versão oficial exportada usada pelo mapa. `P:\Noronha_Workspace\ce-editor` é o projeto do CE Editor; `P:\Noronha_Workspace\mission-test` é somente a missão de teste.

Depois de aprovar uma exportação do CE Editor, atualize `ce/`, revise o diff e execute:

```powershell
P:\Noronha_Workspace\tools\sync-ce.ps1 -WhatIf
```

Use `-WhatIf` antes de uma sincronização sensível. O script preserva arquivos exclusivos da missão, como `areaflags.map`, e sobrescreve apenas os arquivos existentes na CE oficial.
