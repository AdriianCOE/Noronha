// =============================================================
//  NORONHA — Fernando de Noronha | DayZ Mod
//  Autor: AdriianCOE
//  Steam: https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894
//  Clima tropical do Atlantico Sul — Hemisferio Sul, Brasil.
// =============================================================

class CfgPatches
{
    class Noronha
    {
        units[]={};
        weapons[]={};
        requiredVersion=0.1;
        requiredAddons[]={
            "DZ_Data",
            "DZ_Surfaces",
            "DZ_Surfaces_Bliss",
        };
        author="Adrian";
        name="Noronha";
        url="https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894";
    };
};

// =============================================================
// CENAS DO MENU PRINCIPAL
// =============================================================
class cfgCharacterScenes
{
    class Noronha
    {
        class loc1 { target[]={5815.05, 54.29, 5825.00}; position[]={5815.05, 54.29, 5809.21}; fov=0.52359998; date[]={2026,2,23,12,00}; overcast=0.05; rain=0; fog=0; };
    };
};

// =============================================================
// MUNDOS
// =============================================================
class CfgWorlds
{
    class DefaultLighting;
    class DefaultWorld;

    class CAWorld: DefaultWorld
    {
        class Grid;
        class Sounds;
        class Ambient;
        class Weather
        {
            class Overcast
            {
                class Weather1;  class Weather2;  class Weather3;
                class Weather4;  class Weather5;  class Weather6;
                class Weather7;  class Weather8;  class Weather9;
                class Weather10; class Weather11; class Weather12;
            };
        };
    };

    class Noronha: CAWorld
    {
        // ---------------------------------------------------------
        // INFORMACOES BASICAS
        // ---------------------------------------------------------
        access=3;
        worldId=3000;
        description="Noronha";
        worldName="Noronha\world\Noronha.wrp";
        heightBlendingMode=1;
        bicubicMode=1;
        ceFiles="Noronha\ce";

        icon="";
        pictureMap="";
        pictureShot="";

        cutscenes[]=
		{
			"NoronhaIntro"
		};

        plateFormat="### - ####";
        plateLetters="ABCDEGHIKLMNOPRSTVXZ";

        mapSize=10240;
        latitude=-3.84;
        longitude=-32.42;

        mapDisplayNameKey="Guia Turistico de Noronha";
        mapDescriptionKey="Um desdobravel colorido prometendo 'as ferias mais inesqueciveis da sua vida'. Mostra trilhas, praias paradisiacas e pontos de mergulho. Hoje, e a unica coisa que te impede de se perder na selva.";
        mapTextureClosed="dz\gear\navigation\data\map_enoch_co.paa";
		mapTextureOpened="dz\structures_bliss\signs\tourist\data\karta_enoch_co.paa";
		mapTextureLegend="dz\structures_bliss\signs\tourist\data\karta_enoch_side_co.paa";

        oceanMaterial="dz\water\data\ocean_samplemap.emat";
        oceanNiceMaterial="dz\water\data\ocean_nice_samplemap.emat";
        oceanStormMaterial="dz\water\data\ocean_storm_samplemap.emat";
 
        // ---------------------------------------------------------
        // TERRENO EXTERNO
        // ---------------------------------------------------------
        class OutsideTerrain
        {
            satellite="\DZ\rocks\Data\MainTextures\terrain\cp_gravel_co.paa";
            enableTerrainSynth=0;
            class Layers
            {
                class Layer0
                {
                    nopx="\DZ\surfaces_bliss\data\terrain\en_grass1_nopx.paa";
                    texture="\DZ\surfaces_bliss\data\terrain\en_grass1_ca.paa";
                };
            };
        };

