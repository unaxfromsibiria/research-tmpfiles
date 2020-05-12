#include <stdlib.h>
#include <string.h>

#define NEIGHBORS_COUNT 8

int x_delta[NEIGHBORS_COUNT] = {-1, 0, 1, -1, 1, -1, 0, 1};
int y_delta[NEIGHBORS_COUNT] = {-1, -1, -1, 0, 0, 1, 1, 1};

void make_step(int size, int *state)
{
    int i, j, k, l, m = 0;
    int n = size + 2;
    int index_size = n - 1;
    k = sizeof(int) * n * n;
    int *state_copy = malloc(k);
    memcpy(state_copy, state, k);

    for (i = 0; i < size; i++)
    {
        for (j = 0; j < size; j++)
        {
            k = i + j * n;
            if ((0 < i) && (i < index_size) && (0 < j) && (j < index_size))
            {
                m = 0;
                for (l = 0; l < NEIGHBORS_COUNT; l++)
                {
                    if (state_copy[(i + x_delta[l]) + (j + y_delta[l]) * n] > 0)
                    {
                        m++;
                    }
                }
                state[k] = ((m == 3 || (state_copy[k] == 1 && m == 2)) ? 1 : 0);
            }
            else
            {
                state[k] = 0;
            }
        }
    }
}
