# -*-coding:Utf-8 -*

# ===================================================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                      Particles engine

# ====================================================================================

import harfang as hg
from MathsSupp import *
from math import radians, degrees, pi, sqrt, exp
from random import uniform, random
from data_converter import *


class Particle:
	def __init__(self, node: hg.Node):
		self.node = node
		self.age = -1
		self.v_move = hg.Vector3(0, 0, 0)
		self.delay = 0
		self.scale = 1
		self.rot_speed = hg.Vector3(0, 0, 0)

	def kill(self):
		self.age=-1
		self.node.SetEnabled(False)


class ParticlesEngine:
	particle_id = 0

	def __init__(self, name, plus, scene, node_file_name, num_particles, start_scale, end_scale, stream_angle,color_label="teint"):
		self.name = name
		self.color_label=color_label
		self.particles_cnt = 0
		self.particles_cnt_f = 0
		self.num_particles = num_particles
		self.flow = 8
		self.particles_delay = 3
		self.particles = []
		self.create_particles(plus, scene, node_file_name)
		self.start_speed_range = hg.Vector2(800, 1200)
		self.delay_range = hg.Vector2(1, 2)
		self.start_scale = start_scale
		self.end_scale = end_scale
		self.scale_range = hg.Vector2(1,2)
		self.stream_angle = stream_angle
		self.colors = [hg.Color(1, 1, 1, 1), hg.Color(1, 1, 1, 0)]
		self.start_offset = 0
		self.rot_range_x = hg.Vector2(0, 0)
		self.rot_range_y = hg.Vector2(0, 0)
		self.rot_range_z = hg.Vector2(0, 0)
		self.gravity=hg.Vector3(0,-9.8,0)
		self.linear_damping = 1
		self.loop=True
		self.end=False #True when loop=True and all particles are dead
		self.num_new=0
		self.reset()

	def set_rot_range(self,xmin,xmax,ymin,ymax,zmin,zmax):
		self.rot_range_x = hg.Vector2(xmin, xmax)
		self.rot_range_y = hg.Vector2(ymin, ymax)
		self.rot_range_z = hg.Vector2(zmin, zmax)

	def create_particles(self, plus, scene, node_file_name):
		for i in range(self.num_particles):
			node,geo = load_object(plus, node_file_name, self.name + "." + str(i), True)
			particle = Particle(node)
			scene.AddNode(particle.node)
			self.particles.append(particle)

	def reset(self):
		self.num_new = 0
		self.particles_cnt = 0
		self.particles_cnt_f = 0
		self.end=False
		for i in range(self.num_particles):
			self.particles[i].age = -1
			self.particles[i].node.SetEnabled(False)
			self.particles[i].v_move = hg.Vector3(0, 0, 0)

	def get_direction(self, main_dir):
		if self.stream_angle == 0: return main_dir
		axe0 = hg.Vector3(0, 0, 0)
		axeRot = hg.Vector3(0, 0, 0)
		while axeRot.Len() < 1e-4:
			while axe0.Len() < 1e-5:
				axe0 = hg.Vector3(uniform(-1, 1), uniform(-1, 1), uniform(-1, 1))
			axe0.Normalize()
			axeRot = hg.Cross(axe0, main_dir)
		axeRot.Normalize()
		return MathsSupp.rotate_vector(main_dir, axeRot, random() * radians(self.stream_angle))

	def update_color(self, particle: Particle):
		if len(self.colors) == 1:
			c = self.colors[0]
		else:
			c=MathsSupp.get_mix_color_value(particle.age / particle.delay,self.colors)
		particle.node.GetObject().GetGeometry().GetMaterial(0).SetFloat4(self.color_label, c.r, c.g, c.b, c.a)

	def update_kinetics(self, position: hg.Vector3, direction: hg.Vector3, v0: hg.Vector3, axisY: hg.Vector3, dts):
		self.num_new = 0
		if not self.end:
			self.particles_cnt_f += dts * self.flow
			self.num_new = int(self.particles_cnt_f) - self.particles_cnt
			if self.num_new > 0:
				for i in range(self.num_new):
					if not self.loop and self.particles_cnt+i>=self.num_particles:break
					particle = self.particles[(self.particles_cnt + i) % self.num_particles]
					particle.age = 0
					particle.delay = uniform(self.delay_range.x, self.delay_range.y)
					particle.scale = uniform(self.scale_range.x,self.scale_range.y)
					mat = particle.node.GetTransform()
					dir = self.get_direction(direction)
					rot_mat = hg.Matrix3(hg.Cross(axisY, dir), axisY, dir)
					mat.SetPosition(position + dir * self.start_offset)
					mat.SetRotationMatrix(rot_mat)
					mat.SetScale(self.start_scale)
					particle.rot_speed = hg.Vector3(uniform(self.rot_range_x.x, self.rot_range_x.y),
													uniform(self.rot_range_y.x, self.rot_range_y.y),
													uniform(self.rot_range_z.x, self.rot_range_z.y))
					particle.v_move = v0 + dir * uniform(self.start_speed_range.x, self.start_speed_range.y)
					particle.node.SetEnabled(False)
				self.particles_cnt += self.num_new

			n=0

			for particle in self.particles:
				if particle.age > particle.delay:
					particle.kill()
				elif particle.age == 0:
					particle.age += dts
					n+=1
				elif particle.age > 0:
					n+=1
					if not particle.node.GetEnabled(): particle.node.SetEnabled(True)
					t = particle.age / particle.delay
					mat = particle.node.GetTransform()
					pos = mat.GetPosition()
					rot = mat.GetRotation()
					particle.v_move += self.gravity * dts
					spd = particle.v_move.Len()
					particle.v_move -= particle.v_move.Normalized()*spd*self.linear_damping*dts
					pos += particle.v_move  * dts
					rot += particle.rot_speed * dts
					pos.y=max(0,pos.y)
					mat.SetPosition(pos)
					mat.SetRotation(rot)
					mat.SetScale((self.start_scale * (1 - t) + self.end_scale * t)*particle.scale)
					# material = particle.node.GetObject().GetGeometry().GetMaterial(0)
					# material.SetFloat4("self_color",1.,1.,0.,1-t)
					self.update_color(particle)
					# particle.node.GetObject().GetGeometry().GetMaterial(0).SetFloat4("teint", 1,1,1,1)
					particle.age += dts

			if n==0 and not self.loop: self.end=True