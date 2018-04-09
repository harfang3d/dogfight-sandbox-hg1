in {
	tex2D diffuse_map [wrap-u:repeat, wrap-v:repeat];
	tex2D ao_map [wrap-u:repeat, wrap-v:repeat];
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
			float intensity = texture2D(ao_map, v_uv).r;
			%diffuse% = diffuse_color.xyz*intensity;
			%specular% = specular_color.rgb;
			%glossiness% = glossiness;
		%}
	}
}
