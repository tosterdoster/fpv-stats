import os,struct,time,re,sys,threading,json,glob,pymysql

def find_pid():
    for d in glob.glob('/proc/*/comm'):
        try:
            name=open(d).read().strip()
            if 'FPV' in name or 'fpv' in name or 'Kamikaze' in name:
                return int(d.split('/')[2])
        except:pass
    for d in glob.glob('/proc/*/cmdline'):
        try:
            cmd=open(d,'rb').read().replace(b'\x00',b' ').decode()
            if 'FPV' in cmd or 'fpv' in cmd or 'Kamikaze' in cmd:
                return int(d.split('/')[2])
        except:pass
    return None

PID=int(sys.argv[1]) if len(sys.argv)>1 else find_pid()
if not PID:print('Game process not found!');sys.exit(1)
INTERVAL=float(sys.argv[2]) if len(sys.argv)>2 else 3.0
OFF_NAME=0x148
OFF_UID=0x158
CACHE_FILE='/tmp/fpv_uid_cache.json'
DB_HOST='127.0.0.1'
DB_USER='fpv'
DB_PASS='fpv_pass_2026'
DB_NAME='fpv_stats'

fd=os.open(f'/proc/{PID}/mem',os.O_RDONLY)
lock=threading.Lock()
try:uid_cache=json.load(open(CACHE_FILE))
except:uid_cache={}

def detect_game_range():
    totals={}
    for line in open(f'/proc/{PID}/maps'):
        p=line.split()
        if len(p)<2:continue
        rs,re_=[int(x,16) for x in p[0].split('-')]
        if 'r' not in p[1] or 'x' in p[1]:continue
        prefix=rs>>40
        if prefix==0 or prefix>=0x7f:continue
        totals[prefix]=totals.get(prefix,0)+(re_-rs)
    best_prefix=None;best_total=0
    for prefix,total in totals.items():
        if total>best_total:best_total=total;best_prefix=prefix
    if best_prefix:
        lo=best_prefix<<40
        hi=(best_prefix+1)<<40
        pat=struct.pack('B',best_prefix)+b'\x00\x00'
        print(f'[*] Range: {lo:#018x}-{hi:#018x} pat={pat.hex()}')
        return lo,hi,pat
    return 0x6ffb00000000,0x6ffd00000000,b'\x6f\x00\x00'

GAME_LO,GAME_HI,PTR_PAT=detect_game_range()

def save_cache():
    try:json.dump(uid_cache,open(CACHE_FILE,'w'))
    except:pass

def rm(a,n):
    try:
        os.lseek(fd,a,os.SEEK_SET)
        d=os.read(fd,n)
        return d+b'\x00'*(n-len(d)) if len(d)<n else d
    except:return b'\x00'*n

def fstr(a):
    ptr=struct.unpack_from('<Q',rm(a,8))[0]
    cnt=struct.unpack_from('<i',rm(a+8,4))[0]
    if not(GAME_LO<=ptr<GAME_HI) or not(1<=cnt<=128):return ''
    try:return rm(ptr,cnt*2).decode('utf-16-le').rstrip('\x00')
    except:return ''

NAME_RE=re.compile(r'^[a-zA-Z0-9\u0400-\u04ff][a-zA-Z0-9\u0400-\u04ff _\-\[\]#!]{0,30}$')

def is_valid_name(n):
    return bool(NAME_RE.match(n))

def read_obj(obj):
    raw=rm(obj,16)
    if len(raw)<16:return None
    k,d,a,s=struct.unpack_from('<iiii',raw)
    if not(-9999<=k<=9999 and -9999<=d<=9999 and -9999<=a<=9999 and -999999<=s<=999999):return None
    if s!=0 and s%50!=0:return None
    name=fstr(obj+OFF_NAME)
    if not name or not is_valid_name(name):return None
    uid=fstr(obj+OFF_UID)
    has_uid=bool(uid and uid.startswith('0002') and len(uid)>=30)
    in_cache=name in uid_cache
    if not has_uid and not in_cache:return None
    if has_uid and uid_cache.get(name)!=uid:
        uid_cache[name]=uid;save_cache()
    return name,k,d,a,s,uid_cache.get(name,'—'),has_uid

def get_regions():
    regs=[]
    for line in open(f'/proc/{PID}/maps'):
        p=line.split()
        if len(p)<2:continue
        rs,re_=[int(x,16) for x in p[0].split('-')]
        if not(GAME_LO<=rs<GAME_HI):continue
        if 'r' not in p[1] or 'x' in p[1]:continue
        sz=re_-rs
        if sz<0x1000 or sz>0x10000000:continue
        regs.append((rs,re_))
    return regs

def scan_all():
    regs=get_regions()
    candidates={}
    for rs,re_ in regs:
        addr=rs
        while addr<re_:
            sz=min(0x400000,re_-addr)
            try:
                os.lseek(fd,addr,os.SEEK_SET)
                data=os.read(fd,sz)
            except:addr+=sz;continue
            idx=0
            while True:
                i=data.find(PTR_PAT,idx)
                if i==-1 or i+20>len(data):break
                nc=struct.unpack_from('<i',data,i+3)[0]
                if 2<=nc<=25:
                    if i+19<len(data) and data[i+16:i+19]==PTR_PAT:
                        uc=struct.unpack_from('<i',data,i+19)[0]
                        if 30<=uc<=36:
                            obj=addr+i-0x14d
                            r=read_obj(obj)
                            if r:
                                name=r[0];hu=r[6]
                                act=abs(r[1])+abs(r[2])+abs(r[3])+abs(r[4])
                                key=(hu,act)
                                if name not in candidates or key>candidates[name][0]:
                                    candidates[name]=(key,obj)
                idx=i+1
            addr+=sz
    return {n:obj for n,(key,obj) in candidates.items()}