        // ---------------------------------------------------------
        // NAVMESH — IA e Animais
        // ---------------------------------------------------------
        class Navmesh
        {
            navmeshName="Noronha\navmesh\navmesh.nm";
            filterIsolatedIslandsOnLoad=1;
            visualiseOffset=0;
            class GenParams
            {
                tileWidth=50;
                cellSize1=0.25; cellSize2=0.1; cellSize3=0.1;
                filterIsolatedIslands=1;
                seedPosition[]={5120,0,5120};
                class Agent
                {
                    diameter=0.60000002; standHeight=1.5; crouchHeight=1;
                    proneHeight=0.5; maxStepHeight=0.45; maxSlope=60;
                };
                class Links
                {
                    class ZedJump387_050   { jumpLength=1.50; jumpHeight=0.50; minCenterHeight=0.30;  jumpDropdownMin=0.5;  jumpDropdownMax=-0.5;  areaType="jump0"; flags[]={"jumpOver"}; color=1727987712; };
                    class ZedJump388_050   { jumpLength=1.50; jumpHeight=0.50; minCenterHeight=-0.5;  jumpDropdownMin=0.5;  jumpDropdownMax=-0.5;  areaType="jump0"; flags[]={"jumpOver"}; color=1725781248; };
                    class ZedJump387_110   { jumpLength=3.90; jumpHeight=1.10; minCenterHeight=0.5;   jumpDropdownMin=0.5;  jumpDropdownMax=-0.5;  areaType="jump0"; flags[]={"jumpOver"}; color=1711308800; };
                    class ZedJump420_160   { jumpLength=4.00; jumpHeight=1.60; minCenterHeight=1.1;   jumpDropdownMin=0.5;  jumpDropdownMax=-0.5;  areaType="jump0"; flags[]={"jumpOver"}; color=1711276287; };
                    class ZedJump265_210   { jumpLength=2.45; jumpHeight=2.50; minCenterHeight=1.8;   jumpDropdownMin=0.5;  jumpDropdownMax=-0.5;  areaType="jump0"; flags[]={"climb"};    color=1720975571; };
                    class Fence50_110deer  { typeId=100; jumpLength=8.0; jumpHeight=1.1; minCenterHeight=0.5; jumpDropdownMin=1.0; jumpDropdownMax=-1.0; areaType="jump2"; flags[]={"jumpOver"}; color=1722460927; };
                    class Fence110_160deer { typeId=101; jumpLength=8.0; jumpHeight=1.6; minCenterHeight=1.1; jumpDropdownMin=1.0; jumpDropdownMax=-1.0; areaType="jump3"; flags[]={"jumpOver"}; color=1713700856; };
                    class Fence50_110hen   { typeId=110; jumpLength=4.0; jumpHeight=1.1; minCenterHeight=0.5; jumpDropdownMin=0.5; jumpDropdownMax=-0.5; areaType="jump4"; flags[]={"jumpOver"}; color=-22016; };
                    class Fence110_160hen  { typeId=111; jumpLength=4.0; jumpHeight=1.6; minCenterHeight=1.1; jumpDropdownMin=0.5; jumpDropdownMax=-0.5; areaType="jump4"; flags[]={"jumpOver"}; color=-22016; };
                };
            };
        };

        // ---------------------------------------------------------
        // GRID DO MAPA
        // ---------------------------------------------------------
        class Grid: Grid
        {
            offsetX=0; offsetY=10240;
            class Zoom1 { zoomMax=0.15;  format="XY"; formatX="000"; formatY="000"; stepX=100;   stepY=-100;   };
            class Zoom2 { zoomMax=0.85;  format="XY"; formatX="00";  formatY="00";  stepX=1000;  stepY=-1000;  };
            class Zoom3 { zoomMax=1e+30; format="XY"; formatX="0";   formatY="0";   stepX=10000; stepY=-10000; };
        };

        startTime="13:00";
        startDate="23/02/2026";

        // ---------------------------------------------------------
        // ILUMINACAO — CICLO SOLAR TROPICAL
        // ---------------------------------------------------------
        class Lighting: DefaultLighting
        {
            class Lighting0
            {
                height=1.0;
                ambient[]={0.65, 0.68, 0.65, 1.0}; // mais alto e neutro — levanta as sombras dos objetos
                diffuse[]={2.20, 2.05, 1.85, 1.0}; // leve quente no sol direto
                diffuseCloud[]={1.05, 1.0, 0.95, 1.0};
            };

