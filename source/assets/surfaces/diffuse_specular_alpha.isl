in {
	vec4 diffuse_color = vec4(0.7,0.7,0.7,1.0) [hint:color];
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
			%diffuse% = diffuse_color.rgb;
			%specular% = specular_color.rgb;
			%opacity% = diffuse_color.a;
			%constant% = vec3(0.,0.,0.);
		%}
	}
}

surface {
	blend:alpha,
	z-write:True,
	double-sided:True
	}
