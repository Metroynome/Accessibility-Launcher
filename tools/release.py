"""Build and publish an Accessibility Launcher update from the repository root."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import urllib.request
import zipfile

def run(*args):
	return subprocess.check_output(args, text=True).strip()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("version", help="Three version numbers, for example 1.0.1")
parser.add_argument("--check", action="store_true", help="Build and verify locally")
args = parser.parse_args()
version = args.version
if not re.fullmatch(r"[1-9]\d?\.(?:0|[1-9]\d?)\.(?:0|[1-9]\d?)", version):
	parser.error("Use major.minor.patch, with each number under 100.")
os.chdir(Path(__file__).resolve().parents[1])
major, minor, patch = map(int, version.split("."))
code = major * 10000 + minor * 100 + patch
tag = "v" + version
repo = "Metroynome/Accessibility-Launcher"
head = run("git", "rev-parse", "HEAD")
if not args.check:
	if run("git", "status", "--porcelain") or run("git", "branch", "--show-current") != "main":
		parser.error("Commit your changes on main first.")
	remote = "https://github.com/" + repo + ".git"
	if run("git", "ls-remote", remote, "refs/heads/main").split()[0] != head:
		parser.error("Push main before releasing.")
	for line in run("git", "ls-remote", "--tags", remote).splitlines():
		match = re.search(r"refs/tags/v(\d+)\.(\d+)\.(\d+)$", line)
		if match and tuple(map(int, match.groups())) >= (major, minor, patch):
			parser.error("Choose a version above the latest published tag.")

image = "cleanyourtv-android-build"
if subprocess.run(["docker", "image", "inspect", image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
	subprocess.run(["docker", "build", "-t", image, "-f", "tools/Dockerfile", "tools"], check=True)
docker = ["docker", "run", "--rm", "-v", str(Path.cwd()) + ":/repo", "-v", "cleanyourtv-gradle:/gradle", "-w", "/repo", "-e", "ANDROID_USER_HOME=/gradle/.android", image]
apk = Path("app/build/outputs/apk/debug/app-debug.apk")
subprocess.run([*docker, "sh", "./gradlew", "testDebugUnitTest", "assembleDebug", "-PreleaseCode="+str(code), "-PreleaseName="+version], check=True)
cert = run(*docker, "/opt/android-sdk/build-tools/34.0.0/apksigner", "verify", "--print-certs", apk.as_posix())
if "Signer #1 certificate SHA-256 digest: b1ca57f7fe7144d627eeaf8fa04d9e32d790ff130174bf6551e5809715896ca2" not in cert.splitlines():
	raise SystemExit("Signing key differs from v1.0.0. Restore the original key.")
order = Path("preset/order.txt").read_bytes()
tar = io.BytesIO()
with tarfile.open(fileobj=tar, mode="w") as archive:
	for name, data in [("files/order.txt", order), ("shared_prefs/launcher_settings.xml", Path("preset/launcher_settings.xml").read_bytes())]:
		info = tarfile.TarInfo(name)
		info.size = len(data)
		archive.addfile(info, io.BytesIO(data))
items = {"Accessibility Launcher.apk":apk.read_bytes(), "launcher-data.tar":tar.getvalue(), "app-order.txt":order, "Restore.py":Path("tools/Restore.py").read_bytes(), "README.txt":Path("README.md").read_bytes()}
items["SHA256.txt"] = "".join(hashlib.sha256(data).hexdigest()+"  "+name+"\n" for name,data in items.items()).encode()
output = Path("build/distributions") / tag / "Accessibility.Launcher.zip"
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
	for name,data in items.items():
		archive.writestr(name,data)
with zipfile.ZipFile(output) as archive:
	if any(archive.read(name)!=data for name,data in items.items()):
		raise SystemExit("ZIP verification failed.")
print("Verified",output,flush=True)
if args.check:
	raise SystemExit(0)

credential = subprocess.check_output(["git","credential","fill"],input="protocol=https\nhost=github.com\nusername=Metroynome\n\n",text=True)
token = dict(line.split("=",1) for line in credential.splitlines() if "=" in line)["password"]
def request(url, data, method="POST", kind="application/json"):
	body = data if isinstance(data,bytes) else json.dumps(data).encode()
	req = urllib.request.Request(url,data=body,method=method,headers={"Authorization":"Bearer "+token,"User-Agent":"Accessibility-Launcher-release","Content-Type":kind})
	with urllib.request.urlopen(req,timeout=90) as response:
		return json.load(response)

api = "https://api.github.com/repos/"+repo+"/releases"
# Resume a draft if an upload or network request failed.
req = urllib.request.Request(api+"?per_page=100",headers={"Authorization":"Bearer "+token,"User-Agent":"Accessibility-Launcher-release"})
with urllib.request.urlopen(req,timeout=30) as response:
	draft = next((r for r in json.load(response) if r["draft"] and r["tag_name"]==tag),None)
if draft is None:
	draft = request(api,{"tag_name":tag,"target_commitish":head,"name":"Accessibility Launcher "+tag,"draft":True,"generate_release_notes":True})
if draft["target_commitish"] != head:
	raise SystemExit("Existing draft targets a different commit. Review it on GitHub.")
digest = "sha256:"+hashlib.sha256(output.read_bytes()).hexdigest()
asset = next((a for a in draft["assets"] if a["name"]==output.name),None)
if asset and asset.get("digest")!=digest:
	delreq = urllib.request.Request(asset["url"],method="DELETE",headers=req.headers)
	urllib.request.urlopen(delreq,timeout=30).close()
	asset = None
if not asset:
	asset = request(draft["upload_url"].split("{")[0]+"?name="+output.name,output.read_bytes(),kind="application/zip")
if asset.get("digest")!=digest:
	raise SystemExit("Uploaded asset checksum differs. Draft retained.")
print(request(draft["url"],{"draft":False},"PATCH")["html_url"])