            class Lighting1
            {
                height=0.15;
                ambient[]={0.55, 0.55, 0.52, 1.0};
                diffuse[]={1.90, 1.75, 1.50, 1.0};
                diffuseCloud[]={0.95, 0.85, 0.75, 1.0};
            };
            class Lighting15  // Transicao suave para crepusculo
            {
                height=0.05;
                ambient[]={0.20, 0.22, 0.25, 1.0};
                diffuse[]={1.20, 0.80, 0.50, 1.0};
                diffuseCloud[]={0.60, 0.40, 0.30, 1.0};
            };
            class Lighting2  // Por do sol — laranja/vermelho no horizonte
            {
                height=0.0;
                ambient[]={0.10, 0.10, 0.15, 1.0};
                diffuse[]={0.80, 0.40, 0.20, 1.0};
                diffuseCloud[]={0.50, 0.20, 0.10, 1.0};
            };
            class Lighting25  // Crepusculo — roxo escuro
            {
                height=-0.05;
                ambient[]={0.05, 0.05, 0.08, 1.0};
                diffuse[]={0.20, 0.10, 0.25, 1.0};
                diffuseCloud[]={0.10, 0.05, 0.15, 1.0};
            };
            class Lighting3  // Noite — ilha remota, escuro real
            {
                height=-0.2;
                ambient[]={0.02, 0.02, 0.04, 1.0};
                diffuse[]={0.08, 0.09, 0.15, 1.0};
                diffuseCloud[]={0.04, 0.04, 0.06, 1.0};
            };
        };

