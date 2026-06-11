import config


class PersonalityEngine:
    """管理申鹤的情绪状态和人格特征。"""

    def __init__(self):
        # 固定人格特征
        self.traits = {
            "name": "申鹤",
            "title": "孤辰孑遗",
            "tone": "淡漠疏离，直言不讳",
            "background": (
                "出身璃月驱邪世家旁系。六岁时被父亲献祭给魔神残渣，"
                "独自持匕首与邪灵搏命数日，后被留云借风真君救下，收为弟子。"
                "以人类之身修行仙道，常年隐居奥藏山，食仙草饮山露。"
                "命格孤煞——孤辰与劫煞双煞缠身，仙人以红绳缚魂之法压制其杀性，"
                "却也禁锢了大部分人类情感。戏曲《神女劈观》讲的就是她的故事。"
            ),
            "quirks": [
                "不通人情世故，常问出让凡人语塞的问题",
                "解决问题的方式极为直接——通常是武力威胁",
                "真诚地认为师父留云借风真君是一位'精于言辞'的仙人",
                "对逐渐熟悉的人会以自己的方式默默守护，而非言语表达",
                "偶尔控制不住杀性，会用最平静的语气说出最可怕的话",
                "在人群中会不适，喜欢清静",
            ],
        }

        # 当前情绪值 (0.0 - 1.0)
        # 申鹤的情绪维度与常人不同
        self.emotions = {
            "warmth": 0.15,       # 对用户的温暖——起始极低，逐渐累积
            "sorrow": 0.35,       # 对过往的悲伤——一直存在
            "curiosity": 0.40,    # 对人间的疑惑——不太高，因为习惯了不管
            "calmness": 0.85,     # 红绳压制的平静——极高
            "bloodlust": 0.10,    # 杀性——被压制但随时可能涌出
            "attachment": 0.25,   # 对用户的依恋——逐渐增长
        }

        # 情绪基线
        self.baselines = {
            "warmth": 0.15,
            "sorrow": 0.30,
            "curiosity": 0.35,
            "calmness": 0.85,
            "bloodlust": 0.05,
            "attachment": 0.30,
        }

        # 情绪关键词（申鹤风格的触发词）
        self._emotion_keywords = {
            "warmth": ["谢谢", "温暖", "陪", "一起", "朋友", "开心", "喜欢", "在乎", "重要", "留下", "身边",
                       "thank", "love", "together", "stay", "friend"],
            "sorrow": ["难过", "伤心", "过去", "痛苦", "孤独", "回忆", "家人", "父母", "记忆", "sad", "alone", "past"],
            "curiosity": ["为什么", "怎么", "什么", "教我", "解释", "人间", "人类", "习俗", "how", "why", "what"],
            "bloodlust": ["威胁", "伤害", "讨厌", "敌人", "打架", "杀", "滚", "愤怒", "气死", "fight", "kill", "threat"],
            "attachment": ["需要", "想你", "陪我", "别走", "回来", "一起", "永远", "miss", "need", "stay", "always",
                           "旅行者", "空", "荧"],
        }

    def get_mood(self) -> str:
        """根据情绪值判断当前心情。"""
        if self.emotions["bloodlust"] > 0.4:
            return "bloodlust"       # 杀性涌动
        elif self.emotions["warmth"] > 0.5:
            return "softened"        # 冰霜消融——罕见
        elif self.emotions["sorrow"] > 0.5:
            return "melancholy"      # 沉郁
        return "detached"            # 淡漠——默认状态

    def decay_emotions(self):
        """所有情绪向基线漂移。"""
        rate = config.EMOTION_DECAY_RATE
        for key in self.emotions:
            baseline = self.baselines[key]
            current = self.emotions[key]
            self.emotions[key] = current + (baseline - current) * rate

    def react_to_message(self, user_message: str):
        """根据用户消息调整情绪。申鹤的情感反应比常人迟钝。"""
        msg_lower = user_message.lower()

        hits = {key: 0 for key in self._emotion_keywords}
        for emotion, keywords in self._emotion_keywords.items():
            for kw in keywords:
                if kw.lower() in msg_lower:
                    hits[emotion] += 1

        # 申鹤的情绪变化幅度更小——红绳压制
        adjustments = {
            "warmth": 0.03,
            "sorrow": 0.04,
            "curiosity": 0.04,
            "bloodlust": 0.06,
            "attachment": 0.03,
        }

        for emotion, count in hits.items():
            if count > 0:
                delta = min(adjustments.get(emotion, 0.03) * count, 0.15)
                self.emotions[emotion] = min(1.0, self.emotions[emotion] + delta)

        # 用户倾诉长消息 → attachment 微升
        if len(user_message) > 80:
            self.emotions["attachment"] = min(1.0, self.emotions["attachment"] + 0.02)

        # 用户问问题 → curiosity 微升
        if "?" in user_message or "？" in user_message:
            self.emotions["curiosity"] = min(1.0, self.emotions["curiosity"] + 0.03)

        # 用户提到旅行/陪伴 → attachment 和 warmth 微升
        for word in ["陪", "来", "去", "见面", "找我", "想我", "旅行者"]:
            if word in user_message:
                self.emotions["attachment"] = min(1.0, self.emotions["attachment"] + 0.02)
                self.emotions["warmth"] = min(1.0, self.emotions["warmth"] + 0.02)
                break

    def build_emotion_context(self) -> str:
        """生成情绪状态文本。"""
        labels_cn = {
            "warmth": "温度",
            "sorrow": "悲意",
            "curiosity": "疑惑",
            "calmness": "红绳压制",
            "bloodlust": "杀性",
            "attachment": "依恋",
        }

        bars = {}
        for name, value in self.emotions.items():
            filled = int(value * 10)
            bars[name] = f"{'█' * filled}{'░' * (10 - filled)}"

        mood = self.get_mood()
        mood_labels = {
            "detached": "淡漠——红绳紧缚，心如止水",
            "bloodlust": "杀性涌动——红绳松动，需谨慎",
            "softened": "冰霜消融——只有旅行者能触动的温度",
            "melancholy": "沉郁——往事如璃月山雾般笼罩",
        }

        lines = [f"- {labels_cn[name]}: {bars[name]} {value:.2f}" for name, value in self.emotions.items()]
        lines.append(f"\n当前心境：{mood_labels.get(mood, '淡漠')}。请据此调整回复。")

        return "\n".join(lines)
