import asyncio
import json
import logging
import struct
import zlib
import base64

import brotli
import aiohttp
from backend import get_wbi
from backend import util
from backend import dm_pb2

logger = logging.getLogger("DanmuService")

class DanmuService:
    def __init__(self, api_client, session_state):
        self.api = api_client
        self.state = session_state
        self.ws = None
        self.running = False
        self.heartbeat_task = None
        self.receive_task = None
        self.message_callback = None
        self.log_callback = None
        self.session = None

    def set_callback(self, callback):
        self.message_callback = callback

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, msg):
        logger.info(msg)
        if self.log_callback:
            self.log_callback(msg)

    def _mask_string(self, s, visible_start=2, visible_end=2):
        """简单的字符串脱敏"""
        if not s or len(s) <= visible_start + visible_end:
            return "***"
        return s[:visible_start] + "***" + s[-visible_end:]

    def send_danmu(self, msg):
        """发送弹幕 (同步方法)"""
        room_id = self.state.room_id
        if not room_id:
            return {"code": -1, "msg": "未获取到房间ID"}
            
        csrf = self.api.cookies.get('bili_jct')
        if not csrf:
             return {"code": -1, "msg": "未获取到 CSRF Token"}

        success, res = self.api.send_danmu(room_id, msg, csrf)
        if success:
             # 处理特定的错误码
             code = res.get('code')
             msg_text = res.get('msg', '未知错误')
             
             if code == 1003212:
                 msg_text = "超出限制长度"
             elif code == 0:
                 msg_text = "发送成功"
             elif code == -101:
                 msg_text = "未登录"
             elif code == -400:
                 msg_text = "参数错误"
             elif code == 10031:
                 msg_text = "发送频率过高"
             
             return {"code": code, "msg": msg_text}
        else:
             return {"code": -1, "msg": "网络请求失败"}

    async def get_danmu_info(self, room_id):
        """获取弹幕服务器信息"""
        try:
            # 1. 准备参数
            params = {
                "id": room_id,
                "type": 0
            }
            
            # 2. 获取 Wbi 签名
            signed_params, _ = get_wbi.get_w_rid_and_wts(params)

            if 'buvid3' not in self.api.cookies:
                buvid3 = self.api.get_buvid3()
                if buvid3:
                    self.api.cookies['buvid3'] = buvid3
                    self._log(f"Fetched buvid3: {self._mask_string(buvid3, 4, 4)}")
                else:
                    logger.warning("Failed to fetch buvid3")
            
            # 3. 请求接口
            success, res = self.api._req("GET", "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo", params=signed_params)
            
            if success and res['code'] == 0:
                return res['data']
            else:
                logger.error(f"Failed to get danmu info: {res}")
                return None
        except Exception as e:
            logger.error(f"Error getting danmu info: {e}")
            return None

    async def connect(self, room_id):
        """连接弹幕服务器"""
        if self.running:
            await self.stop()

        self.running = True
        
        # 尝试获取 buvid3，如果不存在则先获取
        if 'buvid3' not in self.api.cookies:
            buvid3 = self.api.get_buvid3()
            if buvid3:
                self.api.cookies['buvid3'] = buvid3
                self._log(f"Fetched buvid3: {self._mask_string(buvid3, 4, 4)}")
            else:
                logger.warning("Failed to fetch buvid3")

        # 尝试获取 uid
        if not self.state.uid:
             success, res = self.api.get_user_info()
             if success and res['code'] == 0 and res['data']['isLogin']:
                 self.state.uid = res['data']['mid']
                 self._log(f"Fetched uid: {self._mask_string(str(self.state.uid), 2, 2)}")
             else:
                 self.state.uid = 0
                 self._log("User not logged in, using uid=0")

        danmu_info = await self.get_danmu_info(room_id)
        if not danmu_info:
            return False

        token = danmu_info['token']
        host_list = danmu_info['host_list']
        
        # 优先使用 wss
        ws_url = f"wss://{host_list[0]['host']}:{host_list[0]['wss_port']}/sub"
        
        try:
            # # 获取 buvid3
            # buvid3 = self.api.cookies.get('buvid3', '')
            # headers = {}
            # if buvid3:
            #     headers['Cookie'] = f'buvid3={buvid3}'

            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(ws_url, headers=self.api.headers, )
            
            # 发送认证包
            auth_data = {
                "uid": int(self.state.uid),
                "roomid": int(room_id),
                "protover": 3,
                "platform": "web",
                "type": 2,
                "key": token
            }
            await self.send_packet(7, json.dumps(auth_data))
            
            # 启动心跳和接收任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            self._log(f"Connected to danmu server: {ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to danmu server: {e}")
            self.running = False
            if self.session:
                await self.session.close()
                self.session = None
            return False

    async def stop(self):
        """停止弹幕服务"""
        self.running = False
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
            self.session = None
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        self._log("Danmu service stopped")

    async def send_packet(self, operation, body):
        """发送数据包"""
        if not self.ws:
            return
        
        body_bytes = body.encode('utf-8')
        header = struct.pack('!IHHII', 16 + len(body_bytes), 16, 1, operation, 1)
        await self.ws.send_bytes(header + body_bytes)

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                await self.send_packet(2, "")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _receive_loop(self):
        """接收循环"""
        while self.running:
            try:
                msg = await self.ws.receive()
                if msg.type == aiohttp.WSMsgType.BINARY:
                    await self._decode_packet(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break

    async def _decode_packet(self, data):
        """解码数据包"""
        offset = 0
        while offset < len(data):
            try:
                packet_len, header_len, proto_ver, operation, seq = struct.unpack('!IHHII', data[offset:offset+16])
                body = data[offset+16:offset+packet_len]
                
                if proto_ver == 2:
                    # zlib 压缩
                    body = zlib.decompress(body)
                    await self._decode_packet(body)
                elif proto_ver == 3:
                    # brotli 压缩
                    body = brotli.decompress(body)
                    await self._decode_packet(body)
                else:
                    if operation == 5:
                        # 普通包 (命令)
                        try:
                            body_json = json.loads(body.decode('utf-8'))
                            await self._handle_command(body_json)
                        except Exception as e:
                            logger.error(f"JSON decode error: {e}")
                    elif operation == 3:
                        # 心跳回复 (人气值)
                        popularity = struct.unpack('!I', body)[0]
                        # logger.debug(f"Popularity: {popularity}")
                    elif operation == 8:
                        # 认证包回复
                        try:
                            body_json = json.loads(body.decode('utf-8'))
                            if body_json.get('code') == 0:
                                self._log("Danmu authentication successful")
                            else:
                                logger.error(f"Danmu authentication failed: {body_json}")
                        except Exception as e:
                            logger.error(f"Auth response decode error: {e}")
                
                offset += packet_len
            except Exception as e:
                logger.error(f"Packet decode error: {e}")
                break

    async def _handle_command(self, command):
        """处理命令"""
        cmd = command.get('cmd', '')
        if cmd.startswith('DANMU_MSG'):
            # print(command)
            info = command.get('info', [])
            # print(info)
            if info:
                danmu_data = {
                    'type': 'danmu',
                    'uid': info[2][0],
                    'uname': info[2][1],
                    'face': '', # 弹幕消息中不直接包含头像，需要额外获取或从 info[0][15]['user']['base']['face'] 获取
                    'msg': info[1]
                }
                
                # 尝试获取头像
                try:
                    if len(info) > 0 and len(info[0]) > 15:
                         extra = info[0][15]
                         if 'user' in extra and 'base' in extra['user']:
                             danmu_data['face'] = extra['user']['base']['face']
                except:
                    pass

                if self.message_callback:
                    self.message_callback(danmu_data)
        
        elif cmd == 'INTERACT_WORD':
             # 交互消息（进场、关注、分享）
             data = command.get('data', {})
             msg_type = data.get('msg_type')
             
             # 尝试转为 int
             try:
                 msg_type = int(msg_type)
             except:
                 pass

             msg_text = ""
             if msg_type == 1:
                 msg_text = "进入直播间"
             elif msg_type == 2:
                 msg_text = "关注了直播间"
             elif msg_type == 3:
                 msg_text = "分享了直播间"
             
             if msg_text:
                 self._log(f"Interact: {data.get('uname')} {msg_text}")
                 interact_data = {
                     'type': 'interact',
                     'uid': data.get('uid'),
                     'uname': data.get('uname'),
                     'msg': msg_text
                 }
                 if self.message_callback:
                     self.message_callback(interact_data)

        elif cmd.startswith('ENTRY_EFFECT'):
             # 进场特效
             data = command.get('data', {})
             # print(data)
             copy_writing = data.get('copy_writing')
             if copy_writing:
                 self._log(f"Entry Effect: {copy_writing}")
                 msg = copy_writing.replace('<%', '').replace('%>', '')
                 interact_data = {
                     'type': 'interact',
                     'uid': data.get('uid'),
                     'uname': '', # 名字在 msg 里
                     'msg': msg
                 }
                 if self.message_callback:
                     self.message_callback(interact_data)

        elif cmd.startswith('SEND_GIFT'):
            # 送礼
            data = command.get('data', {})
            # print(data)
            gift_name = data.get('giftName') or data.get('gift_name')
            self._log(f"Gift: {data.get('uname')} sent {gift_name}")
            gift_data = {
                'type': 'gift',
                'uid': data.get('uid'),
                'uname': data.get('uname'),
                'face': data.get('face'),
                'gift_name': gift_name,
                'num': data.get('num'),
                'action': data.get('action') or '投喂'
            }
            if self.message_callback:
                self.message_callback(gift_data)

        elif cmd.startswith('COMBO_SEND'):
            # 连击送礼
            data = command.get('data', {})
            gift_name = data.get('gift_name') or data.get('giftName')
            self._log(f"Combo Gift: {data.get('uname')} sent {gift_name} x {data.get('combo_num')}")
            gift_data = {
                'type': 'gift',
                'uid': data.get('uid'),
                'uname': data.get('uname'),
                'face': '', 
                'gift_name': gift_name,
                'num': data.get('combo_num'),
                'action': data.get('action') or '投喂'
            }
            if self.message_callback:
                self.message_callback(gift_data)
        
        elif cmd.startswith('INTERACT_WORD_V2'):
             # 交互消息（进场、关注、分享）
             data = command.get('data', {})

             # print(data)
             
             # 先用 base64 解码 data['pb'] 内的字符串为字节数据pb，再使用proto文件解码pb数据。
             try:
                 pb_data = base64.b64decode(data.get('pb', ''))
                 dm_v2 = dm_pb2.InteractWordV2()
                 dm_v2.ParseFromString(pb_data)
                 
                 msg_type = dm_v2.msg_type
                 uname = dm_v2.uname
                 uid = dm_v2.uid
                 
                 msg_text = ""
                 if msg_type == 1:
                     msg_text = "进入直播间"
                 elif msg_type == 2:
                     msg_text = "关注了直播间"
                 elif msg_type == 3:
                     msg_text = "分享了直播间"
                 
                 if msg_text:
                     self._log(f"Interact V2: {uname} {msg_text}")
                     interact_data = {
                         'type': 'interact',
                         'uid': uid,
                         'uname': uname,
                         'msg': msg_text
                     }
                     if self.message_callback:
                         self.message_callback(interact_data)
             except Exception as e:
                 logger.error(f"Decode INTERACT_WORD_V2 error: {e}")