        // ---------------------------------------------------------
        // CLIMA — 12 ESTAGIOS TROPICAIS
        // ---------------------------------------------------------
        class Weather: Weather
        {
            class Overcast: Overcast
            {
                // W1 — Azul atlantico puro
                class Weather1: Weather1
                {
                    overcast=0.05; lightingOvercast=0;
                    sky="#(argb,8,8,3)color(0.18,0.42,0.75,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.25; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W2 — Poucos cumulus brancos
                class Weather2: Weather2
                {
                    overcast=0.10; lightingOvercast=0.05;
                    sky="#(argb,8,8,3)color(0.18,0.42,0.75,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage10_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.22; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W3 — Cumulus crescendo
                class Weather3: Weather3
                {
                    overcast=0.16; lightingOvercast=0.10;
                    sky="#(argb,8,8,3)color(0.20,0.44,0.76,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage11_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.20; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W4 — Dia tipico de Noronha
                class Weather4: Weather4
                {
                    overcast=0.22; lightingOvercast=0.12;
                    sky="#(argb,8,8,3)color(0.22,0.46,0.76,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage12_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.18; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W5 — Raios de sol entre cumulus
                class Weather5: Weather5
                {
                    overcast=0.30; lightingOvercast=0.15;
                    sky="#(argb,8,8,3)color(0.25,0.46,0.72,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage13_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.20; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W6 — Semi-nublado, cirrus no horizonte
                class Weather6: Weather6
                {
                    overcast=0.38; lightingOvercast=0.18;
                    sky="#(argb,8,8,3)color(0.28,0.46,0.68,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\enoch\data\Sky_Stage10_Cirrus_en_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage14_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=1;
                    godrayStrength=0.15; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W7 — Pre-trovoada
                class Weather7: Weather7
                {
                    overcast=0.46; lightingOvercast=0.20;
                    sky="#(argb,8,8,3)color(0.30,0.44,0.62,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\enoch\data\Sky_Stage10_Cirrus_en_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage15_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0.80;
                    godrayStrength=0.12; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W8 — Nublado, chuva possivel
                class Weather8: Weather8
                {
                    overcast=0.54; lightingOvercast=0.25;
                    sky="#(argb,8,8,3)color(0.28,0.38,0.55,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\enoch\data\Sky_Stage10_Cirrus_en_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage16_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0.65;
                    godrayStrength=0.08; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W9 — Nublado pesado
                class Weather9: Weather9
                {
                    overcast=0.62; lightingOvercast=0.40;
                    sky="#(argb,8,8,3)color(0.22,0.30,0.44,1.0,CO)";
                    skyR="DZ\data\data\sky_clear_lco.paa";
                    farCloud="DZ\worlds\enoch\data\Sky_Stage10_Cirrus_en_sky.paa";
                    cloud="DZ\worlds\enoch\data\Cloud_Stage16_Cumulus_en_sky.paa";
                    cloudClip=0.80000001;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage01_ClearHills_sky.paa";
                    horizonClip=0.80000001;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0.50;
                    godrayStrength=0.04; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W10 — Trovoada a aproximar
                class Weather10: Weather10
                {
                    overcast=0.72; lightingOvercast=0.72;
                    sky="#(argb,8,8,3)color(0.16,0.22,0.32,1.0,CO)";
                    skyR="DZ\data\data\sky_semicloudy_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Cloud_Stage20_Altostratus_sky.paa";
                    cloud="DZ\worlds\chernarusplus\data\Cloud_Stage01_Transparent_sky.paa";
                    cloudClip=0;
                    horizon="DZ\worlds\chernarusplus\data\Horizont_Stage02_FoggyHills_sky.paa";
                    horizonClip=0;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0.35;
                    godrayStrength=0; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W11 — Trovoada tropical intensa
                class Weather11: Weather11
                {
                    overcast=0.85; lightingOvercast=1;
                    sky="#(argb,8,8,3)color(0.08,0.10,0.14,1.0,CO)";
                    skyR="DZ\data\data\sky_mostlycloudy_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Sky_Stage30_Stratocumulus_sky.paa";
                    cloud="DZ\worlds\chernarusplus\data\Cloud_Stage30_Nimbostratus_sky.paa";
                    cloudClip=0;
                    horizon="DZ\worlds\chernarusplus\data\Cloud_Stage00_Transparent_sky.paa";
                    horizonClip=0;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0;
                    godrayStrength=0; diffuse=0; cloudDiffuse=0; waves=0;
                };
                // W12 — Tempestade total
                class Weather12: Weather12
                {
                    overcast=1.01; lightingOvercast=1;
                    sky="#(argb,8,8,3)color(0.06,0.07,0.09,1.0,CO)";
                    skyR="DZ\data\data\sky_mostlycloudy_lco.paa";
                    farCloud="DZ\worlds\chernarusplus\data\Sky_Stage30_Stratocumulus_sky.paa";
                    cloud="DZ\worlds\chernarusplus\data\Cloud_Stage31_Nimbostratus_sky.paa";
                    cloudClip=0;
                    horizon="DZ\worlds\chernarusplus\data\Cloud_Stage00_Transparent_sky.paa";
                    horizonClip=0;
                    alpha=0; bright=0; speed=0; size=0; height=0; through=0;
                    godrayStrength=0; diffuse=0; cloudDiffuse=0; waves=0;
                };
            };

            class VolFog
            {
                CameraFog = 0;
                
                    // Distância (m), Densidade, Altura, ..., Ativação
                    Item1[] = {3000,  0.00,  0.0,  0.00, 1}; // Limpo
                    Item2[] = {7000,  0.00,  0.0,  0.00, 1}; // Limpo
                    Item3[] = {8000,  0.00,  0.0,  0.00, 1}; // Limpo
                    Item4[] = {12000, 0.001, 0.05, 0.00, 1}; // Densidade 0.001 só na borda do mundo para disfarçar o corte do mapa
                    
                    UseDynamic = 1; // Trava o fog dinâmico do servidor para não fechar o tempo de surpresa
                };

        };
        volFogOffset=0;
        maxDynLights=64;

        // ---------------------------------------------------------
        // CEU NOTURNO — Hemisferio Sul, Via Lactea invertida
        // ---------------------------------------------------------
        spaceObject="DZ\Data\data\milkyway.p3d";
        spaceObjectRotationPreOffset[]={0,0,0};
        spaceObjectRotationOffset[]={0,180,0};
        spaceTexture0="DZ\Data\data\milkyway_left_co.paa";
        spaceTexture1="DZ\Data\data\milkyway_right_co.paa";
 
