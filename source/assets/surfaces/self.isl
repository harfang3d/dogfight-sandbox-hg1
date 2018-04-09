in {
	vec4 self_color;
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
			%diffuse% = vec3(0,0,0);
			%specular% = vec3(0.,0.,0.);
			%constant% = self_color.rgb;
		%}
	}
}
