import os,sqlite3,hmac,hashlib,json,urllib.parse,requests
from pathlib import Path
from typing import Optional
from fastapi import FastAPI,Header,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
BASE=Path(__file__).parent;DB=BASE/'online_easy_work.db';TOKEN=os.getenv('TELEGRAM_TOKEN','');BOT_USERNAME=os.getenv('BOT_USERNAME','Online_easy_work_bot');CHANNEL=os.getenv('CHANNEL_USERNAME','@Online_essywork');JOIN_REWARD=.60;VIDEO_REWARD=float(os.getenv('VIDEO_REWARD_ETB','0'))
app=FastAPI(title='Online Easy Work');app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():c=db();c.executescript('CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,first_name TEXT,username TEXT,balance REAL DEFAULT 0,invite_count INTEGER DEFAULT 0,joined_channel INTEGER DEFAULT 0,join_reward_claimed INTEGER DEFAULT 0,videos_completed INTEGER DEFAULT 0);CREATE TABLE IF NOT EXISTS video_claims(user_id INTEGER,video_id INTEGER,PRIMARY KEY(user_id,video_id));CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,country TEXT,payment_method TEXT,full_name TEXT,wallet_phone TEXT,amount REAL,status TEXT DEFAULT "pending");');c.commit();c.close()
@app.on_event('startup')
def startup():init()
def tgdata(s):
 if not s or not TOKEN:return None
 v=dict(urllib.parse.parse_qsl(s,keep_blank_values=True));hh=v.pop('hash',None)
 if not hh:return None
 check='\n'.join(f'{k}={v[k]}' for k in sorted(v));secret=hmac.new(b'WebAppData',TOKEN.encode(),hashlib.sha256).digest();calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
 if not hmac.compare_digest(calc,hh):return None
 return json.loads(v.get('user','{}'))
def user(s):
 u=tgdata(s) or {'id':7980352863,'first_name':'Zayya','username':'zayya'};c=db();r=c.execute('SELECT * FROM users WHERE user_id=?',(u['id'],)).fetchone()
 if not r:c.execute('INSERT INTO users(user_id,first_name,username) VALUES(?,?,?)',(u['id'],u.get('first_name','User'),u.get('username')));c.commit()
 return c.execute('SELECT * FROM users WHERE user_id=?',(u['id'],)).fetchone()
@app.get('/')
def root():return FileResponse(BASE/'static/index.html')
@app.get('/api/me')
def me(x_telegram_init_data:Optional[str]=Header(None)):d=dict(user(x_telegram_init_data));d['bot_username']=BOT_USERNAME;return d
@app.get('/api/videos')
def videos(x_telegram_init_data:Optional[str]=Header(None)):
 r=user(x_telegram_init_data);c=db();done={x['video_id'] for x in c.execute('SELECT video_id FROM video_claims WHERE user_id=?',(r['user_id'],))};c.close();return [{'id':i,'title':f'Video {i}','reward':VIDEO_REWARD,'completed':i in done} for i in range(1,21)]
@app.post('/api/tasks/channel/verify')
def verify(x_telegram_init_data:Optional[str]=Header(None)):
 r=user(x_telegram_init_data)
 if not TOKEN:raise HTTPException(400,'Set TELEGRAM_TOKEN first.')
 z=requests.get(f'https://api.telegram.org/bot{TOKEN}/getChatMember',params={'chat_id':CHANNEL,'user_id':r['user_id']},timeout=10).json()
 if not z.get('ok'):raise HTTPException(400,'Channel verification failed. Check channel username and bot admin access.')
 if z['result']['status'] not in {'member','administrator','creator'}:raise HTTPException(400,'Join the channel first.')
 c=db()
 if not r['join_reward_claimed']:c.execute('UPDATE users SET joined_channel=1,join_reward_claimed=1,balance=balance+? WHERE user_id=?',(JOIN_REWARD,r['user_id']));msg='+0.60 ETB added.'
 else:c.execute('UPDATE users SET joined_channel=1 WHERE user_id=?',(r['user_id'],));msg='Channel already verified.'
 c.commit();c.close();return {'message':msg}
@app.post('/api/videos/{vid}/claim')
def claim(vid:int,x_telegram_init_data:Optional[str]=Header(None)):
 r=user(x_telegram_init_data)
 if not 1<=vid<=20:raise HTTPException(404,'Video not found.')
 c=db()
 if c.execute('SELECT 1 FROM video_claims WHERE user_id=? AND video_id=?',(r['user_id'],vid)).fetchone():raise HTTPException(400,'Already completed.')
 c.execute('INSERT INTO video_claims VALUES(?,?)',(r['user_id'],vid));c.execute('UPDATE users SET videos_completed=videos_completed+1,balance=balance+? WHERE user_id=?',(VIDEO_REWARD,r['user_id']));c.commit();c.close();return {'message':f'Video {vid} completed.'}
class W(BaseModel):country:str=Field(min_length=2);payment_method:str=Field(min_length=2);full_name:str=Field(min_length=2);wallet_phone:str=Field(min_length=7);amount:float=Field(gt=0)
@app.post('/api/withdrawals')
def withdraw(w:W,x_telegram_init_data:Optional[str]=Header(None)):
 r=user(x_telegram_init_data)
 if r['invite_count']<12 or not r['joined_channel'] or r['videos_completed']<20:raise HTTPException(400,'Withdrawal is locked. Complete all requirements.')
 if w.amount>r['balance']:raise HTTPException(400,'Insufficient balance.')
 c=db();c.execute('INSERT INTO withdrawals(user_id,country,payment_method,full_name,wallet_phone,amount) VALUES(?,?,?,?,?,?)',(r['user_id'],w.country,w.payment_method,w.full_name,w.wallet_phone,w.amount));c.execute('UPDATE users SET balance=balance-? WHERE user_id=?',(w.amount,r['user_id']));c.commit();c.close();return {'message':'Withdrawal request submitted. Status: Pending.'}
