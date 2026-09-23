class CfgPatches
{
	class Noronha_Loading
	{
		units[]={};
		weapons[]={};
		requiredVersion=0.1;
		requiredAddons[]=
		{
			"DZ_Data",
			"DZ_Scripts"
		};
	};
};
class CfgMods
{
	class Noronha_Loading
	{
		dir="Noronha/loading";
		type="mod";
		dependencies[]=
		{
			"Game",
			"Mission"
		};
		class defs
		{
			class imageSets
			{
				files[]={"Noronha/loading/data/noronha_loading.imageset"};
			};
			class gameScriptModule
			{
				value="";
				files[]=
				{
					"Noronha/loading/scripts/3_game"
				};
			};
			class missionScriptModule
			{
				value="";
				files[]=
				{
					"Noronha/loading/scripts/5_mission"
				};
			};
		};
	};
};
