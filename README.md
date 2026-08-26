<div align="center">

# Fernando de Noronha — DayZ Map Mod

*Sobrevivência tropical brasileira inspirada no arquipélago de Fernando de Noronha.*

<br/>

<a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894" target="_blank">
  <img src="https://img.shields.io/badge/Steam_Workshop-171A21?style=for-the-badge&logo=steam&logoColor=white" alt="Steam Workshop" />
</a>

<br/><br/>

<a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894" target="_blank">
  <img src="https://images.steamusercontent.com/ugc/16706076935950692857/AB074CF857EDDDD21454844CC70E80C6E2197F8B/?imw=5000&imh=5000&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=false" width="50%" alt="Mapa de Fernando de Noronha no DayZ" />
</a>

<br/><br/>

` WORK IN PROGRESS `

</div>

---

## Desenvolvimento

Este é o repositório oficial do mapa: world, CE exportada, navmesh, sons,
configurações e artefatos runtime necessários para os PBOs. O addon de itens é
independente em [Noronha_Items](https://github.com/AdriianCOE/Noronha_Items) e é
uma dependência do CE.

- Mapa Workshop: <https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894>
- Noronha Items Workshop: <https://steamcommunity.com/sharedfiles/filedetails/?id=3698170839>

A documentação técnica está em [`docs/`](docs/): arquitetura, dependências, CE,
terreno, build, desenvolvimento, responsabilidades entre repositórios e
auditorias. O WRP DEV validado é rastreado por Git LFS; consulte
[`docs/TERRAIN.md`](docs/TERRAIN.md) para identidade, proveniência e limites do
baseline.

---

## Sobre o projeto

**Noronha** é um mapa custom para **DayZ** fortemente inspirado em Fernando de
Noronha, mas desenhado primeiro como um mapa de sobrevivência. A geografia,
nomes, praias, relevo e identidade brasileira servem como referência; distâncias,
densidade, construções, vegetação e pontos de interesse podem ser simplificados
ou adaptados quando isso melhora navegação, atmosfera e gameplay.

A meta não é reproduzir o arquipélago real metro por metro. O objetivo é fazer o
jogador reconhecer a inspiração em Noronha enquanto o mapa continua plausível,
legível e interessante dentro das limitações e sistemas de DayZ.

O projeto busca combinar:

- ambientação tropical oceânica;
- identidade brasileira sem depender de caricaturas;
- exploração costeira, urbana e de áreas isoladas;
- loot e objetos personalizados quando acrescentarem valor;
- clima, som e vegetação próprios do mapa;
- sobrevivência difícil e progressão pensada para uma ilha.

> **Aviso:** o mapa está em desenvolvimento e ainda longe da versão final.
> Terreno, loot, vegetação, construções, áreas jogáveis, ambientação e
> balanceamento continuarão recebendo mudanças. O estado atual é jogável, não
> uma representação definitiva da direção artística.

---

## Escala e área jogável

O projeto usa uma área de mundo de **10,24 km × 10,24 km** e mantém a forma geral
e vários marcos reconhecíveis de Fernando de Noronha. A escala percebida e o
conteúdo jogável, porém, são adaptados ao DayZ; o projeto não assume fidelidade
1:1 como requisito de design.
