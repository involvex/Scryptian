Name "Scryptian"
OutFile "Scryptian Installer.exe"
InstallDir "$PROGRAMFILES\Scryptian"
RequestExecutionLevel admin
Icon "icon.ico"
Section
  SetOutPath "$INSTDIR"
  File "dist\Scryptian.exe"
  CreateShortCut "$DESKTOP\Scryptian.lnk" "$INSTDIR\Scryptian.exe" "" 0
  CreateDirectory "$SMPROGRAMS\Scryptian"
  CreateShortCut "$SMPROGRAMS\Scryptian\Scryptian.lnk" "$INSTDIR\Scryptian.exe" "" 0
SectionEnd
