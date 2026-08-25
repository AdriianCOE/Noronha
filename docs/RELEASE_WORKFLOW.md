# DEV, TEST e LIVE

Há uma única fonte por repositório. DEV, TEST e LIVE são estados de Git e de builds, não cópias de diretórios nem variantes da CE.

```text
Terrain Builder -> Noronha.wrp
                         |
                         v
                    PBO Project
                         |
                         v
          autor monta, testa e publica manualmente
```

## Convenção

- `main`: baseline técnica estável, marcada por `baseline-2026-08-25`.
- `develop`: integração do próximo desenvolvimento, criada a partir da baseline.
- `feature/*`: trabalho isolado, criado a partir de `develop`.
- `P:\Noronha_Builds\test\Noronha` e `P:\Noronha_Builds\test\Noronha_Items`: outputs locais, fora de qualquer repositório.
- `P:\Noronha_Builds\live-reference`: cópias de diagnóstico de PBOs da Workshop; nunca são fonte DEV.

Não existem `CE_DEV`, `CE_TEST`, `CE_REAL`, `Noronha_FINAL` ou pastas manuais equivalentes. A CE oficial é `ce/`; a missão offline recebe essa CE por `P:\Noronha_Workspace\tools\sync-ce.ps1`.

## Promoção e versões

O autor executa o build final com PBO Project, monta a combinação de mods e
realiza os testes DayZ. A tag técnica não representa uma versão pública nem uma
publicação Workshop; novas mudanças seguem por `feature/*` e são integradas em
`develop` antes de qualquer promoção deliberada para `main`.
