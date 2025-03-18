import os
import sys

# add parent dir to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.abspath(os.join(current_dir, os.pardir, os.pardir))
sys.path.append(workspace_dir)
