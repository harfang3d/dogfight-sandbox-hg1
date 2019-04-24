# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Basic scene -


# ===========================================================

import harfang as hg
import platform
from math import radians


def init_scene(plus):
	scene = plus.NewScene()
	plus.LoadScene(scene, "assets/scenes/main_scene.scn")

	scene.UpdateAndCommitWaitAll()

	# Ground:

	cam = scene.GetNode("Camera")
	pos=cam.GetTransform().GetPosition()
	fps = hg.FPSController(pos.x, pos.y, pos.z)


	return scene, fps


def init_lights(plus, scene):
	# Main light:
	ligth_sun = plus.AddLight(scene, hg.Matrix4.TransformationMatrix(hg.Vector3(3,9,0),hg.Vector3(radians(75), radians(-45), 0)),
							  hg.LightModelLinear)
	ligth_sun.SetName("Sun")
	ligth_sun.GetLight().SetDiffuseColor(hg.Color(255. / 255., 155. / 255., 155. / 255., 1.))

	ligth_sun.GetLight().SetShadow(hg.LightShadowMap)
	ligth_sun.GetLight().SetShadowRange(50)

	ligth_sun.GetLight().SetDiffuseIntensity(1.)
	ligth_sun.GetLight().SetSpecularIntensity(1.)

	#render_script = hg.RenderScript("assets/lua_scripts/volumetric_light.lua")
	#ligth_sun.AddComponent(render_script)

	# Ambient:
	ambient_color = hg.Color(103. / 255., 157. / 255., 190. / 255., 1.)
	environment = hg.Environment()
	environment.SetAmbientColor(ambient_color)
	environment.SetAmbientIntensity(0.3)
	environment.SetFogColor(ambient_color * 0.3)
	environment.SetFogNear(1)
	environment.SetFogFar(500)
	environment.SetBackgroundColor(ambient_color )
	scene.AddComponent(environment)

# ==================================================================================================

#                                   Program start here

# ==================================================================================================

# Display settings
resolution = hg.Vector2(1600, 900)
antialiasing = 8
screenMode = hg.Windowed

# System setup
plus = hg.GetPlus()
hg.LoadPlugins()
hg.MountFileDriver(hg.StdFileDriver())

# Multi-threading mode:
plus.CreateWorkers()

# Run display
plus.RenderInit(int(resolution.x), int(resolution.y), antialiasing, screenMode)
plus.SetBlend2D(hg.BlendAlpha)

renderer=plus.GetRendererAsync()
renderer.SetVSync(True)

print (platform.system())
print (platform.version())
print (platform.release())


scene,fps=init_scene(plus)

camera = scene.GetNode("Camera")

radar = scene.GetNode("aircraft_carrier_radar")
rot = radar.GetTransform().GetRotation()
# ==================================================================================================

#                                   Program start here

# ==================================================================================================

while not plus.KeyDown(hg.KeyEscape):
	delta_t = plus.UpdateClock()
	dts = hg.time_to_sec_f(delta_t)

	fps.UpdateAndApplyToNode(camera, delta_t)

	rot.y+=0.01
	radar.GetTransform().SetRotation(rot)

	plus.UpdateScene(scene, delta_t)

	plus.Flip()
	plus.EndFrame()

plus.RenderUninit()