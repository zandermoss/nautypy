=======
nautypy
=======
**nautypy** provides an interface between the `NetworkX network analysis library <https://networkx.org/>`_ and the `NAUTY graph canonization library <https://pallini.di.uniroma1.it/>`_, extending the latter to support multigraphs with arbitrary vertex and edge attributes (colors). Graphs are encoded as `networkx.Graph` or `networkx.MultiGraph` objects, and calls from Python to NAUTY are made through the `C Foreign Function Interface <https://cffi.readthedocs.io/en/stable/>`_.

Development of nautypy was motivated by the problem of finding isomorphisms among Feynman diagrams
(and off-shell diagrams) in quantum field theory calculations. Frequently, one is presented with a large number of graphs resulting from Wick contraction (or cut merging) and wishes to partition them by isomorphism class.

NetworkX has built-in methods for pair-wise isomorphism (graph matching), but using pair matching to classify n graphs into m isomorphism classes requires O(n*m) comparisons. Canonization, on the other hand, produces representative isomorphs for each class, and thus permits classification with O(n) canonization operations, plus the (trivial) overhead of hash table insertion.

There is a nice, pre-existing Python interface to NAUTY, `pynauty <https://github.com/pdobsan/pynauty>`_, but it does not support multigraphs, which are essential for calculations with loop diagrams, nor does it integrate with NetworkX out of the box.

Usage of `nautypy` is demonstrated in the examples. Translation between multigraphs and simple graphs is explained in detail in `examples/3flavor_hostgraphs.py` and in the documentation.

Installation
============
* The C interface to NAUTY, `libnautypy`, is built from source (`src/nautypy.c`, `include/nautypy.h`) using the `Meson build system <https://mesonbuild.com>`_.
If you are unfamiliar with Meson, take a look at their `in-depth tutorial <https://mesonbuild.com/IndepthTutorial.html>`_.

* The python module `nautypy` calls the C function `canonize()` defined in `libnautypy` using the `C Foreign Function Interface <https://cffi.readthedocs.io/en/stable/>`_.
If you are unfamiliar with CFFI, check out this `excellent build tutorial <https://dmerej.info/blog/post/chuck-norris-part-5-python-cffi/>`_.

* The `nautypy` python module is built from `python/nautypy.py` and `libnautypy` using a setuptools script `python/setup.py` and a CFFI script `python/cffibuild_nautypy.py`.

QuickStart
----------
* Build nauty (with ``-fPIC`` in CFLAGS!) and install (see Section 16 of the `NAUTY User's Guide <https://pallini.di.uniroma1.it/Guide.html>`_ for installation details). 
* To build the nautypy C library (the C interface, which contains `canonize()`)::

    meson setup build
    cd build
    meson compile -v
    cd ..

* To build and install the python module `nautypy`::

    cd python
    (if python/build/ exists, rm -rf build/)
    python3 setup.py build_ext
    sudo pip install .

* Try it out with one of the example scripts.


FIXME: testing!
