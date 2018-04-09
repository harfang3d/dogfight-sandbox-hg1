/*

				Sky render - 2017		

*/

in {
	tex2D tex_sky_N [wrap-u: clamp, wrap-v: clamp];
	tex2D tex_sky_S [wrap-u: clamp, wrap-v: clamp];
	float screen_ratio;
	float focal_distance;
	mat3 cam_normal;
	
	vec3 zenith_color;
	vec3 horizonH_color;
	vec3 horizonL_color;
	vec3 nadir_color;
	
	vec3 sun_dir;
    vec3 sun_color;
	
}

variant {
	
	//====================================================================================================
	
	vertex {
		out {
			vec2 v_uv;
			vec3 screen_ray; 
		}

		source %{
			v_uv = vUV0;
			screen_ray=vec3(vPosition.x,vPosition.y,0.)*vec3(screen_ratio,1.,0.)+vec3(0.,0.,focal_distance);
			%out.position% = vec4(vPosition, 1.0);
		%}
	}

	//====================================================================================================
	
	pixel {
			
		global %{
			
			#define M_PI 3.141592653
			#define GRAY_FACTOR_R 0.11
			#define GRAY_FACTOR_V 0.59
			#define GRAY_FACTOR_B 0.3
			
			// Get spherical coordinate texel:
			vec3 get_sky_texel(vec3 dir)
			{
				float phi,theta,v,r;
				vec2 uv;
				if (dir.y<0)
				{
					phi=asin(dir.y)+M_PI;
					v=acos(-dir.x/sqrt(pow(-dir.x,2)+pow(dir.z,2)));
				}
				else 
				{
					phi=asin(dir.y);
					v=acos(dir.x/sqrt(pow(dir.x,2)+pow(dir.z,2)));
				}
				if (dir.z>=0.) theta=v;
				else theta=2.*M_PI-v;
				
				r=0.5-phi/M_PI;
				uv=vec2(r*cos(theta),r*sin(theta))+vec2(0.5,0.5);
				if (dir.y<0) return texture2D(tex_sky_S,uv).rgb;
				else return texture2D(tex_sky_N,uv).rgb;
			}
			
			vec3 get_atmosphere_color(vec3 dir)
			{
				vec3 c_atmosphere;
				if (dir.y<-1e-4)c_atmosphere=mix(nadir_color,horizonL_color,pow(min(1.,1+dir.y),2.));
				else if(dir.y>=-1e-4 && dir.y<1e-4) c_atmosphere=horizonL_color;
				else c_atmosphere=mix(zenith_color,horizonH_color,pow(min(1.,1-dir.y),2.));
				return c_atmosphere;
			}
			
			float get_sun_intensity(vec3 dir, vec3 sun_dir)
			{
				float prod_scal = max(dot(sun_dir,-dir),0);
				return min(pow(prod_scal,8000) + 0.2 * pow(prod_scal,500) + 0.5 *pow(prod_scal,10),1);
			}
			
			
			vec3 get_sky_color(vec3 dir,vec3 sun_dir,vec3 c_sun, vec3 c_atmosphere)
			{
				vec3 sky_tex=get_sky_texel(dir);
				float sun_lum = get_sun_intensity(dir,sun_dir);
				float sky_lum=c_atmosphere.r*GRAY_FACTOR_R+c_atmosphere.g*GRAY_FACTOR_V+c_atmosphere.b*GRAY_FACTOR_B;
				return mix(c_atmosphere+sky_tex*(1-sky_lum),c_sun,sun_lum);
			}
			
		%}
		
	//====================================================================================================
		
		
		source %{
			vec3 dir=normalize(cam_normal*normalize(screen_ray));

			vec3 c_atmosphere = get_atmosphere_color(dir);
			vec3 color=get_sky_color(dir,sun_dir,sun_color,c_atmosphere);
			
			%out.color% =vec4(color,1.);
		%}
	}
}
