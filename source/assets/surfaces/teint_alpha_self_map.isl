in {
	tex2D self_map;
	vec4 teint;
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
			vec4 self_color = texture2D(self_map, v_uv);
			%diffuse% = vec3(0,0,0);
			%specular% = vec3(0.,0.,0.);
			%opacity% = self_color.a*teint.a;
			%constant% = self_color.rgb * teint.rgb;
		%}
	}
}

surface {
	blend:alpha,
	z-write:True,
	double-sided:True
	}
