import streamlit as st
from agent.core import AgentCore

st.set_page_config(
    page_title="申鹤 — 孤辰孑遗",
    page_icon="❄️",
    layout="wide",
)


@st.cache_resource
def get_agent() -> AgentCore:
    return AgentCore()


def render_sidebar(agent: AgentCore):
    """侧边栏：情绪指示器 + 记忆 + 对话管理。"""
    with st.sidebar:
        st.title("❄️ 申鹤")

        # ── 情绪状态 ──
        st.subheader("🔮 心境")
        emotions = agent.get_emotions()
        mood = agent.get_mood()

        mood_display = {
            "detached": "🪨 淡漠",
            "bloodlust": "⚔️ 杀性涌动",
            "softened": "🫧 冰霜消融",
            "melancholy": "🌫️ 沉郁",
        }
        st.caption(f"当前：{mood_display.get(mood, '🪨 淡漠')}")

        labels = {
            "warmth": "🔥 温度",
            "sorrow": "💧 悲意",
            "curiosity": "❓ 疑惑",
            "calmness": "🪢 红绳压制",
            "bloodlust": "⚔️ 杀性",
            "attachment": "💫 依恋",
        }
        for name, value in emotions.items():
            st.progress(value, text=f"{labels.get(name, name)} {value:.2f}")

        st.divider()

        # ── 已知信息 ──
        st.subheader("📜 对你的了解")
        facts = agent.get_facts(limit=8)
        if facts:
            for f in facts:
                st.caption(f"• {f['content']}")
        else:
            st.caption("（尚未了解你）")

        st.divider()

        # ── 对话管理 ──
        st.subheader("💬 对话")
        if st.button("🆕 新的相遇", use_container_width=True):
            agent.new_conversation()
            st.session_state.messages = []
            st.rerun()

        conversations = agent.get_conversations()
        if len(conversations) > 1:
            st.caption("过往对话：")
            for conv in conversations:
                is_current = conv["id"] == agent.conversation_id
                label = f"{'❄️' if is_current else '  '} {conv['title'][:20]}"
                if not is_current and st.button(label, key=conv["id"], use_container_width=True):
                    agent.switch_conversation(conv["id"])
                    st.session_state.messages = []
                    st.rerun()


def main():
    agent = get_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    render_sidebar(agent)

    # ── 主聊天区域 ──
    st.title("❄️ 申鹤 · 孤辰孑遗")
    st.caption("「我名申鹤，命格孤煞，易伤身边人。若不畏惧与我同行……就请伸出手来吧。」")

    # 显示历史消息
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "❄️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image"):
                st.image(msg["image"])
            if msg.get("audio"):
                st.audio(msg["audio"])

    # 输入框
    if prompt := st.chat_input("和申鹤说话……"):
        st.session_state.messages.append({"role": "user", "content": prompt, "image": None, "audio": None})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="❄️"):
            with st.spinner("申鹤正在凝神……"):
                response = agent.process_message(prompt)
            st.markdown(response["text"])
            if response.get("image_path"):
                st.image(response["image_path"])
            if response.get("audio_path"):
                st.audio(response["audio_path"])

        st.session_state.messages.append({
            "role": "assistant",
            "content": response["text"],
            "image": response.get("image_path"),
            "audio": response.get("audio_path"),
        })
        st.rerun()


if __name__ == "__main__":
    main()
