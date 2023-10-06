#-----Define build project-----#
project('nautypy', 'c',
	version : '1.0',
	license : 'MIT', 
	default_options : ['prefix=/usr/local']
	)

#-----Specify build and install directories-----#
#Installation directory suffix for libdir and includedir
suffix = 'nautypy'
#Source tree include directory for the build
build_includedir = include_directories('include')

#-----Specify dependencies-----#
nauty_dep = dependency('nauty')

#-----Execute subdirectory builds-----#
#Install headers
subdir('include')
#Compile libraries/executables and toggle install flags
subdir('src')
#Compile example executables
subdir('examples/c')

#-----Invoke Meson's pkgconfig module-----#
#Generates a .pc file in libdir/pkgconfig
pkg_mod = import('pkgconfig')
pkg_mod.generate(libraries : libnautypy,
                 version : '1.0',
                 name : 'libnautypy',
                 filebase : 'nautypy',
                 #subdirs: suffix,
                 description : 'C interface to NAUTY for nautypy.')
