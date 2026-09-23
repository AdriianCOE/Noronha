modded class MainMenu
{
	protected Widget m_NoronhaMainMenuLogoRoot;

	override Widget Init()
	{
		Widget root = super.Init();
		if (!root)
			return root;

		m_NoronhaMainMenuLogoRoot = NoronhaLoadingScreenHelper.CreateLogo(g_Game.GetWorkspace(), root, NoronhaLoadingScreenHelper.MAIN_MENU_LOGO_LAYOUT);

		return root;
	}
}
