#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAXN 100000

typedef struct { int idx, val; } Item;
typedef struct { Item *a; int cap, head, size; } Deque;

void dq_init(Deque *d, int cap) {
    d->a = malloc(cap * sizeof(Item)); d->cap = cap; d->head = 0; d->size = 0;
}
int  dq_empty(Deque *d)        { return d->size == 0; }
Item dq_front(Deque *d)        { return d->a[d->head]; }
Item dq_back(Deque *d)         { return d->a[(d->head + d->size - 1) % d->cap]; }
void dq_push_back(Deque *d, Item x) { d->a[(d->head + d->size) % d->cap] = x; d->size++; }
void dq_pop_back(Deque *d)     { d->size--; }
void dq_pop_front(Deque *d)    { d->head = (d->head + 1) % d->cap; d->size--; }

int main(int argc, char **argv) {
    static int r[MAXN];
    int n = 0, v, K, high, low;
    FILE *f = (argc > 1) ? fopen(argv[1], "r") : NULL;

    if (f) {                       /* replay file: integers separated by spaces, commas or newlines */
        int c;
        while (n < MAXN && fscanf(f, "%d", &v) == 1) {
            r[n++] = v;
            c = fgetc(f);          /* eat the separator after a number */
            if (c != ',' && c != ' ' && c != '\n' && c != '\r' && c != '\t' && c != EOF)
                ungetc(c, f);
        }
        fclose(f);
    } else {                       /* manual input */
        printf("How many readings (max %d)? ", MAXN);
        scanf("%d", &n); if (n > MAXN) n = MAXN;
        printf("Enter %d readings: ", n);
        for (int i = 0; i < n; i++) scanf("%d", &r[i]);
    }
    printf("Window size K (1..%d): ", n);   scanf("%d", &K);
    printf("High limit: ");                 scanf("%d", &high);
    printf("Low limit: ");                  scanf("%d", &low);
    if (K < 1 || K > n) { puts("Invalid K"); return 1; }

    int W = n - K + 1;
    int *MX = malloc(W * sizeof(int)), *MN = malloc(W * sizeof(int));
    Deque mx, mn; dq_init(&mx, K + 1); dq_init(&mn, K + 1);
    long ops = 0; int w = 0;

    clock_t t0 = clock();
    for (int i = 0; i < n; i++) {
        while (!dq_empty(&mx) && dq_back(&mx).val <= r[i]) { dq_pop_back(&mx); ops++; }
        dq_push_back(&mx, (Item){i, r[i]}); ops++;
        while (!dq_empty(&mn) && dq_back(&mn).val >= r[i]) { dq_pop_back(&mn); ops++; }
        dq_push_back(&mn, (Item){i, r[i]}); ops++;

        if (dq_front(&mx).idx <= i - K) { dq_pop_front(&mx); ops++; }
        if (dq_front(&mn).idx <= i - K) { dq_pop_front(&mn); ops++; }

        if (i >= K - 1) {          /* only complete windows produce results */
            MX[w] = dq_front(&mx).val;
            MN[w] = dq_front(&mn).val;
            w++;
        }
    }
    double tDeque = (double)(clock() - t0) / CLOCKS_PER_SEC;

    /* Baseline: rescan every window */
    int *BX = malloc(W * sizeof(int)), *BN = malloc(W * sizeof(int));
    long cmps = 0;
    t0 = clock();
    for (int s = 0; s < W; s++) {
        int hi = r[s], lo = r[s];
        for (int j = s + 1; j < s + K; j++) {
            if (r[j] > hi) hi = r[j];
            if (r[j] < lo) lo = r[j];
            cmps += 2;
        }
        BX[s] = hi; BN[s] = lo;
    }
    double tBase = (double)(clock() - t0) / CLOCKS_PER_SEC;

    int mismatch = 0, alerts = 0;
    for (int s = 0; s < W; s++) {
        if (MX[s] != BX[s] || MN[s] != BN[s]) mismatch++;
        if (MX[s] > high || MN[s] < low) alerts++;
    }

    /* Table: first 10 and last 5 windows (or all if small) */
    printf("\n%-8s %-14s %-6s %-6s %s\n", "Window", "Range", "Max", "Min", "Status");
    for (int s = 0; s < W; s++) {
        if (W > 20 && s == 10) { printf("  ...\n"); s = W - 6; continue; }
        int bad = (MX[s] > high || MN[s] < low);
        printf("%-8d [%d..%d]%*s %-6d %-6d %s\n", s + 1, s, s + K - 1, 4, "",
               MX[s], MN[s], bad ? "ALERT" : "OK");
    }

    printf("\nLatest window (readings %d..%d)", W - 1, n - 1);
    if (K <= 20) { printf(": "); for (int j = W - 1; j < n; j++) printf("%d ", r[j]); }
    printf("\n  max=%d  min=%d  %s\n", MX[W-1], MN[W-1],
           (MX[W-1] > high || MN[W-1] < low) ? "ALERT" : "OK");

    printf("\nWindows: %d | Alerts: %d | Mismatches vs baseline: %d\n", W, alerts, mismatch);
    printf("Deque   : %ld ops,  %.4f s\n", ops, tDeque);
    printf("Baseline: %ld cmps, %.4f s\n", cmps, tBase);
    return 0;
}