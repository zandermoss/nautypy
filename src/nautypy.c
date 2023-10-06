#include "nautypy.h"
#include "nausparse.h"    /* which includes nauty.h */
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

void canonize(int _nv, size_t _nde, size_t* _v, int* _d, int* _e, int* lab, int* ptn, int* n_auts, int*** auts)
{
	*n_auts = 0;	
	
	*auts = NULL;

	void store_auts(int count, int* perm, int* orbits, int numorbits, int stabvertex, int n)
	{
		*n_auts = *n_auts + 1;
		*auts = realloc(*auts,(*n_auts)*(sizeof (int*)));
		(*auts)[*n_auts-1] = malloc(n*sizeof(int));	
		memcpy((*auts)[*n_auts-1],perm,n*sizeof(int));
	}

    DYNALLSTAT(int,orbits,orbits_sz);
    static DEFAULTOPTIONS_SPARSEGRAPH(options);
    statsblk stats;
    sparsegraph sg;   /* Declare sparse graph structure */
    sparsegraph canonsg;   /* Declare sparse graph structure */

	//options.writeautoms = TRUE;
	//options.defaultptn = TRUE; 
    options.defaultptn = FALSE; // Use initial partition from function argument.
	options.getcanon = TRUE; // Compute canonical labeling. Will be stored in lab.
	options.userautomproc = store_auts; // Store automorphisms as they are found.

	//Initialise sparse graph structure.
    SG_INIT(sg);
    SG_INIT(canonsg);

    int m = SETWORDSNEEDED(_nv);
    nauty_check(WORDSIZE,m,_nv,NAUTYVERSIONID);

    DYNALLOC1(int,orbits,orbits_sz,_nv,"malloc");

	/* SG_ALLOC makes sure that the v,d,e fields of a sparse graph
    structure point to arrays that are large enough.  This only
    works if the structure has been initialised. */
    SG_ALLOC(sg,_nv,_nde,"malloc");
    SG_ALLOC(canonsg,_nv,_nde,"malloc");

    sg.nv = _nv;  //Number of vertices
    sg.nde = _nde; //Number of directed edges

	// Copy the graph structure from canonize() arguments.
	memcpy(sg.v, _v, _nv*sizeof(size_t));
	memcpy(sg.d, _d, _nv*sizeof(int));
	memcpy(sg.e, _e, _nde*sizeof(int));

	// Run nauty.
    sparsenauty(&sg,lab,ptn,orbits,&options,&stats,&canonsg);

	// Free memory.
	SG_FREE(sg);
	SG_FREE(canonsg);
	DYNFREE(orbits,orbits_sz);

}
