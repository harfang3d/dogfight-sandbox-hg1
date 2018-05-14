# -*-coding:Utf-8 -*

# ===================================================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#         Aircrafts, Aircraft Carriers, Missiles...etd

# ====================================================================================

import harfang as hg
from MathsSupp import *
from math import radians, degrees, pi, sqrt, exp, floor, acos, asin
from data_converter import *
from Particles import *


# =====================================================================================================
#                                  Destroyable machine
# =====================================================================================================
class Destroyable_Machine:
	TYPE_SHIP = 1
	TYPE_AIRCRAFT = 2
	TYPE_MISSILE = 3
	TYPE_GROUND = 4

	def __init__(self, parent_node, type, nationality):
		self.type = type
		self.nationality = nationality
		self.parent_node = parent_node
		self.health_level = 1
		self.wreck = False
		self.activated = False  # Used by HUD radar
		self.v_move = hg.Vector3(0, 0, 0)
		self.ground_ray_cast_pos = hg.Vector3()
		self.ground_ray_cast_dir = hg.Vector3()
		self.ground_ray_cast_length = 2

	def get_parent_node(self):
		return self.parent_node

	def hit(self, value):
		raise NotImplementedError


# =====================================================================================================
#                                  Missile
# =====================================================================================================

class Missile(Destroyable_Machine):

	def __init__(self, name, nationality, plus, scene, audio, missile_file_name, smoke_file_name_prefix,
				 smoke_color: hg.Color = hg.Color.White, start_position=hg.Vector3.Zero,
				 start_rotation=hg.Vector3.Zero):
		self.name = name
		self.start_position = start_position
		self.start_rotation = start_rotation
		self.smoke_color = smoke_color
		self.gravity = hg.Vector3(0, -9.8, 0)
		self.audio = audio

		nd, geo = load_object(plus, missile_file_name, name, False)
		Destroyable_Machine.__init__(self, nd, Destroyable_Machine.TYPE_MISSILE, nationality)

		scene.AddNode(self.parent_node)
		self.smoke = []

		for i in range(17):
			node, geo = load_object(plus, smoke_file_name_prefix + "." + str(i) + ".geo", name + ".smoke." + str(i),
									True)
			scene.AddNode(node)
			self.smoke.append(node)

		self.target = None
		self.f_thrust = 200
		self.moment_speed = 1.

		self.drag_coeff = hg.Vector3(0.37, 0.37, 0.0003)
		self.air_density = 1.225
		self.smoke_parts_distance = 1.44374
		self.set_smoke_solor(self.smoke_color)
		self.smoke_delay = 1
		self.smoke_time = 0

		self.life_delay = 20
		self.life_cptr = 0

		# Feed-backs:
		self.explode = ParticlesEngine(self.name + ".explode", plus, scene, "assets/feed_backs/feed_back_explode.geo",
									   50, hg.Vector3(5, 5, 5), hg.Vector3(100, 100, 100), 180)
		self.explode.delay_range = hg.Vector2(1, 2)
		self.explode.flow = 0
		self.explode.scale_range = hg.Vector2(0.25, 2)
		self.explode.start_speed_range = hg.Vector2(0, 100)
		self.explode.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0., 0., 0.5), hg.Color(0., 0., 0., 0.25),
							   hg.Color(0., 0., 0., 0.125), hg.Color(0., 0., 0., 0.0)]
		self.explode.set_rot_range(radians(20), radians(50), radians(10), radians(45), radians(5), radians(15))
		self.explode.gravity = hg.Vector3(0, -9.8, 0)
		self.explode.loop = False

		# Sfx:
		self.explosion_settings = hg.MixerChannelState(0, 0, hg.MixerNoLoop)
		self.turbine_channel = None
		self.turbine_settings = hg.MixerChannelState(0, 0, hg.MixerRepeat)

	def hit(self, value):
		pass

	def reset(self, position=None, rotation=None):
		if self.turbine_channel is not None:
			self.audio.Stop(self.turbine_channel)
		self.smoke_time = 0
		if position is not None:
			self.start_position = position
		if rotation is not None:
			self.start_rotation = rotation
		self.parent_node.GetTransform().SetPosition(self.start_position)
		self.parent_node.GetTransform().SetRotation(self.start_rotation)
		self.activated = False
		for node in self.smoke:
			node.GetTransform().SetPosition(hg.Vector3(0, 0, 0))
			node.SetEnabled(False)
		self.explode.reset()
		self.explode.flow = 0
		self.parent_node.SetEnabled(True)
		self.wreck = False
		self.v_move *= 0
		self.life_cptr = 0

	def set_smoke_solor(self, color: hg.Color):
		self.smoke_color = color
		for node in self.smoke:
			node.GetTransform().SetPosition(hg.Vector3(0, 0, 0))
			node.GetObject().GetGeometry().GetMaterial(0).SetFloat4("teint", self.smoke_color.r, self.smoke_color.g,
																	self.smoke_color.b, self.smoke_color.a)

	def get_parent_node(self):
		return self.parent_node

	def start(self, target: Destroyable_Machine, v0: hg.Vector3):
		if not self.activated:
			self.smoke_time = 0
			self.life_cptr = 0
			self.target = target
			self.v_move = hg.Vector3(v0)
			self.activated = True
			pos = self.parent_node.GetTransform().GetPosition()
			for node in self.smoke:
				node.SetEnabled(True)
				node.GetTransform().SetPosition(pos)

			self.turbine_settings.volume = 0
			self.turbine_channel = self.audio.Start(self.audio.LoadSound("assets/sfx/missile_engine.wav"),
													self.turbine_settings)

	def get_linear_speed(self):
		return self.v_move.Len()

	def update_smoke(self, target_point: hg.Vector3, dts):
		spd = self.get_linear_speed() * 0.033
		t = min(1, abs(self.smoke_time) / self.smoke_delay)
		self.smoke_time += dts
		n = len(self.smoke)
		color_end = self.smoke_color * t + hg.Color(1., 1., 1., 0.) * (1 - t)
		for i in range(n):
			node = self.smoke[i]
			ts = t * n
			ti = int(ts)
			if ti == i:
				ts -= ti
				alpha = ts * color_end.a
			elif ti > i:
				alpha = color_end.a
			else:
				alpha = 0
			node.GetObject().GetGeometry().GetMaterial(0).SetFloat4("teint", color_end.r, color_end.g, color_end.b,
																	alpha)

			mat = node.GetTransform().GetWorld()
			mat.SetScale(hg.Vector3(1, 1, 1))
			pos = mat.GetTranslation()
			v = target_point - pos
			dir = v.Normalized()
			# Position:
			if v.Len() > self.smoke_parts_distance * spd:
				pos = target_point - dir * self.smoke_parts_distance * spd * t
				node.GetTransform().SetPosition(hg.Vector3(pos))  # node.SetEnabled(True)
			# else:
			# node.SetEnabled(False)
			# Orientation:
			aZ = mat.GetZ().Normalized()
			axis_rot = hg.Cross(aZ, dir)
			angle = axis_rot.Len()
			if angle > 0.001:
				# Rotation matrix:
				ay = axis_rot.Normalized()
				rot_mat = hg.Matrix3(hg.Cross(ay, dir), ay, dir)
				node.GetTransform().SetRotationMatrix(rot_mat)
			node.GetTransform().SetScale(hg.Vector3(1, 1, spd * t))
			target_point = pos

	def update_kinetics(self, scene, dts):
		if self.activated:
			self.life_cptr += dts
			if self.life_cptr > self.life_delay:
				self.start_explosion()
			if not self.wreck:
				mat = self.parent_node.GetTransform().GetWorld()
				pos = mat.GetTranslation()

				aX = mat.GetX()
				aY = mat.GetY()
				aZ = mat.GetZ()
				# axis speed:
				spdX = aX * hg.Dot(aX, self.v_move)
				spdY = aY * hg.Dot(aY, self.v_move)
				spdZ = aZ * hg.Dot(aZ, self.v_move)

				q = hg.Vector3(pow(spdX.Len(), 2), pow(spdY.Len(), 2), pow(spdZ.Len(), 2)) * 0.5 * self.air_density

				# Drag force:
				F_drag = spdX.Normalized() * q.x * self.drag_coeff.x + spdY.Normalized() * q.y * self.drag_coeff.y + spdZ.Normalized() * q.z * self.drag_coeff.z

				F_thrust = aZ * self.f_thrust

				self.v_move += (F_thrust - F_drag + self.gravity) * dts

				pos += self.v_move * dts
				self.parent_node.GetTransform().SetPosition(pos)

				# Rotation
				if self.target is not None:
					target_node = self.target.get_parent_node()
					target_dir = (target_node.GetTransform().GetPosition() - pos).Normalized()
					axis_rot = hg.Cross(aZ, target_dir)
					if axis_rot.Len() > 0.001:
						# Rotation matrix:
						rot_mat = MathsSupp.rotate_matrix(mat.GetRotationMatrix(), axis_rot.Normalized(),
														  self.moment_speed * dts)
						self.parent_node.GetTransform().SetRotationMatrix(rot_mat)

				# Collision
				if self.target is not None:
					spd = self.v_move.Len()
					hit, impact = scene.GetPhysicSystem().Raycast(pos, self.v_move.Normalized(), 0x255, spd)
					if hit:
						if impact.GetNode() == target_node:
							v_impact = impact.GetPosition() - pos
							if v_impact.Len() < 2 * spd * dts:
								self.start_explosion()
								self.target.hit(0.35)
				if pos.y < 0:
					self.start_explosion()
				self.update_smoke(pos, dts)

				level = MathsSupp.get_sound_distance_level(scene.GetCurrentCamera().GetTransform().GetPosition(),
														   self.parent_node.GetTransform().GetPosition())
				self.turbine_settings.volume = level
				self.audio.SetChannelState(self.turbine_channel, self.turbine_settings)

			else:
				pos = self.parent_node.GetTransform().GetPosition()
				self.explode.update_kinetics(pos, hg.Vector3.Front, self.v_move, hg.Vector3.Up, dts)
				if self.smoke_time < 0:
					self.update_smoke(pos, dts)
				if self.explode.end and self.smoke_time >= 0:
					self.activated = False

	def start_explosion(self):
		if not self.wreck:
			self.audio.Stop(self.turbine_channel)
			self.explosion_settings.volume = min(1, self.turbine_settings.volume * 2)
			self.audio.Start(self.audio.LoadSound("assets/sfx/missile_explosion.wav"), self.explosion_settings)
			self.wreck = True
			self.explode.flow = 3000
			self.parent_node.SetEnabled(False)
			self.smoke_time = -self.smoke_delay


