in {
	tex2D diffuse_map;
	vec4 teint;
}

variant {
	vertex {
		out {
			float front_face;
			vec2 v_uv;
		}

		source %{
			v_uv = vUV0;
			vec3 face_normal = vNormalViewMatrix * vNormal;
			vec3 model_pos = (_mtx_mul(vModelViewMatrix, vec4(0,0,0, 1.0))).xyz;
			front_face = abs(dot(face_normal,normalize(model_pos)));
		%}
	}

	pixel {
		source %{
			vec4 diffuse_color = texture2D(diffuse_map, v_uv);
			%diffuse% = vec3(0,0,0);
			%specular% = vec3(0.,0.,0.);
			%opacity% = diffuse_color.a*teint.a*front_face;
			%constant% = diffuse_color.rgb * teint.rgb;
		%}
	}
}

surface {
	blend:alpha,
	z-write:True,
	
	//blend:opaque,
	//alpha-test:True,
	//alpha_threshold:0.5,
	double-sided:True
	}
