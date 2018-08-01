# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                   Screen mode Requester

# ===========================================================

import harfang as hg

res_w=520
res_h=160
monitors=None
monitors_names=[]
modes=None
current_monitor=0
current_mode=0

screenModes=[hg.FullscreenMonitor1,hg.FullscreenMonitor2,hg.FullscreenMonitor3]
smr_screenMode=hg.FullscreenMonitor1
smr_resolution=hg.IntVector2(1280,1024)

def gui_ScreenModeRequester():
	global current_monitor,current_mode,monitors_names,modes

	hg.ImGuiSetNextWindowPosCenter(hg.ImGuiCond_Always)
	hg.ImGuiSetNextWindowSize(hg.Vector2(res_w, res_h), hg.ImGuiCond_Always)
	if hg.ImGuiBegin("Choose screen mode",hg.ImGuiWindowFlags_NoTitleBar
										  | hg.ImGuiWindowFlags_MenuBar
										  | hg.ImGuiWindowFlags_NoMove
										  | hg.ImGuiWindowFlags_NoSavedSettings
										  | hg.ImGuiWindowFlags_NoCollapse):
		if hg.ImGuiBeginCombo("Monitor", monitors_names[current_monitor]):
			for i in range(len(monitors_names)):
				f = hg.ImGuiSelectable(monitors_names[i], current_monitor == i)
				if f:
					current_monitor = i
			hg.ImGuiEndCombo()

		if hg.ImGuiBeginCombo("Screen size", modes[current_monitor].at(current_mode).name):
			for i in range(modes[current_monitor].size()):
				f = hg.ImGuiSelectable(modes[current_monitor].at(i).name+"##"+str(i), current_mode == i)
				if f:
					current_mode = i
			hg.ImGuiEndCombo()

		ok=hg.ImGuiButton("Ok")
		hg.ImGuiSameLine()
		cancel=hg.ImGuiButton("Quit")

	hg.ImGuiEnd()

	if ok: return "ok"
	elif cancel: return "quit"
	else: return ""

def request_screen_mode():
	global monitors,monitors_names,modes,smr_screenMode,smr_resolution

	monitors = hg.GetMonitors()
	monitors_names = []
	modes = []
	for i in range(monitors.size()):
		monitors_names.append(hg.GetMonitorName(monitors.at(i)))
		f, m = hg.GetMonitorModes(monitors.at(i))
		modes.append(m)

	plus=hg.GetPlus()
	plus.RenderInit(res_w, res_h, 1, hg.Windowed)
	select=""
	while select=="":
		select=gui_ScreenModeRequester()
		plus.Flip()
		plus.EndFrame()
	plus.RenderUninit()

	if select=="ok":
		smr_screenMode=screenModes[current_monitor]
		rect=modes[current_monitor].at(current_mode).rect
		smr_resolution.x,smr_resolution.y=rect.ex-rect.sx,rect.ey-rect.sy
	return select,smr_screenMode,smr_resolution
