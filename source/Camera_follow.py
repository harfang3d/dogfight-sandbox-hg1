# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                       Camera follow

# ===========================================================

import harfang as hg
from math import radians, sqrt
from MathsSupp import *

# ==================================================================================================
#                       Camera follow
# ==================================================================================================

track_position = hg.Vector3(0, 4, -20)
track_orientation = hg.Matrix3(hg.Vector3(1, 0, 0), hg.Vector3(0, 1, 0), hg.Vector3(0, 0, 1))

pos_inertia = 0.2
rot_inertia = 0.07

follow_inertia = 0.01
follow_distance = 200

target_point = hg.Vector3(0, 0, 0)
target_matrix = hg.Matrix3()
target_node = None

satellite_camera = None
satellite_view_size = 100
satellite_view_size_inertia = 0.7

camera_move = hg.Vector3(0, 0, 0)  # Translation in frame

noise_x = Temporal_Perlin_Noise(0.1446)
noise_y = Temporal_Perlin_Noise(0.1017)
noise_z = Temporal_Perlin_Noise(0.250314)

# ----------------------------------------
#   Tracking views
# ----------------------------------------

back_view = {"position": hg.Vector3(0, 4, -20),
			 "orientation": hg.Matrix3(hg.Vector3(1, 0, 0), hg.Vector3(0, 1, 0), hg.Vector3(0, 0, 1)),
			 "pos_inertia": 0.2, "rot_inertia": 0.07}

front_view = {"position": hg.Vector3(0, 4, 40),
			  "orientation": hg.Matrix3(hg.Vector3(-1, 0, 0), hg.Vector3(0, 1, 0), hg.Vector3(0, 0, -1)),
			  "pos_inertia": 0.9, "rot_inertia": 0.05}

right_view = {"position": hg.Vector3(-40, 4, 0),
			  "orientation": hg.Matrix3(hg.Vector3(0, 0, -1), hg.Vector3(0, 1, 0), hg.Vector3(1, 0, 0)),
			  "pos_inertia": 0.9, "rot_inertia": 0.05}

left_view = {"position": hg.Vector3(40, 4, 0),
			 "orientation": hg.Matrix3(hg.Vector3(0, 0, 1), hg.Vector3(0, 1, 0), hg.Vector3(-1, 0, 0)),
			 "pos_inertia": 0.9, "rot_inertia": 0.05}

top_view = {"position": hg.Vector3(0, 50, 0),
			"orientation": hg.Matrix3(hg.Vector3(1, 0, 0), hg.Vector3(0, 0, 1), hg.Vector3(0, -1, 0)),
			"pos_inertia": 0.9, "rot_inertia": 0.05}


# =====================================================================================================
#           Functions
# =====================================================================================================

def setup_camera_follow(targetNode: hg.Node, targetPoint: hg.Vector3, targetMatrix: hg.Matrix3):
	global target_point, target_matrix, target_node
	target_point = targetPoint
	target_matrix = targetMatrix
	target_node = targetNode


def RangeAdjust(value, oldmin, oldmax, newmin, newmax):
	return (value - oldmin) / (oldmax - oldmin) * (newmax - newmin) + newmin


def update_target_point(dts):
	global target_point, target_matrix
	v = target_node.GetTransform().GetPosition() - target_point
	target_point += v * pos_inertia * dts * 60

	mat_n = target_node.GetTransform().GetWorld()
	rz = hg.Cross(target_matrix.GetZ(), mat_n.GetZ())
	ry = hg.Cross(target_matrix.GetY(), mat_n.GetY())
	mr = rz + ry
	if mr.Len() > 0.001:
		target_matrix = MathsSupp.rotate_matrix(target_matrix, mr.Normalized(), mr.Len() * rot_inertia * dts * 60)


def update_track_translation(camera: hg.Node, dts):
	global camera_move
	trans = camera.GetTransform()
	camera_pos = trans.GetPosition()
	new_position = target_point + target_matrix.GetX() * track_position.x + target_matrix.GetY() * track_position.y + target_matrix.GetZ() * track_position.z
	trans.SetPosition(new_position)
	camera_move = new_position - camera_pos
	return new_position


def update_follow_translation(camera: hg.Node, dts):
	global camera_move
	trans = camera.GetTransform()
	camera_pos = trans.GetPosition()
	aX = trans.GetWorld().GetX()
	target_pos = target_node.GetTransform().GetPosition()

	# Wall
	v = target_pos - camera_pos
	target_dir = v.Normalized()
	target_dist = v.Len()

	v_trans = target_dir * (target_dist - follow_distance) + aX * 20

	new_position = camera_pos + v_trans * follow_inertia * 60 * dts
	trans.SetPosition(new_position)
	camera_move = new_position - camera_pos
	return new_position


def update_track_direction(camera: hg.Node, dts, noise_level):
	# v = target_point - camera.GetTransform().GetPosition()
	f = radians(noise_level)
	rot = target_matrix.ToEuler()
	rot += hg.Vector3(noise_x.temporal_Perlin_noise(dts) * f, noise_y.temporal_Perlin_noise(dts) * f,
					  noise_z.temporal_Perlin_noise(dts) * f)
	rot_mat = hg.Matrix3.FromEuler(rot)
	rot_mat = rot_mat * track_orientation
	camera.GetTransform().SetRotationMatrix(rot_mat)
	return rot_mat  # camera.GetTransform().GetWorld().GetRotationMatrix().LookAt(v, target_matrix.GetY()))


def update_follow_direction(camera: hg.Node):
	v = target_point - camera.GetTransform().GetPosition()
	rot_mat = camera.GetTransform().GetWorld().GetRotationMatrix().LookAt(v, hg.Vector3.Up)
	camera.GetTransform().SetRotationMatrix(rot_mat)
	return rot_mat


def update_camera_tracking(camera: hg.Node, dts, noise_level=0):
	global target_point, target_node
	update_target_point(dts)
	rot_mat = update_track_direction(camera, dts, noise_level)
	pos = update_track_translation(camera, dts)
	mat = hg.Matrix4(rot_mat)
	mat.SetTranslation(pos)
	return mat


def update_camera_follow(camera: hg.Node, dts):
	global target_point, target_node
	update_target_point(dts)
	rot_mat = update_follow_direction(camera)
	pos = update_follow_translation(camera, dts)
	mat = hg.Matrix4(rot_mat)
	mat.SetTranslation(pos)
	return mat


def set_track_view(parameters: dict):
	global track_position, track_orientation, pos_inertia, rot_inertia
	track_position = parameters["position"]
	track_orientation = parameters["orientation"]
	pos_inertia = parameters["pos_inertia"]
	rot_inertia = parameters["rot_inertia"]


def setup_satellite_camera(camera: hg.Node):
	camera.GetCamera().SetOrthographic(True)
	camera.GetCamera().SetOrthographicSize(satellite_view_size)
	camera.GetTransform().SetRotation(hg.Vector3(radians(90), 0, 0))


def update_satellite_camera(camera, screen_ratio, dts):
	camera.GetTransform().SetPosition(
		hg.Vector3(target_point.x, camera.GetCamera().GetOrthographicSize() * screen_ratio, target_point.z))
	cam = camera.GetCamera()
	size = cam.GetOrthographicSize()
	cam.SetOrthographicSize(size + (satellite_view_size - size) * satellite_view_size_inertia)


def increment_satellite_view_size():
	global satellite_view_size
	satellite_view_size *= 1.01


def decrement_satellite_view_size():
	global satellite_view_size
	satellite_view_size = max(10, satellite_view_size / 1.01)
