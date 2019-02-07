# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - VR handler -


# ===========================================================
import harfang as hg
openvr_frame_renderer=None

def is_vr_present():
    global openvr_frame_renderer
    try:
        openvr_frame_renderer = hg.CreateFrameRenderer("VR")
        print("!! VR detected")
        return True
    except:
        print("!! No VR detected")
        openvr_frame_renderer = None
        return False

def init_vr(scene:hg.Scene,plus:hg.Plus):
    global openvr_frame_renderer
    if openvr_frame_renderer is not None and openvr_frame_renderer.Initialize(plus.GetRenderSystem()):
        scene.GetRenderableSystem().SetFrameRenderer(openvr_frame_renderer)
        print("!! Use VR")
        return True
    else:
        openvr_frame_renderer = None
        print("!! Unable to initialize VR")
        return False
