class CfgPatches
{
	class Noronha
	{
		units[]={};
		weapons[]={};
		worlds[]=
		{
			"Noronha"
		};
		requiredVersion=0.1;
		requiredAddons[]=
		{
			"DZ_Data",
			"DZ_Surfaces",
			"DZ_Surfaces_Bliss",
			"DZ_Rocks",
			"DZ_Water",
			"DZ_Gear_Navigation",
			"DZ_Structures_Bliss_Signs",
			"DZ_Worlds_Chernarusplus_World",
			"DZ_Worlds_Enoch_Data",
			"DZ_Sounds_Environment",
			"Noronha_Sounds"
		};
		author="AdriianCOE";
		name="Noronha";
		url="https://steamcommunity.com/sharedfiles/filedetails/?id=3682451894";
	};
};
class CfgCharacterScenes
{
	class Noronha
	{
		class loc1
		{
			target[]={5815.05,5825,54.29};
			position[]={5815.05,5809.21,54.29};
			fov=0.52359998;
			date[]={2026,2,23,12,0};
			overcast=0.050000001;
			rain=0;
			fog=0;
		};
	};
};
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
				class Weather1;
				class Weather2;
				class Weather3;
				class Weather4;
				class Weather5;
				class Weather6;
				class Weather7;
				class Weather8;
				class Weather9;
				class Weather10;
				class Weather11;
				class Weather12;
			};
		};
	};
	class Noronha: CAWorld
	{
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
		latitude=3.84;
		longitude=-32.419998;
		mapDisplayNameKey="Guia de Noronha";
		mapDescriptionKey="Um guia turistico antigo da ilha. Praias, trilhas e mirantes ainda estao marcados, mas muita coisa mudou desde que foi impresso.";
		mapTextureClosed="dz\gear\navigation\data\map_enoch_co.paa";
		mapTextureOpened="dz\structures_bliss\signs\tourist\data\karta_enoch_co.paa";
		mapTextureLegend="dz\structures_bliss\signs\tourist\data\karta_enoch_side_co.paa";
		userMapPath="";
		oceanMaterial="dz\water\data\ocean_samplemap.emat";
		oceanNiceMaterial="dz\water\data\ocean_nice_samplemap.emat";
		oceanStormMaterial="dz\water\data\ocean_storm_samplemap.emat";
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
		class Navmesh
		{
			#include "navmesh.hpp"
		};
		class Grid: Grid
		{
			offsetX=0;
			offsetY=10240;
			class Zoom1
			{
				zoomMax=0.15000001;
				format="XY";
				formatX="000";
				formatY="000";
				stepX=100;
				stepY=-100;
			};
			class Zoom2
			{
				zoomMax=0.85000002;
				format="XY";
				formatX="00";
				formatY="00";
				stepX=1000;
				stepY=-1000;
			};
			class Zoom3
			{
				zoomMax=1e+30;
				format="XY";
				formatX="0";
				formatY="0";
				stepX=10000;
				stepY=-10000;
			};
		};
		startTime="13:00";
		startDate="23/02/2026";
		class Lighting: DefaultLighting
		{
			class Lighting0
			{
				height=1;
				ambient[]={0.64999998,0.68000001,0.64999998,1};
				diffuse[]={2.2,2.05,1.85,1};
				diffuseCloud[]={1.05,1,0.94999999,1};
			};
			class Lighting1
			{
				height=0.15000001;
				ambient[]={0.55000001,0.55000001,0.51999998,1};
				diffuse[]={1.9,1.75,1.5,1};
				diffuseCloud[]={0.94999999,0.85000002,0.75,1};
			};
			class Lighting15
			{
				height=0.050000001;
				ambient[]={0.2,0.22,0.25,1};
				diffuse[]={1.2,0.80000001,0.5,1};
				diffuseCloud[]={0.60000002,0.40000001,0.30000001,1};
			};
			class Lighting2
			{
				height=0;
				ambient[]={0.1,0.1,0.15000001,1};
				diffuse[]={0.80000001,0.40000001,0.2,1};
				diffuseCloud[]={0.5,0.2,0.1,1};
			};
			class Lighting25
			{
				height=-0.050000001;
				ambient[]={0.050000001,0.050000001,0.079999998,1};
				diffuse[]={0.2,0.1,0.25,1};
				diffuseCloud[]={0.1,0.050000001,0.15000001,1};
			};
			class Lighting3
			{
				height=-0.2;
				ambient[]={0.02,0.02,0.039999999,1};
				diffuse[]={0.079999998,0.090000004,0.15000001,1};
				diffuseCloud[]={0.039999999,0.039999999,0.059999999,1};
			};
		};
		#include "weather.hpp"
		volFogOffset=0;
		maxDynLights=64;
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
		class Sounds: Sounds
		{
			sounds[]={};
			class OceanWaves
			{
				name="ocean_waves_noronha";
				sound[]=
				{
					"dz\sounds\environment\ambients\coast",
					1,
					1
				};
				frequency=1;
				volume="sea";
				range=300;
			};
			class SeaBirds
			{
				name="seagulls_ambient_noronha";
				sound[]=
				{
					"Noronha\sounds\birds_seagull",
					1,
					1
				};
				frequency=0.2;
				volume="(1 - night) * (1 - rain) * sea";
				range=200;
			};
			class TropicalBirds
			{
				name="bemtevi_ambient_noronha";
				sound[]=
				{
					"Noronha\sounds\birds-bemtevi",
					1,
					1
				};
				frequency=0.15000001;
				volume="(1 - night) * (1 - rain) * trees";
				range=150;
			};
			class GralhasBirds
			{
				name="gralhas_ambient_noronha";
				sound[]=
				{
					"Noronha\sounds\birds-gralhas",
					1,
					1
				};
				frequency=0.1;
				volume="(1 - night) * (1 - rain) * trees";
				range=150;
			};
			class Cicadas
			{
				name="cigarra_ambient_noronha";
				sound[]=
				{
					"Noronha\sounds\cigarra-sound",
					1,
					1
				};
				frequency=0.40000001;
				volume="(1 - night) * (1 - rain) * trees";
				range=100;
			};
		};
		centerPosition[]={5120,5120,100};
		seagullPos[]={5120,5120,150};
		ilsPosition[]={5845.8101,5907.8301};
		ilsDirection[]={0.70700002,0,-0.70700002};
		ilsTaxiOff[]={5700,5820,5730,5850,5780,5880,5820,5907.8301,5845.8101,5907.8301};
		ilsTaxiIn[]={5845.8101,5907.8301,5870,5930,5895,5960,5910,5990};
		drawTaxiway=1;
		class SecondaryAirports
		{
		};
		midDetailTexture="DZ\worlds\enoch\data\enoch_middle_mco.paa";
		terrainNormalTexture="DZ\worlds\enoch\data\enoch_global_nohq.paa";
		soundMapAttenCoef=0.003;
		class SoundMapValues
		{
			treehard=0.029999999;
			treesoft=0.029999999;
			bushhard=0.0099999998;
			bushsoft=0.0099999998;
			forest=1;
			house=0.30000001;
			church=0.5;
		};
		clutterGrid=1;
		clutterDist=125;
		noDetailDist=75;
		fullDetailDist=15;
		minTreesInForestSquare=10;
		minRocksInRockSquare=6;
		class ReplaceObjects
		{
		};
		class AISpawnerParams
		{
		};
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
			material12="DZ\surfaces\data\terrain\cp_concrete2.rvmat";
		};
		class Subdivision
		{
			class Fractal
			{
				rougness=5;
				maxRoad=0.02;
				maxTrack=0.5;
				maxSlopeFactor=0.050000001;
			};
			class WhiteNoise
			{
				rougness=2;
				maxRoad=0.0099999998;
				maxTrack=0.050000001;
				maxSlopeFactor=0.0024999999;
			};
			minY=0;
			minSlope=0.02;
		};
		class Ambient: Ambient
		{
			class BigInsects
			{
				radius=20;
				cost="(5 - (2 * houses)) * (1 - night) * (1 - rain) * (1 - sea) * (1 - windy)";
				class Species
				{
					class FxButterflyBrown
					{
						probability="0.4 * (1 - hills)";
						cost=1;
					};
					class FxButterflyWhite
					{
						probability="0.3 * trees";
						cost=1;
					};
					class FxBee
					{
						probability="0.3 * (1 - sea)";
						cost=1;
					};
				};
			};
			class BigInsectsAquatic
			{
				radius=20;
				cost="(3 * sea) * (1 - night) * (1 - rain) * (1 - windy)";
				class Species
				{
				};
			};
			class NightInsects
			{
				radius=3;
				cost="9 * night * (1 - rain) * (1 - sea)";
				class Species
				{
					class FxCrickets1
					{
						probability="0.7 * (1 - sea)";
						cost=1;
					};
					class FxCrickets2
					{
						probability="0.3 * trees";
						cost=1;
					};
				};
			};
			class WindClutter
			{
				radius=10;
				cost="((20 - 5 * rain) * (3 * (windy factor [0.2, 0.5]))) * (1 - sea)";
				class Species
				{
					class FxWindGrass1
					{
						probability="0.4 - 0.2 * hills - 0.2 * trees";
						cost=1;
					};
					class FxCrWindLeaf1
					{
						probability="0.4 * trees";
						cost=1;
					};
				};
			};
			class NoWindClutter
			{
				radius=15;
				cost="8 * (1 - rain) * (1 - sea)";
				class Species
				{
					class FxWindPollen1
					{
						probability=1;
						cost=1;
					};
				};
			};
		};
		class Names
		{
			class Vila_Remedios
			{
				name="Vila dos Remedios";
				position[]={7798.26,7476.31};
				type="Capital";
				radiusA=500;
				radiusB=450;
				angle=0;
			};
			class Vila_Trinta
			{
				name="Vila do Trinta";
				position[]={8317.81,6973.91};
				type="City";
				radiusA=400;
				radiusB=350;
				angle=0;
			};
			class Vila_Floresta_Velha
			{
				name="Floresta Velha";
				position[]={7575.78,7080.51};
				type="Village";
				radiusA=400;
				radiusB=300;
				angle=0;
			};
			class Vila_Floresta_Nova
			{
				name="Floresta Nova";
				position[]={7669.26,6750.47};
				type="Village";
				radiusA=350;
				radiusB=300;
				angle=0;
			};
			class Vila_Mulungu
			{
				name="Mulungu";
				position[]={5332.29,6403.56};
				type="Village";
				radiusA=239.03999;
				radiusB=180;
				angle=0;
			};
			class Vila_Coria
			{
				name="Coria";
				position[]={5373.40,5851.26};
				type="Village";
				radiusA=240;
				radiusB=200;
				angle=0;
			};
			class Vila_Conceicao
			{
				name="Vila da Conceicao";
				position[]={7149.8398,7420.7002};
				type="Village";
				radiusA=152.98;
				radiusB=117.72;
				angle=0;
			};
			class Vila_Tres_Paus
			{
				name="Tres Paus";
				position[]={6386.1299,6254.6499};
				type="Village";
				radiusA=191.23;
				radiusB=147.14999;
				angle=0;
			};
			class Vila_Quixaba
			{
				name="Quixaba";
				position[]={4624.24,5900.96};
				type="Village";
				radiusA=230;
				radiusB=200;
				angle=0;
			};
			class Vila_Boldro
			{
				name="Vila do Boldro";
				position[]={6107.6899,6661.8599};
				type="Village";
				radiusA=280;
				radiusB=220;
				angle=0;
			};
			class Aeroporto
			{
				name="Aeroporto de Noronha";
				position[]={5841.99,5868.06};
				type="IndustrialSite";
				radiusA=300;
				radiusB=240;
				angle=0;
			};
			class Vila_Militar_FAB
			{
				name="Base Aerea";
				position[]={5969.60,5488.22};
				type="StrongpointArea";
				radiusA=350;
				radiusB=300;
				angle=0;
			};
			class Radar_Aeronautica
			{
				name="Radar da Aeronautica";
				position[]={8854.31,6826.84};
				type="StrongpointArea";
				radiusA=300;
				radiusB=250;
				angle=0;
			};
			class Forte_Noronha
			{
				name="Forte dos Remedios";
				position[]={7883.4399,7882.8599};
				type="StrongpointArea";
				radiusA=78.330002;
				radiusB=60.27;
				angle=0;
			};
			class Porto
			{
				name="Porto de Santo Antonio";
				position[]={8912.96,8249.36};
				type="Marine";
				radiusA=300;
				radiusB=250;
				angle=0;
			};
			class Hospital_Noronha
			{
				name="Hospital";
				position[]={7600,7300};
				type="LocalOffice";
				radiusA=60;
				radiusB=60;
				angle=0;
			};
			class Centro_Visitantes
			{
				name="Visitantes";
				position[]={7200,7100};
				type="LocalOffice";
				radiusA=50;
				radiusB=50;
				angle=0;
			};
			class Praia_Cacimba
			{
				name="Praia da Cacimba";
				position[]={4686.45,6513.02};
				type="Local";
				radiusA=150;
				radiusB=150;
				angle=0;
			};
			class Praia_Boldro
			{
				name="Praia do Boldro";
				position[]={6016.48,7142.6802};
				type="Local";
				radiusA=97.910004;
				radiusB=75.339996;
				angle=0;
			};
			class Praia_Atalaia
			{
				name="Praia da Atalaia";
				position[]={8016.25,5854.3101};
				type="Local";
				radiusA=152.98;
				radiusB=117.72;
				angle=0;
			};
			class Praia_Sueste
			{
				name="Baia do Sueste";
				position[]={6289.1401,4827.8599};
				type="Local";
				radiusA=122.39;
				radiusB=94.18;
				angle=0;
			};
			class Praia_Leao
			{
				name="Praia do Leao";
				position[]={4903.13,4431.01};
				type="Local";
				radiusA=191.23;
				radiusB=147.14999;
				angle=0;
			};
			class Praia_Sancho
			{
				name="Baia do Sancho";
				position[]={4159.9399,6053.3198};
				type="Local";
				radiusA=122.39;
				radiusB=94.18;
				angle=0;
			};
			class Praia_Americano
			{
				name="Praia do Americano";
				position[]={5380.9302,6899.5698};
				type="Local";
				radiusA=80;
				radiusB=60;
				angle=0;
			};
			class Praia_Bode
			{
				name="Praia do Bode";
				position[]={5141.69,6772.55};
				type="Local";
				radiusA=80;
				radiusB=60.27;
				angle=0;
			};
			class Praia_Conceicao
			{
				name="Praia da Conceicao";
				position[]={7400,7650};
				type="Local";
				radiusA=150;
				radiusB=120;
				angle=0;
			};
			class Praia_Cachorro
			{
				name="Praia do Cachorro";
				position[]={7777.1699,7762.52};
				type="Local";
				radiusA=100;
				radiusB=100;
				angle=0;
			};
			class Acude_Xareu
			{
				name="Acude do Xareu";
				position[]={5701.9302,4869.1001};
				type="Local";
				radiusA=132.69;
				radiusB=102.11;
				angle=0;
			};
			class Piscina_Natural
			{
				name="Piscina Natural";
				position[]={8150,5720};
				type="Local";
				radiusA=60;
				radiusB=60;
				angle=0;
			};
			class Enseada_Boto
			{
				name="Baia dos Golfinhos";
				position[]={6720,7450};
				type="Marine";
				radiusA=180;
				radiusB=150;
				angle=0;
			};
			class Baia_Porcos
			{
				name="Baia dos Porcos";
				position[]={4405.46,6405.8501};
				type="Marine";
				radiusA=100;
				radiusB=100;
				angle=0;
			};
			class Cemiterio_Quixaba
			{
				name="Cemiterio da Quixaba";
				position[]={4700,5800};
				type="Ruin";
				radiusA=40;
				radiusB=40;
				angle=0;
			};
			class Rocha_Nega
			{
				name="Pico da Rocha Nega";
				position[]={6594.6001,7163.3999};
				type="RockArea";
				radiusA=160;
				radiusB=130;
				angle=0;
			};
			class Morro_Dois_Irmaos
			{
				name="Morro Dois Irmaos";
				position[]={4416.23,6661.29};
				type="RockArea";
				radiusA=100;
				radiusB=100;
				angle=0;
			};
			class Mirante_Forte_Boldro
			{
				name="Mirante do Forte Boldro";
				position[]={5534.50,6918.80};
				type="ViewPoint";
				radiusA=100;
				radiusB=100;
				angle=0;
			};
			class Ponta_Air_France
			{
				name="Air France";
				position[]={9157.75,8674.3203};
				type="ViewPoint";
				radiusA=152.98;
				radiusB=117.72;
				angle=0;
			};
			class Pontinha
			{
				name="Pontinha";
				position[]={9684.6602,6438.1001};
				type="ViewPoint";
				radiusA=239.03999;
				radiusB=183.94;
				angle=0;
			};
			class Ponta_Sapata
			{
				name="Ponta da Sapata";
				position[]={983.60999,3734.55};
				type="ViewPoint";
				radiusA=239.03999;
				radiusB=183.94;
				angle=0;
			};
			class Buraco_Raquel
			{
				name="Buraco da Raquel";
				position[]={9229.1201,8436.4404};
				type="ViewPoint";
				radiusA=80;
				radiusB=80;
				angle=0;
			};
			class Capela_Sao_Pedro
			{
				name="Sao Pedro";
				position[]={9132.2197,8389.5596};
				type="Local";
				radiusA=50;
				radiusB=50;
				angle=0;
			};
			class Museu_Tubarao
			{
				name="Museu do Tubarao";
				position[]={9114.8799,8247.7402};
				type="Local";
				radiusA=50;
				radiusB=50;
				angle=0;
			};
			class Ilha_Meio
			{
				name="Ilha do Meio";
				position[]={9771.5801,9924.7197};
				type="Local";
				radiusA=239.03999;
				radiusB=183.94;
				angle=0;
			};
			class Ilha_Sela_Gineta
			{
				name="Sela Gineta";
				position[]={9702.9502,9394.6602};
				type="Local";
				radiusA=122.39;
				radiusB=94.18;
				angle=0;
			};
			class Ilha_Rasa
			{
				name="Ilha Rasa";
				position[]={9368.5498,9039.4297};
				type="Local";
				radiusA=97.910004;
				radiusB=75.339996;
				angle=0;
			};
			class Ilha_Sao_Jose
			{
				name="Ilha Sao Jose";
				position[]={8844.1699,9119.7998};
				type="Local";
				radiusA=78.330002;
				radiusB=60.27;
				angle=0;
			};
			class Porto_Secreto
			{
				name="Porto Secreto";
				position[]={3784.33,3944.64};
				type="Marine";
				radiusA=400;
				radiusB=300;
				angle=360;
			};
			class Base_Secreta
			{
				name="Base Secreta";
				position[]={3778.27,4501.00};
				type="StrongpointArea";
				radiusA=370.19;
				radiusB=230;
				angle=0;
			};
			class Usina_Eolica
			{
				name="Usina Eolica";
				position[]={2064.39,3764.77};
				type="RockArea";
				radiusA=259;
				radiusB=180;
				angle=0;
			};
			class Estacao_TV
			{
				name="Estacao de TV";
				position[]={3649.16,4917.22};
				type="Local";
				radiusA=200;
				radiusB=180;
				angle=0;
			};
			class Mansao
			{
				name="Mansao";
				position[]={8397.25,7509.87};
				type="Local";
				radiusA=200;
				radiusB=150;
				angle=0;
			};
			class Acampamentos_Praia
			{
				name="Acampamentos da Praia";
				position[]={5886.60,5069.33};
				type="Village";
				radiusA=250;
				radiusB=200;
				angle=0;
			};
			class Fazedinha_Interior
			{
				name="Fazenda de Adra";
				position[]={4466.32,5202.36};
				type="Village";
				radiusA=189.54;
				radiusB=118.71;
				angle=0;
			};
			class Ultima_Fazenda
			{
				name="Ultima Fazenda";
				position[]={2556.72,3835.08};
				type="Local";
				radiusA=200;
				radiusB=150;
				angle=0;
			};
			class Vila_Aeroporto
			{
				name="Vila do Aeroporto";
				position[]={6321.96,5723.61};
				type="Village";
				radiusA=300;
				radiusB=200;
				angle=0;
			};
			class Vila_Menor_Boldro
			{
				name="Vila Menor do Boldro";
				position[]={5522.03,6694.83};
				type="Village";
				radiusA=151.63;
				radiusB=94.97;
				angle=0;
			};
		};
	};
};
class CfgWorldList
{
	class Noronha
	{
	};
};
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
