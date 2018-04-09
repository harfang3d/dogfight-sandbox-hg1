in {
	tex2D diffuse_map [wrap-u:repeat, wrap-v:repeat];
	tex2D ao_map [wrap-u:repeat, wrap-v:repeat];
	tex2D normal_map [wrap-u:repeat, wrap-v:repeat];
	vec4 specular_color = vec4(0.7,0.7,0.7,1.0) [hint:color];
	float glossiness = 1. ;
}

variant {
	vertex {
		out {
			vec2 v_uv;
			vec3 v_normal;
			vec3 v_tangent;
			vec3 v_bitangent;
		}

		source %{
			v_uv = vUV0;
			v_normal = vNormal;
			v_tangent = vTangent;
			v_bitangent = vBitangent;
		%}
	}

	pixel {
		source %{
			
			vec3 n = texture2D(normal_map, v_uv).xyz * vec3(1.,1.,1.);
			mat3 tangent_matrix = _build_mat3(normalize(v_bitangent), normalize(v_tangent), normalize(v_normal));
			n = n * 2.0 - 1.0;
			n = tangent_matrix * n;
			n = vNormalViewMatrix * n;
			%normal% = n;
			
			vec4 diffuse_color = texture2D(diffuse_map, v_uv);
			float intensity = texture2D(ao_map, v_uv).r;
			%diffuse% = diffuse_color.xyz*intensity;
			%specular% = specular_color.rgb;
			%glossiness% = glossiness;
		%}
	}
}
