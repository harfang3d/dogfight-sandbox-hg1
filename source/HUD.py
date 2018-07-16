# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                   Dogfigth - Main module

# ===========================================================


import harfang as hg
from Machines import *
from MathsSupp import *


def get_2d(camera, renderer, point3d: hg.Vector3):
	f, pos = hg.Project(camera.GetTransform().GetWorld(), camera.GetCamera().GetZoomFactor(), renderer.GetAspectRatio(),
						point3d)
	if f:
		return hg.Vector2(pos.x, 1 - pos.y)
	else:
		return None


def update_radar(Main,plus,aircraft,targets):
	value = Main.HSL_postProcess.GetL()
	t=hg.time_to_sec_f(plus.GetClock())
	rx,ry = 150/1600*Main.resolution.x, 150/900*Main.resolution.y
	rs=200/1600*Main.resolution.x
	rm=6/1600*Main.resolution.x

	radar_scale = 4000
	plot_size = 12/1600*Main.resolution.x/2

	plus.Sprite2D(rx,ry,rs,"assets/sprites/radar.png",hg.Color(1,1,1,value))
	mat=aircraft.get_parent_node().GetTransform().GetWorld()

	aZ=mat.GetZ()
	aZ.y=0
	aZ.Normalize()
	aY=mat.GetY()
	if aY.y<0:
		aY=hg.Vector3(0,-1,0)
	else:
		aY=hg.Vector3(0,1,0)
	aX=hg.Cross(aY,aZ)
	mat_trans = hg.Matrix4.TransformationMatrix(mat.GetTranslation(),hg.Matrix3(aX,aY,aZ)).InversedFast()

	for target in targets:
		if not target.wreck and target.activated:
			t_mat = target.get_parent_node().GetTransform().GetWorld()
			aZ=t_mat.GetZ()
			aZ.y=0
			aZ.Normalize()
			aY=hg.Vector3(0,1,0)
			aX=hg.Cross(aY,aZ)
			t_mat_trans = mat_trans * hg.Matrix4.TransformationMatrix(t_mat.GetTranslation(),hg.Matrix3(aX,aY,aZ))
			pos=t_mat_trans.GetTranslation()
			v2D = hg.Vector2(pos.x, pos.z) / radar_scale * rs / 2
			if abs(v2D.x)<rs/2-rm and abs(v2D.y)<rs/2-rm:

				if target.type==Destroyable_Machine.TYPE_MISSILE:
					plot=Main.texture_hud_plot_missile
				elif target.type==Destroyable_Machine.TYPE_AIRCRAFT:
					plot=Main.texture_hud_plot_aircraft
				elif target.type==Destroyable_Machine.TYPE_SHIP:
					plot=Main.texture_hud_plot_ship
				t_mat_rot = t_mat_trans.GetRotationMatrix()
				ps=plot_size
				a = 0.5 + 0.5*abs(sin(t*uniform(1,500)))
			else:
				if target.type == Destroyable_Machine.TYPE_MISSILE: continue
				dir=v2D.Normalized()
				v2D = dir * (rs/2-rm)
				ps=plot_size
				plot=Main.texture_hud_plot_dir
				aZ=hg.Vector3(dir.x,0,dir.y)
				aX=hg.Cross(hg.Vector3.Up,aZ)
				t_mat_rot = hg.Matrix3(aX,hg.Vector3.Up,aZ)
				a = 0.5 + 0.5*abs(sin(t*uniform(1,500)))

			cx, cy = rx + v2D.x, ry + v2D.y

			if target.nationality == 1:
				c = hg.Color(0.25, 1., 0.25, a)
			elif target.nationality == 2:
				c = hg.Color(1., 0.5, 0.5, a)

			c.a*=value
			p1 = t_mat_rot * hg.Vector3(-plot_size, 0, -ps)
			p2 = t_mat_rot * hg.Vector3(-plot_size, 0, ps)
			p3 = t_mat_rot * hg.Vector3(plot_size, 0, ps)
			p4 = t_mat_rot * hg.Vector3(plot_size, 0, -ps)
			plus.Quad2D(cx + p1.x, cy + p1.z, cx + p2.x, cy + p2.z, cx + p3.x, cy + p3.z, cx + p4.x, cy + p4.z, c, c, c, c, plot)


	c=hg.Color(1,1,1,value*max(pow(1-aircraft.health_level,2),0.05))
	plus.Quad2D(rx-rs/2,ry-rs/2,
				rx-rs/2,ry+rs/2,
				rx+rs/2,ry+rs/2,
				rx+rs/2,ry-rs/2,
				c,c,c,c,Main.texture_noise,0.25+0.25*sin(t*103),(0.65+0.35*sin(t*83)),0.75+0.25*sin(t*538),0.75+0.25*cos(t*120))
	c=hg.Color(1,1,1,value)
	plus.Sprite2D(rx, ry, rs, "assets/sprites/radar_light.png",hg.Color(1,1,1,0.3*value))
	plus.Sprite2D(rx, ry, rs, "assets/sprites/radar_box.png",c)


