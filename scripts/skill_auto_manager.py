#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UMX Skill 自动扫描、分类、索引与 README 生成器；无需付费 API。"""
import hashlib, json, re
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"SKILLS_INDEX.json"; README=ROOT/"README.md"; REPORT=ROOT/"reports"/"skill-scan-report.json"
IGNORE_DIRS={".git",".github","scripts","reports","assets","images","node_modules","__pycache__"}
IGNORE_FILES={"README.md","SKILLS_INDEX.json","LICENSE"}
EXTENSIONS={".txt",".md",".skill",".prompt"}
CATEGORIES=[
{"id":"character","name":"人物角色设计","emoji":"🎨","terms":["人物设计","角色设计","character design","character sheet","三视图","角色设定集","人物设定"]},
{"id":"script","name":"剧本创作","emoji":"📖","terms":["剧本","编剧","screenwriting","screenplay","script master","分镜剧本"]},
{"id":"music","name":"歌曲与音乐制作","emoji":"🎵","terms":["主题曲","歌曲创作","音乐制作","theme song","song creation","歌词","suno"]},

{"id":"comic2d","name":"2D 动态漫画","emoji":"🌸","terms":["2d动态漫画","dynamic comic","animated comic","2d animated","动态漫画制作"]},
{"id":"donghua3d","name":"3D 国漫","emoji":"⚔️","terms":["3d国漫","3d donghua","chinese 3d animation","donghua production"]},
{"id":"liveaction","name":"真人影视","emoji":"🎬","terms":["真人影视","live-action","live action","film and television","影视制作","真人电影"]},
{"id":"game","name":"游戏开发","emoji":"🎮","terms":["游戏开发","game development","roblox studio","game design"]},
{"id":"worldbuilding","name":"世界观设计","emoji":"🌍","terms":["世界观","worldbuilding","宇宙设定"]},
{"id":"environment","name":"建筑与场景设计","emoji":"🏙️","terms":["建筑设计","场景设计","environment design","architecture"]},
{"id":"action","name":"战斗与动作设计","emoji":"⚔️","terms":["战斗设计","动作设计","combat choreography"]},
{"id":"audio","name":"配音与音效制作","emoji":"🎧","terms":["配音","音效","sound design","voice acting","dubbing"]},
{"id":"trailer","name":"宣传片制作","emoji":"📺","terms":["宣传片","预告片","trailer","promo video"]},
{"id":"management","name":"制作管理与质量审核","emoji":"🔍","terms":["质量审核","质量检查","production management","quality assurance"]},
]
def read_text(p):
    try: return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError: return p.read_text(encoding="gb18030",errors="replace")
def classify(p,text):
    name=p.name.lower(); hay=(p.name+" "+text[:16000]).lower(); scores=[]
    for c in CATEGORIES:
        score=sum((5 if t.lower() in name else 0)+(1 if t.lower() in hay else 0) for t in c["terms"])
        if score: scores.append((score,c))
    scores.sort(key=lambda x:x[0],reverse=True)
    if not scores or scores[0][0]<3 or (len(scores)>1 and scores[0][0]-scores[1][0]<2 and scores[0][0]<7): return {"id":"uncategorized","name":"待确认分类","emoji":"📥","confidence":"低"}
    c=scores[0][1]; return {**c,"confidence":"高" if scores[0][0]>=7 else "中"}
