; FOMO desktop installer.
; Compiled by installer\build.ps1 after staging the bundle into installer\staging\.
; Per-user install (no admin/UAC) so a non-technical user never sees a privilege prompt.

#define MyAppName "FOMO"
#define MyAppVersion "0.1.0"
#define MyAppExeName "FomoControlPanel.exe"

[Setup]
AppId={{B9E5C9F4-6D2E-4B7E-9C5A-1F6E7D8A9B3C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\FOMO
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputBaseFilename=FomoSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Flags: unchecked -- Inno Setup task checkboxes default to CHECKED otherwise, which
; would silently opt every install into launch-at-login.
Name: "startupicon"; Description: "Start FOMO automatically when you log in"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
Source: "staging\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: not startupicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FOMO"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function IsWebView2Installed(): Boolean;
var
  Version: String;
begin
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

procedure InitializeWizard();
begin
  if not IsWebView2Installed() then
  begin
    MsgBox('FOMO needs the Microsoft Edge WebView2 Runtime, which is preinstalled ' +
      'on virtually all Windows 10/11 machines but wasn''t detected on this one.' + #13#10 + #13#10 +
      'Setup will continue -- if the app window fails to open afterward, install the ' +
      'WebView2 Runtime from Microsoft (search "WebView2 Runtime download") and try again.',
      mbInformation, MB_OK);
  end;
end;
