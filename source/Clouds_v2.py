# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                           Clouds

# ===========================================================

import harfang as hg
from math import radians, pi, sin, cos
from data_converter import *


class ViewTrame:
	def __init__(self, distance_min=0, distance_max=1000, tile_size=10, margin=1., focal_margin=1.1):
		self.distance_min = distance_min
		self.distance_max = distance_max
		self.tile_size = tile_size
		self.O = hg.Vector2()
		self.A = hg.Vector2()
		self.B = hg.Vector2()
		self.focal_margin = focal_margin
		self.margin = margin
		self.Oint = hg.IntVector2()
		self.Aint = hg.IntVector2()
		self.Bint = hg.IntVector2()

		self.indiceA, self.indiceB = 0, 0
		self.ymin, self.ymax = 0, 0
		self.dAB, self.dBC, self.dAC = hg.IntVector2(), hg.IntVector2(), hg.IntVector2()
		self.detAB, self.detBC, self.detAC = 0, 0, 0
		self.obs = None
		self.obs2D = None
		self.vertices = []
		self.case = 0
		self.send_position = self.default_send

	def default_send(self, position: hg.Vector2):
		pass

	def update_triangle(self, resolution, position:hg.Vector3, direction:hg.Vector3, zoomFactor):
		self.obs = position
		self.obs2D = hg.Vector2(self.obs.x, self.obs.z)
		dir3D = direction
		dir2D = hg.Vector2(dir3D.x, dir3D.z).Normalized()
		focal_distance = zoomFactor * self.focal_margin
		view_width = 2 * resolution.x / resolution.y  # 2 because screen xmin=-1, screen xmax=1

		distAB = self.distance_max * view_width / focal_distance
		VUab = hg.Vector2(-dir2D.y, dir2D.x)
		dir2D *= self.distance_max
		VUab *= distAB / 2

		self.O = hg.Vector2(self.obs.x, self.obs.z)
		self.A = hg.Vector2(self.obs.x + dir2D.x - VUab.x, self.obs.z + dir2D.y - VUab.y)
		self.B = hg.Vector2(self.obs.x + dir2D.x + VUab.x, self.obs.z + dir2D.y + VUab.y)

		# Margin:
		cx = (self.O.x + self.A.x + self.B.x) / 3
		cy = (self.O.y + self.A.y + self.B.y) / 3
		self.O.x = (self.O.x - cx) * self.margin + cx
		self.O.y = (self.O.y - cy) * self.margin + cy
		self.A.x = (self.A.x - cx) * self.margin + cx
		self.A.y = (self.A.y - cy) * self.margin + cy
		self.B.x = (self.B.x - cx) * self.margin + cx
		self.B.y = (self.B.y - cy) * self.margin + cy

		# Tiled triangle:
		self.Oint = hg.IntVector2(int(round(self.O.x / self.tile_size)), int(round(self.O.y / self.tile_size)))
		self.Aint = hg.IntVector2(int(round(self.A.x / self.tile_size)), int(round(self.A.y / self.tile_size)))
		self.Bint = hg.IntVector2(int(round(self.B.x / self.tile_size)), int(round(self.B.y / self.tile_size)))

		self.vertices = [self.Oint, self.Aint, self.Bint]

		self.indiceA = 0
		self.ymin = self.Oint.y
		self.ymax = self.ymin
		if self.Aint.y < self.ymin:
			self.ymin = self.Aint.y
			self.indiceA = 1

		if self.Bint.y < self.ymin:
			self.ymin = self.Bint.y
			self.indiceA = 2
		if self.Aint.y > self.ymax:
			self.ymax = self.Aint.y
		if self.Bint.y > self.ymax:
			self.ymax = self.Bint.y

		self.indiceB = (self.indiceA + 1) % 3
		self.indiceC = (self.indiceA + 2) % 3

		if self.vertices[self.indiceA].y == self.vertices[self.indiceC].y:
			self.indiceA = self.indiceC
			self.indiceB = (self.indiceA + 1) % 3
			self.indiceC = (self.indiceA + 2) % 3

		self.dAB.x = self.vertices[self.indiceB].x - self.vertices[self.indiceA].x
		self.dAB.y = self.vertices[self.indiceB].y - self.vertices[self.indiceA].y
		self.dBC.x = self.vertices[self.indiceC].x - self.vertices[self.indiceB].x
		self.dBC.y = self.vertices[self.indiceC].y - self.vertices[self.indiceB].y
		self.dAC.x = self.vertices[self.indiceC].x - self.vertices[self.indiceA].x
		self.dAC.y = self.vertices[self.indiceC].y - self.vertices[self.indiceA].y

		if self.dAB.y == 0:
			self.detAB = 0
		else:
			self.detAB = float(self.dAB.x) / float(self.dAB.y)

		if self.dBC.y == 0:
			self.detBC = 0
		else:
			self.detBC = float(self.dBC.x) / float(self.dBC.y)

		if self.dAC.y == 0:
			self.detAC = 0
		else:
			self.detAC = float(self.dAC.x) / float(self.dAC.y)

	def fill_triangle(self):
		# Cas1:
		#       A*******B
		#        *****
		#          C
		if self.dAB.y == 0:
			self.case = 1
			self.fill_case(self.ymin, self.ymax, float(self.vertices[self.indiceA].x),
						   float(self.vertices[self.indiceB].x), self.detAC, self.detBC)
		# Cas2:
		#       A
		#     *****
		#   C*******B
		elif self.dBC.y == 0:
			self.case = 2
			self.fill_case(self.ymin, self.ymax, float(self.vertices[self.indiceA].x),
						   float(self.vertices[self.indiceA].x), self.detAC, self.detAB)

		# Cas3:
		#        A
		#       ***
		#      C***
		#       ****
		#         *B
		elif self.dAB.y > self.dAC.y:
			self.case = 3
			self.fill_case(self.ymin, self.vertices[self.indiceC].y - 1, float(self.vertices[self.indiceA].x),
						   float(self.vertices[self.indiceA].x), self.detAC, self.detAB)
			self.fill_case(self.vertices[self.indiceC].y, self.ymax, float(self.vertices[self.indiceC].x),
						   float(self.vertices[self.indiceA].x) + self.detAB * (
								   float(self.vertices[self.indiceC].y) - float(self.ymin)), self.detBC, self.detAB)
		# Cas4:
		#       A
		#       ***
		#       ***B
		#      ****
		#      C*
		else:
			self.case = 4
			self.fill_case(self.ymin, self.vertices[self.indiceB].y - 1, float(self.vertices[self.indiceA].x),
						   float(self.vertices[self.indiceA].x), self.detAC, self.detAB)

			self.fill_case(self.vertices[self.indiceB].y, self.ymax,
						   float(self.vertices[self.indiceA].x) + self.detAC * (
								   float(self.vertices[self.indiceB].y) - float(self.ymin)),
						   float(self.vertices[self.indiceB].x), self.detAC, self.detBC)

	def fill_case(self, ymin, ymax, p_x0, p_x1, d1, d2):
		x0 = p_x0
		x1 = p_x1
		for y in range(ymin, ymax + 1):
			for x in range(int(x0), int(x1)):
				pos = hg.Vector2(x * self.tile_size, y * self.tile_size)
				if (pos - self.obs2D).Len() >= self.distance_min:
					self.send_position(pos)
			x0 += d1
			x1 += d2


