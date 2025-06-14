import os
import sys

script_path = "/Users/aj/Documents/blender-screen-space-hatch-lines/experiment.py"
__file__ = script_path

module_path = os.path.dirname(os.path.abspath(__file__))
print("Module path:", module_path)
if module_path not in sys.path:
    sys.path.append(module_path)

modules_to_remove = [module for module in sys.modules if module.startswith("screen_space")]
print("Modules to remove:", modules_to_remove)
for module in modules_to_remove:
    del sys.modules[module]

exec(open(script_path).read())
