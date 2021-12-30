Create textures from [ShaderToy](https://www.shadertoy.com/) shaders on Blender 3.0.

This is a slight modification of [glslTexture](https://github.com/patriciogonzalezvivo/glslTexture) from Patricio Gonzalez Vivo to follow the ShaderToy shader conventions.

Supported shader inputs:

- [x] _iResolution_ - viewport resolution (in pixels)
- [x] _iTime_ - shader playback time (in seconds)
- [ ] _iTimeDelta_ - render time (in seconds)
- [x] _iFrame_ - shader playback frame
- [ ] _iChannelTime[4]_ - channel playback time (in seconds)
- [ ] _iChannelResolution[4]_ - channel resolution (in pixels)
- [ ] _iMouse_ - mouse pixel coords. xy: current (if MLB down), zw: click
- [ ] _iChannel0..3_ - input channel. XX = 2D/Cube
- [x] _iDate_ - (year, month, day, time in seconds)
- [ ] _iSampleRate_ - sound sample rate (i.e., 44100)



# Install

![](imgs/04.png)

1. Click on "Clone or Download"
2. Click on "Download ZIP"
3. Click "Edit" > "Preferences..." > "Add-ons"
4. Click install and load the zip file you just download
5. Check the box next to "GlslTexture"

![](imgs/05.png)

# Use

1. Operator Search: `F3` (or `SpaceBar` depending on your setup). Type `GlslTexture`

![](imgs/00.png)

2. Change `width` and `height` size and `Source` file (which can be a path to an external file). 

![](imgs/01.png)

3. Use the Image on your materials. The Image name will be based on the name of the source file.

![](imgs/02.png)

4. Go to the Text Editor (or an external editor if your source file is external) and edit the shader. It will hot reload.

![](imgs/03.png)

The uniform specs will be the same that: 

* [The Book of Shaders](https://thebookofshaders.com/): gentel guide into shaders
* [PixelSpirit Deck](https://patriciogonzalezvivo.github.io/PixelSpiritDeck/): esoteric tarot deck, where each card builds on top of each other a portable library of generative GLSL code.
* [glslCanvas](https://github.com/patriciogonzalezvivo/glslCanvas/): Js/WebGL
* [glslEditor](https://github.com/patriciogonzalezvivo/glslEditor/): Js/WebGL/Electron editor
* [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer): C++/OpenGL ES 2.0 native app for win/osx/linux/raspberry pi 
* [ofxshader](https://github.com/patriciogonzalezvivo/ofxShader/): Openframeworks addon
* [vscode-glsl-canvas](https://marketplace.visualstudio.com/items?itemName=circledev.glsl-canvas): live WebGL preview of GLSL shaders for VSCode made by [Luca Zampetti](https://twitter.com/actarian)
* [shader-doodle](https://github.com/halvves/shader-doodle): A friendly web-component for writing and rendering shaders made by [@halvves](https://twitter.com/halvves)

So far the supported uniforms are:

* `uniform vec2  u_resolution;`: 2D vector with the width and height of the target texture  
* `uniform float u_time;`: float variable with the amount of seconds of the timeline 

# Roadmap

[ ] Reaload GlslTextures (actually any image with the same name that a text on a project)
[ ] Improve performance for animation
[ ] it's possible to make this a node to pass uniforms in?
[ ] Multi buffers?