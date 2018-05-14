# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#                  Load/Save data conversions

# ===========================================================

import harfang as hg
from math import radians,degrees
import json

def list_to_color(c: list):
	return hg.Color(c[0], c[1], c[2], c[3])

def color_to_list(c: hg.Color):
	return [c.r, c.g, c.b, c.a]

def list_to_vec2(v: list):
	return hg.Vector2(v[0], v[1])

def vec2_to_list(v: hg.Vector2):
	return [v.x, v.y]

def list_to_vec3(v: list):
	return hg.Vector3(v[0], v[1],v[2])

def list_to_vec3_radians(v: list):
	v=list_to_vec3(v)
	v.x=radians(v.x)
	v.y=radians(v.y)
	v.z=radians(v.z)
	return v

def vec3_to_list(v: hg.Vector3):
	return [v.x, v.y, v.z]

def vec3_to_list_degrees(v: hg.Vector3):
	l=vec3_to_list(v)
	l[0]=degrees(l[0])
	l[1]=degrees(l[1])
	l[2]=degrees(l[2])
	return l

def load_json_matrix(file_name):
	json_script = hg.GetFilesystem().FileToString(file_name)
	if json_script != "":
		script_parameters = json.loads(json_script)
		pos = list_to_vec3(script_parameters["position"])
		rot = list_to_vec3_radians(script_parameters["rotation"])
		return pos,rot
	return None,None

def save_json_matrix(pos : hg.Vector3, rot:hg.Vector3,output_filename ):
	script_parameters = {"position" : vec3_to_list(pos), "rotation" : vec3_to_list_degrees(rot)}
	json_script = json.dumps(script_parameters, indent=4)
	return hg.GetFilesystem().StringToFile(output_filename, json_script)

def duplicate_node_object(original_node:hg.Node, name):
	node = hg.Node(name)
	trans = hg.Transform()
	node.AddComponent(trans)
	obj = hg.Object()
	obj.SetGeometry(original_node.GetObject().GetGeometry())
	node.AddComponent(obj)
	return node

def load_object(plus,geometry_file_name, name,duplicate_material=False):
	renderSystem = plus.GetRenderSystem()
	node = hg.Node(name)
	trans = hg.Transform()
	node.AddComponent(trans)
	obj = hg.Object()
	geo = hg.Geometry()
	hg.LoadGeometry(geo,geometry_file_name)
	if geo is not None:
		geo = renderSystem.CreateGeometry(geo,False)
		if duplicate_material:
			material = geo.GetMaterial(0)
			material = material.Clone()
			geo.SetMaterial(0,material)
		obj.SetGeometry(geo)
		node.AddComponent(obj)
	return node,geo

