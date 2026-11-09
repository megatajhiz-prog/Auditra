; Inno Setup script for the Auditra Windows installer (built on GitHub by .github/workflows/build-installer.yml)
#define AppVer "0.2.1"
[Setup]
AppId={{8F3A6C1E-5B7D-4E2A-9C41-2D6B7A90E5F3}
AppName=Auditra
AppVersion={#AppVer}
AppPublisher=Auditra
DefaultDirName={autopf}\Auditra
DefaultGroupName=Auditra
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Auditra-Setup-{#AppVer}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=Auditra
SetupIconFile=..\assets\Auditra.ico
UninstallDisplayIcon={app}\app\Auditra.ico
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\app\*"; DestDir: "{app}\app"; Flags: recursesubdirs ignoreversion
Source: "..\assets\Auditra.ico"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\knowledge\*"; DestDir: "{app}\knowledge"; Flags: recursesubdirs ignoreversion
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: recursesubdirs ignoreversion
Source: "..\tools\*"; DestDir: "{app}\tools"; Flags: recursesubdirs ignoreversion
Source: "..\Start-Auditra.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Auditra"; Filename: "{app}\app\index.html"; IconFilename: "{app}\app\Auditra.ico"
Name: "{autodesktop}\Auditra"; Filename: "{app}\app\index.html"; IconFilename: "{app}\app\Auditra.ico"; Tasks: desktopicon
[Run]
Filename: "{app}\app\index.html"; Description: "Open Auditra now"; Flags: postinstall shellexec skipifsilent