db_sent={}

def db_connect():
    return pymysql.connect(host=DB_HOST,user=DB_USER,password=DB_PASS,database=DB_NAME,autocommit=True)

def db_update(name,uid,k,d,a,s):
    prev=db_sent.get(name,(0,0,0,0))
    dk=k-prev[0];dd=d-prev[1];da=a-prev[2];ds=s-prev[3]
    if dk==0 and dd==0 and da==0 and ds==0:return
    if dk<0 or dd<0 or da<0:
        dk,dd,da,ds=k,d,a,s
    db_sent[name]=(k,d,a,s)
    if dk==0 and dd==0 and da==0 and ds==0:return
    try:
        conn=db_connect();cur=conn.cursor()
        cur.execute("""
            INSERT INTO players (uid,nickname,kills,deaths,assists,score)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                nickname=%s,kills=kills+%s,deaths=deaths+%s,
                assists=assists+%s,score=score+%s,last_seen=NOW()
        """,(uid,name,dk,dd,da,ds,name,dk,dd,da,ds))
        conn.close()
    except Exception as e:print(f'  [DB ERR] {e}')

def db_reset_match():
    db_sent.clear()

players={}
last_good={}
zero_since={}

def do_scan(clear=False):
    global players
    if clear:last_good.clear();zero_since.clear();db_reset_match()
    result=scan_all()
    with lock:players=result
    for name,obj in result.items():
        r=read_obj(obj)
        if r:
            if r[1]!=0 or r[2]!=0 or r[3]!=0 or r[4]!=0:
                last_good[name]=(r[1],r[2],r[3],r[4],r[5],time.time())
            print(f'  [+] {name} ({r[1]}/{r[2]}/{r[3]}/{r[4]})')

def bg_scan():
    while True:
        time.sleep(15)
        with lock:cur=dict(players)
        alive=any(read_obj(obj) for obj in cur.values())
        if not alive and cur:
            print('[*] Rescan...')
            do_scan(clear=True)
        else:
            new=scan_all()
            with lock:
                for name,obj in new.items():
                    if name not in players:
                        players[name]=obj
                        r=read_obj(obj)
                        if r:
                            if r[1]!=0 or r[2]!=0 or r[3]!=0 or r[4]!=0:
                                last_good[name]=(r[1],r[2],r[3],r[4],r[5],time.time())
                            print(f'  [+] {name} (new)')

print('FPV Kamikaze Drone — Live Stats')
print(f'PID: {PID}  |  Interval: {INTERVAL}s')
if uid_cache:print(f'[*] Cached: {list(uid_cache.keys())}')
print('[*] Scanning...')
t0=time.time()
do_scan()
print(f'[*] Done in {time.time()-t0:.1f}s')
t=threading.Thread(target=bg_scan,daemon=True);t.start()

while True:
    if not os.path.exists(f'/proc/{PID}'):
        print('[!] Game process died, exiting...')
        save_cache()
        sys.exit(1)
    with lock:cur=dict(players)
    rows=[];now=time.time()
    for name,obj in cur.items():
        r=read_obj(obj)
        if r:
            k,d,a,s=r[1],r[2],r[3],r[4]
            is_zero=(k==0 and d==0 and a==0 and s==0)
            if is_zero:
                if name not in zero_since:zero_since[name]=now
                if now-zero_since[name]>30:continue
                if name in last_good:
                    ok,od,oa,os_,ouid,ots=last_good[name]
                    if now-ots<10:
                        rows.append((name,ok,od,oa,os_,ouid));continue
                rows.append((name,0,0,0,0,r[5]))
            else:
                zero_since.pop(name,None)
                last_good[name]=(k,d,a,s,r[5],now)
                rows.append((name,k,d,a,s,r[5]))
                uid=r[5] if r[5]!='—' else uid_cache.get(name,'')
                if uid and uid.startswith('0002'):db_update(name,uid,k,d,a,s)
        elif name in last_good:
            k,d,a,s,uid,ts=last_good[name]
            if now-ts<30:rows.append((name,k,d,a,s,uid))
    print(f'\n{"─"*68}')
    print(f'  {time.strftime("%H:%M:%S")}  Players: {len(rows)}')
    print(f'{"─"*68}')
    if rows:
        print(f'  {"Name":<20} {"K":>4} {"D":>4} {"A":>4} {"Score":>6}  UserId')
        print(f'  {"─"*20} {"─"*4} {"─"*4} {"─"*4} {"─"*6}  {"─"*32}')
        for name,k,d,a,s,uid in sorted(rows,key=lambda x:-x[4]):
            print(f'  {name:<20} {k:>4} {d:>4} {a:>4} {s:>6}  {uid}')
    else:print('  (no active players)')
    try:time.sleep(INTERVAL)
    except KeyboardInterrupt:save_cache();print('\nStopped.');break
