# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "glslTexture",
    "author": "Patricio Gonzalez Vivo, Kristian Sons",
    "description": "Adds a texture generated from a GLSL shader in ShaderToy style",
    "blender": (3, 0, 0),
    "version": (0, 0, 1),
    "location": "Add",
    "warning": "",
    "doc_url": "",
    "category": "Texture"
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

from datetime import date, datetime

FRAGMENT_DEFAULT = '''

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
    // Normalized pixel coordinates (from 0 to 1)
    vec2 uv = fragCoord/iResolution.xy;

    // Time varying pixel color
    vec3 col = 0.5 + 0.5*cos(iTime+uv.xyx+vec3(0,2,4));

    // Output to screen
    fragColor = vec4(col,1.0);
}

'''

VERTEX_DEFAULT = '''
in vec2 a_position;
in vec2 a_texcoord;

void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
}
'''

SHADERTOY_CONTEXT = '''
uniform vec3      iResolution;           // viewport resolution (in pixels)
uniform float     iTime;                 // shader playback time (in seconds)
uniform float     iTimeDelta;            // render time (in seconds)
uniform int       iFrame;                // shader playback frame
uniform float     iChannelTime[4];       // channel playback time (in seconds)
uniform vec3      iChannelResolution[4]; // channel resolution (in pixels)
uniform vec4      iMouse;                // mouse pixel coords. xy: current (if MLB down), zw: click
// uniform samplerXX iChannel0..3;       // input channel. XX = 2D/Cube
uniform sampler2D iChannel0;             // input channel 0
uniform sampler2D iChannel1;             // input channel 1
uniform sampler2D iChannel2;             // input channel 2
uniform sampler2D iChannel3;             // input channel 3
uniform vec4      iDate;                 // (year, month, day, time in seconds)
uniform float     iSampleRate;           // sound sample rate (i.e., 44100)

out vec4 shadertoy_out_color;

{}

void main( void ) {{
    vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
    mainImage( color, gl_FragCoord.xy );
    shadertoy_out_color = vec4(color.xyz, color.a);
}}

'''

