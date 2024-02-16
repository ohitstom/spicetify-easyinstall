block_cipher = None

a = Analysis(['Spicetify-Easyinstall.py'],
             pathex=[],
             datas=[
             ( 'resources/fonts', 'fonts' ),
             ( 'resources/icons', 'icons' ),
             ( 'resources/notes', 'notes' )
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          exclude_binaries=True,
          name='Spicetify-Easyinstall',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          uac_admin=False,
          icon='resources/icons/icon.ico',
          contents_directory='resources')
