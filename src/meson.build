project(
  'Bubvol',
  ['vala', 'c'],
  version: '0.1',
  license: 'GPL-3.0',
  meson_version: '>=1.1.0',
  default_options: [
    'buildtype=debugoptimized',
  ]
)

version = meson.project_version()
name = meson.project_name()
extless_name = name
extless_v_name = extless_name + '-' + version
lib_name = extless_name.to_lower()
header_name = extless_name.to_lower() + '.h'
vapi_name = extless_name.to_lower() + '.vapi'
gir_name = extless_v_name + '.gir'
lib_dependency_name = extless_name.to_lower()
typelib_name = extless_v_name + '.typelib'
typelib_target_name = extless_name.to_lower() + '_typelib'

dependencies = [
  dependency('glib-2.0'),
  dependency('gobject-2.0'),
  dependency('amlcore'),
  dependency('amlparticles'),
  dependency('amltypes'),
  dependency('amlmath'),
]

sources = files(
  'computevolume.vala',
)

lib = shared_library(
  lib_name,
  sources,
  vala_header: header_name,
  vala_vapi: vapi_name,
  vala_gir: gir_name,
  version: version,
  dependencies: dependencies,
  install: true,
  install_dir: [ true, true, true, true ],
)

g_ir_compiler = find_program('g-ir-compiler')
typelib = custom_target(
  typelib_target_name,
  command: [
    g_ir_compiler,
    '--shared-library',
    lib.full_path(),
    '--output',
    '@OUTPUT@',
    meson.current_build_dir() / gir_name,
  ],
  output: typelib_name,
  depends: lib,
  install: true,
  install_dir: '/usr/lib/girepository-1.0',
)
