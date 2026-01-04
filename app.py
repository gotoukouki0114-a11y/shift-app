import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="シフト読み取りアプリ", page_icon="📅")
st.title("📅 シフト読み取りアプリ")

# --- 🛠 システム診断エリア ---
with st.expander("🛠 システム診断（エラー時はここを見て！）", expanded=False):
    st.write(f"Streamlit Version: {st.__version__}")
    # ライブラリのバージョンを表示
    try:
        st.write(f"Google Generative AI Version: {genai.__version__}")
        if genai.__version__ < "0.8.3":
            st.error("⚠️ ライブラリが古いです！requirements.txtを確認してください。")
    except:
        st.write("バージョン確認不可")

# --- 🔑 APIキー設定 ---
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ エラー: APIキーが見つかりません。Secretsの設定を確認してください。")
        st.stop()

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"✅ APIキー接続OK！ (Version: {genai.__version__})")

except Exception as e:
    st.error(f"❌ 設定エラー: {e}")
    st.stop()

# --- 📱 アプリ本編 ---
my_name = st.text_input("あなたの名前（シフト表と同じ表記で）", "飯田")
hourly_wage = st.number_input("時給", value=1100)
year_month = st.text_input("年月（例：2026-01）", "2026-01")

uploaded_file = st.file_uploader("シフト表をアップロード", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロード画像', use_container_width=True)
    
    if st.button("🚀 解析スタート"):
        with st.spinner("AIが解析中..."):
            try:
                # ★ここで最新モデルを指定★
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                この画像はシフト表です。以下のデータをJSON形式で抽出してください。
                ターゲット名: {my_name}
                日付は"{year_month}-01"形式。時間は"09:30"形式。
                JSONリストのみ出力（```json不要）。
                """
                
                response = model.generate_content([prompt, image])
                text = response.text.replace("```json", "").replace("```", "").strip()
                if text.startswith("json"): text = text[4:]
                
                data = json.loads(text)
                st.success(f"🎉 {len(data)}件のシフトが見つかりました！")
                
                total_salary = 0
                for item in data:
                    start = datetime.strptime(f"{item['date']} {item['start']}", "%Y-%m-%d %H:%M")
                    end = datetime.strptime(f"{item['date']} {item['end']}", "%Y-%m-%d %H:%M")
                    hours = (end - start).seconds / 3600
                    salary = hours * hourly_wage
                    total_salary += salary
                    
                    # リンク作成
                    title = urllib.parse.quote(f"バイト({item['start']}-{item['end']})")
                    dates = start.strftime("%Y%m%dT%H%M00") + "/" + end.strftime("%Y%m%dT%H%M00")
                    details = urllib.parse.quote(f"予想給与: ¥{int(salary):,}")
                    url = f"[https://www.google.com/calendar/render?action=TEMPLATE&text=](https://www.google.com/calendar/render?action=TEMPLATE&text=){title}&dates={dates}&details={details}"
                    
                    st.markdown(f"📅 **{item['date']}** ({item['start']}-{item['end']}) → [カレンダー追加]({url})")
                
                st.info(f"💰 予想給与合計: ¥{int(total_salary):,}")
                
            except Exception as e:
                st.error("解析エラーが発生しました。")
                st.error(f"詳細: {e}")
                # もしモデルエラーなら、使えるモデル一覧を表示してあげる
                st.write("👇 あなたのAPIキーで使えるモデル一覧:")
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            st.write(f"- {m.name}")
                except:
                    st.write("モデル一覧の取得に失敗しました。")
