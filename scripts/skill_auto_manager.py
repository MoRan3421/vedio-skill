#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UMX Skill 自动扫描、分类、索引与 README 更新器；无需付费 API。"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'SKILLS_INDEX.json'; README=ROOT/'README.md'; REPORT=ROOT/'reports'/'skill-scan-report.json'
IGNORE={'.git','.github','scripts','reports','node_modules','__pycache__'}
IGNORE_FILES={'README.md','README-归档说明.md','SKILLS_INDEX.json','LICENSE'}
EXTS={'.txt','.md','.skill','.prompt'}
def read_text(p):
    try: return p.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError: return p.read_text(encoding='gb18030',errors='replace')
def classify(p,body):
    parts='/'.join(p.parts)
    # 已归档目录优先作为分类依据，避免正文关键词导致误分类。
    path_rules=[
      ('01-人物角色设计','01｜人物角色设计中心','🎨','character'),
      ('02-剧本创作','02｜剧本创作中心','📖','script'),
      ('03-动漫与影视制作','03｜动漫与影视制作中心','🎬','production'),
      ('04-歌曲与音乐制作','04｜歌曲与音乐制作中心','🎵','music'),
      ('05-分镜与视觉特效','05｜分镜与视觉特效中心','🎞️','storyboard'),
      ('06-AI Skill 管理','06｜AI Skill 管理中心','🧠','skill-management'),
      ('07-团团官方视觉规范','07｜团团官方视觉规范','🌟','visual-standard'),
      ('08-统一 Skill 文档规范','08｜统一 Skill 文档规范','📚','document-standard'),
      ('09-后续新增 Skill 登记规范','09｜后续新增 Skill 登记规范','📝','intake-standard'), ('10-官方管理原则','10｜官方管理原则','📌','management-principles')
    ]
    for prefix,label,emoji,cid in path_rules:
        if prefix in parts: return (cid,label,emoji,'高')
    hay=(p.name+' '+body[:16000]).lower()
    keyword_rules=[
      ('character','01｜人物角色设计中心','🎨',['character design','character sheet','人物设计','角色设计','人物设定','三视图','设定集']),
      ('script','02｜剧本创作中心','📖',['screenwriting','screenplay','script master','剧本','编剧','叙事总控']),
      ('music','04｜歌曲与音乐制作中心','🎵',['theme song','song creation','music video','mv','主题曲','歌曲','音乐','配乐','suno','op片头','ed片尾','bgm']),
      ('comic2d','03｜动漫与影视制作中心','🎬',['dynamic comic','animated comic','2d animated','2d动态漫画','二维动态漫画']),
      ('donghua3d','03｜动漫与影视制作中心','🎬',['3d donghua','chinese 3d animation','3d国漫','国漫制作']),
      ('liveaction','03｜动漫与影视制作中心','🎬',['live-action','live action','film and television','真人影视','真人电影']),
      ('storyboard','05｜分镜与视觉特效中心','🎞️',['storyboard','visual effects','vfx','分镜','运镜','视觉特效','粒子特效']),
      ('skill-management','06｜AI Skill 管理中心','🧠',['skill manager','skill management','auto manager','自动识别','自动分类','skill管理'])
    ]
    for cid,label,emoji,terms in keyword_rules:
        if any(term in hay for term in terms): return (cid,label,emoji,'中')
    return ('uncategorized','待确认分类','📥','低')