        atmosphereObject="DZ\Data\data\atmosphere.p3d";
        atmosphereTexture="DZ\worlds\chernarusplus\data\Sky_Stage01_Clear_sky.paa";
 
        farCloudObject="DZ\Data\data\obloha.p3d";
        farCloudObjectRotationAxis[]={0,1,0};
        farCloudObjectRotationSpeed=3;
 
        cloudObject="DZ\Data\data\cloudObject.p3d";
        cloudObjectRotationAxis[]={0,1,0};
        cloudObjectRotationSpeed=9;
 
        horizonObject="DZ\Data\data\horizont.p3d";
        horizonObjectRotationAxis[]={0,1,0};
        horizonObjectRotationSpeed=0;
 
        // ---------------------------------------------------------
        // SONS AMBIENTE DA ILHA
        // ---------------------------------------------------------
        class Sounds: Sounds
        {
            sounds[]={};
            
            class OceanWaves
            {
                name="ocean_waves_noronha";
                sound[]={"dz\sounds\environment\water\river_close_loop", db(12), 1.0}; 
                frequency=1.0;
                volume="sea"; 
                range=300;
            };

            class SeaBirds
            {
                name="seagulls_ambient_noronha";
                sound[]={"Noronha\sounds\birds_seagull", db(10), 1.0}; 
                frequency=0.2;
                volume="(1 - night) * (1 - rain) * sea"; 
                range=200;
            };

            class TropicalBirds
            {
                name="bemtevi_ambient_noronha";
                sound[]={"Noronha\sounds\birds-bemtevi", db(8), 1.0}; 
                frequency=0.15; 
                volume="(1 - night) * (1 - rain) * trees"; 
                range=150;
            };

            class GralhasBirds
            {
                name="gralhas_ambient_noronha";
                sound[]={"Noronha\sounds\birds-gralhas", db(8), 1.0}; // Sem o .ogg!
                frequency=0.10;
                volume="(1 - night) * (1 - rain) * trees"; 
                range=150;
            };
            
            class Cicadas
            {
                name="cigarra_ambient_noronha";
                sound[]={"Noronha\sounds\cigarra-sound", db(5), 1.0};
                frequency=0.4;
                volume="(1 - night) * (1 - rain) * trees"; 
                range=100;
            };
        };
  
        centerPosition[]={5120, 100, 5120};
        seagullPos[]={5120, 150, 5120};
 
        // ---------------------------------------------------------
        // AEROPORTO
        // ---------------------------------------------------------
        ilsPosition[]={5845.81, 5907.83};
        ilsDirection[]={0.707, 0, -0.707};
        ilsTaxiOff[]={5700.0,5820.0, 5730.0,5850.0, 5780.0,5880.0, 5820.0,5907.83, 5845.81,5907.83};
        ilsTaxiIn[]={5845.81,5907.83, 5870.0,5930.0, 5895.0,5960.0, 5910.0,5990.0};
        drawTaxiway=1;
        class SecondaryAirports {};
 
        // ---------------------------------------------------------
        // TEXTURAS E ACUSTICA
        // ---------------------------------------------------------
        midDetailTexture="DZ\worlds\enoch\data\enoch_middle_mco.paa";
		terrainNormalTexture="DZ\worlds\enoch\data\enoch_global_nohq.paa";
 
        soundMapAttenCoef=0.003;
 
        class SoundMapValues
        {
            treehard=0.03; treesoft=0.03;
            bushhard=0.01; bushsoft=0.01;
            forest=1; house=0.3; church=0.5;
        };
 
        // ---------------------------------------------------------
        // CLUTTER
        // ---------------------------------------------------------
        clutterGrid=1;
        clutterDist=125;
        noDetailDist=75;
        fullDetailDist=15;

        minTreesInForestSquare=10;
        minRocksInRockSquare=6;

        class ReplaceObjects {};
        class AISpawnerParams {};

