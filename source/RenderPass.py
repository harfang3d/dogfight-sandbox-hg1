# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                  Render to texture tools

# ===========================================================

import harfang as hg
import json


class RenderRect:
	def __init__(self, plus):
		renderer = plus.GetRenderer()

		# create primitive index buffer
		'''
		data = hg.BinaryData()
		data.WriteInt16s([0, 1, 2, 0, 2, 3])

		self.indices = renderer.NewBuffer()
		renderer.CreateBuffer(self.indices, data, hg.GpuBufferIndex)

		# create primitive vertex buffer
		self.vertex_layout = hg.VertexLayout()
		self.vertex_layout.AddAttribute(hg.VertexPosition, 3, hg.VertexFloat)
		self.vertex_layout.AddAttribute(hg.VertexUV0, 2, hg.VertexUByte,
										True)  # UVs are sent as normalized 8 bit unsigned integer (range [0;255])

		data = hg.BinaryData()
		x, y = 1, 1
		data.WriteFloats([-x, -y, 0])
		data.WriteUInt8s([0, 0])

		data.WriteFloats([-x, y, 0])
		data.WriteUInt8s([0, 255])

		data.WriteFloats([x, y, 0])
		data.WriteUInt8s([255, 255])

		data.WriteFloats([x, -y, 0])
		data.WriteUInt8s([255, 0])

		self.vertex = renderer.NewBuffer()
		renderer.CreateBuffer(self.vertex, data, hg.GpuBufferVertex)
		'''

	def draw(self, plus):
		render_system=plus.GetRenderSystem()
		render_system.DrawFullscreenQuad(render_system.GetViewportToInternalResolutionRatio())
		#hg.DrawBuffers(plus.GetRenderer(), 6, self.indices, self.vertex, self.vertex_layout)


class RenderToTexture(RenderRect):
	def __init__(self, plus, resolution: hg.Vector2):
		RenderRect.__init__(self, plus)

		renderer = plus.GetRenderer()

		# Parameters:
		self.hue = 0
		self.saturation = 1
		self.value = 1
		self.contrast = 0
		self.contrast_threshold = 0.5

		# Shaders:
		self.shader_z_fusion = renderer.LoadShader("assets/shaders/fusion_2_tex_post_render.isl")
		self.shader_HSV = renderer.LoadShader("assets/shaders/HSV_post_render.isl")

		# Création des textures de rendu:
		self.texture_rendu_1 = renderer.NewTexture()
		renderer.CreateTexture(self.texture_rendu_1, int(resolution.x), int(resolution.y), hg.TextureRGBA8,
							   hg.TextureNoAA, 0, False)
		self.texture_rendu_1_depth = renderer.NewTexture()
		renderer.CreateTexture(self.texture_rendu_1_depth, int(resolution.x), int(resolution.y), hg.TextureDepth,
							   hg.TextureNoAA, 0, False)

		self.texture_rendu_2 = renderer.NewTexture()
		renderer.CreateTexture(self.texture_rendu_2, int(resolution.x), int(resolution.y), hg.TextureRGBA8,
							   hg.TextureNoAA, 0, False)
		self.texture_rendu_2_depth = renderer.NewTexture()
		renderer.CreateTexture(self.texture_rendu_2_depth, int(resolution.x), int(resolution.y), hg.TextureDepth,
							   hg.TextureNoAA, 0, False)

		# Création des frameBuffer objects:
		self.render_target_1 = renderer.NewRenderTarget()
		renderer.CreateRenderTarget(self.render_target_1)
		renderer.SetRenderTargetColorTexture(self.render_target_1, self.texture_rendu_1)
		renderer.SetRenderTargetDepthTexture(self.render_target_1, self.texture_rendu_1_depth)

		self.render_target_2 = renderer.NewRenderTarget()
		renderer.CreateRenderTarget(self.render_target_2)
		renderer.SetRenderTargetColorTexture(self.render_target_2, self.texture_rendu_2)
		renderer.SetRenderTargetDepthTexture(self.render_target_2, self.texture_rendu_2_depth)

		self.projection_matrix_mem = None
		self.view_matrix_mem = None
		self.projection_matrix_ortho = None

	def begin_render(self, plus):
		renderer = plus.GetRenderer()

		renderer.SetWorldMatrix(hg.Matrix4.Identity)
		self.projection_matrix_mem = renderer.GetProjectionMatrix()
		self.view_matrix_mem = renderer.GetViewMatrix()

		self.projection_matrix_ortho = hg.ComputeOrthographicProjectionMatrix(1., 500., 2, hg.Vector2(1, 1))
		renderer.SetProjectionMatrix(self.projection_matrix_ortho)
		renderer.SetViewMatrix(hg.Matrix4.Identity)

	def end_render(self, plus):
		renderer = plus.GetRenderer()
		self.draw(plus)
		renderer.SetProjectionMatrix(self.projection_matrix_mem)
		renderer.SetViewMatrix(self.view_matrix_mem)

	def draw_renderTexture_fusion_HSV(self, plus):
		renderer = plus.GetRenderer()
		self.begin_render(plus)
		renderer.SetShader(self.shader_z_fusion)
		renderer.SetShaderTexture("u_tex1", self.texture_rendu_1)
		renderer.SetShaderTexture("u_tex2", self.texture_rendu_2)
		renderer.SetShaderTexture("u_tex1_depth", self.texture_rendu_1_depth)
		renderer.SetShaderTexture("u_tex2_depth", self.texture_rendu_2_depth)
		renderer.SetShaderFloat("contrast", self.contrast)
		renderer.SetShaderFloat("threshold", self.contrast_threshold)
		renderer.SetShaderFloat("H", self.hue)
		renderer.SetShaderFloat("S", self.saturation)
		renderer.SetShaderFloat("V", self.value)
		self.end_render(plus)

	def draw_renderTexture_HSV(self, plus):
		renderer = plus.GetRenderer()
		self.begin_render(plus)
		renderer.SetShader(self.shader_HSV)
		renderer.SetShaderTexture("u_tex", self.texture_rendu_1)
		renderer.SetShaderFloat("contrast", self.contrast)
		renderer.SetShaderFloat("threshold", self.contrast_threshold)
		renderer.SetShaderFloat("H", self.hue)
		renderer.SetShaderFloat("S", self.saturation)
		renderer.SetShaderFloat("V", self.value)
		self.end_render(plus)

	def load_parameters(self, file_name="assets/scripts/post_render.json"):
		json_script = hg.GetFilesystem().FileToString(file_name)
		if json_script != "":
			script_parameters = json.loads(json_script)
			self.contrast = script_parameters["contrast"]
			self.contrast_threshold = script_parameters["contrast_threshold"]
			self.hue = script_parameters["hue"]
			self.saturation = script_parameters["saturation"]
			self.value = script_parameters["value"]

	def save_parameters(self, output_filename="assets/scripts/post_render.json"):
		script_parameters = {"contrast": self.contrast, "contrast_threshold": self.contrast_threshold, "hue": self.hue,
							 "saturation": self.saturation, "value": self.value}
		json_script = json.dumps(script_parameters, indent=4)
		return hg.GetFilesystem().StringToFile(output_filename, json_script)
