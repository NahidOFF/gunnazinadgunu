/* The red desk note's first line is a three-word phrase of lengths 5, 2, 7 -- exactly
   fourteen letters, which is exactly what fourteen pieces give.  So test that shape:
   which 5+2+7 phrases can the pieces spell, and what blue string does each imply? */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NP 14
static const char *RED[NP] = {
  "ADEP","AHL","OITH","ESLNB","FLMIT","ABCDEFGHIJKLMNOPQRSTUVWXYZ","CRUSDO",
  "TBEPNWS","ADIG","HOETD","HDEMC","ERGY","GCNED","IEGA" };
/* blue letter for each red letter, same index in these strings */
static const char *BLU[NP] = {
  "EEKR","ELS","FNAT","FSSBW","OFOIA","ABCDEFGHIJKLMNOPQRSTUVWXYZ","ACRUOK",
  "MFPFTWW","RGGA","AWCDC","DCFSHI","OGGJ","ELREL","????" };
/* note: RED[i][k] pairs with BLU[i][k]; wildcard pieces use the identity/any mapping */
static const char *SHORT[] = {"OF","IN","TO","ON","AT","IS","IT","BY","AS","MY","NO",
  "SO","UP","US","WE","AN","OR","DO","GO","HE","ME","BE","IF","AM","US",0};
static int pmask[NP];
static int adj[NP], matchR[NP], seen[NP], mL[NP];
static char red[16];
static int tryk(int u){
  for(int v=0;v<14;v++){
    if(!((adj[u]>>v)&1)||seen[v]) continue;
    seen[v]=1;
    if(matchR[v]<0||tryk(matchR[v])){ matchR[v]=u; mL[u]=v; return 1; }
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
  int allow=0;
  for(int i=0;i<NP;i++){ pmask[i]=0; for(const char*p=RED[i];*p;p++) pmask[i]|=1<<(*p-'A'); allow|=pmask[i]; }
  FILE*f=fopen(argv[1],"r"); char buf[256];
  while(fgets(buf,sizeof buf,f)){
    int n=0; char w[64];
    for(char*p=buf;*p;p++){ char c=*p; if(c>='a'&&c<='z')c-=32; if(c>='A'&&c<='Z'&&n<62) w[n++]=c; }
    w[n]=0; if(n!=5&&n!=7) continue;
    int ok=1; for(int i=0;i<n;i++) if(!((allow>>(w[i]-'A'))&1)){ ok=0; break; }
    if(ok&&nw[n]<MAXW) wl[n][nw[n]++]=strdup(w);
  }
  fclose(f);
  fprintf(stderr,"5-letter %d  7-letter %d\n",nw[5],nw[7]);
  long hits=0;
  for(int a=0;a<nw[5];a++) for(int s=0;SHORT[s];s++) for(int b=0;b<nw[7];b++){
    memcpy(red,wl[5][a],5); memcpy(red+5,SHORT[s],2); memcpy(red+7,wl[7][b],7); red[14]=0;
    for(int u=0;u<NP;u++){
      int m=0;
      for(int v=0;v<14;v++) if((pmask[u]>>(red[v]-'A'))&1) m|=1<<v;
      adj[u]=m; if(!m) goto next;
    }
    if(!feasible()) goto next;
    hits++;
    printf("%s %s %s\n", wl[5][a], SHORT[s], wl[7][b]);
    next: ;
  }
  fprintf(stderr,"HITS %ld\n",hits);
  return 0;
}