# =====================================================================================================
#                                   Machine Gun
# =====================================================================================================

class MachineGun(ParticlesEngine):
	def __init__(self, name, plus, scene):
		ParticlesEngine.__init__(self, name, plus, scene, "assets/weaponry/gun_bullet.geo", 24, hg.Vector3(2, 2, 20),
								 hg.Vector3(20, 20, 100), 0.1, "self_color")

		self.start_speed_range = hg.Vector2(2000, 2000)
		self.delay_range = hg.Vector2(2, 2)
		self.start_offset = 0  # self.start_scale.z
		self.gravity = hg.Vector3.Zero
		self.linear_damping = 0
		self.scale_range = hg.Vector2(1, 1)

		self.bullets_feed_backs = []
		for i in range(self.num_particles):
			fb = ParticlesEngine(self.name + ".fb." + str(i), plus, scene, "assets/feed_backs/bullet_impact.geo", 5,
								 hg.Vector3(1, 1, 1), hg.Vector3(10, 10, 10), 180)
			fb.delay_range = hg.Vector2(1, 1)
			fb.flow = 0
			fb.scale_range = hg.Vector2(1, 3)
			fb.start_speed_range = hg.Vector2(0, 20)
			fb.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., .5, 0.25, 0.25), hg.Color(0.1, 0., 0., 0.)]
			fb.set_rot_range(radians(20), radians(50), radians(10), radians(45), radians(5), radians(15))
			fb.gravity = hg.Vector3(0, 0, 0)
			fb.loop = False
			self.bullets_feed_backs.append(fb)

	def strike(self, i):
		self.particles[i].kill()
		fb = self.bullets_feed_backs[i]
		fb.reset()
		fb.flow = 3000

	def update_kinetics(self, scene, targets, position: hg.Vector3, direction: hg.Vector3, v0: hg.Vector3,
						axisY: hg.Vector3, dts):
		ParticlesEngine.update_kinetics(self, position, direction, v0, axisY, dts)
		for i in range(self.num_particles):
			bullet = self.particles[i]
			mat = bullet.node.GetTransform().GetWorld()
			pos_fb = mat.GetTranslation()
			pos = mat.GetTranslation() - mat.GetZ()

			if bullet.node.GetEnabled():
				spd = bullet.v_move.Len()
				if pos_fb.y < 1:
					bullet.v_move *= 0
					self.strike(i)
				hit, impact = scene.GetPhysicSystem().Raycast(pos, bullet.v_move.Normalized(), 0x255, spd)
				if hit:
					if (impact.GetPosition() - pos).Len() < spd * dts * 2:
						for target in targets:
							if target.get_parent_node() == impact.GetNode():
								target.hit(0.1)
								bullet.v_move = target.v_move
								self.strike(i)
			fb = self.bullets_feed_backs[i]
			if not fb.end and fb.flow > 0:
				fb.update_kinetics(pos_fb, hg.Vector3.Front, bullet.v_move, hg.Vector3.Up, dts)


