class CfgPatches
{
	class NW_Loading
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
	class NW_Loading
	{
		dir="nw/loading";
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
				files[]={"nw/loading/data/noronha_loading.imageset"};
			};
			class gameScriptModule
			{
				value="";
				files[]=
				{
					"nw/loading/scripts/3_game"
				};
			};
			class missionScriptModule
			{
				value="";
				files[]=
				{
					"nw/loading/scripts/5_mission"
				};
			};
		};
	};
};
