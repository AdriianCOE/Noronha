# Dependências

O mapa depende dos pacotes base DayZ já declarados nos patches próprios. A CE oficial usa classes `Noronha_*`; por isso `ce/config.cpp` requer explicitamente `Noronha_Items`.

Não adicione `Noronha_Items` a `world`, `data` ou `navmesh`: esses PBOs não referenciam classes do addon. Carregue o addon antes da CE/servidor que usa os types.

- Mapa: <https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894>
- Addon Noronha Items: <https://steamcommunity.com/sharedfiles/filedetails/?id=3698170839>
