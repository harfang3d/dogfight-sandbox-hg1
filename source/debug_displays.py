# ==============================================================================================
#               Displays
# ==============================================================================================

import harfang as hg

class DebugDisplays:
	courbe = []
	ymin = 0
	ymax = 0
	start_courbe = False

	@classmethod
	def maj_courbe(cls, y):
		if not cls.start_courbe:
			cls.ymin = y
			cls.ymax = y
			cls.start_courbe = True
		else:
			if y < cls.ymin:
				ymin = y
			if y > cls.ymax:
				cls.ymax = y
		cls.courbe.append(y)

	@classmethod
	def affiche_courbe(cls, plus):
		resolution = hg.Vector2(float(plus.GetScreenWidth()), float(plus.GetScreenHeight()))
		num = len(cls.courbe)
		if num > 10:
			x_step = resolution.x / (num - 1)
			x1 = 0
			x2 = x_step
			y1 = (cls.courbe[0] - cls.ymin) / (cls.ymax - cls.ymin) * resolution.y
			for i in range(num - 1):
				y2 = (cls.courbe[i + 1] - cls.ymin) / (cls.ymax - cls.ymin) * resolution.y
				plus.Line2D(x1, y1, x2, y2, hg.Color.Yellow, hg.Color.Yellow)
				x1 = x2
				x2 += x_step
				y1 = y2

	@classmethod
	def get_2d(cls, camera, renderer, point3d: hg.Vector3):
		f, pos = hg.Project(camera.GetTransform().GetWorld(), camera.GetCamera().GetZoomFactor(),
							renderer.GetAspectRatio(), point3d)
		if f:
			return hg.Vector2(pos.x, 1 - pos.y)
		else:
			return None

	@classmethod
	def affiche_vecteur(cls, plus:hg.Plus, camera, position, direction, unitaire=True, c1=hg.Color.Yellow, c2=hg.Color.Red):
		resolution = hg.Vector2(float(plus.GetScreenWidth()),float(plus.GetScreenHeight()))
		if unitaire:
			position_b = position + direction.Normalized()
		else:
			position_b = position + direction
		pA = cls.get_2d(camera, plus.GetRenderer(), position)
		pB = cls.get_2d(camera, plus.GetRenderer(), position_b)
		if pA is not None and pB is not None:
			plus.Line2D(pA.x * resolution.x, pA.y * resolution.y, pB.x * resolution.x, pB.y * resolution.y, c1, c2)

	@classmethod
	def affiche_repere(cls, plus, camera, position: hg.Vector3, repere: hg.Matrix3):
		cls.affiche_vecteur(plus, camera, position, repere.GetX(), hg.Color.White, hg.Color.Red)
		cls.affiche_vecteur(plus, camera, position, repere.GetY(), hg.Color.White, hg.Color.Green)
		cls.affiche_vecteur(plus, camera, position, repere.GetZ(), hg.Color.White, hg.Color.Blue)