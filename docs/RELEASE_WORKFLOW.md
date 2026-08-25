# DEV, TEST e LIVE

Há uma única fonte por repositório. DEV, TEST e LIVE são estados de Git e de builds, não cópias de diretórios nem variantes da CE.

```text
feature/*
    |
    v
develop
    |
    v
TEST build local
    |
    v
main
    |
    v
tag v0.x.y
    |
    v
Workshop LIVE
```

## Convenção

- `main`: estado estável que pode corresponder à Workshop LIVE.
- `develop`: origem de trabalho integrado e das builds TEST. Só será criada a partir de uma `main` validada.
- `feature/*`: trabalho isolado, integrado em `develop`.
- `P:\Noronha_Builds\test\Noronha` e `P:\Noronha_Builds\test\Noronha_Items`: outputs locais, fora de qualquer repositório.
- `P:\Noronha_Builds\live-reference`: cópias de diagnóstico de PBOs da Workshop; nunca são fonte DEV.

Não existem `CE_DEV`, `CE_TEST`, `CE_REAL`, `Noronha_FINAL` ou pastas manuais equivalentes. A CE oficial é `ce/`; a missão offline recebe essa CE por `P:\tools\sync-ce.ps1`.

## Promoção e versões

Antes de publicar uma atualização, valide a build TEST, integre `develop` em `main`, crie uma tag `v0.x.y`, faça uma build limpa e registre commit, data e Workshop. Nenhum número de versão atual é presumido aqui.

Enquanto a branch `codex/repository-organization` não completar as validações de checkout, WRP e build, ela não deve ser integrada em `main`.
