# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                      Sea / sky render

# ===========================================================

import harfang as hg
from math import radians
from data_converter import *
import json


class SeaRender:
	def __init__(self, plus, scene, render_script: hg.RenderScript = None):
		self.render_script = render_script
		self.sun_light = scene.GetNode("Sun")
		self.sky_light = scene.GetNode("SkyLigth")

		self.sea_scale = hg.Vector3(0.02, 3, 0.005)

		self.zenith_color = hg.Color(17. / 255., 56. / 255., 155. / 255., 1.)
		self.horizon_N_color = hg.Color(76. / 255., 128. / 255., 255 / 255., 1.)
		self.horizon_S_color = hg.Color(76. / 255., 128. / 255., 255 / 255., 1.)
		self.sea_color = hg.Color(19 / 255., 39. / 255., 89. / 255., 1.)
		self.horizon_line_color = hg.Color(1, 1, 1, 1)
		self.horizon_line_size = 40
		self.sea_reflection = 0.5
		renderer = plus.GetRenderer()

		self.sea_filtering = 0  # 1 to activate sea texture filtering
		self.render_scene_reflection = False

		self.max_filter_samples = 3
		self.filter_precision = 10

		self.shader = renderer.LoadShader("assets/shaders/sky_sea_render_optim.isl")

		self.noise_texture_1 = renderer.LoadTexture("assets/textures/noise.png")
		self.noise_texture_2 = renderer.LoadTexture("assets/textures/noise_3.png")
		self.noise_displacement_texture = renderer.LoadTexture("assets/textures/noise_2.png")
		self.stream_texture = renderer.LoadTexture("assets/textures/stream.png")
		self.clouds_map = renderer.LoadTexture("assets/textures/clouds_map.png")

		self.clouds_scale = hg.Vector3(1000., 0.1, 1000.)
		self.clouds_altitude = 1000.
		self.clouds_absorption = 0.1

		self.tex_sky_N = renderer.LoadTexture("assets/skymaps/clouds.png")
		self.tex_sky_N_intensity = 1
		self.zenith_falloff = 4

		self.reflect_map = None
		self.reflect_map_depth = None
		self.reflect_offset = 50

		self.render_sea = True

	def load_json_script(self, file_name="assets/scripts/sea_parameters.json"):
		json_script = hg.GetFilesystem().FileToString(file_name)
		if json_script != "":
			script_parameters = json.loads(json_script)
			self.horizon_N_color = list_to_color(script_parameters["horizon_N_color"])
			self.horizon_S_color = list_to_color(script_parameters["horizon_S_color"])
			self.zenith_color = list_to_color(script_parameters["zenith_color"])
			self.zenith_falloff = script_parameters["zenith_falloff"]
			self.tex_sky_N_intensity = script_parameters["tex_sky_N_intensity"]
			self.horizon_line_color = list_to_color(script_parameters["horizon_line_color"])
			self.sea_color = list_to_color(script_parameters["sea_color"])
			self.sea_scale = list_to_vec3(script_parameters["sea_scale"])
			self.sea_reflection = script_parameters["sea_reflection"]
			self.horizon_line_size = script_parameters["horizon_line_size"]
			self.sea_filtering = script_parameters["sea_filtering"]
			self.max_filter_samples = script_parameters["max_filter_samples"]
			self.filter_precision = script_parameters["filter_precision"]
			self.clouds_scale = list_to_vec3(script_parameters["clouds_scale"])
			self.clouds_altitude = script_parameters["clouds_altitude"]
			self.clouds_absorption = script_parameters["clouds_absorption"]
			self.reflect_offset = script_parameters["reflect_offset"]
			self.render_scene_reflection = script_parameters["render_scene_reflection"]

	def save_json_script(self, output_filename="assets/scripts/sea_parameters.json"):
		script_parameters = {"horizon_N_color": color_to_list(self.horizon_N_color),
			"horizon_S_color": color_to_list(self.horizon_S_color),
			"horizon_line_color": color_to_list(self.horizon_line_color),
			"zenith_color": color_to_list(self.zenith_color), "zenith_falloff": self.zenith_falloff,
			"tex_sky_N_intensity": self.tex_sky_N_intensity, "sea_color": color_to_list(self.sea_color),
			"sea_reflection": self.sea_reflection, "horizon_line_size": self.horizon_line_size,
			"sea_scale": vec3_to_list(self.sea_scale), "sea_filtering": self.sea_filtering,
			"max_filter_samples": self.max_filter_samples, "filter_precision": self.filter_precision,
			"clouds_scale": vec3_to_list(self.clouds_scale), "clouds_altitude": self.clouds_altitude,
			"clouds_absorption": self.clouds_absorption, "reflect_offset": self.reflect_offset,
			"render_scene_reflection": self.render_scene_reflection}
		json_script = json.dumps(script_parameters, indent=4)
		return hg.GetFilesystem().StringToFile(output_filename, json_script)

	def enable_render_sea(self, value):
		self.render_sea = value
		if value:
			self.render_script.Set("render_sea", 1)
		else:
			self.render_script.Set("render_sea", 0)

	def update_render_script(self, scene, resolution: hg.Vector2, time):
		if self.render_sea:
			self.render_script.Set("render_sea", 1)
		else:
			self.render_script.Set("render_sea", 0)
		self.render_script.Set("zenith_color", self.zenith_color)
		self.render_script.Set("horizon_N_color", self.horizon_N_color)
		self.render_script.Set("horizon_S_color", self.horizon_S_color)
		self.render_script.Set("zenith_falloff", self.zenith_falloff)
		self.render_script.Set("horizon_line_color", self.horizon_line_color)
		self.render_script.Set("sea_color", self.sea_color)
		l_color = self.sun_light.GetLight().GetDiffuseColor()
		self.render_script.Set("sun_color", l_color)
		amb = hg.Color(scene.GetEnvironment().GetAmbientColor()) * scene.GetEnvironment().GetAmbientIntensity()
		self.render_script.Set("ambient_color", amb)
		self.render_script.Set("horizon_line_size", self.horizon_line_size)
		self.render_script.Set("tex_sky_N_intensity", self.tex_sky_N_intensity)
		self.render_script.Set("resolution", resolution)
		self.render_script.Set("clouds_scale", self.clouds_scale)
		self.render_script.Set("clouds_altitude", self.clouds_altitude)
		self.render_script.Set("clouds_absorption", self.clouds_absorption)

		camera = scene.GetCurrentCamera()
		pos = camera.GetTransform().GetPreviousWorld().GetTranslation()
		camera = camera.GetCamera()
		self.render_script.Set("sea_reflection", self.sea_reflection)
		self.render_script.Set("sea_filtering", self.sea_filtering)
		self.render_script.Set("max_filter_samples", self.max_filter_samples)
		self.render_script.Set("filter_precision", self.filter_precision)
		l_dir = self.sun_light.GetTransform().GetWorld().GetRotationMatrix().GetZ()
		self.render_script.Set("sun_dir", l_dir)

		self.render_script.Set("sea_scale", self.sea_scale)
		self.render_script.Set("time_clock", time)
		self.render_script.Set("cam_pos", pos)
		self.render_script.Set("z_near", camera.GetZNear())
		self.render_script.Set("z_far", camera.GetZFar())
		self.render_script.Set("zoom_factor", camera.GetZoomFactor())

		self.render_script.Set("reflect_map", self.reflect_map)
		self.render_script.Set("reflect_map_depth", self.reflect_map_depth)
		self.render_script.Set("reflect_offset", self.reflect_offset)

		self.render_script.Set("tex_sky_N", self.tex_sky_N)
		self.render_script.Set("noise_texture_1", self.noise_texture_1)
		self.render_script.Set("noise_texture_2", self.noise_texture_2)
		self.render_script.Set("noise_displacement_texture", self.noise_displacement_texture)
		self.render_script.Set("stream_texture", self.stream_texture)
		self.render_script.Set("clouds_map", self.clouds_map)
		if self.render_scene_reflection:
			self.render_script.Set("scene_reflect", 1)
		else:
			self.render_script.Set("scene_reflect", 0)

	def update_shader(self, plus, scene, resolution, time):
		camera = scene.GetCurrentCamera()
		renderer = plus.GetRenderer()
		renderer.EnableDepthTest(True)
		renderer.EnableDepthWrite(True)
		renderer.EnableBlending(False)

		renderer.SetShader(self.shader)
		renderer.SetShaderInt("sea_filtering", self.sea_filtering)
		renderer.SetShaderInt("max_samples", self.max_filter_samples)
		renderer.SetShaderFloat("filter_precision", self.filter_precision)
		renderer.SetShaderFloat("reflect_offset", self.reflect_offset)
		renderer.SetShaderTexture("tex_sky_N", self.tex_sky_N)
		renderer.SetShaderTexture("reflect_map", self.reflect_map)
		renderer.SetShaderTexture("reflect_map_depth", self.reflect_map_depth)
		renderer.SetShaderTexture("noise_texture_1", self.noise_texture_1)
		renderer.SetShaderTexture("noise_texture_2", self.noise_texture_2)
		renderer.SetShaderTexture("displacement_texture", self.noise_displacement_texture)
		renderer.SetShaderTexture("stream_texture", self.stream_texture)
		renderer.SetShaderTexture("clouds_map", self.clouds_map)
		renderer.SetShaderFloat3("clouds_scale", 1. / self.clouds_scale.x, self.clouds_scale.y,
								 1. / self.clouds_scale.z)
		renderer.SetShaderFloat("clouds_altitude", self.clouds_altitude)
		renderer.SetShaderFloat("clouds_absorption", self.clouds_absorption)
		# renderer.SetShaderFloat2("stream_scale",self.stream_scale.x,.y)

		renderer.SetShaderFloat2("resolution", resolution.x, resolution.y)
		renderer.SetShaderFloat("focal_distance", camera.GetCamera().GetZoomFactor())
		renderer.SetShaderFloat("tex_sky_N_intensity", self.tex_sky_N_intensity)
		renderer.SetShaderFloat("zenith_falloff", self.zenith_falloff)
		cam = camera.GetTransform().GetPreviousWorld()
		pos = cam.GetTranslation()
		renderer.SetShaderFloat3("cam_position", pos.x, pos.y, pos.z)
		renderer.SetShaderMatrix3("cam_normal", cam.GetRotationMatrix())
		renderer.SetShaderFloat3("sea_scale", 1 / self.sea_scale.x, self.sea_scale.y, 1 / self.sea_scale.z)
		renderer.SetShaderFloat("time", time)
		renderer.SetShaderFloat3("zenith_color", self.zenith_color.r, self.zenith_color.g, self.zenith_color.b)
		renderer.SetShaderFloat3("horizonH_color", self.horizon_N_color.r, self.horizon_N_color.g,
								 self.horizon_N_color.b)
		renderer.SetShaderFloat3("horizonL_color", self.horizon_S_color.r, self.horizon_S_color.g,
								 self.horizon_S_color.b)
		renderer.SetShaderFloat3("sea_color", self.sea_color.r, self.sea_color.g, self.sea_color.b)
		renderer.SetShaderFloat3("horizon_line_color", self.horizon_line_color.r, self.horizon_line_color.g,
								 self.horizon_line_color.b)
		renderer.SetShaderFloat("sea_reflection", self.sea_reflection)
		renderer.SetShaderFloat("horizon_line_size", self.horizon_line_size)

		l_dir = self.sun_light.GetTransform().GetWorld().GetRotationMatrix().GetZ()

		renderer.SetShaderFloat3("sun_dir", l_dir.x, l_dir.y, l_dir.z)
		l_couleur = self.sun_light.GetLight().GetDiffuseColor()
		renderer.SetShaderFloat3("sun_color", l_couleur.r, l_couleur.g, l_couleur.b)
		amb = hg.Color(scene.GetEnvironment().GetAmbientColor()) * scene.GetEnvironment().GetAmbientIntensity()
		renderer.SetShaderFloat3("ambient_color", amb.r, amb.g, amb.b)
		renderer.SetShaderFloat2("zFrustum", camera.GetCamera().GetZNear(), camera.GetCamera().GetZFar())
		if self.render_scene_reflection:
			renderer.SetShaderInt("scene_reflect", 1)
		else:
			renderer.SetShaderInt("scene_reflect", 0)
