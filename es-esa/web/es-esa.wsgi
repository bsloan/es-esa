import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

print sys.path
print "Current working directory:", os.getcwd()

activate_this = "/Users/bsloan/Workspace/es-esa/venv/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

from main import app as application
