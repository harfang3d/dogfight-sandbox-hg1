/*

				Sky & sea render - 2017		

*/

in {
	tex2D tex_sky_N [wrap-u: clamp, wrap-v: clamp];
	tex2D reflect_map;
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
				if (dir.y<-1e-4)c_atmosphere=mix(sea_color,horizonL_color,pow(min(1.,1+dir.y),8.));
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
			
			
			//============================= Sea =============================
			
			vec3 hash(vec3 p)
			{
					p = vec3( dot(p,vec3(321.1,141.7, 0.7)),
							  dot(p,vec3(41.478,1389.3,3654.123)),
							  dot(p,vec3(468.2,21.9,1564.1321)));

					return -1.0 + 2.0*fract(sin(p)*134.53123);
			}
			
			float noise3D( vec3 x )
			{
				// grid
				vec3 p = floor(x);
				vec3 w = fract(x);
				
				// quintic interpolant
				vec3 u = w*w*w*(w*(w*6.0-15.0)+10.0);

				
				// gradients
				vec3 ga = hash( p+vec3(0.0,0.0,0.0) );
				vec3 gb = hash( p+vec3(1.0,0.0,0.0) );
				vec3 gc = hash( p+vec3(0.0,1.0,0.0) );
				vec3 gd = hash( p+vec3(1.0,1.0,0.0) );
				vec3 ge = hash( p+vec3(0.0,0.0,1.0) );
				vec3 gf = hash( p+vec3(1.0,0.0,1.0) );
				vec3 gg = hash( p+vec3(0.0,1.0,1.0) );
				vec3 gh = hash( p+vec3(1.0,1.0,1.0) );
				
				// projections
				float va = dot( ga, w-vec3(0.0,0.0,0.0) );
				float vb = dot( gb, w-vec3(1.0,0.0,0.0) );
				float vc = dot( gc, w-vec3(0.0,1.0,0.0) );
				float vd = dot( gd, w-vec3(1.0,1.0,0.0) );
				float ve = dot( ge, w-vec3(0.0,0.0,1.0) );
				float vf = dot( gf, w-vec3(1.0,0.0,1.0) );
				float vg = dot( gg, w-vec3(0.0,1.0,1.0) );
				float vh = dot( gh, w-vec3(1.0,1.0,1.0) );
				
				// interpolation
				return va + 
					   u.x*(vb-va) + 
					   u.y*(vc-va) + 
					   u.z*(ve-va) + 
					   u.x*u.y*(va-vb-vc+vd) + 
					   u.y*u.z*(va-vc-ve+vg) + 
					   u.z*u.x*(va-vb-ve+vf) + 
					   u.x*u.y*u.z*(-va+vb+vc-vd+ve-vf-vg+vh);
			}
			
			
			float noise3D_octaves ( vec3 x, int no, float fo )
			{
				float n=0.;
				float p=1;
				for(int i=0;i<no;i++)
				{
					n+=noise3D(x*pow(2.,float(i))+vec3(123.,784.,3216.)*float(i))*p;
					p*=fo;
				}
				float amplitude = 1. + pow(fo,float(no));
				return n/amplitude;
			}
			
			
			float get_wave_altitude(vec2 p)
			{
				vec3 pa = vec3(p.x*sea_scale.x,time*0.5,p.y*sea_scale.z);
				float a=noise3D_octaves(pa,2,0.75);

				//return a*min(sea_scale.y*pow(1.00015,distance),100);
				return a*sea_scale.y;
			}
			
			vec3 get_normale(vec2 pos)
			{
				float f=0.02;
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
			
			
			vec3 get_sea_color(vec3 pos, vec3 dir, vec3 dirX, vec3 dirY,float distance, float distanceX, float distanceY)
			{
				vec3 n;
				if (sea_filtering==1) n=get_filtered_normale((pos+dir*distance).xz, (pos+dirX*distanceX).xz, (pos+dirY*distanceY).xz);
				else n=get_normale((pos+dir*distance).xz);
				
				vec3 dir_r=reflect(dir,n);
				vec3 c_water=get_atmosphere_color(dir);
				vec3 c_sky=get_atmosphere_color(dir*vec3(1.,-1.,1.));
				vec3 c_sea=mix(c_sky,c_water,(pow(dot(-dir,n),2.)*sea_reflection + (1-sea_reflection)));
				float sun_lum = get_sun_intensity(dir_r,sun_dir);
				return mix(c_sea,sun_color,sun_lum);
			}
			
			float get_zDepth(float near,float far)
			{
					float a,b,z;
					z=far*near;
					a=zFrustum.y/(zFrustum.y-zFrustum.x);
					b=zFrustum.y*zFrustum.x/(zFrustum.x-zFrustum.y);
					return ((a+b/z)+1.)/2.;
			}
			
		%}
		
	//====================================================================================================
		
		
		source %{
			vec3 screen_ray_dir = normalize(screen_ray);
			vec3 dir=normalize(cam_normal*screen_ray_dir);
			
			//Reflect UV:
			//vec2 screen_coord=(%in.fragcoord%.xy*vInverseInternalResolution.xy)*vec2(1.,-1.)+vec2(0.,1.);
			vec2 screen_coord=position*vec2(1.,-1.)+vec2(0.,1.);
			vec3 scene_reflect_color = texture2D(reflect_map, screen_coord).rgb;

			vec3 color;
			float distance;
			if (dir.y>0) 
				{
					distance = zFrustum.y*0.99;
					color = get_atmosphere_color(dir);
					color=get_sky_color(dir,sun_dir,sun_color,color);
				}
			else 
			{
				vec3 dirX=normalize(cam_normal*normalize(screen_ray_X));
				vec3 dirY=normalize(cam_normal*normalize(screen_ray_Y));
				distance = cam_position.y / dot(vec3(0,-1,0),dir);
				float distanceX = cam_position.y / dot(vec3(0,-1,0),dirX);
				float distanceY = cam_position.y / dot(vec3(0,-1,0),dirY);
				color = get_sea_color(cam_position, dir, dirX, dirY, distance, distanceX, distanceY);
			}
	
			//Smooth horizon line:
			color+=scene_reflect_color;
			color = mix(color,horizon_line_color,pow(min(1.,1-abs(dir.y)),horizon_line_size));
	
			%out.color% =vec4(color,1.);
			%out.depth%=get_zDepth(screen_ray_dir.z,min(distance,zFrustum.y*0.99));
		%}
	}
}
