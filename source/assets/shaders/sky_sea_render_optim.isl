/*

				Sky & sea render - 2017		

*/

in {
	tex2D tex_sky_N [wrap-u: clamp, wrap-v: clamp];
	tex2D reflect_map;
	tex2D reflect_map_depth;
	tex2D noise_texture_1 [wrap-u: repeat, wrap-v: repeat];
	tex2D noise_texture_2 [wrap-u: repeat, wrap-v: repeat];
	tex2D displacement_texture [wrap-u: repeat, wrap-v: repeat];
	tex2D stream_texture [wrap-u: repeat, wrap-v: repeat];
	tex2D clouds_map [wrap-u: repeat, wrap-v: repeat];
	
	vec3 clouds_scale;
	float clouds_altitude;
	float clouds_absorption;
	
	float tex_sky_N_intensity;
	vec2 resolution;
	float focal_distance;
	vec3 cam_position;
	mat3 cam_normal;
	
	int sea_filtering;
	int max_samples;
	float filter_precision;
	
	vec3 sea_scale;
	
	vec3 zenith_color;
	float zenith_falloff;
	vec3 horizonH_color;
	vec3 horizonL_color;
	vec3 horizon_line_color;
	float horizon_line_size;
	vec3 sea_color;
	float sea_reflection;
	float time;
	
	vec2 zFrustum;
	vec3 sun_dir;
    vec3 sun_color;
    vec3 ambient_color;
	
	float reflect_offset;
	
	int scene_reflect;
	
	
}

