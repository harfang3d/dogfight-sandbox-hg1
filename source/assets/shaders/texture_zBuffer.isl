/*

	Display color + depth texture
	
*/

in {
		tex2D u_tex;
		tex2D u_tex_depth;
	}

variant {
	
	vertex {
		out { vec2 v_uv; }

		source %{
			v_uv = vUV0;
			%out.position% = vec4(vPosition, 1.0);
		%}
	}

	pixel {
		in { vec2 v_uv;
				
			}
		
		source %{
			
			// --------------- Sélection de la scène:
			
			vec4 texel=texture2D(u_tex,v_uv);
			float depth=texture2D(u_tex_depth,v_uv).r;
		
			%out.color%=texel;
			%out.depth%=depth;
		%}
	}
}
