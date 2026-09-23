class NoronhaLoadingScreenHelper
{
	static const string BACKGROUND_IMAGE = "set:noronha_loading image:loading1";
	static const string VANILLA_REVEAL_MASK = "{F2CEA7E35B785FB7}Gui/textures/loading_screens/loading_screen_3_mask.edds";
	static const string HINTS_PATH = "Noronha/loading/data/hints.json";
	static const string LOADING_LOGO_LAYOUT = "Noronha/loading/gui/layouts/noronha_loading_logo.layout";
	static const string MAIN_MENU_LOGO_LAYOUT = "Noronha/loading/gui/layouts/noronha_main_menu_logo.layout";

	static void ApplyBackground(Widget root, string backgroundWidgetName, bool preserveReveal)
	{
		if (!root)
			return;

		ImageWidget bg;
		if (!Class.CastTo(bg, root.FindAnyWidget(backgroundWidgetName)))
			return;

		if (!bg.LoadImageFile(0, BACKGROUND_IMAGE))
			return;

		if (preserveReveal)
		{
			// Reapply the native loading.layout mask after replacing its image source.
			bg.LoadMaskTexture(VANILLA_REVEAL_MASK);
			bg.SetMaskTransitionWidth(1.0);
			bg.SetMaskProgress(0.0);
		}
	}

	static Widget CreateLogo(WorkspaceWidget workspace, Widget parent, string layoutPath)
	{
		if (!workspace || !parent)
			return null;

		return workspace.CreateWidgets(layoutPath, parent);
	}

}

modded class UiHintPanelLoading
{
	override protected void LoadContentList()
	{
		string errorMessage;
		if (!JsonFileLoader<array<ref HintPage>>.LoadFile(NoronhaLoadingScreenHelper.HINTS_PATH, m_ContentList, errorMessage))
		{
			ErrorEx(errorMessage);
			super.LoadContentList();
		}
	}
}

modded class LoadingScreen
{
	protected Widget m_NoronhaLoadingLogoRoot;

	override void Show()
	{
		super.Show();

		NoronhaLoadingScreenHelper.ApplyBackground(m_WidgetRoot, "ImageBackground", true);

		if (!m_NoronhaLoadingLogoRoot)
			m_NoronhaLoadingLogoRoot = NoronhaLoadingScreenHelper.CreateLogo(m_DayZGame.GetLoadingWorkspace(), m_WidgetRoot, NoronhaLoadingScreenHelper.LOADING_LOGO_LAYOUT);

		ProgressAsync.SetProgressData(m_ProgressLoading);
		ProgressAsync.SetUserData(m_ImageBackground);
	}
}

modded class LoginQueueBase
{
	override void Show()
	{
		super.Show();
		NoronhaLoadingScreenHelper.ApplyBackground(layoutRoot, "Background", false);
	}
}

modded class LoginTimeBase
{
	override void Show()
	{
		super.Show();
		NoronhaLoadingScreenHelper.ApplyBackground(layoutRoot, "Background", false);
	}
}
