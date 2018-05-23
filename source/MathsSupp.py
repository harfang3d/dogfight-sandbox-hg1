# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                           Maths

# ===========================================================

import harfang as hg
from math import sin, cos, pi
from random import uniform


class MathsSupp:
	@classmethod
	def rotate_vector(cls, point: hg.Vector3, axe: hg.Vector3, angle):
		axe.Normalize()
		dot_prod = point.x * axe.x + point.y * axe.y + point.z * axe.z
		cos_angle = cos(angle)
		sin_angle = sin(angle)

		return hg.Vector3(
			cos_angle * point.x + sin_angle * (axe.y * point.z - axe.z * point.y) + (1 - cos_angle) * dot_prod * axe.x, \
			cos_angle * point.y + sin_angle * (axe.z * point.x - axe.x * point.z) + (1 - cos_angle) * dot_prod * axe.y, \
			cos_angle * point.z + sin_angle * (axe.x * point.y - axe.y * point.x) + (1 - cos_angle) * dot_prod * axe.z)

	@classmethod
	def rotate_matrix(cls, mat: hg.Matrix3, axe: hg.Vector3, angle):
		axeX = mat.GetX()
		axeY = mat.GetY()
		# axeZ=mat.GetZ()
		axeXr = cls.rotate_vector(axeX, axe, angle)
		axeYr = cls.rotate_vector(axeY, axe, angle)
		axeZr = hg.Cross(axeXr, axeYr)  # cls.rotate_vector(axeZ,axe,angle)
		return hg.Matrix3(axeXr, axeYr, axeZr)

	@classmethod
	def rotate_vector_2D(cls, p: hg.Vector2, angle):
		cos_angle = cos(angle)
		sin_angle = sin(angle)

		return hg.Vector2(p.x * cos_angle - p.y * sin_angle, p.x * sin_angle + p.y * cos_angle)

	@classmethod
	def get_sound_distance_level(cls, listener_position: hg.Vector3, sounder_position: hg.Vector3):
		distance = (sounder_position - listener_position).Len()
		return 1 / (distance / 10 + 1)


	@classmethod
	def get_mix_color_value(cls,f,colors):
		if f < 1:
			fc = f * (len(colors) - 1)
			i = int(fc)
			fc -= i
			return colors[i] * (1 - fc) + colors[i + 1] * fc
		else:
			return colors[-1]

# ===================================================================================
#          Génère une valeur temporelle aléatoire, lissée selon un bruit de Perlin
#          La valeur renvoyée est comprise entre -1 et 1
#          t: temps en s
#          t_prec: temps précédent en s
#          intervalle: l'intervalle de temps entre les valeurs aléatoires à interpôler (en s)
# ===================================================================================

class Temporal_Perlin_Noise:
	def __init__(self, interval=0.1):
		self.pt_prec = 0
		self.b0 = 0
		self.b1 = 0
		self.date = 0
		self.interval = interval

	def temporal_Perlin_noise(self, dts):
		self.date += dts
		t = self.date / self.interval
		pr = int(t)
		t -= self.pt_prec

		if pr > self.pt_prec:
			self.pt_prec = pr
			self.b0 = self.b1
			self.b1 = uniform(-1, 1)
			t = 0

		return self.b0 + (self.b1 - self.b0) * (sin(t * pi - pi / 2) * 0.5 + 0.5)
