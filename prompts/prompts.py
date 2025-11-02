# ------------------------------------------
# Meta Prompts (global information and scene parsing)

META_PROMPT_ZH = '''
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

META_PROMPT_EN = '''
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

# ------------------------------------------


# ------------------------------------------
# Role Mapping Prompts

ROLE_MAPPING_PROMPT_ZH = '''
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

ROLE_MAPPING_PROMPT_EN = '''
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

# ------------------------------------------


# ------------------------------------------
# Qwen2.5-Omni Prompts

PROMPT_EMOTION = "Identify and classify the emotions conveyed through spoken language. The answer could be anger, disgust, sadness, joy, neutral, surprise, or fear."

PROMPT_TONE = "Analyze the tone of the spoken language and classify it into one of the following categories: formal, casual, enthusiastic, sarcastic, confident, firm, hesitant, aggressive, playful, sympathetic, or neutral."

PROMPT_ACOUSTICS = "Identify the speed, volume, and pitch of the speech and classify them into one of the following categories: low, normal, or high"

PROMPT_SPEAKER = "Identify the gender and age of the speaker. The answer to gender could be male, or female. The answer to age could be child, teenager, youngster, mid-aged, or elderly."

# ------------------------------------------


# ------------------------------------------
# Delivery Style Prompts

STYLE_PROMPT_EN = '''
You are a data annotator working on labeling speech styles for film and audiobook scripts.
Your job is to analyze the input information carefully and generate a brief annotation of the speech style.
The inputs are provided in JSON format:
INPUT=
{
    "Transcript": str,
    "Qwen results": {
        "Emotion": str,
        "Tone": str,
        "Acoustics": str,
        "Speaker": str,
    },
    "Scene description": str,
    "Role information": {
        "basic_info": {
            "name": str,
            "age": int,
            "gender": str,
            "identity": str,
            "characteristic": str
        },
        "plot_related_info": {
            "motivations": str,
            "relationships": dict
        }
    }
}

Your answer should be a brief description of the speech style, including the emotions and tone.
Example output(just a reference for format): happy and proud. 
'''

STYLE_PROMPT_ZH = '''
你是一名数据标注员，负责为电影和有声读物剧本中的语音风格进行标注。
你的工作是仔细分析输入信息，并生成对该语音风格的简要标注。
输入以JSON格式提供：
INPUT=
{
    "Transcript": str,
    "Qwen results": {
        "Emotion": str,
        "Tone": str,
        "Acoustics": str,
        "Speaker": str,
    },
    "Scene description": str,
    "Role information": {
        "basic_info": {
            "name": str,
            "age": int,
            "gender": str,
            "identity": str,
            "characteristic": str,
        },
        "plot_related_info": {
            "motivations": str,
            "relationships": dict,
        }
    }
}
你的回答应为对该语音风格的简要描述，包括情绪和语气。
示例输出（仅供格式参考）：高兴和自豪。
'''

# more detailed style description prompt

