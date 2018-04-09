/*

	Post render color filters
	
*/

in {
		tex2D u_tex;
		float contrast;
		float threshold;
		float H;
		float S;
		float V;
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
			#define M_PI 3.14159
			#define GRAY_FACTOR_R 0.11
			#define GRAY_FACTOR_G 0.59
			#define GRAY_FACTOR_B 0.3
			
			
			// ------------- Texel:
			vec4 c,color;
			
			c=texture2D(u_tex,v_uv);
			
			//-------------- Contrast with 0-threshold:
			float c0=c.r*GRAY_FACTOR_R+c.g*GRAY_FACTOR_G+c.b*GRAY_FACTOR_B;

			c.r=clamp(c.r+contrast*(c0-threshold),0.,1.);
			c.g=clamp(c.g+contrast*(c0-threshold),0.,1.);
			c.b=clamp(c.b+contrast*(c0-threshold),0.,1.);
			
			
			//--------------- Hue,Saturation,Value: 
			
			float VSU = V*S*cos(H*M_PI/180.);
			
			float VSW = V*S*sin(H*M_PI/180.);
			
			color.r = (.299*V+.701*VSU+.168*VSW)*c.r
				+ (.587*V-.587*VSU+.330*VSW)*c.g
				+ (.114*V-.114*VSU-.497*VSW)*c.b;
			color.g = (.299*V-.299*VSU-.328*VSW)*c.r
				+ (.587*V+.413*VSU+.035*VSW)*c.g
				+ (.114*V-.114*VSU+.292*VSW)*c.b;
			color.b = (.299*V-.3*VSU+1.25*VSW)*c.r
				+ (.587*V-.588*VSU-1.05*VSW)*c.g
				+ (.114*V+.886*VSU-.203*VSW)*c.b;
			
			color.a=1.;
			
			%out.color% = color;
		%}
	}
}
