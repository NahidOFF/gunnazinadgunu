/* Both colours at once, under a naming-cost budget.

   A piece takes a position only through one of its candidate names, and that name fixes
   BOTH its letters, so red and blue prune each other. Every name carries a plausibility
   rank; the search spends a bounded total of rank. A low budget means only orderings
   whose naming a normal person would actually write down. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "opts.h"
#define N 14
#define MAXNODE 900000
typedef struct { int ch[26]; unsigned char term; } Node;
static Node nd[MAXNODE]; static int nn=1;
static void addw(const char*w){
  int c=0;
  for(const char*p=w;*p;p++){
    int k=*p-'A';
    if(nd[c].ch[k]==0){ nd[c].ch[k]=nn; nd[nn].term=0; memset(nd[nn].ch,0,sizeof nd[nn].ch); nn++; }
    c=nd[c].ch[k];
  }
  nd[c].term=1;
}
static int MINW=3, MAXWORDS=2;
#define MAXST 128
typedef struct { int n; int node[MAXST]; unsigned char ph[MAXST]; } St;
static void push(St*s,int node,int ph){
  for(int i=0;i<s->n;i++) if(s->node[i]==node&&s->ph[i]==ph) return;
  if(s->n<MAXST){ s->node[s->n]=node; s->ph[s->n]=ph; s->n++; }
}
static int stepq(const St*in, St*out, int c, int i){
  out->n=0; int rem=N-(i+1);
  for(int k=0;k<in->n;k++){
    int nx=nd[in->node[k]].ch[c];
    if(!nx) continue;
    push(out,nx,in->ph[k]);
    if(in->ph[k]+1<MAXWORDS && nd[nx].term && rem>=MINW) push(out,0,in->ph[k]+1);
  }
  return out->n;
}
static int acc(const St*s){
  for(int k=0;k<s->n;k++) if(nd[s->node[k]].term && s->ph[k]>=1) return 1;
  return 0;
}
static int BUDGET=6;
static long nodes=0, hits=0, CAP=4000;
static char R[N+1],B[N+1];
static int chosenP[N], chosenO[N];
static void rec(int i,int used,int cost,St rs,St bs){
  nodes++;
  if(hits>=CAP) return;
  if(i==N){
    if(acc(&rs)&&acc(&bs)){
      R[N]=0;B[N]=0;
      printf("cost %2d  RED %s  BLUE %s  |",cost,R,B);
      for(int p=0;p<N;p++) printf(" %s=%s",PKEY[chosenP[p]],ONM[chosenP[p]][chosenO[p]]);
      printf("\n"); hits++;
    }
    return;
  }
  for(int u=0;u<NP;u++){
    if(used>>u&1) continue;
    for(int k=0;k<NOPT[u];k++){
      int rank=OR_[u][k];
      if(cost+rank>BUDGET) break;          /* options are rank-sorted */
      St nrs; if(!stepq(&rs,&nrs,OL_[u][k]-'A',i)) continue;
      char b=OB_[u][k];
      if(b!='?'){
        St nbs; if(!stepq(&bs,&nbs,b-'A',i)) continue;
        R[i]=OL_[u][k]; B[i]=b; chosenP[i]=u; chosenO[i]=k;
        rec(i+1,used|(1<<u),cost+rank,nrs,nbs);
      } else {
        for(int c=0;c<26;c++){
          St nbs; if(!stepq(&bs,&nbs,c,i)) continue;
          R[i]=OL_[u][k]; B[i]='A'+c; chosenP[i]=u; chosenO[i]=k;
          rec(i+1,used|(1<<u),cost+rank,nrs,nbs);
          if(hits>=CAP) return;
        }
      }
      if(hits>=CAP) return;
    }
  }
}
int main(int argc,char**argv){
  const char*wl=argv[1];
  BUDGET=atoi(argv[2]);
  if(argc>3) MAXWORDS=atoi(argv[3]);
  if(argc>4) MINW=atoi(argv[4]);
  memset(nd[0].ch,0,sizeof nd[0].ch);
  FILE*f=fopen(wl,"r"); char buf[256]; int cnt=0;
  while(fgets(buf,sizeof buf,f)){
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'&&n<62) w[n++]=c; }
    w[n]=0;
    if(n>=MINW&&n<=N-MINW){ addw(w); cnt++; }
  }
  fclose(f);
  fprintf(stderr,"words %d  trie %d  budget %d  maxwords %d  minw %d\n",cnt,nn,BUDGET,MAXWORDS,MINW);
  St s0; s0.n=0; push(&s0,0,0);
  rec(0,0,0,s0,s0);
  fprintf(stderr,"nodes %ld  hits %ld\n",nodes,hits);
  return 0;
}