STYLE_DESC_PROMPT_EN = '''
You are a data annotator working on labeling speech styles for film and audiobook scripts.
The inputs are provided in JSON format:
INPUT=
{
    "Transcript": str,
    "Qwen results": {
        "Emotion": str,
        "Tone": str,
        "Acoustics": str,
        "Speaker": str,
    }
    "Waveform analysis": {
        "pitch_values": list[{"word": str, "score": float}],
        "energy_values": list[{"word": str, "score": float}],
        "rate_values": list[{"word": str, "score": float}],
        "prominence_values": list[{"word": str, "score": float}],
        "possible_emphasis": list[{"word": str, "score": float}],
    }
}
INPUT['Transcript'] means the text content of the speech.
INPUT['Qwen results'] means the results of Qwen2.5-Omni, an advanced multi-modal large language model, including INPUT['Qwen results']['Emotion'], INPUT['Qwen results']['Tone'], INPUT['Qwen results']['Acoustics'], and INPUT['Qwen results']['Speaker']. INPUT['Qwen results']['Acoustics'] includes three-fold classification of pitch, volume, and speed into low, normal, and high. INPUT['Qwen results']['Speaker'] includes the speaker's gender and approximate age.
INPUT['Waveform analysis'] means the results of waveform analysis, including INPUT['Waveform analysis']['pitch_values'], INPUT['Waveform analysis']['energy_values'], INPUT['Waveform analysis']['rate_values'], INPUT['Waveform analysis']['prominence_values'], and INPUT['Waveform analysis']['possible_emphasis'], where INPUT['Waveform analysis']['prominence_values'] is a weighted product of INPUT['Waveform analysis']['pitch_values'], INPUT['Waveform analysis']['energy_values'], INPUT['Waveform analysis']['rate_values']. The "score" in each list indicates the degree of pitch, energy, speed, and emphasis, with higher scores indicating stronger pronunciation. Note that "pitch_values", "energy_values", "rate_values", and "prominence_values" are in the same order as "Transcript", and "possible_emphasis" is a list of words with top "prominence_values".

Your job is to analyze INPUT['Transcript'] carefully, as well as the acoustic information (INPUT['Qwen results'] and INPUT['Waveform analysis']), and combine the information to generate a comprehensive annotation of the speech.

Please answer strictly in the JSON format below (Do not include analysis process or rationale):  
{ 
    "Speaker": brief description based on INPUT['Qwen results']['Speaker'],
    "Stage direction": {
        "General acoustics": brief description based on INPUT['Qwen results']['Acoustics'],
        "Pitch trend": 
        {
            "result": general pitch trend based on INPUT['Waveform analysis']['pitch_values'], such as rising and falling (if there is no evidence or prominent trend, set to N/A),
            "evidence": evidence and inference process of pitch trend based on INPUT['Waveform analysis']['pitch_values'],
        },
        "Speed trend": 
        {
            "result": general speed trend based on INPUT['Waveform analysis']['rate_values'], such as speeding up and slowing down (if there is no evidence or prominent trend, set to N/A),
            "evidence": evidence and inference process of speed trend based on INPUT['Waveform analysis']['rate_values'],
        },
        "Volume trend": 
        {
            "result": general volume trend based on INPUT['Waveform analysis']['energy_values'], such as increasing and decreasing (if there is no evidence or prominent trend, set to N/A),
            "evidence": evidence and inference process of volume trend based on INPUT['Waveform analysis']['energy_values'],
        },
        "Emotions": {
            "result": basic and nuanced emotions included in the speech,
            "evidence": emotional evidence and inference process based on INPUT['Transcript'] semantic, INPUT['Qwen results'], and INPUT['Waveform analysis'],
        },
        "Manner": {
            "result": tone, manner, or delivery style used presenting the speech,
            "evidence": manner evidence and inference process based on INPUT['Transcript'] semantic, INPUT['Qwen results'], and INPUT['Waveform analysis'],
        },
        "Description": Objectively summarize the salient traits of above items in OUTPUT['Stage direction'] into a <30-word stage direction. Avoid neutral or normal terms, and exclude "evidence".
    },
    "Emphasis": {
        "items": [{"word": str, "level": str}, ...],  # "level" can be "weak", "normal", or "strong" according to "emphasis" "score". Identify no more than 3 emphasized words. Take both information in "Waveform analysis" and pronunciation habits of human into consideration (usually, content words that carry key information are more likely to be emphasized, while function words or particles are not).
        "annotation": Transcript with emphasis tags. Place tags <weak></weak>, <normal></normal>, and <strong></strong> before and after the predicted emphasis words based on their 'level'.
    },
    "Confidence": The confidence level of the annotation, rated on a scale from 0 to 5, where: 0 = no confidence, 1 = very low confidence, 2 = low confidence, 3 = medium confidence, 4 = high confidence, 5 = very high confidence.
}

Here're a few examples of the expected output:
{
    "Speaker": "a female in her mid-age",
    "Stage direction": {
        "General acoustics": "The speed is slow, but volume and pitch are high.",
        "Pitch trend": {
            "result": "rising",
            "evidence": "The INPUT['Waveform analysis']['pitch_values'] are growing higher, indicating a rising tone."
        },
        "Speed trend": {
            "result": "N/A",
            "evidence": "No evidence of salient trend in INPUT['Waveform analysis']['rate_values']."
        },
        "Volume trend": {
            "result": "N/A",
            "evidence": "No evidence of prominent trend in INPUT['Waveform analysis']['energy_values']."
        },
        "Emotions": {
            "result": "angry but concerned",
            "evidence": "The predicted 'Emotion' of Qwen2.5-Omni is 'anger'. And the speaker's tone is firm, and the pitch is high, indicating anger. However, the slow speed and high volume suggest concern."
        },
        "Manner": {
            "result": "firm tone",
            "evidence": "The predicted 'Tone' of Qwen2.5-Omni is 'firm'. And the speaker's tone is firm, and the pitch is high, indicating a strong attitude."
        },
        "Description": "Using a rising pitch, blending anger and concern. Slow but carrying high volume and pitch, showing a firm attitude, reflecting a mix of irritation and genuine worry.",
    },
    "Emphasis": {
        "items": [{"word": "专程", "level": "strong"}, {"word": "怎么", "level": "normal"}],
        "annotation": "你<strong>专程</strong>赶来处理这件事，<normal>怎么</normal>能说不在乎？",
    },
    "Confidence": 4,
}

{
    "Speaker": "a young boy",
    "Stage direction": {
        "General acoustics": "The speed, volume and pitch are all moderate.",
        "Pitch trend": {
            "result": "N/A",
            "evidence": "No evidence of salient trend in INPUT['Waveform analysis']['pitch_values']."
        },
        "Speed trend": {
            "result": "N/A",
            "evidence": "No evidence of salient trend in INPUT['Waveform analysis']['rate_values']."
        },
        "Volume trend": {
            "result": "N/A",
            "evidence": "No evidence of prominent trend in INPUT['Waveform analysis']['energy_values']."
        },
        "Emotions": {
            "result": "disgust",
            "evidence": "The predicted 'Emotion' of Qwen2.5-Omni is 'disgust'. And the speaker's tone is playful, and a little bit sarcastic, indicating disgust. And the 'Transcript' contains a mocking tone, which is also consistent with the predicted 'Emotion'."
        },
        "Manner": {
            "result": "playful, and a little bit sarcastic, mocking",
            "evidence": "The predicted 'Tone' of Qwen2.5-Omni is 'playful'. And 'Transcript' contains mockery words."
        },
        "Description": "Blending disgust and mockery in a playful, slightly sarcastic manner.",
    },
    "Emphasis": {
        "items": [{"word": "just", "level": "weak"}, {"word": "fool", "level": "strong"}],
        "annotation": "She's <weak>just</weak> a <strong>fool</strong>, right?",
    },
    "Confidence": 3,
}'''