def main():
    skills=[]; seen={}; now=datetime.now(timezone.utc).isoformat()
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.name in IGNORE_FILES or p.name.startswith("."): continue
        rel=p.relative_to(ROOT)
        if any(part in IGNORE_DIRS for part in rel.parts): continue
        if p.suffix.lower() not in EXTENSIONS and p.suffix: continue
        try:
            raw=p.read_bytes()
            if b"\x00" in raw[:4096]: continue
            text=read_text(p)
        except (OSError,UnicodeError): continue
        if len(text.strip())<80: continue
        cat=classify(p,text); h=hashlib.sha256(text.encode("utf-8")).hexdigest(); dup=seen.get(h); seen.setdefault(h,rel.as_posix())
        ver=re.search(r"\bV(?:ERSION)?\s*([0-9]+(?:\.[0-9]+)*)",text,re.I)
        title=next((s.strip().lstrip("#").strip() for s in text.splitlines()[:35] if s.strip() and len(s.strip())<140),p.stem)
        desc=next((re.sub(r"^\*\*.*?\*\*[：:]\s*","",s.strip()) for s in text.splitlines() if re.search(r"(主要用途|核心定位|系统类型|用途|目标)\s*[：:]",s)),"请查看原始技能文件。")[:220]
        skills.append({"id":"skill-"+h[:10],"name":title,"filename":p.name,"path":rel.as_posix(),"category_id":cat["id"],"category":cat["name"],"emoji":cat["emoji"],"confidence":cat["confidence"],"version":"V"+ver.group(1) if ver else "未标注","description":desc,"sha256":h,"duplicate_of":dup,"status":"重复内容（保留原文件）" if dup and dup!=rel.as_posix() else ("待确认" if cat["id"]=="uncategorized" else "已识别"),"last_scanned":now})
    skills.sort(key=lambda x:(x["category"],x["name"].lower(),x["path"].lower()))
    payload={"schema_version":1,"repository":"MoRan3421/vedio-skill","generated_at":now,"scan_scope":"TXT、MD、SKILL、PROMPT及可读取的无扩展名文本文件","total":len(skills),"skills":skills}
    INDEX.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({"generated_at":now,"total":len(skills),"recognized":sum(x["status"]=="已识别" for x in skills),"needs_review":sum(x["status"]=="待确认" for x in skills),"duplicates":sum(x["duplicate_of"] is not None for x in skills),"skills":skills},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    groups={}
    for x in skills: groups.setdefault(x["category"],[]).append(x)
    L=["# 🌌 UMX 创意工坊｜AI Skill 技能库","","> 一站式 AI 创意设计、动画、音乐与影视制作技能仓库。","","**仓库：** [MoRan3421/vedio-skill](https://github.com/MoRan3421/vedio-skill)  ","**管理方式：** GitHub Actions 自动扫描、识别、分类并生成目录  ",f"**技能数量：** {len(skills)} 项  ",f"**最近索引时间（UTC）：** {now}","","## 🌟 项目介绍","","UMX 创意工坊汇集可复用的 AI 创作 Skill，覆盖人物设定、剧本创作、动画制作、音乐与 MV、真人影视等领域。每份技能文件保留原始内容；本系统负责读取文件、提取基本资料、判断所属类别，并自动维护本目录。","","## ⚙️ 自动管理功能","","- 自动扫描 TXT、MD、SKILL、PROMPT 及可读取的无扩展名文本文件。","- 根据文件名与正文关键词识别名称、版本、用途及分类。","- 自动生成 SKILLS_INDEX.json 和本 README。","- 检测完全相同的内容并标记重复，不删除原文件。","- 无法可靠识别的文件列入待确认分类。","- 保留原始文件位置，不自动搬动或重命名。","","## 📚 Skill 技能目录",""]
    for cat,items in groups.items():
        L += [f"### {items[0][chr(101)+chr(109)+chr(111)+chr(106)+chr(105)]} {cat}（{len(items)} 项）",""]
        for x in items:
            flags=([x["version"]] if x["version"]!="未标注" else [])+([ "待确认"] if x["confidence"]=="低" else [])+([ "内容重复"] if x["duplicate_of"] else [])
            L += [f"- [{x[chr(110)+chr(97)+chr(109)+chr(101)]}](<{x[chr(112)+chr(97)+chr(116)+chr(104)]}>){chr(32)+chr(183)+chr(32)+chr(183).join(flags) if flags else chr(32)}","  - **文件：** `"+x["path"]+"`","  - **用途：** "+x["description"]]
        L.append("")
    L += ["## 🗂️ 索引与扫描报告","","- [机器可读技能索引](SKILLS_INDEX.json)","- [自动扫描报告](reports/skill-scan-report.json)","- [自动管理程序](scripts/skill_auto_manager.py)","- [GitHub Actions 工作流](.github/workflows/skill-auto-manager.yml)","","## 🔄 自动运行方式","","向 main 分支上传或修改技能文本文件后，GitHub Actions 会自动扫描并更新本目录。也可以在仓库 Actions 页面手动运行工作流。","","## 🧭 分类说明","","分类由文件名和正文关键词规则识别，不调用付费 AI API。无法明确判断时标记为待确认。自动摘要仅用于导航，完整指令请查看原始文件。","","## ⚖️ 使用与版权说明","","使用者应确认原创内容权利及第三方 AI 平台的授权条款。自动分类不构成版权或商业授权判断。","","---","","<p align=\"center\">","","### 🌠 想象 · 创作 · 动画 · 无限可能","","**UMX 创意工坊**  ","*构建想象之外的无限世界。*","","</p>",""]
    README.write_text("\n".join(L),encoding="utf-8")
    print(f"完成：{len(skills)} 项；待确认：{sum(x[chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)]==chr(待确认) for x in skills)}")
if __name__=="__main__": main()