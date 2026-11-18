import re,sys,difflib
def load(p):
    t=open(p,encoding='utf-8',errors='ignore').read().replace('\f','\n')
    t='\n'.join(l for l in t.split('\n') if not re.fullmatch(r'\s*\d{3}\s*',l))
    t=re.sub(r'-\n(?=[a-z])','',t); t=re.sub(r'\s+',' ',t)
    return t
def parts(t):
    a=t.find('Abstract'); l=max(t.rfind(' Limitations Several'),t.rfind(' Limitations We acknowledge')); e=t.find(' Ethical Considerations This study',l); r=t.find(' References Emily Allaway',e)
    ack=t.find(' Acknowledgments ',e)
    ap=t.find('A Data Collection',r)
    return {'body (abstract to conclusion)':t[a:l],'limitations':t[l:e],'ethics':t[e:(ack if 0<ack<r else r)],'appendix':t[ap:]}
def sents(x): return [s.strip() for s in re.split(r'(?<=[.?!;:])\s+',x) if s.strip()]
def norm(s): return re.sub(r'[^a-z0-9 ]','',s.lower()).split()
def share(old,new):
    # order-insensitive: each camera-ready sentence is matched to its closest reviewed sentence; unmatched words count as new or changed
    O=[norm(s) for s in sents(old)]; Oj=[' '.join(o) for o in O]; oset=set(Oj)
    tot=0; chg=0
    for s in sents(new):
        n=norm(s); tot+=len(n)
        j=' '.join(n)
        if j in oset or not n: continue
        c=difflib.get_close_matches(j,Oj,n=1,cutoff=0.3)
        if not c: chg+=len(n); continue
        sm=difflib.SequenceMatcher(None,c[0].split(),n,autojunk=False)
        chg+=len(n)-sum(b.size for b in sm.get_matching_blocks())
    return tot,chg
if __name__=="__main__":
    o=parts(load(sys.argv[1])); n=parts(load(sys.argv[2]))
    T=C=0
    for k in ['body (abstract to conclusion)','limitations']:
        t,c=share(o[k],n[k]); T+=t; C+=c; print(f'{k}: {t} words, new or changed {c} ({100*c/t:.1f}%)')
    print(f'MAIN TEXT (body through Limitations): {T} words, new or changed {C} ({100*C/T:.1f}%)')
    for k in ['ethics','appendix']:
        t,c=share(o[k],n[k]); T+=t; C+=c; print(f'{k}: {t} words, new or changed {c} ({100*c/max(t,1):.1f}%)')
    print(f'WHOLE PAPER excl. references: {T} words, new or changed {C} ({100*C/T:.1f}%)')
    