class CloudsLayer(ViewTrame):
	billboard2D = 0
	billboard3D = 1

	def __getstate__(self):
		dico = {"name": self.name, "billboard_type": self.billboard_type,
			"particles_scale_range": vec2_to_list(self.particles_scale_range), "num_particles": self.num_particles,
			"num_geometries": self.num_geometries, "particles_files_names": self.particles_files_names,
			"distance_min": self.distance_min, "distance_max": self.distance_max, "tile_size": self.tile_size,
			"margin": self.margin, "focal_margin": self.focal_margin, "absorption": self.absorption,
			"altitude": self.altitude, "altitude_floor": self.altitude_floor, "alpha_threshold": self.alpha_threshold,
			"scale_falloff": self.scale_falloff, "alpha_scale_falloff": self.alpha_scale_falloff,
			"altitude_falloff": self.altitude_falloff, "perturbation": self.perturbation,
		    "particles_rot_speed": self.particles_rot_speed, "morph_level": self.morph_level}
		return dico

	def __setstate__(self, state):
		if "particles_scale_range" in state:
			state["particles_scale_range"] = list_to_vec2(state["particles_scale_range"])
		for k, v in state.items():
			if hasattr(self, k): setattr(self, k, v)

	def __init__(self, plus, scene, parameters: dict):
		ViewTrame.__init__(self, parameters["distance_min"], parameters["distance_max"], parameters["tile_size"],
						   parameters["margin"], parameters["focal_margin"])
		self.name = parameters["name"]
		self.billboard_type = parameters["billboard_type"]
		self.particles_scale_range = list_to_vec2(parameters["particles_scale_range"])
		self.num_tiles = 0
		self.num_particles = parameters["num_particles"]  # List !
		self.num_geometries = parameters["num_geometries"]
		self.particle_index = [0] * self.num_geometries
		self.particle_index_prec = [0] * self.num_geometries
		self.particles_files_names = parameters["particles_files_names"]  # List !
		self.particles = []
		for i in range(0, self.num_geometries):
			particles = self.create_particles(plus, scene, self.particles_files_names[i], self.num_particles[i],
											  self.name + "." + str(i))
			self.particles.append(particles)

		self.absorption = parameters["absorption"]
		self.altitude = parameters["altitude"]
		self.altitude_floor = parameters["altitude_floor"]
		self.alpha_threshold = parameters["alpha_threshold"]
		self.scale_falloff = parameters["scale_falloff"]
		self.alpha_scale_falloff = parameters["alpha_scale_falloff"]
		self.altitude_falloff = parameters["altitude_falloff"]
		self.perturbation = parameters["perturbation"]
		self.particles_rot_speed=0.1
		if "particles_rot_speed" in parameters:
			self.particles_rot_speed=parameters["particles_rot_speed"]

		# map:
		self.map_size = None
		self.map_scale = None
		self.bitmap_clouds = None

		# Environment:
		self.sun_dir = None
		self.sun_color = None
		self.ambient_color = None

		# Updates vars
		self.rot_hash = hg.Vector3(313.464, 7103.3, 4135.1)
		self.scale_size = 0
		self.pc = hg.Color(1, 1, 1, 1)
		self.cam_pos = None
		self.t = 0

		self.morph_level=1.2
		if "morph_level" in parameters:
			self.morph_level=parameters["morph_level"]
		self.offset=hg.Vector2(0,0) #Used for clouds wind displacement

		self.renderable_system = scene.GetRenderableSystem()
		self.smooth_alpha_threshold_step=0.1

	@staticmethod
	def create_particles(plus, scene, file_name, num, name):
		particles = []
		for i in range(num):
			node, geo = load_object(plus, file_name, name + "." + str(i), True)
			# scene.AddNode(node)
			particles.append([geo, hg.Matrix4(),geo.GetMaterial(0)])
		return particles

	def set_map(self, bitmap: hg.Picture, map_scale: hg.Vector2, map_position:hg.Vector2):
		self.bitmap_clouds = bitmap
		self.map_scale = map_scale
		self.map_size = hg.IntVector2(self.bitmap_clouds.GetWidth(), self.bitmap_clouds.GetHeight())
		self.offset=map_position

	def set_environment(self, sun_dir, sun_color, ambient_color):
		self.sun_dir = sun_dir
		self.sun_color = sun_color
		self.ambient_color = ambient_color
		self.update_particles()

	def update_lighting(self, sun_dir, sun_color, ambient_color):
		self.sun_dir = sun_dir
		self.sun_color = sun_color
		self.ambient_color = ambient_color
		self.update_particles_lighting()

	def clear_particles(self):
		return
		for particles in self.particles:
			for particle in particles:
				particle.SetEnabled(False)

	def update_particles_lighting(self):
		for i in range(0, self.num_geometries):
			particles = self.particles[i]
			for particle in particles:
				material = particle[0].GetMaterial(0)
				material.SetFloat3("sun_dir", self.sun_dir.x, self.sun_dir.y, self.sun_dir.z)
				material.SetFloat3("sun_color", self.sun_color.r, self.sun_color.g, self.sun_color.b)
				material.SetFloat3("ambient_color", self.ambient_color.r, self.ambient_color.g, self.ambient_color.b)

	def update_particles(self):
		altitude_min = self.altitude - self.particles_scale_range.y / 2
		if altitude_min > self.altitude:
			altitude_max = altitude_min
			altitude_min = self.altitude
		else:
			altitude_max = self.altitude
		for i in range(0, self.num_geometries):
			particles = self.particles[i]
			c = hg.Color(1., 1., 1., 1.)
			for particle in particles:
				material = particle[0].GetMaterial(0)
				t = material.IsReadyOrFailed()
				if t:
					material.SetFloat("alpha_cloud", c.a)
					material.SetFloat3("sun_dir", self.sun_dir.x, self.sun_dir.y, self.sun_dir.z)
					material.SetFloat3("sun_color", self.sun_color.r, self.sun_color.g, self.sun_color.b)
					material.SetFloat3("ambient_color", self.ambient_color.r, self.ambient_color.g, self.ambient_color.b)
					material.SetFloat("absorption_factor", self.absorption)
					material.SetFloat("layer_dist", self.distance_min)
					material.SetFloat("altitude_min", altitude_min)
					material.SetFloat("altitude_max", altitude_max)
					material.SetFloat("altitude_falloff", self.altitude_falloff)
					material.SetFloat("rot_speed",self.particles_rot_speed)




	def set_altitude(self, value):
		self.altitude = value
		self.update_particles()

	def set_particles_rot_speed(self,value):
		self.particles_rot_speed = value
		self.update_particles()

	def set_distance_min(self, value):
		self.distance_min = value
		self.distance_max = max(self.distance_max, self.distance_min + self.tile_size)
		self.update_particles()

	def set_distance_max(self, value):
		self.distance_max = value
		self.distance_min = min(self.distance_min, self.distance_max - self.tile_size)
		self.update_particles()

	def set_absorption(self, value):
		self.absorption = value
		self.update_particles()

	def set_altitude_floor(self, value):
		self.altitude_floor = value
		self.update_particles()

	def set_altitude_falloff(self, value):
		self.altitude_falloff = value
		self.update_particles()

	def set_particles_min_scale(self, value):
		self.particles_scale_range.x = value
		self.particles_scale_range.y = max(self.particles_scale_range.y, value + 1)
		self.update_particles()

	def set_particles_max_scale(self, value):
		self.particles_scale_range.y = value
		self.particles_scale_range.x = min(self.particles_scale_range.x, value - 1)
		self.update_particles()

	def get_pixel_bilinear(self, pos: hg.Vector2):
		x = (pos.x * self.map_size.x - 0.5) % self.map_size.x
		y = (pos.y * self.map_size.y - 0.5) % self.map_size.y
		xi = int(x)
		yi = int(y)
		xf = x - xi
		yf = y - yi
		xi1 = (xi + 1) % self.map_size.x
		yi1 = (yi + 1) % self.map_size.y
		c1 = self.bitmap_clouds.GetPixelRGBA(xi, yi)
		c2 = self.bitmap_clouds.GetPixelRGBA(xi1, yi)
		c3 = self.bitmap_clouds.GetPixelRGBA(xi, yi1)
		c4 = self.bitmap_clouds.GetPixelRGBA(xi1, yi1)
		c12 = c1 * (1 - xf) + c2 * xf
		c34 = c3 * (1 - xf) + c4 * xf
		c = c12 * (1 - yf) + c34 * yf
		return c

	def update(self, t, camera, resolution,map_position:hg.Vector2):
		self.offset=map_position
		self.t = t
		self.num_tiles = 0
		self.particle_index_prec = self.particle_index
		self.particle_index = [0] * self.num_geometries
		# for i in range (0,self.num_textures_layer_2):
		#    self.particle_index_layer_2.append(0)
		self.cam_pos = camera.GetTransform().GetPosition()
		self.pc = hg.Color(1., 1., 1., 1.)
		self.scale_size = self.particles_scale_range.y - self.particles_scale_range.x
		self.rot_hash = hg.Vector3(133.464, 4713.3, 1435.1)

		self.send_position = self.set_particle
		self.update_triangle(resolution, camera.GetTransform().GetPosition()+hg.Vector3(self.offset.x,0,self.offset.y),
		                     camera.GetTransform().GetWorld().GetZ(), camera.GetCamera().GetZoomFactor())
		self.fill_triangle()


	def set_particle(self, position: hg.Vector2):
		self.num_tiles += 1
		# x = int(position.x / self.map_scale.x * self.map_size.x)
		# y = int(position.y / self.map_scale.y * self.map_size.y)
		# c = self.bitmap_clouds.GetPixelRGBA(int(x % self.map_size.x), int(y % self.map_size.y))
		c = self.get_pixel_bilinear((position+self.offset*self.morph_level) / self.map_scale)

		scale_factor = pow(c.x, self.scale_falloff)
		# id = int(max(0,scale_factor - self.layer_2_alpha_threshold) / (1 - self.layer_2_alpha_threshold) * 7)
		id = int((sin(position.x * 1735.972 + position.y * 345.145) * 0.5 + 0.5) * (self.num_geometries - 1))
		if self.particle_index[id] < self.num_particles[id]:

			particle = self.particles[id][self.particle_index[id]]
			if c.x > self.alpha_threshold:
				smooth_alpha_threshold=min(1,(c.x-self.alpha_threshold)/self.smooth_alpha_threshold_step)
				s = self.particles_scale_range.x + scale_factor * self.scale_size
				py = self.altitude + s * self.altitude_floor + (self.perturbation * (1 - c.x) * sin(position.x * 213))
				pos = hg.Vector3(position.x-self.offset.x, py, position.y-self.offset.y)

				d = (hg.Vector2(pos.x, pos.z) - hg.Vector2(self.cam_pos.x, self.cam_pos.z)).Len()
				layer_n = abs(max(0, min(1, (d - self.distance_min) / (self.distance_max - self.distance_min))) * 2 - 1)
				self.pc.a = (1 - min(pow(layer_n, 8), 1)) * (1 - pow(1. - scale_factor, self.alpha_scale_falloff)) * smooth_alpha_threshold

				particle[1] = hg.Matrix4(hg.Matrix3.Identity)
				particle[1].SetScale(hg.Vector3(s, s, s))

				particle[1].SetTranslation(pos)
				material = particle[2]
				material.SetFloat2("pos0", position.x, position.y)
				material.SetFloat("alpha_cloud", self.pc.a)

				self.renderable_system.DrawGeometry(particle[0], particle[1])

				self.particle_index[id] += 1


