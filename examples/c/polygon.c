/* This program prints generators for the automorphism group of an
   n-vertex polygon, where n is a number supplied by the user.
   This version uses sparse form with dynamic allocation.
*/

#include "nautypy.h"    /* which includes nauty.h */
#include "nausparse.h"

int
main(int argc, char *argv[])
{
	sparsegraph sg;

    int n,m,i;

	n=4;

 /* Initialise sparse graph structure. */

    SG_INIT(sg);
	
    m = SETWORDSNEEDED(n);
    nauty_check(WORDSIZE,m,n,NAUTYVERSIONID);

 /* SG_ALLOC makes sure that the v,d,e fields of a sparse graph
    structure point to arrays that are large enough.  This only
    works if the structure has been initialised. */

    SG_ALLOC(sg,n,2*n,"malloc");

    sg.nv = n;              /* Number of vertices */
    sg.nde = 2*n;           /* Number of directed edges */

    for (i = 0; i < n; ++i)
    {
        sg.v[i] = 2*i;
        sg.d[i] = 2;
        sg.e[2*i] = (i+n-1)%n;      /* edge i->i-1 */
        sg.e[2*i+1] = (i+n+1)%n;    /* edge i->i+1 */
    }


	int n_auts;
	int** auts;

	int* lab = malloc(n*sizeof(int));
	int* ptn = malloc(n*sizeof(int));

	for(int j=0; j<sg.nv; j++)
	{
		lab[j] = j;
		ptn[j] = 1;
	}

	canonize(sg.nv, sg.nde, sg.v, sg.d, sg.e, lab, ptn, &n_auts, &auts);

	printf("CANON LABEL\n(");
	for(int j=0; j<sg.nv; j++)
	{
		printf("%d ",lab[j]);
	}
	printf(")\n");

	printf("AUTS\n");
	for(int i=0; i<n_auts; i++)
	{
		printf("(");
		for(int j=0; j<sg.nv; j++)
		{
			printf("%d ",auts[i][j]);
		}
		printf(")\n");
	}


	free(lab);
	free(ptn);
	for(int i=0; i<n_auts; i++)
	{
		free(auts[i]);
	}
	free(auts);
	SG_FREE(sg);	

//    exit(0);
	return 0;
}
