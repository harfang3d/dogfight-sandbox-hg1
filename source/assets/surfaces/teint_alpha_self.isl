in {
	vec4 teint;
}

variant {
	vertex {
		out {
		}

		source %{
		%}
	}

	pixel {
		source %{
			%diffuse% = vec3(0,0,0);
			%specular% = vec3(0.,0.,0.);
			%opacity% = teint.a;
			%constant% = teint.rgb;
		%}
	}
}

surface {
	blend:alpha,
	z-write:True,
	double-sided:True
	}