        // ---------------------------------------------------------
        // MATERIAIS DE TERRENO
        // ---------------------------------------------------------
        class UsedTerrainMaterials
		{
			material0="DZ\surfaces_bliss\data\terrain\en_deforested.rvmat";
			material1="DZ\surfaces_bliss\data\terrain\en_flowers1.rvmat";
			material2="DZ\surfaces_bliss\data\terrain\en_flowers2.rvmat";
			material3="DZ\surfaces_bliss\data\terrain\en_flowers3.rvmat";
			material4="DZ\surfaces_bliss\data\terrain\en_forest_con.rvmat";
			material5="DZ\surfaces_bliss\data\terrain\en_forest_dec.rvmat";
			material6="DZ\surfaces_bliss\data\terrain\en_grass1.rvmat";
			material7="DZ\surfaces_bliss\data\terrain\en_grass2.rvmat";
			material8="DZ\surfaces_bliss\data\terrain\en_soil.rvmat";
			material9="DZ\surfaces_bliss\data\terrain\en_stones.rvmat";
			material10="DZ\surfaces_bliss\data\terrain\en_stubble.rvmat";
			material11="DZ\surfaces_bliss\data\terrain\en_tarmac_old.rvmat";
            material12 ="DZ\surfaces\data\terrain\cp_concrete2.rvmat";
		};

        // ---------------------------------------------------------
        // SUBDIVISAO DO TERRENO
        // ---------------------------------------------------------
        class Subdivision
        {
            class Fractal    { rougness=5; maxRoad=0.02;        maxTrack=0.5;        maxSlopeFactor=0.050000001; };
            class WhiteNoise { rougness=2; maxRoad=0.0099999998; maxTrack=0.050000001; maxSlopeFactor=0.0024999999; };
            minY=0; minSlope=0.02;
        };

        // ---------------------------------------------------------
        // VIDA AMBIENTE
        // ---------------------------------------------------------
        class Ambient: Ambient
        {
            class BigInsects
            {
                radius=20;
                cost="(5 - (2 * houses)) * (1 - night) * (1 - rain) * (1 - sea) * (1 - windy)";
                class Species
                {
                    class FxButterflyBrown { probability="0.4 * (1 - hills)"; cost=1; };
                    class FxButterflyWhite { probability="0.3 * trees";       cost=1; };
                    class FxBee            { probability="0.3 * (1 - sea)";   cost=1; };
                };
            };
            class BigInsectsAquatic
            {
                radius=20;
                cost="(3 * sea) * (1 - night) * (1 - rain) * (1 - windy)";
                class Species {};
            };
            class NightInsects
            {
                radius=3;
                cost="9 * night * (1 - rain) * (1 - sea)";
                class Species
                {
                    class FxCrickets1 { probability="0.7 * (1 - sea)"; cost=1; };
                    class FxCrickets2 { probability="0.3 * trees";     cost=1; };
                };
            };
            class WindClutter
            {
                radius=10;
                cost="((20 - 5 * rain) * (3 * (windy factor [0.2, 0.5]))) * (1 - sea)";
                class Species
                {
                    class FxWindGrass1  { probability="0.4 - 0.2 * hills - 0.2 * trees"; cost=1; };
                    class FxCrWindLeaf1 { probability="0.4 * trees";                     cost=1; };
                };
            };
            class NoWindClutter
            {
                radius=15; cost=8;
                class Species
                {
                    class FxWindPollen1 { probability=1; cost=1; };
                };
            };
        };

