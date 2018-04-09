/*

	Double texture z-fusion + color filters
	
*/

in {
		tex2D u_tex1;
		tex2D u_tex2;
		tex2D u_tex1_depth;
		tex2D u_tex2_depth;
	
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
			float depth;
			vec4 c1=texture2D(u_tex1,v_uv);
			vec4 c2=texture2D(u_tex2,v_uv);
			float c1z=texture2D(u_tex1_depth,v_uv).r;
			float c2z=texture2D(u_tex2_depth,v_uv).r;
			//c=c2;

			if(c2z<c1z)
			{
				if (c1.a >0. && c1z==1.) //Detect mesh transparency on sea foreground
				{
					c.rgb=mix(c2.rgb,c1.rgb,c1.a);
					//c.rgb=c1.rgb;
					//c.rgb=vec3(1.,1.,1.)-(vec3(1.,1.,1.)-c1.rgb)*(vec3(1.,1.,1.)-c2.rgb);
					//c=c1+c2;
					//c=c2*(vec4(1.,1.,1.,1.)-c1)+c1;
				}
				else c=c2;
			}
			else
			{
				c=c1;
			}
			
			//if (c1.rgb==vec4(0.,0.,0.)
			//c=c1*a+c2*(1.-a);
			
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
			//%out.depth% = min(c1z,c2z);
		%}
	}
}
