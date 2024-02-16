block_cipher = None

a = Analysis(['Spicetify-Easyinstall.py'],
             pathex=[],
             binaries=[],
             datas=[('resources', 'resources_spec')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
             
splash = Splash('resources/icons/icon.png',
                binaries=a.binaries,
                datas=a.datas,
                text_pos=(10, 50),
                text_size=12,
                text_color='black')
                
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          splash,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Spicetify-Easyinstall',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          uac_admin=False,
          icon='resources/icons/icon.ico')

coll = COLLECT(exe,
               splash.binaries,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Spicetify-Easyinstall')