        // ---------------------------------------------------------
        // CIDADES E PONTOS DE INTERESSE
        // ---------------------------------------------------------
        class Names
        {
            // Vilas
            class Vila_Remedios       { name="Vila dos Remedios";   position[]={7777.94,7489.46}; type="Capital";       radiusA=400.00; radiusB=400.00; angle=0; };
            class Vila_Trinta         { name="Vila do Trinta";      position[]={8187.84,6967.93}; type="City";          radiusA=239.04; radiusB=183.94; angle=0; };
            class Vila_Floresta_Velha { name="Vila Floresta Velha"; position[]={7513.63,7091.27}; type="Village";       radiusA=298.79; radiusB=229.92; angle=0; };
            class Vila_Floresta_Nova  { name="Vila Floresta Nova";  position[]={7669.26,6824.57}; type="Village";       radiusA=298.79; radiusB=229.92; angle=0; };
            class Vila_Mulungu        { name="Vila do Mulungu";     position[]={5302.92,6437.34}; type="Village";       radiusA=239.04; radiusB=180.00; angle=0; };
            class Vila_Coria          { name="Vila da Coria";       position[]={5317.95,5830.23}; type="Village";       radiusA=239.04; radiusB=183.94; angle=0; };
            class Vila_Conceicao      { name="Vila Da Conceicao";   position[]={7149.84,7420.70}; type="Village";       radiusA=152.98; radiusB=117.72; angle=0; };
            class Vila_Tres_Paus      { name="Vila dos Tres Paus";  position[]={6386.13,6254.65}; type="Village";       radiusA=191.23; radiusB=147.15; angle=0; };
            class Vila_Quixaba        { name="Vila da Quixaba";     position[]={4615.87,5886.62}; type="Village";       radiusA=191.23; radiusB=147.15; angle=0; };
            class Vila_Boldro         { name="Vila do Boldro";      position[]={6107.69,6661.86}; type="Village";       radiusA=280.00; radiusB=220.00; angle=0; };
            // Infraestrutura
            class Aeroporto           { name="Aeroporto de Noronha"; position[]={5845.81,5907.83}; type="IndustrialSite"; radiusA=239.04; radiusB=183.94; angle=0; };
            class Vila_Militar_FAB    { name="Vila Militar da FAB";  position[]={5934.72,5496.17}; type="LocalOffice";    radiusA=298.79; radiusB=229.92; angle=0; };
            class Radar_Aeronautica   { name="Radar da Aeronautica"; position[]={8867.31,6830.66}; type="Local";          radiusA=122.39; radiusB=94.18;  angle=0; };
            class Forte_Noronha       { name="Forte Noronha";        position[]={7883.44,7882.86}; type="Ruin";           radiusA=78.33;  radiusB=60.27;  angle=0; };
            class Porto               { name="Vila do Porto";         position[]={9021.95,8296.21}; type="Marine";         radiusA=152.98; radiusB=117.72; angle=0; };
            class Hospital_Noronha    { name="Hospital Sao Lucas";   position[]={7600.00,7300.00}; type="LocalOffice";    radiusA=60.00;  radiusB=60.00;  angle=0; };
            class Centro_Visitantes   { name="Centro de Visitantes"; position[]={7200.00,7100.00}; type="LocalOffice";    radiusA=50.00;  radiusB=50.00;  angle=0; };
            // Praias
            class Praia_Cacimba       { name="Praia da Cacimba";    position[]={4662.59,6550.35}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
            class Praia_Boldro        { name="Praia do Boldro";     position[]={6016.48,7142.68}; type="Local"; radiusA=97.91;  radiusB=75.34;  angle=0; };
            class Praia_Atalaia       { name="Praia da Atalaia";    position[]={8016.25,5854.31}; type="Local"; radiusA=152.98; radiusB=117.72; angle=0; };
            class Praia_Sueste        { name="Praia do Sueste";     position[]={6289.14,4827.86}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
            class Praia_Leao          { name="Praia do Leao";       position[]={4818.69,4339.22}; type="Local"; radiusA=191.23; radiusB=147.15; angle=0; };
            class Praia_Sancho        { name="Praia do Sancho";     position[]={4159.94,6053.32}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
            class Praia_Americano     { name="Praia do Americano";  position[]={5380.93,6899.57}; type="Local"; radiusA=62.66;  radiusB=48.22;  angle=0; };
            class Praia_Bode          { name="Praia do Bode";       position[]={5164.33,6769.49}; type="Local"; radiusA=78.33;  radiusB=60.27;  angle=0; };
            class Praia_Conceicao     { name="Praia da Conceicao";  position[]={7400.00,7650.00}; type="Local"; radiusA=150.00; radiusB=120.00; angle=0; };
            class Praia_Cachorro      { name="Praia do Cachorro";   position[]={7777.17,7762.52}; type="Local"; radiusA=100.00; radiusB=100.00; angle=0; };
            // Natureza
            class Acude_Xareu         { name="Acude do Xareu";          position[]={5701.93,4869.10}; type="Local";  radiusA=132.69; radiusB=102.11; angle=0; };
            class Piscina_Natural      { name="Piscina Natural";         position[]={8150.00,5720.00}; type="Local";  radiusA=60.00;  radiusB=60.00;  angle=0; };
            class Enseada_Boto         { name="Enseada dos Golfinhos";   position[]={6720.00,7450.00}; type="Marine"; radiusA=180.00; radiusB=150.00; angle=0; };
            class Baia_Porcos          { name="Baia dos Porcos";         position[]={4405.46,6405.85}; type="Marine"; radiusA=100.00; radiusB=100.00; angle=0; };
            class Cemiterio_Quixaba    { name="Cemiterio da Quixaba";    position[]={4700.00,5800.00}; type="Ruin";   radiusA=40.00;  radiusB=40.00;  angle=0; };
            // Morros
            class Rocha_Nega           { name="Morro do Pico";      position[]={6594.60,7163.40}; type="RockArea"; radiusA=160.00; radiusB=130.00; angle=360; };
            class Morro_Dois_Irmaos    { name="Morro Dois Irmaos";  position[]={4416.23,6661.29}; type="RockArea"; radiusA=100.00; radiusB=100.00; angle=0;   };
            // Mirantes
            class Mirante_Forte_Boldro { name="Mirante Forte Boldro"; position[]={5535.67,6924.67}; type="ViewPoint"; radiusA=62.66;  radiusB=48.22;  angle=0; };
            class Ponta_Air_France     { name="Ponta da Air France";  position[]={9157.75,8674.32}; type="ViewPoint"; radiusA=152.98; radiusB=117.72; angle=0; };
            class Pontinha             { name="Pontinha";              position[]={9684.66,6438.10}; type="ViewPoint"; radiusA=239.04; radiusB=183.94; angle=0; };
            class Ponta_Sapata         { name="Ponta da Sapata";      position[]={983.61, 3734.55}; type="ViewPoint"; radiusA=239.04; radiusB=183.94; angle=0; };
            class Buraco_Raquel        { name="Buraco da Raquel";     position[]={9229.12,8436.44}; type="ViewPoint"; radiusA=80.00;  radiusB=80.00;  angle=0; };
            // Cultura
            class Capela_Sao_Pedro    { name="Capela de Sao Pedro"; position[]={9132.22,8389.56}; type="Local"; radiusA=50.00; radiusB=50.00; angle=0; };
            class Museu_Tubarao       { name="Museu do Tubarao";    position[]={9114.88,8247.74}; type="Local"; radiusA=50.00; radiusB=50.00; angle=0; };
            // Ilhas secundarias
            class Ilha_Meio           { name="Ilha do Meio";      position[]={9771.58,9924.72}; type="Local"; radiusA=239.04; radiusB=183.94; angle=0; };
            class Ilha_Sela_Gineta    { name="Ilha Sela Gineta";  position[]={9702.95,9394.66}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
            class Ilha_Rasa           { name="Ilha Rasa";         position[]={9368.55,9039.43}; type="Local"; radiusA=97.91;  radiusB=75.34;  angle=0; };
            class Ilha_Sao_Jose       { name="Ilha Sao Jose";     position[]={8844.17,9119.80}; type="Local"; radiusA=78.33;  radiusB=60.27;  angle=0; };
        };
    };
};

// =============================================================
// LISTA DE MUNDOS
// =============================================================
class CfgWorldList
{
    class Noronha {};
};

// =============================================================
// MISSOES
// =============================================================
class CfgMissions
{
    class Cutscenes
    {
        class NoronhaIntro
        {
            directory="Noronha\data\scenes\intro.Noronha";
        };
    };
};