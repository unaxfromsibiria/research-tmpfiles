/*
cd ./cffi_impl/ && python setup.py && cd ..
*/
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <stdio.h>

#define NEIGHBORS_COUNT 8

int x_delta[NEIGHBORS_COUNT] = {-1, 0, 1, -1, 1, -1, 0, 1};
int y_delta[NEIGHBORS_COUNT] = {-1, -1, -1, 0, 0, 1, 1, 1};

typedef struct Params
{
    int *state;
    int *src_state;
    int a, b, size;
} Params;


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
    free(state_copy);
}


void *make_step_part(void *params_ptr)
{
    struct Params *params = (struct Params *)params_ptr;
    int i, j, k, m, l;
    int size = params->size;
    int n = size + 2;
    int index_size = n - 1;

    for (i = params->a; i < params->b; i++)
    {
        for (j = 0; j < size; j++)
        {
            k = i + j * n;
            if ((0 < i) && (i < index_size) && (0 < j) && (j < index_size))
            {
                m = 0;
                for (l = 0; l < NEIGHBORS_COUNT; l++)
                {
                    if (params->src_state[(i + x_delta[l]) + (j + y_delta[l]) * n] > 0)
                    {
                        m++;
                    }
                }
                params->state[k] = ((m == 3 || (params->src_state[k] == 1 && m == 2)) ? 1 : 0);
            }
            else
            {
                params->state[k] = 0;
            }
        }
    }
    return NULL;
}


void make_step_th(int size, int th_count, int *state)
{
    int n = size + 2;
    int k = sizeof(int) * n * n;
    int step = size / th_count;
    int *state_copy = malloc(k);
    memcpy(state_copy, state, k);
    pthread_t threads[th_count];
    Params *param = malloc(sizeof(Params) * th_count);

    for (k = 0; k < th_count; k++)
    {
        param[k].size = size;
        param[k].state = state;
        param[k].src_state = state_copy;
        param[k].a = k * step;
        param[k].b = (k + 1) * step;
        if (k == th_count - 1)
        {
            param[k].b = size;
        }

        if (pthread_create(&threads[k], NULL, make_step_part, &param[k]))
        {
            fprintf(stderr, "Failed creating thread\n");
        }
    }

    for (k = 0; k < th_count; k++)
    {
        if (pthread_join(threads[k], NULL))
        {
            fprintf(stderr, "Error joining thread\n");
        }
    }

    free(state_copy);
    free(param);
}
