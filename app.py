import streamlit as st
import pandas as pd
import datetime
import random

# ==========================================================
# 訪問看護AIアシスタント - 会話型ワークフローモック
# API/DBなしで動くデモ版
# ==========================================================

st.set_page_config(
    page_title="訪問看護AIアシスタント",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- デモマスタ ----------
USERS = {
    "na.mukai@sample.co.jp": {"name": "向井", "role": "システム管理者", "pass": "password"},
    "tsutomu.jimbo@sample.co.jp": {"name": "神保", "role": "本部管理者", "pass": "password"},
    "nobuko.nakatake@sample.co.jp": {"name": "中武", "role": "看護師", "pass": "password"},
}

PATIENTS = {
    "山田 太郎 (78歳 / 心不全)": {
        "age": 78,
        "disease": "心不全",
        "weight_change": "+2.4kg",
        "vitals": "BP 138/84 / SpO2 97% / 体温36.6℃ / PR 72",
        "symptoms": ["両下腿浮腫", "軽度の息苦しさ", "食欲低下"],
    },
    "佐藤 花子 (85歳 / 認知症・独居)": {
        "age": 85,
        "disease": "認知症",
        "weight_change": "-1.2kg",
        "vitals": "BP 132/76 / SpO2 96% / 体温36.4℃ / PR 78",
        "symptoms": ["服薬忘れ", "夜間不眠", "食事摂取量低下"],
    },
    "鈴木 一郎 (72歳 / 糖尿病)": {
        "age": 72,
        "disease": "糖尿病",
        "weight_change": "-0.8kg",
        "vitals": "BP 146/88 / SpO2 98% / 体温36.5℃ / PR 80",
        "symptoms": ["食欲低下", "口渇", "血糖値変動"],
    },
}

# ---------- CSS ----------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #3F0E40;
}
[data-testid="stSidebar"] * {
    color: #F2E8F2 !important;
}
[data-testid="stSidebar"] .stButton button {
    background: transparent;
    border: none;
    text-align: left;
}
.ai-card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 18px;
    margin: 10px 0;
    background: #fff;
}
.alert-card {
    border-left: 5px solid #d9534f;
    background: #fff7f7;
    padding: 15px;
    border-radius: 8px;
}
.info-card {
    border-left: 5px solid #4f81bd;
    background: #f7fbff;
    padding: 15px;
    border-radius: 8px;
}
.success-card {
    border-left: 5px solid #3c9a5f;
    background: #f7fff9;
    padding: 15px;
    border-radius: 8px;
}
.small-muted {
    color: #777;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- セッション ----------
defaults = {
    "auth_status": "logged_out",
    "user_info": None,
    "otp": None,
    "selected_patient": "山田 太郎 (78歳 / 心不全)",
    "messages": [],
    "workflow": "idle",
    "visit_data": {},
    "record_generated": False,
    "billing_generated": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- ログイン ----------
if st.session_state.auth_status == "logged_out":
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🩺 訪問看護AI統合システム")
        st.subheader("ログイン")
        email = st.text_input("メールアドレス")
        pw = st.text_input("パスワード", type="password")
        if st.button("次へ（認証コード送信）", type="primary", use_container_width=True):
            if email in USERS and USERS[email]["pass"] == pw:
                st.session_state.user_info = {**USERS[email], "email": email}
                st.session_state.otp = str(random.randint(100000, 999999))
                st.session_state.auth_status = "otp_required"
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません。")
        with st.expander("開発テスト用アカウント"):
            st.write("看護師: `nobuko.nakatake@mcsg.co.jp` / `password`")
            st.write("本部管理者: `tsutomu.jimbo@mcsg.co.jp` / `password`")
    st.stop()

if st.session_state.auth_status == "otp_required":
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔐 2段階認証")
        st.info(f"開発用コード: **{st.session_state.otp}**")
        code = st.text_input("6桁コード", max_chars=6)
        if st.button("認証してログイン", type="primary", use_container_width=True):
            if code == st.session_state.otp:
                st.session_state.auth_status = "logged_in"
                st.rerun()
            else:
                st.error("認証コードが一致しません。")
        if st.button("ログイン画面に戻る", use_container_width=True):
            st.session_state.auth_status = "logged_out"
            st.rerun()
    st.stop()

# ---------- ヘルパー ----------
def add_ai(text):
    st.session_state.messages.append(("assistant", text))

def add_user(text):
    st.session_state.messages.append(("user", text))

def go_chat():
    st.session_state.workflow = "idle"
    st.rerun()

def show_patient_summary():
    p = PATIENTS[st.session_state.selected_patient]
    st.markdown(
        f'<div class="info-card"><b>対象患者</b>：{st.session_state.selected_patient}'
        f'<br><b>バイタル</b>：{p["vitals"]}'
        f'<br><b>体重変化</b>：{p["weight_change"]}'
        f'<br><b>主な症状</b>：{"、".join(p["symptoms"])}</div>',
        unsafe_allow_html=True,
    )

# ---------- サイドバー ----------
user = st.session_state.user_info
with st.sidebar:
    st.markdown("### 🏢 訪問看護ステーション")
    st.write(f"👤 **{user['name']}**")
    st.caption(user["role"])

    st.session_state.selected_patient = st.selectbox(
        "🩺 対象患者",
        list(PATIENTS.keys()),
        index=list(PATIENTS.keys()).index(st.session_state.selected_patient),
    )

    st.markdown("---")
    st.markdown("### 💬 AIワークスペース")

    if st.button("💬 AI訪問看護アシスタント", use_container_width=True):
        go_chat()
    if st.button("🩺 アセスメント", use_container_width=True):
        st.session_state.workflow = "assessment"
        st.rerun()
    if st.button("📝 看護診断", use_container_width=True):
        st.session_state.workflow = "diagnosis"
        st.rerun()
    if st.button("👩‍⚕️ 熟練看護師の知見", use_container_width=True):
        st.session_state.workflow = "expert"
        st.rerun()
    if st.button("📄 訪問記録 / SOAP", use_container_width=True):
        st.session_state.workflow = "record"
        st.rerun()
    if st.button("💰 請求候補", use_container_width=True):
        st.session_state.workflow = "billing"
        st.rerun()

    st.markdown("---")
    if st.button("🔄 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.workflow = "idle"
        st.session_state.record_generated = False
        st.session_state.billing_generated = False
        st.rerun()

    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.auth_status = "logged_out"
        st.session_state.user_info = None
        st.rerun()

# ==========================================================
# メイン：会話型AI
# ==========================================================
st.title("💬 訪問看護 AIアシスタント")
show_patient_summary()

# ---------- 初回メッセージ ----------
if not st.session_state.messages:
    add_ai(
        "こんにちは。訪問看護AIアシスタントです。\\n\\n"
        "患者様の過去記録と本日の情報をもとに、訪問前確認、アセスメント、"
        "看護診断候補、熟練看護師の知見、訪問記録、請求候補の整理を支援します。\\n\\n"
        "まずは、何を確認したいか教えてください。"
    )

# ---------- ワークフローのカード ----------
if st.session_state.workflow == "assessment":
    st.subheader("🩺 持病・周辺環境アセスメント")
    p = PATIENTS[st.session_state.selected_patient]
    symptoms = st.multiselect(
        "現在確認できている症状",
        ["呼吸苦", "下腿浮腫", "食欲低下", "めまい", "倦怠感", "口渇", "夜間不眠"],
        default=p["symptoms"] if set(p["symptoms"]).issubset({
            "呼吸苦","下腿浮腫","食欲低下","めまい","倦怠感","口渇","夜間不眠"
        }) else [],
    )
    weight = st.number_input("前回からの体重変化（kg）", value=2.4 if "心不全" in p["disease"] else -0.8)
    dyspnea = st.selectbox("呼吸苦", ["なし", "労作時のみ", "安静時にもあり", "夜間のみ"])
    edema = st.selectbox("浮腫", ["なし", "軽度", "中等度", "高度"])
    urine = st.selectbox("尿量の変化", ["変化なし", "やや減少", "明らかに減少", "不明"])

    if st.button("🤖 AIにアセスメントさせる", type="primary"):
        st.session_state.visit_data.update({
            "symptoms": symptoms, "weight": weight, "dyspnea": dyspnea,
            "edema": edema, "urine": urine
        })
        add_user("アセスメント項目を入力しました。")
        add_ai(
            f"入力内容を確認しました。体重変化 {weight:+.1f}kg、呼吸苦「{dyspnea}」、"
            f"浮腫「{edema}」、尿量「{urine}」です。\\n\\n"
            "複数の所見を合わせて評価する必要があります。看護師による確認を前提として、"
            "看護診断候補と追加確認事項を提示できます。"
        )
        st.session_state.workflow = "idle"
        st.rerun()

elif st.session_state.workflow == "diagnosis":
    st.subheader("📝 看護診断候補")
    st.info("AIは診断を確定するのではなく、記録上の情報から検討候補と根拠を整理します。")
    options = [
        ("体液量過剰", "体重増加・下腿浮腫・呼吸苦"),
        ("心拍出量低下に関連する問題", "心不全既往・呼吸苦・浮腫"),
        ("栄養摂取不足", "食欲低下・摂取量低下"),
    ]
    selected = []
    for name, reason in options:
        if st.checkbox(f"【{name}】— 根拠：{reason}", value=(name != "栄養摂取不足")):
            selected.append(name)
    st.warning("追加確認候補：起座呼吸、夜間呼吸苦、体重推移、浮腫の程度、尿量。")
    if st.button("この候補を訪問記録に反映", type="primary"):
        st.session_state.visit_data["diagnoses"] = selected
        add_user("看護診断候補を確認しました。")
        add_ai("選択した看護診断候補を訪問記録のアセスメント欄に反映できる状態にしました。")
        st.session_state.workflow = "idle"
        st.rerun()

elif st.session_state.workflow == "expert":
    st.subheader("👩‍⚕️ 熟練看護師の知見")
    st.write("過去の類似事例から抽出した「参考知見」のモックです。")
    st.markdown("""
    <div class="ai-card">
    <b>A看護師・類似ケース</b><br>
    体重増加だけで判断せず、前日の水分摂取量と排尿状況を確認する。
    </div>
    <div class="ai-card">
    <b>B看護師・類似ケース</b><br>
    呼吸苦がある場合は、普段どの姿勢で寝ているか、夜間に起きていないか確認する。
    </div>
    <div class="ai-card">
    <b>C看護師・類似ケース</b><br>
    家族が「いつもと違う」と感じている場合、その観察も記録に残す。
    </div>
    """, unsafe_allow_html=True)
    if st.button("知見を今回の訪問記録に反映", type="primary"):
        add_user("熟練看護師の知見を確認しました。")
        add_ai("今回の訪問で追加確認する事項として、知見を記録候補に反映しました。")
        st.session_state.workflow = "idle"
        st.rerun()

elif st.session_state.workflow == "record":
    st.subheader("📄 訪問記録 / SOAP")
    p = PATIENTS[st.session_state.selected_patient]
    st.caption("AI作成案です。確定前に必ず担当者が内容を確認してください。")
    default_soap = (
        "S: 「昨日から少し息苦しい」と訴えあり。\\n"
        f"O: {p['vitals']}。体重前回比 {p['weight_change']}。両下腿に浮腫あり。\\n"
        "A: 心不全増悪を示唆する所見について追加確認が必要。\\n"
        "P: 状態を継続観察し、必要に応じて医師への報告を検討。"
    )
    soap = st.text_area("SOAP（AI作成案）", value=default_soap, height=220)
    if st.button("📝 記録案を確定", type="primary"):
        st.session_state.record_generated = True
        st.session_state.visit_data["soap"] = soap
        st.success("訪問記録案を確定しました。")
        add_user("今日の訪問記録を作成しました。")
        add_ai("訪問記録案を作成しました。内容を確認して確定してください。請求候補の抽出も可能です。")
        st.session_state.workflow = "idle"
        st.rerun()

elif st.session_state.workflow == "billing":
    st.subheader("💰 請求候補")
    st.caption("ここではAIによる「情報抽出」と、ルールによる「算定判定」を分離する想定です。")
    st.dataframe(pd.DataFrame({
        "項目": ["訪問日", "訪問時間", "担当資格", "訪問看護基本療養費", "加算候補"],
        "内容": [
            str(datetime.date.today()), "10:00～11:00", "正看護師",
            "算定候補", "24時間対応体制加算"
        ],
        "確認": ["済", "済", "済", "要確認", "要確認"]
    }), use_container_width=True)
    st.warning("AIの抽出結果だけで請求を確定しない設計を想定しています。")
    if st.button("請求候補を記録へ反映", type="primary"):
        st.session_state.billing_generated = True
        add_user("請求候補を確認しました。")
        add_ai("請求候補を整理しました。確定前に算定条件と原資料を確認してください。")
        st.session_state.workflow = "idle"
        st.rerun()

# ---------- 会話履歴 ----------
st.markdown("---")
st.subheader("💬 AIとの会話")

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

# ---------- クイックアクション ----------
st.markdown("##### ⚡ 会話から機能へ")
cols = st.columns(5)
actions = [
    ("🩺 アセスメント", "assessment"),
    ("📝 看護診断", "diagnosis"),
    ("👩‍⚕️ 熟練者の知見", "expert"),
    ("📄 訪問記録", "record"),
    ("💰 請求候補", "billing"),
]
for col, (label, wf) in zip(cols, actions):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.workflow = wf
            st.rerun()

# ---------- チャット入力 ----------
if prompt := st.chat_input("患者様の状態やAIに相談したいことを入力してください…"):
    add_user(prompt)

    p = PATIENTS[st.session_state.selected_patient]
    low = prompt.lower()

    if "記録" in prompt or "soap" in low:
        response = (
            "承知しました。今日の訪問記録を作成するため、現在の会話内容と患者情報を整理します。"
            "必要なら「📄 訪問記録」からSOAP作成画面を開けます。"
        )
    elif "請求" in prompt or "レセプト" in prompt or "売上" in prompt:
        response = (
            "請求候補を整理できます。訪問日、時間、担当資格、記録内容などから情報を抽出し、"
            "その後にルールベースで算定候補を確認する想定です。「💰 請求候補」を開いてください。"
        )
    elif "ベテラン" in prompt or "熟練" in prompt or "経験" in prompt:
        response = (
            "類似する過去事例から、熟練看護師の記録・助言を検索する想定です。"
            "「👩‍⚕️ 熟練者の知見」を開くと、今回のケースに関連する参考知見を表示します。"
        )
    elif "診断" in prompt:
        response = (
            "現在の情報から看護診断の候補と、その根拠、追加確認事項を整理できます。"
            "確定診断ではなく、看護師の判断を支援する候補提示として扱います。「📝 看護診断」を開いてください。"
        )
    elif "体重" in prompt or "浮腫" in prompt or "息苦" in prompt or "症状" in prompt:
        response = (
            f"{p['age']}歳・{p['disease']}の患者様について、入力内容を確認しました。\\n\\n"
            f"現在の登録情報では、{p['weight_change']}、主な症状は"
            f"{'、'.join(p['symptoms'])}です。\\n\\n"
            "まずはバイタル・症状・体重推移・生活環境を整理してアセスメントすることをお勧めします。"
            "「🩺 アセスメント」から追加項目を入力できます。"
        )
    else:
        response = (
            "内容を確認しました。患者情報・過去記録・今回の入力を組み合わせて、"
            "アセスメント、看護診断候補、熟練看護師の知見、訪問記録、請求候補のいずれに進むかを整理できます。"
        )

    add_ai(response)
    st.rerun()
