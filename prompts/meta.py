PROMPT_ZH = '''
你需要处理一段通过自动语音识别（ASR）和说话人聚类生成的台本，核心任务是：
1. 理解对话内容，在后续推理、分析时结合上下文。
2. 结构化分析：归纳故事背景、核心情节，并完整解析角色设定。
3. 场景划分：根据时间、地点、角色进出等逻辑依据，将对话拆分为连续且互不重叠的场景。
最终，你需要生成一份标准化的JSON报告，包含故事概要、角色分析和场景划分，并确保所有原始行号（LINE_NUM）均被完整覆盖。

输入数据格式：
```text
LINE_NUM. TEXT
```
- LINE_NUM：连续行号（从0开始）
- TEXT：对话内容（可能含ASR转写错误，但不允许修改）

处理任务说明：
请执行以下三层分析任务，必须基于对话上下文进行合理推理：
1. 故事分析层（"story"）
- 背景推断（"background"）：
    - 提取时间、地点、世界观等关键要素
    - 若无明确线索需标注`N/A`
- 情节归纳（"plot"）：
    - 用3-5句话概括核心故事线
    - 需体现主要矛盾与关键转折

2. 角色分析层（"characters"）
- 角色筛选标准：
    - 必须包含：出场次数多、台词多或对剧情推动有重要作用的主角、配角、旁白
    - 排除：出场次数少、台词少或对主线剧情影响较小的配角、群众
- 角色属性填写规范：
```json
character_json_format = {
    "basic_info": {
        "name": string,          // 优先使用剧本内称呼，其次用特征、身份命名（如“警官”、“暴躁老哥”等）
        "age": "N/A"|大致年龄,     // 推断或标注N/A
        "gender": "男"|"女"|"未知",
        "identity": string,       // 如"退休刑警/高中生/AI助手"
        "characteristic": string, // 至少1个形容词（如"谨慎"）
        "description": { # 总结 "age", "gender", "identity", and "characteristic"，不要包含 "plot_related_info"
            "en": "string",  # Neutral 1-2 sentence summary in English, combine key attributes naturally ("A righteous Wudang warrior" instead of "He is a...")
            "zh": "string"   # 中文版角色人设总结 (采用「身份+特征」的简洁结构 (例：正义的武当侠士)，避免"该角色是"等冗余表达)
        }
    }
    "plot_related_info": {
        "motivations": string,    // 驱动其行为的内在原因
        "relationships": {        // 仅列出明确关系
            [角色名]: "父子/敌对/同事/朋友/恋人..."
        }
    }
}
```

3. 场景划分层（"scenes"）
- 划分规则：
    - 连续性：相邻场景行号必须衔接（end+1=next start）
    - 排他性：单行只能属于一个场景
    - 转换依据：地点；时间；角色进出了；情节转折...
- 场景描述要求：
    - "characters"：在场景中进行对话的角色
        - 首先匹配角色分析层（"characters"）中已定义的角色
        - 若角色分析层（"characters"）中没有匹配的角色，用特征、身份为未定义的角色命名
        - 若未定义角色的特征、身份难以推断，用“路人甲”等匿名称呼命名
    - "description"：时间、地点、核心事件+结果（若有），简洁概括

输出规范：
```json
{
    "story": {
        "background": "string",
        "plot": "string"
    },
    "characters": [character_json_format, ...],
    "scenes": [
        {
            "scene": {
                "characters": ["name1", ...],
                "description": {
                    "en": "string",  # Neutral 1-2 sentence summary of scene time, location and event in English, excluding start or end LINE_NUM
                    "zh": "string"   # 中文版场景描述（1-2句话），包括时间、地点和事件，不要包含start和end LINE_NUM
                }
            },
            "start": int, // 必须≥0
            "end": int, // 必须≥start
            "confidence": { // [0,1]
                "character_assignment": float,
                "scene_segmentation": float,
                "event_accuracy": float
            },
        },
        ...
    ]
    "coverage_check": bool // 是否覆盖了所有行,
}
```
'''

