execution_context = hg.ScriptContextAll

--------------------------------------------------------------------------------

local scale_min = 50
local scale_max = 400
local clouds = {}

function load_object(plus,geometry_file_name, name,duplicate_material)
	print(name)
	renderSystem = plus:GetRenderSystem()
    nd = hg.Node(name)
    trans = hg.Transform()
    nd:AddComponent(trans)
    obj = hg.Object()
    geo = hg.LoadCoreGeometry(geometry_file_name)
    if geo ~= nil then
        geo = renderSystem:CreateGeometry(geo,false)
        if duplicate_material then
            material = geo:GetMaterial(0)
            material = material:Clone()
            geo:SetMaterial(0,material)
		end
        obj:SetGeometry(geo)
        nd:AddComponent(obj)
	end
    return nd
end


function uniform(vmin,vmax)
	return math.random()*(vmax-vmin)+vmin
end

function create_cloud_particles(name, plus, scene, node_file_name, num_particles)
    particles = {}
    for i=1,num_particles,1 do
        x = uniform(-1000, 1000)
        y = uniform(0, 200)
        z = uniform(-500, 500)
        s = uniform(scale_min, scale_max)
        node = load_object(plus, node_file_name, name .. "." .. i, true)
        node:GetTransform():SetPosition(hg.Vector3(x, y, z))
        node:GetTransform():SetScale(hg.Vector3(s, s, s))
        scene:AddNode(node)
        table.insert(particles,node)
	end
    return particles
end
		
function update_clouds(particles, dts)
    c = hg.Color(1., 1., 1., 1.)
    for i,nd in pairs(particles) do
        s = nd:GetTransform():GetScale().x
        c.a = (1-(s - scale_min) / (scale_max - scale_min))*0.5
        nd:GetObject():GetGeometry():GetMaterial(0):SetFloat4("teint", c.r, c.g, c.b, c.a)
        rot = nd:GetTransform():GetRotation()
        rot.x = rot.x + 0.5 * dts
        rot.y = rot.y + 0.125 * dts
        rot.z = rot.z + 0.073 * dts
        nd:GetTransform():SetRotation(rot)
	end
end


--------------------------------------------------------------------------------

function Setup()
	clouds = create_cloud_particles("cloudz",hg.GetPlus(),this,"assets/clouds/cloud_particle_12.geo", 100)
	return true
end

function Update()
	plus=hg.GetPlus()
	delta_t = plus:UpdateClock()
    dts=hg.time_to_sec_f(delta_t)
	update_clouds(clouds,dts)
	--return true
end