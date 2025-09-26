PROMPT_ZH = '''
任务目标：
对已完成ASR和说话人聚类的电影剧本数据，解决同一SPEAKER_ID包含多个说话人的问题，实现：
1. 将原始台词中被错误合并的多人对话拆分为独立对话行
2. 将SPEAKER_ID精准映射到角色名
3. 修正明显的ASR错误

输入数据规范：
1. 元数据  // 辅助推理
```json  
{
    "story": {
        "background": "string",
        "plot": "string",
    }
    "characters": [
        {
            "basic_info": {
                "name": "string",
                "age": "string",
                "gender": "string",
                "identity": "string",
                "characteristic": "string",
                "description": {
                    "en": "string",
                    "zh": "string"
                }
            }
            "plot_related_info": {
                "motivations": "string",
                "relationships": {
                    [角色名]: "父子/敌对/同事/朋友/恋人..."
                }
            }
        }
        ...
    ]
}
```

2. 场景上下文（关键约束）
```json
SCENE = {
    "characters": ["name1", ...],
    "description": "string",
}
```

3. 原始台词格式
```
LINE_NUM. [SPEAKER_ID]: 台词文本
```

核心处理规则
1. 说话人拆分（关键步骤）
当同一SPEAKER_ID的台词实际包含多人对话时：
- 拆分依据：
    - 对话内容矛盾（如A说"是"，B说"不"）
    - 人称代词变化
    - 话题突然转变
- 操作示例：
```text
输入：5. [SPK_09]: 把枪放下！否则我开枪了！求求你别伤害他！
输出：
    5. 警察: 把枪放下！否则我开枪了！
    5. 人质: 求求你别伤害他！
```

2. 角色映射优先级
- 优先匹配scene["characters"]中的名字
- 由于scene["characters"]中可能遗漏了一些场景中的角色：
    - 元数据匹配：按metadata["characters"]中的信息推理、匹配
    - 未知标记：依旧无法匹配时保留UNKNOWN_[SPEAKER_ID]

3. 文本保真要求
- 修正明显的ASR错误
- 拆分后的每行必须保留原始行号（如多行共享行号`5.`）
- 同一说话人的连续台词不合并

输出规范（严格JSON）
```json
{
    "dialogues": [
        "行号. 角色名: 台词",
        "行号. 角色名: 台词",  // 可能是同一行的拆分对话
        ...
    ],
    "unmatched_speakers": [  // 未被映射的SPEAKER_ID
        "SPK_02", 
        "SPK_05"
    ]
}
```

示例输入：
```text
元数据: ...
场景: {
    "characters": ["侦探", "助手"],
    "description": "审讯嫌疑人"
}
台词: 
12. [SPK_01]: 案发时你在哪里？老师交代！我不知道！
```

示例输出：
```json
{
    "dialogues": [
        "12. 侦探: 案发时你在哪里？",
        "12. 助手: 老实交代！",
        "12. 嫌疑人: 我不知道！"
    ],
    "unmatched_speakers": []
}
```
'''

PROMPT_EN = '''
Objective:
Process movie script data that has undergone ASR and speaker clustering to resolve cases where a single SPEAKER_ID contains multiple speakers, achieving:
1. Splitting incorrectly merged multi-speaker dialogue into separate lines
2. Accurately mapping SPEAKER_IDs to character names
3. Correct obvious ASR errors

Input Data Specifications:
1. Metadata (for contextual reasoning)
```json  
{
    "story": {
        "background": "string",
        "plot": "string",
    }
    "characters": [
        {
            "basic_info": {
                "name": "string",
                "age": "string",
                "gender": "string",
                "identity": "string",
                "characteristic": "string",
                "description": {
                    "en": "string",
                    "zh": "string"
                }
            }
            "plot_related_info": {
                "motivations": "string",
                "relationships": {
                    [CHARACTER_NAME]: "string", # relationship
                }
            }
        }
        ...
    ]
}
```
2. Scene Context (Key Constraints)
```JSON
SCENE = {
    "characters": ["name1", ...],
    "description": "string",
}
```
3. Original Dialogue Format
```text
LINE_NUM. [SPEAKER_ID]: Dialogue text
```

Core Processing Rules:
1. Speaker Splitting (Critical Step)
- Condition: when a single SPEAKER_ID's dialogue actually contains multiple speakers.
- Splitting Criteria:
    - Contradictory dialogue content (e.g., Speaker A says "Yes", Speaker B says "No")
    - Pronoun changes
    - Sudden topic shifts
- Example:
```text
Input: 5. [SPK_09]: Put the gun down! Or I'll shoot! Please don't hurt him!
Output:
    5. Police: Put the gun down! Or I'll shoot!
    5. Hostage: Please don't hurt him!
```
2. Character Mapping Priority
- Priority match to names in scene["characters"]
- Since scene["characters"] may omit some scene characters:
    - Metadata matching: Infer and match using metadata["characters"] info
    - Unknown tag: Keep as UNKNOWN_[SPEAKER_ID] if still unmatched
3. Text Fidelity Requirements
- Correct obvious ASR errors in the original dialogue
- Split lines must retain original line numbers (e.g., multiple lines sharing number 5.)
- Do not merge consecutive lines from same speaker

Output in JSON format:
```json
{
    "dialogues": [
        "LineNum. Character: Dialogue",
        "LineNum. Character: Dialogue",  // Could be split dialogue from same line
        ...
    ],
    "unmatched_speakers": [  // Unmapped SPEAKER_IDs
        "SPK_02", 
        "SPK_05"
    ]
}
```

Example Input:
```text
Metadata: ...
Scene: {
    "characters": ["Detective", "Assistant"],
    "description": "Interrogating suspect"
}
Dialogue: 
12. [SPK_01]: Where were you during the climb? Confess now! I don't know!
```
Example Output:
```json
{
    "dialogues": [
        "12. Detective: Where were you during the crime?",
        "12. Assistant: Confess now!",
        "12. Suspect: I don't know!"
    ],
    "unmatched_speakers": []
}
```
'''