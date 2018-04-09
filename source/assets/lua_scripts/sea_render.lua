execution_context = hg.ScriptContextAll

--------------------------------------------------------------------------------
zenith_color = hg.Color()
horizon_N_color = hg.Color()
horizon_S_color = hg.Color()

zenith_falloff = 4.0

horizon_line_color = hg.Color(1,0,0,1)

horizon_line_size = 40.0
tex_sky_N = nil 
tex_sky_N_intensity = 1.0

noise_texture_1 = nil
noise_texture_2 = nil
noise_displacement_texture = nil
stream_texture = nil
clouds_map = nil

clouds_scale=hg.Vector3(1000,0.1,1000)

clouds_altitude = 1000.
clouds_absorption = 0.5

reflect_map = nil --renderer:LoadTexture("assets/textures/empty.png")
reflect_map_depth = nil --renderer:LoadTexture("assets/textures/empty.png")
reflect_offset=50
z_near=1
z_far=1000
zoom_factor=1
resolution = hg.Vector2(1920,1080)

time_clock = 0
cam_pos = hg.Vector3()

sea_color = hg.Color()

sea_reflection = 0.5
sea_filtering = 1
max_filter_samples = 3
filter_precision = 8
sea_scale = hg.Vector3(1/10,1,1/10)


sun_color = hg.Color()

ambient_color = hg.Color()

sun_dir = hg.Vector3(0,-1,0)

scene_reflect=0
render_sea=1

--------------------------------------------------------------------------------

function ClearFrame()
	-- only clear the depth buffer
	renderer:Clear(hg.Color.Black, 1.0, hg.ClearDepth)
	-- notify the engine that clearing has been handled
	return true
end

-- load the shader (RenderScript is run from the rendering thread)
shader = renderer:LoadShader("assets/shaders/sky_sea_render_optim.isl")

-- hook the end of opaque render pass to draw the skybox
function EndRenderPass(pass)
	if not shader:IsReadyOrFailed() then
		return -- shader is not ready yet
	end

	if  render_sea==0 then
		return
	end
	
	if pass ~= hg.RenderPassOpaque then
		return -- we're only interested in the opaque primitive pass
	end

	-- backup current view state
	local view_state = render_system:GetViewState()
	local view_rotation = view_state.view:GetRotationMatrix()

	-- configure the shader
	renderer:SetShader(shader)
	renderer:SetShaderTexture("tex_sky_N", tex_sky_N)
	renderer:SetShaderTexture("noise_texture_1", noise_texture_1)
	renderer:SetShaderTexture("noise_texture_2", noise_texture_2)
	renderer:SetShaderTexture("displacement_texture", noise_displacement_texture)
	renderer:SetShaderTexture("stream_texture", stream_texture)
	renderer:SetShaderTexture("clouds_map", clouds_map)
	renderer:SetShaderFloat3("clouds_scale",1/clouds_scale.x,clouds_scale.y,1/clouds_scale.z)
	renderer:SetShaderFloat("clouds_altitude",clouds_altitude)
	renderer:SetShaderFloat("clouds_absorption",clouds_absorption)
	if reflect_map ~= nil then renderer:SetShaderTexture("reflect_map", reflect_map) end
	if reflect_map_depth ~= nil then renderer:SetShaderTexture("reflect_map_depth", reflect_map_depth) end
	renderer:SetShaderInt("scene_reflect",scene_reflect)
	renderer:SetShaderFloat("reflect_offset",reflect_offset)
	renderer:SetShaderFloat("tex_sky_N_intensity",tex_sky_N_intensity)
	renderer:SetShaderFloat2("resolution",resolution.x,resolution.y)
	renderer:SetShaderFloat("focal_distance",zoom_factor)
	renderer:SetShaderMatrix3("cam_normal", view_rotation)
	renderer:SetShaderFloat3("cam_position", cam_pos.x,cam_pos.y,cam_pos.z)
	renderer:SetShaderFloat("zenith_falloff",zenith_falloff)
	renderer:SetShaderFloat3("zenith_color", zenith_color.r, zenith_color.g, zenith_color.b)
	renderer:SetShaderFloat3("horizonH_color", horizon_N_color.r, horizon_N_color.g,horizon_N_color.b)
	renderer:SetShaderFloat3("horizonL_color", horizon_S_color.r, horizon_S_color.g,horizon_S_color.b)
	renderer:SetShaderFloat3("horizon_line_color", horizon_line_color.r,horizon_line_color.g,horizon_line_color.b)
	renderer:SetShaderFloat("horizon_line_size", horizon_line_size)
	renderer:SetShaderFloat("time", time_clock)
	renderer:SetShaderInt("sea_filtering", sea_filtering)
	renderer:SetShaderInt("max_samples", max_filter_samples)
	renderer:SetShaderFloat("filter_precision", filter_precision)
	renderer:SetShaderFloat("sea_reflection", sea_reflection)
	renderer:SetShaderFloat3("sea_scale", 1/sea_scale.x, sea_scale.y, 1/sea_scale.z)
	renderer:SetShaderFloat3("sea_color", sea_color.r, sea_color.g, sea_color.b)
	renderer:SetShaderFloat2("zFrustum", z_near, z_far)

	renderer:SetShaderFloat3("sun_dir",sun_dir.x,sun_dir.y,sun_dir.z)
	renderer:SetShaderFloat3("sun_color", sun_color.r, sun_color.g, sun_color.b)
	renderer:SetShaderFloat3("ambient_color", ambient_color.r, ambient_color.g, ambient_color.b)
	-- configure the frame buffer so that only background pixels are drawn to
	renderer:EnableDepthTest(true)
	renderer:EnableDepthWrite(false)
	renderer:SetDepthFunc(hg.DepthLessEqual)
	render_system:DrawFullscreenQuad(render_system:GetViewportToInternalResolutionRatio())
	renderer:EnableDepthWrite(true)
	renderer:EnableDepthTest(true)

	-- restore view state
	render_system:SetViewState(view_state)
end