variant {
	
	//====================================================================================================
	
	vertex {
		out {
			vec2 v_uv;
			vec2 position;
			vec3 screen_ray; 
			vec3 screen_ray_X;
			vec3 screen_ray_Y; 
		}

		source %{
			v_uv = vUV0;
			position = (vPosition.xy+vec2(1.,1.))*0.5;
			float ratio = resolution.x / resolution.y;
			screen_ray=vec3(vPosition.x,vPosition.y,0.)*vec3(ratio,1.,0.)+vec3(0.,0.,focal_distance);
			screen_ray_X=screen_ray + vec3(ratio*2./resolution.x,0.,0.);
			screen_ray_Y=screen_ray + vec3(0.,2./resolution.y,0.);
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
			
			float get_zDepth(float near,float far)
			{
					float a,b,z;
					z=far*near;
					a=zFrustum.y/(zFrustum.y-zFrustum.x);
					b=zFrustum.y*zFrustum.x/(zFrustum.x-zFrustum.y);
					return ((a+b/z)+1.)/2.;
			}
			
			float get_zFromDepth(float near,float zDepth)
			{
					float a,b;
					a=zFrustum.y/(zFrustum.y-zFrustum.x);
					b=zFrustum.y*zFrustum.x/(zFrustum.x-zFrustum.y);
					return b/((zDepth*2.-1.-a)*near);
			}
			
			// Get spherical coordinate texel:
			vec4 get_sky_texel(vec3 dir)
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
				return texture2D(tex_sky_N,uv)*tex_sky_N_intensity;
			}
			
			vec3 get_atmosphere_color(vec3 dir)
			{
				vec3 c_atmosphere;
				if (dir.y<-1e-4)c_atmosphere=mix(sea_color,horizonL_color,pow(min(1.,1+dir.y),1.));
				else if(dir.y>=-1e-4 && dir.y<1e-4) c_atmosphere=horizonH_color;
				else c_atmosphere=mix(zenith_color,horizonH_color,pow(min(1.,1-dir.y),zenith_falloff));
				return c_atmosphere;
			}
			
			float get_sun_intensity(vec3 dir, vec3 sun_dir)
			{
				float prod_scal = max(dot(sun_dir,-dir),0);
				return min(0.4*pow(prod_scal,7000) + 0.5 * pow(prod_scal,50) + 0.4 *pow(prod_scal,2),1);
			}
			
			
			vec3 get_sky_color(vec3 dir,vec3 sun_dir,vec3 c_sun, vec3 c_atmosphere)
			{
				vec4 sky_col=get_sky_texel(dir);
				vec3 sky_tex=sky_col.rgb*sky_col.a;
				float sun_lum = get_sun_intensity(dir,sun_dir);
				float sky_lum=c_atmosphere.r*GRAY_FACTOR_R+c_atmosphere.g*GRAY_FACTOR_V+c_atmosphere.b*GRAY_FACTOR_B;
				return mix(c_atmosphere+sky_tex*(1-sky_lum),c_sun,sun_lum);
			}
			
			
			float noise_2d_textures (vec2 pa)
			{
				vec2 p = vec2(pa.x,pa.y)*sea_scale.xz;
				float disp = texture2D(displacement_texture, p/4.+vec2(time*0.01,time*0.004)).r;
				vec2 p_disp = p+vec2(disp*0.06,disp*0.07);
				vec2 noise_2_disp = vec2(time*0.025,time*0.001);
				float a = texture2D(noise_texture_1, p_disp/2.).r;
				a += texture2D(noise_texture_2, p_disp+noise_2_disp).r;
				a+=texture2D(noise_texture_1, p/10.).r;
				a/=3.;
				//a=texture2D(noise_texture, p).r;
				return a;
			}
			
			
			float get_wave_altitude(vec2 p)
			{
				float a=noise_2d_textures(p);
				return a*sea_scale.y;
			}
			
			vec3 get_normale(vec2 pos)
			{
				float f=0.5;//0.02 for rt noise
				vec2 xd=vec2(f,0);
				vec2 zd=vec2(0,f);
				return normalize(vec3(
										get_wave_altitude(pos-xd) - get_wave_altitude(pos+xd),
										2.*f,
										get_wave_altitude(pos-zd) - get_wave_altitude(pos+zd)
									  ));
			}
			
			vec3 get_filtered_normale(vec2 po, vec2 px, vec2 py)
			{
				float scale=max(sea_scale.x,sea_scale.z)*filter_precision;
				
				vec3 n=vec3(0,0,0);
				
				int sx = 1 + int(clamp(int(length (px-po) * scale) , 0, max_samples -1));
				int sy = 1 + int(clamp(int(length (py-po) * scale) , 0, max_samples -1));
				int x,y ;
				for (y=0;y<sy;y++)
				{
					for (x=0;x<sx;x++)
					{
						vec2 si = vec2(float(x),float(y)) / vec2(float(sx),float(sy));
						n+=get_normale(po + (px-po) * si.x + (py-po) * si.y);
					}
				}
				
				return n/float(sx*sy);
			}
			
			//Clouds texture ======================================================
			
			float get_cloudTex_altitude(vec2 p)
			{
				float a=texture2D(clouds_map, p).r;
				return a*clouds_scale.y;
			}
			
			vec3 get_cloudTex_normale(vec2 pos)
			{
				float f=0.02;//0.02 for rt noise
				vec2 xd=vec2(f,0);
				vec2 zd=vec2(0,f);
				return normalize(vec3(
										get_cloudTex_altitude(pos-xd) - get_cloudTex_altitude(pos+xd),
										2.*f,
										get_cloudTex_altitude(pos-zd) - get_cloudTex_altitude(pos+zd)
									  ));
			}
			
			
			vec4 get_clouds_color(vec3 pos, vec3 dir)
			{
				float distance;
				vec4 c_cloud=vec4(0.,0.,0.,0.);
				if (pos.y>clouds_altitude && dir.y<-1e-4 || pos.y<clouds_altitude && dir.y>1e-4)
				{
					distance = (clouds_altitude-pos.y) / dot(vec3(0,1.,0),dir);
					vec2 p=(pos+distance*dir).xz*clouds_scale.xz;
					vec3 n_cloud=get_cloudTex_normale(p);
					c_cloud=texture2D(clouds_map, p);
					c_cloud.a=c_cloud.r;
					if (pos.y<clouds_altitude) n_cloud.y*=-1.;
					float light_cloud=dot(sun_dir,-n_cloud);
					vec3 dark_color=mix(sun_color,ambient_color,clouds_absorption);
					if (light_cloud<0.)c_cloud.rgb=mix(dark_color,sun_color,(1.-c_cloud.a)*-1.*light_cloud);
					else c_cloud.rgb=mix(dark_color,sun_color,light_cloud);
					
				}
				return c_cloud;
			}
			
			//Sea color ==========================================================
			vec3 get_sea_color(vec2 screen_coords, vec3 pos, vec3 dir, vec3 dirX, vec3 dirY,float distance, float distanceX, float distanceY,vec3 screen_dir)
			{
				vec3 n;
				vec3 p_surface=pos+dir*distance;
				if (sea_filtering==1) n=get_filtered_normale((p_surface).xz, (pos+dirX*distanceX).xz, (pos+dirY*distanceY).xz);
				else n=get_normale((pos+dir*distance).xz);
				vec2 coordsTexReflect=vec2(screen_coords.x+n.x*reflect_offset/distance,screen_coords.y+n.z*reflect_offset/distance);
				
				vec4 scene_reflect_color;
				
				if (scene_reflect==1) scene_reflect_color = texture2D(reflect_map, coordsTexReflect);
				else scene_reflect_color=vec4(0.,0.,0.,0.);
				
				vec3 dir_r=reflect(dir,n);
				vec3 c_water=get_atmosphere_color(dir);
				vec3 c_sky;
				float sun_lum = get_sun_intensity(dir_r,sun_dir);
				float zDepth=texture2D(reflect_map_depth, coordsTexReflect).r;
				float z=get_zFromDepth(screen_dir.z,zDepth);
				if (z<zFrustum.y*0.99) 
				{
					float d=z/length(screen_dir.xz);
					if (d<distance || scene_reflect_color.a<0.1) 
					{
						c_sky = get_atmosphere_color(dir*vec3(1.,-1.,1.));
						c_sky = mix(c_sky,sun_color,sun_lum);
					}
					else c_sky=scene_reflect_color.rgb;	
				}
				else c_sky=scene_reflect_color.rgb;
				
				float fresnel = (0.04 + (1.0-0.04)*(pow(1.0 - max(0.0, dot(dir,-n)), 5.0)));
				vec3 c_sea=mix(c_sky,c_water,((1.-fresnel)*sea_reflection + (1-sea_reflection)));
				vec3 c_stream = texture2D(stream_texture, p_surface.xz/50000.).rgb*0.1;
				//sun_lum=min(sun_lum+c_stream.r,1.);
				c_sea=mix(c_sea,sun_color,sun_lum);
				c_sea = min(c_sea + c_stream,vec3(1.,1.,1.));
				return c_sea;
			}
			
			
			
		%}
		
	//====================================================================================================
		
		
		source %{
			vec3 screen_ray_dir = normalize(screen_ray);
			vec3 dir=normalize(cam_normal*screen_ray_dir);
			vec4 clouds_color;
			
			//Reflect UV:
			//vec2 screen_coord=(%in.fragcoord%.xy*vInverseInternalResolution.xy)*vec2(1.,-1.)+vec2(0.,1.);
			

			vec3 color;
			float distance;
			if (dir.y>0) 
				{
					distance = zFrustum.y*0.99;
					color = get_atmosphere_color(dir);
					color=get_sky_color(dir,sun_dir,sun_color,color);
					clouds_color = get_clouds_color(cam_position,dir);
					color = mix(color,clouds_color.rgb,clouds_color.a);
				}
			else 
			{
				vec3 dirX=normalize(cam_normal*normalize(screen_ray_X));
				vec3 dirY=normalize(cam_normal*normalize(screen_ray_Y));
				if (cam_position.y<=0.)
				{
					color=get_atmosphere_color(dir);
				}
				else
				{
					distance = cam_position.y / dot(vec3(0,-1,0),dir);
					float distanceX = cam_position.y / dot(vec3(0,-1,0),dirX);
					float distanceY = cam_position.y / dot(vec3(0,-1,0),dirY);
					vec2 screen_coords=position*vec2(1.,-1.)+vec2(0.,1.);
					color = get_sea_color(screen_coords,cam_position, dir, dirX, dirY, distance, distanceX, distanceY,screen_ray_dir);
					clouds_color = get_clouds_color(cam_position,dir);
					color = mix(color,clouds_color.rgb,clouds_color.a);
				}
			}
	
			//Smooth horizon line:
			color = mix(color,horizon_line_color,pow(min(1.,1-abs(dir.y)),horizon_line_size));
	
			%out.color% =vec4(color,1.);
			%out.depth%=get_zDepth(screen_ray_dir.z,min(distance,zFrustum.y*0.99));
		%}
	}
}
