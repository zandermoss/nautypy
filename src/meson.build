libnautypy = static_library('nautypy',
            'nautypy.c',
            include_directories : build_includedir,
            dependencies : nauty_dep,
            install : true,
	    install_dir : get_option('libdir') / suffix
	    )
