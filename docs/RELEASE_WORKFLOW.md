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

- `codex/repository-organization`: estado DEV atual da reorganização.
- `main`: linha pública existente; não é promovida automaticamente nesta etapa.
- `develop`: não existe e não deve ser criada antes de um build manual e smoke
  test relevantes concluídos pelo autor.
- `feature/*`: trabalho isolado quando necessário; não pressupõe uma branch de
  integração enquanto `develop` não existir.
- `P:\Noronha_Builds\test\Noronha` e `P:\Noronha_Builds\test\Noronha_Items`: outputs locais, fora de qualquer repositório.
- `P:\Noronha_Builds\live-reference`: cópias de diagnóstico de PBOs da Workshop; nunca são fonte DEV.

Não existem `CE_DEV`, `CE_TEST`, `CE_REAL`, `Noronha_FINAL` ou pastas manuais equivalentes. A CE oficial é `ce/`; a missão offline recebe essa CE por `P:\tools\sync-ce.ps1`.

## Promoção e versões

O autor executa o build final com PBO Project, monta a combinação de mods e
realiza os testes DayZ. Depois de uma validação manual relevante, ele decide se
promove branches, cria uma tag e publica no Workshop. Nenhum número de versão,
promoção para `main` ou criação de `develop` é presumido aqui.

Enquanto a branch `codex/repository-organization` não completar as validações
manuais de WRP e runtime, ela não deve ser integrada em `main`.
