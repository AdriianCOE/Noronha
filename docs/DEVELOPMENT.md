# Desenvolvimento

Use branches de reorganização e commits estreitos. Revise conteúdo normalizado para CRLF/LF antes de concluir que dois arquivos divergem. Nunca remova uma fonte única só porque parece cache.

Para placement costeiro:

```powershell
python source/scripts/coastal_placement2.0.py --heightmap source/QGIS/gtt_heightmap.asc --surfacemap <caminho-para-gtt_mask_osm.bmp> --output source/scripts/generated_coastal_objects
```

Instale as dependências com `python -m pip install -r source/scripts/requirements.txt`. Os arquivos `generated_coastal_objects_*_tb.txt` são outputs rastreados históricos; só atualize-os quando a geração for intencional e revisada.
