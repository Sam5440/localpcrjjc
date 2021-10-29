#Created by ColdThunder11 2021/1/3
#changed by lulu to another api 2021/1/7
import asyncio
import copy
import datetime
import json
import time
from os import path

import hoshino
import nonebot
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data, chara
from hoshino.typing import NoticeSession

from .queryapi import getprofile
from .queryapi_full import getprofilefull

sv_help = '''
[竞技场绑定 uid] 绑定竞技场排名变动推送（仅下降），默认双场均启用
[竞技场查询 (uid)] 查询竞技场简要信息
[停止竞技场订阅] 停止战斗竞技场排名变动推送
[停止公主竞技场订阅] 停止公主竞技场排名变动推送
[启用竞技场订阅] 启用战斗竞技场排名变动推送
[启用公主竞技场订阅] 启用公主竞技场排名变动推送
[删除竞技场订阅] 删除竞技场排名变动推送绑定
[竞技场订阅状态] 查看排名变动推送绑定状态
[信息查询 (uid)] 查询个人信息
'''.strip()

sv = Service('竞技场推送',help_=sv_help,enable_on_default=False , bundle='pcr查询')

Inited = False
pcrprofile = None
binds = {}
arena_ranks = {}
grand_arena_ranks ={}
tr = None

@sv.on_fullmatch('jjc帮助', only_to_me=False)
async def send_jjchelp(bot, ev):
    await bot.send(ev, sv_help)

def Init():
    global Inited
    global pcrprofile
    global binds
    global tr
    Inited = True
    config_path = path.join(path.dirname(__file__),"binds.json")
    with open(config_path,"r",encoding="utf8")as fp:
        binds = json.load(fp)

def save_binds():
    config_path = path.join(path.dirname(__file__),"binds.json")
    jsonStr = json.dumps(binds, indent=4)
    with open(config_path,"r+",encoding="utf8")as fp:
        fp.truncate(0)
        fp.seek(0)
        fp.write(jsonStr)

@sv.on_rex(r'竞技场绑定 (.{0,15})$')
async def on_arena_bind(bot,ev):
    global binds
    if not Inited:
        Init()
    robj = ev['match']
    id = robj.group(1)
    if not id.isdigit() or not len(id) == 13:
        await bot.send(ev,"ID格式错误，请检查",at_sender=True)
        return
    uid = str(ev['user_id'])
    gid = str(ev['group_id'])
    if not uid in binds["arena_bind"]:
        binds["arena_bind"][uid] = {"id":id,"uid":uid,"gid":gid,"arena_on":True,"grand_arena_on":True,"nightslient_on": False}
    else:
        binds["arena_bind"][uid]["id"] = id
        binds["arena_bind"][uid]["uid"] = uid
        binds["arena_bind"][uid]["gid"] = gid
    save_binds()
    await bot.send(ev,"竞技场绑定成功",at_sender=True)

@sv.on_rex(r'(竞技场查询 (.{0,15})$)|(^竞技场查询$)')
async def on_query_arena(bot,ev):
    if not Inited:
        Init()
    robj = ev['match']
    try:
        id = robj.group(2)
    except:
        id = ""
    if id=='' or id==None:
        uid = str(ev['user_id'])
        if not uid in binds["arena_bind"]:
            await bot.send(ev,"您还未绑定竞技场",at_sender=True)
            return
        else:
            id = binds["arena_bind"][uid]["id"]
    if not id.isdigit() or not len(id) == 13:
        await bot.send(ev,"ID格式错误，请检查",at_sender=True)
        return
    try:
        res = getprofile(int(id))
        res = res["user_info"]
        '''if res["err_code"] == 403:
            sv.logger.info("您的API KEY错误或者被屏蔽，请尽快停止本插件")
            await bot.send(ev,"错误403，查询出错，请联系维护者",at_sender=True)
            return'''
        if res == "queue":
            sv.logger.info("成功添加至队列"),
            await bot.send(ev,"请等待源站更新数据，稍等几分钟再来查询",at_sender=True)
        if res == "id err":
            sv.logger.info("该viewer_id有误")
            await bot.send(ev,"查询出错，请检查ID是否正确",at_sender=True)
            return
        strList = []
        strList.append("\n")
        strList.append("竞技场排名：")
        strList.append(str(res["arena_rank"]))
        strList.append("\n")
        strList.append("公主竞技场排名：")
        strList.append(str(res["grand_arena_rank"]))
        '''
        # 范围时间
        t1 = '8:00'
        t2 = '22:00'
        now = datetime.datetime.now().strftime("%H:%M")
        print("当前时间:" + now)
        if t1 < now < t2:
            strList.append("\n时间还早，加油骑士君!")
        else：
            strList.append("\n该休息了呢，开启免打扰停止推送")
        '''
        await bot.send(ev,"".join(strList),at_sender=True)
    except:
        await bot.send(ev,"查询出错，请检查ID是否正确",at_sender=True)
    pass