class GlslTexture(bpy.types.Operator):
    """Make a texture from a Shadertoy Shader"""
    bl_idname = 'add.glsltexture'
    bl_label = 'Shadertoy Texture'
    bl_options = { 'REGISTER', 'UNDO' }
    
    width: bpy.props.IntProperty(
        name = 'width',
        description = 'Texture width',
        default = 512,
        min = 1
    )
        
    height: bpy.props.IntProperty(
        name = 'height',
        description = 'Texture height',
        default = 512,
        min = 1
    )

    source: bpy.props.StringProperty(
#        subtype="FILE_PATH",
        name = 'Source',
        description = 'Text file name which contain the frament shader source code',
        default = 'default.frag'
    )

    current_code = bpy.props.StringProperty(default = FRAGMENT_DEFAULT)
    current_time = bpy.props.FloatProperty(default = 0.0)



    @classmethod
    def poll(cls, context):
        return True
    
    def file_exist(self, filename):
        try:
            file = open( bpy.path.abspath(filename) ,'r')
            file.close()
            return True
        except:
            return False
    
    _timer = None
    
    def invoke(self, context, event):
        
        self.current_frame = 1
        self.init_resources()   
    
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            
            # If there is no reference to source on the text editor, create one
            if not self.source in bpy.data.texts:
                print(f'File name {self.source} not found. Will create an internal one')
                
                # If match an external file 
                if self.file_exist(self.source):
                    bpy.ops.text.open(filepath=self.source)

                # else create a internal file with the default fragment code
                else:
                    bpy.data.texts.new(self.source)
                    bpy.data.texts[self.source].write(FRAGMENT_DEFAULT)
            
            # If the source file is external and it have been modify, reload it
            if not bpy.data.texts[self.source].is_in_memory and bpy.data.texts[self.source].is_modified:
                print(f'External file {self.source} have been modify. Reloading...')
                text = bpy.data.texts[self.source]
                ctx = context.copy()
                #Ensure  context area is not None
                ctx['area'] = ctx['screen'].areas[0]
                oldAreaType = ctx['area'].type
                ctx['area'].type = 'TEXT_EDITOR'
                ctx['edit_text'] = text
                bpy.ops.text.resolve_conflict(ctx, resolution='RELOAD')
                #Restore context
                ctx['area'].type = oldAreaType

            render = False
            recompile = False

            now = context.scene.frame_float / context.scene.render.fps

            
            # If shader content change 
            if self.current_code != bpy.data.texts[self.source].as_string():
                recompile = True

            if self.current_time != now:
                render = True

            if render or recompile:
                self.current_code = bpy.data.texts[self.source].as_string()
                self.current_time = now
                self.current_frame = context.scene.frame_current

                shader_code = SHADERTOY_CONTEXT.format(self.current_code)
            
                offscreen = gpu.types.GPUOffScreen(self.width, self.height)
                with offscreen.bind():
                    fb = gpu.state.active_framebuffer_get()
                    fb.clear(color=(0.0, 0.0, 0.0, 0.0))
    
                    # If there is no shader or need to be recompiled
                    if self.shader == None or recompile:
                        try:    
                            self.shader = gpu.types.GPUShader(VERTEX_DEFAULT, shader_code)
                        except Exception as Err:
                            print(Err)
                            self.shader = None
                    
                    # if there is a shader and no batch
                    if (self.shader != None and self.batch == None):
                        self.batch = batch_for_shader(
                            self.shader, 
                            'TRI_FAN', {
                                'a_position': ((-1, -1), (1, -1), (1, 1), (-1, 1))
                            },
                        )
                
                    if self.shader != None:
                        self.shader.bind()
            
                        try:
                            self.shader.uniform_float('iTime', self.current_time)
                        except ValueError:
                            pass

                        try:
                            self.shader.uniform_int('iFrame', self.current_frame)
                        except ValueError:
                            pass

                        try:
                            self.shader.uniform_float('iResolution', (self.width, self.height, 0))
                        except ValueError:
                            pass

                        try:
                            n = datetime.now()
                            seconds_since_midnight = (n - n.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                            self.shader.uniform_float('iDate', (n.year, n.month, n.day, seconds_since_midnight))
                        except ValueError:
                            pass

                        self.batch.draw(self.shader)

                    buffer = fb.read_color(0, 0, self.width, self.height, 4, 0, 'FLOAT')
                    buffer.dimensions = self.width * self.height * 4
                    render = True

                offscreen.free()

                if render:
                    name = self.source
                    if not name in bpy.data.images:
                        bpy.data.images.new(name, self.width, self.height)
                    image = bpy.data.images[name]
                    image.scale(self.width, self.height)
                    image.pixels.foreach_set(buffer)
                    
        return {'PASS_THROUGH'}
    
    def init_resources(self):
        self.shader = None
        self.batch = None

    def execute(self, context):
        self.init_resources()
        wm = context.window_manager
        self.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        print(f'GlslTexture {self.source} cancel refreshing')
        if self.timer:
            wm = context.window_manager
            wm.event_timer_remove(self.timer)


@persistent
def loadGlslTextures(dummy):

    print("Looking for GlslTexture")
    for source_name in bpy.data.texts.keys():
        if source_name in bpy.data.images.keys():
            width = bpy.data.images[source_name].generated_width
            height = bpy.data.images[source_name].generated_height
            print(f"Loading GlslTexture {source_name}")
            bpy.ops.add.glsltexture('EXEC_DEFAULT', width=width, height=height, source=source_name)

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(GlslTexture.bl_idname, text=GlslTexture.bl_label,icon='COLORSET_02_VEC')

def register():

    bpy.utils.register_class(GlslTexture)
    bpy.app.handlers.load_post.append(loadGlslTextures)
    bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    bpy.app.handlers.load_post.remove(loadGlslTextures)
    bpy.utils.unregister_class(GlslTexture)
    



if __name__ == "__main__":
    register()