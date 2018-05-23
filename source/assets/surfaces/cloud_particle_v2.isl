in {
	tex2D diffuse_map;
	float alpha_cloud;
	
	vec3 sun_dir;
	vec3 sun_color;
	vec3 ambient_color;
	float absorption_factor;
	float layer_dist;
	float altitude_min;
	float altitude_max;
	float altitude_falloff;
	float rot_speed;
	vec2 pos0;
}

variant {
	vertex {
		out {
			float front_face;
			vec2 v_uv;
			vec3 vertice_pos;
			vec3 vertice_world;
			vec3 model_pos;
			float scale;
		}

		global %{
			vec3 rot_hash=vec3(133.464, 4713.3, 1435.1);
			
			vec3 rotate(vec3 point, vec3 axe, float angle)
			{
				vec3 axe_n = normalize(axe);
				float dot_prod = point.x * axe_n.x + point.y * axe_n.y + point.z * axe_n.z;
				float cos_angle = cos(angle);
				float sin_angle = sin(angle);

				return vec3(
					cos_angle * point.x + sin_angle * (axe_n.y * point.z - axe_n.z * point.y) + (1 - cos_angle) * dot_prod * axe_n.x,
					cos_angle * point.y + sin_angle * (axe_n.z * point.x - axe_n.x * point.z) + (1 - cos_angle) * dot_prod * axe_n.y,
					cos_angle * point.z + sin_angle * (axe_n.x * point.y - axe_n.y * point.x) + (1 - cos_angle) * dot_prod * axe_n.z
					);
			}
		%}
		source %{
			
			v_uv = vUV0;
			
			model_pos = (_mtx_mul(vModelMatrix, vec4(0,0,0, 1.0))).xyz;
			vec3 axe_rot=normalize(vec3(pos0.x,model_pos.y,pos0.y)*rot_hash);
			float rot_angle=6.282*(sin(dot(pos0,rot_hash.xz)));
			rot_angle+=abs(rot_angle)/rot_angle*(0.05+rot_angle*0.01)*vClock*rot_speed;
			
			vec3 normal=rotate(vNormal,axe_rot,rot_angle);
			
			vec3 face_normal = vNormalViewMatrix * normal;
			vec3 v_model_pos = (_mtx_mul(vModelViewMatrix, vec4(0,0,0, 1.0))).xyz;
			front_face = abs(dot(face_normal,normalize(v_model_pos)));
			//vec3 scale=vec3(vModelMatrix[0][0],vModelMatrix[1][1],vModelMatrix[2][2]);
			scale=vModelMatrix[0][0];
			
			vertice_pos=rotate(vPosition,axe_rot,rot_angle);
			%position%=vec4(vertice_pos,1.);
			vertice_pos*=scale;
			vertice_world = model_pos+vertice_pos;
			
		%}
	}

	pixel {
		global %{
			const float PI=3.1415926535; //que j'aime a faire connaitre un nombre utile aux sages :)
			//r_pos : ray origin in sphere space
			vec2 sphere_intersect(vec3 r_pos, vec3 r_dir, float s_r)
			{
				const float EPSILON=1e-2;
				
				float t1,t2;
				 //Determinant:
				float a=r_dir.x*r_dir.x+r_dir.y*r_dir.y+r_dir.z*r_dir.z;
				float b=2.*(r_pos.x*r_dir.x+r_pos.y*r_dir.y+r_pos.z*r_dir.z);
				float c=r_pos.x*r_pos.x+r_pos.y*r_pos.y+r_pos.z*r_pos.z-s_r*s_r;

				float delta=b*b-4.*a*c;
				if(delta>0.)
				{
					delta=sqrt(delta);
					t1=(-b-delta)/(2.*a);
					t2=(-b+delta)/(2.*a);
					if(t1>EPSILON && t2 >EPSILON)
					{
						if(t2<t1) return vec2(t2,t1);
						else return vec2(t1,t2);
					}

					else if(t1>EPSILON && t2<=EPSILON)
					{
						return vec2(t1,t2);
					}
					else if(t1<=EPSILON && t2>EPSILON)
					{
						return vec2(t2,t1);
					}
				}

				else if (delta==0.)
				{
					t1=-b/2.*a;
					if(t1>EPSILON) return vec2(t1,t1);
				}
				return vec2(0.,0.);
			}
		%}
		
		source %{
			vec4 c_texture = texture2D(diffuse_map, v_uv);
			vec3 c_cloud=c_texture.rgb;//*vLightDiffuseColor.rgb;
			vec2 v_ray=sphere_intersect(vertice_pos,-sun_dir,scale/2.);
			float g=0.6;
			vec3 v_frag = vertice_world-vViewPosition.xyz;
			//float a_dist=1.-pow(length(v_frag)/512.,4.);
			vec3 v_dir = normalize(v_frag);
			float cos_theta = dot(v_dir,sun_dir);
			float HG = 1.;//(1.-g*g)/(4.*3.141592*pow(1.+g*g-2.*g*cos_theta,1.5));
			float absorption = exp(-v_ray.x*absorption_factor);
			float powder = 1.;//1.-exp(-v_ray.x*2.*absorption_factor);
			
			//Alpha falloff under floor altitude:
			float na=clamp((vertice_world.y-altitude_min)/(altitude_max-altitude_min),0.,1.);
			float altitude_alpha = pow(sin((na-0.5)*PI)/2.+0.5,altitude_falloff);
			
			%diffuse% = vec3(0,0,0);
			%specular% = vec3(0.,0.,0.);
			float a = c_texture.a*alpha_cloud*front_face*altitude_alpha; //*a_dist;
			%opacity% = a;
			%constant% = mix(ambient_color*c_cloud,sun_color*c_cloud,absorption*powder*HG*na);
		%}
	}
}

surface {
	blend:alpha,
	z-write:False,
	
	//blend:opaque,
	//alpha-test:True,
	//alpha_threshold:0.5,
	double-sided:True
	}
