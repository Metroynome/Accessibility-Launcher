# Accessibility Launcher

A home screen for Android TV and Google TV designed for low vision. The selected tile grows over its neighbors. A large bold header names the selected app on every row and scrolls when the name is too long. The included preset uses a black background and five apps per row.

## Easy installation

1. Download **Accessibility.Launcher.zip** under Assets on the [latest release page](https://github.com/Metroynome/Accessibility-Launcher/releases/latest).
2. On a computer on the same network as your TV, attach the ZIP to a coding assistant with terminal access and paste the [installation prompt](docs/Accessibility%20Launcher%20AI%20Prompt.txt).
3. Follow its pairing instructions, preview the launcher, and try the remote before choosing whether to make it Home.

## Manual installation

You'll need Android TV 8.0 or newer, Python 3, and [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) with adb on your PATH.

1. Extract the release ZIP. Enable debugging in the TV's Developer options. Use adb connect with the address shown by your TV. For Wireless debugging, use adb pair with the pairing address first, then adb connect with the separate connection address. Accept the authorization prompt on the TV.
2. Run adb devices and copy your TV identifier. Replace TV_ID below with that identifier. Check the active user with adb -s TV_ID shell am get-current-user. The bundled restore script targets Android user 0. For another user, follow the guided installation above. If you already use this launcher, back up its preferences and order before restoring.
3. In a terminal inside the extracted folder, run:

~~~sh
python Restore.py adb TV_ID
adb -s TV_ID shell am start -n com.gathin.tvhome/.MainActivity
~~~

4. Try moving between rows. Open launcher settings to adjust header size, bold text, tile growth and spacing. If your TV offers a default Home chooser, select this launcher there. Select your previous Home in the same chooser to switch back. Turn debugging off when finished.

## Development

Open the project in Android Studio with JDK 17 and Android SDK 34. Run gradlew.bat assembleDebug on Windows or ./gradlew assembleDebug on macOS/Linux. The APK appears in app/build/outputs/apk/debug/. The preset directory contains the saved preferences and order.

v1.0.0 identifies the original shared ZIP. Its APK retains the upstream Android version name 3.4 and version code 13. For in-place updates, preserve the package ID and signing key and increase the version code.

Based on [CleanYourTV](https://github.com/Gathin23/cleanyourtv) at b95380483c9716b0bce6c151fa8de6b1f5000265 with accessibility and layout changes. See LICENSE and the included font and icon licenses.

## Publish an update

On the maintainer's Windows PC, start Docker Desktop, commit your changes, and push main. From the repository folder run:

~~~powershell
python tools/release.py 1.0.1
~~~

Use the next unused version in place of 1.0.1. The script runs unit tests, builds the APK, verifies the original signing certificate, packages the preset and installer, and publishes a GitHub release. It uses the GitHub sign-in saved by Git Credential Manager. Add `--check` to build and verify locally without publishing. The ZIP is written to build/distributions/.

The original signing key lives in the Docker volume `cleanyourtv-gradle` under .android. Back up that volume privately before replacing this PC or resetting Docker. On another PC, restore the key at the same path. To update an existing TV while keeping its preferences, extract the new ZIP and run `adb -s TV_ID install -r "Accessibility Launcher.apk"`. Use Restore.py when you want to apply the shared preset.
