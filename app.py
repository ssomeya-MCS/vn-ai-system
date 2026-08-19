import streamlit as st
import pandas as pd
import datetime
import random

# --- ページ設定 ---
st.set_page_config(
    page_title="訪問看護AIアシスタント (Slack Style)", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ユーザー定義マスタ ---
USERS = {
    "na.mukai@gakken.co.jp": {"name": "向井", "role": "システム管理者", "pass": "password"},
    "tsutomu.jimbo@mcsg.co.jp": {"name": "神保", "role": "本部管理者", "pass": "password"},
    "nobuko.nakatake@mcsg.co.jp": {"name": "中武", "role": "看護師", "pass": "password"}
}

# --- セッション状態の初期化 ---
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = 'logged_out' # logged_out, otp_required, logged_in
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'chat'
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = "山田 太郎 (78歳 / 心不全)"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "こんにちは！訪問看護AIアシスタントです。本日の訪問計画や患者様のアセスメント、看護診断についてお手伝いします。何か気になる点はありますか？"}
    ]

# --- カスタムCSS (Slack風UI & OTP画面デザイン) ---
st.markdown("""
    <style>
    /* Slack風サイドバーカラー */
    [data-testid="stSidebar"] {
        background-color: #3F0E40 !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] * {
        color: #E0D0E0 !important;
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: transparent !important;
        border: none !important;
        color: #D1D2D3 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 10px !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #350d36 !important;
        color: #FFFFFF !important;
    }
    
    /* 2段階認証カード風スタイル */
    .otp-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 450px;
        margin: 40px auto;
        text-align: center;
        border: 1px solid #eaeaea;
    }
    .sim-code-box {
        background-color: #FFF8E1;
        border: 1px solid #FFE082;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #5D4037;
        font-weight: bold;
    }
    .badge-code {
        background-color: #1A237E;
        color: #FFFFFF;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 1.2rem;
        letter-spacing: 2px;
    }
    .action-btn {
        margin: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. セキュリティ & ログインフロー
# ==========================================

# 【ログアウト状態】ID/PASS入力画面
if st.session_state.auth_status == 'logged_out':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔒 訪問看護AI統合システム")
        st.subheader("ログイン")
        
        email_input = st.text_input("メールアドレス (ID)", placeholder="例: na.mukai@gakken.co.jp")
        pass_input = st.text_input("パスワード", type="password", placeholder="password")
        
        if st.button("次へ（認証コード送信）", type="primary", use_container_width=True):
            if email_input in USERS and USERS[email_input]["pass"] == pass_input:
                st.session_state.user_info = USERS[email_input]
                st.session_state.user_info["email"] = email_input
                # 6桁のOTPコード生成
                st.session_state.generated_otp = str(random.randint(100000, 999999))
                st.session_state.auth_status = 'otp_required'
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません。")
                
        with st.expander("💡 開発テスト用アカウント情報"):
            st.write("・システム管理者: `na.mukai@gakken.co.jp` / `password`")
            st.write("・本部管理者: `tsutomu.jimbo@mcsg.co.jp` / `password`")
            st.write("・看護師: `nobuko.nakatake@mcsg.co.jp` / `password`")
    st.stop()

# 【OTP要求状態】2段階認証画面
elif st.session_state.auth_status == 'otp_required':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
            <div class="otp-card">
                <div class="sim-code-box">
                    🪲【開発用シミュレート】<br>
                    登録メール宛てに送信された仮想コード：<br>
                    <span class="badge-code">{st.session_state.generated_otp}</span>
                </div>
                <h2 style="color:#2C3E50;">🛡️ 2段階認証コードの入力</h2>
                <p style="color:#7F8C8D; font-size: 0.9rem;">
                    登録されたメールアドレス（{st.session_state.user_info['email']}）に送信された6桁のコードを入力してください。
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        otp_input = st.text_input("セキュリティコード (6桁)", max_chars=6, placeholder="000000")
        
        if st.button("🔒 認証してシステムにログイン", type="primary", use_container_width=True):
            if otp_input == st.session_state.generated_otp:
                st.session_state.auth_status = 'logged_in'
                st.success("認証に成功しました！")
                st.rerun()
            else:
                st.error("認証コードが一致しません。")
                
        if st.button("← ログイン画面に戻る", use_container_width=True):
            st.session_state.auth_status = 'logged_out'
            st.rerun()
    st.stop()


# ==========================================
# 2. メインアプリケーション (Slack風UI)
# ==========================================

user = st.session_state.user_info

# --- サイドバー (Slack風チャンネル & ナビゲーション) ---
with st.sidebar:
    st.markdown(f"### 🏢 訪問看護ステーション")
    st.markdown(f"👤 **{user['name']}** ({user['role']})")
    
    if st.button("🚪 ログアウト"):
        st.session_state.auth_status = 'logged_out'
        st.session_state.user_info = None
        st.rerun()
        
    st.markdown("---")
    
    # 患者選択ボックス
    st.markdown("🩺 **対象患者（コンテキスト）**")
    st.session_state.selected_patient = st.selectbox(
        "選択中の患者",
        ["山田 太郎 (78歳 / 心不全)", "佐藤 花子 (85歳 / 認知症・独居)", "鈴木 一郎 (72歳 / 糖尿病)"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("💬 **チャンネル / ワークスペース**")
    
    def nav_btn(label, page_name):
        active = "➡️ " if st.session_state.current_page == page_name else "  "
        if st.button(f"{active}{label}", key=f"nav_{page_name}"):
            st.session_state.current_page = page_name
            st.rerun()

    nav_btn("💬 AI訪問看護アシスタント", "chat")
    nav_btn("👤 顧客（対象患者）新規登録", "patient_register")
    nav_btn("📝 周辺環境・持病アセスメント", "assessment")
    nav_btn("🤖 AI看護診断 (NANDA-I)", "diagnosis")
    nav_btn("✅ 熟練看護師査読", "expert")
    nav_btn("📄 カルテ・請求情報入力", "billing")
    
    # 権限制御: 看護師権限（中武様など）には「事業所管理」を表示しない
    if user["role"] != "看護師":
        nav_btn("📊 事業所管理", "management")


# ==========================================
# 3. 画面コンテンツの描画
# ==========================================

# --- A. 💬 AI訪問看護アシスタント（Slack風チャットUI） ---
if st.session_state.current_page == 'chat':
    st.title("💬 訪問看護 AIアシスタント")
    st.caption(f"現在の対象患者: **{st.session_state.selected_patient}**")
    
    # チャット画面の上部にSlack風のショートカットアクションボタンを設置
    st.markdown("##### ⚡ クイックアクション (機能へ分岐)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🩺 持病アセスメント", use_container_width=True):
            st.session_state.current_page = 'assessment'
            st.rerun()
    with col2:
        if st.button("📝 看護診断を行う", use_container_width=True):
            st.session_state.current_page = 'diagnosis'
            st.rerun()
    with col3:
        if st.button("👩‍⚕️ 熟練者の助言を見る", use_container_width=True):
            st.session_state.current_page = 'expert'
            st.rerun()
    with col4:
        if st.button("💰 請求・カルテ作成", use_container_width=True):
            st.session_state.current_page = 'billing'
            st.rerun()

    st.markdown("---")

    # 過去の会話履歴表示
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # チャット入力フォーム
    if prompt := st.chat_input("患者様の状態や、AIに相談したいことを入力... (例: 食欲が落ちていて浮腫が気になります)"):
        # ユーザーの発言を記録
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # AIの応答（ダミーレスポンス＆誘導）
        with st.chat_message("assistant"):
            response = f"【{st.session_state.selected_patient} 様へのAI解説】\n\nご報告ありがとうございます。「{prompt}」についての過去記録を参照しました。\n\n心不全の増悪パターン（下腿浮腫・食欲低下）の予兆が見られます。左側メニューまたは上のボタンから **「📝 看護診断」** または **「🩺 持病アセスメント」** を開いて、選択式フォームでの詳細確認を行ってください。"
            st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})


# --- B. 👤 顧客（対象患者）新規登録画面 ---
elif st.session_state.current_page == 'patient_register':
    st.title("👤 顧客（対象患者）新規登録")
    st.write("新しい訪問看護対象者（患者様）の基本情報を登録します。")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("患者氏名", placeholder="例: 学研 太郎")
            kana = st.text_input("フリガナ", placeholder="例: ガッケン タロウ")
            gender = st.radio("性別", ["男性", "女性", "その他"], horizontal=True)
            birth = st.date_input("生年月日", datetime.date(1950, 1, 1))
        with col2:
            care_level = st.selectbox("要介護度", ["要支援1", "要支援2", "要介護1", "要介護2", "要介護3", "要介護4", "要介護5"])
            branch = st.selectbox("担当事業所（拠点）", ["東京第一ステーション", "横浜ステーション", "埼玉中央ステーション"])
            address = st.text_input("居住地住所")
            emergency_contact = st.text_input("緊急連絡先 (ご家族等)")

        st.markdown("---")
        medical_history = st.multiselect("持病・既往歴 (複数選択)", ["心不全", "糖尿病", "高血圧", "脳卒中", "認知症", "COPD", "がん(ターミナル)"])
        notes = st.text_area("キーパーソン・居住環境の特記事項", placeholder="独居。近隣に長男居住だが日中は不在。鍵はキーボックスにて管理。")

        submitted = st.form_submit_button("登録を確定する", type="primary")
        if submitted:
            if name:
                st.success(f"✅ 患者「{name} 様」の新規登録が完了しました。（※プロトタイプのためDBへの保存はシミュレーションです）")
            else:
                st.error("患者氏名を入力してください。")


# --- C. 📝 周辺環境・持病アセスメント画面 ---
elif st.session_state.current_page == 'assessment':
    st.title("📝 周辺環境・持病アセスメント")
    st.info(f"対象患者: **{st.session_state.selected_patient}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("持病・身体状況")
        st.multiselect("現在の主要症状", ["呼吸苦", "下腿浮腫", "食欲不振", "めまい", "倦怠感"], default=["下腿浮腫", "食欲不振"])
        st.slider("ADLスコア (日常生活動作能力)", 0, 100, 65)
    with col2:
        st.subheader("周辺環境・介護体制")
        st.radio("世帯状況", ["独居", "高齢夫婦（認認介護）", "家族同居（日中独居）", "施設居住"])
        st.text_area("介護者の疲弊度・家族サポート状況", "主介護者（妻）に疲弊傾向あり。ショートステイの活用を検討中。")


# --- D. 🤖 AI看護診断 (NANDA-I) 画面 ---
elif st.session_state.current_page == 'diagnosis':
    st.title("🤖 AI看護診断 (NANDA-I アシスタント)")
    st.info(f"対象患者: **{st.session_state.selected_patient}**")
    
    st.subheader("1. AI推奨の診断因子・関連因子 (既往歴から自動ソート)")
    st.checkbox("1. 【心拍出量減少】（既往の心不全・浮腫より推測）", value=True)
    st.checkbox("2. 【体液量過剰】（塩分摂取・利尿剤服薬状況要確認）", value=True)
    st.checkbox("3. 【栄養摂取不足の可能性】（食欲不振の記載より）")

    st.markdown("---")
    st.subheader("2. AI提示：追加確認すべきバイタル・反応")
    st.warning("⚠️ **推奨確認項目:** 起座呼吸の有無、下腿浮腫の深度(mm)、体重変化(+2kg/週がないか)")


# --- E. ✅ 熟練看護師査読画面 ---
elif st.session_state.current_page == 'expert':
    st.title("✅ 熟練看護師 査読・学習フィードバック")
    st.write("AIの提示した看護診断に対し、ベテランの判断を入力してモデルを継続学習させます。")
    
    st.info("AIの判断: [心拍出量減少] 確信度: 88%")
    status = st.radio("熟練者の判定", ["妥当である（AI提案を採用）", "修正が必要", "不適切"])
    st.text_area("ベテラン看護師のアドバイス・修正理由", placeholder="単なる心不全増悪だけでなく、訪問時の水分・塩分摂りすぎの問診も必要。")
    
    if st.button("学習データとして送信"):
        st.success("フィードバックを保存しました。AIモデルの重み付けに反映されます。")


# --- F. 📄 カルテ・請求情報入力画面 ---
elif st.session_state.current_page == 'billing':
    st.title("📄 カルテ・訪問記録・請求情報入力")
    st.info(f"対象患者: **{st.session_state.selected_patient}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.date_input("訪問日", datetime.date.today())
        st.time_input("開始時間", datetime.time(10, 0))
        st.number_input("滞在時間(分)", value=60)
    with col2:
        st.selectbox("訪問スタッフ資格", ["正看護師", "准看護師", "理学療法士(PT)", "作業療法士(OT)"])
        st.multiselect("自動判定された算定加算", ["24時間対応体制加算", "緊急訪問看護加算", "特別指示書期間内"], default=["24時間対応体制加算"])
        
    st.text_area("看護記録 (SOAP)", "S: 「少し足が重い感じがする」と訴えあり。\nO: BP 138/84, KT 36.6℃, PR 72, SPO2 97%。両下腿に軽度凹陷性浮腫あり。\nA: 心不全の軽度増悪の兆候あり。AI診断に基づき経過観察。\nP: 塩分管理の指導。次回訪問時に体重計測。")


# --- G. 📊 事業所管理画面（※看護師ロールには非表示） ---
elif st.session_state.current_page == 'management':
    st.title("📊 事業所・拠点管理ダッシュボード")
    st.caption("※この画面は本部管理者およびシステム管理者のみ閲覧可能です。")
    
    tab1, tab2 = st.tabs(["300拠点 収支サマリー", "AI診断一致率・品質分析"])
    with tab1:
        st.metric("全国324拠点 当月売上見込み", "¥248,500,000", "+8.4%")
        st.bar_chart(pd.DataFrame({'売上': [180, 210, 240, 250], '利益': [30, 45, 50, 52]}, index=['10月', '11月', '12月', '1月']))
    with tab2:
        st.write("拠点ごとのAI診断採用率と熟練看護師査読一致度")
        st.dataframe(pd.DataFrame({
            '拠点名': ['東京第一', '横浜ステーション', '埼玉中央', '大阪北'],
            '訪問件数': [420, 380, 310, 290],
            'AI採択率': ['94.2%', '91.8%', '88.5%', '95.0%'],
            '請求漏れ防止率': ['99.8%', '100%', '98.9%', '99.5%']
        }))