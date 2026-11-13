import pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parent
adb=sys.argv[1] if len(sys.argv)>1 else 'adb'
serial=sys.argv[2] if len(sys.argv)>2 else sys.exit('Usage: python Restore.py adb TV_ID')
def run(*args, **kw): subprocess.run([adb,'-s',serial,*args],check=True,**kw)
pkg='com.gathin.tvhome'
run('install','-r',str(root/'Accessibility Launcher.apk'))
run('shell','am','force-stop',pkg)
run('exec-in','run-as',pkg,'tar','-xf','-',input=(root/'launcher-data.tar').read_bytes())
print('Launcher restored. Open Accessibility Launcher on the TV.')