# =====================================================================================================
#                                   Aircraft
# =====================================================================================================

class Aircraft(Destroyable_Machine):
	main_node = None

	def __init__(self, name, nationality, id_string, plus, scene, start_position: hg.Vector3,
				 start_rotation=hg.Vector3.Zero):
		self.name = name
		self.id_string = id_string

		Destroyable_Machine.__init__(self, scene.GetNode("dummy_" + id_string + "_fuselage"),
									 Destroyable_Machine.TYPE_AIRCRAFT, nationality)
		self.wing_l = scene.GetNode("dummy_" + id_string + "_configurable_wing_l")
		self.wing_r = scene.GetNode("dummy_" + id_string + "_configurable_wing_r")
		self.aileron_l = scene.GetNode("dummy_" + id_string + "_aileron_l")
		self.aileron_r = scene.GetNode("dummy_" + id_string + "_aileron_r")
		self.elevator_l = scene.GetNode("dummy_" + id_string + "_elevator_changepitch_l")
		self.elevator_r = scene.GetNode("dummy_" + id_string + "_elevator_changepitch_r")
		self.rudder_l = scene.GetNode(id_string + "_rudder_changeyaw_l")
		self.rudder_r = scene.GetNode(id_string + "_rudder_changeyaw_r")

		self.wings_max_angle = 45
		self.wings_level = 0
		self.wings_thresholds = hg.Vector2(500, 750)
		self.wings_geometry_gain_friction = -0.0001

		for nd in scene.GetNodes():
			if nd.GetName().split("_")[0] == "dummy":
				nd.RemoveComponent(nd.GetObject())

		self.start_position = start_position
		self.start_rotation = start_rotation
		self.thrust_level = 0
		self.thrust_force = 10
		self.post_combution = False
		self.post_combution_force = self.thrust_force / 2

		self.angular_frictions = hg.Vector3(0.000175, 0.000125, 0.000275)  # pitch, yaw, roll
		self.speed_ceiling = 1750  # maneuverability is not guaranteed beyond this speed !
		self.angular_levels = hg.Vector3(0, 0, 0)  # 0 to 1
		self.angular_levels_dest = hg.Vector3(0, 0, 0)
		self.angular_levels_inertias = hg.Vector3(3, 3, 3)
		self.parts_angles = hg.Vector3(radians(15), radians(45), radians(45))
		self.angular_speed = hg.Vector3(0, 0, 0)

		self.drag_coeff = hg.Vector3(0.033, 0.06666, 0.0002)
		self.wings_lift = 0.0005
		self.brake_level = 0
		self.brake_drag = 0.006
		self.flaps_level = 0
		self.flaps_lift = 0.0025
		self.flaps_drag = 0.002

		self.flag_easy_steering = True

		# Physic parameters:
		self.F_gravity = hg.Vector3(0, -9.8, 0)
		self.air_density = 1.225  # Pour plus de réalisme, à modifier en fonction de l'altitude

		# collisions:
		self.rigid, self.rigid_wing_r, self.rigid_wing_l, self.collisions = self.get_collisions(scene)

		self.flag_landed = True

		# Missiles:
		self.missiles_slots = self.get_missiles_slots(scene)
		self.missiles = [None] * 4
		self.missiles_started = []

		self.targets = []
		self.target_id = 0
		self.target_lock_range = hg.Vector2(100, 3000)  # Target lock distance range
		self.target_lock_delay = hg.Vector2(1, 5)  # Target lock delay in lock range
		self.target_lock_t = 0
		self.target_locking_state = 0  # 0 to 1
		self.target_locked = False
		self.target_out_of_range = False
		self.target_distance = 0
		self.target_cap = 0
		self.target_altitude = 0
		self.target_angle = 0

		# Gun machine:
		self.gun_position = hg.Vector3(0, -0.65, 9.8)
		self.gun_machine = MachineGun(self.name + ".gun", plus, scene)

		# Feed-backs:
		self.explode = ParticlesEngine(self.name + ".explode", plus, scene, "assets/feed_backs/feed_back_explode.geo",
									   100, hg.Vector3(10, 10, 10), hg.Vector3(100, 100, 100), 180)
		self.explode.delay_range = hg.Vector2(1, 4)
		self.explode.flow = 0
		self.explode.scale_range = hg.Vector2(0.25, 2)
		self.explode.start_speed_range = hg.Vector2(0, 100)
		self.explode.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0., 0., 0.5), hg.Color(.5, .5, .5, 0.25),
							   hg.Color(0., 0., 0., 0.125), hg.Color(0., 0., 0., 0.0)]
		self.explode.set_rot_range(radians(20), radians(50), radians(10), radians(45), radians(5), radians(15))
		self.explode.gravity = hg.Vector3(0, -9.8, 0)
		self.explode.loop = False

		self.smoke = ParticlesEngine(self.name + ".smoke", plus, scene, "assets/feed_backs/feed_back_explode.geo", 400,
									 hg.Vector3(5, 5, 5), hg.Vector3(50, 50, 50), 180)
		self.smoke.delay_range = hg.Vector2(4, 8)
		self.smoke.flow = 0
		self.smoke.scale_range = hg.Vector2(0.1, 5)
		self.smoke.start_speed_range = hg.Vector2(5, 15)
		self.smoke.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0., 0., 0.3), hg.Color(.7, .7, .7, 0.2),
							 hg.Color(.0, .0, .0, 0.1), hg.Color(0., 0., 0., 0.05), hg.Color(0., 0., 0., 0)]
		self.smoke.set_rot_range(0, 0, radians(120), radians(120), 0, 0)
		self.smoke.gravity = hg.Vector3(0, 30, 0)
		self.smoke.linear_damping = 0.5
		self.smoke.loop = True

		self.engines_position = [hg.Vector3(1.56887, -0.14824, -6.8), hg.Vector3(-1.56887, -0.14824, -6.8)]
		self.pc_r = self.create_post_combustion_particles(plus, scene, ".pcr")
		self.pc_l = self.create_post_combustion_particles(plus, scene, ".pcl")

		self.destroyable_targets = []

		# Linear acceleration:
		self.linear_acceleration = 0
		self.linear_speeds = [0] * 10
		self.linear_spd_rec_cnt = 0

		# Attitudes calculation:
		self.horizontal_aX = None
		self.horizontal_aY = None
		self.horizontal_aZ = None
		self.pitch_attitude = 0
		self.roll_attitude = 0
		self.y_dir = 1

		self.cap = 0

		# IA
		self.IA_activated = False
		self.IA_fire_missiles_delay = 10
		self.IA_fire_missile_cptr = 0
		self.IA_flag_altitude_correction = False
		self.IA_altitude_min = 500
		self.IA_altitude_safe = 2000
		self.IA_gun_distance_max = 1000
		self.IA_gun_angle = 10
		self.IA_cruising_altitude = 3000

		# Autopilot (used by IA)
		self.autopilot_activated = False
		self.autopilot_altitude = 1000
		self.autopilot_cap = 0
		self.autopilot_pitch_attitude = 0
		self.autopilot_roll_attitude = 0

		self.reset()

	def create_post_combustion_particles(self, plus, scene, engine_name):
		pc = ParticlesEngine(self.name + engine_name, plus, scene, "assets/feed_backs/bullet_impact.geo", 15,
							 hg.Vector3(1, 1, 1), hg.Vector3(0.2, 0.2, 0.2), 15)
		pc.delay_range = hg.Vector2(0.3, 0.4)
		pc.flow = 0
		pc.scale_range = hg.Vector2(1, 1)
		pc.start_speed_range = hg.Vector2(1, 1)
		pc.colors = [hg.Color(1., 1., 1., 1), hg.Color(1., 0.9, 0.7, 0.5), hg.Color(0.9, 0.7, 0.1, 0.25),
					 hg.Color(0.9, 0.5, 0., 0.), hg.Color(0.85, 0.5, 0., 0.25), hg.Color(0.8, 0.4, 0., 0.15),
					 hg.Color(0.8, 0.1, 0.1, 0.05), hg.Color(0.5, 0., 0., 0.)]
		pc.set_rot_range(radians(1200), radians(2200), radians(1420), radians(1520), radians(1123), radians(5120))
		pc.gravity = hg.Vector3(0, 0, 0)
		pc.linear_damping = 0
		pc.loop = True
		return pc

	def set_destroyable_targets(self, targets):
		self.destroyable_targets = targets

	def hit(self, value):
		if not self.wreck:
			self.set_health_level(self.health_level - value)
			if self.health_level == 0 and not self.wreck:
				self.start_explosion()
				self.set_thrust_level(0)

	def get_missiles_slots(self, scene):
		slots = []
		# slots=[hg.Vector3(0,0,0),hg.Vector3(0,0,0),hg.Vector3(0,0,0),hg.Vector3(0,0,0)]
		# return slots
		for i in range(4):
			nd = scene.GetNode("dummy_" + self.id_string + "_slot." + str(i + 1))
			slots.append(nd.GetTransform().GetPosition())  # scene.RemoveNode(nd)
		return slots

	def get_collisions(self, scene):
		rigid, rigid_wing_r, rigid_wing_l = hg.RigidBody(), hg.RigidBody(), hg.RigidBody()
		rigid.SetType(hg.RigidBodyKinematic)
		rigid_wing_r.SetType(hg.RigidBodyKinematic)
		rigid_wing_l.SetType(hg.RigidBodyKinematic)
		self.parent_node.AddComponent(rigid)
		self.wing_l.AddComponent(rigid_wing_l)
		self.wing_r.AddComponent(rigid_wing_r)
		collisions_nodes = []
		for nd in scene.GetNodes():
			if nd.GetName().find(self.id_string + "_col_shape") >= 0:
				collisions_nodes.append(nd)
		collisions_boxes = []
		for col_shape in collisions_nodes:
			colbox = hg.BoxCollision()
			collisions_boxes.append(colbox)
			obj = col_shape.GetObject()
			bounds = obj.GetLocalMinMax()
			dimensions = bounds.mx - bounds.mn
			pos = col_shape.GetTransform().GetPosition() + bounds.mn + dimensions * 0.5
			colbox.SetDimensions(dimensions)
			colbox.SetMatrix(hg.Matrix4.TranslationMatrix(pos))
			if col_shape.GetName().find("wing_l") >= 0:
				self.wing_l.AddComponent(colbox)
			elif col_shape.GetName().find("wing_r") >= 0:
				self.wing_r.AddComponent(colbox)
			else:
				self.parent_node.AddComponent(colbox)
			scene.RemoveNode(col_shape)
		return rigid, rigid_wing_r, rigid_wing_l, collisions_boxes

	def reset(self, position=None, rotation=None):
		if position is not None:
			self.start_position = position
		if rotation is not None:
			self.start_rotation = rotation
		self.parent_node.GetTransform().SetPosition(self.start_position)
		self.parent_node.GetTransform().SetRotation(self.start_rotation)

		self.v_move = hg.Vector3(0, 0, 0)
		self.angular_levels = hg.Vector3(0, 0, 0)
		self.set_thrust_level(0)
		self.deactivate_post_combution()
		self.flaps_level = 0
		self.brake_level = 0

		self.missiles = [None] * 4
		self.missiles_started = []

		if self.gun_machine is not None:
			self.gun_machine.reset()
			self.gun_machine.flow = 0

		self.smoke.reset()
		self.explode.reset()
		self.wreck = False
		self.activated = True
		self.explode.flow = 0
		self.set_health_level(1)
		self.target_id = 0
		self.target_lock_t = 0
		self.target_locked = False
		self.target_out_of_range = False
		self.target_locking_state = 0

		self.linear_speeds = [0] * 10

	def get_world_speed(self):
		sX = hg.Vector3.Right * (hg.Dot(hg.Vector3.Right, self.v_move))
		sZ = hg.Vector3.Front * (hg.Dot(hg.Vector3.Front, self.v_move))
		vs = hg.Dot(hg.Vector3.Up, self.v_move)
		hs = (sX + sZ).Len()
		return hs, vs

	def set_linear_speed(self, value):
		aZ = self.parent_node.GetTransform().GetWorld().GetZ()
		self.v_move = aZ * value

	def get_linear_speed(self):
		return self.v_move.Len()

	def get_altitude(self):
		return self.parent_node.GetTransform().GetPosition().y

	def set_thrust_level(self, value):
		self.thrust_level = min(max(value, 0), 1)
		if self.thrust_level < 1: self.deactivate_post_combution()

	def set_health_level(self, value):
		self.health_level = min(max(value, 0), 1)
		if self.health_level < 1:
			self.smoke.flow = 40
		else:
			self.smoke.flow = 0
		self.smoke.delay_range = hg.Vector2(1, 10) * pow(1 - self.health_level, 3)
		self.smoke.scale_range = hg.Vector2(0.1, 5) * pow(1 - self.health_level, 3)
		self.smoke.stream_angle = pow(1 - self.health_level, 2.6) * 180

	def start_explosion(self):
		self.wreck = True
		self.explode.flow = 500

	def set_wings_level(self, value):
		self.wings_level = min(max(value, 0), 1)
		rot = self.wing_l.GetTransform().GetRotation()
		rot.y = -radians(self.wings_max_angle * self.wings_level)
		self.wing_l.GetTransform().SetRotation(rot)

		rot = self.wing_r.GetTransform().GetRotation()
		rot.y = radians(self.wings_max_angle * self.wings_level)
		self.wing_r.GetTransform().SetRotation(rot)

	def set_brake_level(self, value):
		self.brake_level = min(max(value, 0), 1)

	def set_flaps_level(self, value):
		self.flaps_level = min(max(value, 0), 1)

	def set_pitch_level(self, value):
		self.angular_levels_dest.x = max(min(1, value), -1)

	def set_yaw_level(self, value):
		self.angular_levels_dest.y = max(min(1, value), -1)

	def set_roll_level(self, value):
		self.angular_levels_dest.z = max(min(1, value), -1)

	def set_autopilot_pitch_attitude(self, value):
		self.autopilot_pitch_attitude = max(min(180, value), -180)

	def set_autopilot_roll_attitude(self, value):
		self.autopilot_roll_attitude = max(min(180, value), -180)

	def set_autopilot_cap(self, value):
		self.autopilot_cap = max(min(360, value), 0)

	def set_autopilot_altitude(self, value):
		self.autopilot_altitude = value

	def update_inertial_value(self, v0, vd, vi, dts):
		vt = vd - v0
		if vt < 0:
			v = v0 - vi * dts
			if v < vd: v = vd
		elif vt > 0:
			v = v0 + vi * dts
			if v > vd: v = vd
		else:
			v = vd
		return v

	def update_angular_levels(self, dts):
		self.angular_levels.x = self.update_inertial_value(self.angular_levels.x, self.angular_levels_dest.x,
														   self.angular_levels_inertias.x, dts)
		self.angular_levels.y = self.update_inertial_value(self.angular_levels.y, self.angular_levels_dest.y,
														   self.angular_levels_inertias.y, dts)
		self.angular_levels.z = self.update_inertial_value(self.angular_levels.z, self.angular_levels_dest.z,
														   self.angular_levels_inertias.z, dts)

	def stabilize(self, dts, p, y, r):
		if p: self.set_pitch_level(0)
		if y: self.set_yaw_level(0)
		if r: self.set_roll_level(0)

	def activate_post_combution(self):
		if self.thrust_level == 1:
			self.post_combution = True
			self.pc_r.flow = 35
			self.pc_l.flow = 35

	def deactivate_post_combution(self):
		self.post_combution = False
		self.pc_r.flow = 0
		self.pc_l.flow = 0

	def fire_gun_machine(self):
		if not self.wreck:
			self.gun_machine.flow = 24 / 2

	def stop_gun_machine(self):
		self.gun_machine.flow = 0

	def is_gun_activated(self):
		if self.gun_machine.flow == 0:
			return False
		else:
			return True

	def update_mobile_parts(self):
		self.elevator_l.GetTransform().SetRotation(hg.Vector3(-self.parts_angles.x * self.angular_levels.x, 0, 0))
		self.elevator_r.GetTransform().SetRotation(hg.Vector3(-self.parts_angles.x * self.angular_levels.x, 0, 0))

		rot_l, rot_r = self.rudder_l.GetTransform().GetRotation(), self.rudder_r.GetTransform().GetRotation()
		rot_l.y = self.parts_angles.y * self.angular_levels.y + pi
		rot_r.y = -self.parts_angles.y * self.angular_levels.y
		self.rudder_l.GetTransform().SetRotation(rot_l)
		self.rudder_r.GetTransform().SetRotation(rot_r)

		rot_l, rot_r = self.aileron_l.GetTransform().GetRotation(), self.aileron_r.GetTransform().GetRotation()
		rot_l.x = -self.parts_angles.z * self.angular_levels.z
		rot_r.x = -self.parts_angles.z * self.angular_levels.z
		self.aileron_l.GetTransform().SetRotation(rot_l)
		self.aileron_r.GetTransform().SetRotation(rot_r)

	def rec_linear_speed(self):
		self.linear_speeds[self.linear_spd_rec_cnt] = self.v_move.Len()
		self.linear_spd_rec_cnt += 1
		if self.linear_spd_rec_cnt >= len(self.linear_speeds):
			self.linear_spd_rec_cnt = 0

	def update_linear_acceleration(self):
		m = 0
		for s in self.linear_speeds:
			m += s
		m /= len(self.linear_speeds)
		self.linear_acceleration = self.v_move.Len() - m

	def get_linear_acceleration(self):
		return self.linear_acceleration

	def update_post_combustion_particles(self, dts, pos, rot_mat):
		self.pc_r.update_kinetics(self.engines_position[0] * rot_mat + pos, rot_mat.GetZ() * -1, self.v_move,
								  rot_mat.GetY(), dts)
		self.pc_l.update_kinetics(self.engines_position[1] * rot_mat + pos, rot_mat.GetZ() * -1, self.v_move,
								  rot_mat.GetY(), dts)

	def update_IA(self, dts):
		alt = self.get_altitude()
		if self.target_id > 0:
			self.set_autopilot_cap(self.target_cap)
			if self.IA_flag_altitude_correction:
				self.set_autopilot_altitude(self.IA_altitude_safe)
				if self.IA_altitude_safe - 100 < alt < self.IA_altitude_safe + 100:
					self.IA_flag_altitude_correction = False
			else:
				self.set_autopilot_altitude(self.target_altitude)
				if alt < self.IA_altitude_min:
					self.IA_flag_altitude_correction = True

			if self.target_locked:
				if self.IA_fire_missile_cptr <= 0:
					self.fire_missile()
					self.IA_fire_missile_cptr = self.IA_fire_missiles_delay
				if self.IA_fire_missile_cptr > 0:
					self.IA_fire_missile_cptr -= dts

			if self.target_angle < self.IA_gun_angle and self.target_distance < self.IA_gun_distance_max:
				self.fire_gun_machine()
			else:
				self.stop_gun_machine()

		else:
			self.set_autopilot_altitude(self.IA_cruising_altitude)
			self.set_autopilot_cap(0)
			self.stop_gun_machine()

		if self.pitch_attitude > 15:
			self.set_thrust_level(1)
			self.activate_post_combution()
		elif -15 < self.pitch_attitude < 15:
			self.deactivate_post_combution()
			self.set_thrust_level(1)
		else:
			self.deactivate_post_combution()
			self.set_thrust_level(0.5)

	def update_autopilot(self, dts):
		# straighten aircraft:
		if self.y_dir < 0:
			self.set_roll_level(0)
			self.set_pitch_level(0)
			self.set_yaw_level(0)
		else:
			# cap / roll_attitude:
			diff = self.autopilot_cap - self.cap
			if diff > 180:
				diff -= 360
			elif diff < -180:
				diff += 360

			tc = max(-1, min(1, -diff / 90))
			if tc < 0:
				tc = -pow(-tc, 0.5)
			else:
				tc = pow(tc, 0.5)
			self.set_autopilot_roll_attitude(tc * 85)

			diff = self.autopilot_roll_attitude - self.roll_attitude
			tr = max(-1, min(1, diff / 20))
			self.set_roll_level(tr)

			# altitude / pitch_attitude:
			diff = self.autopilot_altitude - self.get_altitude()
			ta = max(-1, min(1, diff / 500))

			if ta < 0:
				ta = -pow(-ta, 0.7)
			else:
				ta = pow(ta, 0.7)

			self.set_autopilot_pitch_attitude(ta * 45)

			diff = self.autopilot_pitch_attitude - self.pitch_attitude
			tp = max(-1, min(1, diff / 10))
			self.set_pitch_level(-tp)

	def calculate_cap(self, h_dir: hg.Vector3):
		cap = degrees(acos(max(-1, min(1, hg.Dot(h_dir, hg.Vector3.Front)))))
		if h_dir.x < 0: cap = 360 - cap
		return cap

	def update_kinetics(self, scene, dts):
		if self.activated:
			#                               AJOUTER UNE CONDITION SI WRECK = TRUE (CRASH EN PIQUE + ROTATION AXEZ)
			#                               Meshe de substitution ?

			if self.IA_activated:
				self.update_IA(dts)
			if self.autopilot_activated or self.IA_activated:
				self.update_autopilot(dts)

			self.update_angular_levels(dts)
			self.update_mobile_parts()

			mat = self.parent_node.GetTransform().GetWorld()
			aX = mat.GetX()
			aY = mat.GetY()
			aZ = mat.GetZ()

			# Cap, Pitch & Roll attitude:
			if aY.y > 0:
				self.y_dir = 1
			else:
				self.y_dir = -1

			self.horizontal_aZ = hg.Vector3(aZ.x, 0, aZ.z).Normalized()
			self.horizontal_aX = hg.Cross(hg.Vector3.Up, self.horizontal_aZ) * self.y_dir
			self.horizontal_aY = hg.Cross(aZ, self.horizontal_aX)  # ! It's not an orthogonal repere !

			self.pitch_attitude = degrees(acos(max(-1, min(1, hg.Dot(self.horizontal_aZ, aZ)))))
			if aZ.y < 0: self.pitch_attitude *= -1

			self.roll_attitude = degrees(acos(max(-1, min(1, hg.Dot(self.horizontal_aX, aX)))))
			if aX.y < 0: self.roll_attitude *= -1

			self.cap = self.calculate_cap(self.horizontal_aZ)

			# axis speed:
			spdX = aX * hg.Dot(aX, self.v_move)
			spdY = aY * hg.Dot(aY, self.v_move)
			spdZ = aZ * hg.Dot(aZ, self.v_move)

			frontal_speed = spdZ.Len()

			# wings_geometry:
			self.set_wings_level(max(min(
				(frontal_speed * 3.6 - self.wings_thresholds.x) / (self.wings_thresholds.y - self.wings_thresholds.x),
				1), 0))

			# Thrust force:
			k = pow(self.thrust_level, 2) * self.thrust_force
			if self.post_combution and self.thrust_level == 1:
				k += self.post_combution_force
			F_thrust = mat.GetZ() * k

			# Dynamic pressure:
			q = hg.Vector3(pow(spdX.Len(), 2), pow(spdY.Len(), 2), pow(spdZ.Len(), 2)) * 0.5 * self.air_density

			# F Lift
			F_lift = aY * q.z * (self.wings_lift + self.flaps_level * self.flaps_lift)

			# Drag force:
			F_drag = spdX.Normalized() * q.x * self.drag_coeff.x + spdY.Normalized() * q.y * self.drag_coeff.y + spdZ.Normalized() * q.z * (
					self.drag_coeff.z + self.brake_drag * self.brake_level + self.flaps_level * self.flaps_drag + self.wings_geometry_gain_friction * self.wings_level)

			# Total
			self.v_move += ((F_thrust + F_lift - F_drag) * self.health_level + self.F_gravity) * dts

			# Displacement:
			pos = mat.GetTranslation()
			pos += self.v_move * dts

			# Rotations:
			F_pitch = self.angular_levels.x * q.z * self.angular_frictions.x
			F_yaw = self.angular_levels.y * q.z * self.angular_frictions.y
			F_roll = self.angular_levels.z * q.z * self.angular_frictions.z

			# Angular damping:
			gaussian = exp(-pow(frontal_speed * 3.6 * 3 / self.speed_ceiling, 2) / 2)

			# Angular speed:
			self.angular_speed = hg.Vector3(F_pitch, F_yaw, F_roll) * gaussian

			# Moment:
			pitch_m = aX * self.angular_speed.x
			yaw_m = aY * self.angular_speed.y
			roll_m = aZ * self.angular_speed.z

			# Easy steering:
			if self.flag_easy_steering or self.autopilot_activated:

				easy_yaw_angle = (1 - (hg.Dot(aX, self.horizontal_aX)))
				if hg.Dot(aZ, hg.Cross(aX, self.horizontal_aX)) < 0:
					easy_turn_m_yaw = self.horizontal_aY * -easy_yaw_angle
				else:
					easy_turn_m_yaw = self.horizontal_aY * easy_yaw_angle

				easy_roll_stab = hg.Cross(aY, self.horizontal_aY) * self.y_dir
				if self.y_dir < 0:
					easy_roll_stab.Normalize()
				else:
					n = easy_roll_stab.Len()
					if n > 0.1:
						easy_roll_stab.Normalize()
						easy_roll_stab *= (1 - n) * n + n * pow(n, 0.125)

				zl = min(1, abs(self.angular_levels.z + self.angular_levels.x + self.angular_levels.y))
				roll_m += (easy_roll_stab * (1 - zl) + easy_turn_m_yaw) * q.z * self.angular_frictions.y * gaussian

			# Moment:
			moment = yaw_m + roll_m + pitch_m
			axis_rot = moment.Normalized()
			moment_speed = moment.Len() * self.health_level

			# Rotation matrix:
			rot_mat = MathsSupp.rotate_matrix(mat.GetRotationMatrix(), axis_rot, moment_speed * dts)
			self.parent_node.GetTransform().SetRotationMatrix(rot_mat)

			# Ground collisions:
			self.flag_landed = False
			self.ground_ray_cast_pos = pos - aY
			self.ground_ray_cast_dir = aY * -1
			hit, impact = scene.GetPhysicSystem().Raycast(self.ground_ray_cast_pos, self.ground_ray_cast_dir, 0x255,
														  self.ground_ray_cast_length)
			if hit and impact.GetNode() != self.parent_node:
				i_pos = impact.GetPosition()
				alt = i_pos.y + 2
			else:
				alt = 4
			if pos.y < alt:
				if degrees(abs(asin(aZ.y))) < 15 and degrees(abs(asin(aX.y))) < 10 and frontal_speed * 3.6 < 300:

					pos.y += (alt - pos.y) * 0.1 * 60 * dts
					if self.v_move.y < 0: self.v_move.y *= pow(0.8, 60 * dts)
					b = min(1, self.brake_level + (1 - self.health_level))
					self.v_move *= ((b * pow(0.8, 60 * dts)) + (1 - b))
					self.flag_landed = True
				else:
					pos.y = alt
					self.hit(1)
					self.v_move *= pow(0.9, 60 * dts)

			self.parent_node.GetTransform().SetPosition(pos)

			# Gun:
			self.gun_machine.update_kinetics(scene, self.destroyable_targets, rot_mat * self.gun_position + pos, aZ,
											 self.v_move, aY, dts)
			# Missiles:
			self.update_target_lock(dts)
			for missile in self.missiles_started:
				missile.update_kinetics(scene, dts)

			# Feed backs:
			if self.health_level < 1:
				self.smoke.update_kinetics(pos, aZ * -1, self.v_move, aY,
										   dts)  # AJOUTER UNE DUREE LIMITE AU FOURNEAU LORSQUE WRECK=TRUE !
			if self.wreck and not self.explode.end:
				self.explode.update_kinetics(pos, aZ * -1, self.v_move, aY, dts)

			self.update_post_combustion_particles(dts, pos, rot_mat)

			self.rec_linear_speed()
			self.update_linear_acceleration()

	def update_target_lock(self, dts):
		if self.target_id > 0:
			target = self.targets[self.target_id - 1]
			if target.wreck or not target.activated:
				self.next_target()
				if self.target_id == 0:
					return
			t_pos = self.targets[self.target_id - 1].get_parent_node().GetTransform().GetPosition()
			mat = self.parent_node.GetTransform().GetWorld()
			dir = mat.GetZ()
			v = t_pos - mat.GetTranslation()
			self.target_cap = self.calculate_cap((v * hg.Vector3(1, 0, 1)).Normalized())
			self.target_altitude = t_pos.y
			self.target_distance = v.Len()
			t_dir = v.Normalized()
			self.target_angle = degrees(acos(max(-1, min(1, hg.Dot(dir, t_dir)))))
			if self.target_angle < 15 and self.target_lock_range.x < self.target_distance < self.target_lock_range.y:
				t = (self.target_distance - self.target_lock_range.x) / (
						self.target_lock_range.y - self.target_lock_range.x)
				delay = self.target_lock_delay.x + t * (self.target_lock_delay.y - self.target_lock_delay.x)
				self.target_out_of_range = False
				self.target_lock_t += dts
				self.target_locking_state = min(1, self.target_lock_t / delay)
				if self.target_lock_t >= delay:
					self.target_locked = True
			else:
				self.target_locked = False
				self.target_lock_t = 0
				self.target_out_of_range = True
				self.target_locking_state = 0

	def fit_missile(self, missile: Missile, slot_id):
		nd = missile.get_parent_node()
		nd.GetTransform().SetParent(self.parent_node)
		missile.reset(self.missiles_slots[slot_id], hg.Vector3(0, 0, 0))
		self.missiles[slot_id] = missile

	def set_target_id(self, id):
		self.target_id = id
		if id > 0:
			if self.targets is None or len(self.targets) == 0:
				self.target_id = 0
			target = self.targets[id - 1]
			if target.wreck or not target.activated:
				self.next_target()

	def next_target(self):
		if self.targets is not None:
			self.target_locked = False
			self.target_lock_t = 0
			self.target_locking_state = 0
			self.target_id += 1
			if self.target_id > len(self.targets):
				self.target_id = 0
				return
			t = self.target_id
			target = self.targets[t - 1]
			if target.wreck or not target.activated:
				while target.wreck or not target.activated:
					self.target_id += 1
					if self.target_id > len(self.targets):
						self.target_id = 1
					if self.target_id == t:
						self.target_id = 0
						break
					target = self.targets[self.target_id - 1]

	def get_target(self):
		if self.target_id > 0:
			return self.targets[self.target_id - 1]
		else:
			return None

	def fire_missile(self):
		if not self.wreck:
			for i in range(len(self.missiles)):
				missile = self.missiles[i]
				if missile is not None:
					self.missiles[i] = None
					trans = missile.get_parent_node().GetTransform()
					mat = trans.GetWorld()
					trans.SetParent(Aircraft.main_node)
					trans.SetWorld(mat)
					if self.target_locked:
						target = self.targets[self.target_id - 1]
					else:
						target = None
					missile.start(target, self.v_move)
					self.missiles_started.append(missile)
					break


