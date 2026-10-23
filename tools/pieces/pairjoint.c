/* The GC8 analogue: red spells one thing, blue spells another, under ONE ordering.
   A piece can only sit where its name supplies BOTH letters at once, so a candidate
   pair of strings is checked position by position against the (red,blue) pairs each
   piece can actually produce -- which kills nearly everything before any matching runs. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "opts.h"
#define N 14
static int PAIR[26][26];              /* bitmask of pieces that can give (r,b) */
static int PCOST[26][26][NP];         /* cheapest rank for that piece to do it */
static int adj[NP], matchR[NP], seen_[NP], mL[NP];
static int tryk(int u){
  for(int v=0;v<N;v++){
    if(!((adj[u]>>v)&1)||seen_[v]) continue;
    seen_[v]=1;
    if(matchR[v]<0||tryk(matchR[v])){ matchR[v]=u; mL[u]=v; return 1; }
  }
  return 0;
}
static int feasible(void){
  for(int v=0;v<N;v++) matchR[v]=-1;
  for(int u=0;u<NP;u++){
    for(int v=0;v<N;v++) seen_[v]=0;
    if(!tryk(u)) return 0;
  }
  return 1;
}
#define MAXS 8000
static char S[MAXS][16]; static char D[MAXS][80]; static int NS=0;
int main(int argc,char**argv){
  for(int r=0;r<26;r++) for(int b=0;b<26;b++){ PAIR[r][b]=0; for(int u=0;u<NP;u++) PCOST[r][b][u]=99; }
  for(int u=0;u<NP;u++) for(int k=0;k<NOPT[u];k++){
    int r=OL_[u][k]-'A'; char bb=OB_[u][k];
    if(bb=='?'){ for(int b=0;b<26;b++){ PAIR[r][b]|=1<<u; if(OR_[u][k]<PCOST[r][b][u]) PCOST[r][b][u]=OR_[u][k]; } }
    else { int b=bb-'A'; PAIR[r][b]|=1<<u; if(OR_[u][k]<PCOST[r][b][u]) PCOST[r][b][u]=OR_[u][k]; }
  }
  FILE*f=fopen(argv[1],"r"); char buf[256];
  while(fgets(buf,sizeof buf,f)&&NS<MAXS){
    char*t=strchr(buf,'\t'); if(!t) continue; *t=0;
    if(strlen(buf)!=N) continue;
    strcpy(S[NS],buf); t++; t[strcspn(t,"\r\n")]=0; strncpy(D[NS],t,79); NS++;
  }
  fclose(f);
  fprintf(stderr,"strings %d\n",NS);
  long tested=0,pairok=0,hits=0;
  for(int i=0;i<NS;i++) for(int j=0;j<NS;j++){
    if(i==j) continue;
    tested++;
    int ok=1, cost=0;
    for(int p=0;p<N;p++){
      int r=S[i][p]-'A', b=S[j][p]-'A';
      if(!PAIR[r][b]){ ok=0; break; }
    }
    if(!ok) continue;
    pairok++;
    for(int u=0;u<NP;u++){
      int m=0;
      for(int p=0;p<N;p++){ int r=S[i][p]-'A', b=S[j][p]-'A'; if(PAIR[r][b]>>u&1) m|=1<<p; }
      adj[u]=m; if(!m){ ok=0; break; }
    }
    if(!ok) continue;
    if(!feasible()) continue;
    for(int u=0;u<NP;u++){ int p=mL[u]; cost+=PCOST[S[i][p]-'A'][S[j][p]-'A'][u]; }
    hits++;
    printf("cost %3d  RED %-16s BLUE %-16s | %s / %s\n",cost,S[i],S[j],D[i],D[j]);
  }
  fprintf(stderr,"tested %ld  position-pairs ok %ld  matched %ld\n",tested,pairok,hits);
  return 0;
}
