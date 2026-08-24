import streamlit as st
import pandas as pd
import datetime
import random

# ==========================================================
# 訪問看護AIアシスタント - 会話型ワークフローモック
# 完全統合版（権限制御＋リッチUI復活）
# ==========================================================

st.set_page_config(
    page_title="訪問看護AIアシスタント",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- デモマスタ (権限・事業所追加) ----------
USERS = {
    "na.mukai@sample.co.jp": {"name": "向井", "role": "システム管理者", "branch": "本部", "pass": "password"},
    "tsutomu.jimbo@sample.co.jp": {"name": "神保", "role": "本部管理者", "branch": "本部", "pass": "password"},
    "nobuko.nakatake@sample.co.jp": {"name": "中武", "role": "看護師", "branch": "東京第一ステーション", "pass": "password"},
}

BRANCHES = ["東京第一ステーション", "横浜ステーション", "埼玉中央ステーション"]

PATIENTS = {
    "山田 太郎 (78歳 / 心不全)": {
        "age": 78, "disease": "心不全", "branch": "東京第一ステーション",
        "weight_change": "+2.4kg", "vitals": "BP 138/84 / SpO2 97% / 体温36.6℃ / PR 72",
        "symptoms": ["両下腿浮腫", "軽度の息苦しさ", "食欲低下"],
    },
    "佐藤 花子 (85歳 / 認知症・独居)": {
        "age": 85, "disease": "認知症", "branch": "東京第一ステーション",
        "weight_change": "-1.2kg", "vitals": "BP 132/76 / SpO2 96% / 体温36.4℃ / PR 78",
        "symptoms": ["服薬忘れ", "夜間不眠", "食事摂取量低下"],
    },
    "鈴木 一郎 (72歳 / 糖尿病)": {
        "age": 72, "disease": "糖尿病", "branch": "横浜ステーション",
        "weight_change": "-0.8kg", "vitals": "BP 146/88 / SpO2 98% / 体温36.5℃ / PR 80",
        "symptoms": ["食欲低下", "口渇", "血糖値変動"],
    },
}

# ---------- CSS ----------
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #3F0E40; }
[data-testid="stSidebar"] * { color: #F2E8F2 !important; }
[data-testid="stSidebar"] .stButton button { background: transparent; border: none; text-align: left; }
.ai-card { border: 1px solid #ddd; border-radius: 12px; padding: 18px; margin: 10px 0; background: #fff; }
.info-card { border-left: 5px solid #4f81bd; background: #f7fbff; padding: 15px; border-radius: 8px; }
.manage-card { border-left: 5px solid #f0ad4e; background: #fcf8e3; padding: 15px; border-radius: 8px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# ---------- セッション ----------
defaults = {
    "auth_status": "logged_out", "user_info": None, "otp": None,
    "selected_patient": "山田 太郎 (78歳 / 心不全)", "messages": [],
    "workflow": "idle", "visit_data": {}, "record_generated": False, "billing_generated": False,
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
            st.write("・システム管理者: `na.mukai@sample.co.jp` / `password`")
            st.write("・本部管理者: `tsutomu.jimbo@sample.co.jp` / `password`")
            st.write("・看護師: `nobuko.nakatake@sample.co.jp` / `password`")
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
    st.stop()

# ---------- ヘルパー ----------
def add_ai(text): st.session_state.messages.append(("assistant", text))
def add_user(text): st.session_state.messages.append(("user", text))
def go_chat(): st.session_state.workflow = "idle"; st.rerun()

def show_patient_summary():
    if not st.session_state.selected_patient: return
    p = PATIENTS.get(st.session_state.selected_patient)
    if p:
        st.markdown(
            f'<div class="info-card"><b>対象患者</b>：{st.session_state.selected_patient}'
            f'<br><b>バイタル</b>：{p["vitals"]}'
            f'<br><b>体重変化</b>：{p["weight_change"]}'
            f'<br><b>主な症状</b>：{"、".join(p["symptoms"])}</div>',
            unsafe_allow_html=True,
        )

# ---------- サイドバー ----------
user = st.session_state.user_info

# 看護師の場合は、自分の事業所の患者のみ選択肢に出す
if user["role"] == "看護師":
    available_patients = {k: v for k, v in PATIENTS.items() if v["branch"] == user["branch"]}
else:
    available_patients = PATIENTS

with st.sidebar:
    st.markdown("### 🏢 訪問看護ステーション")
    st.write(f"👤 **{user['name']}** ({user['role']})")
    st.caption(f"📍 所属: {user['branch']}")

    if st.session_state.selected_patient not in available_patients:
        st.session_state.selected_patient = list(available_patients.keys())[0] if available_patients else None

    if available_patients:
        st.session_state.selected_patient = st.selectbox(
            "🩺 対象患者",
            list(available_patients.keys()),
            index=list(available_patients.keys()).index(st.session_state.selected_patient) if st.session_state.selected_patient in available_patients else 0,
        )
    else:
        st.warning("担当患者がいません")

    st.markdown("---")
    st.markdown("### 💬 業務機能")
    if st.button("💬 メインチャットへ戻る", use_container_width=True): go_chat()
    if st.button("🩺 アセスメント", use_container_width=True): st.session_state.workflow = "assessment"; st.rerun()
    if st.button("📝 看護診断", use_container_width=True): st.session_state.workflow = "diagnosis"; st.rerun()
    if st.button("👩‍⚕️ 熟練看護師の知見", use_container_width=True): st.session_state.workflow = "expert"; st.rerun()
    if st.button("📄 訪問記録 / SOAP", use_container_width=True): st.session_state.workflow = "record"; st.rerun()
    if st.button("💰 請求候補", use_container_width=True): st.session_state.workflow = "billing"; st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ 管理メニュー")
    if st.button("👥 患者管理 (登録・編集)", use_container_width=True): st.session_state.workflow = "patient_manage"; st.rerun()
    
    if user["role"] in ["本部管理者", "システム管理者"]:
        if st.button("🏢 事業所管理", use_container_width=True): st.session_state.workflow = "branch_manage"; st.rerun()
        
    if user["role"] == "システム管理者":
        if st.button("🔑 ユーザー管理", use_container_width=True): st.session_state.workflow = "user_manage"; st.rerun()

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
# メイン：会話型AI & ワークフロー
# ==========================================================
st.title("💬 訪問看護 AIアシスタント")

# 初回メッセージ
if not st.session_state.messages:
    add_ai(
        "こんにちは。訪問看護AIアシスタントです。\n\n"
        "患者様の過去記録と本日の情報をもとに、訪問前確認、アセスメント、"
        "看護診断候補、熟練看護師の知見、訪問記録、請求候補の整理を支援します。\n\n"
        "まずは、何を確認したいか教えてください。"
    )

# ---------- ワークフローのカード (上部に展開) ----------

if st.session_state.workflow == "idle":
    show_patient_summary()

elif st.session_state.workflow == "patient_manage":
    st.markdown('<div class="manage-card"><b>👥 患者管理メニュー</b><br>新しい患者様の登録や、既存情報の編集を行います。</div>', unsafe_allow_html=True)
    if user["role"] == "看護師":
        st.info(f"※{user['branch']} に所属する患者のみ表示・編集可能です。")
    
    tab1, tab2 = st.tabs(["新規患者登録", "既存患者の編集"])
    with tab1:
        with st.form("new_patient_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("患者氏名")
            disease = c2.text_input("主病名")
            branch = c2.text_input("担当事業所", value=user["branch"], disabled=True) if user["role"] == "看護師" else c2.selectbox("担当事業所", BRANCHES)
            if st.form_submit_button("新規登録", type="primary"):
                add_user(f"{name} 様の新規登録を行いました。")
                add_ai(f"{name} 様（{branch}）の情報を登録しました。チャット画面から引き続き別のアセスメントや記録が可能です。")
                st.success("✅ 新規登録しました！")
    with tab2:
        edit_target = st.selectbox("編集する患者", list(available_patients.keys()))
        if edit_target:
            st.text_input("主病名 (編集)", value=available_patients[edit_target]["disease"])
            if st.button("更新する"):
                st.success("✅ 更新しました。")

elif st.session_state.workflow == "branch_manage":
    st.markdown('<div class="manage-card"><b>🏢 事業所管理メニュー</b><br>事業所の追加・編集を行います。</div>', unsafe_allow_html=True)
    new_branch = st.text_input("新しい事業所名")
    if st.button("事業所を追加", type="primary"):
        st.success(f"✅ {new_branch} を新設しました！")

elif st.session_state.workflow == "user_manage":
    st.markdown('<div class="manage-card"><b>🔑 ユーザー管理メニュー</b><br>新規スタッフのアカウントを追加します。</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    new_email = c1.text_input("メールアドレス")
    new_role = c1.selectbox("権限", ["看護師", "本部管理者", "システム管理者"])
    if st.button("招待を送信", type="primary"):
        st.success("✅ 招待メールを送信しました！")

# ----------------- リッチUI復活部分 -----------------
elif st.session_state.workflow == "assessment":
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
            f"浮腫「{edema}」、尿量「{urine}」です。\n\n"
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
        "S: 「昨日から少し息苦しい」と訴えあり。\n"
        f"O: {p['vitals']}。体重前回比 {p['weight_change']}。両下腿に浮腫あり。\n"
        "A: 心不全増悪を示唆する所見について追加確認が必要。\n"
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


# ---------- 会話履歴 (常に下部に表示) ----------
st.markdown("---")
st.subheader("💬 AIとの会話")

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

# ---------- クイックアクション ----------
st.markdown("##### ⚡ 会話から機能へ")
cols = st.columns(6)
actions = [
    ("🩺 アセス", "assessment"),
    ("📝 診断", "diagnosis"),
    ("👩‍⚕️ 知見", "expert"),
    ("📄 記録", "record"),
    ("💰 請求", "billing"),
    ("👤 新規患者", "patient_manage")
]
for col, (label, wf) in zip(cols, actions):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.workflow = wf
            st.rerun()

# ---------- チャット入力 ----------
if prompt := st.chat_input("患者様の状態や、行いたい操作（例: 新規患者を登録したい）を入力..."):
    add_user(prompt)

    low = prompt.lower()
    p = PATIENTS[st.session_state.selected_patient]
    
    # ユーザーの発言に応じて自動で機能画面を展開する
    if "新規" in prompt or "登録" in prompt or "追加" in prompt:
        add_ai("承知しました。患者様の新規登録画面を展開します。上部のフォームから入力してください。")
        st.session_state.workflow = "patient_manage"
    elif "記録" in prompt or "soap" in low:
        add_ai("今日の訪問記録を作成するための画面を展開します。")
        st.session_state.workflow = "record"
    elif "請求" in prompt or "レセプト" in prompt:
        add_ai("請求候補を確認します。")
        st.session_state.workflow = "billing"
    elif "ベテラン" in prompt or "熟練" in prompt or "経験" in prompt:
        add_ai("類似する過去事例から、熟練看護師の記録・助言を検索しました。「熟練看護師の知見」を展開します。")
        st.session_state.workflow = "expert"
    elif "診断" in prompt:
        add_ai("現在の情報から看護診断の候補を展開します。")
        st.session_state.workflow = "diagnosis"
    elif "体重" in prompt or "浮腫" in prompt or "息苦" in prompt or "症状" in prompt:
        add_ai(
            f"{p['age']}歳・{p['disease']}の患者様について、入力内容を確認しました。\n\n"
            f"現在の登録情報では、{p['weight_change']}、主な症状は"
            f"{'、'.join(p['symptoms'])}です。\n\n"
            "まずはバイタル・症状・体重推移・生活環境を整理してアセスメントすることをお勧めします。"
            "アセスメント画面を展開します。"
        )
        st.session_state.workflow = "assessment"
    else:
        add_ai("内容を確認しました。アセスメントや記録など、必要な機能を選択してください。")
        st.session_state.workflow = "idle"

    st.rerun()