class Clouds:
	def __setstate__(self, state):
		vec2_list = ["map_scale", "map_position", "v_wind"]
		for k in vec2_list:
			if k in state: state[k] = list_to_vec2(state[k])
		if "layers" in state:
			for layer_state in state["layers"]:
				layer = self.get_layer_by_name(layer_state["name"])
				if layer is not None:
					layer.__setstate__(layer_state)  # !!! Ne recharge pas les géométries !!
		del state["layers"]

		for k, v in state.items():
			if hasattr(self, k): setattr(self, k, v)
		self.update_layers_cloud_map()
		self.update_layers_environment()
		self.update_particles()

	def __getstate__(self):
		layers_list = []
		for layer in self.layers:
			layers_list.append(layer.__getstate__())
		dico = {"name": self.name, "bitmap_clouds_file": self.bitmap_clouds_file,
			"map_scale": vec2_to_list(self.map_scale), "map_position": vec2_to_list(self.map_position),
		    "v_wind":vec2_to_list(self.v_wind),"layers": layers_list}
		return dico

	def __init__(self, plus, scene, main_light, resolution, parameters):

		self.layers = []
		for layer_params in parameters["layers"]:
			self.layers.append(CloudsLayer(plus, scene, layer_params))

		self.name = parameters["name"]
		self.t = 0
		self.cam_pos = None
		self.bitmap_clouds = hg.Picture()
		self.bitmap_clouds_file = parameters["bitmap_clouds_file"]
		hg.LoadPicture(self.bitmap_clouds, self.bitmap_clouds_file)
		self.map_size = hg.IntVector2(self.bitmap_clouds.GetWidth(), self.bitmap_clouds.GetHeight())
		self.map_scale = list_to_vec2(parameters["map_scale"])
		self.map_position = list_to_vec2(parameters["map_position"])
		self.sun_light = main_light
		self.ambient_color = scene.GetEnvironment().GetAmbientColor() * scene.GetEnvironment().GetAmbientIntensity()
		self.v_wind=hg.Vector2(60,60)
		if "v_wind" in parameters:
			self.v_wind=list_to_vec2(parameters["v_wind"])

		self.update_layers_cloud_map()
		self.update_layers_environment()
		self.update_particles()

	def get_layer_by_name(self, layer_name):
		for layer in self.layers:
			if layer.name == layer_name: return layer
		return None

	def update_layers_cloud_map(self):
		for layer in self.layers:
			layer.set_map(self.bitmap_clouds, self.map_scale, self.map_position)

	def update_layers_lighting(self):
		sun_dir = self.sun_light.GetTransform().GetWorld().GetZ()
		lt = self.sun_light.GetLight()
		sun_color = lt.GetDiffuseColor() * lt.GetDiffuseIntensity()
		for layer in self.layers:
			layer.update_lighting(sun_dir, sun_color, self.ambient_color)

	def update_layers_environment(self):
		sun_dir = self.sun_light.GetTransform().GetWorld().GetZ()
		lt = self.sun_light.GetLight()
		sun_color = lt.GetDiffuseColor() * lt.GetDiffuseIntensity()
		for layer in self.layers:
			layer.set_environment(sun_dir, sun_color, self.ambient_color)

	def load_json_script(self, file_name="assets/scripts/clouds_parameters.json"):
		json_script = hg.GetFilesystem().FileToString(file_name)
		if json_script != "":
			script_parameters = json.loads(json_script)
			self.__setstate__(script_parameters)

	def save_json_script(self, scene, output_filename="assets/scripts/clouds_parameters.json"):
		script_parameters = self.__getstate__()
		json_script = json.dumps(script_parameters, indent=4)
		return hg.GetFilesystem().StringToFile(output_filename, json_script)

	def set_map_scale_x(self, value):
		self.map_scale.x = value
		self.update_layers_cloud_map()

	def set_map_scale_z(self, value):
		self.map_scale.y = value
		self.update_layers_cloud_map()

	def clear_particles(self):
		for layer in self.layers:
			layer.clear_particles()

	def update_particles(self):
		for layer in self.layers:
			layer.update_particles()

	def update(self, t, delta_t, scene, resolution):
		self.t = t
		camera = scene.GetCurrentCamera()
		self.cam_pos = camera.GetTransform().GetPosition()
		self.map_position+=self.v_wind*delta_t
		for layer in self.layers:
			layer.update(t, camera, resolution, self.map_position)
