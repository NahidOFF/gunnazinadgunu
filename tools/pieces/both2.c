/* Both colours at once, but each colour gets its own vocabulary and word-count rule.
   That lets me ask e.g. "red reads as two dictionary words while blue is a single
   14-letter place name", which is the shape the author's previous puzzle used. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "opts.h"
#define N 14
#define MAXNODE 2000000
typedef struct { int ch[26]; unsigned char term; } Node;
static Node nd[MAXNODE]; static int nn=1;
static int newnode(void){ memset(nd[nn].ch,0,sizeof nd[nn].ch); nd[nn].term=0; return nn++; }
static void addw(int root,const char*w){
  int c=root;
  for(const char*p=w;*p;p++){ int k=*p-'A'; if(!nd[c].ch[k]) nd[c].ch[k]=newnode(); c=nd[c].ch[k]; }
  nd[c].term=1;
}
typedef struct { int root, minw, maxwords; } Lang;
static Lang LR, LB;
#define MAXST 160
typedef struct { int n; int node[MAXST]; unsigned char ph[MAXST]; } St;
static void push(St*s,int node,int ph){
  for(int i=0;i<s->n;i++) if(s->node[i]==node&&s->ph[i]==ph) return;
  if(s->n<MAXST){ s->node[s->n]=node; s->ph[s->n]=ph; s->n++; }
}
static int stepq(const Lang*L,const St*in, St*out, int c, int i){
  out->n=0; int rem=N-(i+1);
  for(int k=0;k<in->n;k++){
    int nx=nd[in->node[k]].ch[c];
    if(!nx) continue;
    push(out,nx,in->ph[k]);
    if(in->ph[k]+1<L->maxwords && nd[nx].term && rem>=L->minw) push(out,L->root,in->ph[k]+1);
  }
  return out->n;
}
static int acc(const Lang*L,const St*s){
  for(int k=0;k<s->n;k++) if(nd[s->node[k]].term && s->ph[k]+1>=1) return 1;
  return 0;
}
static int BUDGET=8; static long nodes=0,hits=0,CAP=3000;
static char R[N+1],B[N+1]; static int cp[N],co[N];
static void rec(int i,int used,int cost,St rs,St bs){
  nodes++; if(hits>=CAP) return;
  if(i==N){
    if(acc(&LR,&rs)&&acc(&LB,&bs)){
      R[N]=0;B[N]=0;
      printf("cost %2d  RED %s  BLUE %s |",cost,R,B);
      for(int p=0;p<N;p++) printf(" %s=%s",PKEY[cp[p]],ONM[cp[p]][co[p]]);
      printf("\n"); hits++;
    }
    return;
  }
  for(int u=0;u<NP;u++){
    if(used>>u&1) continue;
    for(int k=0;k<NOPT[u];k++){
      int rank=OR_[u][k];
      if(cost+rank>BUDGET) break;
      St nrs; if(!stepq(&LR,&rs,&nrs,OL_[u][k]-'A',i)) continue;
      char b=OB_[u][k];
      if(b!='?'){
        St nbs; if(!stepq(&LB,&bs,&nbs,b-'A',i)) continue;
        R[i]=OL_[u][k]; B[i]=b; cp[i]=u; co[i]=k;
        rec(i+1,used|(1<<u),cost+rank,nrs,nbs);
      } else {
        for(int c=0;c<26;c++){
          St nbs; if(!stepq(&LB,&bs,&nbs,c,i)) continue;
          R[i]=OL_[u][k]; B[i]='A'+c; cp[i]=u; co[i]=k;
          rec(i+1,used|(1<<u),cost+rank,nrs,nbs);
          if(hits>=CAP) return;
        }
      }
      if(hits>=CAP) return;
    }
  }
}
static int loadlang(const char*path,int minw,int maxwords,Lang*L){
  L->root=newnode(); L->minw=minw; L->maxwords=maxwords;
  FILE*f=fopen(path,"r"); if(!f){perror(path);exit(1);}
  char buf[512]; int cnt=0;
  while(fgets(buf,sizeof buf,f)){
    char*t=strchr(buf,'\t'); if(t) *t=0;
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'&&n<62) w[n++]=c; }
    w[n]=0;
    if(n>=minw&&n<=N){ addw(L->root,w); cnt++; }
  }
  fclose(f); return cnt;
}
int main(int argc,char**argv){
  memset(nd[0].ch,0,sizeof nd[0].ch);
  const char*rw=argv[1]; int rmin=atoi(argv[2]), rmax=atoi(argv[3]);
  const char*bw=argv[4]; int bmin=atoi(argv[5]), bmax=atoi(argv[6]);
  BUDGET=atoi(argv[7]);
  int a=loadlang(rw,rmin,rmax,&LR), b=loadlang(bw,bmin,bmax,&LB);
  fprintf(stderr,"red vocab %d (min %d, <=%d words)   blue vocab %d (min %d, <=%d words)  budget %d\n",
          a,rmin,rmax,b,bmin,bmax,BUDGET);
  St r0; r0.n=0; push(&r0,LR.root,0);
  St b0; b0.n=0; push(&b0,LB.root,0);
  rec(0,0,0,r0,b0);
  fprintf(stderr,"nodes %ld  hits %ld\n",nodes,hits);
  return 0;
}
