# Proposta de refactor futuro para `ce/init.c`

Status: proposta somente. Nenhum código de runtime é alterado por este
documento. O objetivo é permitir uma revisão posterior legível sem alterar
starter kit, RNG, CE ou gameplay inadvertidamente.

## CURRENT STRUCTURE

`main()` cria e inicializa a Hive offline e aplica a regra de data. A classe
`CustomMission` concentra:

1. `SetRandomHealth`: `Math.RandomFloat(0.45, 0.65)`.
2. `CreateCharacter`: cria/seleciona o jogador.
3. `StartingEquipSetup`: aplica saúde às roupas, troca a camisa de body com
   `Math.RandomFloatInclusive(0.0, 1.0) <= 0.15`, cria quatro `Rag`, uma
   chemlight, uma comida e uma `StoneKnife`, e define os atalhos 1–4.
4. `CreateCustomMission`: instancia `CustomMission`.

## PROPOSED STRUCTURE

Somente em uma futura branch isolada e depois de teste runtime, separar a
intenção em helpers privados ou funções equivalentes. A proposta declara a
chance como uma constante nomeada com o mesmo valor `0.15`, e mantém os
limites de saúde `0.45`/`0.65` igualmente explícitos:

```text
ApplyOfflineDatePolicy()
ApplyRandomHealth(item)
TryReplaceBodyWithTeamShirt(player)
EquipDefaultClothingHealth(player)
GiveStarterRags(player)
GiveRandomChemlight(player)
GiveRandomBeachFood(player)
GiveStarterKnife(player)
```

As listas de camisas, chemlights e comida devem permanecer locais ou em
constantes imutáveis com a mesma ordem. Se o refactor substituir os limites
literais por `array.Count()`, deve fazê-lo somente como equivalente direto de
`Math.RandomInt(0, 3)`/`Math.RandomInt(0, 4)`, preservando a exclusividade do
limite superior e a ordem dos arrays. O refactor não deve introduzir configs
novos, JSON, APIs externas ou alterar o ponto de criação da missão.

## SEMANTICS PRESERVED

- Intervalo de saúde `0.45` a `0.65`.
- Condição de camisa `<= 0.15`, usando o mesmo RNG inclusivo.
- Camisas: Palmeiras, Corinthians, Flamengo, nesta ordem.
- `Math.RandomInt(0, 3)` para camisa/comida e `Math.RandomInt(0, 4)` para
  chemlight — ou o `Count()` equivalente — com os arrays na ordem atual.
- Quatro `Rag` no atalho 2; chemlight no 1; comida no 3; `StoneKnife` no 4.
- `SetRandomHealth` aplicado aos mesmos itens e no mesmo fluxo condicional.
- `ObjectDelete` da roupa de body somente quando a condição atual vencer.
- Criação/seleção do player e `CreateCustomMission` inalteradas.

## SEMANTIC RISKS

- A política de data atual não normaliza todos os dias de janeiro/fevereiro.
  Isso é `SEMANTIC_REVIEW_REQUIRED`, não uma correção mecânica.
- Mover chamadas de RNG, mesmo com as mesmas listas, altera a sequência de
  aleatoriedade e pode mudar resultados observáveis.
- Trocar `RandomFloatInclusive` por `RandomFloat`, ou `<` por `<=`, altera a
  regra documentada de chance.
- Reordenar listas, inserir novos itens ou mover quickbar muda gameplay.
- Alterar a ordem `ObjectDelete`/`CreateAttachment`/saúde pode afetar
  inventário, attachment ou estado do item.

Uma futura alteração deve comparar o source antigo e novo linha a linha,
validar sintaxe com ferramenta DayZ real e executar smoke test manual. Não
fazer esse refactor junto com ajustes de CE, loot, tiers, fauna ou spawns.
