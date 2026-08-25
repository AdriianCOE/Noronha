# Repositórios

- **Noronha** (público): mapa oficial, CE exportada, configs, scripts, sons e runtime comprovado.
- **Noronha_Items** (privado inicialmente): addon independente de bebidas, roupas e placas. Não depende do mapa.
- **NoronhaFiles** (privado): workspace do autor para Terrain Builder, CE Editor, GIS, fontes de textura, missão offline e utilitários.

Não mantenha dois masters para o mesmo conteúdo. Use um checkout Git de `Noronha` em `P:\Noronha` para DayZ Tools. Se a letra `P:` não puder apontar ao checkout, crie uma junction para ele; não copie arquivos manualmente.

Exemplo, em PowerShell elevado quando necessário:

```powershell
New-Item -ItemType Junction -Path P:\Noronha -Target C:\Users\drioj\Documents\GitHub\Noronha
```

Crie a junction somente depois de remover a cópia operacional antiga e preservar seus artefatos únicos.
