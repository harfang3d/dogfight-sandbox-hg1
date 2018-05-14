# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                      Plane reflexion

# ===========================================================

import harfang as hg
import json
from data_converter import *


class WaterReflection():
	def __init__(self, plus, scene, resolution: hg.Vector2, texture_width=256):

		renderer = plus.GetRenderer()
		render_system = plus.GetRenderSystem()

		# Parameters:
		self.color = hg.Color(1, 1, 0, 1)
		self.reflect_level = 0.75

		# Shaders:
		# self.shader_water_reflection = render_system.LoadSurfaceShader("assets/shaders/water_reflection.isl")

		# Reflection plane, just to get normal & origine:
		# self.plane=plus.AddPlane(scene, hg.Matrix4.TransformationMatrix(hg.Vector3(0,0,0), hg.Vector3(radians(0), radians(0), radians(0))), 1, 1)
		# self.plane.SetName("Water_Reflection_Plane")

		# Création des textures de rendu:
		tex_res = hg.Vector2(texture_width, texture_width * resolution.y / resolution.x)
		self.render_texture = renderer.NewTexture()
		renderer.CreateTexture(self.render_texture, int(tex_res.x), int(tex_res.y), hg.TextureRGBA8, hg.TextureNoAA, 0,
							   False)
		self.render_depth_texture = renderer.NewTexture()
		renderer.CreateTexture(self.render_depth_texture, int(tex_res.x), int(tex_res.y), hg.TextureDepth,
							   hg.TextureNoAA, 0, False)

		# Création des frameBuffer objects:
		self.render_target = renderer.NewRenderTarget()
		renderer.CreateRenderTarget(self.render_target)
		renderer.SetRenderTargetColorTexture(self.render_target, self.render_texture)
		renderer.SetRenderTargetDepthTexture(self.render_target, self.render_depth_texture)

		self.projection_matrix_mem = None
		self.view_matrix_mem = None
		self.projection_matrix_ortho = None
		# Reflection camera:
		self.camera_reflect = plus.AddCamera(scene, hg.Matrix4.TranslationMatrix(hg.Vector3(0, -2, 0)))
		self.camera_reflect.SetName("Camera.water_reflection")

		self.clear_reflect_map(plus)

	@staticmethod
	def get_plane_projection_factor(p: hg.Vector3, plane_origine: hg.Vector3, plane_normal: hg.Vector3):
		d = -plane_normal.x * plane_origine.x - plane_normal.y * plane_origine.y - plane_normal.z * plane_origine.z
		return -plane_normal.x * p.x - plane_normal.y * p.y - plane_normal.z * p.z - d

	def clear_reflect_map(self, plus):
		renderer = plus.GetRenderer()
		renderer.SetRenderTarget(self.render_target)
		renderer.Clear(hg.Color(0., 0., 0., 0.))

	def render(self, plus, scene, camera, disable_render_scripts=False, mat_camera=None):
		renderer = plus.GetRenderer()
		# Clipping plane:
		# mat=self.plane.GetTransform().GetWorld()
		# plane_pos=mat.GetTranslation()
		# plane_normal=mat.GetY()
		# renderer.SetClippingPlane(plane_pos+plane_normal*0.01, plane_normal)

		plane_pos = hg.Vector3(0, 0, 0)
		plane_normal = hg.Vector3(0, 1, 0)

		# Camera reflect:
		if mat_camera is not None:
			mat = mat_camera
		else:
			mat = camera.GetTransform().GetWorld()
		pos = mat.GetTranslation()
		t = self.get_plane_projection_factor(pos, plane_pos, plane_normal)
		pos_reflect = pos + plane_normal * 2 * t
		xAxis = mat.GetX()
		zAxis = mat.GetZ()
		px = pos + xAxis
		tx = self.get_plane_projection_factor(px, plane_pos, plane_normal)
		x_reflect = px + plane_normal * 2 * tx - pos_reflect
		z_reflect = hg.Reflect(zAxis, plane_normal)
		y_reflect = hg.Cross(z_reflect, x_reflect)
		mat.SetTranslation(pos_reflect)
		mat.SetX(x_reflect)
		mat.SetY(y_reflect)
		mat.SetZ(z_reflect)
		self.camera_reflect.GetTransform().SetWorld(mat)
		scene.SetCurrentCamera(self.camera_reflect)
		cam_org = camera.GetCamera()
		cam = self.camera_reflect.GetCamera()
		cam.SetZoomFactor(cam_org.GetZoomFactor())
		cam.SetZNear(cam_org.GetZNear())
		cam.SetZFar(cam_org.GetZFar())
		# Render target:
		vp_mem = renderer.GetViewport()
		rect = self.render_texture.GetRect()
		renderer.SetViewport(rect)
		renderer.SetRenderTarget(self.render_target)
		renderer.Clear(hg.Color(0., 0., 0., 0.))

		if disable_render_scripts:
			enabled_list = []
			render_scripts = scene.GetComponents("RenderScript")
			for rs in render_scripts:
				enabled_list.append(rs.GetEnabled())
				rs.SetEnabled(False)

		scene.Commit()
		scene.WaitCommit()
		plus.UpdateScene(scene)

		# Update reflection texture:
		# material = self.plane.GetObject().GetGeometry().GetMaterial(0)
		# material.SetTexture("reflect_map", self.render_texture)
		# material.SetFloat("reflect_level", self.reflect_level)
		# material.SetFloat4("color", self.color.r,self.color.g,self.color.b,self.color.a)

		# System restauration
		scene.SetCurrentCamera(camera)
		renderer.ClearRenderTarget()
		# renderer.ClearClippingPlane()
		renderer.SetViewport(vp_mem)

		if disable_render_scripts:
			for rs in enumerate(render_scripts):
				if enabled_list[rs[0]]:
					rs[1].SetEnabled(True)

		scene.Commit()
		scene.WaitCommit()

	def load_parameters(self, file_name="assets/scripts/water_reflection.json"):
		json_script = hg.GetFilesystem().FileToString(file_name)
		if json_script != "":
			script_parameters = json.loads(json_script)
			self.color = list_to_color(script_parameters["color"])
			self.reflect_level = script_parameters["reflect_level"]

	def save_parameters(self, output_filename="assets/scripts/water_reflection.json"):
		script_parameters = {"color": color_to_list(self.color), "reflect_level": self.reflect_level}
		json_script = json.dumps(script_parameters, indent=4)
		return hg.GetFilesystem().StringToFile(output_filename, json_script)