def update_machine_gun_sight(Main,plus,aircraft:Aircraft):
	mat = aircraft.get_parent_node().GetTransform().GetWorld()
	aZ=mat.GetZ()
	pos=aircraft.gun_position * mat
	p=pos+aZ*500
	Main.gun_sight_2D=get_2d(Main.scene.GetCurrentCamera(),plus.GetRenderer(),p)
	p2D=Main.gun_sight_2D
	if p2D is not None:
		plus.Sprite2D(p2D.x*Main.resolution.x, p2D.y*Main.resolution.y, 64/1600*Main.resolution.x, "assets/sprites/machine_gun_sight.png", hg.Color(0.5,1,0.5, Main.HSL_postProcess.GetL()))


def update_target_sight(Main,plus,aircraft:Aircraft):
	tps = hg.time_to_sec_f(plus.GetClock())
	target=aircraft.get_target()
	f = Main.HSL_postProcess.GetL()
	if target is not None:
		p2D=get_2d(Main.scene.GetCurrentCamera(),plus.GetRenderer(),target.get_parent_node().GetTransform().GetPosition())
		if p2D is not None:
			a_pulse = 0.5 if (sin(tps * 20) > 0) else 0.75
			if aircraft.target_locked:
				c=hg.Color(1.,0.5,0.5,a_pulse)
				msg="LOCKED - "+str(int(aircraft.target_distance))
				x=(p2D.x - 32 / 1600)
				a=a_pulse
			else:
				msg=str(int(aircraft.target_distance))
				x=(p2D.x - 12 / 1600)
				c=hg.Color(0.5,1,0.5,0.75)

			c.a*=f
			plus.Sprite2D(p2D.x * Main.resolution.x, p2D.y * Main.resolution.y, 32 / 1600 * Main.resolution.x,
						  "assets/sprites/target_sight.png", c)


			if aircraft.target_out_of_range:

				plus.Text2D((p2D.x-40/1600) * Main.resolution.x, (p2D.y-24/900) * Main.resolution.y, "OUT OF RANGE",
							0.012 * Main.resolution.y, hg.Color(0.2, 1, 0.2, a_pulse*f))
			else:
				plus.Text2D(x * Main.resolution.x, (p2D.y - 24 / 900) * Main.resolution.y,
							msg, 0.012 * Main.resolution.y, c)

			if aircraft.target_locking_state>0:
				t=sin(aircraft.target_locking_state*pi-pi/2)*0.5+0.5
				p2D=hg.Vector2(0.5,0.5)*(1-t)+p2D*t
				plus.Sprite2D(p2D.x * Main.resolution.x, p2D.y * Main.resolution.y, 32 / 1600 * Main.resolution.x,
							  "assets/sprites/missile_sight.png", c)

		c=hg.Color(0,1,0,f)
		plus.Text2D(0.05 * Main.resolution.x, 0.93 * Main.resolution.y, "Target dist: %d" % (aircraft.target_distance),
					0.016 * Main.resolution.y,c)
		plus.Text2D(0.05 * Main.resolution.x, 0.91 * Main.resolution.y, "Target cap: %d" % (aircraft.target_cap),
					0.016 * Main.resolution.y, c)
		plus.Text2D(0.05 * Main.resolution.x, 0.89 * Main.resolution.y, "Target alt: %d" % (aircraft.target_altitude),
					0.016 * Main.resolution.y, c)



