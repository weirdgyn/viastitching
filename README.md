# ViaStitching

Via Stitching action-plugin

Fill a selected copper area with a pattern of vias.

## When to use this tool

Whenever you need to fill a copper area with vias to improve thermal or current conduction this tool is the answer (yet not the best one probably). The plugin is based on premade areas so you have to define one before invoking the plugin.

## How it works

The workflow is pretty simple: select the area you want to fill, click on ```Tools->External Plugins->ViaStitching``` or click on ![AddNet icon](viastitching.png?raw=true) toolbar icon: a dilaog like the one below should appear:

![AddNet dialog](pictures/viastitching_dialog.PNG?raw=true "ViaStitching dialog")

The vias you're going to create needs to have an assigned net usually this's the net assigned to the surrouding area (the one you select  I guess) for this reason the plugin pre-select this net for you in the combobox but of course you're free to select another net if you like.
The plugin dialog let you also specify the main parameters for the via creation (via size and drill size), the values you find in the textboxes are taken from the configuration of the board but you can change them. The other parameters to set here are the vertical and horizzontal spacing between each vias you can customize them also.
When you're satisfied with your settings you just need to press __Ok__ button and the fillup begin.
If everything goes fine you'll get something like this:

![viastitching result](pictures/viastitching_result.PNG?raw=true "ViaStitching result")

## Coding notes

If you are willing to make any modification to the GUI (you're welcome) trough __wxFormBuilder__ (```viastitching.fbp``` file) remember to modify this line (around line 21 ```viastitching_gui.py```):
```
self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
```
In this way:
```
if sys.version_info[0] == 2:
 self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
else:
 self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
```
This modification allows the code to work with __Python 2__ (that's the standard KiCAD/Python distribution AFAIK) as long as __Python 3__, please note that you need to ```import sys```. Special thanks to *NilujePerchut* for this hint.

## kicad-action-scripts - ViaStitching plugin similarity

Yes my plugin is pretty similar to this plugin but I'm using a radical different approach in coding. At the time I wrote this plugin unluckly __jsreynaud__ plugin wasn't working but I bet he will fix it.

## References

Some useful references that helped me coding this plugin:
1. https://sourceforge.net/projects/wxformbuilder/
2. https://wxpython.org/
3. http://docs.kicad-pcb.org/doxygen-python/namespacepcbnew.html
4. https://forum.kicad.info/c/external-plugins
5. https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md
6. https://kicad.mmccoo.com/
7. http://docs.kicad-pcb.org/5.1.4/en/pcbnew/pcbnew.html#kicad_scripting_reference


Tool I got inspired by:
- Altium Via Stitching feature!
- https://github.com/jsreynaud/kicad-action-scripts

## Greetings

Hope someone find my work useful or at least *inspiring* to create something else/better.
I would like to thank everyone has shared his knoledge of Python and KiCAD with me: Thanks!

Live long and prosper!

That's all folks.

By[t]e{s}
 Weirdgyn