PROMPT_EN = '''
You need to process a script generated through Automatic Speech Recognition (ASR). Your tasks are:  
1. Understand the dialogue content: Incorporate contextual reasoning during subsequent analysis.
2. Structured analysis: Summarize the story background, core plot, and fully analyze character settings.  
3. Scene segmentation: Split the dialogue into continuous, non-overlapping scenes based on logical cues such as time, location, or character entrances/exits.  
Finally, you must generate a standardized JSON report containing the story summary, character analysis, and scene segmentation, ensuring complete coverage of all original line numbers (`LINE_NUM`).  

Input Data Format:  
```text  
LINE_NUM. TEXT  
```  
- LINE_NUM: Continuous line number (starting from 0).
- TEXT: Dialogue content (may contain ASR transcription errors, but don't modify them).  

Task Instructions:
Perform the following three-layer analysis, always based on contextual reasoning:  
1. Story Analysis Layer ("story")  
- Background inference ("background"):  
    - Extract key elements (time, location, worldbuilding, etc.).  
    - Label as `N/A` if no clear clues exist.  
- Plot summary ("plot"):  
    - Summarize the core storyline in 3–5 sentences.  
    - Highlight central conflicts and key turning points.  

2. Character Analysis Layer ("characters")  
- Character inclusion criteria:  
    - Must include: Major characters, supporting roles with significant dialogue/plot impact, and narrators.  
    - Exclude: Minor roles, background characters with minimal influence.  
- Format:  
```json  
character_json_format = {  
    "basic_info": {
        "name": "string",          // Prefer in-script names; otherwise, use descriptors (e.g., "Detective," "Angry Man").  
        "age": "N/A"|approximate age,       // Infer or label "N/A".  
        "gender": "Male"|"Female"|"Unknown",  
        "identity": "string",      // E.g., "Retired detective/High school student/AI assistant."  
        "characteristic": "string", // At least 1 adjective (e.g., "cautious").  
        "description": {  # summary of "age", "gender", "identity", and "characteristic", excluding "plot_related_info"
            "en": "string",  # Neutral 1-2 sentence summary in English, combine key attributes naturally ("A righteous Wudang warrior" instead of "He is a...")
            "zh": "string"   # 中文版角色人设总结 (采用「身份+特征」的简洁结构 (例：正义的武当侠士)，避免"该角色是"等冗余表达)
        }
    },
    "plot_related_info": {
        "motivations": "string",   // Internal drivers for actions.  
        "relationships": {        // Only list confirmed relationships.  
            "[Character Name]": "Parent-child/Rivals/Colleagues/Lovers..."  
        }
    }
}  
```  

3. Scene Segmentation Layer ("scenes")  
- Segmentation rules:  
    - Continuity: Adjacent scenes must have consecutive line numbers (end + 1 = next start).  
    - Exclusivity: Each line belongs to only one scene.  
    - Transition triggers: Location changes, time jumps, character entrances/exits, plot twists, etc.  
- Scene description requirements:  
- "characters": characters in the scene
    - Firstly, match the characters defined in "Character Analysis Layer".  
    - If there's no appropriate character in "Character Analysis Layer", name he/she by traits/identities (e.g., "Market Vendor").  
    - If undefined roles lack clear traits, use generic labels (e.g., "Passerby A").  
- "description": Concisely summarize the time, location, core action and outcome (if any).  


Output in JSON Format:
```json  
{  
    "story": {  
        "background": "string",  
        "plot": "string"  
    },  
    "characters": [character_json_format, ...],  
    "scenes": [  
        {  
            "scene": {
                "characters": ["name1", ...],  
                "description": {
                    "en": "string",  # Neutral 1-2 sentence summary of scene time, location and event in English, excluding start or end LINE_NUM
                    "zh": "string"   # 中文版场景描述（1-2句话），包括时间、地点和事件，不要包含start和end LINE_NUM
                }
            },  
            "start": int,  // Must be ≥0.  
            "end": int,    // Must be ≥start. 
            "confidence": { // [0,1]
                "character_assignment": float,
                "scene_segmentation": float,
                "event_accuracy": float
            }, 
        },
        ...
    ],  
    "coverage_check": bool  // Whether all lines are covered.  
}  
```  
'''