def main():
    found=[]; hashes={}
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.name in IGNORE_FILES or p.name.startswith('.'): continue
        rel=p.relative_to(ROOT)
        if any(part in IGNORE for part in rel.parts): continue
        if p.suffix.lower() not in EXTS and p.suffix: continue
        try:
            raw=p.read_bytes()
            if b'\x00' in raw[:4096]: continue
            body=read_text(p)
        except (OSError,UnicodeError): continue
        if len(body.strip())<80: continue
        cid,cat,emoji,confidence=classify(p,body); digest=hashlib.sha256(raw).hexdigest()
        duplicate=hashes.get(digest); hashes.setdefault(digest,rel.as_posix())
        ver=re.search(r'\bV(?:ERSION)?\s*([0-9]+(?:\.[0-9]+)*)',body,re.I)
        title=next((x.strip().lstrip('# ').strip() for x in body.splitlines()[:40] if x.strip() and len(x.strip())<140),p.stem)
        purpose=next((re.sub(r'^\*\*.*?\*\*[：:]\s*','',x.strip()) for x in body.splitlines() if re.search(r'(主要用途|核心定位|系统类型|用途|目标)\s*[：:]',x)),'请查看原始 Skill 全文。')
        found.append({'id':'UMX-'+digest[:10],'name':title,'path':rel.as_posix(),'category_id':cid,'category':cat,'emoji':emoji,'confidence':confidence,'version':'V'+ver.group(1) if ver else '未标注','description':purpose[:220],'sha256':digest,'duplicate_of':duplicate,'status':'待确认' if cid=='uncategorized' else ('重复内容' if duplicate else '已识别')})
    found.sort(key=lambda x:(x['category'],x['name'].lower(),x['path']))
    now=datetime.now(timezone.utc).isoformat()
    categories=[{'id':'00','name':'知识库首页'},{'id':'01','name':'人物角色设计中心','subcategories':['2D动态漫画人物设计','3D国漫人物设计','真人影视人物设计','通用专业人物设定系统']},{'id':'02','name':'剧本创作中心','subcategories':['2D动态漫画剧本','3D国漫剧本','真人影视剧本','漫剧剧本总控']},{'id':'03','name':'动漫与影视制作中心','subcategories':['2D动态漫画制作','3D国漫制作','真人影视制作']},{'id':'04','name':'歌曲与音乐制作中心','subcategories':['原创主题曲','OP片头曲','ED片尾曲','BGM背景音乐','MV制作','歌词与音乐创作']},{'id':'05','name':'分镜与视觉特效中心','subcategories':['分镜制作','镜头设计','战斗与视觉特效','动作与舞蹈']},{'id':'06','name':'AI Skill 管理中心','subcategories':['Skill文件管理','自动识别与分类','GitHub自动化','知识库维护']},{'id':'07','name':'团团官方视觉规范','subcategories':['官方发色体系','视觉设计要求','页面风格']},{'id':'08','name':'统一 Skill 文档规范','subcategories':['原始提示词完整保存','文件命名与版本标注','来源与更新记录']},{'id':'09','name':'后续新增 Skill 登记规范','subcategories':['新增Skill登记','分类识别','双平台归档']},{'id':'10','name':'官方管理原则','subcategories':['真实性核验','原文保留','分类一致','版本与权限管理']} ]\n    data={'schema_version':2,'repository':'MoRan3421/vedio-skill','language':'zh-CN','generated_at':now,'total':len(found),'categories':categories,'rules':{'music':'OP、ED、主题曲、BGM、MV统一归入04｜歌曲与音乐制作中心','preserve_original':True},'skills':found}
    INDEX.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    report={'generated_at':now,'total':len(found),'recognized':sum(x['status']=='已识别' for x in found),'needs_review':sum(x['status']=='待确认' for x in found),'duplicates':sum(x['duplicate_of'] is not None for x in found),'skills':found}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 🌙 UMX AI SKILL LIBRARY｜自动技能目录','','技能文件：{} 项'.format(len(found)),'扫描时间（UTC）：{}'.format(now),'','## 官方分类目录','']
    official=[
      ('00｜知识库首页','🏛️'),('01｜人物角色设计中心','🎨'),('02｜剧本创作中心','📖'),
      ('03｜动漫与影视制作中心','🎬'),('04｜歌曲与音乐制作中心','🎵'),
      ('05｜分镜与视觉特效中心','🎞️'),('06｜AI Skill 管理中心','🧠'),
      ('07｜团团官方视觉规范','🌟'),('08｜统一 Skill 文档规范','📚'),
      ('09｜后续新增 Skill 登记规范','📝'),('10｜官方管理原则','📌')]
    for category,emoji in official:
        items=[x for x in found if x['category']==category]
        lines += ['### {} {}（{} 项）'.format(emoji,category,len(items)),'']
        if not items: lines += ['- 暂无已归档 Skill。','']
        for x in items: lines += [f"- [{x['name']}]({x['path']}) — {x['version']} / {x['status']}",f"  - 用途：{x['description']}"]
        lines.append('')
    lines += ['## 统一分类规则','','- OP、ED、主题曲、BGM、MV 全部归入「04｜歌曲与音乐制作中心」，不单独建立 MV 一级分类。','- 原始 Skill 完整内容优先；目录摘要只用于导航。','- 不确定分类时标记待确认；不删除、不改写原始文件。','','## 自动管理文件','','- 索引：SKILLS_INDEX.json','- 报告：reports/skill-scan-report.json','- 程序：scripts/skill_auto_manager.py','- 工作流：.github/workflows/skill-auto-manager.yml','']
    README.write_text('\n'.join(lines),encoding='utf-8')
    print('扫描完成：{} 项；待确认：{}；重复：{}'.format(len(found),report['needs_review'],report['duplicates']))
if __name__=='__main__': main()