def display_hud(Main, plus, aircraft: Aircraft,targets):
	f =Main.HSL_postProcess.GetL()
	tps = hg.time_to_sec_f(plus.GetClock())
	a_pulse = 0.1 if (sin(tps * 25) > 0) else 0.9
	hs, vs = aircraft.get_world_speed()

	plus.Text2D(0.05 * Main.resolution.x, 0.95 * Main.resolution.y, "Health: %d" % (aircraft.health_level*100),
				0.016 * Main.resolution.y, (hg.Color.White*aircraft.health_level+hg.Color.Red*(1-aircraft.health_level)) * f)

	plus.Text2D(0.49 * Main.resolution.x, 0.95 * Main.resolution.y, "Cap: %d" % (aircraft.cap),
				0.016 * Main.resolution.y, hg.Color.White * f)

	plus.Text2D(0.8 * Main.resolution.x, 0.90 * Main.resolution.y, "Altitude (m): %d" % (aircraft.get_altitude()),
				0.016 * Main.resolution.y, hg.Color.White * f)
	plus.Text2D(0.8 * Main.resolution.x, 0.88 * Main.resolution.y, "Vertical speed (m/s): %d" % (vs), 0.016 * Main.resolution.y,
				hg.Color.White * f)

	plus.Text2D(0.8 * Main.resolution.x, 0.03 * Main.resolution.y, "horizontal speed (m/s): %d" % (hs), 0.016 * Main.resolution.y,
				hg.Color.White * f)

	plus.Text2D(0.8 * Main.resolution.x, 0.13 * Main.resolution.y, "Pitch attitude: %d" % (aircraft.pitch_attitude),
				0.016 * Main.resolution.y, hg.Color.White * f)

	plus.Text2D(0.8 * Main.resolution.x, 0.11 * Main.resolution.y,
				"Roll attitude: %d" % (aircraft.roll_attitude), 0.016 * Main.resolution.y,
				hg.Color.White * f)

	ls=aircraft.get_linear_speed()*3.6
	plus.Text2D(0.8 * Main.resolution.x, 0.05 * Main.resolution.y,
				"Linear speed (km/h): %d" % (ls), 0.016 *Main. resolution.y,
				hg.Color.White * f)
	if ls<250 and not aircraft.flag_landed:
		plus.Text2D(749/1600 * Main.resolution.x, 120/900 * Main.resolution.y, "LOW SPEED",
					0.018 * Main.resolution.y, hg.Color(1.,0,0,a_pulse))

	plus.Text2D(0.8 * Main.resolution.x, 0.01 * Main.resolution.y,
				"Linear acceleration (m.s2): %.2f" % (Main.p1_aircraft.get_linear_acceleration()), 0.016 * Main.resolution.y,
				hg.Color.White * f)

	plus.Text2D(749 / 1600 * Main.resolution.x, 94 / 900 * Main.resolution.y,
				"Thrust: %d %%" % (Main.p1_aircraft.thrust_level * 100), 0.016 * Main.resolution.y, hg.Color.White * f)
	if Main.p1_aircraft.brake_level > 0:
		plus.Text2D(688 / 1600 * Main.resolution.x, 32 / 900 * Main.resolution.y,
					"Brake: %d %%" % (Main.p1_aircraft.brake_level * 100), 0.016 * Main.resolution.y, hg.Color(1, 0.4, 0.4) * f)
	if Main.p1_aircraft.flaps_level > 0:
		plus.Text2D(824 / 1600 * Main.resolution.x, 32 / 900 * Main.resolution.y,
					"Flaps: %d %%" % (Main.p1_aircraft.flaps_level * 100), 0.016 * Main.resolution.y, hg.Color(1, 0.8, 0.4) * f)


	#if Main.p1_aircraft.post_combution:
	#    plus.Text2D(710 / 1600 * Main.resolution.x, 76 / 900 * Main.resolution.y, "POST COMBUSTION", 0.02 * Main.resolution.y,
	#                hg.Color.Red)

	update_radar(Main, plus, aircraft, targets)
	update_target_sight(Main, plus, aircraft)

	if not Main.satellite_view:
		update_machine_gun_sight(Main, plus, aircraft)

