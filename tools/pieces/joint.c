/* Build both colours at once, one position at a time.
   RED must come out as the 5+2+7 phrase the red desk note's first line describes.
   BLUE must come out as some run of 2..4 dictionary words.
   A piece may take a position only via one of its candidate names, and that same name
   fixes the blue letter there -- so the two strings are yoked and prune each other. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NP 14
#define N  14
#define MAXNODE 400000
typedef struct { int ch[26]; unsigned char term; } Node;
static Node nd[MAXNODE]; static int nn=1;
static int add(const char*w){
  int c=0;
  for(const char*p=w;*p;p++){
    int k=*p-'A';
    if(nd[c].ch[k]==0){ nd[c].ch[k]=nn; nd[nn].term=0; memset(nd[nn].ch,0,sizeof nd[nn].ch); nn++; }
    c=nd[c].ch[k];
  }
  nd[c].term=1; return c;
}
/* piece candidate (red,blue) letter pairs */
static const char *RP[NP]={"ADEEP","AHHL","OITTH","ESLNB","FLMIT","","CRUSDO","TBEPNWS","ADIG","HOETD","HDEEMC","ERGY","GCNED","IEGA"};
static const char *BP[NP]={"EEKRR","ELSH","FOTAN","FSSBW","OFOIA","","ACRUOK","MFPFTWW","RGGA","AWCDC","DCFHSI","OGGJ","ELREL",""};
static int np_[NP];
static char pr[NP][40], pb[NP][40];
/* blue parse state */
#define MAXST 96
typedef struct { int n; short node[MAXST]; unsigned char wd[MAXST]; } St;
static void push(St*s,int node,int w){
  for(int i=0;i<s->n;i++) if(s->node[i]==node&&s->wd[i]==w) return;
  if(s->n<MAXST){ s->node[s->n]=node; s->wd[s->n]=w; s->n++; }
}
#define MINW 3
#define MAXWD 4
static int bstep(const St*in, St*out, int c, int i){
  out->n=0;
  int rem=N-(i+1);
  for(int k=0;k<in->n;k++){
    int nx=nd[in->node[k]].ch[c];
    if(!nx) continue;
    push(out,nx,in->wd[k]);
    if(nd[nx].term && in->wd[k]+1<MAXWD && rem>=MINW) push(out,0,in->wd[k]+1);
  }
  return out->n;
}
static int baccept(const St*s){
  for(int k=0;k<s->n;k++) if(nd[s->node[k]].term && s->wd[k]>=1) return 1;
  return 0;
}
static long hits=0, nodes=0;
static char R[N+1], B[N+1];
static const char *SHORT2[]={"OF","IN","TO","ON","AT","IS","IT","BY","AS","MY","NO","SO","UP","US","WE","AN","OR","DO","GO","HE","ME","BE","IF",0};
static int t5,t7;               /* roots for the 5- and 7-letter tries */
static int rnode;               /* current red trie node */
static void rec(int i,int used,int rn,int seg,St bs){
  nodes++;
  if(hits>20000) return;
  if(i==N){ if(nd[rn].term && baccept(&bs)){ R[N]=0;B[N]=0; printf("%.5s %.2s %.7s | %s\n",R,R+5,R+7,B); hits++; } return; }
  for(int u=0;u<NP;u++){
    if(used>>u&1) continue;
    for(int k=0;k<np_[u];k++){
      char rc=pr[u][k], bc=pb[u][k];
      int nrn;
      if(i==5||i==7||i==0){ /* segment starts handled by caller state */ }
      nrn=nd[rn].ch[rc-'A'];
      if(!nrn) continue;
      /* segment boundary checks */
      int nseg=seg, nrn2=nrn;
      if(i==4){ if(!nd[nrn].term) continue; nrn2=0; nseg=1; }
      else if(i==6){ if(!nd[nrn].term) continue; nrn2=0; nseg=2; }
      St nb; if(!bstep(&bs,&nb,bc-'A',i)) continue;
      R[i]=rc; B[i]=bc;
      rec(i+1,used|(1<<u),nrn2,nseg,nb);
      if(hits>20000) return;
    }
  }
}
int main(int argc,char**argv){
  memset(nd[0].ch,0,sizeof nd[0].ch);
  /* red trie: 5-letter words, then 2-letter, then 7-letter, all from the same root:
     segment boundaries force terminality and reset to root, so mixing lengths is safe
     only if we keep separate roots -- simplest is to load all three sets into root and
     rely on the length checks at i==4 and i==6. */
  FILE*f=fopen(argv[1],"r"); char buf[256];
  int n5=0,n7=0,nb=0;
  while(fgets(buf,sizeof buf,f)){
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'&&n<62) w[n++]=c; }
    w[n]=0;
    if(n==5){ add(w); n5++; }
    else if(n==7){ add(w); n7++; }
  }
  for(int s=0;SHORT2[s];s++) add(SHORT2[s]);
  fclose(f);
  /* blue trie shares the same node pool but needs all lengths: load 3..11 */
  f=fopen(argv[1],"r"); int bstart=nn;
  while(fgets(buf,sizeof buf,f)){
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'&&n<62) w[n++]=c; }
    w[n]=0; if(n>=3&&n<=11) add(w);
  }
  fclose(f);
  fprintf(stderr,"trie nodes %d (5-letter %d, 7-letter %d)\n",nn,n5,n7);
  for(int u=0;u<NP;u++){
    if(RP[u][0]==0){ /* wildcard piece: red==blue, any letter */
      np_[u]=26; for(int c=0;c<26;c++){ pr[u][c]='A'+c; pb[u][c]='A'+c; }
    } else if(BP[u][0]==0){ /* blue unknown: any blue letter */
      int m=0; for(const char*p=RP[u];*p;p++) for(int c=0;c<26;c++){ if(m<40){ pr[u][m]=*p; pb[u][m]='A'+c; m++; } }
      np_[u]=m;
    } else {
      int m=strlen(RP[u]); np_[u]=m;
      for(int k=0;k<m;k++){ pr[u][k]=RP[u][k]; pb[u][k]=BP[u][k]; }
    }
  }
  St s0; s0.n=0; push(&s0,0,0);
  rec(0,0,0,0,s0);
  fprintf(stderr,"nodes %ld  hits %ld\n",nodes,hits);
  return 0;
}
