"""Package only public assets. Never copy local records/backups into a deployment."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
out=root/'public'
if out.exists(): shutil.rmtree(out)
shutil.copytree(root/'static',out)
# Authenticated manifests come from the Python function.
(out/'manifest.webmanifest').unlink(missing_ok=True)
print('Public assets packaged.')
