in {
	tex2D diffuse_map;
	vec4 specular_color = vec4(0.7,0.7,0.7,1.0) [hint:color];
	float glossiness = 1. ;
}

variant {
	vertex {
		out {
			vec2 v_uv;
		}

		source %{
			v_uv = vUV0;
		%}
	}

	pixel {
		source %{
			vec4 diffuse_color = texture2D(diffuse_map, v_uv);
			%diffuse% = diffuse_color.rgb;
			%specular% = diffuse_color.rgb*specular_color.rgb;
			%glossiness% = glossiness;
			%opacity% = diffuse_color.r*0.25;
			%constant% = vec3(0,0,0);
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