class AircraftSFX:
	def __init__(self, aircraft: Aircraft):
		self.aircraft = aircraft

		self.turbine_pitch_levels = hg.Vector2(1, 2)
		self.turbine_settings = hg.MixerChannelState(0, 0, hg.MixerRepeat)
		self.air_settings = hg.MixerChannelState(0, 0, hg.MixerRepeat)
		self.pc_settings = hg.MixerChannelState(0, 0, hg.MixerRepeat)
		self.wind_settings = hg.MixerChannelState(0, 0, hg.MixerRepeat)
		self.explosion_settings = hg.MixerChannelState(0, 0, hg.MixerNoLoop)
		self.machine_gun_settings = hg.MixerChannelState(0, 0, hg.MixerNoLoop)
		self.start = False

		self.pc_cptr = 0
		self.pc_start_delay = 0.25
		self.pc_stop_delay = 0.5

		self.turbine_chan = 0
		self.wind_chan = 0
		self.air_chan = 0
		self.pc_chan = 0
		self.pc_started = False
		self.pc_stopped = False

		self.exploded = False

	def reset(self):
		self.exploded = False

	def set_air_pitch(self, value):
		self.air_settings.pitch = value

	def set_pc_pitch(self, value):
		self.pc_settings.pitch = value

	def set_turbine_pitch_levels(self, values: hg.Vector2):
		self.turbine_pitch_levels = values

	def start_engine(self, main):
		self.turbine_settings.volume = 0
		self.turbine_settings.pitch = 1
		self.air_settings.volume = 0
		self.pc_settings.volume = 0
		self.air_chan = main.audio.Start(main.audio.LoadSound("assets/sfx/air.wav"), self.air_settings)
		self.turbine_chan = main.audio.Start(main.audio.LoadSound("assets/sfx/turbine.wav"), self.turbine_settings)
		self.pc_chan = main.audio.Start(main.audio.LoadSound("assets/sfx/post_combustion.wav"), self.pc_settings)
		self.start = True
		self.pc_started = False
		self.pc_stopped = True
		if self.wind_chan > 0:
			main.audio.Stop(self.wind_chan)

	def stop_engine(self, main):
		self.turbine_settings.volume = 0
		self.turbine_settings.pitch = 1
		self.air_settings.volume = 0
		self.pc_settings.volume = 0
		main.audio.Stop(self.turbine_chan)
		main.audio.Stop(self.air_chan)
		main.audio.Stop(self.pc_chan)

		self.start = False
		self.pc_started = False
		self.pc_stopped = True

		self.wind_settings.volume = 0
		self.wind_chan = main.audio.Start(main.audio.LoadSound("assets/sfx/wind.wav"), self.wind_settings)

	def update_sfx(self, main, dts):

		level = MathsSupp.get_sound_distance_level(main.camera.GetTransform().GetWorld().GetTranslation(),
												   self.aircraft.get_parent_node().GetTransform().GetPosition())

		if self.aircraft.thrust_level > 0 and not self.start:
			self.start_engine(main)

		if self.aircraft.wreck and not self.exploded:
			self.explosion_settings.volume = level
			main.audio.Start(main.audio.LoadSound("assets/sfx/explosion.wav"), self.explosion_settings)
			self.exploded = True

		if self.start:
			if self.aircraft.thrust_level <= 0:
				self.stop_engine(main)

			else:
				self.turbine_settings.volume = 0.5 * level
				self.turbine_settings.pitch = self.turbine_pitch_levels.x + self.aircraft.thrust_level * (
						self.turbine_pitch_levels.y - self.turbine_pitch_levels.x)
				self.air_settings.volume = (0.1 + self.aircraft.thrust_level * 0.9) * level

				main.audio.SetChannelState(self.turbine_chan, self.turbine_settings)
				main.audio.SetChannelState(self.air_chan, self.air_settings)

				if self.aircraft.post_combution:
					self.pc_settings.volume = level
					if not self.pc_started:
						self.pc_stopped = False
						self.pc_settings.volume *= self.pc_cptr / self.pc_start_delay
						self.pc_cptr += dts
						if self.pc_cptr >= self.pc_start_delay:
							self.pc_started = True
							self.pc_cptr = 0
					main.audio.SetChannelState(self.pc_chan, self.pc_settings)
				else:
					if not self.pc_stopped:
						self.pc_started = False
						self.pc_settings.volume = (1 - self.pc_cptr / self.pc_stop_delay) * level
						main.audio.SetChannelState(self.pc_chan, self.pc_settings)
						self.pc_cptr += dts
						if self.pc_cptr >= self.pc_stop_delay:
							self.pc_stopped = True
							self.pc_cptr = 0
		else:
			f = min(1, self.aircraft.get_linear_speed() * 3.6 / 1000)
			self.wind_settings.volume = f * level
			main.audio.SetChannelState(self.wind_chan, self.wind_settings)

		# Machine gun
		if self.aircraft.gun_machine.num_new > 0:
			self.machine_gun_settings.volume = level * 0.5
			self.wind_chan = main.audio.Start(main.audio.LoadSound("assets/sfx/machine_gun.wav"),
											  self.machine_gun_settings)


