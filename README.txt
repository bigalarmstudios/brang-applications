BRANG APPLICATIONS
==================

This repository is the app catalogue for Brang OS. It is published to GitHub,
and Brang OS downloads scripts from appFiles when a user chooses Get App.

THIS IS NOT A USER DOWNLOAD
---------------------------
Normal users should download and set up brang_os only. Keep this repository
public on GitHub: Brang OS reads its catalogue and downloads selected apps from
there automatically through the Big Alarm Store. Clone this repository only if
you are maintaining or developing Brang apps.

ADDING OR UPDATING AN APP
-------------------------
1. Add an app script to appFiles, for example: appFiles/myApp.py.
2. Add the same name and a version to catalougeAlone/catalogue.txt:
       myApp,1.0
3. Commit and push this repository's main branch. Brang OS reads that branch.

APP CONTRACT
------------
- An app must expose update(events) and render(screen).
- Optional: load_file(path) receives a file from the built-in file explorer.
- Do not create another Pygame window while running inside Brang OS.
- Use the BRANG_OS_HOME environment variable for Brang OS's root folder;
  do not use os.getcwd(), because a user can start Brang OS from any folder.
- Store user-created files only inside BRANG_OS_HOME/files.

LOCAL DEVELOPER TESTING
-----------------------
Install the dependency with:
    py -3 -m pip install -r requirements.txt

Then copy the app into brang_os/programs/installedApps and start Brang OS.
Keep the catalogue filename spelling as "catalougeAlone" for compatibility
with existing Brang OS releases.

SETTINGS APP
------------
The Settings app stores simple preferences only on the user's computer, under
Brang OS's programs\cache folder. It currently controls the desktop theme,
cursor-square size, and whether the Big Alarm Store may reuse its local
catalogue cache. The user must restart Brang OS after saving to apply changes.
