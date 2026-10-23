/* Which two-word 14-letter phrases can the fourteen pieces actually spell?
   Each piece contributes one letter, drawn from the letters its candidate names put
   at that piece's red index.  A phrase is reachable iff there is a perfect matching
   of pieces onto the phrase's letter positions. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NP 14
static const char *SETS[NP] = {
  "ADEHP",        /* calendar   */
  "AHILNO",       /* figure     */
  "BDHIST",       /* sil+plant  */
  "BEILST",       /* bow        */
  "FLMNT",        /* oman       */
  "BEILORU",      /* two thin   */
  "CDELNOSUW",    /* rectangle  */
  "BCDEPST",      /* frames     */
  "AISTU",        /* us+barn    */
  "CDHIO",        /* chart      */
  "DEHMW",        /* snow       */
  "EGTY",         /* joy        */
  "ACEGHN",       /* eagle      */
  "ACEGIN"        /* piece 15   */
};
static int pmask[NP];
static int adj[NP];             /* bitmask over 14 positions */
static int matchR[NP], seen[NP];
static char red[16];
static int tryk(int u){
  for(int v=0;v<14;v++){
    if(!((adj[u]>>v)&1) || seen[v]) continue;
    seen[v]=1;
    if(matchR[v]<0 || tryk(matchR[v])){ matchR[v]=u; return 1; }
  }
  return 0;
}
static int feasible(void){
  for(int v=0;v<14;v++) matchR[v]=-1;
  for(int u=0;u<NP;u++){
    for(int v=0;v<14;v++) seen[v]=0;
    if(!tryk(u)) return 0;
  }
  return 1;
}
#define MAXW 20000
static char *wl[16][MAXW]; static int nw[16];
int main(int argc,char**argv){
  for(int i=0;i<NP;i++){ pmask[i]=0; for(const char*p=SETS[i];*p;p++) pmask[i]|=1<<(*p-'A'); }
  int allow=0; for(int i=0;i<NP;i++) allow|=pmask[i];
  FILE*f=fopen(argv[1],"r"); char buf[256];
  while(fgets(buf,sizeof buf,f)){
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'){ if(n<62) w[n++]=c; } }
    w[n]=0;
    if(n<3||n>11) continue;
    int ok=1; for(int i=0;i<n;i++) if(!((allow>>(w[i]-'A'))&1)) { ok=0; break; }
    if(!ok) continue;
    if(nw[n]<MAXW) wl[n][nw[n]++]=strdup(w);
  }
  fclose(f);
  long tested=0, hits=0;
  for(int l1=3;l1<=11;l1++){
    int l2=14-l1; if(l2<3||l2>11) continue;
    for(int a=0;a<nw[l1];a++) for(int b=0;b<nw[l2];b++){
      memcpy(red,wl[l1][a],l1); memcpy(red+l1,wl[l2][b],l2); red[14]=0;
      tested++;
      for(int u=0;u<NP;u++){
        int m=0;
        for(int v=0;v<14;v++) if((pmask[u]>>(red[v]-'A'))&1) m|=1<<v;
        adj[u]=m;
        if(!m){ adj[0]=-1; goto next; }
      }
      if(feasible()){ hits++; printf("%s %s\n", wl[l1][a], wl[l2][b]); }
      next: ;
    }
    fprintf(stderr,"len %d+%d done: tested %ld hits %ld\n",l1,l2,tested,hits);
  }
  fprintf(stderr,"TOTAL tested %ld hits %ld\n",tested,hits);
  return 0;
}