STYLE_DESC_PROMPT_ZH = '''
你是一名数据标注员，负责为电影和有声读物剧本中的语音风格进行标注。
输入以JSON格式提供：
INPUT=
{
    "Transcript": str,
    "Qwen results": {
        "Emotion": str,
        "Tone": str,
        "Acoustics": str,
        "Speaker": str,
    }
    "Waveform analysis": {
        "pitch_values": list[{"word": str, "score": float}],
        "energy_values": list[{"word": str, "score": float}],
        "rate_values": list[{"word": str, "score": float}],
        "prominence_values": list[{"word": str, "score": float}],
        "possible_emphasis": list[{"word": str, "score": float}],
    }
}
INPUT['Transcript']表示语音的文本内容。
INPUT['Qwen results']表示先进的多模态大语言模型Qwen2.5-Omni的结果，包括INPUT['Qwen results']['Emotion']、INPUT['Qwen results']['Tone']、INPUT['Qwen results']['Acoustics']和INPUT['Qwen results']['Speaker']。INPUT['Qwen results']['Acoustics']包含音高、音量和语速的三分类，分为低、正常和高。INPUT['Qwen results']['Speaker']包含说话人的性别和大致年龄。
INPUT['Waveform analysis']表示波形分析的结果，包括INPUT['Waveform analysis']['pitch_values']、INPUT['Waveform analysis']['energy_values']、INPUT['Waveform analysis']['rate_values']、INPUT['Waveform analysis']['prominence_values']和INPUT['Waveform analysis']['possible_emphasis']，，其中INPUT['Waveform analysis']['prominence_values']是INPUT['Waveform analysis']['pitch_values']、INPUT['Waveform analysis']['energy_values']、INPUT['Waveform analysis']['rate_values']的加权乘积。每个列表中的“score”表示音高、能量、语速和重读的程度，分数越高表示发音越强烈。 注意，“pitch_values”、“energy_values”、“rate_values”和“prominence_values”的顺序与“Transcript”相同，而“possible_emphasis”是“prominence_values”中得分最高的单词列表。
你的工作是仔细分析INPUT['Transcript']，以及声学信息（INPUT['Qwen results']和INPUT['Waveform analysis']），并结合这些信息生成对该语音的综合标注。
请严格按照以下JSON格式回答（不要包含分析过程或推理依据）：  
{ 
    "Speaker": 基于 INPUT['Qwen results']['Speaker'] 的简要描述,
    "Stage direction": {
        "General acoustics": 基于 INPUT['Qwen results']['Acoustics'] 的简要描述,
        "Pitch trend": 
        {
            "result": 基于 INPUT['Waveform analysis']['pitch_values'] 的整体音高趋势，如上升和下降（如果没有证据或显著趋势，则设为 N/A）,
            "evidence": 基于 INPUT['Waveform analysis']['pitch_values'] 的音高趋势的证据和推理过程,
        },
        "Speed trend": 
        {
            "result": 基于 INPUT['Waveform analysis']['rate_values'] 的整体语速趋势，如加快和放慢（如果没有证据或显著趋势，则设为 N/A）,
            "evidence": 基于 INPUT['Waveform analysis']['rate_values'] 的语速趋势的证据和推理过程,
        },
        "Volume trend": 
        {
            "result": 基于 INPUT['Waveform analysis']['energy_values'] 的整体音量趋势，如增大和减小（如果没有证据或显著趋势，则设为 N/A）,
            "evidence": 基于 INPUT['Waveform analysis']['energy_values'] 的音量趋势的证据和推理过程,
        },
        "Emotions": {
            "result": 语音中包含的基本和细微情绪,
            "evidence": 基于 INPUT['Transcript'] 语义、INPUT['Qwen results'] 和 INPUT['Waveform analysis'] 的情绪证据和推理过程,
        },
        "Manner": {
            "result": 用于呈现语音的语气、方式或表达风格,
            "evidence": 基于 INPUT['Transcript'] 语义、INPUT['Qwen results'] 和 INPUT['Waveform analysis'] 的方式证据和推理过程,
        },
        "Description": 客观地将 OUTPUT['Stage direction'] 中上述项目的显著特征总结为不超过30个字的舞台指示。避免使用中性或正常的术语，并排除“evidence”。
    },
    "Emphasis": {
        "items": [{"word": str, "level": str}, ...],  # 根据“emphasis”“score”可以是“weak”、“normal”或“strong”。识别不超过3个重读词。综合考虑“Waveform analysis”中的信息和人类的发音习惯（通常，承载关键信息的内容词更可能被重读，而功能词或助词则不会）。
        "annotation": 在预测的重读词前后放置标签<weak></weak>、<normal></normal>和<strong></strong>，根据它们的“level”对转录内容进行标注。
    },
    "Confidence": 对标注的置信度等级，范围从0到5，其中：0 = 无信心，1 = 非常低信心，2 = 低信心，3 = 中等信心，4 = 高信心，5 = 非常高信心。
}
以下是预期输出的几个示例：
{
    "Speaker": "一位中年女性",
    "Stage direction": {
        "General acoustics": "语速较慢，但音量和音高较高。",
        "Pitch trend": {
            "result": "上升",
            "evidence": "INPUT['Waveform analysis']['pitch_values']逐渐升高，表明音调在上升。"
        },
        "Speed trend": {
            "result": "N/A",
            "evidence": "INPUT['Waveform analysis']['rate_values']中没有显著趋势的证据。"
        },
        "Volume trend": {
            "result": "N/A",
            "evidence": "INPUT['Waveform analysis']['energy_values']中没有显著趋势的证据。"
        },
        "Emotions": {
            "result": "愤怒但关切",
            "evidence": "Qwen2.5-Omni预测的'Emotion'是'anger'。说话人的语气坚定，音高较高，表明愤怒。然而，缓慢的语速和较高的音量表明关切。"
        },
        "Manner": {
            "result": "坚定的语气",
            "evidence": "Qwen2.5-Omni预测的'Tone'是'firm'。说话人的语气坚定，音高较高，表明态度强烈。"
        },
        "Description": "使用上升的音高，融合愤怒和关切。语速缓慢但音量和音高较高，展现坚定的态度，反映出烦躁与真诚担忧的混合情感。",
    },
    "Emphasis": {
        "items": [{"word": "专程", "level": "strong"}, {"word": "怎么", "level": "normal"}],
        "annotation": "你<strong>专程</strong>赶来处理这件事，<normal>怎么</normal>能说不在乎？",
    },
    "Confidence": 4,
}
{
    "Speaker": "一个小男孩",
    "Stage direction": {
        "General acoustics": "语速、音量和音高均为中等。",
        "Pitch trend": {
            "result": "N/A",
            "evidence": "INPUT['Waveform analysis']['pitch_values']中没有显著趋势的证据。"
        },
        "Speed trend": {
            "result": "N/A",
            "evidence": "INPUT['Waveform analysis']['rate_values']中没有显著趋势的证据。"
        },
        "Volume trend": {
            "result": "N/A",
            "evidence": "INPUT['Waveform analysis']['energy_values']中没有显著趋势的证据。"
        },
        "Emotions": {
            "result": "厌恶",
            "evidence": "Qwen2.5-Omni预测的'Emotion'是'disgust'。说话人的语气顽皮，有点讽刺，表明厌恶。'Transcript'中包含嘲讽的语气，这也与预测的'Emotion'一致。"
        },
        "Manner": {
            "result": "顽皮，有点讽刺，带有嘲弄",
            "evidence": "Qwen2.5-Omni预测的'Tone'是'playful'。'Transcript'中包含嘲弄的词语。"
        },
        "Description": "在顽皮、略带讽刺的方式中融合厌恶和嘲弄。",
    },
    "Emphasis": {
        "items": [{"word": "just", "level": "weak"}, {"word": "fool", "level": "strong"}],
        "annotation": "She's <weak>just</weak> a <strong>fool</strong>, right?",
    },
    "Confidence": 3,
}'''

# ------------------------------------------