@sv.on_fullmatch('开启免打扰')
async def disable_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["nightslient_on"] = True
        save_binds()
        await bot.send(ev,"已经停止夜间推送（22:00-8:00)",at_sender=True)

@sv.on_fullmatch('关闭免打扰')
async def disable_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["nightslient_on"] = False
        save_binds()
        await bot.send(ev,"已经开启夜间推送（22:00-8:00)",at_sender=True)

@sv.on_fullmatch('停止竞技场订阅')
async def disable_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["arena_on"] = False
        save_binds()
        await bot.send(ev,"停止竞技场订阅成功",at_sender=True)

@sv.on_fullmatch('停止公主竞技场订阅')
async def disable_grand_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["grand_arena_on"] = False
        save_binds()
        await bot.send(ev,"停止公主竞技场订阅成功",at_sender=True)

@sv.on_fullmatch('启用竞技场订阅')
async def enable_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["arena_on"] = True
        save_binds()
        await bot.send(ev,"启用竞技场订阅成功",at_sender=True)

@sv.on_fullmatch('启用公主竞技场订阅')
async def enable_arena_sub(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        binds["arena_bind"][uid]["grand_arena_on"] = True
        save_binds()
        await bot.send(ev,"启用公主竞技场订阅成功",at_sender=True)

@sv.on_prefix('删除竞技场订阅')
async def delete_arena_sub(bot,ev):
    if not Inited:
        Init()
    if len(ev.message) == 1 and ev.message[0].type == 'text' and not ev.message[0].data['text']:
        uid = str(ev['user_id'])
        if not uid in binds["arena_bind"]:
            await bot.finish(ev, "您还未绑定竞技场", at_sender=True)
        else:
            binds["arena_bind"].pop(uid)
            save_binds()
            await bot.send(ev, "删除竞技场订阅成功", at_sender=True)
    elif ev.message[0].type == 'at':
        if not priv.check_priv(ev, priv.SUPERUSER):
            await bot.finish(ev, '删除他人订阅请联系维护', at_sender=True)
        else:
            uid = str(ev.message[0].data['qq'])
            if not uid in binds["arena_bind"]:
                await bot.finish(ev, "对方尚未绑定竞技场", at_sender=True)
            else:
                binds["arena_bind"].pop(uid)
                save_binds()
                await bot.send(ev, "删除竞技场订阅成功", at_sender=True)
    else:
        await bot.finish(ev, '参数格式错误, 请重试')

@sv.on_fullmatch('竞技场订阅状态')
async def send_arena_sub_status(bot,ev):
    if not Inited:
        Init()
    uid = str(ev['user_id'])
    if not uid in binds["arena_bind"]:
        await bot.send(ev,"您还未绑定竞技场",at_sender=True)
    else:
        id = binds["arena_bind"][uid]["id"]
        res = getprofilefull(int(id))
        res = res["user_info"]
        strList = []
        strList.append("\n绑定用户名：")
        strList.append(str(res["user_name"]))
        strList.append("\n竞技场绑定ID：\n")
        strList.append(str(binds["arena_bind"][uid]["id"]))
        strList.append("\n排名推送群：")
        strList.append(str(binds["arena_bind"][uid]["gid"]))
        strList.append("\n")
        strList.append("竞技场排名：")
        strList.append(str(res["arena_rank"]))
        strList.append("\n")
        strList.append("公主竞技场排名：")
        strList.append(str(res["grand_arena_rank"]))
        await bot.send(ev,"".join(strList),at_sender=True)
        strList.append("\n竞技场订阅：")
        if binds["arena_bind"][uid]["arena_on"]:
            strList.append("开启")
        else:
            strList.append("关闭")
        strList.append("\n公主竞技场订阅：")
        if binds["arena_bind"][uid]["grand_arena_on"]:
            strList.append("开启")
        else:
            strList.append("关闭")
        strList.append("\n免打扰状态(测试功能，未安装)：")
        if binds["arena_bind"][uid]["nightslient_on"]:
            strList.append("开启")
        else:
            strList.append("关闭")    
        strList.append("\n")
        strList.append(str(res["user_comment"]))
        await bot.send(ev,"".join(strList),at_sender=True)

@sv.scheduled_job('interval', minutes=3)
async def on_arena_schedule():
    global arena_ranks
    global grand_arena_ranks
    bot = nonebot.get_bot()
    if not Inited:
        Init()
    arena_bind = copy.deepcopy(binds["arena_bind"])
    for user in arena_bind:
        user = str(user)
        await asyncio.sleep(1)
        try:
            res = getprofile(int(binds["arena_bind"][user]["id"]))
            res = res["user_info"]
            if binds["arena_bind"][user]["arena_on"]:
                if not user in arena_ranks:
                    arena_ranks[user] = res["arena_rank"]
                else:
                    origin_rank = arena_ranks[user]
                    new_rank = res["arena_rank"]
                    if origin_rank >= new_rank:#不动或者上升
                        arena_ranks[user] = new_rank
                    else:
                        msg = "[CQ:at,qq={uid}]您的竞技场排名发生变化：{origin_rank}->{new_rank}".format(uid=binds["arena_bind"][user]["uid"], origin_rank=str(origin_rank), new_rank=str(new_rank))
                        arena_ranks[user] = new_rank
                        await bot.send_group_msg(group_id=int(binds["arena_bind"][user]["gid"]),message=msg)
                        await asyncio.sleep(1)
            if binds["arena_bind"][user]["grand_arena_on"]:
                if not user in grand_arena_ranks:
                    grand_arena_ranks[user] = res["grand_arena_rank"]
                else:
                    origin_rank = grand_arena_ranks[user]
                    new_rank = res["grand_arena_rank"]
                    if origin_rank >= new_rank:#不动或者上升
                        grand_arena_ranks[user] = new_rank
                    else:
                        msg = "[CQ:at,qq={uid}]您的公主竞技场排名发生变化：{origin_rank}->{new_rank}".format(uid=binds["arena_bind"][user]["uid"], origin_rank=str(origin_rank), new_rank=str(new_rank))
                        grand_arena_ranks[user] = new_rank
                        await bot.send_group_msg(group_id=int(binds["arena_bind"][user]["gid"]),message=msg)
                        await asyncio.sleep(1)
        except:
            sv.logger.info("对{id}的检查出错".format(id=binds["arena_bind"][user]["id"]))

@sv.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    if not Inited:
        Init()
    uid = str(session.ctx['user_id'])
    if not uid in binds["arena_bind"]:
        pass
    else:
        binds["arena_bind"].pop(uid)
        save_binds()
        pass
    return

@sv.on_rex(r'(信息查询 (.{0,15})$)|(^信息查询$)')
async def on_query_info(bot,ev):
    if not Inited:
        Init()
    robj = ev['match']
    try:
        id = robj.group(2)
    except:
        id = ""
    if id=='' or id==None:
        uid = str(ev['user_id'])
        if not uid in binds["arena_bind"]:
            await bot.send(ev,"您还未绑定竞技场",at_sender=True)
            return
        else:
            id = binds["arena_bind"][uid]["id"]
    if not id.isdigit() or not len(id) == 13:
        await bot.send(ev,"ID格式错误，请检查",at_sender=True)
        return
    try:
        res = getprofilefull(int(id))
        res_c = res["clan_name"]
        res_f = res["favorite_unit"]
        res = res["user_info"]
        if res == "queue":
            sv.logger.info("成功添加至队列"),
            await bot.send(ev,"请等待源站更新数据，稍等几分钟再来查询",at_sender=True)
        if res == "id err":
            sv.logger.info("该viewer_id有误")
            await bot.send(ev,"查询出错，请检查ID是否正确",at_sender=True)
            return
        strList = []
        strList.append("\n")
        strList.append("昵称：")
        
        strList.append(str(res["user_name"]))
        strList.append("\n等级：")
        strList.append(str(res["team_level"]))
        strList.append("\n角色数：")
        strList.append(str(res["unit_num"]))
        strList.append("\n总战力：")
        strList.append(str(res["total_power"]))
    
        strList.append("\n公会：")
        strList.append(str(res_c)) #claninfo可？
    
        strList.append("\n个性签名：")
        strList.append(str(res["user_comment"]))
        ###########################################
        strList.append("\n")
        strList.append("竞技场排名：")
        strList.append(str(res["arena_rank"]))
        strList.append("\n竞技场场次：")
        strList.append(str(res["arena_group"]))
        timeStamp = int(res["arena_time"])
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        strList.append("\n竞技场创建时间：")
        strList.append(str(otherStyleTime))
        ############################################
        strList.append("\n")
        strList.append("公主竞技场排名：")
        strList.append(str(res["grand_arena_rank"]))
        strList.append("\n公主竞技场场次：")
        strList.append(str(res["arena_group"]))
        timeStamp = int(res["grand_arena_time"])
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        strList.append("\n公主竞技场创建时间：")
        strList.append(str(otherStyleTime))
        ############################################
        c = chara.fromid(int(str(res_f["id"])[0:4]))
        msg = f'\n头像人物是:{c.name} {c.icon.cqcode}\n '
        strList.append(msg)
        ###########################################
        await bot.send(ev,"".join(strList),at_sender=True)
    except:
        await bot.send(ev,"查询出错，请检查ID是否正确",at_sender=True)
    pass
@sv1.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    if not Inited:
        Init()
    uid = str(session.ctx['user_id'])
    if not uid in binds["arena_bind"]:
        pass
    else:
        binds["arena_bind"].pop(uid)
        save_binds()
        pass
    return

