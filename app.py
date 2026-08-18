import streamlit as st
import pandas as pd
import datetime

# --- ページ設定 ---
st.set_page_config(page_title="訪問看護AI統合システム", layout="wide")

# --- カスタムCSS (見た目の調整) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #0078d4; color: white; }
    .status-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- セッション状態でページ遷移を管理 ---
if 'page' not in st.session_state:
    st.session_state.page = 'portal'

def change_page(page_name):
    st.session_state.page = page_name

# --- サイドバー (ナビゲーション) ---
st.sidebar.title("📌 業務メニュー")
if st.sidebar.button("🏠 ポータル画面"): change_page('portal')
if st.sidebar.button("📝 環境・持病アセスメント"): change_page('assessment')
if st.sidebar.button("🤖 AI看護診断"): change_page('diagnosis')
if st.sidebar.button("✅ 熟練者査読"): change_page('expert')
if st.sidebar.button("📄 カルテ・請求入力"): change_page('billing')
if st.sidebar.button("📊 事業所管理"): change_page('management')

# --- 1. ポータル画面 ---
if st.session_state.page == 'portal':
    st.title("🚀 訪問看護AI統合ポータル")
    st.info("現在、全国324拠点のうち、稼働中の全拠点のサマリーを表示しています。")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("本日の訪問予定", "1,240件", "+12%")
    with col2:
        st.metric("AI診断一致率", "94.2%", "+1.5%")
    with col3:
        st.metric("未処理アラート", "8件", "-2", delta_color="normal")
    
    st.subheader("💡 今日の重点アクション")
    st.warning("【アラート】第3拠点：ターミナルケア移行に伴う緊急アセスメントが必要です。")

# --- 2. 環境・持病アセスメント入力 ---
elif st.session_state.page == 'assessment':
    st.title("📝 周辺環境・持病アセスメント")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("対象患者", ["山田 太郎 (78歳)", "佐藤 花子 (85歳)"])
        st.multiselect("持病・既往歴", ["心不全", "糖尿病", "高血圧", "認知症"], default=["心不全"])
    with col2:
        st.radio("居住環境", ["独居", "認認介護", "同居（日中独居）", "施設"])
        st.text_area("家族関係の特記事項", "長男が近隣に住んでいるが、平日は連絡困難。")

# --- 3. AI看護診断画面 ---
elif st.session_state.page == 'diagnosis':
    st.title("🤖 AI看護診断アシスタント")
    st.write("アセスメント情報に基づき、優先度の高い診断因子を提示しています。")
    
    # 動的選択肢のシミュレーション
    st.subheader("診断因子の選択（AI推奨順）")
    st.checkbox("1. 心拍出量減少（既往の心不全から推測）", value=True)
    st.checkbox("2. 体液量過剰（浮腫の兆候あり）", value=True)
    st.checkbox("3. 転倒リスク（独居・ADL低下）")

    st.markdown("---")
    st.subheader("🚩 AIの判断・推奨アクション")
    st.success("**診断候補: 心拍出量減少**")
    st.info("**追加確認すべきバイタル:** 起座呼吸の有無、下腿浮腫の深度(mm)、頸静脈怒張")

# --- 4. 熟練看護師の判断入力 ---
elif st.session_state.page == 'expert':
    st.title("✅ 熟練看護師 査読・フィードバック")
    st.write("AIの判定に対し、ベテランの視点からフィードバックを入力し学習させます。")
    
    st.info("AIの提示: [心拍出量減少] 確信度: 88%")
    choice = st.radio("判定の妥当性", ["妥当である", "修正が必要", "不適切"])
    st.text_area("修正内容・新人へのアドバイス", placeholder="心不全の悪化よりは、水分摂取過多による一時的な浮腫の可能性が高い。")
    if st.button("学習データとして送信"):
        st.success("フィードバックを保存しました。AIモデルに反映されます。")

# --- 5. カルテ・請求入力 ---
elif st.session_state.page == 'billing':
    st.title("📄 カルテ・請求情報入力")
    col1, col2 = st.columns(2)
    with col1:
        st.date_input("訪問日", datetime.date.today())
        st.time_input("開始時間")
        st.number_input("滞在時間(分)", value=60)
    with col2:
        st.selectbox("訪問スタッフ", ["正看護師: 田中", "准看護師: 鈴木", "PT: 佐藤"])
        st.multiselect("算定加算", ["ターミナルケア加算", "緊急訪問看護加算", "24時間対応体制"])
    
    st.text_area("看護記録 (SOAP)", "S: 息苦しさはない。 O: 足の甲に軽度の浮腫あり。 A: AI診断に基づき経過観察。 P: 塩分制限の指導継続。")

# --- 6. 事業所管理画面 ---
elif st.session_state.page == 'management':
    st.title("📊 事業所管理ダッシュボード")
    tab1, tab2 = st.tabs(["収支分析", "拠点比較"])
    with tab1:
        st.bar_chart(pd.DataFrame({'売上': [100, 120, 150, 130], '利益': [20, 30, 45, 25]}, index=['10月', '11月', '12月', '1月']))
    with tab2:
        st.write("全300拠点の平均値との比較")
        st.dataframe(pd.DataFrame({
            '拠点': ['東京第一', '横浜第二', '全体平均'],
            '訪問効率': ['4.2件/日', '3.8件/日', '3.5件/日'],
            '未回収リスク': ['低', '中', '低']
        }))