# =====================================================================================================
#                                   Aircraft-carrier
# =====================================================================================================

class Carrier(Destroyable_Machine):
	def __init__(self, name, nationality, plus, scene):
		self.name = name
		Destroyable_Machine.__init__(self, scene.GetNode("aircraft_carrier"), Destroyable_Machine.TYPE_SHIP,
									 nationality)
		self.activated = True
		self.parent_node.GetTransform().SetPosition(hg.Vector3(0, 0, 0))
		self.parent_node.GetTransform().SetRotation(hg.Vector3(0, 0, 0))
		self.radar = scene.GetNode("aircraft_carrier_radar")
		self.rigid, self.collisions = self.get_collisions(scene)
		self.aircraft_start_point = scene.GetNode("carrier_aircraft_start_point")
		self.aircraft_start_point.RemoveComponent(self.aircraft_start_point.GetObject())

	def hit(self, value):
		pass

	def update_kinetics(self, scene, dts):
		rot = self.parent_node.GetTransform().GetRotation()
		# print(str(rot.x)+" , "+str(rot.y)+" , "+str(rot.z))
		rot = self.radar.GetTransform().GetRotation()
		rot.y += radians(45 * dts)
		self.radar.GetTransform().SetRotation(rot)

	def get_aircraft_start_point(self):
		mat = self.aircraft_start_point.GetTransform().GetWorld()
		return mat.GetTranslation(), mat.GetRotation()

	def get_collisions(self, scene):
		rigid = hg.RigidBody()
		rigid.SetType(hg.RigidBodyKinematic)
		self.parent_node.AddComponent(rigid)
		collisions_nodes = []
		for nd in scene.GetNodes():
			if nd.GetName().find("carrier_col_shape") >= 0:
				collisions_nodes.append(nd)
		collisions_boxes = []
		for col_shape in collisions_nodes:
			colbox = hg.BoxCollision()
			collisions_boxes.append(colbox)
			obj = col_shape.GetObject()
			bounds = obj.GetLocalMinMax()
			dimensions = bounds.mx - bounds.mn
			pos = col_shape.GetTransform().GetPosition() + bounds.mn + dimensions * 0.5
			colbox.SetDimensions(dimensions)
			colbox.SetMatrix(hg.Matrix4.TranslationMatrix(pos))
			self.parent_node.AddComponent(colbox)
			scene.RemoveNode(col_shape)
		return rigid, collisions_boxes
