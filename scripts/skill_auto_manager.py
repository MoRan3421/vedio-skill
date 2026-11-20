#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UMX Skill 自动扫描、分类、索引与 README 更新器；无需付费 API。"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'SKILLS_INDEX.json'; README=ROOT/'README.md'; REPORT=ROOT/'reports'/'skill-scan-report.json'
IGNORE={'.git','.github','scripts','reports','node_modules','__pycache__'}
IGNORE_FILES={'README.md','SKILLS_INDEX.json','LICENSE'}
EXTS={'.txt','.md','.skill','.prompt'}
CATS=[
('character','人物角色设计','🎨',['character design','character sheet','人物设计','角色设计','人物设定','三视图','设定集']),
('script','剧本创作','📖',['screenwriting','screenplay','script master','剧本','编剧']),
('music','歌曲与音乐制作','🎵',['theme song','song creation','music video','mv','op','ed','bgm','主题曲','歌曲','音乐','配乐','suno']),
('comic2d','动漫与影视制作｜2D动态漫画','🌸',['dynamic comic','animated comic','2d animated','2d动态漫画','动态漫画制作']),
('donghua3d','动漫与影视制作｜3D国漫','⚔️',['3d donghua','chinese 3d animation','3d国漫','国漫制作']),
('liveaction','动漫与影视制作｜真人影视','🎬',['live-action','live action','film and television','真人影视','真人电影','影视制作']),
('storyboard','分镜与视觉特效','🎞️',['storyboard','visual effects','vfx','分镜','运镜','视觉特效','粒子特效']),
('skill-management','AI Skill 管理','🧠',['skill manager','skill management','auto manager','自动识别','自动分类','skill管理']),
('worldbuilding','世界观与IP开发','🌍',['worldbuilding','世界观','宇宙设定','ip开发']),
('game','游戏与互动内容','🎮',['game development','roblox','游戏开发','游戏设计'])]
def read_text(p):
    try: return p.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError: return p.read_text(encoding='gb18030',errors='replace')
def classify(p,body):
    name=p.name.lower(); hay=(name+' '+body[:12000].lower()); scores=[]
    for cid,label,emoji,terms in CATS:
        score=sum((5 if t in name else 0)+(1 if t in hay else 0) for t in terms)
        if score: scores.append((score,cid,label,emoji))
    scores.sort(reverse=True)
    if not scores or scores[0][0]<3 or (len(scores)>1 and scores[0][0]-scores[1][0]<2 and scores[0][0]<7):
        return ('uncategorized','待确认分类','📥','低')
    s=scores[0]; return (s[1],s[2],s[3],'高' if s[0]>=7 else '中')
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
    data={'schema_version':2,'repository':'MoRan3421/vedio-skill','language':'zh-CN','generated_at':now,'total':len(found),'skills':found}
    INDEX.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    report={'generated_at':now,'total':len(found),'recognized':sum(x['status']=='已识别' for x in found),'needs_review':sum(x['status']=='待确认' for x in found),'duplicates':sum(x['duplicate_of'] is not None for x in found),'skills':found}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    groups={}
    for x in found: groups.setdefault(x['category'],[]).append(x)
    lines=['# UMX 创意工坊｜AI Skill 自动目录','',f'技能文件：{len(found)} 项','',f'扫描时间（UTC）：{now}','','## 技能分类目录','']
    for category,items in groups.items():
        lines += [f"### {items[0]['emoji']} {category}（{len(items)} 项）",'']
        for x in items: lines += [f"- [{x['name']}]({x['path']}) — {x['version']} / {x['status']}",f"  - 用途：{x['description']}"]
        lines.append('')
    lines += ['## 统一分类规则','','- OP、ED、主题曲、BGM、MV 全部归入「歌曲与音乐制作」，不单独建立 MV 一级分类。','- 2D 动态漫画、3D 国漫、真人影视分别识别与归档。','- 低置信度文件标记待确认；不删除、不改写原始 Skill。','','## 自动管理文件','','- 索引：SKILLS_INDEX.json','- 报告：reports/skill-scan-report.json','- 程序：scripts/skill_auto_manager.py','- 工作流：.github/workflows/skill-auto-manager.yml','']
    README.write_text('\n'.join(lines),encoding='utf-8')
    print('扫描完成：{} 项；待确认：{}；重复：{}'.format(len(found),report['needs_review'],report['duplicates']))
if __name__=='__main__': main()